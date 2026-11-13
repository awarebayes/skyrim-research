"""Import isolated family workflow metadata without rewriting review evidence.

The caller holds the shared state lock. Public inputs remain in the source worktree;
this imports private scheduling state, not acceptances or version baselines.
"""
import copy
import hashlib
import json
from pathlib import Path
import re

import accept_function as af
import family_review as fr
from flow_state import atomic_write, state_lock


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def within(base, name):
    path = (base / name).resolve()
    fr.require(path.is_relative_to(base.resolve()) and path.is_file(), 'missing or escaping import file: ' + str(name))
    return path


def import_state(root, destination, source, reviews):
    """Merge under the CLI's destination lock; validate everything before publishing files.

    Receipts freeze allocation and input hashes before writes, making an interrupted
    import resumable. A complete receipt permits subsequent legitimate group progress.
    No source event is replayed as a new session, dispatch or version baseline.
    """
    import flow
    root, destination, source, reviews = map(lambda p: Path(p).resolve(), (root, destination, source, reviews))
    fr.require(destination == af.active_flow_dir(root), 'import destination must be shared flow state')
    fr.require(source != destination and source.is_dir(), 'source must be an isolated flow directory')
    source_root = source.parent.parent
    fr.require(source.parent.name == '.local' and source.name == 'flow', 'source must be a worktree .local/flow')
    fr.require(reviews == (source_root / '.local/reviews').resolve(), 'reviews must belong to the source worktree')
    fr.require(af.active_flow_dir(source_root) == destination, 'source is not a worktree of this repository')
    shared_root = destination.parent.parent
    with state_lock(source):
        return _import(flow, source_root, shared_root, destination, source, reviews)


def _import(flow, root, shared_root, destination, source, reviews):
    snapshots = {}

    def capture(path):
        path = Path(path)
        blob = path.read_bytes()
        key = str(path.resolve())
        fr.require(key not in snapshots or snapshots[key] == sha(blob), 'source changed during import: ' + key)
        snapshots[key] = sha(blob)
        return blob

    def read(path):
        return json.loads(capture(path), object_pairs_hook=fr.unique_fields)

    data = read(root / 'data/progress.json')
    _, target = af.load(root)
    capture(root / 'builds/target.json')
    by_id = {fn['id']: fn for fn in data['functions']}
    by_rva = {flow.hexrva(fn['rva']): fn for fn in data['functions'] if fn['build_id'] == data['target_build_id']}
    original = {p.stem: read(p) for p in sorted((source / 'groups').glob('*.json'))}
    fr.require(bool(original), 'source has no review groups')
    families = flow.family_manifests(root)
    fr.require(bool(families), 'source has no family plans')
    records = {}

    def check_fn(fn):
        if fn['id'] not in records:
            rec = af.validate_match(fn, target, root)
            capture(within(root, fn['report']))
            for path in rec['source']['translation_unit']:
                capture(within(root, path))
            records[fn['id']] = rec
        return records[fn['id']]

    family_files = {}
    for path, family in families.items():
        family_files[path] = capture(root / path)
        fr.validate_family(family, approved=family['review'] is not None)
        fr.require(Path(path).stem == fr.family_key(family), 'family manifest identity mismatch')
        for field in ('template_source', 'parameter_source'):
            src = family[field]
            fr.require(sha(capture(within(root, src['path']))) == src['sha256'], 'template or extraction digest mismatch')
        for fid, digest in family['first_members'].items():
            fn = by_id[fid]
            rec = check_fn(fn)
            fr.check_member(family, fn, rec, ranges=False)
            fr.require(fr.member_digest(fn, rec) == digest, 'first member digest mismatch: ' + fid)
        if family['review']:
            fr.private_approval(root, family, family['review']['profile'])
    # Validate every generated member, including those not in an initial review group.
    for fn in data['functions']:
        if not fn.get('report'):
            continue
        rec = fr.read(root, fn['report'])
        active = [f for f in families.values() if not f.get('superseded_by') and rec.get('origin') == f['origin']]
        for family in active:
            fr.check_member(family, fn, check_fn(fn), ranges=False)
    for path, batch in flow.family_batches(root).items():
        family = families[batch['family_path']]
        fr.validate_batch(batch, family, planned=batch['sample'] is None)
        family_files[path] = capture(root / path)
        for fid, digest in batch['members'].items():
            fr.require(fr.member_digest(by_id[fid], check_fn(by_id[fid])) == digest, 'batch member digest mismatch')
        if batch['sample'] is not None:
            fr.ordering(root, path, batch)
    review_blobs = {}
    for path in sorted(reviews.rglob('*')):
        if path.is_file():
            # Archive rejected/retired reviews too, so prior holds cannot disappear.
            review_blobs[path.relative_to(reviews).as_posix()] = capture(within(reviews, path.relative_to(reviews)))
    for name, g in original.items():
        fr.require(g['name'] == name and re.fullmatch(r'g\d+(?:-[sc])?', name), 'invalid source group identity')
        fr.require(g['kind'] in ('review', 'sampling') and not g.get('integrated'), 'only unintegrated review groups can be imported')
        fr.require(g.get('pair') is None or g['pair'] in original, 'missing paired group')
        fr.require(g['build_id'] == data['target_build_id'], 'group build differs')
        for rva in g['functions']:
            check_fn(by_rva[rva])
        file = flow.review_path(root, g)
        if file.is_file():
            status, blocks = flow.read_review(root, g, data['functions'])
            fr.require(status == 'ok', 'source review ' + status)
            fr.require(set(blocks) == set(g['functions']), 'review population differs from group')
            for rva, block in blocks.items():
                fr.require(block['source_digest'] == check_fn(by_rva[rva])['source']['digest'], 'review unit digest mismatch')
        rerun = g.get('rerun')
        if rerun:
            path = within(root, rerun['file'])
            blob = capture(path)
            if (path.parent / 'sample.json').is_file():
                capture(path.parent / 'sample.json')
            rows = {}
            for line in blob.decode().splitlines():
                rva, verdict = re.search(r'\b(0x[0-9a-f]+)\b', line), re.search(r'\b(AGREE|DISAGREE)\s*$', line)
                if rva and verdict:
                    rows.setdefault(rva[1], set()).add(verdict[1])
            agree = [r for r in g['sampled'] if rows.get(r) == {'AGREE'}]
            fr.require(rerun['agree'] == agree and rerun['not_agree'] == [r for r in g['sampled'] if r not in agree],
                       'sampling rerun record mismatch')
    # Saved family approvals are verified even before activation, without activating them.
    for filename, blob in review_blobs.items():
        if filename.endswith('.family.json') and '/' not in filename:
            doc = json.loads(blob, object_pairs_hook=fr.unique_fields)
            hits = [f for f in families.values() if fr.digest(fr.spec(f)) == doc['spec_sha256']]
            fr.require(len(hits) == 1, 'family approval spec digest mismatch')
            family = copy.deepcopy(hits[0])
            family['review'] = {k: doc[k] for k in ('review_task_id', 'reviewer_model', 'profile', 'spec_sha256')}
            family['review']['review_sha256'] = sha(blob)
            fr.validate_family(family)
            fr.private_approval(root, family, doc['profile'])
    event_blob = capture(source / 'events.jsonl') if (source / 'events.jsonl').exists() else b''
    for path, digest in snapshots.items():
        fr.require(sha(Path(path).read_bytes()) == digest, 'source changed during import: ' + path)
    identity = sha(str(source).encode())
    receipt_path = destination / 'imports' / (identity + '.json')
    receipt = fr.read(destination, receipt_path) if receipt_path.exists() else None
    if receipt:
        fr.require(receipt['inputs'] == snapshots, 'import source changed since its recorded snapshot')
        if receipt['complete']:
            for old, new in receipt['groups'].items():
                fr.require(flow.load_group(destination, new).get('import_id') == identity, 'imported group was replaced')
            for rel, digest in receipt['outputs'].items():
                if rel.startswith('groups/'):
                    continue  # mutable workflow state; immutable evidence is still checked below
                fr.require(sha((destination / rel).read_bytes()) == digest, 'imported file changed: ' + rel)
            return receipt
    existing = flow.groups(destination, allow_incomplete=True)
    if receipt:
        mapping = receipt['groups']
    else:
        n = max([int(m[1]) for k in existing if (m := re.fullmatch(r'g(\d+)(?:-[sc])?', k))] or [0])
        bases = sorted({re.match(r'g\d+', k)[0] for k in original})
        base_map = {old: f'g{n+i+1:03d}' for i, old in enumerate(bases)}
        mapping = {old: base_map[re.match(r'g\d+', old)[0]] + old[len(re.match(r'g\d+', old)[0]):] for old in original}
    outputs, paths = {}, {}

    def output(path, blob):
        rel = str(path.relative_to(destination)) if path.is_relative_to(destination) else str(Path('..') / path.relative_to(shared_root / '.local'))
        fr.require(rel not in outputs or outputs[rel] == blob, 'conflicting import output')
        outputs[rel], paths[rel] = blob, path

    filenames = {}
    for filename, blob in review_blobs.items():
        pattern = r'(?<![a-z0-9])(' + '|'.join(re.escape(k) for k in sorted(mapping, key=len, reverse=True)) + r')(?=\.|-r\d+\.)'
        renamed = re.sub(pattern, lambda match: mapping[match[1]], filename)
        filenames[filename] = renamed
        output(shared_root / '.local/reviews' / renamed, blob)
    for name, original_group in original.items():
        g = copy.deepcopy(original_group)
        g.update(name=mapping[name], pair=mapping.get(g.get('pair')), import_id=identity)
        saved = f'{g["task_id"]}.md'
        if saved in review_blobs:
            g['saved_review'] = '.local/reviews/' + filenames[saved]
        else:
            g['task_id'] = g['task_id'].replace(name, mapping[name])
        # Review titles are immutable. Refuse any incompatible profile for that title.
        fr.require(all(e.get('profile', 'cheap') == g.get('profile', 'cheap') for e in existing.values()
                       if e['task_id'] == g['task_id']), 'review task has conflicting existing profile')
        if g.get('rerun'):
            blob = (root / g['rerun']['file']).read_bytes()
            dest = destination / 'rerun' / mapping[name] / 'compare.txt'
            output(dest, blob)
            g['rerun']['file'] = str(dest)
            sample_file = (root / original_group['rerun']['file']).parent / 'sample.json'
            if sample_file.is_file():
                sample_blob = capture(sample_file)
                sample = json.loads(sample_blob, object_pairs_hook=fr.unique_fields)
                selection = sample.get('reviewed', {})
                fr.require(not sample.get('label_only') and
                           sorted(r for rows in selection.values() for r in rows) == sorted(g['sampled']),
                           'sampling rerun selection mismatch')
                fr.require(all(flow.unit_of(root, by_rva[r])[0] == unit for unit, rows in selection.items() for r in rows),
                           'sampling rerun unit binding mismatch')
                output(dest.parent / 'sample.json', sample_blob)
        # Render into the transaction; never overwrite the source worktree's files.
        by_rva = {flow.hexrva(fn['rva']): fn for fn in data['functions']}
        brief_path = shared_root / '.local/briefs' / ('import-' + g['name'] + '.md')
        g['brief'] = str(brief_path)
        if g.get('saved_review'):
            text = within(root, original_group['brief']).read_text() if original_group.get('brief') else flow.write_review_brief(root, g, by_rva, render_only=True)
        elif g.get('family_review_path'):
            member_path = brief_path.with_name('import-' + g['name'] + '-members.md')
            g['member_brief'] = str(member_path)
            output(member_path, flow.write_review_brief(root, g, by_rva, render_only=True).encode())
            text = flow.family_brief(root, g['family_review_path'], g.get('profile', 'cheap'), source,
                                     render_only=True, attached_group=g)
        else:
            text = flow.write_review_brief(root, g, by_rva, render_only=True)
        output(brief_path, text.encode())
        if g['kind'] == 'review' and g.get('sampled') and not g.get('rerun'):
            text, sample = flow.write_rerun_brief(root, g, by_rva, render_only=True)
            output(shared_root / '.local/briefs' / ('rerun-' + g['name'] + '.md'), text.encode())
            output(destination / 'rerun' / g['name'] / 'sample.json', sample)
        output(destination / 'groups' / (g['name'] + '.json'), encoded(g))
    for path, blob in family_files.items():
        output(destination / 'imports' / identity / path, blob)
    output(destination / 'imports' / identity / 'events.jsonl', event_blob)
    for rel, blob in outputs.items():
        path = paths[rel]
        fr.require(not path.exists() or path.read_bytes() == blob, 'refuse to overwrite different import entry: ' + str(path))
    receipt = dict(import_schema=1, source=str(source), inputs=snapshots, groups=mapping,
                   review_files=filenames, outputs={k: sha(v) for k,v in outputs.items()}, complete=False)
    atomic_write(receipt_path, encoded(receipt))
    # A retry uses the same allocation and accepts only byte-identical partial files.
    for rel, blob in outputs.items():
        atomic_write(paths[rel], blob)
    receipt['complete'] = True
    atomic_write(receipt_path, encoded(receipt))
    flow.log_event(destination, 'import-state', import_id=identity, groups=mapping)
    return receipt
