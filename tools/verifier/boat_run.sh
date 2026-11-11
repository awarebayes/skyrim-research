#!/usr/bin/env bash
# Run one task's command on the standing verifier machine (bring it up first with boat_up.sh).
#
#   boat_run.sh <task-id> <local-dir> <command>
#
# On the machine the task gets its own directory, ~/tasks/<task-id>, so several agents can share
# one machine without touching each other's files:
#   in/   a fresh copy of <local-dir> (replaced on every run)
#   out/  emptied before the run; the command writes its results here
# The command runs under bash in ~/tasks/<task-id> with TASK_DIR, IN, OUT, SR (repository tools)
# and MSVC (toolchain root) set. Afterwards out/ is copied back to
# .local/boat-results/<task-id>/ (or $BOAT_RESULTS_DIR/<task-id>, which must stay under .local/).
# Exits with the command's exit code; 124 if it hit BOAT_RUN_TIMEOUT (seconds, default 600;
# 0 means no limit).
#
# Copy only inputs the recorded gates allow onto the machine; never credentials.
set -euo pipefail
. "$(dirname "$0")/boat_lib.sh"

[ $# -eq 3 ] || die "usage: boat_run.sh <task-id> <local-dir> <command>" 2
TASK=$1 SRC=$2 CMD=$3
[[ "$TASK" =~ ^[a-z0-9][a-z0-9.-]{0,63}$ ]] || die "task id must match [a-z0-9][a-z0-9.-]*" 2
[ -d "$SRC" ] || die "not a directory: $SRC" 2
TIMEOUT=${BOAT_RUN_TIMEOUT:-600}

RESULTS_ROOT=${BOAT_RESULTS_DIR:-$REPO/.local/boat-results}
mkdir -p "$RESULTS_ROOT"
RESULTS_ROOT=$(cd "$RESULTS_ROOT" && pwd -P)
case "$RESULTS_ROOT/" in
    "$(cd "$REPO" && pwd -P)/.local/"*) ;;
    *) die "results must stay under .local/ (got $RESULTS_ROOT)" 2 ;;
esac
DEST=$RESULTS_ROOT/$TASK

LOOK=$(verifier_lookup)
read -r ID STATE <<<"$LOOK" || true
case "${STATE:-missing}" in
    ready|idle|running) ;;
    *) die "$BOAT_VERIFIER_NAME is ${STATE:-missing}; run boat_up.sh first" ;;
esac

T=$REMOTE_TASKS/$TASK
remote "$ID" 60 "rm -rf $T/in $T/out && mkdir -p $T/out" >&2

say "upload $SRC -> $ID:$T/in"
# boat push skips gitignored files (it would copy nothing from .local/), so use scp. Without
# COPYFILE_DISABLE the macOS tar adds AppleDouble ._ files and the upload fails.
COPYFILE_DISABLE=1 "$BOAT" scp -r "$SRC" "$ID:$T/in" >/dev/null 2>"$RESULTS_ROOT/.scp-$TASK.log" \
    || { cat "$RESULTS_ROOT/.scp-$TASK.log" >&2; die "upload failed"; }

say "run in $T (timeout ${TIMEOUT}s)"
QCMD=$(printf '%q' "$CMD")
# .running marks the task as in progress so boat_down.sh does not stop the machine under it.
set +e
remote "$ID" "$TIMEOUT" "cd $T && touch .running && TASK_DIR=$T IN=$T/in OUT=$T/out SR=$REMOTE_SR MSVC=$REMOTE_HOME/msvc bash -c $QCMD; rc=\$?; rm -f .running; exit \$rc"
RC=$?
set -e

say "fetch $ID:$T/out -> $DEST"
rm -rf "$DEST.part"
if "$BOAT" scp -r "$ID:$T/out" "$DEST.part" >/dev/null 2>"$RESULTS_ROOT/.scp-$TASK.log"; then
    rm -rf "$DEST" && mv "$DEST.part" "$DEST"
else
    cat "$RESULTS_ROOT/.scp-$TASK.log" >&2
    say "fetch failed; results remain on the machine in $T/out"
    [ "$RC" -ne 0 ] || RC=1
fi
rm -f "$RESULTS_ROOT/.scp-$TASK.log"
say "exit $RC"
exit "$RC"
