#!/usr/bin/env bash
# Bring up the standing verifier machine and prove its compiler is the pinned one.
#
#   running  -> reuse it (prints its auto-stop deadline)
#   stopped  -> boat resume (seconds; the disk with the toolchain comes back)
#   missing  -> refuse, unless BOAT_ALLOW_CREATE=1: then create a no-env machine and run
#               setup_boat_machine.sh (minutes, and it accepts the Build Tools licence)
#
# Then copies this checkout's tools/ (tracked and unignored files only) to ~/sr/tools and checks
# the compiler binaries against tools/verifier/pinned.sha256. Last stdout line:
#   BOAT_VERIFIER_ID=<id>
#
# Settings: BOAT_CLI, BOAT_VERIFIER_NAME (see boat_lib.sh); BOAT_TTL auto-stop seconds applied
# on resume or create (default 3600; the trial refuses more than 7200).
set -euo pipefail
. "$(dirname "$0")/boat_lib.sh"

TTL=${BOAT_TTL:-3600}
compute_line >&2

# Starts budget check and log (tools/verifier/starts.py); exit 5 when the reserve would be used.
take_start() {
    python3 "$(dirname "$0")/starts.py" take --reason "$1" --machine "$BOAT_VERIFIER_NAME" || exit 5
}

LOOK=$(verifier_lookup)
read -r ID STATE <<<"$LOOK" || true
case "${STATE:-missing}" in
    ready|idle|running)
        say "$BOAT_VERIFIER_NAME ($ID) already running; auto-stop at $(sandbox_field "$ID" archiveAfter)"
        ;;
    stopped|stopping|error)
        take_start "boat_up.sh resume"
        say "resuming $BOAT_VERIFIER_NAME ($ID) with auto-stop ${TTL}s"
        "$BOAT" resume "$ID" --ttl "$TTL" --json >/dev/null
        say "ready; auto-stop at $(sandbox_field "$ID" archiveAfter)"
        ;;
    provisioning|provisioned|starting|cloning)
        say "$ID is $STATE; waiting"
        wait_state "$ID" ready 120 || die "machine did not become ready"
        ;;
    missing)
        [ "${BOAT_ALLOW_CREATE:-0}" = 1 ] || die "no machine named $BOAT_VERIFIER_NAME. Check \`boat list --all\`; to build a new one from the recipe set BOAT_ALLOW_CREATE=1"
        take_start "boat_up.sh create"
        say "creating $BOAT_VERIFIER_NAME (no account secrets, auto-stop ${TTL}s)"
        ID=$("$BOAT" new --no-env --type default --ttl "$TTL" --name "$BOAT_VERIFIER_NAME" --json \
            | python3 -I -c '
import json, sys
# Read to the end: stopping at the first ready line closes the pipe while boat new is still
# writing, and the SIGPIPE exit then aborts this script under pipefail with a machine created.
found = None
for line in sys.stdin:
    try:
        f = json.loads(line)
    except ValueError:
        continue
    if found is None and (f.get("event") == "ready" or (f.get("id") and f.get("state") == "ready")):
        found = f["id"]
if found:
    print(found)
')
        [ -n "$ID" ] || die "boat new did not report a ready machine"
        ;;
    *)
        die "unexpected state $STATE for $ID"
        ;;
esac

say "copying tools/ to $REMOTE_SR/tools"
"$BOAT" push "$ID" "$REPO/tools" --to "$REMOTE_SR/tools" --json >/dev/null

if [ "${STATE:-missing}" = missing ]; then
    say "running setup_boat_machine.sh (several minutes)"
    remote "$ID" 0 "cd $REMOTE_SR && tools/verifier/setup_boat_machine.sh $REMOTE_HOME/msvc"
fi

say "checking compiler binaries against pinned.sha256"
remote "$ID" 120 "cd $REMOTE_HOME/msvc/VC/Tools/MSVC/*/bin/Hostx64/x64 && sha256sum -c $REMOTE_SR/tools/verifier/pinned.sha256" >&2 \
    || die "toolchain does not match pinned.sha256; do not use this machine for verification" 3
echo "BOAT_VERIFIER_ID=$ID"
