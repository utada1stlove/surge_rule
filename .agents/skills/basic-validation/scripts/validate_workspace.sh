#!/usr/bin/env bash
set -euo pipefail

target="$(cd -- "${1:-.}" && pwd)"
status=0

if command -v git >/dev/null 2>&1 && git -C "$target" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git -C "$target" diff --check || status=1
fi

while IFS= read -r -d '' file; do
  python3 -m json.tool "$file" >/dev/null || { echo "invalid JSON: $file" >&2; status=1; }
done < <(find "$target" -type f -name '*.json' -print0)

if command -v pdfinfo >/dev/null 2>&1; then
  while IFS= read -r -d '' file; do
    pdfinfo "$file" >/dev/null || { echo "unreadable PDF: $file" >&2; status=1; }
  done < <(find "$target" -type f -name '*.pdf' -print0)
fi

if find "$target" -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.fls' -o -name '*.fdb_latexmk' -o -name '*.synctex.gz' \) -print -quit | grep -q .; then
  echo "build intermediates remain; run safe-file-cleanup" >&2
  status=1
fi

exit "$status"
