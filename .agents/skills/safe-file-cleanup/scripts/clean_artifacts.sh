#!/usr/bin/env bash
set -euo pipefail

dry_run=false
if [[ "${1:-}" == "--dry-run" ]]; then
  dry_run=true
  shift
fi
target="${1:-.}"
target="$(cd -- "$target" && pwd)"
case "$target" in
  /|"$HOME")
    echo "refusing broad cleanup target: $target" >&2
    exit 2
    ;;
esac

mapfile -d '' files < <(find "$target" -type f \( -name '*.aux' -o -name '*.log' -o -name '*.out' -o -name '*.toc' -o -name '*.fls' -o -name '*.fdb_latexmk' -o -name '*.synctex.gz' \) -print0)
mapfile -d '' caches < <(find "$target" -type d -name '__pycache__' -print0)

if (( ${#files[@]} == 0 && ${#caches[@]} == 0 )); then
  echo "no known build intermediates under $target"
  exit 0
fi

printf '%s\n' "cleanup candidates under $target:"
printf '%s\n' "${files[@]}" "${caches[@]}"
if [[ "$dry_run" == true ]]; then
  exit 0
fi

for file in "${files[@]}"; do rm -f -- "$file"; done
for cache in "${caches[@]}"; do rm -rf -- "$cache"; done
echo "cleanup complete"
