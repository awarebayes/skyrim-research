#!/usr/bin/env bash
# Stop the standing verifier machine, wait until it is stopped, and print the compute used.
#
#   boat_down.sh [--force]
#
# Refuses while any ~/tasks/<task-id>/.running marker exists, because another agent may still be
# working on the shared machine; --force stops anyway (use it only for markers you know are
# stale). A stop keeps the disk; it never deletes the machine.
set -euo pipefail
. "$(dirname "$0")/boat_lib.sh"

FORCE=0
[ "${1:-}" = --force ] && FORCE=1

LOOK=$(verifier_lookup)
read -r ID STATE <<<"$LOOK" || true
[ -n "${ID:-}" ] || die "no machine named $BOAT_VERIFIER_NAME"
case "$STATE" in
    stopped)
        say "$BOAT_VERIFIER_NAME ($ID) is already stopped"
        ;;
    *)
        if [ "$FORCE" = 0 ]; then
            BUSY=$(remote "$ID" 30 "ls -d $REMOTE_TASKS/*/.running 2>/dev/null | sed 's|/.running||; s|.*/||' || true")
            [ -z "$BUSY" ] || die "tasks still marked running: $(echo "$BUSY" | tr '\n' ' ')(use --force if stale)" 4
        fi
        say "stopping $BOAT_VERIFIER_NAME ($ID)"
        "$BOAT" stop "$ID" --json >/dev/null
        wait_state "$ID" stopped 300 || die "machine did not reach stopped; check \`boat info $ID\`"
        ;;
esac
echo "machine: $ID state=$(sandbox_field "$ID" state) usage_seconds_since_create=$(usage_seconds "$ID")"
compute_line
