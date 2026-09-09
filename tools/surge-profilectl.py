#!/usr/bin/env python3
"""Safely manage private Surge profile sources and trigger updates."""

from __future__ import annotations

import argparse
import getpass
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.parse
from pathlib import Path


DEFAULT_CONFIG = Path("/etc/surge-profile/config.json")
DEFAULT_SECRETS = Path("/etc/surge-profile/secrets.json")
RENDERER = "/usr/local/libexec/surge-profile/render-private-profiles.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_atomic(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_name, 0o600)
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def read_url() -> str:
    value = getpass.getpass("Sub-Store HTTPS URL (input hidden): ").strip()
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme != "https" or not parsed.netloc or any(c in value for c in ('\n', '\r', '"')):
        raise ValueError("URL must be an absolute HTTPS URL without quotes or line breaks")
    return value


def update() -> int:
    return subprocess.run([RENDERER], check=False).returncode


def apply_source_change(secrets_path: Path, original: dict, changed: dict) -> int:
    write_json_atomic(secrets_path, changed)
    result = update()
    if result != 0:
        write_json_atomic(secrets_path, original)
        print("source change rolled back; active profiles were not replaced", file=sys.stderr)
    return result


def command_set_default(secrets_path: Path) -> int:
    original = load_json(secrets_path)
    data = json.loads(json.dumps(original))
    data["default_substore_url"] = read_url()
    data.setdefault("profiles", {})
    print("default Sub-Store source updated")
    return apply_source_change(secrets_path, original, data)


def command_set_profile(secrets_path: Path, profile_id: str) -> int:
    original = load_json(secrets_path)
    data = json.loads(json.dumps(original))
    profiles = data.setdefault("profiles", {})
    profiles[profile_id] = read_url()
    print(f"Sub-Store source override updated for {profile_id}")
    return apply_source_change(secrets_path, original, data)


def command_clear_profile(secrets_path: Path, profile_id: str) -> int:
    original = load_json(secrets_path)
    data = json.loads(json.dumps(original))
    profiles = data.setdefault("profiles", {})
    if profile_id in profiles:
        del profiles[profile_id]
        print(f"Sub-Store source override cleared for {profile_id}")
    else:
        print(f"no source override configured for {profile_id}")
        return 0
    return apply_source_change(secrets_path, original, data)


def read_profile_meta(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if not raw.startswith("# @"):
            continue
        key, _, value = raw[3:].partition(":")
        meta[key.strip()] = value.strip()
    return meta


def command_status(config_path: Path, secrets_path: Path, check: bool = False) -> int:
    config = load_json(config_path)
    secrets = load_json(secrets_path)
    print(f"default source configured: {bool(secrets.get('default_substore_url'))}")
    overrides = secrets.get("profiles", {})
    print("profile overrides: " + (", ".join(sorted(overrides)) if overrides else "none"))
    output_root = Path(config.get("output_root", "/var/lib/surge-profile"))
    current = output_root / "current"
    if current.is_symlink():
        release = current.resolve()
        print(f"active release: {release.name}")
        metadata = release / "release.json"
        problems: list[str] = []
        if metadata.exists():
            info = load_json(metadata)
            generated = int(info.get("generated_at", 0))
            age = int(time.time()) - generated
            print(f"release age: {age} second(s) (generated {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(generated))})")
            if age > 45 * 60:
                problems.append(f"release is {age} second(s) old, expected a refresh every 15 minutes")
            for output in info.get("outputs", []):
                profile_path = release / output
                if not profile_path.is_file():
                    problems.append(f"{output}: rendered file is missing")
                    continue
                meta = read_profile_meta(profile_path)
                print(
                    f"{output}: profile={meta.get('profile', '?')} "
                    f"version={meta.get('version', '?')} status={meta.get('status', '?')}"
                )
                if not meta.get("profile") or not meta.get("version"):
                    problems.append(f"{output}: missing profile/version metadata")
            if problems:
                print("problems:")
                for problem in problems:
                    print(f"  - {problem}")
                return 1 if check else 0
            return 0
        print("release.json is missing")
        return 1 if check else 0
    else:
        print("active release: none")
        return 1 if check else 0


def command_urls(config_path: Path) -> int:
    config = load_json(config_path)
    base = config["public_base_url"].rstrip("/")
    output_root = Path(config.get("output_root", "/var/lib/surge-profile"))
    current = output_root / "current"
    if not current.is_symlink():
        print("no active release", file=sys.stderr)
        return 1
    info = load_json(current.resolve() / "release.json")
    for output in info.get("outputs", []):
        print(f"{base}/{output}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="surge-profilectl")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--secrets", type=Path, default=DEFAULT_SECRETS)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("set-default")
    set_parser = subparsers.add_parser("set")
    set_parser.add_argument("profile_id")
    clear_parser = subparsers.add_parser("clear")
    clear_parser.add_argument("profile_id")
    subparsers.add_parser("update")
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--check", action="store_true", help="exit non-zero when the release is stale or broken")
    subparsers.add_parser("urls")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        if args.command == "set-default":
            return command_set_default(args.secrets)
        if args.command == "set":
            return command_set_profile(args.secrets, args.profile_id)
        if args.command == "clear":
            return command_clear_profile(args.secrets, args.profile_id)
        if args.command == "update":
            return update()
        if args.command == "status":
            return command_status(args.config, args.secrets, check=args.check)
        if args.command == "urls":
            return command_urls(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
