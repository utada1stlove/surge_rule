#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).with_name("render-private-profiles.py")
SPEC = importlib.util.spec_from_file_location("render_private_profiles", MODULE_PATH)
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


TEMPLATE = """#!MANAGED-CONFIG __MANAGED_CONFIG_URL__ interval=86400 strict=false
[General]
dns-server = system
[Proxy]
[Proxy Group]
Proxy = select, policy-path=\"__SUBSTORE_URL__\", update-interval=86400
[Rule]
DOMAIN-SUFFIX,example.cn,DIRECT
FINAL,Proxy
"""


class RendererTests(unittest.TestCase):
    @staticmethod
    def fetch_fixture(url: str, timeout: int) -> str:
        del timeout
        if "sub.example" in url:
            return "Test Node = socks5, 127.0.0.1, 1080\n"
        return TEMPLATE

    def test_stage_and_activate_profiles_with_override(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            output_root = Path(temporary_dir) / "output"
            config = {
                "output_root": str(output_root),
                "public_base_url": "https://profiles.example/private",
                "timeout_seconds": 5,
            }
            secrets = {
                "default_substore_url": "https://sub.example/default",
                "profiles": {"simple": "https://sub.example/simple"},
            }
            manifest = {
                "version": 1,
                "profiles": [
                    {
                        "id": "main",
                        "template_url": "https://raw.example/main",
                        "output": "surge-main.conf",
                    },
                    {
                        "id": "simple",
                        "template_url": "https://raw.example/simple",
                        "output": "surge-simple.conf",
                    },
                ],
            }
            with mock.patch.object(renderer, "fetch_text", side_effect=self.fetch_fixture), mock.patch.object(
                renderer, "fetch_private_text", side_effect=self.fetch_fixture
            ):
                release, outputs = renderer.stage_release(config, secrets, manifest)
            self.assertEqual(outputs, ["surge-main.conf", "surge-simple.conf"])
            renderer.activate_release(output_root, release)
            current = output_root / "current"
            self.assertTrue(current.is_symlink())
            main = (current / "surge-main.conf").read_text(encoding="utf-8")
            simple = (current / "surge-simple.conf").read_text(encoding="utf-8")
            self.assertIn("https://sub.example/default", main)
            self.assertIn("https://sub.example/simple", simple)
            self.assertNotIn("__SUBSTORE_URL__", main + simple)
            metadata = json.loads((current / "release.json").read_text(encoding="utf-8"))
            self.assertEqual(metadata["outputs"], outputs)

    def test_invalid_final_does_not_create_release(self) -> None:
        broken = TEMPLATE.replace("FINAL,Proxy\n", "FINAL,Proxy\nDOMAIN,late.example,Proxy\n")
        with tempfile.TemporaryDirectory() as temporary_dir:
            config = {
                "output_root": temporary_dir,
                "public_base_url": "https://profiles.example/private",
            }
            secrets = {
                "default_substore_url": "https://sub.example/default",
                "profiles": {},
            }
            manifest = {
                "version": 1,
                "profiles": [
                    {
                        "id": "main",
                        "template_url": "https://raw.example/main",
                        "output": "surge-main.conf",
                    }
                ],
            }
            def fetch_broken(url: str, timeout: int) -> str:
                del timeout
                if "sub.example" in url:
                    return "Test Node = socks5, 127.0.0.1, 1080\n"
                return broken

            with mock.patch.object(renderer, "fetch_text", side_effect=fetch_broken), mock.patch.object(
                renderer, "fetch_private_text", side_effect=fetch_broken
            ):
                with self.assertRaises(renderer.RenderError):
                    renderer.stage_release(config, secrets, manifest)
            releases = Path(temporary_dir) / "releases"
            self.assertEqual(list(releases.iterdir()), [])

    def test_rejects_html_substore_response(self) -> None:
        with self.assertRaises(renderer.RenderError):
            renderer.validate_substore_payload("<!doctype html><html>error</html>")


if __name__ == "__main__":
    unittest.main()
