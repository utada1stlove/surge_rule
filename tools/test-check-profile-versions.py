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
    """Body shared by the entry file and its snapshot; only @status may differ."""
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
        self.write_raw_manifest(entries)

    def write_raw_manifest(self, entries: list[dict]) -> None:
        (self.root / "config/private-profile-templates.json").write_text(
            json.dumps({"version": 1, "profiles": entries}, indent=2),
            encoding="utf-8",
        )

    def collect(self) -> list[str]:
        errors: list[str] = []
        manifest = gate.load_manifest(self.root)
        gate.check_manifest(self.root, manifest, errors)
        gate.check_profiles(self.root, manifest, errors)
        gate.check_legacy_and_archive(self.root, manifest, errors)
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
        self.write_snapshot("surge", "1.0.1")
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
        self.write_snapshot("surge", "1.0.3")
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

    def test_manifest_source_must_exist(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        self.write_snapshot("surge", "1.0.1")
        self.write_entry("surge", "surge", "1.0.1")
        # A rename that forgot the manifest leaves the VPS rendering an orphan path.
        self.write_manifest(["profiles/surge/surge.conf.bak"])
        errors = self.collect()
        self.assertTrue(any("does not exist in the repository" in e for e in errors))

    def test_archive_must_not_be_referenced(self) -> None:
        self.write_profile("surge", "1.0.0")
        archive = self.root / "archive"
        archive.mkdir()
        snapshot = archive / "surge-old.conf"
        snapshot.write_text(profile_body("surge", "0.9.0", "superseded"), encoding="utf-8")
        self.write_manifest(["profiles/surge/1.0.0.conf", "archive/surge-old.conf"])
        errors = self.collect()
        self.assertTrue(any("archive file must not be referenced" in e for e in errors))

    def build_stable_family(self, version: str = "1.0.1") -> None:
        """A family in the shape the publish flow leaves behind."""
        self.write_snapshot("surge", "1.0.0")
        self.write_snapshot("surge", version)
        self.write_entry("surge", "surge", version)
        self.write_manifest(["profiles/surge/surge.conf"])

    def test_active_version_needs_a_snapshot(self) -> None:
        self.write_entry("surge", "surge", "1.0.1")
        self.write_manifest(["profiles/surge/surge.conf"])
        errors = self.collect()
        self.assertTrue(any("no snapshot for the active version" in e for e in errors))

    def test_current_snapshot_must_match_the_entry_file(self) -> None:
        self.write_snapshot("surge", "1.0.0")
        self.write_entry("surge", "surge", "1.0.1")
        drifted = profile_body("surge", "1.0.1", "superseded")
        drifted = drifted.replace("[Rule]\n", "[Rule]\nHOST,added-later.example.com,DIRECT\n")
        self.write_snapshot("surge", "1.0.1").write_text(drifted, encoding="utf-8")
        self.write_manifest(["profiles/surge/surge.conf"])
        errors = self.collect()
        self.assertTrue(any("differs from the entry file" in e for e in errors))

    def test_rollback_travels_forward_as_a_new_version(self) -> None:
        # 1.0.2 broke something, so its body came back from 1.0.1 under a fresh number.
        reverted = profile_body("surge", "1.0.1", "superseded").replace("FINAL,Proxy", "FINAL,DIRECT")
        self.write_snapshot("surge", "1.0.1").write_text(reverted, encoding="utf-8")
        self.write_snapshot("surge", "1.0.2")
        rolled_back = reverted.replace("@version: 1.0.1", "@version: 1.0.3")
        self.write_snapshot("surge", "1.0.3").write_text(rolled_back, encoding="utf-8")
        entry = self.write_entry("surge", "surge", "1.0.3")
        entry.write_text(rolled_back.replace("@status: superseded", "@status: active"), encoding="utf-8")
        self.write_manifest(["profiles/surge/surge.conf"])
        self.assertEqual(self.collect(), [])

    def test_forward_only_rollback_leaves_snapshots_superseded(self) -> None:
        self.build_stable_family()
        old = self.root / "profiles/surge/version 1/1.0.0.conf"
        old.write_text(profile_body("surge", "1.0.0", "active"), encoding="utf-8")
        errors = self.collect()
        self.assertTrue(any("snapshot versions must be @status: superseded" in e for e in errors))

    def test_family_directory_rejects_stray_files(self) -> None:
        self.build_stable_family()
        (self.root / "profiles/surge/notes.txt").write_text("scratch\n", encoding="utf-8")
        errors = self.collect()
        self.assertTrue(any("only .conf files and CHANGELOG.md belong" in e for e in errors))

    def test_family_subdirectories_must_be_version_directories(self) -> None:
        self.build_stable_family()
        stray_dir = self.root / "profiles/surge/backup"
        stray_dir.mkdir()
        backup = stray_dir / "1.0.0.conf"
        backup.write_text(profile_body("surge", "1.0.0", "superseded"), encoding="utf-8")
        errors = self.collect()
        self.assertTrue(any("family subdirectories must be named" in e for e in errors))

    def test_snapshot_must_live_in_its_own_major_directory(self) -> None:
        self.build_stable_family()
        wrong_major = self.root / "profiles/surge/version 1/2.0.0.conf"
        wrong_major.write_text(profile_body("surge", "2.0.0", "superseded"), encoding="utf-8")
        errors = self.collect()
        self.assertTrue(any("snapshot 2.0.0 belongs in version 2" in e for e in errors))

    def test_template_url_must_point_at_the_source(self) -> None:
        self.build_stable_family()
        manifest_path = self.root / "config/private-profile-templates.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        # The old raw path 404s on the VPS while source still looks healthy.
        manifest["profiles"][0]["template_url"] = "https://raw.example/profiles/surge/1.0.0.conf"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        errors = self.collect()
        self.assertTrue(any("does not point at" in e for e in errors))

    def test_manifest_outputs_must_be_unique(self) -> None:
        self.build_stable_family()
        self.write_snapshot("simple", "1.0.0")
        self.write_entry("simple", "surge-simple", "1.0.0")
        self.write_raw_manifest(
            [
                {
                    "id": "surge",
                    "template_url": "https://raw.example/profiles/surge/surge.conf",
                    "output": "surge.conf",
                    "source": "profiles/surge/surge.conf",
                },
                {
                    "id": "simple",
                    "template_url": "https://raw.example/profiles/simple/surge-simple.conf",
                    "output": "surge.conf",
                    "source": "profiles/simple/surge-simple.conf",
                },
            ]
        )
        errors = self.collect()
        self.assertTrue(any("is shared by surge and simple" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
