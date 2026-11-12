---
name: boat-up
description: Start a verifier session on Boat for skyrim-research (machines A and B, sr-verifier-msvc141 and sr-verifier-b) with at most one start per machine, and report hashes, deadlines and the starts budget. Use when the maintainer or orchestrator asks to bring the Boat verifiers up, start a session, or before a batch of attempt/confirm work. Project-internal; not for external contributors.
---

# boat-up

Machines A and B were deleted (`docs/authorizations.md`, Notes); the local and ssh runners (`tools/verifier/runners.py`) replace them. Do not run this; tell the user instead.

Only the maintainer, the orchestrator, or an Engineer whose brief says so runs this. Drafters never do.
Rules: `docs/boat-agent-guidelines.md`. Never run `boat billing` or buy extra starts.

1. From the repository root, show the budget first: `python3 tools/verifier/starts.py status`
2. Run `python3 tools/verifier/session up` (add `--ttl <seconds>` if the user gave a duration;
   the trial maximum is 7200). Add `--create` only if the user agreed to build a missing B
   (one start, about 7 minutes, accepts the Build Tools licence).
3. Report to the user, from the command's output only:
   - each machine (A, B by name): how it came up (already running, resumed, created);
   - toolchain check (pinned.sha256) and image check (builds/target.json): `ok` or not;
   - the auto-stop deadline of each machine;
   - starts used and left for the day and the hour, before and after.
4. Exit 5 (starts reserve, or a full hour or minute window): say how many starts are left and
   that the rolling window frees them over time; do not retry in a loop, and pass `--force`
   only if the user explicitly agrees to use the reserve.
5. A failed hash check leaves that machine unverified: tell the user; never reinstall.
6. "no machine named ...": A is rebuilt only on the maintainer's decision; B with `--create`
   after the user agrees.

Do not print machine ids, tokens or private paths beyond what the command prints.
