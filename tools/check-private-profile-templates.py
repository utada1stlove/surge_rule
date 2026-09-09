#!/usr/bin/env python3
"""Offline preflight for the private profile renderer.

Every manifest entry is validated against the same checks the VPS renderer
runs, using local templates and dummy placeholder values, so a template that
would break production is rejected before it is pushed.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDERER = ROOT / "deploy/private-profile-service/render-private-profiles.py"
SPEC = importlib.util.spec_from_file_location("render_private_profiles", RENDERER)
assert SPEC and SPEC.loader
renderer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(renderer)

WG_FIXTURES = {
    "__WG_PRIVATE_KEY__": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "__WG_SELF_IP__": "10.0.0.2",
    "__WG_SELF_IP_V6__": "fd00::2",
    "__WG_DNS_SERVER__": "10.0.0.1:53",
    "__WG_PEER_PUBLIC_KEY__": "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=",
    "__WG_ENDPOINT__": "192.0.2.1:51820",
    "__WG_ALLOWED_IPS__": "0.0.0.0/0,::/0",
    "__WG_KEEPALIVE__": "25",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=str(ROOT), help="repository root (default: current directory)")
    root = Path(parser.parse_args().root).resolve()
    manifest_path = root / "config/private-profile-templates.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    for entry in manifest.get("profiles", []):
        profile_id = entry.get("id")
        source = entry.get("source")
        if not source or (root / source).is_relative_to(root / "archive"):
            errors.append(f"{profile_id}: manifest source must exist outside archive/")
            continue
        path = root / source
        if not path.is_file():
            errors.append(f"{profile_id}: manifest source missing: {source}")
            continue
        template = path.read_text(encoding="utf-8")
        if template.count("__MANAGED_CONFIG_URL__") != 1:
            errors.append(f"{profile_id}: template needs exactly one managed URL placeholder")
            continue
        if template.count("__SUBSTORE_URL__") > 1:
            errors.append(f"{profile_id}: template needs at most one Sub-Store placeholder")
        rendered = template.replace("__MANAGED_CONFIG_URL__", f"https://managed.invalid/{entry.get('output')}")
        rendered = rendered.replace("__SUBSTORE_URL__", f"https://substore.invalid/{profile_id}")
        for token, value in WG_FIXTURES.items():
            rendered = rendered.replace(token, value)
        unresolved = sorted(set(renderer.PLACEHOLDER_RE.findall(rendered)))
        if unresolved:
            errors.append(f"{profile_id}: unresolved placeholders: {', '.join(unresolved)}")
        try:
            renderer.validate_profile(rendered, profile_id, f"https://managed.invalid/{entry.get('output')}")
        except renderer.RenderError as exc:
            errors.append(str(exc))
    for message in errors:
        print(f"ERROR: {message}")
    count = len(manifest.get("profiles", []))
    print(f"Template preflight: {count} manifest profile(s), {len(errors)} error(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
