"""Print what a Reviewer needs for a set of functions, one compact view per source unit.

    python3 tools/review_packet.py 0x73ad90 sse-steam-1-7-104-0x73ae00   # RVAs or inventory ids
    python3 tools/review_packet.py --stale                               # every stale acceptance
    python3 tools/review_packet.py --all [--no-notes]

Per unit: the files, the digest the match records bind against the digest computed now, recipe
and compiler, and the record notes once. Per function: identity, name and origin, record, hosts,
coverage, code-section hash, the current Reviewer record and the review it needs. For a function
whose Reviewer record binds an earlier digest (a delta review candidate), it also prints the unit
diff since the commit where that approved digest was current, and whether the compared code
section is unchanged between the approved record and the current one.

The packet is a reading aid built from public files and git history; it decides nothing. The
diff is reconstructed source, so pass a packet only to a Reviewer working under G2. Nothing is
written.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check import (ROOT, STALE_UNIT, _json_or_none, acceptance_staleness,  # noqa: E402
                   record_code_section, review_record_path)
from source_digest import include_closure, tu_digest  # noqa: E402


def git(root, *args):
    try:
        return subprocess.run(['git', *args], cwd=root, check=True, capture_output=True).stdout
    except (subprocess.CalledProcessError, OSError):
        return None


def digest_at(root, commit, files):
    """The tu-sha256-v1 digest of `files` as they were at `commit`, or None if one did not exist."""
    with tempfile.TemporaryDirectory() as tmp:
        for name in files:
            blob = git(root, 'show', f'{commit}:{name}')
            if blob is None:
                return None
            path = Path(tmp) / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob)
        return tu_digest(tmp, files)


def approved_commit(root, fn, files, digest):
    """(commit, unit files then, match record then) for the newest commit at which the unit had
    `digest`, searching commits that touched the records or the unit; None if there is none."""
    record_path, review_path = fn.get('report'), review_record_path(fn)
    paths = [p for p in [record_path, review_path, *files] if p]
    log = git(root, 'log', '--format=%H', '--', *paths)
    for commit in (log or b'').decode().split():
        blob = git(root, 'show', f'{commit}:{record_path}') if record_path else None
        try:
            record = json.loads(blob) if blob else None
        except ValueError:
            record = None
        unit = (record or {}).get('source', {}).get('translation_unit') or files
        if digest_at(root, commit, unit) == digest:
            return commit, unit, record
    return None


def previous_code_section(root, fn, previous_digest):
    """(hash or None, where it came from) of the compared code section the approval at
    `previous_digest` saw: from the superseded Reviewer record if it carries one, else from the
    match record at the commit where that digest was current."""
    review = _json_or_none(Path(root) / review_record_path(fn))
    if review and review.get('source_digest') == previous_digest and review.get('code_section_sha256'):
        return review['code_section_sha256'], 'superseded Reviewer record'
    record = record_of(root, fn) or {}
    found = approved_commit(root, fn, (record.get('source') or {}).get('translation_unit') or [], previous_digest)
    if found is None:
        return None, 'no commit found where the approved digest was current'
    commit, _, old = found
    if not old or (old.get('source') or {}).get('digest') != previous_digest:
        return None, f'commit {commit[:12]} has no match record at the approved digest'
    try:
        value = record_code_section(old)
    except (ValueError, KeyError, TypeError) as exc:
        return None, f'match record at commit {commit[:12]} is inconsistent: {exc}'
    if value is None:
        return None, f'match record at commit {commit[:12]} carries no code-section hash'
    return value, f'match record at commit {commit[:12]}'


def record_of(root, fn):
    return _json_or_none(Path(root) / fn['report']) if isinstance(fn.get('report'), str) else None


def short(value):
    return value[:16] if isinstance(value, str) else str(value)


def select(data, root, ids, stale, everything):
    picked = []
    for fn in data['functions']:
        wanted = (everything or fn['id'] in ids or f'0x{fn["rva"]:x}' in ids
                  or (stale and fn['status'] == 'matched' and acceptance_staleness(fn, root)))
        if wanted:
            picked.append(fn)
    return picked


def unit_view(root, compiled, fns, notes):
    out = []
    records = {fn['id']: record_of(root, fn) for fn in fns}
    first = next(iter(records.values()))
    unit = first['source']['translation_unit']
    try:
        fresh = tu_digest(root, include_closure(root, compiled))
    except (ValueError, OSError) as exc:
        fresh = f'cannot compute ({exc})'
    out.append(f'## unit {compiled}')
    out.append(f'files: {" ".join(unit)}')
    bound = sorted({r['source']['digest'] for r in records.values()})
    out.append(f'digest now: {fresh}')
    out.append(f'records bind: {", ".join(bound)}' + ('' if bound == [fresh] else '  <- CHANGED since the record'))
    recipe_path = first['recipe']['path']
    recipe = _json_or_none(root / recipe_path) or {}
    out.append(f'recipe: {recipe_path} ({(recipe.get("compiler") or {}).get("version", "?")})')
    out.append(f'flags: {" ".join(recipe.get("flags") or [])}')
    if notes:
        seen = []
        for r in records.values():
            seen += [n for n in r.get('notes') or [] if n not in seen]
        out += ['notes:'] + [f'  {i}. {n}' for i, n in enumerate(seen, 1)]
    shown = set()
    for fn in fns:
        out += function_view(root, fn, records[fn['id']], shown)
    return out


def function_view(root, fn, record, shown):
    out = ['', f'### {fn["build_id"]} 0x{fn["rva"]:x} {fn["size"]}  {fn["name"]} ({fn["name_origin"]})']
    state = acceptance_staleness(fn, root) if fn['status'] == 'matched' else None
    out.append(f'status: {fn["status"]}' + (f', STALE ({state})' if state else ''))
    runs = record.get('runs') or []
    reports = [r.get('report') or {} for r in runs]
    compiled_on = sorted({r.get('compiled_on') for r in runs})
    compared_on = sorted({r.get('compared_on') for r in runs})
    symbols = sorted({(rep.get('function') or {}).get('symbol') for rep in reports})
    out.append(f'record: {fn["report"]}; {len(runs)} runs; compiled on {", ".join(compiled_on)}; '
               f'compared on {", ".join(compared_on)}')
    out.append(f'symbol: {", ".join(map(str, symbols))}')
    results = sorted({f'{rep.get("result")}/{rep.get("reason")}' for rep in reports})
    cov = sorted({(c.get('code_bytes_exact'), c.get('code_bytes_by_reference'), c.get('code_bytes_total'),
                   c.get('unwind')) for c in (rep.get('coverage') or {} for rep in reports)}, key=str)
    out.append(f'result: {", ".join(results)}; coverage (exact + by reference of total, unwind): '
               + '; '.join(f'{a} + {b} of {t}, {u}' for a, b, t, u in cov))
    try:
        section = record_code_section(record)
    except ValueError as exc:
        section = f'inconsistent ({exc})'
    out.append(f'code section: {section or "absent (comparator does not emit it yet)"}')
    review = _json_or_none(root / review_record_path(fn))
    if review is None:
        out.append('review record: none' + ('' if fn['status'] == 'matched' else '; needs: full review'))
        return out
    out.append(f'review record: {review.get("review_kind", "full")} by {review.get("reviewer_model")} '
               f'({review.get("review_task_id")}, {review.get("review_date")}) on digest {review.get("source_digest")}')
    current = record['source']['digest']
    if review.get('source_digest') == current and state != STALE_UNIT:
        out.append('needs: nothing (review binds the current record)')
        return out
    if state == STALE_UNIT:
        out.append('needs: re-confirmation (tools/verifier/confirm) before any review; the record is stale')
        return out
    previous = review.get('source_digest')
    old, where = previous_code_section(root, fn, previous)
    out.append(f'needs: full review, or delta review with previous_source_digest: {previous}')
    verdict = ('unchanged' if old is not None and old == section else
               'CHANGED: delta review not possible, full review needed' if old is not None else
               f'unavailable ({where}): delta review not possible, full review needed')
    out.append(f'code section since approval: {verdict}' + (f' (approved {short(old)} from {where})' if old else ''))
    found = approved_commit(root, fn, record['source']['translation_unit'], previous)
    if found is None:
        out.append('diff: no commit found where the approved digest was current')
        return out
    commit, old_unit, _ = found
    files = sorted(set(old_unit) | set(record['source']['translation_unit']))
    # Functions of one unit approved together share one diff; print it once per unit.
    if (commit, tuple(files)) in shown:
        out.append(f'diff since approved digest (commit {commit[:12]}): as printed above for this unit')
        return out
    shown.add((commit, tuple(files)))
    diff = git(root, 'diff', '--no-color', commit, '--', *files)
    out.append(f'diff since approved digest (commit {commit[:12]}, working tree now):')
    out.append((diff or b'').decode('utf-8', 'replace').rstrip() or '(no textual difference)')
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('functions', nargs='*', help='Inventory ids or RVAs (0x...)')
    p.add_argument('--stale', action='store_true', help='Add every matched entry whose acceptance is stale')
    p.add_argument('--all', action='store_true', help='Every entry that names a match record')
    p.add_argument('--no-notes', action='store_true', help='Omit the record notes')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    root = args.root
    data = json.loads((root / 'data/progress.json').read_text())
    picked = select(data, root, set(args.functions), args.stale, args.all)
    without = [fn['id'] for fn in picked if record_of(root, fn) is None]
    picked = [fn for fn in picked if fn['id'] not in without]
    if not picked:
        print('no selected function names a readable match record', file=sys.stderr)
        return 1
    units = {}
    for fn in picked:
        units.setdefault(record_of(root, fn)['source']['compiled'], []).append(fn)
    out = [f'# Review packet: {len(picked)} function(s) in {len(units)} unit(s)']
    if without:
        out.append(f'skipped (no readable match record): {", ".join(without)}')
    for compiled, fns in sorted(units.items()):
        out += [''] + unit_view(root, compiled, fns, not args.no_notes)
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
