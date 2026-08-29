#!/usr/bin/env python3
"""Render private Surge profiles from public GitHub templates."""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import ssl
import sys
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path


PLACEHOLDER_RE = re.compile(r"__[A-Z][A-Z0-9_]*__")
PROFILE_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
USER_AGENT = "surge-private-profile-renderer/1"


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


def validate_https_url(value: str, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise RenderError(f"{label} is missing")
    if any(char in value for char in ('\n', '\r', '"')):
        raise RenderError(f"{label} contains an unsafe character")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc:
        raise RenderError(f"{label} must be an absolute HTTPS URL")
    return value.rstrip("/")


def fetch_text(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            if response.status != 200:
                raise RenderError(f"download returned HTTP {response.status}")
            raw = response.read()
    except Exception as exc:
        raise RenderError(f"download failed for {urllib.parse.urlsplit(url).netloc}: {exc}") from exc
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RenderError("downloaded content is not UTF-8") from exc


def fetch_private_text(url: str, timeout: int) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=timeout, context=context) as response:
            if response.status != 200:
                raise RenderError("private source returned a non-200 status")
            raw = response.read()
        return raw.decode("utf-8")
    except Exception as exc:
        raise RenderError("Sub-Store source could not be read as UTF-8 Surge output") from exc


def cache_bust(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
    query.append(("_surge_ts", str(int(time.time()))))
    return urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, urllib.parse.urlencode(query), parsed.fragment)
    )


def load_manifest(config: dict, timeout: int) -> dict:
    manifest_url = validate_https_url(config.get("manifest_url", ""), "manifest_url")
    try:
        manifest = json.loads(fetch_text(cache_bust(manifest_url), timeout))
    except json.JSONDecodeError as exc:
        raise RenderError(f"manifest is not valid JSON: {exc}") from exc
    if not isinstance(manifest, dict) or manifest.get("version") != 1:
        raise RenderError("manifest version must be 1")
    profiles = manifest.get("profiles")
    if not isinstance(profiles, list) or not profiles:
        raise RenderError("manifest profiles must be a non-empty list")
    return manifest


def validate_profile_entry(entry: object) -> tuple[str, str, str]:
    if not isinstance(entry, dict):
        raise RenderError("each manifest profile must be an object")
    profile_id = entry.get("id")
    template_url = entry.get("template_url")
    output = entry.get("output")
    if not isinstance(profile_id, str) or not PROFILE_ID_RE.fullmatch(profile_id):
        raise RenderError("profile id must contain lowercase letters, digits, _ or -")
    template_url = validate_https_url(template_url, f"template_url for {profile_id}")
    if not isinstance(output, str) or Path(output).name != output or not output.endswith(".conf"):
        raise RenderError(f"output for {profile_id} must be a .conf basename")
    return profile_id, template_url, output


def validate_rendered_profile(text: str, profile_id: str, managed_url: str) -> None:
    unresolved = sorted(set(PLACEHOLDER_RE.findall(text)))
    if unresolved:
        raise RenderError(f"{profile_id}: unresolved placeholders: {', '.join(unresolved)}")
    expected_header = f"#!MANAGED-CONFIG {managed_url} interval=86400 strict=false"
    if text.splitlines()[0] != expected_header:
        raise RenderError(f"{profile_id}: invalid managed profile header")
    for section in ("[General]", "[Proxy]", "[Proxy Group]", "[Rule]"):
        if text.count(section) != 1:
            raise RenderError(f"{profile_id}: expected exactly one {section} section")

    in_rules = False
    active_rules: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line.startswith("[") and line.endswith("]"):
            in_rules = line == "[Rule]"
            continue
        if in_rules and line and not line.startswith("#"):
            active_rules.append(line)
    finals = [line for line in active_rules if line.startswith("FINAL,")]
    if len(finals) != 1 or not active_rules or active_rules[-1] != finals[0]:
        raise RenderError(f"{profile_id}: FINAL must appear exactly once and be the last rule")


def choose_substore_url(secrets: dict, profile_id: str) -> str:
    overrides = secrets.get("profiles", {})
    if not isinstance(overrides, dict):
        raise RenderError("secrets profiles must be an object")
    value = overrides.get(profile_id) or secrets.get("default_substore_url")
    return validate_https_url(value, f"Sub-Store URL for {profile_id}")


def validate_substore_payload(text: str) -> None:
    lowered = text[:4096].lower()
    if "<html" in lowered or "<!doctype html" in lowered:
        raise RenderError("Sub-Store source returned HTML instead of Surge output")
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        raise RenderError("Sub-Store source returned an empty response")
    has_proxy_section = any(line == "[Proxy]" for line in lines)
    has_proxy_definition = any(
        "=" in line and not (line.startswith("[") and line.endswith("]")) for line in lines
    )
    if not has_proxy_section and not has_proxy_definition:
        raise RenderError("Sub-Store source is not a Surge proxy list or complete Profile")


def stage_release(config: dict, secrets: dict, manifest: dict) -> tuple[Path, list[str]]:
    output_root = Path(config.get("output_root", "/var/lib/surge-profile"))
    releases_dir = output_root / "releases"
    releases_dir.mkdir(parents=True, exist_ok=True)
    timeout = int(config.get("timeout_seconds", 30))
    public_base = validate_https_url(config.get("public_base_url", ""), "public_base_url")
    release_dir = Path(tempfile.mkdtemp(prefix=".staging-", dir=releases_dir))
    release_dir.chmod(0o755)
    outputs: list[str] = []
    seen_ids: set[str] = set()
    seen_outputs: set[str] = set()
    checked_sources: set[str] = set()

    try:
        for raw_entry in manifest["profiles"]:
            profile_id, template_url, output = validate_profile_entry(raw_entry)
            if profile_id in seen_ids or output in seen_outputs:
                raise RenderError(f"duplicate profile id or output: {profile_id}")
            seen_ids.add(profile_id)
            seen_outputs.add(output)
            substore_url = choose_substore_url(secrets, profile_id)
            if substore_url not in checked_sources:
                validate_substore_payload(fetch_private_text(substore_url, timeout))
                checked_sources.add(substore_url)
            managed_url = f"{public_base}/{output}"
            template = fetch_text(cache_bust(template_url), timeout)
            if template.count("__SUBSTORE_URL__") != 1:
                raise RenderError(f"{profile_id}: template must contain one __SUBSTORE_URL__")
            if template.count("__MANAGED_CONFIG_URL__") != 1:
                raise RenderError(f"{profile_id}: template must contain one __MANAGED_CONFIG_URL__")
            rendered = template.replace("__SUBSTORE_URL__", substore_url)
            rendered = rendered.replace("__MANAGED_CONFIG_URL__", managed_url)
            validate_rendered_profile(rendered, profile_id, managed_url)
            target = release_dir / output
            target.write_text(rendered, encoding="utf-8")
            target.chmod(0o644)
            outputs.append(output)
        metadata_path = release_dir / "release.json"
        metadata_path.write_text(
            json.dumps(
                {"generated_at": int(time.time()), "outputs": outputs},
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        metadata_path.chmod(0o644)
        return release_dir, outputs
    except Exception:
        shutil.rmtree(release_dir, ignore_errors=True)
        raise


def activate_release(output_root: Path, release_dir: Path) -> None:
    final_release = release_dir.with_name(f"release-{int(time.time())}-{os.getpid()}")
    release_dir.rename(final_release)
    current = output_root / "current"
    temporary_link = output_root / ".current-new"
    temporary_link.unlink(missing_ok=True)
    temporary_link.symlink_to(final_release)
    os.replace(temporary_link, current)

    keep = 4
    releases = sorted(
        (path for path in (output_root / "releases").glob("release-*") if path.is_dir()),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_release in releases[keep:]:
        if old_release != final_release:
            shutil.rmtree(old_release, ignore_errors=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/etc/surge-profile/config.json")
    parser.add_argument("--secrets", default="/etc/surge-profile/secrets.json")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_json(Path(args.config))
        secrets_path = Path(args.secrets)
        secrets = load_json(secrets_path)
        if secrets_path.stat().st_mode & 0o077:
            raise RenderError(f"secrets file permissions must be 0600: {secrets_path}")
        output_root = Path(config.get("output_root", "/var/lib/surge-profile"))
        output_root.mkdir(parents=True, exist_ok=True)
        with (output_root / ".render.lock").open("a+", encoding="utf-8") as lock:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
            timeout = int(config.get("timeout_seconds", 30))
            manifest = load_manifest(config, timeout)
            release_dir, outputs = stage_release(config, secrets, manifest)
            activate_release(output_root, release_dir)
        print(f"activated {len(outputs)} profiles: {', '.join(outputs)}")
        return 0
    except (RenderError, OSError, ValueError) as exc:
        print(f"render failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
