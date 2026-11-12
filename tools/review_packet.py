"""Print what a Reviewer needs for a set of functions, one compact view per source unit.

    python3 tools/review_packet.py 0x73ad90 sse-steam-1-7-104-0x73ae00   # RVAs or inventory ids
    python3 tools/review_packet.py --stale                               # every stale acceptance
    python3 tools/review_packet.py --all [--no-notes]
    python3 tools/review_packet.py --prior-review .local/reviews/<old>.md [--prior-ref <commit>] [ids...]

Per unit: the files, the digest the match records bind against the digest computed now, recipe
and compiler, and the record notes once. Per function: identity, name and origin, record, hosts,
coverage, code-section hash, the current Reviewer record and the review it needs. Per unit it also
lists the community declaration of every COMMUNITY-labelled name, read from the local pinned
checkouts (tools/check_labels.py), and the bodies tools/check_origin.py finds close to a same-named
community or FNV body, with one similarity line per function (both omitted with --no-community or
when no checkout is present). For a function
whose Reviewer record binds an earlier digest (a delta review candidate), it also prints the unit
diff since the commit where that approved digest was current, and whether the compared code
section is unchanged between the approved record and the current one.

With `--template` each function ends with a blank review block in the current reviewer.md output
format (checks, blocking_findings, naming_findings), so a Reviewer writes the format the
acceptance tool reads. With `--prior-review <file>` (repeatable) the packet is for a re-review of
functions an earlier review already judged, for example one written before the two-tier rule:
functions default to those the file has a block for; each gets the earlier block verbatim, its
file hash and the digest it reviewed, whether the unit's digest is still that digest, and if not
the unit diff since a commit where it was (found in history, or the commit `--prior-ref` names,
whose digest is verified first; without a verified commit no diff is printed). It implies
`--template`. The earlier review is context only: it is never converted into a verdict, and the
new review is a full review in the new format. When a sibling index is present
(`<analysis>/fnv_index.jsonl`, tools/build_fnv_index.py), each function also lists its FNV
counterparts, so the Reviewer can compare for undeclared reuse.

The packet is a reading aid built from public files and git history; it decides nothing. The
diff is reconstructed source, so pass a packet only to a Reviewer working under G2. Nothing is
written.
"""
import argparse
import hashlib
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


def accepted_current(root, fn):
    """A matched entry whose acceptance binds the current source needs no re-review, so a
    --prior-review default selection leaves it out; naming the function selects it anyway."""
    return fn['status'] == 'matched' and not acceptance_staleness(fn, root)


def select(data, root, ids, stale, everything, prior=None):
    picked = []
    for fn in data['functions']:
        wanted = (everything or fn['id'] in ids or f'0x{fn["rva"]:x}' in ids
                  or (stale and fn['status'] == 'matched' and acceptance_staleness(fn, root))
                  or (prior is not None and not ids and (fn['build_id'], fn['rva']) in prior
                      and not accepted_current(root, fn)))
        if wanted:
            picked.append(fn)
    return picked


def community_view(root, unit):
    """The community declaration of each COMMUNITY-labelled name in the unit, from the local
    pinned checkouts (tools/check_labels.py), so a Reviewer need not open the checkout."""
    try:
        import check_labels
        lines = check_labels.community_excerpts([root / name for name in unit], root=root)
    except Exception as exc:  # noqa: BLE001 - the excerpts are a reading aid; the packet still prints
        return [f'community excerpts: not available ({type(exc).__name__}: {exc})']
    return ['community excerpts (name: repo path:line: declaration):'] + [f'  {line}' for line in lines]


_CLONES = []


def origin_view(root, unit):
    """(hits or None, lines): bodies of the unit close to a same-named community or FNV body
    (tools/check_origin.py), the list the Reviewer's provenance check starts from."""
    try:
        import check_origin
        if not _CLONES:
            _CLONES.append(check_origin.open_clones(root))
        clones, missing = _CLONES[0]
        hits = check_origin.check_unit([root / name for name in unit], clones, root=root)
    except Exception as exc:  # noqa: BLE001 - a reading aid; the packet still prints
        return None, [f'body origin: not available ({type(exc).__name__}: {exc})']
    pins = ', '.join(f'{c.repo}@{(c.head or "?")[:7]}' for c in clones) or 'no local clone'
    out = [f'body origin (tools/check_origin.py, threshold {check_origin.DEFAULT_THRESHOLD:.2f}, {pins}'
           + (f'; not compared: {", ".join(missing)}' if missing else '') + '):']
    out += [f'  {check_origin.describe(h)}' for h in hits if not h['trivial']]
    same = sorted({h['function'] for h in hits if h['trivial']})
    if same:
        out.append(f'  trivial, same as community or sibling ({len(same)}): {", ".join(same)}')
    if not hits:
        out.append('  none at or above the threshold')
    return hits, out


# Fields only the two-tier format has; a block without them is refused by tools/accept_function.py.
NEW_FORMAT_FIELDS = ('report_binding', 'checks', 'blocking_findings', 'naming_findings')


def prior_reviews(root, paths):
    """{(build id, rva): [(path, sha256, title, first line, block lines, block fields)]} from earlier
    review files. Fields are parsed the way the acceptance tool parses them."""
    from accept_function import fields  # imported here: accept_function imports this module
    out = {}
    for name in paths:
        path = Path(name) if Path(name).is_absolute() else Path(root) / name
        blob = path.read_bytes()
        lines = blob.decode('utf-8').splitlines()
        title = next((l[len('# Review '):].strip() for l in lines if l.startswith('# Review ')), None)
        starts = [i for i, l in enumerate(lines) if l.startswith('## ')] + [len(lines)]
        for i, end in zip(starts, starts[1:]):
            parts = lines[i][3:].split()
            if len(parts) != 3:
                continue  # a unit heading, not a function block
            try:
                rva = int(parts[1], 16)
            except ValueError:
                continue
            body = lines[i:end]
            while body and not body[-1].strip():
                body.pop()
            out.setdefault((parts[0], rva), []).append(
                (path, hashlib.sha256(blob).hexdigest(), title, i + 1, body, fields(lines[i + 1:end])))
    return out


def prior_view(root, fn, record, entries, prior_ref, shown):
    """The earlier review of one function and what changed in the unit since the digest it saw."""
    out = []
    unit = record['source']['translation_unit']
    current = record['source']['digest']
    for path, sha, title, line, body, block in entries:
        missing = [k for k in NEW_FORMAT_FIELDS if k not in block]
        out.append(f'earlier review: {title} ({path.name} line {line}, file sha256 {sha})')
        out.append(f'earlier verdict: {block.get("verdict", "?")} ({block.get("review_kind", "full")}) '
                   f'on digest {block.get("source_digest", "?")}')
        out.append('earlier format: ' + ('old (no ' + ', '.join(missing) + '): the acceptance tool refuses it; '
                                         'write a new-format block' if missing else 'current'))
        out.append('earlier block (context, not a verdict; re-judge every reason under the current '
                   'blocking grounds and move naming reasons to naming_findings):')
        out += [f'  | {l}' for l in body]
        old = block.get('source_digest')
        if old == current:
            out.append('unit since earlier review: unchanged (same digest); the earlier reading applies to this source')
            continue
        if prior_ref:
            then = digest_at(root, prior_ref, unit)
            commit = prior_ref if old and then == old else None
            why = f'--prior-ref {prior_ref} has digest {then}, not {old}'
        else:
            found = approved_commit(root, fn, unit, old) if old else None
            commit = found[0] if found else None
            why = 'no commit found where that digest was current (pass --prior-ref if one exists)'
        if commit is None:
            out.append(f'unit since earlier review: CHANGED, no verified base: {why}; read the whole unit')
            continue
        key = ('prior', commit, tuple(unit))
        if key in shown:
            out.append(f'unit since earlier review: CHANGED; diff from {commit[:12]} as printed above for this unit')
            continue
        shown.add(key)
        diff = git(root, 'diff', '--no-color', commit, '--', *unit)
        out.append(f'unit since earlier review: CHANGED; diff from {commit[:12]} (digest verified) to the working tree:')
        out.append((diff or b'').decode('utf-8', 'replace').rstrip() or '(no textual difference)')
    return out


def sibling_view(fn, analysis):
    """FNV counterparts of one function from the sibling index, for the undeclared-reuse check."""
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent / 'ghidra'))
        import export_pack
        index = export_pack.sibling_index(analysis)
    except Exception as exc:  # noqa: BLE001 - a reading aid; the packet still prints
        return [f'sibling counterparts: not available ({type(exc).__name__}: {exc})']
    if index is None:
        return []
    hits = index['by_rva'].get(fn['rva'], [])
    if not hits:
        return ['sibling counterparts: none joined in the index (not proof of absence; the class may still be in the clone)']
    out = ['sibling counterparts (compare for undeclared reuse; FNV path:line):']
    for r, o in hits:
        how = 'same name' if o['how'] == 'name' else f'same slot {o.get("slot")} (positional guess)'
        where = f'{r["source"]}:{r["line"]}' if r.get('line') else f'{r["source"]} (no line found)'
        out.append(f'  {r.get("class")}::{r.get("method")} {where}; {how}')
    return out


def template_view(fn, record, prior):
    """A blank block in the reviewer.md output format for this function."""
    out = ['', 'review block to fill (reviewer.md "Output"; compute source_digest yourself):', '```text',
           f'## {fn["build_id"]} 0x{fn["rva"]:x} {fn["size"]}', '',
           'verdict: <approve|reject|escalate>',
           'escalation_category: <provenance|legal|systemic|other|none>',
           'review_kind: full',
           f'source_paths: {" ".join(record["source"]["translation_unit"])}',
           'source_digest: <tu-sha256-v1 digest you computed>',
           f'report_path: {fn["report"]}',
           'report_binding: <agree|disagree|missing>, <one line>',
           'checks:',
           '  plausible_source: <pass|fail>, <one line>',
           '  provenance: <pass|fail>, <one line>',
           '  claim_scope: <pass|fail>, <one line>',
           '  publication_hygiene: <pass|fail>, <one line>',
           'blocking_findings: <none, or one "  - <item>" line each below>',
           'naming_findings: <none, or one "  - <item>" line each below; published>']
    for _path, sha, title, *_ in prior or []:
        out.append(f'prior_review: {title} {sha}')
    out += ['reasons: <short prose; no code, bytes or disassembly>', '```']
    return out


def unit_view(root, compiled, fns, notes, community=True, extras=None):
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
    hits = None
    if community:
        out += community_view(root, unit)
        hits, lines = origin_view(root, unit)
        out += lines
    shown = set()
    extras = extras or {}
    prior = extras.get('prior')
    for fn in fns:
        record = records[fn['id']]
        out += function_view(root, fn, record, shown)
        if hits is not None:
            import check_origin
            out.append(check_origin.function_lines(fn['name'], hits))
        if extras.get('analysis') is not None:
            out += sibling_view(fn, extras['analysis'])
        entries = (prior or {}).get((fn['build_id'], fn['rva']))
        if entries:
            out += prior_view(root, fn, record, entries, extras.get('prior_ref'), shown)
        elif prior is not None:
            out.append('earlier review: none of the --prior-review files has a block for this function')
        if extras.get('template'):
            out += template_view(fn, record, entries)
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
    out.append(f'code section: {section or "absent (record from before comparator version 2)"}')
    review = _json_or_none(root / review_record_path(fn))
    if review is None:
        out.append('review record: none' + ('' if fn['status'] == 'matched' else '; needs: full review'))
        return out
    out.append(f'review record: {review.get("review_kind", "full")} by {review.get("reviewer_model")} '
               f'({review.get("review_task_id")}, {review.get("review_date")}) on digest {review.get("source_digest")}')
    # A new review restates the open naming findings (tier 2), so it needs the current ones.
    naming = review.get('naming_findings')
    named = {True: 'checked', False: 'open'}.get(fn.get('named'), 'not assessed')
    if naming is None:
        out.append(f'naming findings: not recorded (record predates them); names: {named}')
    else:
        out.append(f'naming findings: {len(naming) or "none"}; names: {named}')
        out += [f'  - {item}' for item in naming]
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
    if old is not None and old == section:
        out.append('or: label-only re-acceptance with no review (tools/accept_function.py --label-only); '
                   'a review is then only for closing naming findings')
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
    p.add_argument('--no-community', action='store_true',
                   help='Omit the community declarations of COMMUNITY-labelled names')
    p.add_argument('--template', action='store_true',
                   help='End each function with a blank review block in the reviewer.md output format')
    p.add_argument('--prior-review', action='append', metavar='FILE',
                   help='An earlier review to cite as context (repeatable); implies --template')
    p.add_argument('--prior-ref', metavar='COMMIT',
                   help='Commit holding the source the earlier review saw (its digest is verified)')
    p.add_argument('--analysis', type=Path, default=None,
                   help='Directory with fnv_index.jsonl (default .local/analysis)')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = p.parse_args(argv)
    root = args.root
    if args.prior_ref and not args.prior_review:
        p.error('--prior-ref needs --prior-review')
    data = json.loads((root / 'data/progress.json').read_text())
    try:
        prior = prior_reviews(root, args.prior_review) if args.prior_review else None
    except (OSError, UnicodeDecodeError) as exc:
        print(f'cannot read --prior-review: {exc}', file=sys.stderr)
        return 1
    if args.prior_ref and git(root, 'rev-parse', '--verify', '--quiet', f'{args.prior_ref}^{{commit}}') is None:
        print(f'--prior-ref {args.prior_ref} is not a commit', file=sys.stderr)
        return 1
    extras = {'prior': prior, 'prior_ref': args.prior_ref, 'template': args.template or bool(prior),
              'analysis': args.analysis or (root / '.local/analysis')}
    picked = select(data, root, set(args.functions), args.stale, args.all, prior)
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
    if extras['template']:
        out += ['', 'review document header (reviewer.md "Output"):', '```text', '# Review <task-id>', '',
                'reviewer_model: <model id>', 'fresh_context: yes', 'drafted_or_triaged_any_reviewed_function: no',
                'gates_in_force: <list>', 'source_revision: <git commit>', 'sampling_second_pass: <yes|no>',
                'decompiler_output_read: <yes|no>', '```']
    for compiled, fns in sorted(units.items()):
        out += [''] + unit_view(root, compiled, fns, not args.no_notes, not args.no_community, extras)
    print('\n'.join(out))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
