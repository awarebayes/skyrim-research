# Instructions for all agents and contributors

## First read

Read `README.md`, `LEGAL.md`, `PROVENANCE.md`, `docs/verification.md` and
`docs/clean-room.md` before research or publication. Claude must read this file too;
`CLAUDE.md` imports it. This repository is independent of Mudcrab: never apply Mudcrab's
Cargo/build/cache instructions here or modify its checkout as part of a research task.

## Keep private inputs private

- Use `.local/` for legally obtained executables, toolchains, databases, raw decompiler output,
  traces, saves and generated objects. Never force-add ignored paths.
- No game files, binary bytes, disassembly, dumps, proprietary symbols/SDKs, leaked code or
  unlicensed copied code in commits, PRs, issues, logs, releases or CI artifacts.
- Do not upload game-derived material to an AI/cloud service without explicit owner authorization
  and assessment of the service terms. Permission to research locally is not permission to upload.
- Analyze your own legally obtained inputs. Do not download game binaries or unofficial PDBs,
  acquire cracks, or add copy-protection removal instructions/tools.
- Stop the affected publication if provenance is uncertain. Record the question without reproducing
  suspect content. Unrelated original tooling work may continue.

## Be precise about evidence

- The target is UNPINNED until `builds/target.json` has real metadata and a locally measured hash.
  Do not invent a version, checksum, compiler, address, test result, cost or completion denominator.
- Address identity is `(build id, RVA)`; never transfer an address between versions without proof.
- Every finding identifies sources, revisions, source exposure, method, limitations and confidence.
  Label inferred names as guesses. Preserve unknowns rather than filling them plausibly.
- Byte match, semantic equivalence, inferred behavior and layout-size agreement are different claims.
- Never mark a function `matched` until the matching gate in `docs/verification.md` is implemented
  and maintainer-enabled, then require a reviewed, reproducible report. Bootstrap CI checks only
  publication hygiene, metadata and site generation; it does NOT compare against the game.
- Progress comes only from `data/progress.json`; totals are derived, not manually entered into HTML.
  Unknown scope means no completion percentage. No dummy success records or fake history.

## Work safely and leave a usable handoff

- Claim a small issue before a long task. Record human owner, agent/model if used, exact build,
  reproduction command, outcome, blockers and next step. Do not launch extra agents unless asked.
- All shell commands run from this repo. Private command paths must stay in local configs.
- Keep ordinary CLI/tooling work on macOS; Windows Arm VM and live Skyrim/SKSE compatibility are
  unverified. Do not install a VM, change a game install or provision paid machines without scope.
- No broad staging: inspect `git diff`, then stage named files. Run `python3 tools/check.py --staged`
  immediately before committing. Never bypass a guard to ship suspect material.
- Before a PR/push run `python3 tools/check.py`, `python3 -m unittest discover -s tests -v`,
  and `python3 tools/build_site.py`. Review all staged text for provenance and secrets.
- PRs describe evidence and limitations. Do not claim CI proves legality or gameplay parity.
- Protect the research/implementation boundary. Do not port reconstructed functions into Mudcrab
  or declare a specification clean-room-safe just because it is prose or lives in another repo.
