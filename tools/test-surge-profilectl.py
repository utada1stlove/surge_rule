#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("surge-profilectl.py")
SPEC = importlib.util.spec_from_file_location("surge_profilectl", MODULE_PATH)
assert SPEC and SPEC.loader
controller = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(controller)


class ControllerTests(unittest.TestCase):
    def test_failed_update_restores_original_source(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            secrets_path = Path(temporary_dir) / "secrets.json"
            original = {
                "default_substore_url": "https://sub.example/old",
                "profiles": {},
            }
            changed = {
                "default_substore_url": "https://sub.example/new",
                "profiles": {},
            }
            controller.write_json_atomic(secrets_path, original)
            with mock.patch.object(controller, "update", return_value=1):
                result = controller.apply_source_change(secrets_path, original, changed)
            self.assertEqual(result, 1)
            restored = json.loads(secrets_path.read_text(encoding="utf-8"))
            self.assertEqual(restored, original)
            self.assertEqual(secrets_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
