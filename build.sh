#!/bin/bash
# Build the "Hacked" font in a podman container.
#
# Usage: ./build.sh [--rebuild-image]
#
# Builds the builder image if missing (the only step that downloads anything),
# then runs the font build offline in a throwaway container. Output goes to
# dist/ next to this script. Edit hacked.conf to change the glyph picks.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
IMAGE=localhost/hacked-builder:latest
DIST="$HERE/dist"

command -v podman >/dev/null || { echo "podman is not installed" >&2; exit 1; }

if [[ "${1:-}" == "--rebuild-image" ]] || ! podman image exists "$IMAGE"; then
    echo "== Building image $IMAGE"
    old_id="$(podman image inspect --format '{{.Id}}' "$IMAGE" 2>/dev/null || true)"
    podman build --pull=missing -t "$IMAGE" -f "$HERE/Containerfile" "$HERE"
    # A rebuild leaves the previous image untagged; remove it so only one copy remains.
    new_id="$(podman image inspect --format '{{.Id}}' "$IMAGE")"
    if [[ -n "$old_id" && "$old_id" != "$new_id" ]]; then
        podman rmi "$old_id" >/dev/null || true
    fi
fi

mkdir -p "$DIST"
# Rootless podman maps container root to the calling user, so output files are owned by you.
podman run --rm --network=none \
    -v "$HERE/container:/work/container:ro,Z" \
    -v "$HERE/hacked.conf:/config/hacked.conf:ro,Z" \
    -v "$DIST:/out:Z" \
    "$IMAGE"

echo
echo "Fonts written to $DIST:"
ls -1 "$DIST"
