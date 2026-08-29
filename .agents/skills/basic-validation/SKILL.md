---
name: basic-validation
description: Run lightweight, deterministic delivery checks for documents, structured data, and repository changes. Use before handing off, committing, or publishing non-trivial work.
---

# Basic Validation

Run `scripts/validate_workspace.sh [project-directory]`. It checks git diff
whitespace, generated-artifact leakage, JSON parseability, and PDF readability
when those files exist. Then run the project's own tests or build commands.

For this Surge repository, also run
`./.agents/skills/surge-profile-lint/scripts/lint_surge_profiles.py [project-directory]`
after editing a public `.conf` Profile or `rules/**/*.list` file.

Validation must match the changed surface. A passing generic check never
replaces a domain validator, typecheck, lint, or artifact inspection.
