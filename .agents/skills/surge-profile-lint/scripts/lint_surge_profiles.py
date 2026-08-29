#!/usr/bin/env python3
"""Offline consistency checks for this repository's public Surge configuration."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


BUILTIN_POLICIES = {"DIRECT", "REJECT", "REJECT-DROP", "REJECT-TINYGIF", "REJECT-DICT", "REJECT-IMG"}
FIRST_PARTY_RAW_PREFIX = "https://raw.githubusercontent.com/utada1stlove/surge_rule/main/"
SECRET_ASSIGNMENT = re.compile(r"(?i)\b(?:password|token|secret|psk|private[_-]?key|uuid)\s*=\s*(?!__)[^\s#]+")
PRIVATE_IP = re.compile(r"(?<![\d.])(?:10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)(?:\d{1,3}\.){1,2}\d{1,3}(?![\d.])")


def effective_lines(path: Path):
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if line and not line.startswith(("#", ";")):
            yield number, line


def profile_sections(path: Path):
    sections: dict[str, list[tuple[int, str]]] = {}
    current: str | None = None
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip()
            sections.setdefault(current, [])
        elif current and line and not line.startswith(("#", ";")):
            sections[current].append((number, line))
    return sections


def rule_policy(parts: list[str]) -> str | None:
    if parts[0].upper() == "FINAL":
        return parts[1] if len(parts) >= 2 else None
    return parts[2] if len(parts) >= 3 else None


def scan_public_text(path: Path, warnings: list[str], *, check_private_ip: bool) -> None:
    for number, line in effective_lines(path):
        if SECRET_ASSIGNMENT.search(line):
            warnings.append(f"{path}:{number}: possible credential assignment")
        if check_private_ip and PRIVATE_IP.search(line):
            warnings.append(f"{path}:{number}: private-network address in public configuration")


def lint_profile(path: Path, root: Path, errors: list[str], warnings: list[str]) -> None:
    sections = profile_sections(path)
    if "Rule" not in sections:
        errors.append(f"{path}: missing [Rule] section")
        return

    groups = set()
    for number, line in sections.get("Proxy Group", []):
        if "=" not in line:
            errors.append(f"{path}:{number}: malformed proxy group")
            continue
        groups.add(line.split("=", 1)[0].strip())

    rules = sections["Rule"]
    final_positions = [index for index, (_, line) in enumerate(rules) if line.split(",", 1)[0].upper() == "FINAL"]
    if len(final_positions) != 1:
        errors.append(f"{path}: [Rule] must contain exactly one FINAL (found {len(final_positions)})")
    elif final_positions[0] != len(rules) - 1:
        errors.append(f"{path}:{rules[final_positions[0]][0]}: FINAL must be the last effective rule")

    for number, line in rules:
        parts = [part.strip() for part in line.split(",")]
        policy = rule_policy(parts)
        if policy and policy not in groups and policy not in BUILTIN_POLICIES:
            errors.append(f"{path}:{number}: policy {policy!r} is not a Proxy Group or built-in policy")
        if parts[0].upper() == "RULE-SET" and len(parts) >= 2 and parts[1].startswith(FIRST_PARTY_RAW_PREFIX):
            relative = parts[1].removeprefix(FIRST_PARTY_RAW_PREFIX)
            if not (root / relative).is_file():
                errors.append(f"{path}:{number}: first-party Rule Set has no local file: {relative}")
    scan_public_text(path, warnings, check_private_ip=True)


def lint_rule_set(path: Path, warnings: list[str]) -> None:
    seen: dict[str, int] = {}
    for number, line in effective_lines(path):
        previous = seen.get(line)
        if previous:
            warnings.append(f"{path}:{number}: duplicate of effective rule at line {previous}")
        else:
            seen[line] = number
    # RFC1918 entries are normal in a public direct-routing Rule Set.
    scan_public_text(path, warnings, check_private_ip=False)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default=".", help="repository root (default: current directory)")
    root = Path(parser.parse_args().root).resolve()
    profiles = sorted(root.glob("*.conf"))
    rule_sets = sorted((root / "rules").rglob("*.list")) if (root / "rules").is_dir() else []
    errors: list[str] = []
    warnings: list[str] = []
    if not profiles:
        errors.append(f"{root}: no top-level .conf Profiles found")
    if not rule_sets:
        errors.append(f"{root}: no Rule Sets found under rules/")
    for profile in profiles:
        lint_profile(profile, root, errors, warnings)
    for rule_set in rule_sets:
        lint_rule_set(rule_set, warnings)
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    print(f"Surge lint: {len(profiles)} profile(s), {len(rule_sets)} Rule Set(s), {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
