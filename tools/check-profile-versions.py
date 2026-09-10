#!/usr/bin/env python3
"""Enforce the profile versioning contract used by this repository.

Rules:
- Every # @profile / # @version / # @status header must be present and coherent;
  @profile has to equal the family directory name.
- Each family has exactly one entry file directly under profiles/<family>/, and
  it is the file the VPS renders. It is named after the manifest output (for
  example profiles/surge/surge.conf) so the rendered path never changes, which
  means its filename does not have to equal @version. A file whose stem already
  looks like a version (1.0.0.conf) must still match @version.
- Released snapshots live in profiles/<family>/version <major>/<semver>.conf.
  They must be named after @version and must be @status: superseded.
- Exactly one active file per family; it must be the highest version and it
  must be the version referenced by config/private-profile-templates.json.
- Families keep at most three distinct versions; older releases must be archived.
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


def split_family_files(family: Path) -> tuple[list[Path], list[Path]]:
    """Return (entry files, snapshots) for one family directory."""
    entries: list[Path] = []
    snapshots: list[Path] = []
    for path in sorted(family.rglob("*.conf")):
        (entries if path.parent == family else snapshots).append(path)
    return entries, snapshots


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
        entries, snapshots = split_family_files(family)
        if not entries:
            errors.append(f"{family}: no .conf files")
            continue
        active: list[Path] = []
        declared: dict[Path, str] = {}
        for path in entries + snapshots:
            is_snapshot = path.parent != family
            meta = parse_metadata(path)
            version = meta.get("version", "")
            if not SEMVER.fullmatch(version):
                errors.append(f"{path}: @version must be semver, got {version!r}")
            # The entry file keeps a stable path, so only its name is free-form
            # when it does not look like a version; snapshots always must match.
            if (is_snapshot or SEMVER.fullmatch(path.stem)) and path.stem != version:
                errors.append(f"{path}: filename version {path.stem!r} != @version {version!r}")
            if meta.get("profile") != family.name:
                errors.append(f"{path}: @profile {meta.get('profile')!r} != family {family.name!r}")
            status = meta.get("status", "")
            if status not in ACTIVE_STATUSES:
                errors.append(f"{path}: @status must be active/superseded, got {status!r}")
            if status == "active":
                if is_snapshot:
                    errors.append(f"{path}: snapshot versions must be @status: superseded")
                    continue
                active.append(path)
            declared[path] = version
            relative = path.relative_to(root).as_posix()
            if relative in sources and status != "active":
                errors.append(f"{path}: manifest references a non-active version")
        distinct = {version for version in declared.values() if SEMVER.fullmatch(version)}
        if len(distinct) > MAX_VERSIONS_PER_FAMILY:
            errors.append(
                f"{family}: {len(distinct)} versions kept (max {MAX_VERSIONS_PER_FAMILY}); archive older releases"
            )
        if len(active) != 1:
            errors.append(f"{family}: expected exactly one active version, found {len(active)}")
            return
        if distinct:
            top = active[0]
            highest = max(version_key(value) for value in distinct)
            if version_key(declared[top]) != highest:
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
