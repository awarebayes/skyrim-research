# Anti-EU-bureaucracy policy

The project ships matched functions. Process exists only where it prevents a false match or a
leak. Replicating EU-level bureaucracy is strictly forbidden: prefer efficient with less
regulation over right with strict regulation.

## The floor (the only things throughput never overrides)

1. A match is a comparator pass reproduced on two independent runner hosts, unchanged comparator.
2. The review the acceptance rule in `docs/verification.md` requires (for families: the template
   review and the sample, not every member).
3. Private inputs stay private (`AGENTS.md`, "Keep private inputs private").
4. No gate, comparator, validator or lint is weakened to get a pass.

Everything else is negotiable in favour of shipping.

## Rules

1. **Ship in bulk.** One push carries all approved work that is ready. Never split homogeneous
   approved work into per-function or per-group pushes or pull requests. A family of any size is
   at most three pushes: first members, sample, the rest. Thousands of functions in one commit
   is normal.
2. **No ceremony without a named rule.** No extra reviews, re-reviews of unchanged work,
   confirmation re-runs, pauses or checkpoints beyond what a written rule names. "To be safe" is
   not a reason.
3. **Decide, do not stop.** When instructions are silent or ambiguous, take the cheapest option
   that keeps the floor, record it in one line, and continue. A worker stops only for: a
   comparator non-reproduction, a binding or digest mismatch, a real provenance doubt, or a red
   `main` it cannot attribute.
4. **Resolve doubts at the lowest level.** A doubt that conservative labelling or a rerun can
   settle is settled that way. Only what a written rule sends to the maintainer goes to the
   maintainer.
5. **One push lane.** Small pushes fold into the next large one. An integrator that loses a
   race rebases and reruns only what the tooling requires.
6. **Short paperwork.** A handoff is a table and a few lines: what shipped, what is blocked,
   what is next. No narrative logs.
7. **Slow process is a defect.** A step that repeats per item, or keeps taking more than ten
   minutes, goes into the friction report as a defect to fix, not a cost to accept.
8. **New rules must pay rent.** A new process step names the false match or leak it prevents,
   or it is not added. A step that has never caught anything is proposed for removal at the
   next direction check.

9. **Ninety-minute box.** No worker runs longer than 90 minutes without reporting to the
   orchestrator. At the box it ends its turn with a short status table, leaving any long command
   running in the background with its log path; the orchestrator resumes it. Watching your own
   generation, confirmation, checks, reviews or CI is work: stay in the turn through it. A worker ends its turn early only when the sole thing left is another worker's push
   or a decision that is not its to make. Every brief states the box.

## Precedence

Where this policy conflicts with a habit, a brief or another process document, this policy
wins. Where it conflicts with the floor, the floor wins and the conflict is written in the
friction report as a candidate for simplification.
