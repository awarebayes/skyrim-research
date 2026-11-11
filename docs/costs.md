# Cost ledger

`data/costs.json` records what reverse-engineering costs, so later work can carry an estimate. It
holds counts and allocations only: no prompts, transcript text, paths or game-derived content.
`tools/cost_ledger.py` writes, validates and reports it; the public page shows its totals.

## What is measured

- **Model tokens** per agent run, from the run's JSONL transcript: fresh `input`, `cache_creation`
  (cache writes), `cache_read` (cache hits) and `output`, plus the number of API messages and
  tool calls. Streaming repeats a message id across lines; each id is counted once.
- **Agent wall time**: first to last transcript timestamp. It includes waiting on tools and Boat.
- **Boat compute seconds** as reported by the worker that ran the machine, or queued by
  `tools/cost_hooks.py` from a verifier command.

## What is estimated

- **Allocation.** Each record splits its cost with `allocations`, a list of
  `{target, share}` summing to 1. A target is `<build id>:<rva>` (a function in
  `data/progress.json`) or `overhead` (tooling, policy, infrastructure, orchestration). A
  `boat_allocations` list may split Boat seconds differently from tokens. When an agent served
  several purposes the split is a judgement call and the record has `estimated: true`.
- Boat seconds shared by several agents and split evenly are also `estimated: true`.
- `complete: false` marks a run ingested while still going; re-ingest it later and the record is
  replaced, not duplicated.
- Projections (`estimate`) multiply a profile's average direct cost. The current sample is a
  handful of short functions chosen to prove the pipeline, so they are a floor, not a forecast.
- Money: `data/prices.json` holds null rates. `report --money` refuses to price until the
  maintainer fills them and records their source; nothing in the repository asserts a price.

## Recording a run

After a worker finishes, one command (repeat it for a running agent to update its record):

```sh
python3 tools/cost_ledger.py ingest --transcript <agent transcript .jsonl or .output> \
  --role drafter --task <task id> --stage draft \
  --alloc sse-steam-1-7-104:0x73ad90=1 --boat-seconds 120
```

Use `--alloc overhead=1` (the default) for tooling, `--estimated` for judgement splits, and
`--incomplete` while the agent is still running. `ingest-dir <dir> --map map.json` does many at
once (map keys are agent ids; values hold `role`, `task`, `stage`, `alloc` and optional
`boat_seconds`, `boat_alloc`, `estimated`, `complete`, `source`); transcripts missing from the map
are recorded as role `unknown`, task `unmapped`. Boat usage without a transcript:
`add-compute --task <id> --seconds N [--wall N] --alloc <target>...`, or queue it from code with
`cost_hooks.record_boat(...)` and run `flush`. Then `validate`, `report` and
`estimate --functions N [--profile first-function|second-batch]`.

## Known gaps

- The orchestrator session is captured only when its transcript is available to ingest; the
  page says which. Main-session time spent by the maintainer is not.
- Cache reads are reported separately from fresh input. They dominate the input count but are
  priced far lower, so totals that add them together overstate cost.
- Human time (review, maintainer decisions) is not tracked.
- Boat seconds come from worker reports and the hook; machine idle time before auto-stop is
  included only where the reporting worker included it.
