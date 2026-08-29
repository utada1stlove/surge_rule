---
name: project-bootstrap
description: Initialize a lightweight Codex-ready project structure with AGENTS.md, planning, reports, and git-safe defaults. Use when starting a new project or adding the first reusable agent workflow.
---

# Project Bootstrap

Use `scripts/init_project.sh <target-directory>` to create only missing files.
It never overwrites an existing `AGENTS.md` without an explicit `--force`.

Start with the supplied minimal template, then add project-specific commands,
data rules, and publication constraints. Do not copy domain rules from another
project merely because its folder structure looks similar.
