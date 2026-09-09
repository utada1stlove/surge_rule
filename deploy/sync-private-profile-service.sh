#!/usr/bin/env bash
# One-shot sync for the private profile service on the EB VPS.
#
# Usage: deploy/sync-private-profile-service.sh
# Precondition: the current branch is pushed; the renderer fetches the manifest
# and templates from the public GitHub repository.
#
# The script stages the exact files that are also installed by CI, ships them
# over SSH, runs the installer (which keeps existing config/secrets), triggers
# an immediate render, verifies status, and compares the remote renderer
# checksum against this repository copy so version drift fails loudly.

set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$repo_root"

host=${1:-eb}
staging=$(mktemp -d "${TMPDIR:-/tmp}/surge-profile-sync.XXXXXX")
bundle="$staging.tar.gz"
trap 'rm -rf "$staging"; rm -f "$bundle"' EXIT

cp deploy/private-profile-service/render-private-profiles.py "$staging/"
cp tools/surge-profilectl.py "$staging/"
cp deploy/systemd/surge-profile-render.service deploy/systemd/surge-profile-render.timer "$staging/"
cp deploy/config/config.json.example deploy/config/secrets.json.example "$staging/"
cp deploy/nginx/surge-profile-location.conf.example "$staging/"
cp deploy/install-private-profile-service.sh "$staging/"

local_renderer_sha=$(sha256sum "$staging/render-private-profiles.py" | awk '{print $1}')

tar -C "$staging" -czf "$bundle" .
scp -q "$bundle" "$host:/tmp/surge-profile-sync-bundle.tar.gz"

remote_report=$(ssh "$host" '
  set -eu
  rm -rf /tmp/surge-profile-deploy
  mkdir -p /tmp/surge-profile-deploy
  tar -xzf /tmp/surge-profile-sync-bundle.tar.gz -C /tmp/surge-profile-deploy
  /tmp/surge-profile-deploy/install-private-profile-service.sh /tmp/surge-profile-deploy >/tmp/surge-profile-install.log
  surge-profilectl update
  surge-profilectl status --check
  echo "remote renderer sha256: $(sha256sum /usr/local/libexec/surge-profile/render-private-profiles.py | awk "{print \$1}")"
')

echo "$remote_report"
remote_renderer_sha=$(echo "$remote_report" | sed -n 's/.*remote renderer sha256: //p')

if [ "$remote_renderer_sha" != "$local_renderer_sha" ]; then
  echo "ERROR: remote renderer sha256 does not match the repository copy" >&2
  exit 1
fi

echo "sync ok: repository renderer and VPS copy are identical ($local_renderer_sha)"
