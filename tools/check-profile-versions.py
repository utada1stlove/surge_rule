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
- The active version must have a snapshot of its own, and that snapshot may
  only differ from the entry file on the # @status line. Rollback is
  forward-only: a restored snapshot becomes the body of a new version, it is
  never flipped back to @status: active.
- Families keep at most three distinct versions; older releases must be archived.
- A family directory holds nothing but .conf files and CHANGELOG.md, and its
  only subdirectories are version snapshot directories.
- Manifest sources must exist, must point at the entry file, and template_url
  (the path the VPS actually fetches) must resolve to the same file.
- Files under legacy/ must be frozen and must NOT be referenced by the manifest.
- Files under archive/ must not be referenced by the manifest.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit


SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
META_RE = re.compile(r"^#\s+@(\S+):\s*(.*)$")
STATUS_RE = re.compile(r"^#\s+@status:")
SNAPSHOT_DIR_RE = re.compile(r"^version (\d+)$")
ACTIVE_STATUSES = {"active", "superseded"}
MAX_VERSIONS_PER_FAMILY = 3
ALLOWED_FAMILY_FILES = {"CHANGELOG.md"}


def version_key(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def body_lines(path: Path) -> list[str]:
    """File content minus @status, the single line a snapshot may differ on."""
    lines = path.read_text(encoding="utf-8").splitlines()
    return [line for line in lines if not STATUS_RE.match(line)]


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


def check_family_tree(family: Path, errors: list[str]) -> None:
    """Reject what the .conf scanners would walk straight past: strays and odd dirs."""
    for path in sorted(family.rglob("*")):
        if path.is_dir():
            if path.parent == family and not SNAPSHOT_DIR_RE.fullmatch(path.name):
                errors.append(f"{path}: family subdirectories must be named 'version <major>'")
            continue
        if path.suffix != ".conf":
            if path.parent != family or path.name not in ALLOWED_FAMILY_FILES:
                errors.append(f"{path}: only .conf files and CHANGELOG.md belong in a family directory")
            continue
        if path.parent == family:
            continue
        snapshot_dir = SNAPSHOT_DIR_RE.fullmatch(path.parent.name)
        if snapshot_dir and SEMVER.fullmatch(path.stem):
            major = path.stem.split(".")[0]
            if snapshot_dir.group(1) != major:
                errors.append(f"{path}: snapshot {path.stem} belongs in version {major}")


def check_manifest(root: Path, manifest: dict, errors: list[str]) -> None:
    """The VPS fetches template_url while everything else reads source; they must agree."""
    seen: dict[str, str] = {}
    for entry in manifest.get("profiles", []):
        profile_id = str(entry.get("id", "?"))
        source = entry.get("source")
        if not isinstance(source, str) or not source:
            errors.append(f"manifest {profile_id}: missing source")
            continue
        if not (root / source).is_file():
            errors.append(f"manifest {profile_id}: source {source!r} does not exist in the repository")
        url_path = urlsplit(str(entry.get("template_url", ""))).path
        if not url_path.endswith("/" + source):
            errors.append(
                f"manifest {profile_id}: template_url {entry.get('template_url')!r} does not point at {source!r}"
            )
        output = str(entry.get("output", ""))
        if output in seen:
            errors.append(f"manifest: output {output!r} is shared by {seen[output]} and {profile_id}")
        seen[output] = profile_id


def check_profiles(root: Path, manifest: dict, errors: list[str]) -> None:
    sources = {entry.get("source") for entry in manifest.get("profiles", [])}
    families = sorted(path for path in (root / "profiles").iterdir() if path.is_dir())
    if not families:
        errors.append("profiles/: no family directories found")
        return
    for family in families:
        check_family_tree(family, errors)
        entries, snapshots = split_family_files(family)
        if not entries:
            errors.append(f"{family}: no .conf files")
            continue
        active: list[Path] = []
        declared: dict[Path, str] = {}
        snapshots_by_version: dict[str, Path] = {}
        for path in entries + snapshots:
            is_snapshot = path.parent != family
            meta = parse_metadata(path)
            version = meta.get("version", "")
            if not SEMVER.fullmatch(version):
                errors.append(f"{path}: @version must be semver, got {version!r}")
            if is_snapshot and SEMVER.fullmatch(version):
                snapshots_by_version.setdefault(version, path)
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
        # The entry version must be archived alongside the releases it replaced, so
        # that a snapshot diff always answers "what changed" for the live config too.
        entry_version = declared[active[0]]
        if SEMVER.fullmatch(entry_version):
            current = snapshots_by_version.get(entry_version)
            if current is None:
                errors.append(
                    f"{family}: no snapshot for the active version {entry_version}; copy the entry file into version <major>/"
                )
            elif body_lines(current) != body_lines(active[0]):
                errors.append(
                    f"{family}: snapshot {current.name} differs from the entry file on more than the @status line"
                )


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
    check_manifest(root, manifest, errors)
    check_profiles(root, manifest, errors)
    check_legacy_and_archive(root, manifest, errors)
    for message in errors:
        print(f"ERROR: {message}")
    print(f"Version check: {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
