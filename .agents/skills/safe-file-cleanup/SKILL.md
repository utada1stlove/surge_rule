---
name: safe-file-cleanup
description: Safely list and remove known build intermediates without deleting source or deliverable files. Use after TeX/PDF generation or other builds that leave temporary artifacts.
---

# Safe File Cleanup

Run `scripts/clean_artifacts.sh --dry-run DIRECTORY` first, then repeat without
`--dry-run` only after confirming targets. It removes only known intermediates:
TeX `.aux`, `.log`, `.out`, `.toc`, `.fls`, `.fdb_latexmk`, `.synctex.gz`,
plus Python cache
directories.

Never use it on `/`, a home directory, or an unresolved path. Finish with
`git status --short` to ensure only intended deliverables remain.
