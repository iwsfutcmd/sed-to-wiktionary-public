#!/bin/sh
# Mirror this repo's history to the public repo with every *.pdf removed from all commits.
# Usage: scripts/sync_public.sh <public-remote-url>   (mirrors the checked-out commit; force-push, since the mirror is derived)
set -eu
url=$1
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
git clone --quiet --no-local --no-tags "$(git rev-parse --show-toplevel)" "$work/mirror"
cd "$work/mirror"
git filter-repo --quiet --force --path-glob '*.pdf' --invert-paths --refs HEAD
git push --force "$url" HEAD:refs/heads/main
