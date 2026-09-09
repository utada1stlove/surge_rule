#!/usr/bin/env python3
"""Enforce the profile versioning contract used by this repository.

Rules:
- Every file under profiles/<family>/ must be named <semver>.conf and carry
  matching # @profile / # @version / # @status metadata.
- Exactly one active version per family; it must be the highest version and it
  must be the version referenced by config/private-profile-templates.json.
- Families keep at most three versions; older releases must be archived.
- Files under legacy/ must be frozen and must NOT be referenced by the manifest.
- Files under archive/ must not be referenced by the manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
META_RE = re.compile(r"^#\s+@(\S+):\s*(.*)$")
ACTIVE_STATUSES = {"active", "superseded"}
MAX_VERSIONS_PER_FAMILY = 3


def version_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def parse_metadata(path: Path) -> dict[str, str]:
    meta: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        match = META_RE.match(raw)
        if match:
            meta[match.group(1)] = match.group(2).strip()
    return meta


def load_manifest(root: Path) -> dict:
    path = root / "config/private-profile-templates.json"
    if not path.is_file():
        return {"profiles": []}
    return json.loads(path.read_text(encoding="utf-8"))


def check_profiles(root: Path, manifest: dict, errors: list[str]) -> None:
    sources = {entry.get("source") for entry in manifest.get("profiles", [])}
    families = sorted(path for path in (root / "profiles").iterdir() if path.is_dir())
    if not families:
        errors.append("profiles/: no family directories found")
        return
    for family in families:
        files = sorted(family.glob("*.conf"))
        if not files:
            errors.append(f"{family}: no .conf files")
            continue
        if len(files) > MAX_VERSIONS_PER_FAMILY:
            errors.append(
                f"{family}: {len(files)} versions kept (max {MAX_VERSIONS_PER_FAMILY}); archive older releases"
            )
        active: list[Path] = []
        versions: dict[Path, tuple[int, ...]] = {}
        for path in files:
            meta = parse_metadata(path)
            declared = meta.get("version", "")
            if not SEMVER.fullmatch(declared):
                errors.append(f"{path}: @version must be semver, got {declared!r}")
            if path.stem != declared:
                errors.append(f"{path}: filename version {path.stem!r} != @version {declared!r}")
            if meta.get("profile") != family.name:
                errors.append(f"{path}: @profile {meta.get('profile')!r} != family {family.name!r}")
            status = meta.get("status", "")
            if status not in ACTIVE_STATUSES:
                errors.append(f"{path}: @status must be active/superseded, got {status!r}")
            if status == "active":
                active.append(path)
            if SEMVER.fullmatch(declared):
                versions[path] = version_key(declared)
            relative = path.relative_to(root).as_posix()
            if relative in sources and status != "active":
                errors.append(f"{path}: manifest references a non-active version")
        if len(active) != 1:
            errors.append(f"{family}: expected exactly one active version, found {len(active)}")
            return
        if versions:
            top = active[0]
            highest = max(versions, key=versions.get)
            if top != highest:
                errors.append(f"{family}: active version is not the highest version")
            relative = top.relative_to(root).as_posix()
            if relative not in sources:
                errors.append(f"{family}: active version is not referenced by the manifest")
            family_sources = [s for s in sources if s.startswith(f"profiles/{family.name}/")]
            for source in family_sources:
                if source != relative:
                    errors.append(f"{family}: manifest source {source!r} is not the active version")


def check_legacy_and_archive(root: Path, manifest: dict, errors: list[str]) -> None:
    sources = {entry.get("source") for entry in manifest.get("profiles", [])}
    legacy_dir = root / "legacy"
    if legacy_dir.is_dir():
        files = sorted(legacy_dir.glob("*.conf"))
        for path in files:
            meta = parse_metadata(path)
            if meta.get("status") != "frozen":
                errors.append(f"{path}: legacy files must be @status: frozen")
            if not meta.get("frozen-at"):
                errors.append(f"{path}: legacy files must carry @frozen-at")
            relative = path.relative_to(root).as_posix()
            if relative in sources:
                errors.append(f"{path}: legacy file must not be referenced by the manifest")
    archive_dir = root / "archive"
    if archive_dir.is_dir():
        for path in sorted(archive_dir.rglob("*.conf")):
            relative = path.relative_to(root).as_posix()
            if relative in sources:
                errors.append(f"{path}: archive file must not be referenced by the manifest")
            meta = parse_metadata(path)
            if meta.get("status") == "active":
                errors.append(f"{path}: archive file must not be active")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    root = Path(parser.parse_args().root).resolve()
    errors: list[str] = []
    manifest = load_manifest(root)
    check_profiles(root, manifest, errors)
    check_legacy_and_archive(root, manifest, errors)
    for message in errors:
        print(f"ERROR: {message}")
    print(f"Version check: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
