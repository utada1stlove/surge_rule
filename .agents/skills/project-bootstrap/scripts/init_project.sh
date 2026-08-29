#!/usr/bin/env bash
set -euo pipefail

force=false
if [[ "${1:-}" == "--force" ]]; then
  force=true
  shift
fi
target="${1:-}"
if [[ -z "$target" ]]; then
  echo "usage: init_project.sh [--force] TARGET_DIRECTORY" >&2
  exit 2
fi

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
kit_root="$(cd -- "$script_dir/../../../.." && pwd)"
mkdir -p "$target/.agents/skills" "$target/.codex/agents" "$target/planning" "$target/reports"

agents_file="$target/AGENTS.md"
if [[ ! -e "$agents_file" || "$force" == true ]]; then
  cp "$kit_root/templates/AGENTS.md" "$agents_file"
  echo "created $agents_file"
else
  echo "kept existing $agents_file"
fi

if [[ ! -e "$target/.gitignore" ]]; then
  cp "$kit_root/.gitignore" "$target/.gitignore"
  echo "created $target/.gitignore"
fi
