# Guide for a contributor's coding agent

You are a coding agent helping an **external contributor** match one function of Skyrim Special
Edition. This file is all you need. Do not follow the orchestrator, Boat or verifier-session
instructions elsewhere in this repository (`AGENTS.md` "Multi-agent execution",
`docs/boat-agent-guidelines.md`, `tools/verifier/attempt|confirm|session`): they are for the
project's own machines. Never use Boat. Everything below runs on the contributor's computer.

Drive one tool, `tools/contrib.py` (Windows: `py tools\contrib.py`), always with `--json`. Each call
prints one JSON object with `ok`, `exit_code`, `error` and `next` (the one next action). Do what
`next` says. Exit codes: 0 ok, 1 a check failed, 2 usage, 3 compile failed, 4 unit or include
problem, 5 input missing, 6 claimed by someone else, 7 a person must decide, 8 offline.

## The two human decisions

Stop and ask the person, quoting what the tool printed, only for these:

1. **The path to their `SkyrimSE.exe`**, when `setup` could not find it in a Steam library
   (exit 5, `game executable`). Also tell them, once, that you will read a listing of their own
   copy of the game locally and that this sends parts of it to your AI provider; continue only if
   they agree.
2. **Microsoft's licence** for the Visual Studio 2017 Build Tools (exit 7 with a `licence` field).
   Show them the link. Pass `--accept-microsoft-license` only after they say they accept it. Never
   accept it yourself.

On Apple silicon, Rosetta 2 has its own Apple licence: if `setup` reports `rosetta`, ask the person
to run `softwareupdate --install-rosetta` themselves. Package installs need no decision: pass
`--yes`. If a package manager needs a password (`sudo`), the tool prints the command; ask the
person to run it.

## The loop

```sh
python3 tools/contrib.py --json --yes go [--exe "<path>"] [--accept-microsoft-license] \
    --drafted-by "<person>, assisted by <your model id>"
```

`go` = `setup` (idempotent; installs Wine and msitools off Windows, LLVM, the community headers,
the pinned MSVC 19.16.27054 toolset and SDK from Microsoft's servers, then compiles and compares a
function the project already matched as a self-test) + `next` + `claim` + `start`. Run it again
after any fix; finished steps are skipped. Then:

1. Read the private pack named in the `packs` field: `bytes.txt` (offsets, bytes with relocated
   fields as `..`, and each call or data target with its public name) and `listing.txt`
   (disassembly, when LLVM is installed). These files never leave the machine: do not paste them
   into issues, pull requests, commit messages or any public place.
2. Read `docs/matching-cookbook.md` once (skip its advice to read the FNV sibling), and
   `docs/drafter-card.md` for the source and label rules (its Boat, attempt-budget and sibling parts
   do not apply to you).
3. Edit the unit the skeleton created (`reconstruction/<area>/<Class>.h` and `.cpp`). Declare only
   the members the function needs, at the offsets the listing uses. Names come from the community
   headers in `.local/sources/` (search them; label `COMMUNITY(...)`), `GUESS` only for names you
   invent. Do not use the FNV decompilation (not yet allowed for external contributors).
4. `python3 tools/contrib.py --json compare`. Read `functions[].reason`, `first_mismatch`, sizes and
   `hint`; the private `side-by-side.txt` under `private_dir` shows target and candidate together.
   If `bind` lists `UNBOUND`, add the hint it names to the task's `bind-hints.json` with an RVA from
   the pack. Revise and repeat. Stop after about ten tries without progress on the first mismatch
   and tell the person; `release 0x<rva> --reason "<one line>"` gives the function back.
5. On PASS: `python3 tools/contrib.py --json submit --dry-run`, fix any `blockers`, then
   `submit`. It needs a fork remote; if it reports none, ask the person to fork the repository on
   GitHub and add it (`git remote add fork https://github.com/<them>/skyrim-research.git`).

A pass on this machine is not acceptance. Tell the person that the project re-runs the comparison
on its own two hosts and a Reviewer checks the source before the function counts as matched.

## The game executable

The pinned file is in `builds/target.json` (Steam, 1.7.104.0, Steam build 24914197). If `setup`
reports another build, tell the person; do not try to obtain or modify game files yourself. The
legitimate routes are the person's own account through Valve's official clients: the Steam app, or
SteamCMD (`setup --steamcmd` installs it; on Ubuntu it needs the multiverse repository and i386
architecture enabled). `setup` prints the SteamCMD steps; the person types their login into
SteamCMD themselves. Never handle, store or type Steam credentials. Whether Steam's current build
is the pinned one is not known to the project; `setup --exe` checks the hash afterwards.

## Claims

`claim` opens a GitHub issue titled `claim: <build> 0x<rva> <name>` (with `gh` signed in) or prints
a prefilled link for the person to click. Another open issue or pull request naming the same RVA
blocks it (exit 6): pick another with `next`. A claim lapses after 14 days without activity;
`claim --take-over` then takes it with a comment. Without network, `claim --offline-ok` lets you
start, but nobody else can see the claim until you run `claim` again online.

## What is untested

The helper's install and compile steps have not been run with the real compiler on any platform
(see `CONTRIBUTING.md`, "Status of the platforms"). If a step fails, report the JSON output (it
holds no game data) in an issue rather than working around a check.
