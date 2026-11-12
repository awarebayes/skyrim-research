---
name: boat-down
description: End the skyrim-research verifier session on Boat (stop machines A and B), refusing while tasks are still running, then flush the cost ledger and report compute and starts used. Use when the maintainer or orchestrator asks to shut down or stop the Boat verifiers, or to end a work session.
---

# boat-down

Only the maintainer, the orchestrator, or an Engineer whose brief says so runs this. Drafters never do.
Rules: `docs/boat-agent-guidelines.md`.

1. From the repository root run `python3 tools/verifier/session status`.
2. If it shows `tasks running:` with any task id, stop: name the tasks and ask the user whether
   they are finished or stale. Continue only if the user confirms, then add `--force` in step 3.
   Never force on your own judgement.
3. Run `python3 tools/verifier/session down` (or `--only a` / `--only b` when the user asked to
   stop one machine, for example to leave A running for other agents). Exit 4 means tasks are
   still marked running: go back to step 2.
4. Run `python3 tools/cost_ledger.py flush`.
5. Report: machines stopped, seconds billed per machine this session, session overhead seconds
   queued for the ledger, starts made this session, and the starts budget line.
6. If a stop fails or a machine stays `stopping`, report it; never use `boat stop --force`
   (it discards data written since the last snapshot).

Never run `boat billing`, delete machines, or print machine ids or tokens.
