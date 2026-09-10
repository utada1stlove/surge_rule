#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools/check-profile-versions.py"
SPEC = importlib.util.spec_from_file_location("check_profile_versions", MODULE)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


def profile_body(profile: str, version: str, status: str) -> str:
    return (
        f"#!MANAGED-CONFIG https://managed.invalid/{profile} interval=86400 strict=false\n"
        f"# @profile: {profile}\n"
        f"# @version: {version}\n"
        f"# @status: {status}\n"
        f"# @changed: 2026-09-09\n"
        "[General]\n"
        "[Proxy]\n"
        "[Proxy Group]\n"
        "[Rule]\n"
        "FINAL,Proxy\n"
    )


class VersionGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "config").mkdir()
        (self.root / "profiles").mkdir()
        (self.root / "legacy").mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_profile(self, family: str, version: str, status: str = "active") -> Path:
        family_dir = self.root / "profiles" / family
        family_dir.mkdir(exist_ok=True)
        path = family_dir / f"{version}.conf"
        path.write_text(profile_body(family, version, status), encoding="utf-8")
        return path

    def write_entry(self, family: str, name: str, version: str, status: str = "active") -> Path:
        """Write the file the VPS renders; its name is stable, not a version."""
        family_dir = self.root / "profiles" / family
        family_dir.mkdir(exist_ok=True)
        path = family_dir / f"{name}.conf"
        path.write_text(profile_body(family, version, status), encoding="utf-8")
        return path

    def write_snapshot(self, family: str, version: str, status: str = "superseded") -> Path:
        snapshot_dir = self.root / "profiles" / family / "version 1"
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        path = snapshot_dir / f"{version}.conf"
        path.write_text(profile_body(family, version, status), encoding="utf-8")
        return path

    def write_manifest(self, sources: list[str]) -> None:
        entries = []
        for index, source in enumerate(sources):
            family = source.split("/")[1]
            entries.append(
                {"id": family, "template_url": f"https://raw.example/{source}", "output": f"{family}.conf", "source": source}
            )
        (self.root / "config/private-profile-templates.json").write_text(
            json.dumps({"version": 1, "profiles": entries}, indent=2), encoding="utf-8"
        )

    def collect(self) -> list[str]:
        errors: list[str] = []
        gate.check_profiles(self.root, gate.load_manifest(self.root), errors)
        gate.check_legacy_and_archive(self.root, gate.load_manifest(self.root), errors)
        return errors

    def test_active_must_be_highest(self) -> None:
        self.write_profile("surge", "1.0.0")
        self.write_profile("surge", "1.0.1", "superseded")
        self.write_manifest(["profiles/surge/1.0.0.conf"])
        errors = self.collect()
        self.assertTrue(any("active version is not the highest version" in e for e in errors))

    def test_manifest_cannot_reference_superseded_version(self) -> None:
        self.write_profile("surge", "1.0.0")
        self.write_profile("surge", "1.0.1", "superseded")
        self.write_manifest(["profiles/surge/1.0.1.conf"])
        errors = self.collect()
        self.assertTrue(any("manifest references a non-active version" in e for e in errors))

    def test_happy_path_is_clean(self) -> None:
        self.write_profile("surge", "1.0.0", "superseded")
        self.write_profile("surge", "1.0.1")
        self.write_manifest(["profiles/surge/1.0.1.conf"])
        self.assertEqual(self.collect(), [])

    def test_filename_version_mismatch_fails(self) -> None:
        self.write_profile("surge", "1.0.0")
        path = self.root / "profiles/surge/1.0.0.conf"
        text = path.read_text(encoding="utf-8").replace("@version: 1.0.0", "@version: 1.0.1")
        path.write_text(text, encoding="utf-8")
        self.write_manifest(["profiles/surge/1.0.0.conf"])
        errors = self.collect()
        self.assertTrue(any("filename version" in e for e in errors))

    def test_too_many_versions_require_archive(self) -> None:
        for version in ("1.0.0", "1.0.1", "1.0.2", "1.0.3"):
            self.write_profile("surge", version, "active" if version == "1.0.3" else "superseded")
        self.write_manifest(["profiles/surge/1.0.3.conf"])
        errors = self.collect()
        self.assertTrue(any("archive older releases" in e for e in errors))

    def test_legacy_must_be_frozen_and_unreferenced(self) -> None:
        legacy = self.root / "legacy/old.conf"
        legacy.write_text(
            "#!MANAGED-CONFIG https://managed.invalid/old interval=86400 strict=false\n"
            "# @profile: old\n"
            "# @version: 1.0.0\n"
            "# @status: active\n"
            "[General]\n",
            encoding="utf-8",
        )
        self.write_manifest(["legacy/old.conf"])
        errors = self.collect()
        self.assertTrue(any("must be @status: frozen" in e for e in errors))
        self.assertTrue(any("legacy file must not be referenced" in e for e in errors))

    def test_stable_entry_with_version_snapshots_is_clean(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        self.write_snapshot("surge", "1.0.1")
        self.write_snapshot("surge", "1.0.2")
        self.write_entry("surge", "surge", "1.0.2")
        self.write_manifest(["profiles/surge/surge.conf"])
        self.assertEqual(self.collect(), [])

    def test_snapshot_may_not_be_active(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        self.write_snapshot("surge", "1.0.1", "active")
        self.write_entry("surge", "surge", "1.0.1")
        self.write_manifest(["profiles/surge/surge.conf"])
        errors = self.collect()
        self.assertTrue(any("snapshot versions must be @status: superseded" in e for e in errors))

    def test_snapshot_filename_must_match_version(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        snapshot = self.write_snapshot("surge", "1.0.1")
        snapshot.write_text(profile_body("surge", "1.0.2", "superseded"), encoding="utf-8")
        self.write_entry("surge", "surge", "1.0.2")
        self.write_manifest(["profiles/surge/surge.conf"])
        errors = self.collect()
        self.assertTrue(any("filename version '1.0.1' != @version '1.0.2'" in e for e in errors))

    def test_snapshots_count_towards_the_version_cap(self) -> None:
        for version in ("1.0.0", "1.0.1", "1.0.2"):
            self.write_snapshot("surge", version)
        self.write_entry("surge", "surge", "1.0.3")
        self.write_manifest(["profiles/surge/surge.conf"])
        errors = self.collect()
        self.assertTrue(any("4 versions kept (max 3)" in e for e in errors))

    def test_manifest_must_point_at_the_entry_file(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        self.write_entry("surge", "surge", "1.0.1")
        self.write_manifest(["profiles/surge/version 1/1.0.0.conf"])
        errors = self.collect()
        self.assertTrue(any("manifest source" in e for e in errors))
        self.assertTrue(any("active version is not referenced by the manifest" in e for e in errors))

    def test_archive_must_not_be_referenced(self) -> None:
        self.write_profile("surge", "1.0.0")
        archive = self.root / "archive"
        archive.mkdir()
        snapshot = archive / "surge-old.conf"
        snapshot.write_text(profile_body("surge", "0.9.0", "superseded"), encoding="utf-8")
        self.write_manifest(["profiles/surge/1.0.0.conf", "archive/surge-old.conf"])
        errors = self.collect()
        self.assertTrue(any("archive file must not be referenced" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
