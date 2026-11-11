"""Ledger of model tokens and Boat compute spent per function, with reports and projections.

The ledger (data/costs.json) is public: it holds counts and allocations only, never transcript
text. See docs/costs.md for what is measured, what is estimated and how allocation works.
"""
import argparse
from collections import Counter, defaultdict
import datetime
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / 'data/costs.json'
PROGRESS = ROOT / 'data/progress.json'
PRICES = ROOT / 'data/prices.json'
PENDING = ROOT / '.local/costs/pending.jsonl'

TOKEN_KEYS = ('input', 'cache_creation', 'cache_read', 'output')
USAGE_KEYS = dict(input='input_tokens', cache_creation='cache_creation_input_tokens',
                  cache_read='cache_read_input_tokens', output='output_tokens')
ROLES = {'orchestrator', 'engineer', 'drafter', 'reviewer', 'verifier', 'unknown'}
STAGES = {'analysis', 'draft', 'confirm', 'review', 'integrate', 'tooling', 'policy', 'prep',
          'orchestration', 'unknown'}
RECORD_KEYS = {'id', 'date', 'role', 'model', 'task', 'stage', 'tokens', 'messages', 'tool_uses',
               'boat_seconds', 'boat_wall_seconds', 'agent_wall_seconds', 'allocations',
               'boat_allocations', 'estimated', 'complete', 'source'}
OVERHEAD = 'overhead'
TOLERANCE = 1e-6
CAVEAT = ('Caveat: the sample is tiny (a handful of accepted functions) and biased toward short, easy '
          'functions chosen to prove the pipeline. Larger functions will need more attempts, tokens and '
          'compute; treat these projections as a floor, not a forecast.')


def empty_ledger():
    return {'schema_version': 1,
            'note': 'Counts only. Tokens come from subagent and session transcripts; shares marked '
                    'estimated are judgement calls. See docs/costs.md.',
            'profiles': {}, 'records': []}


def load_json(path, default=None):
    path = Path(path)
    if not path.exists():
        if default is not None:
            return default
        raise FileNotFoundError(path)
    return json.loads(path.read_text())


def save_ledger(ledger, path):
    ledger['records'].sort(key=lambda r: (r['date'] or '', r['id']))
    Path(path).write_text(json.dumps(ledger, indent=1) + '\n')


def record_id_for(transcript):
    """Stable id per transcript so a re-ingest of a running agent replaces its earlier record."""
    stem = Path(transcript).name.split('.')[0]
    return stem if stem.startswith('agent-') else ('agent-' + stem if stem.startswith('a') and len(stem) == 17
                                                    else 'session-' + stem)


def parse_transcript(path):
    """Usage counts from a JSONL transcript. Streaming responses repeat a message id; count it once."""
    usage = {}
    tools = set()
    first = last = None
    with open(path, encoding='utf-8', errors='replace') as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if not isinstance(entry, dict):
                continue
            stamp = entry.get('timestamp')
            if isinstance(stamp, str):
                first = first or stamp
                last = stamp
            message = entry.get('message')
            if not isinstance(message, dict) or message.get('role') != 'assistant':
                continue
            for block in message.get('content') or []:
                if isinstance(block, dict) and block.get('type') == 'tool_use' and block.get('id'):
                    tools.add(block['id'])
            if isinstance(message.get('usage'), dict) and message.get('id'):
                counts = {k: int(message['usage'].get(v) or 0) for k, v in USAGE_KEYS.items()}
                usage[message['id']] = (message.get('model'), counts)
    tokens = {k: sum(c[k] for _, c in usage.values()) for k in TOKEN_KEYS}
    models = Counter(m for m, _ in usage.values() if m)
    wall = None
    if first and last:
        wall = round((parse_time(last) - parse_time(first)).total_seconds())
    return {'tokens': tokens, 'messages': len(usage), 'tool_uses': len(tools),
            'model': models.most_common(1)[0][0] if models else None,
            'date': first[:10] if first else None, 'agent_wall_seconds': wall}


def parse_time(stamp):
    return datetime.datetime.fromisoformat(stamp.replace('Z', '+00:00'))


def parse_allocs(items):
    """'<build id>:<rva>=<share>' or 'overhead=<share>'; also '<target>' alone for an equal split."""
    if not items:
        return [{'target': OVERHEAD, 'share': 1.0}]
    explicit, equal = [], []
    for item in items:
        target, sep, share = item.rpartition('=')
        if sep:
            explicit.append({'target': normalize_target(target), 'share': float(share)})
        else:
            equal.append(normalize_target(item))
    if equal:
        rest = 1.0 - sum(a['share'] for a in explicit)
        explicit += [{'target': t, 'share': rest / len(equal)} for t in equal]
    return explicit


def normalize_target(target):
    if target == OVERHEAD:
        return target
    build, sep, rva = target.rpartition(':')
    if not sep:
        raise ValueError(f'target {target!r} is neither overhead nor <build id>:<rva>')
    return f'{build}:0x{int(rva, 0):x}'


def function_targets(progress):
    return {f'{fn["build_id"]}:0x{fn["rva"]:x}': fn for fn in progress.get('functions', [])}


def validate(ledger, progress):
    """Raise ValueError on the first schema or allocation problem; returns the ledger."""
    def need(condition, message):
        if not condition:
            raise ValueError(message)
    known = function_targets(progress)
    need(isinstance(ledger, dict) and ledger.get('schema_version') == 1, 'schema_version must be 1')
    need(isinstance(ledger.get('records'), list), 'records must be a list')
    for name, targets in (ledger.get('profiles') or {}).items():
        need(isinstance(targets, list) and targets, f'profile {name}: needs a target list')
        for target in targets:
            need(target in known, f'profile {name}: unknown target {target}')
    seen = set()
    for record in ledger['records']:
        rid = record.get('id')
        need(isinstance(rid, str) and rid, 'record without id')
        need(rid not in seen, f'{rid}: duplicate id')
        seen.add(rid)
        need(set(record) <= RECORD_KEYS, f'{rid}: unexpected fields {sorted(set(record) - RECORD_KEYS)}')
        need(record.get('role') in ROLES, f'{rid}: bad role')
        need(record.get('stage') in STAGES, f'{rid}: bad stage')
        need(isinstance(record.get('task'), str) and record['task'], f'{rid}: task required')
        need(record.get('date') is None or (isinstance(record['date'], str) and len(record['date']) == 10),
             f'{rid}: date must be YYYY-MM-DD or null')
        tokens = record.get('tokens')
        need(isinstance(tokens, dict) and set(tokens) == set(TOKEN_KEYS), f'{rid}: tokens need {TOKEN_KEYS}')
        for key in ('messages', 'tool_uses'):
            need(record.get(key) is None or (type(record[key]) is int and record[key] >= 0), f'{rid}: bad {key}')
        for key in TOKEN_KEYS:
            need(type(tokens[key]) is int and tokens[key] >= 0, f'{rid}: token count {key} must be int >= 0')
        for key in ('boat_seconds', 'boat_wall_seconds', 'agent_wall_seconds'):
            value = record.get(key)
            need(value is None or (isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0),
                 f'{rid}: {key} must be a non-negative number or null')
        need(isinstance(record.get('estimated'), bool) and isinstance(record.get('complete'), bool),
             f'{rid}: estimated and complete must be booleans')
        source = record.get('source')
        need(isinstance(source, str) and source, f'{rid}: source note required')
        need(not any(s in source for s in ('/Users/', '/private/', '/home/', '~/', '\\')),
             f'{rid}: source must not hold a local path')
        for key in ('allocations', 'boat_allocations'):
            allocs = record.get(key)
            if allocs is None and key == 'boat_allocations':
                continue
            need(isinstance(allocs, list) and allocs, f'{rid}: {key} must be a non-empty list')
            for alloc in allocs:
                need(set(alloc) == {'target', 'share'}, f'{rid}: {key} entries need target and share')
                need(alloc['target'] == OVERHEAD or alloc['target'] in known,
                     f'{rid}: {key} target {alloc["target"]} is not overhead or a function in data/progress.json')
                need(isinstance(alloc['share'], (int, float)) and 0 < alloc['share'] <= 1,
                     f'{rid}: {key} share must be in (0, 1]')
            need(len({a['target'] for a in allocs}) == len(allocs), f'{rid}: {key} repeats a target')
            need(abs(sum(a['share'] for a in allocs) - 1) <= TOLERANCE, f'{rid}: {key} shares must sum to 1')
    return ledger


def make_record(rid, role, task, stage, allocations, *, model=None, date=None, tokens=None, messages=None,
                tool_uses=None, boat_seconds=None, boat_wall_seconds=None, agent_wall_seconds=None,
                boat_allocations=None, estimated=False, complete=True, source='session transcript'):
    record = {'id': rid, 'date': date, 'role': role, 'model': model, 'task': task, 'stage': stage,
              'tokens': tokens or {k: 0 for k in TOKEN_KEYS}, 'messages': messages, 'tool_uses': tool_uses,
              'boat_seconds': boat_seconds, 'boat_wall_seconds': boat_wall_seconds,
              'agent_wall_seconds': agent_wall_seconds, 'allocations': allocations,
              'estimated': estimated, 'complete': complete, 'source': source}
    if boat_allocations:
        record['boat_allocations'] = boat_allocations
    return record


def upsert(ledger, record):
    ledger['records'] = [r for r in ledger['records'] if r['id'] != record['id']] + [record]


def ingest(ledger, transcript, role, task, stage, allocations, *, model=None, boat_seconds=None,
           boat_wall_seconds=None, boat_allocations=None, estimated=False, complete=True,
           source='session transcript'):
    parsed = parse_transcript(transcript)
    record = make_record(record_id_for(transcript), role, task, stage, allocations,
                         model=model or parsed['model'], date=parsed['date'], tokens=parsed['tokens'],
                         messages=parsed['messages'], tool_uses=parsed['tool_uses'], boat_seconds=boat_seconds,
                         boat_wall_seconds=boat_wall_seconds, agent_wall_seconds=parsed['agent_wall_seconds'],
                         boat_allocations=boat_allocations, estimated=estimated, complete=complete, source=source)
    upsert(ledger, record)
    return record


def ingest_dir(ledger, directory, mapping):
    """Ingest every transcript in a directory; entries absent from the mapping are kept as unmapped."""
    done, unmapped = [], []
    for path in sorted(Path(directory).iterdir()):
        if not path.is_file() or path.suffix not in {'.jsonl', '.output'}:
            continue
        rid = record_id_for(path)
        key = rid[len('agent-'):] if rid.startswith('agent-') else rid
        entry = mapping.get(key) or mapping.get(rid)
        if entry is None:
            if parse_transcript(path)['messages'] == 0:
                continue  # Background shell logs share the directory but carry no model usage.
            unmapped.append(key)
            entry = {'role': 'unknown', 'task': 'unmapped', 'stage': 'unknown', 'source': 'session transcript, unmapped'}
        ingest(ledger, path, entry['role'], entry['task'], entry['stage'], parse_allocs(entry.get('alloc')),
               model=entry.get('model'), boat_seconds=entry.get('boat_seconds'),
               boat_wall_seconds=entry.get('boat_wall_seconds'),
               boat_allocations=parse_allocs(entry['boat_alloc']) if entry.get('boat_alloc') else None,
               estimated=entry.get('estimated', False), complete=entry.get('complete', True),
               source=entry.get('source', 'session transcript'))
        done.append(key)
    return done, unmapped


def compute_record(task, stage, seconds, wall, allocations, estimated=False, source='verifier hook', date=None):
    payload = json.dumps([task, stage, seconds, wall, allocations, date], sort_keys=True)
    rid = 'compute-' + hashlib.sha256(payload.encode()).hexdigest()[:12]
    return make_record(rid, 'verifier', task, stage, allocations, date=date, boat_seconds=seconds,
                       boat_wall_seconds=wall, estimated=estimated, source=source)


def flush(ledger, pending=PENDING):
    """Move queued Boat entries into the ledger; ids are content hashes so a repeated flush is harmless."""
    pending = Path(pending)
    if not pending.exists():
        return 0
    count = 0
    for line in pending.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        targets = [normalize_target(t) for t in entry.get('functions') or []]
        allocs = parse_allocs(targets) if targets else parse_allocs(None)
        upsert(ledger, compute_record(entry['task'], entry['stage'], entry['seconds'], entry.get('wall'),
                                      allocs, date=entry.get('date')))
        count += 1
    pending.write_text('')
    return count


def allocated(record):
    """Yield (target, tokens dict, boat seconds) for each allocation of one record."""
    boat = record.get('boat_seconds') or 0
    boat_shares = {a['target']: a['share'] for a in record.get('boat_allocations') or record['allocations']}
    targets = {a['target']: a['share'] for a in record['allocations']}
    for target in sorted(set(targets) | set(boat_shares)):
        share = targets.get(target, 0)
        yield target, {k: record['tokens'][k] * share for k in TOKEN_KEYS}, boat * boat_shares.get(target, 0)


def totals(records):
    tokens = {k: sum(r['tokens'][k] for r in records) for k in TOKEN_KEYS}
    return tokens, sum(r.get('boat_seconds') or 0 for r in records), sum(r.get('messages') or 0 for r in records)


def per_target(ledger):
    out = defaultdict(lambda: {'tokens': {k: 0.0 for k in TOKEN_KEYS}, 'boat_seconds': 0.0})
    for record in ledger['records']:
        for target, tokens, boat in allocated(record):
            for k in TOKEN_KEYS:
                out[target]['tokens'][k] += tokens[k]
            out[target]['boat_seconds'] += boat
    return out


def overhead_by_stage(ledger):
    out = defaultdict(lambda: {'tokens': {k: 0.0 for k in TOKEN_KEYS}, 'boat_seconds': 0.0})
    for record in ledger['records']:
        for target, tokens, boat in allocated(record):
            if target == OVERHEAD:
                for k in TOKEN_KEYS:
                    out[record['stage']]['tokens'][k] += tokens[k]
                out[record['stage']]['boat_seconds'] += boat
    return out


def accepted(progress):
    return [t for t, fn in function_targets(progress).items() if fn.get('status') == 'matched']


def profile_average(ledger, progress, name):
    """Mean direct cost of the accepted functions in a profile."""
    targets = [t for t in ledger.get('profiles', {}).get(name, []) if t in set(accepted(progress))]
    if not targets:
        return None
    direct = per_target(ledger)
    tokens = {k: sum(direct[t]['tokens'][k] for t in targets) / len(targets) for k in TOKEN_KEYS}
    return {'functions': len(targets), 'tokens': tokens,
            'boat_seconds': sum(direct[t]['boat_seconds'] for t in targets) / len(targets)}


def summary(ledger, progress):
    """Figures for the public page: totals plus the average direct cost per accepted function."""
    tokens, boat, _ = totals(ledger['records'])
    done = accepted(progress)
    direct = per_target(ledger)
    avg = None
    if done:
        avg = {'input': sum(direct[t]['tokens']['input'] + direct[t]['tokens']['cache_creation']
                            + direct[t]['tokens']['cache_read'] for t in done) / len(done),
               'output': sum(direct[t]['tokens']['output'] for t in done) / len(done),
               'boat_seconds': sum(direct[t]['boat_seconds'] for t in done) / len(done)}
    return {'input_all': tokens['input'] + tokens['cache_creation'] + tokens['cache_read'],
            'output': tokens['output'], 'boat_hours': boat / 3600, 'accepted': len(done), 'average': avg,
            'orchestrator': any(r['role'] == 'orchestrator' for r in ledger['records']),
            'incomplete': sum(1 for r in ledger['records'] if not r['complete'])}


def fmt(n):
    return f'{round(n):,}'


def token_cells(tokens):
    return '  '.join(f'{k}={fmt(tokens[k])}' for k in TOKEN_KEYS)


def money(tokens_by_model, boat_seconds, prices):
    """Return (amount, missing) where missing names every rate still null in the price table."""
    missing, amount = set(), 0.0
    for model, tokens in tokens_by_model.items():
        rates = (prices.get('models') or {}).get(model) or {}
        for k in TOKEN_KEYS:
            if tokens[k] and rates.get(k) is None:
                missing.add(f'{model}.{k}')
            elif tokens[k]:
                amount += tokens[k] / 1e6 * rates[k]
    if boat_seconds:
        if prices.get('boat_per_hour') is None:
            missing.add('boat_per_hour')
        else:
            amount += boat_seconds / 3600 * prices['boat_per_hour']
    return amount, sorted(missing)


def report(ledger, progress, prices=None, out=sys.stdout):
    p = lambda *a: print(*a, file=out)
    tokens, boat, messages = totals(ledger['records'])
    incomplete = [r['id'] for r in ledger['records'] if not r['complete']]
    p(f'Ledger: {len(ledger["records"])} records, {messages:,} API messages, Boat {boat:,.0f} s ({boat / 3600:.2f} h)')
    p(f'  all tokens: {token_cells(tokens)}')
    if incomplete:
        p(f'  incomplete (agent still running when ingested): {len(incomplete)}')
    if not any(r['role'] == 'orchestrator' for r in ledger['records']):
        p('  orchestrator tokens: not captured')
    names = {t: fn.get('name') for t, fn in function_targets(progress).items()}
    status = {t: fn.get('status') for t, fn in function_targets(progress).items()}
    direct = per_target(ledger)
    p('\nDirect cost per function (allocated shares; see estimated flags in the ledger):')
    for target in sorted(t for t in direct if t != OVERHEAD):
        row = direct[target]
        p(f'  {target} [{status.get(target)}] {names.get(target) or ""}')
        p(f'      {token_cells(row["tokens"])}  boat={row["boat_seconds"]:,.0f}s')
    p('\nOverhead by stage:')
    for stage, row in sorted(overhead_by_stage(ledger).items()):
        p(f'  {stage:<13} {token_cells(row["tokens"])}  boat={row["boat_seconds"]:,.0f}s')
    for label, key in (('role', 'role'), ('model', 'model')):
        p(f'\nBy {label}:')
        groups = defaultdict(list)
        for record in ledger['records']:
            groups[record[key] or '(none)'].append(record)
        for name, records in sorted(groups.items()):
            t, b, m = totals(records)
            p(f'  {name:<18} records={len(records):<3} msgs={m:<5,} {token_cells(t)}  boat={b:,.0f}s')
    p('\nAverage direct cost per accepted function:')
    for name in sorted(ledger.get('profiles', {})):
        avg = profile_average(ledger, progress, name)
        if avg:
            p(f'  {name:<15} n={avg["functions"]}  {token_cells(avg["tokens"])}  boat={avg["boat_seconds"]:,.0f}s')
    if prices is not None:
        by_model = defaultdict(lambda: {k: 0 for k in TOKEN_KEYS})
        for record in ledger['records']:
            for k in TOKEN_KEYS:
                by_model[record['model'] or '(none)'][k] += record['tokens'][k]
        amount, missing = money(by_model, boat, prices)
        if missing:
            p(f'\nMoney: cannot price; fill these in data/prices.json: {", ".join(missing)}')
        else:
            p(f'\nMoney (assumed prices from data/prices.json): {amount:,.2f} {prices.get("currency") or ""}')


def estimate(ledger, progress, functions, profile, out=sys.stdout):
    p = lambda *a: print(*a, file=out)
    avg = profile_average(ledger, progress, profile)
    if avg is None:
        raise ValueError(f'profile {profile!r} has no accepted function with recorded cost')
    overhead = per_target(ledger).get(OVERHEAD, {'tokens': {k: 0 for k in TOKEN_KEYS}, 'boat_seconds': 0})
    done = len(accepted(progress))
    p(f'Projection for {functions:,} functions from profile {profile!r} (n={avg["functions"]}):')
    direct = {k: avg['tokens'][k] * functions for k in TOKEN_KEYS}
    p(f'  direct only:     {token_cells(direct)}  boat={avg["boat_seconds"] * functions / 3600:,.1f} h')
    # Overhead so far is mostly one-time tooling; scaling it per function is a pessimistic bound.
    per_fn = {k: overhead['tokens'][k] / done for k in TOKEN_KEYS}
    scaled = {k: direct[k] + per_fn[k] * functions for k in TOKEN_KEYS}
    boat_scaled = (avg['boat_seconds'] + overhead['boat_seconds'] / done) * functions / 3600
    p(f'  with overhead:   {token_cells(scaled)}  boat={boat_scaled:,.1f} h')
    p(f'    (overhead so far spread over {done} accepted functions and scaled linearly: an upper bound,')
    p('     since most of it is one-time tooling and policy)')
    fixed = {k: direct[k] + overhead['tokens'][k] for k in TOKEN_KEYS}
    p(f'  direct + overhead so far once: {token_cells(fixed)}  '
      f'boat={(avg["boat_seconds"] * functions + overhead["boat_seconds"]) / 3600:,.1f} h')
    p(CAVEAT)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ledger', default=str(LEDGER))
    parser.add_argument('--progress', default=str(PROGRESS))
    sub = parser.add_subparsers(dest='command', required=True)
    one = sub.add_parser('ingest', help='Add or replace the record for one transcript')
    one.add_argument('--transcript', required=True)
    one.add_argument('--role', required=True, choices=sorted(ROLES))
    one.add_argument('--task', required=True)
    one.add_argument('--stage', required=True, choices=sorted(STAGES))
    one.add_argument('--model')
    one.add_argument('--alloc', nargs='*', default=[], help='<build id>:<rva>=<share> or overhead=<share>')
    one.add_argument('--boat-seconds', type=float)
    one.add_argument('--boat-wall', type=float)
    one.add_argument('--boat-alloc', nargs='*', default=[], help='Separate split for Boat seconds')
    one.add_argument('--estimated', action='store_true')
    one.add_argument('--incomplete', action='store_true', help='Agent still running; re-ingest later')
    one.add_argument('--source', default='session transcript')
    bulk = sub.add_parser('ingest-dir', help='Ingest every transcript in a directory using a JSON mapping')
    bulk.add_argument('directory')
    bulk.add_argument('--map', required=True)
    comp = sub.add_parser('add-compute', help='Record Boat usage that has no transcript')
    comp.add_argument('--task', required=True)
    comp.add_argument('--stage', default='confirm', choices=sorted(STAGES))
    comp.add_argument('--seconds', required=True, type=float)
    comp.add_argument('--wall', type=float)
    comp.add_argument('--alloc', nargs='*', default=[])
    comp.add_argument('--estimated', action='store_true')
    comp.add_argument('--date')
    sub.add_parser('flush', help='Move queued hook entries from .local/costs/pending.jsonl into the ledger')
    sub.add_parser('validate')
    rep = sub.add_parser('report')
    rep.add_argument('--money', action='store_true')
    rep.add_argument('--prices', default=str(PRICES))
    est = sub.add_parser('estimate')
    est.add_argument('--functions', required=True, type=int)
    est.add_argument('--profile', default='second-batch')
    args = parser.parse_args(argv)

    progress = load_json(args.progress)
    ledger = load_json(args.ledger, empty_ledger())
    try:
        if args.command in {'validate', 'report', 'estimate'}:
            validate(ledger, progress)
        if args.command == 'ingest':
            record = ingest(ledger, args.transcript, args.role, args.task, args.stage, parse_allocs(args.alloc),
                            model=args.model, boat_seconds=args.boat_seconds, boat_wall_seconds=args.boat_wall,
                            boat_allocations=parse_allocs(args.boat_alloc) if args.boat_alloc else None,
                            estimated=args.estimated, complete=not args.incomplete, source=args.source)
            print(f'{record["id"]}: {record["messages"]} messages, {token_cells(record["tokens"])}')
        elif args.command == 'ingest-dir':
            done, unmapped = ingest_dir(ledger, args.directory, load_json(args.map))
            print(f'ingested {len(done)} transcripts; unmapped: {", ".join(unmapped) or "none"}')
        elif args.command == 'add-compute':
            record = compute_record(args.task, args.stage, args.seconds, args.wall, parse_allocs(args.alloc),
                                    estimated=args.estimated, source='manual entry', date=args.date)
            upsert(ledger, record)
            print(f'{record["id"]}: {args.seconds:,.0f} Boat seconds')
        elif args.command == 'flush':
            print(f'flushed {flush(ledger)} queued entries')
        elif args.command == 'validate':
            print(f'PASS: {len(ledger["records"])} cost records')
            return 0
        elif args.command == 'report':
            report(ledger, progress, load_json(args.prices) if args.money else None)
            return 0
        elif args.command == 'estimate':
            estimate(ledger, progress, args.functions, args.profile)
            return 0
        validate(ledger, progress)
        save_ledger(ledger, args.ledger)
    except (ValueError, KeyError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
