# Guide for a contributor's coding agent

You are a coding agent helping an **external contributor** match one function of Skyrim Special
Edition. This file is all you need. Do not follow the orchestrator, Boat or verifier-session
instructions elsewhere in this repository (`AGENTS.md` "Multi-agent execution",
`docs/boat-agent-guidelines.md`, `tools/verifier/attempt|confirm|session`): they are for the
project's own machines. Never use Boat. Everything below runs on the contributor's computer.

Drive one tool, `tools/contrib.py` (Windows: `.\sr.cmd`, which finds Python 3.11+ or unpacks a
pinned private copy), always with `--json`. Each call prints one JSON object with `ok`, `exit_code`, `error` and `next` (the one next action). Do what
`next` says. Exit codes: 0 ok, 1 a check failed, 2 usage, 3 compile failed, 4 unit or include
problem, 5 input missing, 6 claimed by someone else, 7 a person must decide, 8 offline.

## The two human decisions

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
    --drafted-by "<person>, assisted by <your model id>"
```

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
2. Read `docs/matching-cookbook.md` once, and `docs/drafter-card.md` for the source and label rules
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
   the pack. Revise and repeat. Stop after about ten tries without progress on the first mismatch
   and tell the person; `release 0x<rva> --reason "<one line>"` gives the function back.
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

`claim` opens a GitHub issue titled `claim: <build> 0x<rva> <name>` (with `gh` signed in) or prints
a prefilled link for the person to click; after they file it, run `claim` again so it is recorded
(`--github-user <their login>` when `gh` is not signed in). Another open issue or pull request
naming the same RVA blocks it (exit 6): pick another with `next`. If two claims are filed at the
same time, the older one wins and `claim` withdraws the newer. A claim lapses after 14 days without
activity; `claim --take-over` then takes it with a comment. Without network, `claim --offline-ok`
lets you start, but nobody else can see the claim until you run `claim` again online.

## What is tested

macOS on Apple silicon ran the whole path with the real compiler: `setup`, the self-test (same
code-section hash as the project's verifier hosts), `start` and `compare` on an unmatched function.
Linux and Windows are not yet run (see `CONTRIBUTING.md`, "Status of the platforms"). If a step
fails, report the `--redact` JSON output (it holds no game data) in an issue rather than working
around a check.
