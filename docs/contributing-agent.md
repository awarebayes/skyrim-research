# Guide for a contributor's coding agent

You are a coding agent helping an **external contributor** match one function of Skyrim Special
Edition. This file is all you need. Do not follow the orchestrator, Boat or verifier-session
instructions elsewhere in this repository (`AGENTS.md` "Multi-agent execution",
`docs/boat-agent-guidelines.md`, `tools/verifier/attempt|confirm|session`): they are for the
project's own machines. Never use Boat, the project's internal verifier hosts or its runner tools.
Everything below runs on the contributor's computer.

Drive one tool, `tools/contrib.py` (Windows: `.\sr.cmd`, which finds Python 3.11+ or unpacks a
pinned private copy), always with `--json`. Each call prints one JSON object with `ok`, `exit_code`, `error` and `next` (the one next action). Do what
`next` says. Exit codes: 0 ok, 1 a check failed, 2 usage, 3 compile failed, 4 unit or include
problem, 5 input missing, 6 claimed by someone else, 7 a person must decide, 8 offline.

## When to ask the person

Stop and ask the person, quoting what the tool printed, only for these:

1. **The path to their `SkyrimSE.exe`**, when `setup` could not find it in a Steam library
   (exit 5, `game executable`).
2. **Microsoft's licence** for the Visual Studio 2017 Build Tools (exit 7 with a `licence` field).
   Show them the link. Pass `--accept-microsoft-license` only after they say they accept it. Never
   accept it yourself.

Before you read any pack, ask once: reading a listing made from their own copy of the game sends
parts of it to your AI provider. That is their decision and their responsibility, under their
provider's terms; the project grants no rights in the game. Continue only if they agree. Nothing
from a pack ever goes into the repository, a pull request, an issue or CI.

Their system may add questions of its own, which only they answer: on Apple silicon, Rosetta 2 has
its own Apple licence (if `setup` reports `rosetta`, they run `softwareupdate --install-rosetta`);
a package manager may want their password (`sudo`; the tool prints the command for them to run);
winget on Windows asks them to accept its package source terms (pass
`--accept-winget-source-agreements` only after they have). Package installs themselves need no
decision: pass `--yes`.

## The loop

```sh
python3 tools/contrib.py --json --yes go [--exe "<path>"] [--accept-microsoft-license] \
    [--profile cheap|full] --drafted-by "<person>, assisted by <your model id>"
```

**Profiles.** `cheap` (the default) is for small, cheap models (Haiku- or Luna-class): read
`docs/drafter-card-small.md`, sections "Rules for small functions" and "Result lines" (where it
says `attempt`, run `contrib.py compare`; its queue, budget and handoff parts do not apply to
you), and stop after 6 compare runs without a pass. `full` is for Sonnet-class models: read
`docs/drafter-card.md` and `docs/matching-cookbook.md` (step 2 below), and stop after about 10.
`start` prints the documents, the limit and a rough cost line; `python3 tools/profiles.py` prints
them all. Rough cost: `cheap` about $0.01-0.03 of model usage per passing function (an estimate),
`full` about $0.18 per function for drafting (measured on the project's own runs). `cheap` is
the default because small models pass the same comparator gate on small functions; a profile
never changes what counts as a match. If `compare` says to stop under `cheap`, the function may
still be within reach with `--profile full`.

`go` = `setup` (idempotent; installs Wine and msitools off Windows, LLVM, the community headers,
the FNV decompilation and its index, the pinned MSVC 19.16.27054 toolset and SDK from Microsoft's
servers, then compiles and compares a function the project already matched as a self-test) +
`next` + `claim` + `start`. Run it again after any fix; finished steps are skipped. When you show
the person output to post publicly, add `--redact` (it replaces their checkout and home paths).
Then:

1. Read the private pack named in the `packs` field: `bytes.txt` (offsets, bytes with relocated
   fields as `..`, and each call or data target with its public name) and `listing.txt`
   (disassembly, when LLVM is installed). These files never leave the machine: do not paste them
   into issues, pull requests, commit messages or any public place.
2. Read the documents your profile names (`start` prints them under `read`). Under `full`:
   `docs/matching-cookbook.md` once, and `docs/drafter-card.md` for the source and label rules
   (its Boat and attempt-budget parts do not apply to you; its sibling rules do).
3. Edit the unit the skeleton created (`reconstruction/<area>/<Class>.h` and `.cpp`). Declare only
   the members the function needs, at the offsets the listing uses. Names come from the community
   headers in `.local/sources/` (search them; label `COMMUNITY(...)`), `GUESS` only for names you
   invent. If `start` reported a `sibling` file, it points at the same-named method in the FNV
   decompilation (`.local/sources/fnv_decomp`): read it for shape and names, never for offsets,
   layouts or slots (another game, older engine, 32-bit). Label what you take
   `SIBLING(momusdigital/fnv_decomp@91e1b6e8, no-licence)`, and add a
   `Sibling source: momusdigital/fnv_decomp@91e1b6e8 <path>:<line>` header line for a reused body.
4. `python3 tools/contrib.py --json compare`. Read `functions[].reason`, `first_mismatch`, sizes and
   `hint`; the private `side-by-side.txt` under `private_dir` shows target and candidate together.
   If `bind` lists `UNBOUND`, add the hint it names to the task's `bind-hints.json` with an RVA from
   the pack. Revise and repeat. Stop when `next` says to (your profile's limit), or after about ten
   tries without progress on the first mismatch, and tell the person; `release 0x<rva> --reason "<one line>"` gives the function back.
5. On PASS: `python3 tools/contrib.py --json submit --dry-run`, fix any `blockers`, then
   `submit`. It needs a fork remote; if it reports none, ask the person to fork the repository on
   GitHub and add it (`git remote add fork https://github.com/<them>/skyrim-research.git`).

A pass on this machine is not acceptance. Tell the person that the project re-runs the comparison
on its own two hosts and a Reviewer checks the source before the function counts as matched.

## The game executable

The pinned file is in `builds/target.json` (Steam, 1.7.104.0, Steam build 24914197). If `setup`
reports another build, tell the person; do not try to obtain or modify game files yourself. Their
own purchased copy fetched with their own account through Valve's clients is fine: the Steam app,
or SteamCMD (`setup --steamcmd` installs it with Homebrew; on Debian or Ubuntu it prints
`sudo apt install steamcmd` for the person, because that package shows Steam's licence for them to
accept). `setup` prints the SteamCMD steps (the whole game, or only the executable's depot, about
38 MB) and, in a terminal, offers to start SteamCMD there; the person types their login, password
and guard code into SteamCMD themselves. Never handle, store or type Steam credentials, and never
read Steam's account files. A Steam install made in October 2026 delivered exactly the pinned build;
`setup` checks the hash of whatever it finds.

## Claims

`claim` opens an assigned GitHub issue with the `claim` label. A claim may cover one function,
hundreds of functions, several classes or half-open address ranges. For example:

```sh
python3 tools/contrib.py claim 0x1000 0x2000
python3 tools/contrib.py claim --class Actor --class TESForm
python3 tools/contrib.py claim --list functions.txt --range 0x1000-0x2000
```

List files hold one RVA per line, with optional names after it and `#` comment lines. A range
includes every function starting at or above its start and below its end. Titles look like
`claim: <build id> <classes or range> (<N> functions)`. Bodies have a `skyrim-claim-v1 <build id>`
fenced block, one `0x<rva> [public name]` or `0x<start>-0x<end>` per line. Bodies stay below
60,000 characters; large claims split into numbered parts. Names come only from the committed
inventory, never from a local listing. Old single-function issue titles remain recognized.

`next` excludes other people's live claims, including ranges and the project's own published
queue claims. Any partial overlap with another person's live issue or PR is refused (exit 6)
and names the issue. Overlap with your own claim is allowed. If claims race, the older issue
wins and the newer claim is withdrawn. Claims lapse after 24 hours without activity (an issue
update, comment or linked pull request); `claim --take-over` records a takeover comment. With no network,
`claim --offline-ok` records an unpublished local claim: run it again online to make it visible.
Without signed-in `gh`, the helper prints prefilled issue links; file them, assign yourself and
run `claim` again (`--github-user <login>` identifies you). Releasing one member of a batch does
not close the entire batch: edit its scope or close the issue on GitHub.

`python3 tools/claims.py list` shows live claims and accepted counts; `check 0x<rva> ...` checks
specific addresses. Reads use an ignored `.local/claims-cache.json` with a ten-minute TTL;
`--refresh` forces a refresh. Offline project queue commands warn and use the stale cache.
Project `publish` and `sync` renew live claims after 12 hours of inactivity while their work
remains active in the pipeline or is a planned family member.

## What is tested

On macOS (Apple silicon) `setup`, the self-test (same code-section hash as the one the project
recorded), `start` and `compare` on an unmatched function ran with the real pinned compiler.
`claim` and `submit` against GitHub and the one-command `go` have not been run live. Linux and
Windows are not yet run (see `CONTRIBUTING.md`, "Status of the platforms"). If a step
fails, report the `--redact` JSON output (it holds no game data) in an issue rather than working
around a check.
