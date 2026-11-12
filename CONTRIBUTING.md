# Contributing

The project rebuilds Skyrim Special Edition's code one function at a time: you write C++ that the
same Microsoft compiler turns into exactly the bytes of the game's function. No programming
background is needed if you let a coding agent (Claude Code, Codex, Gemini CLI, ...) do the work;
you supply the game and approve two things.

## Match one function

**You need:** a computer running Windows, macOS or Linux; Python 3.11 or newer and git; a GitHub
account; your own copy of Skyrim Special Edition **1.7.104.0 from Steam** (the exact file is pinned
in `builds/target.json`); about 5 GB of free disk. Everything else is installed for you.

```sh
git clone https://github.com/awarebayes/skyrim-research.git
cd skyrim-research
python3 tools/contrib.py go            # Windows: py tools\contrib.py go
```

`go` checks your machine, installs what is missing (Wine on macOS and Linux, LLVM, the pinned
Microsoft compiler from Microsoft's own servers), proves the setup on a function the project
already matched, picks a small unclaimed function, claims it on GitHub and creates its source file.
It stops and tells you the exact next command whenever a person is needed. Only two things are
ever asked of you:

1. **Where your `SkyrimSE.exe` is** (found automatically in a normal Steam library).
2. **Whether you accept Microsoft's licence** for the Visual Studio 2017 Build Tools, which the
   compiler download requires. Nothing accepts it on your behalf.

Then write the function (or ask your agent to) and run:

```sh
python3 tools/contrib.py compare       # compile + compare; repeat until PASS
python3 tools/contrib.py submit        # checks, commit, push to your fork, open the pull request
```

**With a coding agent:** open your agent in the cloned folder and say *"Help me match one function
in this repository. Follow docs/contributing-agent.md."* It runs the commands above itself.

**What happens after you submit.** Your pull request carries only your source files and a
sanitized summary (pass/fail, sizes, hashes). A local pass is not yet a match: the project
re-compiles and re-compares your source on two of its own machines, and a Reviewer checks that it
is plausible source with honest provenance. If both agree, the function is recorded as matched and
you are credited in the commit. If not, the reasons come back on your pull request.

**Status of the platforms.** The comparator, the local pack and the checks are pure Python and run
anywhere and have been run on macOS against the real game file. The pinned compiler recipe is the
one the project's own verifiers use on Linux (Ubuntu 24.04 with Wine), but this helper's install and
compile steps have not yet been run with the real compiler on any platform: on Linux, macOS (Wine)
and Windows (native) they are untested. Please report what happens on yours.

### The game executable

The comparator needs exactly the pinned file (`builds/target.json`: Steam, version 1.7.104.0,
Steam build 24914197). `doctor` reads your file's version and hash and tells you plainly if it is
another build. Use only your own copy through Valve's official clients: the Steam app on Windows,
or Valve's command-line client SteamCMD (also the route on macOS, where the Steam app cannot install
this Windows-only game). `setup --steamcmd` installs SteamCMD with your package manager and prints
the steps; you type your Steam login into SteamCMD yourself. This tool never sees, stores or passes
Steam credentials, never downloads the game itself, and the project gives no instructions for
third-party downloaders, cracks or DRM removal. If the build Steam delivers is not the pinned one,
`setup` says so; whether Steam still delivers 1.7.104.0 is not known to the project.

### Rules that the tools check for you

- Source files go in `reconstruction/<area>/<Class>.h` and `.cpp`, with the header comment the
  skeleton gives you. Label every name with its origin (`docs/drafter-card.md`). Write C++ a
  programmer could have written; no inline assembly, byte arrays or tricks to force bytes.
- Never paste or attach bytes, listings, disassembly or decompiler output anywhere public (issues,
  pull requests, comments, screenshots). They stay in `.local/` on your machine.
- Your coding agent reads the listing of your own copy of the game to do its work; that sends parts
  of it to your AI provider. That is your choice under your own agreements; the project uploads
  nothing.
- Do not use the FNV decompilation as a source for now: whether its reuse permission covers
  external contributors is not yet decided. Community headers (CommonLibSSE-NG, powerof3's
  CommonLibSSE, meh321's Address Library names) are fine with their labels.
- State who drafted the unit and which AI model helped (`--drafted-by`). You stay responsible for
  what your agent submits.

## Other ways to help

- **Names and labels.** Matched functions whose names or labels still have open findings show
  `open` in the `names` column of `reconstruction/INDEX.md`. Fixing a label comment against the
  pinned community headers (`python3 tools/check_labels.py <files>` after `contrib.py setup`) is
  re-accepted by the project without a new review when the compiled code is unchanged. Change
  comments and labels only, not code or declared names.
- **Platform reports.** Run `python3 tools/contrib.py doctor` and `setup` on your machine and open
  an issue with the output (it contains no game data) if something fails.
- **Documentation.** Unclear steps in this file or `docs/contributing-agent.md` are bugs.

## Project members and research contributions

Read `AGENTS.md`, `LEGAL.md`, `PROVENANCE.md` and `docs/verification.md` first. A human operator is
accountable for AI-assisted work; state assistance and source exposure. Do not submit material you
lack rights to contribute. The licensing scope is in `LICENSE`; there is no blanket relicensing of
recovered implementations or third-party material.

1. Pick or open a focused issue. State who is working on it and how long the claim lasts.
2. Pin the target and dependencies before making build-specific claims. Keep inputs in `.local/`.
3. Record the method and outcome with the research template, including failures and unknowns.
4. Update the work item in `data/progress.json`. Changes to GitHub issues do not silently update
   the report: commit the reviewed status so it has a reproducible source revision.
5. Stage named files and inspect their contents. Run:

```sh
python3 tools/check.py --staged
python3 tools/check.py
python3 -m unittest discover -s tests -v
python3 tools/build_site.py
```

Include these results in the PR, along with exact revisions and limitations. Do not attach
private outputs. The automated guard is defense in depth, not a secret scanner or legal review.
Use the PR checklist. A passed infrastructure check does not establish a byte match.

How an external pull request enters the acceptance pipeline is in `docs/contributor-intake.md`.

## Publication

Reconstructed source is published in this repository by engine area, per the maintainer's
decision in `LEGAL.md`. Each function is published only when accepted under the acceptance rule in
`docs/verification.md`: reproduced comparator pass, approval by a fresh Reviewer subagent that
checks plausibility and provenance, and integration. Do not ask the maintainer to review
individual functions; escalate only as that rule lists. Approving behavior specifications for
transfer to Mudcrab still needs the boundary review in `docs/clean-room.md`. Keep executable-building tools separate if pursued later,
with a fresh review of scope and publication policy. No such builder exists here today.
