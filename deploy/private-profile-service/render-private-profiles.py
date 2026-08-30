#!/usr/bin/env python3
"""Render private Surge profiles from public templates without exposing secrets."""

from __future__ import annotations

import argparse
import base64
import fcntl
import ipaddress
import json
import os
import re
import shutil
import ssl
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path

PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")
PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
WG_PLACEHOLDERS = {
    "__WG_PRIVATE_KEY__": "private_key",
    "__WG_SELF_IP__": "self_ip",
    "__WG_SELF_IP_V6__": "self_ip_v6",
    "__WG_DNS_SERVER__": "dns_server",
    "__WG_PEER_PUBLIC_KEY__": "peer_public_key",
    "__WG_ENDPOINT__": "endpoint",
    "__WG_ALLOWED_IPS__": "allowed_ips",
    "__WG_KEEPALIVE__": "keepalive",
}


class RenderError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RenderError(f"cannot read JSON file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RenderError(f"JSON root must be an object: {path}")
    return data


def https_url(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or any(c in value for c in "\r\n\""):
        raise RenderError(f"{label} is missing or unsafe")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RenderError(f"{label} must be an absolute HTTPS URL")
    return value.rstrip("/")


def fetch(url: str, timeout: int, private: bool = False) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "surge-private-profile-renderer/2"})
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=ssl.create_default_context()) as response:
            if response.status != 200:
                raise RenderError("private source returned a non-200 status" if private else f"download returned HTTP {response.status}")
            return response.read().decode("utf-8")
    except RenderError:
        raise
    except Exception as exc:
        raise RenderError("private source could not be read" if private else f"template download failed: {exc}") from exc


def cache_bust(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("_surge_ts", str(int(time.time()))))
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment))


def validate_key(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RenderError(f"{label} is missing")
    try:
        decoded = base64.b64decode(value, validate=True)
    except Exception as exc:
        raise RenderError(f"{label} is not standard Base64") from exc
    if len(decoded) != 32:
        raise RenderError(f"{label} must decode to 32 bytes")
    return value


def validate_ip(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise RenderError(f"{label} is missing")
    try:
        ipaddress.ip_address(value)
    except ValueError as exc:
        raise RenderError(f"{label} is not an IP address") from exc
    return value


def validate_endpoint(value: object) -> str:
    if not isinstance(value, str) or any(c in value for c in "\r\n\"(),") or ":" not in value:
        raise RenderError("WireGuard endpoint is missing or unsafe")
    host, port = value.rsplit(":", 1)
    if not host or not port.isdigit() or not 1 <= int(port) <= 65535:
        raise RenderError("WireGuard endpoint must be host:port")
    return value


def validate_dns_server(value: object) -> str:
    server = validate_endpoint(value)
    host, _ = server.rsplit(":", 1)
    try:
        ipaddress.ip_address(host)
    except ValueError as exc:
        raise RenderError("WireGuard DNS server must be an IP address and port") from exc
    return server


def wireguard_values(secrets: dict, profile_id: str) -> dict[str, str]:
    profiles = secrets.get("wireguard_profiles", {})
    data = profiles.get(profile_id) if isinstance(profiles, dict) else None
    if not isinstance(data, dict):
        raise RenderError(f"WireGuard secret for {profile_id} is missing")
    dns = validate_dns_server(data.get("dns_server"))
    allowed = data.get("allowed_ips")
    if not isinstance(allowed, str) or not allowed or any(c in allowed for c in "\r\n\""):
        raise RenderError("WireGuard allowed_ips is missing or unsafe")
    try:
        for network in allowed.split(","):
            ipaddress.ip_network(network.strip(), strict=False)
    except ValueError as exc:
        raise RenderError("WireGuard allowed_ips contains an invalid network") from exc
    keepalive = data.get("keepalive")
    if not isinstance(keepalive, int) or not 0 <= keepalive <= 65535:
        raise RenderError("WireGuard keepalive must be 0-65535")
    return {
        "private_key": validate_key(data.get("private_key"), "WireGuard private key"),
        "self_ip": validate_ip(data.get("self_ip"), "WireGuard IPv4 address"),
        "self_ip_v6": validate_ip(data.get("self_ip_v6"), "WireGuard IPv6 address"),
        "dns_server": dns,
        "peer_public_key": validate_key(data.get("peer_public_key"), "WireGuard peer public key"),
        "endpoint": validate_endpoint(data.get("endpoint")),
        "allowed_ips": allowed,
        "keepalive": str(keepalive),
    }


def validate_substore(text: str) -> None:
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines or "<html" in text[:4096].lower():
        raise RenderError("Sub-Store source is empty or returned HTML")
    if not any(line == "[Proxy]" or "=" in line for line in lines):
        raise RenderError("Sub-Store source is not Surge output")


def validate_profile(text: str, profile_id: str, managed_url: str) -> None:
    unresolved = sorted(set(PLACEHOLDER_RE.findall(text)))
    if unresolved:
        raise RenderError(f"{profile_id}: unresolved placeholders: {', '.join(unresolved)}")
    if text.splitlines()[0] != f"#!MANAGED-CONFIG {managed_url} interval=86400 strict=false":
        raise RenderError(f"{profile_id}: invalid managed profile header")
    for section in ("[General]", "[Proxy]", "[Proxy Group]", "[Rule]"):
        if text.count(section) != 1:
            raise RenderError(f"{profile_id}: expected exactly one {section} section")
    in_rules, rules = False, []
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            in_rules = line == "[Rule]"
        elif in_rules and line and not line.startswith("#"):
            rules.append(line)
    finals = [line for line in rules if line.startswith("FINAL,")]
    if len(finals) != 1 or not rules or rules[-1] != finals[0]:
        raise RenderError(f"{profile_id}: FINAL must appear exactly once and last")


def stage(config: dict, secrets: dict, manifest: dict) -> tuple[Path, list[str]]:
    root = Path(config.get("output_root", "/var/lib/surge-profile"))
    releases = root / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    timeout = int(config.get("timeout_seconds", 30))
    base = https_url(config.get("public_base_url"), "public_base_url")
    directory = Path(tempfile.mkdtemp(prefix=".staging-", dir=releases))
    directory.chmod(0o755)
    outputs, seen_ids, seen_outputs, checked = [], set(), set(), set()
    try:
        entries = manifest.get("profiles") if manifest.get("version") == 1 else None
        if not isinstance(entries, list) or not entries:
            raise RenderError("manifest version must be 1 with a non-empty profiles list")
        for entry in entries:
            if not isinstance(entry, dict):
                raise RenderError("manifest profile must be an object")
            profile_id, output = entry.get("id"), entry.get("output")
            if not isinstance(profile_id, str) or not PROFILE_ID_RE.fullmatch(profile_id):
                raise RenderError("invalid profile id")
            if not isinstance(output, str) or Path(output).name != output or not output.endswith(".conf"):
                raise RenderError(f"{profile_id}: invalid output")
            if profile_id in seen_ids or output in seen_outputs:
                raise RenderError("duplicate profile id or output")
            seen_ids.add(profile_id); seen_outputs.add(output)
            template = fetch(cache_bust(https_url(entry.get("template_url"), f"template_url for {profile_id}")), timeout)
            managed_url = f"{base}/{output}"
            if template.count("__MANAGED_CONFIG_URL__") != 1:
                raise RenderError(f"{profile_id}: template needs one managed URL placeholder")
            rendered = template.replace("__MANAGED_CONFIG_URL__", managed_url)
            if "__SUBSTORE_URL__" in rendered:
                if rendered.count("__SUBSTORE_URL__") != 1:
                    raise RenderError(f"{profile_id}: template needs at most one Sub-Store placeholder")
                overrides = secrets.get("profiles", {})
                source = overrides.get(profile_id) if isinstance(overrides, dict) else None
                source = source or secrets.get("default_substore_url")
                source = https_url(source, f"Sub-Store URL for {profile_id}")
                if source not in checked:
                    validate_substore(fetch(source, timeout, private=True)); checked.add(source)
                rendered = rendered.replace("__SUBSTORE_URL__", source)
            if any(token in rendered for token in WG_PLACEHOLDERS):
                values = wireguard_values(secrets, profile_id)
                for token, key in WG_PLACEHOLDERS.items():
                    rendered = rendered.replace(token, values[key])
            validate_profile(rendered, profile_id, managed_url)
            target = directory / output
            target.write_text(rendered, encoding="utf-8"); target.chmod(0o644); outputs.append(output)
        metadata = directory / "release.json"
        metadata.write_text(json.dumps({"generated_at": int(time.time()), "outputs": outputs}, indent=2) + "\n", encoding="utf-8")
        metadata.chmod(0o644)
        return directory, outputs
    except Exception:
        shutil.rmtree(directory, ignore_errors=True); raise


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--config", default="/etc/surge-profile/config.json"); parser.add_argument("--secrets", default="/etc/surge-profile/secrets.json")
    args = parser.parse_args()
    try:
        config, secrets_path = load_json(Path(args.config)), Path(args.secrets)
        if secrets_path.stat().st_mode & 0o077:
            raise RenderError(f"secrets file permissions must be 0600: {secrets_path}")
        secrets = load_json(secrets_path); root = Path(config.get("output_root", "/var/lib/surge-profile")); root.mkdir(parents=True, exist_ok=True)
        manifest = json.loads(fetch(cache_bust(https_url(config.get("manifest_url"), "manifest_url")), int(config.get("timeout_seconds", 30))))
        with (root / ".render.lock").open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX); staged, outputs = stage(config, secrets, manifest)
            final = staged.with_name(f"release-{int(time.time())}-{os.getpid()}"); staged.rename(final)
            temporary = root / ".current-new"; temporary.unlink(missing_ok=True); temporary.symlink_to(final); os.replace(temporary, root / "current")
            old_releases = sorted((path for path in (root / "releases").glob("release-*") if path.is_dir()), key=lambda path: path.stat().st_mtime, reverse=True)
            for old in old_releases[4:]:
                shutil.rmtree(old, ignore_errors=True)
        print(f"activated {len(outputs)} profiles: {', '.join(outputs)}"); return 0
    except (RenderError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"render failed: {exc}", file=__import__("sys").stderr); return 1


if __name__ == "__main__":
    raise SystemExit(main())
