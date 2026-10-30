#!/bin/sh
# Mirror this repo's history to the public repo with every *.pdf removed from all commits.
# Usage: scripts/sync_public.sh <public-remote-url> [ref=HEAD]   (the push is a force-push: the mirror is derived)
set -eu
url=$1; ref=${2:-HEAD}
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
git clone --quiet --no-local --no-tags "$(git rev-parse --show-toplevel)" "$work/mirror"
cd "$work/mirror"
git checkout --quiet "$(git -C "$OLDPWD" rev-parse "$ref")" 2>/dev/null || true
git filter-repo --quiet --force --path-glob '*.pdf' --invert-paths --refs HEAD
git push --force "$url" HEAD:refs/heads/main
