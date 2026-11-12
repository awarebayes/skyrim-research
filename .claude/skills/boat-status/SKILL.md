---
name: boat-status
description: Show the skyrim-research verifier session on Boat - machine states, time left before auto-stop, running task markers, starts used and left, compute this session, and disk-retention warnings. Read-only; starts and stops nothing.
---

# boat-status

1. From the repository root run `python3 tools/verifier/session status`.
2. Report its lines: each machine's state and time to auto-stop, `tasks running`, starts used
   and left (day, hour), seconds billed this session, and every `WARNING` line.
3. A retention warning (stopped 10 days or more) needs a resume/stop cycle before day 14:
   suggest `/boat-up` with `--only <a|b>` followed by `/boat-down` with the same `--only`.
   Do not run it without the user's go-ahead.

This skill never starts, extends or stops a machine.
