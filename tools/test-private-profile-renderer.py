#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "deploy/private-profile-service/render-private-profiles.py"
SPEC = importlib.util.spec_from_file_location("render_private_profiles", RENDERER)
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)


TEMPLATE = """#!MANAGED-CONFIG __MANAGED_CONFIG_URL__ interval=86400 strict=false
[General]
dns-server = system
[Proxy]
[Proxy Group]
Proxy = select, policy-path="__SUBSTORE_URL__", update-interval=86400
[Rule]
DOMAIN-SUFFIX,example.cn,DIRECT
FINAL,Proxy
"""

PLAIN_TEMPLATE = """#!MANAGED-CONFIG __MANAGED_CONFIG_URL__ interval=86400 strict=false
[General]
[Proxy]
[Proxy Group]
Proxy = select, DIRECT
[Rule]
FINAL,Proxy
"""

SUBSTORE = "Test Node = socks5, 127.0.0.1, 1080\n"


def resolved(text: str) -> str:
    return (
        text.replace("__MANAGED_CONFIG_URL__", "https://profiles.example/private/surge-simple.conf")
        .replace("__SUBSTORE_URL__", "https://sub.example/default")
    )


def make_fetch(template_map: dict[str, str], substore: str = SUBSTORE):
    def fetch(url: str, timeout: int, private: bool = False) -> str:
        del timeout, private
        url = urllib.parse.urlsplit(url)._replace(query="").geturl()
        if "manifest.example" in url:
            return json.dumps({"version": 1, "profiles": [
                {"id": "simple", "template_url": "https://raw.example/simple", "output": "surge-simple.conf"},
                {"id": "surge", "template_url": "https://raw.example/surge", "output": "surge.conf"},
            ]})
        if "sub.example" in url:
            return substore
        return template_map[url]

    return fetch


class RendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.output_root = Path(self.temporary.name) / "output"
        self.config = {
            "output_root": str(self.output_root),
            "public_base_url": "https://profiles.example/private",
            "manifest_url": "https://manifest.example/manifest.json",
            "timeout_seconds": 5,
        }
        self.secrets = {
            "default_substore_url": "https://sub.example/default",
            "profiles": {"simple": "https://sub.example/simple"},
        }
        self.manifest = {
            "version": 1,
            "profiles": [
                {"id": "simple", "template_url": "https://raw.example/simple", "output": "surge-simple.conf"},
                {"id": "surge", "template_url": "https://raw.example/surge", "output": "surge.conf"},
            ],
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_config(self) -> tuple[Path, Path]:
        config_path = Path(self.temporary.name) / "config.json"
        secrets_path = Path(self.temporary.name) / "secrets.json"
        config_path.write_text(json.dumps(self.config), encoding="utf-8")
        secrets_path.write_text(json.dumps(self.secrets), encoding="utf-8")
        os.chmod(secrets_path, 0o600)
        return config_path, secrets_path

    def test_stage_injects_provenance_and_replaces_sources(self) -> None:
        template_map = {
            "https://raw.example/simple": TEMPLATE,
            "https://raw.example/surge": PLAIN_TEMPLATE,
        }
        with mock.patch.object(renderer, "fetch", side_effect=make_fetch(template_map)):
            directory, outputs = renderer.stage(self.config, self.secrets, self.manifest)
        self.assertEqual(outputs, ["surge-simple.conf", "surge.conf"])
        simple = (directory / "surge-simple.conf").read_text(encoding="utf-8")
        surge = (directory / "surge.conf").read_text(encoding="utf-8")
        self.assertIn("https://sub.example/simple", simple)
        self.assertNotIn("__SUBSTORE_URL__", simple)
        self.assertIn("# @rendered-from: simple\n", simple)
        self.assertIn("# @rendered-at: 20", simple)
        self.assertNotIn("__MANAGED_CONFIG_URL__", simple + surge)
        metadata = json.loads((directory / "release.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["outputs"], outputs)
        self.assertEqual(metadata["sources"]["surge-simple.conf"]["source"], "simple")

    def test_comment_with_section_name_is_not_a_second_header(self) -> None:
        text = resolved(TEMPLATE).replace(
            "[General]\n",
            "[General]\n# 该文件的 [Proxy] 与 [Rule] 出现在注释里，不应被当成第二个段头。\n",
        )
        renderer.validate_profile(text, "simple", "https://profiles.example/private/surge-simple.conf")

    def test_real_duplicate_section_is_rejected(self) -> None:
        text = resolved(TEMPLATE) + "\n[General]\ndns-server = 1.1.1.1\n"
        with self.assertRaises(renderer.RenderError) as context:
            renderer.validate_profile(text, "simple", "https://profiles.example/private/surge-simple.conf")
        self.assertIn("found 2", str(context.exception))

    def test_invalid_final_is_rejected_before_activation(self) -> None:
        broken = PLAIN_TEMPLATE.replace("FINAL,Proxy\n", "FINAL,Proxy\nDOMAIN,late.example,Proxy\n")
        template_map = {
            "https://raw.example/simple": TEMPLATE,
            "https://raw.example/surge": broken,
        }
        with mock.patch.object(renderer, "fetch", side_effect=make_fetch(template_map)):
            with self.assertRaises(renderer.RenderError):
                renderer.stage(self.config, self.secrets, self.manifest)
        self.assertEqual(list((self.output_root / "releases").iterdir()), [])

    def test_rejects_html_substore_response(self) -> None:
        with self.assertRaises(renderer.RenderError):
            renderer.validate_substore("<!doctype html><html>error</html>")

    def test_main_success_then_broken_template_keeps_current(self) -> None:
        config_path, secrets_path = self.write_config()
        template_map = {
            "https://raw.example/simple": TEMPLATE,
            "https://raw.example/surge": PLAIN_TEMPLATE,
        }
        with mock.patch.object(renderer, "fetch", side_effect=make_fetch(template_map)):
            with mock.patch.object(sys, "argv", ["render", "--config", str(config_path), "--secrets", str(secrets_path)]):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    code = renderer.main()
        self.assertEqual(code, 0)
        current = self.output_root / "current"
        self.assertTrue(current.is_symlink())
        first_release = current.resolve()
        rendered = (current / "surge.conf").read_text(encoding="utf-8")
        self.assertIn("# @rendered-from: surge\n", rendered)

        broken = PLAIN_TEMPLATE.replace("FINAL,Proxy\n", "FINAL,Proxy\nDOMAIN,late.example,Proxy\n")
        template_map["https://raw.example/surge"] = broken
        with mock.patch.object(renderer, "fetch", side_effect=make_fetch(template_map)):
            with mock.patch.object(sys, "argv", ["render", "--config", str(config_path), "--secrets", str(secrets_path)]):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    code = renderer.main()
        self.assertEqual(code, 1)
        self.assertEqual(current.resolve(), first_release)

    def test_main_retries_stale_manifest(self) -> None:
        config_path, secrets_path = self.write_config()
        template_map = {
            "https://raw.example/simple": TEMPLATE,
            "https://raw.example/surge": PLAIN_TEMPLATE,
        }
        manifest_calls = {"count": 0}

        def fetch(url: str, timeout: int, private: bool = False) -> str:
            del timeout, private
            url = urllib.parse.urlsplit(url)._replace(query="").geturl()
            if "manifest.example" in url:
                manifest_calls["count"] += 1
                if manifest_calls["count"] == 1:
                    return json.dumps({"version": 1, "profiles": [
                        {"id": "old", "template_url": "https://raw.example/old", "output": "surge.conf"},
                    ]})
                return json.dumps({"version": 1, "profiles": [
                    {"id": "simple", "template_url": "https://raw.example/simple", "output": "surge-simple.conf"},
                    {"id": "surge", "template_url": "https://raw.example/surge", "output": "surge.conf"},
                ]})
            if "raw.example/old" in url:
                raise renderer.DownloadError(
                    "template download failed: HTTP Error 404: Not Found (https://raw.example/old)"
                )
            if "sub.example" in url:
                return SUBSTORE
            return template_map[url]

        with mock.patch.object(renderer, "fetch", side_effect=fetch), mock.patch.object(renderer.time, "sleep") as sleep:
            with mock.patch.object(sys, "argv", ["render", "--config", str(config_path), "--secrets", str(secrets_path)]):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    code = renderer.main()
        self.assertEqual(code, 0)
        self.assertEqual(manifest_calls["count"], 2)
        sleep.assert_called_once()
        current = self.output_root / "current"
        self.assertTrue(current.is_symlink())
        self.assertTrue((current / "surge.conf").is_file())


if __name__ == "__main__":
    unittest.main()
