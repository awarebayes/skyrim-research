"""Queue Boat compute usage for the cost ledger without touching the tracked ledger.

Verifier commands call record_boat after a run; `python3 tools/cost_ledger.py flush` later moves the
queue into data/costs.json. The queue lives under .local/ because it is written on every run and may
be produced on a worker before anyone reviews it.
"""
import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PENDING = ROOT / '.local/costs/pending.jsonl'


def record_boat(task_id, stage, seconds, wall=None, functions=(), pending=PENDING):
    """Append one Boat usage entry. functions holds '<build id>:<rva>' targets; empty means overhead.

    Never raises on I/O trouble: cost bookkeeping must not fail a verifier run.
    """
    entry = {'task': str(task_id), 'stage': stage, 'seconds': round(float(seconds), 3),
             'wall': None if wall is None else round(float(wall), 3),
             'functions': [str(f) for f in functions],
             'date': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d')}
    try:
        pending = Path(pending)
        pending.parent.mkdir(parents=True, exist_ok=True)
        with pending.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(entry, sort_keys=True) + '\n')
    except OSError:
        return None
    return entry
