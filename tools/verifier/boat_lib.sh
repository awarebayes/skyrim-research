# Shared helpers for boat_up.sh, boat_run.sh and boat_down.sh. Source it; do not run it.
# Settings (environment):
#   BOAT_CLI            Boat CLI binary (default: boat on PATH)
#   BOAT_VERIFIER_NAME  name of the standing verifier machine (default: sr-verifier-msvc141)
# The machine is looked up by name so no account-specific id is stored in the repository.

BOAT=${BOAT_CLI:-boat}
BOAT_VERIFIER_NAME=${BOAT_VERIFIER_NAME:-sr-verifier-msvc141}
# Auto-update would change the CLI under a running script; update deliberately instead.
export BOAT_NO_UPDATE=1
REMOTE_HOME=/home/user
REMOTE_SR=$REMOTE_HOME/sr
REMOTE_TASKS=$REMOTE_HOME/tasks
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

say() { printf '== %s\n' "$*" >&2; }
die() { printf 'error: %s\n' "$1" >&2; exit "${2:-1}"; }

command -v "$BOAT" >/dev/null 2>&1 || die "Boat CLI not found: set BOAT_CLI"
command -v python3 >/dev/null 2>&1 || die "python3 is required"

# Prints "<id> <state>" for the machine named $BOAT_VERIFIER_NAME, or nothing if absent.
# Fails if the name is ambiguous, because acting on the wrong machine could stop someone's work.
verifier_lookup() {
    "$BOAT" list --all --json | python3 -I -c '
import json, sys
name = sys.argv[1]
rows = [s for s in json.load(sys.stdin)["sandboxes"] if s.get("name") == name]
if len(rows) > 1:
    sys.exit("more than one sandbox is named %r: %s" % (name, " ".join(s["id"] for s in rows)))
for s in rows:
    print(s["id"], s["state"])
' "$BOAT_VERIFIER_NAME"
}

sandbox_field() {  # sandbox_field <id> <field>
    "$BOAT" info "$1" --json | python3 -I -c '
import json, sys
v = json.load(sys.stdin)["sandbox"].get(sys.argv[1])
print("" if v is None else v)
' "$2"
}

wait_state() {  # wait_state <id> <state> <max-seconds>
    local id=$1 want=$2 max=$3 start now st
    start=$(date +%s)
    while :; do
        st=$(sandbox_field "$id" state)
        [ "$st" = "$want" ] && return 0
        now=$(date +%s)
        [ $((now - start)) -ge "$max" ] && { say "still $st after ${max}s"; return 1; }
        sleep 2
    done
}

# Runs a shell command line on the machine and relays its output; exits like the command.
# Uses --stream so long jobs show progress and the exit code survives (exec prints JSON when
# stdout is not a terminal, which is how agents call it).
remote() {  # remote <id> <timeout-seconds> <command-line>
    "$BOAT" exec "$1" --stream --json --timeout "$2" -- "$3" | python3 -I -c '
import json, sys
code = 1
for line in sys.stdin:
    try:
        f = json.loads(line)
    except ValueError:
        sys.stderr.write(line)
        continue
    t = f.get("type")
    if t == "stdout":
        sys.stdout.write(f.get("data", "")); sys.stdout.flush()
    elif t == "stderr":
        sys.stderr.write(f.get("data", "")); sys.stderr.flush()
    elif t == "exit":
        if f.get("timedOut"):
            sys.stderr.write("remote command timed out\n"); code = 124
        else:
            code = f.get("exitCode") if f.get("exitCode") is not None else 1
    elif "error" in f:
        sys.stderr.write("boat exec: %s\n" % f.get("error")); code = 1
sys.exit(code)
'
}

# Trial and plan counters, so every task can record compute before and after.
compute_line() {
    "$BOAT" limits --json | python3 -I -c '
import json, sys
d = json.load(sys.stdin)
print("compute: trialComputeUsedSeconds=%s creditUsedSeconds=%s activeSandboxes=%s billingStatus=%s"
      % (d.get("trialComputeUsedSeconds"), d.get("creditUsedSeconds"),
         d.get("activeSandboxes"), d.get("billingStatus")))
'
}

usage_seconds() {  # usage_seconds <id>
    "$BOAT" usage "$1" --json | python3 -I -c 'import json,sys; print(json.load(sys.stdin)["seconds"])'
}
