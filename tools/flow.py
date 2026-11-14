#!/usr/bin/env python3
"""Pipeline state and next steps, so a routine orchestrator executes a list instead of tracking state.

    python3 tools/flow.py import-state <other .local/flow> --reviews <other .local/reviews>
    python3 tools/flow.py session-start                  # mark the start of a work session
    python3 tools/flow.py next-actions                   # the exact next steps, in order
    python3 tools/flow.py status [--functions]           # counts per state, groups, stale claims
    python3 tools/flow.py review-group [--max 18]        # group confirmed functions, pick the sample, write briefs
    python3 tools/flow.py dispatched <group>             # a Reviewer was started on that group's brief
    python3 tools/flow.py void-review <group> --setup-failure --reason TEXT  # retire specified setup-failure verdicts
    python3 tools/flow.py redo-review <group>            # new task id after a review the parser refused
    python3 tools/flow.py record-rerun <group> --compare FILE   # sampling re-run result (AGREE/DISAGREE rows)
    python3 tools/flow.py integrate <group> [--no-push] [--approved-only]  # enqueue; --run drains the lane
    python3 tools/flow.py integrate-groups <group> <group> --name <batch>  # enqueue a multi-group selection
    python3 tools/flow.py sync                           # fast-forward the shared checkout after an integration
    python3 tools/flow.py brief drafter|confirm|triage|rerun|direction ...   # write a brief file under .local/briefs/
    python3 tools/flow.py baseline <component> <value> <count>  # versions already past their first 20 (a strong-role call)
    python3 tools/flow.py event friction|direction-check [--note ...]   # record that a report was produced

Each function moves through fixed states, derived from the files that already record them, so the
state cannot drift from the evidence:

    queued, drafting            the work queue (tools/work_queue.py): open or claimed unit
    draft-failed, drafted-pass  the queue's result lines (the last attempt printed FAIL or PASS)
    confirm-stale               a match record exists but no longer binds the working-tree unit
    confirmed                   data/progress.json names a match record with two compile hosts that binds the unit
    review-pending              in a review group whose review file is not saved yet
    approved, rejected, escalated, review-malformed, review-missing   the saved review file says so
    accepted                    data/progress.json says matched
    pushed                      origin's data/progress.json says matched with the same Reviewer record

What this tool keeps itself, under `.local/flow/` (or --flow-dir, $SKYRIM_FLOW_DIR): review groups
(`groups/<name>.json`: functions, task id, brief, sample, re-run result, integration), the event log
(`events.jsonl`, for the friction report) and version baselines (`versions.json`). Nothing here is
evidence: acceptance still happens only through tools/accept_function.py, and `integrate` refuses
wherever the manual process refuses (docs/verification.md). Briefs go to `.local/briefs/`.
"""
import argparse
import datetime as dt
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import time

# CLI helpers must share this module's exceptions and locks, rather than loading it twice.
if __name__ == '__main__':
    sys.modules['flow'] = sys.modules[__name__]

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import accept_function as af  # noqa: E402
import family_review as fr  # noqa: E402
import profiles  # noqa: E402
from source_digest import include_closure, tu_digest  # noqa: E402
from symbol_map import history_name  # noqa: E402
import work_queue as wq  # noqa: E402
import draft_worktrees as drafts  # noqa: E402
from flow_state import atomic_write, state_lock, require_complete, inherited_lock  # noqa: E402

ROOT = TOOLS.parent
REVIEWS = '.local/reviews'
BRIEFS = '.local/briefs'
QUEUES = '.local/queue'
# The first N acceptances under a new version of any component get the second Reviewer pass.
FIRST_N = 20
SAMPLE_RATE = 0.05
# Accepted functions between two direction checks (at least one per work session anyway).
DIRECTION_EVERY = 200
DEFAULT_GROUP_MAX = 18
# A claim this old is listed for a look: the worker may have asked `next` once too often.
CLAIM_LOOK_SECONDS = 45 * 60
BLOCKING_ESCALATIONS = ('provenance', 'legal', 'systemic')
QUEUE_PROFILE = {'small': 'cheap', 'normal': 'cheap', 'mid': 'cheap', 'full': 'full'}
STATES = ('queued', 'drafting', 'draft-failed', 'drafted-pass', 'confirm-stale', 'confirmed', 'review-pending',
          'review-missing', 'review-malformed', 'approved', 'rejected', 'escalated', 'accepted', 'pushed')


class FlowError(Exception):
    pass


def refuse(ok, message):
    if not ok:
        raise FlowError(message)


def utc(t=None):
    return (dt.datetime.now(dt.timezone.utc) if t is None else t).strftime('%Y-%m-%dT%H:%M:%SZ')


def flow_dir(root, arg=None):
    return Path(arg or os.environ.get('SKYRIM_FLOW_DIR') or Path(root) / '.local' / 'flow')


def hexrva(rva):
    return f'0x{int(rva, 16) if isinstance(rva, str) else rva:x}'


# ------------------------------------------------------------------ files this tool keeps

def log_event(fdir, event, **detail):
    with state_lock(fdir):
        path = fdir / 'events.jsonl'
        before = path.read_bytes() if path.exists() else b''
        atomic_write(path, before + (json.dumps(dict(detail, event=event, time=utc()), sort_keys=True) + '\n').encode())


def events(fdir):
    path = fdir / 'events.jsonl'
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.is_file() else []


def groups(fdir, allow_incomplete=False):
    if not allow_incomplete:
        require_complete(fdir)
    gdir = fdir / 'groups'
    return {p.stem: json.loads(p.read_text()) for p in sorted(gdir.glob('*.json'))} if gdir.is_dir() else {}


def save_group(fdir, g):
    with state_lock(fdir):
        atomic_write(fdir / 'groups' / f'{g["name"]}.json', (json.dumps(g, indent=2, sort_keys=True) + '\n').encode())


def load_group(fdir, name, allow_incomplete=False):
    if not allow_incomplete:
        require_complete(fdir)
    path = fdir / 'groups' / f'{name}.json'
    refuse(path.is_file(), f'no review group {name} (python3 tools/flow.py status lists them)')
    return json.loads(path.read_text())


def versions(fdir):
    path = fdir / 'versions.json'
    return json.loads(path.read_text()) if path.is_file() else {'baseline': {}}


# ------------------------------------------------------------------ inputs read from the tree

def inventory(root):
    return json.loads((Path(root) / 'data/progress.json').read_text())


def queue_units(root):
    """[(queue dir, profile, unit dict, state, holder, claim)] over every queue under .local/queue/."""
    out = []
    base = Path(root) / QUEUES
    for qdir in sorted(base.iterdir()) if base.is_dir() else []:
        if not (qdir / 'queue.tsv').is_file():
            continue
        profile = QUEUE_PROFILE.get(qdir.name, qdir.name if qdir.name in profiles.PROFILES else profiles.DEFAULT)
        for state, who, u in wq.status(qdir):
            lock = qdir / 'claims' / f'{u["key"]}.lock'
            claim = wq.read_claim(lock) if lock.exists() else None
            out.append((qdir, profile, u, state, who, claim))
    return out


def queue_results(root):
    """Result lines of every queue, each stamped with the queue's profile when it lacks one."""
    recs = []
    base = Path(root) / QUEUES
    for qdir in sorted(base.iterdir()) if base.is_dir() else []:
        path = qdir / 'results.jsonl'
        if path.is_file():
            for line in path.read_text().splitlines():
                if line.strip():
                    r = json.loads(line)
                    r.setdefault('profile', QUEUE_PROFILE.get(qdir.name, qdir.name if qdir.name in profiles.PROFILES else profiles.DEFAULT))
                    r['queue'] = qdir.name
                    recs.append(r)
    return recs


def record_state(root, fn):
    """'confirmed', 'confirm-stale' or None for an inventory entry's match record."""
    rel = fn.get('report')
    if not rel or not (Path(root) / rel).is_file():
        return None
    rec = json.loads((Path(root) / rel).read_text())
    hosts = {r.get('compiled_on') for r in rec.get('runs') or []}
    try:
        harvested = drafts.source_for(root, rec['source']['compiled'], fn['rva'])
        if harvested and not harvested.get('integrated'):
            from review_packet import digest_at
            digest = digest_at(root, harvested['commit'], rec['source']['translation_unit'])
        else:
            digest = tu_digest(root, rec['source']['translation_unit'])
    except (OSError, ValueError, KeyError):
        return 'confirm-stale'
    return 'confirmed' if len(hosts) >= 2 and digest == rec['source'].get('digest') else 'confirm-stale'


def git(root, *args, check=True):
    command, extra = ['git', *args], {}
    if args[:2] == ('add', '--') and len(args) > 2:
        paths = [os.fsdecode(path) for path in args[2:]]
        refuse(all('\0' not in path for path in paths), 'NUL in git add pathspec')
        command = ['git', 'add', '--pathspec-from-file=-', '--pathspec-file-nul']
        extra['input'] = ''.join(path + '\0' for path in paths)
    r = subprocess.run(command, cwd=root, capture_output=True, text=True, **extra)
    if check and r.returncode:
        raise FlowError(f'git {" ".join(args)} failed: {r.stderr.strip() or r.stdout.strip()}')
    return r.stdout.strip()


def blob_id(data):
    return hashlib.sha1(b'blob %d\0' % len(data) + data).hexdigest()


def origin_matched(root, branch='main'):
    """{function id: git blob id of its Reviewer record} for entries matched on origin/<branch>
    (as last fetched), or None when there is no such ref."""
    ref = f'origin/{branch}'
    if subprocess.run(['git', 'rev-parse', '--verify', '--quiet', ref], cwd=root, capture_output=True).returncode:
        return None
    try:
        data = json.loads(git(root, 'show', f'{ref}:data/progress.json'))
        listing = git(root, 'ls-tree', '-r', ref, '--', 'reports/')
    except (FlowError, ValueError):
        return None
    blobs = {}
    for line in listing.splitlines():
        meta, path = line.split('\t', 1)
        blobs[path] = meta.split()[2]
    return {fn['id']: blobs.get(f'reports/{fn["build_id"]}/0x{fn["rva"]:x}.review.json')
            for fn in data.get('functions', []) if fn.get('status') == 'matched'}


def review_path(root, task):
    # Imported reviews keep their signed-off title and bytes, with a distinct filename.
    rel = (task.get('saved_review') or f'{REVIEWS}/{task["task_id"]}.md') if isinstance(task, dict) else f'{REVIEWS}/{task}.md'
    path = Path(root) / rel
    refuse(path.resolve().is_relative_to((Path(root) / REVIEWS).resolve()), 'review path escapes private reviews')
    return path


def read_review(root, g, functions):
    """(status, {rva: block}) of a group's saved review: status 'missing', 'malformed: <why>' or 'ok'."""
    path = review_path(root, g)
    if not path.is_file():
        return 'missing', {}
    try:
        text = path.read_text(encoding='utf-8')
        title, header, blocks = af.review_blocks(text)
        af.refuse(title == g['task_id'], f'title is {title!r}, not {g["task_id"]!r}')
        af.refuse_malformed(header, blocks, functions)
        af.refuse(header.get('fresh_context') == 'yes', 'fresh_context is not yes')
        af.refuse(header.get('drafted_or_triaged_any_reviewed_function') == 'no', 'drafted_or_triaged is not no')
        model = header.get('reviewer_model')
        af.refuse(af.reviewer_matches(g['reviewer_model'], model), 'reviewer_model does not match assigned model')
        profile = g.get('profile', profiles.DEFAULT)
        if g['kind'] == 'sampling':
            af.refuse(af.strong_reviewer_admitted(root, model, profile),
                      'sampling reviewer_model must be Opus or profile-admitted Sol')
        else:
            af.refuse(af.reviewer_admitted(root, model, profile), 'reviewer_model is not admitted for group profile')
        want = 'yes' if g['kind'] == 'sampling' else 'no'
        af.refuse(header.get('sampling_second_pass') == want, f'sampling_second_pass is not {want}')
    except (af.Refused, UnicodeDecodeError) as exc:
        return f'malformed: {exc}', {}
    out = {}
    for parts, body in blocks:
        if (len(parts) == 3 and parts[0] == g['build_id'] and re.fullmatch(r'0x[0-9a-f]+', parts[1])
                and parts[1] in g['functions']):
            out[parts[1]] = body
    return 'ok', out


def prior_holds(root):
    """{(rva hex, source digest): review task id} for reject and escalate blocks in saved reviews.

    Read leniently (a review the strict parser refuses still records that a Reviewer did not approve)."""
    held = {}
    rdir = Path(root) / REVIEWS
    for path in sorted(rdir.glob('*.md')) if rdir.is_dir() else []:
        try:
            title, _, blocks = af.review_blocks(path.read_text(encoding='utf-8'))
        except (UnicodeDecodeError, OSError):
            continue
        for parts, body in blocks:
            if len(parts) >= 2 and re.fullmatch(r'0x[0-9a-f]+', parts[1]) and body.get('verdict') in ('reject', 'escalate'):
                if body.get('source_digest'):
                    held[(parts[1], body['source_digest'])] = title or path.stem
    return held


# ------------------------------------------------------------------ state of every function

def function_states(root, fdir, branch='main', online=True, review_rvas=None):
    """{rva hex: {'state', 'id', 'name', 'unit', 'group', 'profile', 'detail'}} for every tracked function."""
    root = Path(root)
    data = inventory(root)
    build = data['target_build_id']
    by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == build}
    out = {}
    # Queue first; later evidence overrides it.
    results = {}
    for r in queue_results(root):
        if 'rva' in r:
            results[hexrva(r['rva'])] = r
    for qdir, profile, u, state, who, claim in queue_units(root):
        for rva in u['functions']:
            rva = hexrva(rva)
            st = {'open': 'queued', 'claimed': 'drafting', 'stale': 'drafting'}.get(state)
            r = results.get(rva)
            if state == 'done':
                st = 'drafted-pass' if r and r.get('result') == 'pass' else 'draft-failed'
            out[rva] = {'state': st, 'unit': u['dir'], 'queue': str(qdir), 'profile': (r or {}).get('profile') or profile,
                        'detail': (r or {}).get('reason') or (f'claimed by {who}' if who else '')}
    for rva, fn in by_rva.items():
        rs = record_state(root, fn)
        if rs is None and fn['status'] != 'matched':
            continue
        row = out.setdefault(rva, {'unit': None, 'profile': None, 'detail': ''})
        row.update(id=fn['id'], name=fn.get('name'), size=fn['size'])
        if rs:
            row['state'] = rs
    # A reject or escalate of this exact source in any saved review still holds (docs/verification.md:
    # only a later Reviewer pass on a revised source lifts it), so such a function is not regrouped.
    held = prior_holds(root)
    for rva, row in out.items():
        if row.get('state') == 'confirmed' and row.get('id'):
            fn = by_rva[rva]
            digest = json.loads((root / fn['report']).read_text())['source']['digest']
            if (rva, digest) in held:
                row['state'], row['detail'] = 'rejected', f'held by {held[(rva, digest)]}'
                row['held'] = True
    gs = groups(fdir)
    for name, g in gs.items():
        if g['kind'] != 'review' or g.get('superseded_by'):
            continue
        if review_rvas is not None and not set(g['functions']) & review_rvas:
            continue
        status, blocks = read_review(root, g, data['functions'])
        for rva in g['functions']:
            row = out.setdefault(rva, {'unit': None, 'profile': None, 'detail': ''})
            row['group'] = name
            if status == 'missing':
                row['state'], row['detail'] = 'review-pending', 'dispatched' if g.get('dispatched') else 'not dispatched'
            elif status != 'ok':
                row['state'], row['detail'] = 'review-malformed', status
            elif rva not in blocks:
                row['state'], row['detail'] = 'review-missing', 'the review has no block for it'
            else:
                v = blocks[rva].get('verdict')
                row['state'] = {'approve': 'approved', 'reject': 'rejected'}.get(v, 'escalated')
                row['detail'] = blocks[rva].get('escalation_category', '') if v == 'escalate' else ''
    remote = origin_matched(root, branch) if online else None
    for rva, fn in by_rva.items():
        if fn['status'] != 'matched':
            continue
        row = out[rva]
        row['state'] = 'accepted'
        rec = root / f'reports/{build}/{rva}.review.json'
        if remote is not None and rec.is_file() and remote.get(fn['id']) == blob_id(rec.read_bytes()):
            row['state'] = 'pushed'
    return out


# ------------------------------------------------------------------ sampling

def component_values(root, rva, row, data, model='opus'):
    """The version components the first-20 rule counts (docs/verification.md, Sampling safeguard)."""
    fn = next(f for f in data['functions'] if f'0x{f["rva"]:x}' == rva and f['build_id'] == data['target_build_id'])
    rec = json.loads((Path(root) / fn['report']).read_text())

    def file_hash(rel):
        p = Path(root) / rel
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12] if p.is_file() else 'absent'
    profile = row.get('profile') or 'unrecorded'
    card = profiles.PROFILES.get(profile, {}).get('project_docs', ['unrecorded'])[-1]
    if Path(row.get('queue') or '').name in ('normal', 'mid'):
        card = 'docs/drafter-card-normal.md'
    return {'recipe': rec['recipe']['sha256'][:12], 'compiler': rec['toolchain_pin']['sha256'][:12],
            'drafter_prompt': f'{profile}:{file_hash(card) if card.startswith("docs/") else card}',
            'reviewer_prompt': file_hash('.claude/agents/reviewer.md') + file_hash('docs/reviewer-runbook.md'),
            'reviewer_model': model,
            'acceptance_rule': hashlib.sha256((file_hash('docs/verification.md') + file_hash('tools/accept_function.py'))
                                              .encode()).hexdigest()[:12]}


def accepted_counts(root, fdir, states):
    """{component: {value: count}} of functions accepted through flow groups, plus recorded baselines."""
    counts = {}
    for comp, vals in versions(fdir).get('baseline', {}).items():
        for v, n in vals.items():
            counts.setdefault(comp, {})[v] = n
    for g in groups(fdir).values():
        if g['kind'] != 'review' or g.get('superseded_by'):
            continue
        for rva, comps in (g.get('components') or {}).items():
            if states.get(rva, {}).get('state') in ('accepted', 'pushed'):
                for comp, v in comps.items():
                    counts.setdefault(comp, {})[v] = counts.get(comp, {}).get(v, 0) + 1
    return counts


def choose_sample(name, rvas, comps, counts, seed='flow'):
    """Sampled RVAs: ceil(5%) at random (seeded by the group name), plus every function whose version
    of any component has fewer than FIRST_N acceptances counted so far (pending ones included)."""
    rng = random.Random(f'{seed}:{name}')
    chosen = set(rng.sample(sorted(rvas), math.ceil(SAMPLE_RATE * len(rvas)))) if rvas else set()
    running = {c: dict(v) for c, v in counts.items()}
    for rva in sorted(rvas):
        young = [c for c, v in comps[rva].items() if running.get(c, {}).get(v, 0) < FIRST_N]
        if young:
            chosen.add(rva)
        for c, v in comps[rva].items():
            running.setdefault(c, {})[v] = running.get(c, {}).get(v, 0) + 1
    return sorted(chosen, key=lambda r: int(r, 16))


# ------------------------------------------------------------------ family reviews

def family_manifests(root):
    return {p.relative_to(root).as_posix(): fr.read(root, p.relative_to(root))
            for p in sorted((root / 'reports').glob('*/families/*.json'))}


def family_batches(root):
    return {p.relative_to(root).as_posix(): fr.read(root, p.relative_to(root))
            for p in sorted((root / 'reports').glob('*/family-batches/*.json'))}


def family_reviewed_gate(root, fdir, required, data, target):
    """Reviewed members keep the ordinary parser, comparator gate and second-pass safeguard."""
    by_id = {fn['id']: fn for fn in data['functions']}
    for fid in sorted(required):
        fn = by_id[fid]
        fr.require(fn['status'] == 'matched', f'{fid}: sampled or first-20 member needs its own approving review')
        rec = af.validate_match(fn, target, root)
        rv = af.validate_review(fn, rec, root)
        fr.require(rv.get('review_kind') in ('full', 'delta'), f'{fid}: needs an individual full or delta review')
        rva = hexrva(fn['rva'])
        candidates = [g for g in groups(fdir).values() if g['kind'] == 'review'
                      and rva in g['functions'] and g['task_id'] == rv['review_task_id']]
        fr.require(bool(candidates), f'{fid}: reviewed member lacks its sampling safeguard group')
        g = candidates[-1]
        review_file = review_path(root, g)
        fr.require(review_file.is_file() and hashlib.sha256(review_file.read_bytes()).hexdigest() == rv['review_sha256'],
                   f'{fid}: saved sample review hash differs from its approval')
        status, blocks = read_review(root, g, data['functions'])
        fr.require(status == 'ok' and blocks[rva].get('verdict') == 'approve'
                   and blocks[rva].get('source_digest') == rec['source']['digest'],
                   f'{fid}: saved approving sample review missing or stale')
        ok, why = sampling_gate(root, fdir, g, data)
        fr.require(ok, f'{fid}: sampling safeguard: {why}')


def plan_family(root, spec_file, fdir=None, supersede=None):
    family = fr.read(root, spec_file)
    data, target = af.load(root)
    by_id = {fn['id']: fn for fn in data['functions']}
    first = family['first_members']
    fr.require(isinstance(first, list) and len(set(first)) == 20, 'provide the ordered first 20 member ids')
    if supersede:
        family['supersedes'] = supersede
    family.update(family_schema=1, review=None, paused=False, pause_reason='')
    family['first_members'] = {}
    for fid in first:
        fn = by_id[fid]
        record = af.validate_match(fn, target, root)
        fr.check_member(family, fn, record)
        family['first_members'][fid] = fr.member_digest(fn, record)
    fr.validate_family(family, approved=False)
    if supersede:
        return supersede_family(root, fdir or flow_dir(root), supersede, family, first, data, target)
    if any(by_id[fid]['status'] != 'matched' for fid in first):
        states = function_states(root, fdir or flow_dir(root), online=False,
                                 review_rvas={hexrva(by_id[fid]['rva']) for fid in first})
        fr.require(all(states.get(hexrva(by_id[fid]['rva']), {}).get('state') == 'confirmed'
                       and not states[hexrva(by_id[fid]['rva'])].get('group') for fid in first),
                   'first 20 must be confirmed and ungrouped before planning a new family')
    path = f'reports/{target["build_id"]}/families/{fr.family_key(family)}.json'
    fr.require(not (root / path).exists(), 'family manifest already exists')
    fr.write(root, path, family)
    if any(by_id[fid]['status'] != 'matched' for fid in first):
        fdir = fdir or flow_dir(root)
        made = review_group(root, fdir, max_size=20, select=set(first))
        fr.require(len(made) == 1, 'first 20 must form one new review group; resolve existing groups first')
        g = load_group(fdir, made[0])
        g.update(family_review_path=path, task_id='review-family-' + fr.family_key(family)[:20],
                 member_brief=g['brief'])
        save_group(fdir, g)
        g['brief'] = family_brief(root, path, session_profile(fdir), fdir)[1]
        save_group(fdir, g)
    return path



def supersede_family(root, fdir, old_path, family, first, data, target):
    """Replace only an unapproved family, retaining its manifest and saved reviews."""
    root, fdir = Path(root), Path(fdir)
    old_path = fr.public_path(old_path, f'reports/{target["build_id"]}/families/')
    old = fr.read(root, old_path)
    fr.validate_family(old, approved=old['review'] is not None)
    fr.require(old['review'] is None and not old.get('superseded_by'),
               'only a never-approved family can be superseded')
    fr.supersession_binding(old, family)
    fr.require(set(old['first_members']) == set(first), 'replacement must preserve the first 20')
    by_id = {fn['id']: fn for fn in data['functions']}
    fr.require(all(by_id[fid]['status'] != 'matched' and record_state(root, by_id[fid]) == 'confirmed'
                   for fid in first), 'first 20 must be unaccepted and confirmed')
    fr.require(not any(b['family_path'] == old_path for b in family_batches(root).values()),
               'family with a batch cannot be superseded; use pause and revoke')
    path = f'reports/{target["build_id"]}/families/{fr.family_key(family)}.json'
    fr.require(path != old_path and not (root / path).exists(), 'replacement manifest already exists')
    all_groups = groups(fdir)
    primaries = [g for g in all_groups.values() if g.get('family_review_path') == old_path
                 and g['kind'] == 'review' and not g.get('superseded_by')]
    fr.require(len(primaries) == 1, 'expected one active first-20 family review group')
    primary = primaries[0]
    expected = {hexrva(by_id[fid]['rva']) for fid in first}
    fr.require(set(primary['functions']) == expected and not primary.get('integrated'),
               'family review group differs from first 20 or is integrated')
    release = [primary]
    if primary.get('pair'):
        pair = all_groups.get(primary['pair'])
        fr.require(pair and pair['kind'] == 'sampling' and pair.get('pair') == primary['name']
                   and not pair.get('integrated') and not pair.get('superseded_by'), 'invalid sampling group')
        release.append(pair)
    # No other live group may be displaced by this operation.
    released_names = {g['name'] for g in release}
    fr.require(not any(g['name'] not in released_names and not g.get('superseded_by')
                       and g['kind'] == 'review' and expected.intersection(g['functions'])
                       for g in all_groups.values()), 'first 20 also belong to another active review group')
    ids = {g['task_id'] for g in release}
    ids.add('review-family-' + fr.family_key(old)[:20])
    pattern = re.compile(r'^(?:' + '|'.join(re.escape(i) for i in ids) + r')(?:-r[0-9]+)?(?:\.family)?\.(?:md|json)$')
    reviews = root / REVIEWS
    files = [p for p in reviews.iterdir() if p.is_file() and not p.is_symlink() and pattern.fullmatch(p.name)] if reviews.is_dir() else []
    archive = reviews / 'superseded' / fr.family_key(old)
    fr.require(not any((archive / p.name).exists() for p in files), 'superseded review archive already contains a file')
    old_copy = dict(old)
    snapshots = {g['name']: dict(g) for g in release}
    existing_groups = set(all_groups)
    briefs = root / BRIEFS
    existing_briefs = set(briefs.iterdir()) if briefs.is_dir() else set()
    moved = []
    try:
        archive.mkdir(parents=True, exist_ok=True)
        for p in files:
            p.rename(archive / p.name)
            moved.append(p)
        for g in release:
            g['superseded_by'] = path
            save_group(fdir, g)
        old.update(paused=True, pause_reason='Superseded by a corrected unapproved family.', superseded_by=path)
        fr.write(root, old_path, old)
        fr.write(root, path, family)
        made = review_group(root, fdir, max_size=20, select=set(first))
        fr.require(len(made) == 1, 'first 20 must be confirmed, unheld and form one new review group')
        g = load_group(fdir, made[0])
        g.update(family_review_path=path, task_id='review-family-' + fr.family_key(family)[:20],
                 member_brief=g['brief'])
        save_group(fdir, g)
        g['brief'] = family_brief(root, path, session_profile(fdir), fdir)[1]
        save_group(fdir, g)
        log_event(fdir, 'family-superseded', family=old_path, replacement=path)
    except Exception:
        for name in set(groups(fdir)) - existing_groups:
            (fdir / 'groups' / (name + '.json')).unlink()
        for original in snapshots.values():
            save_group(fdir, original)
        fr.write(root, old_path, old_copy)
        (root / path).unlink(missing_ok=True)
        for p in moved:
            (archive / p.name).rename(p)
        if briefs.is_dir():
            for p in set(briefs.iterdir()) - existing_briefs:
                if p.is_file():
                    p.unlink()
        raise
    return path

def family_brief(root, path, profile=None, fdir=None, render_only=False, attached_group=None):
    family = fr.read(root, path)
    profile = profile or session_profile(flow_dir(root))
    task = 'review-family-' + fr.family_key(family)[:20]
    attached = [g for g in groups(fdir or flow_dir(root)).values()
                if g.get('family_review_path') == path and g['kind'] == 'review']
    if attached_group is not None:
        attached = [attached_group]
    if attached:
        task = attached[0]['task_id']
    brief = f'.local/briefs/{task}.md'
    members = (f"Also write `.local/reviews/{task}.md` with ordinary full-review blocks for all first 20, "
               f"in this same pass. Their group is {attached[0]['name']}; the standard checklist and member inputs "
               f"are in `{attached[0]['member_brief']}`. Use task id {task}, not the earlier task id in that brief."
               if attached else 'The first 20 already have individual approvals; assess them with the template.')
    text = f"""# Family review {task}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: fresh independent admitted Reviewer. Follow docs/reviewer-runbook.md, Family reviews.
Task: {task}; review scope is the family at `{path}` (spec digest `{fr.digest(fr.spec(family))}`).
Gates and exposure: docs/authorizations.md. Stop if the model lacks authorization to read an input.
Allowed inputs: pinned template and parameter source, the manifest and its first 20 members,
public match records and reconstructed units. FNV index: `{(root / ".local/analysis/fnv_index.jsonl").resolve()}`;
function packs: `{(root / ".local/packs").resolve()}`; source checkouts: `{(root / ".local/sources").resolve()}`.
Read no other review or handoff.
Review source plausibility, provenance, extraction, target bindings, labels and all first 20.
Output: `.local/reviews/{task}.family.json`, exactly the JSON schema in the family-review runbook.
{members}
Profile: {profile}. Do not edit anything else, push, post publicly,
mark matched, use verifier hosts or start agents. Limit: 40 minutes, one pass; escalate doubts.
"""
    if render_only:
        return text
    (root / brief).parent.mkdir(parents=True, exist_ok=True)
    (root / brief).write_text(text)
    return task, brief


def approve_family(root, fdir, path, review_file):
    family = fr.read(root, path)
    fr.validate_family(family, approved=False)
    fr.require(family['review'] is None and not family['paused'], 'family already reviewed or paused')
    file = Path(review_file).resolve()
    base = (root / REVIEWS).resolve()
    fr.require(file.is_relative_to(base) and file.is_file(), 'family review must be saved under .local/reviews')
    doc = fr.read(root, file)
    family['review'] = {k: doc[k] for k in ('review_task_id', 'reviewer_model', 'profile', 'spec_sha256')}
    family['review']['review_sha256'] = hashlib.sha256(file.read_bytes()).hexdigest()
    fr.validate_family(family)
    fr.private_approval(root, family, session_profile(fdir))
    for field in ('template_source', 'parameter_source'):
        src = family[field]
        fr.require(hashlib.sha256((root / src['path']).read_bytes()).hexdigest() == src['sha256'],
                   'template or extraction source changed')
    data, target = af.load(root)
    family_reviewed_gate(root, fdir, family['first_members'], data, target)
    for fn in data['functions']:
        if fn['id'] in family['first_members']:
            rec = af.validate_match(fn, target, root)
            fr.check_member(family, fn, rec)
            fr.require(fr.member_digest(fn, rec) == family['first_members'][fn['id']], 'first-20 member changed')
    fr.write(root, path, family)
    return path


def plan_family_batch(root, family_path, name, seed, population):
    fr.require(fr.ID.fullmatch(name) is not None, 'invalid batch name')
    family = fr.read(root, family_path)
    fr.validate_family(family)
    fr.require(not family['paused'], 'family is paused')
    data, target = af.load(root)
    by_id = {fn['id']: fn for fn in data['functions']}
    fr.require(len(population) == len(set(population)) and bool(population), 'empty or duplicate batch population')
    members = {}
    for fid in population:
        fn = by_id[fid]
        fr.require(fn['status'] != 'matched', 'sample drawn after an acceptance in its population')
        record = af.validate_match(fn, target, root)
        fr.check_member(family, fn, record, ranges=False)
        members[fid] = fr.member_digest(fn, record)
    for old in family_batches(root).values():
        fr.require(old['family_path'] != family_path or not set(population) & set(old['population']),
                   'member already belongs to a recorded batch of this family')
    path = f'reports/{target["build_id"]}/family-batches/{name}.json'
    fr.require(not (root / path).exists(), 'batch already exists')
    batch = dict(batch_schema=1, family_path=family_path, family_sha256=fr.digest(fr.spec(family)),
                 seed=seed, population=sorted(population), members=members, commitment=None, sample=None)
    fr.require(isinstance(seed, str) and bool(seed), 'missing draw seed')
    fr.write(root, path, batch)
    return path


def draw_family_batch(root, path):
    batch = fr.read(root, path)
    fr.require(batch['sample'] is None and batch['commitment'] is None, 'batch already drawn; never redraw')
    fr.committed(root, path, batch)
    head = fr.git(root, 'rev-parse', 'HEAD')
    fr.no_prior_acceptance(root, batch['population'], head, batch['members'])
    data = inventory(root)
    fr.require(not any(fn['id'] in batch['population'] and fn['status'] == 'matched' for fn in data['functions']),
               'sample drawn after an acceptance in its population')
    family = fr.read(root, batch['family_path'])
    fr.validate_family(family)
    fr.require(not family['paused'], 'family is paused')
    batch.update(commitment=head, sample=fr.draw(batch['seed'], batch['population']))
    fr.validate_batch(batch, family)
    fr.write(root, path, batch)
    return batch


def pause_family(root, path, reason):
    from check import naming_finding_problem
    fr.require(naming_finding_problem(reason) is None, 'pause reason must be short public prose')
    family = fr.read(root, path)
    fr.validate_family(family, approved=family['review'] is not None)
    family.update(paused=True, pause_reason=reason)
    fr.write(root, path, family)


def family_sample_problem(root, fdir, batch, data):
    expected = {hexrva(fn['rva']): fr.read(root, fn['report'])['source']['digest']
                for fn in data['functions'] if fn['id'] in (batch['sample'] or [])}
    for g in groups(fdir).values():
        if g['kind'] != 'review' or g.get('superseded_by') or not set(g['functions']) & set(expected):
            continue
        status, blocks = read_review(root, g, data['functions'])
        if status != 'ok':
            continue
        current = [b for r, b in blocks.items() if r in expected and b.get('source_digest') == expected[r]]
        if not current:
            continue
        if any(b.get('verdict') != 'approve' for b in current):
            return 'sample rejection or escalation'
        ok, why = sampling_gate(root, fdir, g, data)
        if not ok and why.startswith('DISAGREE'):
            return 'sampling disagreement'
    return None


def family_group_hold(root, fdir, ids, *, data=None):
    """A sample rejection or disagreement freezes every member of that family."""
    data = inventory(root) if data is None else data
    by_id = {fn['id']: fn for fn in data['functions']}
    for path, family in family_manifests(root).items():
        if family.get('superseded_by'):
            fr.check_superseded(root, path, family)
            continue
        relevant = any(by_id[fid].get('report')
                       and fr.read(root, by_id[fid]['report']).get('origin') == family['origin']
                       and fr.binding(by_id[fid], fr.read(root, by_id[fid]['report'])) == family['binding']
                       for fid in ids)
        if not relevant:
            continue
        fr.require(not family['paused'], 'family is paused: ' + path)
        for g in groups(fdir).values():
            if g.get('family_review_path') == path:
                review_file = root / REVIEWS / (g['task_id'] + '.family.json')
                if review_file.is_file():
                    fr.require(fr.read(root, review_file).get('verdict') == 'approve',
                               'family Reviewer did not approve; pause family ' + path)
    for path, batch in family_batches(root).items():
        if not any(fid in batch['population'] and by_id[fid].get('report')
                   and fr.member_digest(by_id[fid], fr.read(root, by_id[fid]['report'])) == batch['members'][fid]
                   for fid in ids):
            continue
        family = fr.read(root, batch['family_path'])
        fr.require(not family['paused'], 'family is paused: ' + batch['family_path'])
        if batch['sample'] is None:
            raise ValueError('Family review: draw and commit sample before reviewing a family batch')
        fr.ordering(root, path, batch)
        problem = family_sample_problem(root, fdir, batch, data)
        fr.require(problem is None, f'{problem}; pause family ' + batch['family_path'])


def _legacy_integrate_family(root, fdir, path, branch='main', push=True):
    root = Path(root)
    batch = fr.read(root, path)
    family = fr.read(root, batch['family_path'])
    fr.validate_family(family)
    fr.validate_batch(batch, family)
    fr.require(not family['paused'], 'family is paused')
    fr.private_approval(root, family, session_profile(fdir))
    fr.ordering(root, path, batch)
    data, target = af.load(root)
    required = set(batch['sample'])
    for fn in data['functions']:
        if fn['id'] in batch['population']:
            rec = af.validate_match(fn, target, root)
            fr.check_member(family, fn, rec, ranges=False)
            fr.require(fr.member_digest(fn, rec) == batch['members'][fn['id']], 'member differs from committed population')
            if fn['status'] == 'matched' or not fr.in_ranges(rec.get('family_parameters'), family['parameter_ranges']):
                required.add(fn['id'])
    family_reviewed_gate(root, fdir, required, data, target)
    name = 'family-' + Path(path).stem
    existing = groups(fdir).get(name)
    if not existing:
        functions = [hexrva(fn['rva']) for fn in data['functions']
                     if fn['id'] in batch['population'] and fn['id'] not in required]
        fr.require(bool(functions), 'batch has no members needing family acceptance')
        save_group(fdir, dict(name=name, kind='family', task_id=family['review']['review_task_id'],
                             build_id=family['binding']['build_id'], functions=functions, batch_path=path,
                             reviewer_model=family['review']['reviewer_model'], profile=session_profile(fdir),
                             integrated=None, sampled=[]))
    return _legacy_integrate(root, fdir, name, branch, push)


def family_deferred(root, fn):
    for path, family in family_manifests(root).items():
        if family.get('superseded_by'):
            fr.check_superseded(root, path, family)
            continue
        if (family['paused'] or (family['review'] is None and fn['id'] not in family['first_members'])) and fn.get('report'):
            rec = fr.read(root, fn['report'])
            if rec.get('origin') == family['origin'] and fr.binding(fn, rec) == family['binding']:
                return True
    for batch in family_batches(root).values():
        if fn['id'] not in batch['population']:
            continue
        family = fr.read(root, batch['family_path'])
        if family['paused'] or batch['sample'] is None:
            return True
        fr.validate_batch(batch, family)
        rec = fr.read(root, fn['report'])
        return fn['id'] not in batch['sample'] and fr.in_ranges(rec.get('family_parameters'), family['parameter_ranges'])
    return False


def family_actions(root, fdir):
    acts = []
    for path, family in family_manifests(root).items():
        fr.validate_family(family, approved=family['review'] is not None)
        if family.get('superseded_by'):
            fr.check_superseded(root, path, family)
            continue
        if family['paused']:
            acts.append(('stop', f'family paused: {path}: {family["pause_reason"]}; assess accepted population before resuming'))
        elif family['review'] is None:
            task, brief = family_brief(root, path, session_profile(fdir), fdir)
            review = f'{REVIEWS}/{task}.family.json'
            if (root / review).is_file():
                doc = fr.read(root, review)
                if doc.get('verdict') != 'approve':
                    acts.append(('stop', f'family review {task} did not approve; pause {path} and escalate per the rule'))
                elif all(fn['status'] == 'matched' for fn in inventory(root)['functions']
                         if fn['id'] in family['first_members']):
                    acts.append(('run', f'python3 tools/flow.py family-approve {path} --review {review}'))
                else:
                    acts.append(('wait', f'family approval {task} waits for first-20 individual integration and safeguards'))
            elif any(e.get('event') == 'family-dispatched' and e.get('task') == task for e in events(fdir)):
                acts.append(('wait', f'family Reviewer {task} is running; saved review: {review}'))
            else:
                profile = session_profile(fdir)
                entry = dict(profiles.role(profile, 'reviewer'))
                if not af.reviewer_admitted(root, entry['model'], profile):
                    entry = {'model': 'opus', 'harness': 'claude-code'}
                prompt = f'Read docs/reviewer-runbook.md and follow it. Your brief is {brief}.'
                acts.append(('dispatch', f'family review needed: {start_worker(entry, prompt, "reviewer")}. '
                             f'Then: python3 tools/flow.py family-dispatched {path}'))
    by_id = {fn['id']: fn for fn in inventory(root)['functions']}
    for path, batch in family_batches(root).items():
        family = fr.read(root, batch['family_path'])
        if family['paused']:
            continue
        missing = [fid for fid in batch['population'] if not by_id[fid].get('report')
                   or not (root / by_id[fid]['report']).is_file()]
        if missing:
            acts.append(('wait', f'family batch {path} needs local match records for {len(missing)} member(s) '
                         'in its source checkout'))
            continue
        if batch['sample'] is None:
            acts.append(('run', f'python3 tools/flow.py family-draw {path}    # draw sample; seed and population must be committed first'))
            continue
        fr.validate_batch(batch, family)
        problem = family_sample_problem(root, fdir, batch, inventory(root))
        if problem:
            acts.append(('stop', f'{problem}: pause family with python3 tools/flow.py family-pause '
                         f"{batch['family_path']} --reason 'Sample review or reproduction defect.'"))
            continue
        required = [fid for fid in batch['population'] if fid in batch['sample'] or not fr.in_ranges(
                    fr.read(root, by_id[fid]['report']).get('family_parameters'), family['parameter_ranges'])]
        if any(by_id[fid]['status'] != 'matched' for fid in required):
            acts.append(('run', 'python3 tools/flow.py review-group    # review sample and out-of-range members; keep second-pass safeguard'))
        elif any(by_id[fid]['status'] != 'matched' for fid in batch['population']):
            acts.append(('run', f'python3 tools/flow.py integrate-family {path}    # accept batch after sample reviews'))
    return acts


# ------------------------------------------------------------------ reviewer model

def reviewer_class(model):
    if model in af.OPUS_MODELS:
        return 'opus'
    return {'gpt-6.1-terra': 'terra', af.SOL_MODEL: 'sol'}.get(model, model)


def strong_reviewer_entry(root, profile, first_model):
    """Choose an admitted strong Reviewer, independent of the first model under claude-low."""
    entry = dict(profiles.role(profile, 'strong'))
    if (not af.strong_reviewer_admitted(root, entry['model'], profile)
            or (profile == 'claude-low' and af.reviewer_matches(entry['model'], first_model))):
        entry = {'model': 'opus', 'harness': 'claude-code'}
    refuse(profile != 'claude-low' or not af.reviewer_matches(entry['model'], first_model),
           'no admitted strong Reviewer with a different model from the first review')
    return entry


def session_profile(fdir):
    ev = [e for e in events(fdir) if e['event'] == 'session-start']
    return (ev[-1].get('profile') if ev else None) or profiles.DEFAULT


def start_worker(entry, prompt, agent_type=None):
    """How to start a worker for a role entry, in the form its harness takes."""
    if entry.get('harness') == 'codex':
        return (f'start a Codex session (model {entry["model"]}, effort {entry.get("effort") or "default"}) in this '
                f'repository with the one line: "{prompt}"')
    kind = f'subagent_type {agent_type}, ' if agent_type else ''
    return f'Agent tool: {kind}model {entry["model"]}, fresh context, prompt "{prompt}"'


# ------------------------------------------------------------------ review groups and briefs

def unit_of(root, fn):
    rec = json.loads((Path(root) / fn['report']).read_text())
    return rec['source']['compiled'], rec['source']['translation_unit']


def next_group_name(fdir):
    n = 1 + max([int(m.group(1)) for k in groups(fdir) if (m := re.fullmatch(r'g(\d+)', k))] or [0])
    return f'g{n:03d}'


def review_group(root, fdir, max_size=DEFAULT_GROUP_MAX, reviewer_model=None, seed='flow', select=None):
    """Group every confirmed function not yet in a review group, unit by unit; returns new group names."""
    root = Path(root)
    profile = session_profile(fdir)
    if reviewer_model:
        refuse(af.reviewer_admitted(root, reviewer_model, profile),
               f'reviewer model {reviewer_model} is not admitted for profile {profile}')
        entry = {'model': reviewer_model, 'harness': 'codex' if reviewer_class(reviewer_model) in ('terra', 'sol') else 'claude-code'}
    else:
        entry = dict(profiles.role(profile, 'reviewer'))
        if not af.reviewer_admitted(root, entry['model'], profile):
            # The stricter Reviewer stands in until the rule admits the profile's one.
            print(f'note: the rule does not admit a {entry["model"]} Reviewer yet; using opus', file=sys.stderr)
            entry = {'model': 'opus', 'harness': 'claude-code'}
    model = entry['model']
    data = inventory(root)
    by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == data['target_build_id']}
    # Keep whole-inventory acceptance/version counts, but read private review files only
    # for the selected population. Unrelated shared groups may belong to another input root.
    scope = {r for r, fn in by_rva.items() if fn['id'] in select} if select is not None else None
    states = function_states(root, fdir, online=False, review_rvas=scope)
    todo = [r for r, s in states.items() if s['state'] == 'confirmed' and not s.get('group')
            and not family_deferred(root, by_rva[r]) and (select is None or by_rva[r]['id'] in select)]
    units = {}
    for rva in sorted(todo, key=lambda r: int(r, 16)):
        units.setdefault(unit_of(root, by_rva[rva])[0], []).append(rva)
    batches, cur = [], []
    for unit in sorted(units):
        if cur and len(cur) + len(units[unit]) > max_size:
            batches.append(cur)
            cur = []
        cur += units[unit]
    if cur:
        batches.append(cur)
    counts = accepted_counts(root, fdir, states)
    for g in groups(fdir).values():  # pending groups count too, so a version is not sampled twice over
        if g['kind'] == 'review' and not g.get('superseded_by'):
            for rva, comps in (g.get('components') or {}).items():
                if states.get(rva, {}).get('state') not in ('accepted', 'pushed'):
                    for c, v in comps.items():
                        counts.setdefault(c, {})[v] = counts.get(c, {}).get(v, 0) + 1
    made = []
    head = git(root, 'rev-parse', 'HEAD')
    for batch in batches:
        name = next_group_name(fdir)
        comps = {r: component_values(root, r, states[r], data, model) for r in batch}
        sample = choose_sample(name, batch, comps, counts, seed)
        for r in batch:
            for c, v in comps[r].items():
                counts.setdefault(c, {})[v] = counts.get(c, {}).get(v, 0) + 1
        second = strong_reviewer_entry(root, profile, model) if sample else None
        g = {'name': name, 'kind': 'review', 'task_id': f'review-flow-{name}', 'build_id': data['target_build_id'],
             'functions': batch, 'created': utc(), 'source_revision': head, 'reviewer_model': model, 'profile': profile,
             'reviewer_harness': entry.get('harness', 'claude-code'),
             'components': comps, 'sampled': sample, 'pair': f'{name}-s' if sample else None,
             'dispatched': None, 'rerun': None, 'integrated': None}
        snapshots = {unit_of(root, by_rva[r])[0]: h for r in batch
                     if (h := drafts.source_for(root, unit_of(root, by_rva[r])[0], by_rva[r]['rva']))
                     and not h.get('integrated')}
        if snapshots:
            g['harvests'] = snapshots
            tree = root / '.local/worktrees/review' / name
            git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), 'origin/main')
            drafts.link_private(root, tree)
            drafts.label(tree, g['task_id'], name, 'review')
            carry_into_tree(root, tree, batch, by_rva, snapshots)
            g['review_root'] = str(tree.resolve())
            g['source_revision'] = git(tree, 'rev-parse', 'HEAD')
        g['brief'] = write_review_brief(root, g, by_rva)
        save_group(fdir, g)
        if sample:
            s = dict(g, name=f'{name}-s', kind='sampling', task_id=f'review-flow-{name}-s', functions=sample,
                     reviewer_model=second['model'], reviewer_harness=second['harness'],
                     pair=name, sampled=sample, components={})
            s['brief'] = write_review_brief(root, s, by_rva)
            save_group(fdir, s)
            write_rerun_brief(root, g, by_rva)
        log_event(fdir, 'review-group', group=name, functions=batch, sampled=sample, reviewer_model=model)
        made.append(name)
    return made


def write_review_brief(root, g, by_rva, render_only=False):
    root = Path(root)
    rows, units, packs = [], {}, []
    for rva in g['functions']:
        fn = by_rva[rva]
        compiled, tu = unit_of(root, fn)
        units[compiled] = tu
        rows.append(f'| {fn["build_id"]} | {rva} | {fn["size"]} | {fn.get("name") or "?"} | {fn["report"]} |')
        if (root / '.local/packs' / fn['build_id'] / rva).is_dir():
            packs.append(f'.local/packs/{fn["build_id"]}/{rva}/')
    sampling = g['kind'] == 'sampling'
    text = f"""# Brief {g['task_id']}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: Reviewer (`docs/reviewer-runbook.md`; in Claude Code `.claude/agents/reviewer.md`), fresh
context, model {g['reviewer_model']}. Task id:
`{g['task_id']}`. Plan step 5 / fan-out review (AGENTS.md "Fan-out design", "Review").
{'This is the sampling safeguard second pass: an independent review of functions another Reviewer is reviewing in group ' + g['pair'] + '. Write `sampling_second_pass: yes`.' if sampling else 'Write `sampling_second_pass: no`.'}

Gates in force: G2 (you may read reconstructed source and, where listed, the private packs under
`.local/packs/`; never quote them). G3/G4/G5 are not needed: run no verifier, no Boat, no network.

Review working directory: `{g.get('review_root', root)}`. Run every review command from this checkout.
{('Exposure authorization: `docs/authorizations.md:33`, Notes, profile `claude-low`, explicitly permits Terra and Sol to read reconstructed source, sanitized reports and function packs through the maintainer own Codex subscription. The owner has knowingly repeated that authorization. A missing written provider-terms assessment is not a stop condition; do not invent or record an assessment. Continue the full review under that authorization. If you decline pack access, complete a source-only review, write `decompiler_output_read: no` and state in the review reasons that packs were not read; this is not a setup failure.') if g.get('profile') == 'claude-low' else ''}

## Functions ({len(g['functions'])})

| build id | RVA | size | name | match record |
|---|---|---|---|---|
""" + '\n'.join(rows) + f"""

Source revision: `{g['source_revision']}` (HEAD when this group was made). A unit may be
uncommitted; the match records bind the working-tree digest, which you compute yourself
(`python3 tools/source_digest.py <files>`).

Translation units:
""" + '\n'.join(f'- `{c}`: {", ".join(f"`{p}`" for p in tu)}' for c, tu in sorted(units.items())) + f"""

Private packs (G2): {', '.join(f'`{p}`' for p in packs) or 'none found'}.
For the provenance comparison you may read `.local/analysis/fnv_index.jsonl` and the pinned FNV
source files it identifies, under the maintainer's recorded FNV reuse and model-exposure permissions.

## Steps

1. Run `python3 tools/lint_review_readiness.py --functions {' '.join(g['functions'])}` before reviewing.
   Validate individual bindings as the runbook requires; explicitly listed pending review-behind
   entries are expected during review. The full `python3 tools/check.py` must pass at integration.
   Unexpected failures outside the group's units, except explicitly listed pending entries,
   are a `setup failure`: report them instead of writing verdicts.
2. Run `python3 tools/review_packet.py --template {' '.join(g['functions'])}` and review every
   function with the checklist in `docs/reviewer-runbook.md`.
3. Do not open any other file under `.local/reviews/` or `.local/handoffs/`: this review must be
   independent.
4. Write your review document, exactly in the runbook's output format, with the title
   `# Review {g['task_id']}`, to `.local/reviews/{g['task_id']}.md`. Create it once; never edit or
   overwrite it afterwards. If that file already exists, stop and return `exists` in the table.
5. Return only the short table from the runbook ("Return message"), nothing else.

Do not push, post publicly, mark `matched`, edit any other file, or start further agents.
"""
    if render_only:
        return text
    path = root / BRIEFS / f'{g["task_id"]}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.relative_to(root).as_posix()


def write_rerun_brief(root, g, by_rva, render_only=False):
    root = Path(root)
    units = sorted({unit_of(root, by_rva[r])[0] for r in g['sampled']})
    sample = {'seed': f'flow:{g["name"]}', 'reviewed': {u: [r for r in g['sampled'] if unit_of(root, by_rva[r])[0] == u]
                                                        for u in units}, 'label_only': {}}
    sdir = root / '.local/flow/rerun' / g['name']
    if not render_only:
        sdir.mkdir(parents=True, exist_ok=True)
        (sdir / 'sample.json').write_text(json.dumps(sample, indent=2) + '\n')
    text = f"""# Brief rerun-{g['name']}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: Engineer (or the routine orchestrator with a shell). Task: the sampling safeguard's
from-scratch comparator re-run for group {g['name']} ({len(g['sampled'])} functions), on a clean
checkout (docs/verification.md, Sampling safeguard). Gates: as recorded for confirm runs.

1. `git worktree add --detach .local/flow/rerun/{g['name']}/tree {g['source_revision']}`, then copy
   the unit files of these units from `{g.get('review_root', root)}`:
   {', '.join(f'`{u}`' for u in units)}. Copy their entire include closures, match records and pinned
   maps with histories from that same frozen checkout. Link `.local` into it as earlier re-runs did.
   Label it with `python3 -c "import sys; sys.path.insert(0, 'tools'); import draft_worktrees as d; d.label('.local/flow/rerun/{g['name']}/tree', 'rerun', '{g['name']}', 'rerun')"`.
2. In that tree: `tools/verifier/confirm --list <file with the units' task dirs> --out .local/flow/rerun/{g['name']}/out`.
   For harvested units use the frozen task paths below, which keep the group's original harvest
   instead of following a newer tier's harvest:
   {', '.join(f"`{u}`: `{h['task']}`" for u, h in g.get('harvests', {}).items()) or 'none (legacy units)'}.
3. `python3 tools/sampling_packet.py --sample .local/flow/rerun/{g['name']}/sample.json --rerun .local/flow/rerun/{g['name']}/out/<build id> --compare-out .local/flow/rerun/{g['name']}/compare.txt`
4. `python3 tools/flow.py record-rerun {g['name']} --compare .local/flow/rerun/{g['name']}/compare.txt`
5. Remove the worktree. Return a table: function, AGREE/DISAGREE; and the compare file path.

Never edit the comparator, the records or the compare file to get AGREE; a DISAGREE is escalated.
Do not push, post publicly, mark `matched`, or start further agents.
"""
    if render_only:
        return text, (json.dumps(sample, indent=2) + '\n').encode()
    path = root / BRIEFS / f'rerun-{g["name"]}.md'
    path.write_text(text)
    return path.relative_to(root).as_posix()


def record_rerun(root, fdir, name, compare_file):
    g = load_group(fdir, name)
    refuse(g['kind'] == 'review' and g.get('sampled'), f'group {name} has no sampled functions')
    rows = {}
    for line in Path(compare_file).read_text().splitlines():
        m = re.search(r'\b(0x[0-9a-f]+)\b', line)
        v = re.search(r'\b(AGREE|DISAGREE)\s*$', line)
        if m and v:
            rows.setdefault(m.group(1), set()).add(v.group(1))
    agree = [r for r in g['sampled'] if rows.get(r) == {'AGREE'}]
    other = [r for r in g['sampled'] if r not in agree]
    g['rerun'] = {'file': str(compare_file), 'agree': agree, 'not_agree': other, 'recorded': utc()}
    save_group(fdir, g)
    log_event(fdir, 'rerun', group=name, agree=len(agree), not_agree=other)
    return agree, other


def void_review(root, fdir, name, reason, setup_failure, selected=None):
    """Archive setup-failure verdicts and dissolve their groups without losing other findings."""
    from check import naming_finding_problem
    refuse(setup_failure, 'explicit --setup-failure is required')
    refuse(bool(reason.strip()) and naming_finding_problem(reason) is None, 'reason must be short public prose')
    root = Path(root)
    g = load_group(fdir, name)
    refuse(g['kind'] in ('review', 'sampling'), 'only individual review groups may be voided')
    data = inventory(root)
    status, blocks = read_review(root, g, data['functions'])
    if status == 'missing':
        refuse(not g.get('superseded_by') and not g.get('integrated'), 'group is superseded or integrated')
        refuse(selected is None and bool(g.get('dispatched')), 'only an unfulfilled dispatch may be reset')
        refuse(not review_path(root, g['task_id']).exists() and not review_path(root, g['task_id']).is_symlink(),
               'a review path already exists')
        g['dispatched'] = None
        save_group(fdir, g)
        log_event(fdir, 'dispatch-reset', group=name, task_id=g['task_id'], reason=reason)
        return []
    refuse(status == 'ok', 'a complete saved review is required')
    chosen = set(selected if selected is not None else blocks)
    refuse(bool(chosen) and chosen <= blocks.keys(), 'select verdicts present in the saved review')
    refuse(all(blocks[r].get('verdict') in ('reject', 'escalate') for r in chosen),
           'cannot void an approval or unknown verdict')
    affected = [g]
    if g.get('pair'):
        affected.append(load_group(fdir, g['pair']))
    plans = []
    for group in affected:
        refuse(not group.get('superseded_by') and not group.get('integrated'),
               'group is superseded or integrated')
        refuse(not (group.get('rerun') or {}).get('not_agree'),
               'comparator non-reproduction must be resolved independently')
        path = review_path(root, group)
        if not path.exists():
            continue
        status, _ = read_review(root, group, data['functions'])
        refuse(status == 'ok', 'a paired saved review must also be complete')
        content = path.read_text(encoding='utf-8')
        pieces = re.split(r'(?=^## )', content, flags=re.M)
        keep = [pieces[0]]
        for piece in pieces[1:]:
            match = re.match(r'## \S+ (0x[0-9a-f]+)\b', piece)
            if group['name'] != name or not match or match.group(1) not in chosen:
                keep.append(piece)
        archive = path.parent / 'superseded' / path.name
        residual = path.parent / (group['task_id'] + '-retained.md')
        refuse(not archive.exists() and not residual.exists(), 'archive or retained review already exists')
        plans.append((path, archive, residual, ''.join(keep) if len(keep) > 1 else None))
    # The original reviews stay byte-identical in the archive. Retained subsets are only an
    # index of their other verdicts for prior_holds, never a new approval or a changed review.
    for path, archive, residual, retained in plans:
        archive.parent.mkdir(parents=True, exist_ok=True)
        path.rename(archive)
        if retained:
            residual.write_text(retained, encoding='utf-8')
    for group in affected:
        group['superseded_by'] = 'void-review:' + g['task_id']
        save_group(fdir, group)
    log_event(fdir, 'void-review', group=name, task_id=g['task_id'], functions=sorted(chosen),
              dissolved_groups=[group['name'] for group in affected], reason=reason)
    return sorted(chosen)


def redo_review(root, fdir, name):
    """A fresh Reviewer under a new task id after a review the parser refused (never edit the file)."""
    g = load_group(fdir, name)
    if g['kind'] == 'sampling':
        primary = load_group(fdir, g['pair'])
        entry = strong_reviewer_entry(root, g.get('profile', profiles.DEFAULT), primary['reviewer_model'])
        g['reviewer_model'], g['reviewer_harness'] = entry['model'], entry['harness']
    m = re.fullmatch(r'(.*?)(?:-r(\d+))?', g['task_id'])
    g['task_id'] = f'{m.group(1)}-r{int(m.group(2) or 1) + 1}'
    g['dispatched'] = None
    g.pop('saved_review', None)
    data = inventory(root)
    by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == data['target_build_id']}
    g['brief'] = write_review_brief(root, g, by_rva)
    if g.get('family_review_path'):
        g['member_brief'] = g['brief']
        save_group(fdir, g)
        g['brief'] = family_brief(root, g['family_review_path'], g.get('profile'), fdir)[1]
    save_group(fdir, g)
    log_event(fdir, 'redo-review', group=name, task_id=g['task_id'])
    return g


# ------------------------------------------------------------------ sampling gate

def sampling_gate(root, fdir, g, data):
    """(ok, problem) for a review group's sampled functions: second review saved and in agreement,
    and the from-scratch re-run recorded with AGREE for each."""
    if not g.get('sampled'):
        return True, None
    s = load_group(fdir, g['pair'])
    if s.get('profile', profiles.DEFAULT) != g.get('profile', profiles.DEFAULT):
        return False, 'DISAGREE: sampling profile does not match primary group profile'
    if (g.get('profile', profiles.DEFAULT) == 'claude-low'
            and af.reviewer_matches(g['reviewer_model'], s['reviewer_model'])):
        return False, 'DISAGREE: sampling reviewer_model must differ from first reviewer_model'
    status, second = read_review(root, s, data['functions'])
    if status == 'missing':
        return False, f'waiting: sampling review {s["task_id"]} not saved'
    if status != 'ok':
        return False, f'redo: sampling review {s["task_id"]} {status}'
    _, first = read_review(root, g, data['functions'])
    for rva in g['sampled']:
        a, b = first.get(rva), second.get(rva)
        if a is None or b is None:
            return False, f'DISAGREE: {rva} lacks a block in one of the two reviews'
        if (a.get('verdict'), a.get('source_digest')) != (b.get('verdict'), b.get('source_digest')):
            return False, (f'DISAGREE: {rva} first review {a.get("verdict")}, second {b.get("verdict")}'
                           + ('' if a.get('source_digest') == b.get('source_digest') else ', different digests'))
    if not g.get('rerun'):
        return False, f'waiting: from-scratch re-run not recorded (brief .local/briefs/rerun-{g["name"]}.md)'
    failed = set(g['sampled']) & set(g['rerun']['not_agree'])
    missing = set(g['sampled']) - set(g['rerun'].get('agree', []))
    if failed or missing:
        return False, f'DISAGREE: re-run did not agree for {", ".join(sorted(failed | missing))}'
    return True, None


def split_group(root, fdir, name, selected):
    """Freeze an explicit approved subset without changing any saved verdict or sample draw.

    Rejected or disputed members remain in the parent. Shared unit changes still need the
    normal re-confirmation, re-review and staged gate; this command edits only flow metadata.
    """
    root = Path(root)
    parent = load_group(fdir, name)
    refuse(parent['kind'] == 'review' and not parent.get('subset_of'), 'split a primary individual review group')
    data = inventory(root)
    by_id = {fn['id']: hexrva(fn['rva']) for fn in data['functions']}
    chosen = sorted({by_id.get(r, r) for r in selected}, key=lambda r: int(r, 16) if r.startswith('0x') else -1)
    refuse(chosen and set(chosen) <= set(parent['functions']), 'selection must name functions of the parent group')
    status, first = read_review(root, parent, data['functions'])
    refuse(status == 'ok', f'parent review {status}')
    review = parent
    for rva in chosen:
        refuse(first.get(rva, {}).get('verdict') == 'approve', f'{rva}: selected function lacks approval')
    key = hashlib.sha256(json.dumps([chosen, review['task_id']], sort_keys=True).encode()).hexdigest()[:12]
    child_name = f'{name}-part-{key}'
    child = dict(review, name=child_name, functions=chosen, subset_of=name, integrated=None,
                 sampled=[r for r in parent.get('sampled', []) if r in chosen],
                 components={r: parent.get('components', {}).get(r, {}) for r in chosen})
    # Keep the original sample pair and re-run receipt, including held members, for audit.
    ok, problem = sampling_gate(root, fdir, child, data)
    refuse(ok, f'selected sampling gate: {problem}')
    if (Path(fdir) / 'groups' / f'{child_name}.json').exists():
        existing = load_group(fdir, child_name)
        refuse(all(existing.get(k) == child.get(k) for k in ('functions', 'task_id', 'subset_of')),
               'existing subset differs')
        return existing
    # A split cannot evade the random safeguard by excluding the original sample.
    count = math.ceil(len(chosen) * SAMPLE_RATE)
    extra = max(0, count - len(child['sampled']))
    if extra:
        candidates = [r for r in chosen if r not in child['sampled']]
        random.Random(child_name).shuffle(candidates)
        child['sampled'] += candidates[:extra]
        entry = strong_reviewer_entry(root, parent.get('profile', profiles.DEFAULT), parent['reviewer_model'])
        pair = dict(child, name=child_name + '-s', kind='sampling', pair=child_name,
                    functions=child['sampled'], reviewer_model=entry['model'],
                    reviewer_harness=entry['harness'], task_id='review-flow-' + child_name + '-s',
                    saved_review=None, dispatched=None)
        by_rva = {hexrva(fn['rva']): fn for fn in data['functions']}
        pair['brief'] = write_review_brief(root, pair, by_rva)
        save_group(fdir, pair)
        child['pair'], child['rerun'], child['rerun_dispatched'] = pair['name'], None, None
        write_rerun_brief(root, child, by_rva)
    save_group(fdir, child)
    log_event(fdir, 'split-group', group=child_name, parent=name, functions=chosen)
    return child


# ------------------------------------------------------------------ next actions

def next_actions(root, fdir, branch='main', now=None, online=True):
    """[(kind, text)] with kind 'stop', 'run', 'dispatch', 'wait' or 'done', in the order to do them."""
    lane_pending = any(json.loads(p.read_text()).get('state') in ('queued', 'running')
                       for name in ('queue', 'tooling-queue')
                       for p in (Path(fdir) / 'lane' / name).glob('*.json'))
    import time
    now = time.time() if now is None else now
    root = Path(root)
    data = inventory(root)
    states = function_states(root, fdir, branch, online)
    gs = groups(fdir)
    stops, acts, waits = [], [], []
    for kind, text in family_actions(root, fdir):
        (stops if kind == 'stop' else waits if kind == 'wait' else acts).append((kind, text))
    profile = session_profile(fdir)
    s_entry = profiles.role(profile, 'strong')
    strong = (f'the strong role ({profiles.model_label(s_entry)}'
              + ('; Agent tool subagent_type engineer)' if s_entry['harness'] == 'claude-code' else '; a Codex session)'))
    for name, g in gs.items():
        integrated = g.get('integrated') or {}
        fully_integrated = integrated.get('ci') == 'green' and integrated.get('accepted', 0) >= len(g['functions'])
        if g.get('superseded_by') or g['kind'] == 'family' or fully_integrated:
            continue
        if g['kind'] == 'sampling' and (gs.get(g.get('pair'), {}).get('integrated') or {}).get('ci') == 'green':
            continue
        status, blocks = read_review(root, g, data['functions'])
        if status.startswith('malformed'):
            acts.append(('run', f'python3 tools/flow.py redo-review {name}    # {g["task_id"]} {status}; never edit the saved review'))
            continue
        if g['kind'] == 'sampling':
            if status == 'missing' and not g.get('dispatched'):
                acts.append(dispatch_line(g, root))
            elif status == 'missing':
                waits.append(('wait', f'Reviewer for {name} ({g["task_id"]}) is running; its file appears at {REVIEWS}/{g["task_id"]}.md'))
            continue
        if g.get('sampled') and not g.get('rerun') and not g.get('rerun_dispatched'):
            acts.append(('dispatch', f'sampling re-run for {name}: {strong} with brief .local/briefs/rerun-{name}.md, '
                         f'or run its commands yourself. Then: python3 tools/flow.py dispatched {name} --rerun'))
        if status == 'missing':
            if g.get('family_review_path'):
                waits.append(('wait', f'first-20 review {g["task_id"]} is handled by its family brief'))
            elif not g.get('dispatched'):
                acts.append(dispatch_line(g, root))
            else:
                waits.append(('wait', f'Reviewer for {name} ({g["task_id"]}) is running; its file appears at {REVIEWS}/{g["task_id"]}.md'))
            continue
        esc = [(r, b.get('escalation_category')) for r, b in blocks.items() if b.get('verdict') == 'escalate']
        for cat in sorted({category for _, category in esc}):
            members = [r for r, category in esc if category == cat]
            rva = members[0] if len(members) == 1 else f'{len(members)} functions'
            if cat in BLOCKING_ESCALATIONS and reviewer_class(g['reviewer_model']) != 'opus':
                # The profile's independent strong Reviewer confirms before the maintainer sees it.
                confirmation = strong_reviewer_entry(root, g.get('profile', profiles.DEFAULT), g['reviewer_model'])
                confirmer = 'Opus' if confirmation['model'] in af.OPUS_MODELS else confirmation['model']
                stops.append(('stop', f'Reviewer ({g["reviewer_model"]}) escalated {rva} in {name} ({cat}): hold group {name} '
                              f'and hand it to the planning orchestrator for a {confirmer} confirmation review; the maintainer '
                              f'gets it only if {confirmer} also escalates'))
            elif cat in BLOCKING_ESCALATIONS:
                stops.append(('stop', f'ESCALATE to the maintainer: Reviewer escalated {rva} in {name} ({cat}); hold group {name}'))
        if any(c in BLOCKING_ESCALATIONS for _, c in esc):
            continue
        integ = g.get('integrated') or {}
        approved = [r for r, b in blocks.items() if b.get('verdict') == 'approve']
        if approved and integ.get('ci') != 'green':
            ok, problem = sampling_gate(root, fdir, g, data)
            if ok:
                if integ.get('batch'):
                    batch = integ['batch']
                    transaction = json.loads((Path(fdir) / 'combined' / f'{batch}.json').read_text())
                    command = 'python3 tools/flow.py integrate-groups ' + ' '.join(transaction['groups']) + f' --name {batch}'
                    if ('run', command) not in acts:
                        acts.append(('run', command))
                else:
                    mode = ' --with-metadata' if integ.get('with_metadata') else ''
                    acts.append(('run', f'python3 tools/flow.py integrate {name}{mode}'))
            elif problem.startswith('DISAGREE'):
                stops.append(('stop', f'ESCALATE to the maintainer (sampling disagreement, systemic): {name}: {problem}; '
                              f'pause group {name}'))
            elif problem.startswith('redo'):
                acts.append(('run', f'python3 tools/flow.py redo-review {g["pair"]}    # {problem}'))
            else:
                waits.append(('wait', f'{name} integrates after: {problem}'))
        back = [r for r, b in blocks.items() if b.get('verdict') == 'reject'
                or (b.get('verdict') == 'escalate' and b.get('escalation_category') not in BLOCKING_ESCALATIONS)]
        if back and not g.get('rejects_briefed'):
            acts.append(('run', f'python3 tools/flow.py brief triage --group {name}    # {len(back)} reject or escalate-other: '
                         f'then start {strong} with the brief it prints'))
    behind = subprocess.run(['git', 'rev-list', '--count', f'HEAD..origin/{branch}'], cwd=root, capture_output=True, text=True)
    if behind.returncode == 0 and behind.stdout.strip() not in ('', '0'):
        acts.insert(0, ('run', f'python3 tools/flow.py sync    # the checkout is {behind.stdout.strip()} commit(s) behind origin/{branch}'))
    # Confirmation and grouping.
    stale = sorted(r for r, s in states.items() if s['state'] == 'confirm-stale' and not s.get('group'))
    passed = sorted({s['unit'] for s in states.values() if s['state'] == 'drafted-pass' and s.get('unit')})
    if passed or stale:
        acts.append(('run', f'python3 tools/flow.py brief confirm    # {len(passed)} drafted unit(s), {len(stale)} stale record(s); '
                     f'then run its commands, or start {strong} with it'))
    if any(s['state'] == 'confirmed' and not s.get('group')
           and not family_deferred(root, next(fn for fn in data['functions'] if hexrva(fn['rva']) == r))
           for r, s in states.items()):
        acts.append(('run', 'python3 tools/flow.py review-group'))
    held = [r for r, s in states.items() if s.get('held') and not s.get('group')]
    if held and not any(e.get('event') == 'triage-brief' and e.get('held') for e in events(fdir)):
        acts.append(('run', f'python3 tools/flow.py brief triage --held    # {len(held)} function(s) held by an earlier '
                     f'reject; then start {strong} with the brief'))
    # Drafting.
    active_profile = profile
    units = queue_units(root)
    for qdir, profile, u, state, who, claim in units:
        age = now - float((claim or {}).get('time', now))
        if state in ('claimed', 'stale') and age < CLAIM_LOOK_SECONDS:
            waits.append(('wait', f'{who} works {u["dir"]} (claimed {int(age // 60)} min ago)'))
        elif state in ('claimed', 'stale'):
            acts.append(('run', f'check whether {who} still works {u["dir"]} (claimed {int(age // 60)} min ago); if its '
                         f'session has ended: python3 tools/work_queue.py --queue-dir {qdir.relative_to(root) if qdir.is_relative_to(root) else qdir} release {u["dir"]}'))
    failed = {}
    for s in states.values():
        if s['state'] == 'draft-failed' and s.get('unit'):
            failed.setdefault(s['unit'], s)
    full_queued = {u['key'] for qdir, profile, u, *_ in units if profile == 'full'}
    triage_units = []
    for unit, s in sorted(failed.items()):
        tier_pending = any(
            u['dir'] == unit and any(wq.eligible(qdir, u, tier, profiles.drafter_tiers(active_profile))
                                     for tier in profiles.drafter_tiers(active_profile)[1:])
            for qdir, _, u, state, *_ in units)
        if tier_pending:
            continue
        if s.get('profile') == 'cheap' and Path(unit).name not in full_queued:
            acts.append(('run', f'python3 tools/work_queue.py --queue-dir {QUEUES}/full add {unit}    # failed under cheap; '
                         'one try under full (refused when the unit has no attempts left: then brief triage)'))
        elif not any(e.get('event') == 'triage-brief' and unit in e.get('units', []) for e in events(fdir)):
            triage_units.append(unit)
    if triage_units:
        acts.append(('run', 'python3 tools/flow.py brief triage --units ' + ' '.join(triage_units)
                     + f'    # {len(triage_units)} failed units; then start {strong} with the brief'))
    by_queue = {}
    for qdir, profile, u, state, *_ in units:
        c = by_queue.setdefault((qdir, profile), {'open': 0, 'live': 0})
        c['open'] += state == 'open'
        c['live'] += state == 'claimed'
    for (qdir, profile), c in sorted(by_queue.items()):
        if c['open'] and not c['live']:
            n = min(c['open'], 3)
            queue_arg = qdir.relative_to(root) if qdir.is_relative_to(root) else qdir
            acts.append(('run', f'python3 tools/flow.py brief drafter --profile {profile} '
                         f'--queue-dir {shlex.quote(str(queue_arg))} --count {n}    '
                         f'# {c["open"]} open unit(s); then dispatch one Drafter per brief it prints'))
    for tier in profiles.drafter_tiers(active_profile)[1:]:
        for qdir in sorted({item[0] for item in units}):
            eligible = [u for u in wq.read_queue(qdir)
                        if wq.eligible(qdir, u, tier, profiles.drafter_tiers(active_profile))
                        and (not (claim := wq.read_claim(wq.tier_dir(qdir, 'claims', tier) / f'{u["key"]}.lock'))
                             or now - float(claim.get('time', now)) >= wq.STALE_SECONDS)]
            if eligible:
                queue_arg = qdir.relative_to(root) if qdir.is_relative_to(root) else qdir
                acts.append(('run', f'python3 tools/flow.py brief drafter --profile {active_profile} --tier {tier} '
                             f'--queue-dir {shlex.quote(str(queue_arg))} --count {min(len(eligible), 3)} '
                             f'# {len(eligible)} {tier} unit(s); dispatch one Drafter per brief'))
    # Reports.
    ev = events(fdir)
    last_session = max([i for i, e in enumerate(ev) if e['event'] == 'session-start'], default=None)
    if last_session is None:
        stops.insert(0, ('run', 'python3 tools/flow.py session-start'))
    else:
        since = ev[last_session + 1:]
        if not any(e['event'] == 'friction' for e in since):
            acts.append(('run', 'python3 tools/friction.py --write    # friction report, once per session'))
        last_dir = max([i for i, e in enumerate(ev) if e['event'] == 'direction-check'], default=-1)
        accepted_since = sum(e.get('accepted', 0) for e in ev[last_dir + 1:] if e['event'] == 'integrated')
        if accepted_since >= DIRECTION_EVERY:
            acts.append(('run', f'python3 tools/flow.py brief direction    # {accepted_since} accepted since the last check; '
                         'then dispatch subagent_type direction-check with the brief'))
        elif not any(e['event'] == 'direction-check' for e in since):
            waits.append(('end', 'before ending the session: python3 tools/flow.py brief direction, then dispatch '
                          'subagent_type direction-check with the brief'))
    out = stops + acts + waits
    import flow_lane
    stale_runs = [flow_lane.run_status(root, fdir, json.loads(p.read_text()))
                  for directory in ('lane/runs', 'lane/tooling')
                  for p in (Path(fdir) / directory).glob('*.json')
                  if json.loads(p.read_text()).get('kind') != 'tooling-request']
    for run in stale_runs:
        if run.get('status') in ('stale', 'paused'):
            command = run['resume_command']
            alternative = ('; or ' + run['retire_command']) if run.get('retire_command') else ''
            out.insert(0, ('wait' if run.get('lane_busy') else 'run',
                           f'{command}    # {run["status"]} lane {run["id"]}{alternative}'))
    if lane_pending and not any(r.get('status') in ('stale', 'paused') for r in stale_runs):
        import flow_lane
        live = Path(fdir) / 'lane-live.json'
        active = json.loads(live.read_text())['running'] if live.is_file() else flow_lane.running(fdir)
        out.insert(len(stops), ('wait', 'push lane is running; new work remains queued for the next run')
                   if active else ('run', 'python3 tools/flow.py lane-run'))
    return out or [('done', 'nothing to do')]


def dispatch_line(g, root=None):
    entry = {'model': g['reviewer_model'], 'harness': g.get('reviewer_harness', 'claude-code'), 'effort': 'high'}
    prompt = (f'Read docs/reviewer-runbook.md and follow it. Your brief is {g["brief"]}.' if entry['harness'] == 'codex'
              else f'Read {g["brief"]} and follow it.')
    preflight = (f'python3 {shlex.quote(str(TOOLS / "lint_review_readiness.py"))} --root '
                 + shlex.quote(str(g.get('review_root') or root or ROOT))
                 + ' --functions ' + ' '.join(g['functions']))
    return ('dispatch', f'Run `{preflight}` first; only after it passes: '
            f'Reviewer for {g["name"]}: [{len(g["functions"])} functions] {start_worker(entry, prompt, "reviewer")}. '
            f'Then: python3 tools/flow.py dispatched {g["name"]}')


# ------------------------------------------------------------------ other briefs

def brief_drafter(root, fdir, profile, count=1, queue_dir=None, tier="first"):
    p = profiles.get(profile)
    queue_dir = queue_dir or p['queue_dir']
    if tier not in profiles.drafter_tiers(profile):
        raise ValueError(f'profile has no {tier} Drafter')
    kind = 'normal' if Path(queue_dir).name in ('normal', 'mid') else 'small'
    queue_profile = 'full' if profile == 'full' else 'cheap'
    docs = [d.replace('drafter-card-small.md', 'drafter-card-normal.md') if kind == 'normal' else d
            for d in p['project_docs']]
    paths = []
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M')
    for i in range(1, count + 1):
        label = f'{profile}-{tier}-{Path(queue_dir).name}-{stamp}-{i}'
        text = f"""# Brief drafter-{label}

Role: Drafter, profile `{profile}` ({profiles.model_label(p['roles']['drafter'])}). Gates: G2 for Claude models (sheets with FNV
text); Luna-class models read only plain sheets for queues covered by the maintainer's exposure
grant. Those sheets' target listing and decompiler hints are input for writing original C++;
never copy their text. Skip FNV sections in older plain sheets and never read `.fnv.md`.
This brief does not expand an exposure grant. No Boat, no git, no network.

Read `docs/drafter-runbook.md` and follow it exactly. Your worker label is `<model>-{stamp}-{i}`
(for example `haiku-{stamp}-{i}`). Your unit kind is {kind}. Pass `--profile {queue_profile}` to `next`. Queue directory:
`{queue_dir}` (put `--queue-dir {queue_dir}` before the subcommand on every work_queue.py call).
Documents: {', '.join(docs)}. Stop on a function after {p['stuck_after']} counted
attempts with no change in its first mismatch; the unit budget is what `attempt` prints.

Return only the short table from the runbook ("Return message"); full details go to the queue.
Do not push, post publicly, mark `matched`, or start further agents.
"""
        if tier != 'first':
            entry = p['roles']['drafter_' + tier]
            text = f'''# Brief drafter-{label}

Role: {tier} Drafter, profile `{profile}`, tier `{tier}` ({profiles.model_label(entry)}).
Read docs/drafter-runbook.md and {', '.join(docs)}. The recorded exposure grant permits
reading function packs and FNV-variant sheets (`sheet.fnv.md` and `sheet-*.fnv.md`); use them as inputs.
Read the previous tiers' near-miss files (including `near-miss/earlier-*`), unit notes and
`{queue_dir}/results.jsonl` as hints.
Claim with `python3 tools/work_queue.py --queue-dir {queue_dir} next --worker <label> --profile {profile} --tier {tier}`.
Use `--tier {tier}` on queue done and release, and run
`tools/verifier/attempt --tier {tier} --queue-dir {queue_dir} <unit dir>` for every attempt.
Draft only the unpassed functions listed by the claim; previously passed functions remain regression comparisons.
You have {entry['attempts_per_function']} counted attempts per function, and a unit budget of
{entry['attempts_per_function']} times the number of unpassed functions. Keep per-function counts yourself.
For units extending existing source files, preserve every previously passing function body.
You may replace an uncompared placeholder for your assigned target and complete declarations
inside your own unit when that target requires them; every retained regression must still pass.
An accepted adjustor thunk and the destructor it calls are separate targets. A wrong accepted
body needs Engineer revocation, never silent replacement. Remove failed additions by exact text.
Record a function as failed only after its attempt budget is used or a named structural blocker;
stop when it passes. Record one result per newly attempted function and the unit.
No Boat, git or network. Do not push, post publicly, mark `matched`, or start further agents.
Return the short table from the runbook; full details go to the queue.
'''
        text += '''
Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

On claim, `next` prints the private draft checkout. That is the only place to edit source;
cd there and run every attempt there. Never edit source in the shared checkout. The sanctioned
`done` command runs the clean harvest check and snapshots the whole unit; remove failed additions
first. Before done or next, cd back to the printed queue control checkout: done can remove the
draft checkout. A refused harvest is reported, never worked around. Legacy claims without a checkout keep
their original location.
'''
        if Path(root).resolve() != ROOT.resolve():
            tool = ROOT / 'tools/work_queue.py'
            queue_path = (Path(root) / queue_dir).resolve()
            text += (f'\nThis checkout may have older tooling. Make the claim with the landed tool by path:\n'
                     f'`python3 {shlex.quote(str(tool))} --queue-dir {shlex.quote(str(queue_path))} '
                     f'next --worker <label> --profile {profile} --tier {tier}`.\n'
                     f'Use that same tool path and queue path for done and release. After claiming, '
                     f'run the checkout\'s own attempt command from the printed private draft checkout.\n')
        path = Path(root) / BRIEFS / f'drafter-{label}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        paths.append(path.relative_to(root).as_posix())
    log_event(fdir, 'drafter-brief', profile=profile, tier=tier, briefs=paths)
    return paths


def generator_confirm_units(root, manifests, tasks):
    """Preflight a generated selection and copy its tasks for ordinary two-host confirmation.

    Manifests describe a selection, never a review or acceptance. Original local-attempt tasks
    remain unchanged, so changing their symbol-map path cannot invalidate their resume binding.
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location('generator_stamp', TOOLS / 'stamp.py')
    stamp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stamp)
    from lint_reconstruction import SOURCE
    root, tasks = Path(root).resolve(), Path(tasks).resolve()
    inv = {(f['build_id'], f['rva'], f['size']): f for f in inventory(root)['functions']}
    target = json.loads((root / 'builds/target.json').read_text())
    pending, seen, compiled = [], set(), set()
    for manifest in manifests:
        path = root / manifest
        group = json.loads(path.read_text())
        refuse(group.get('schema') == 1 and group.get('kind') == 'generator-selection',
               'not a generator selection manifest')
        refuse(group.get('build_id') == target['build_id'], 'generator group build mismatch')
        refuse(group.get('image_sha256') == target['image_sha256'], 'generator group image mismatch')
        refuse(group.get('members'), 'empty generator group')
        refuse(group.get('generator_family') in ('const-return', 'member-return') and
               isinstance(group.get('generator_version'), str) and group['generator_version'] and
               re.fullmatch(r'[0-9a-f]{64}', group.get('template_digest', '')),
               'invalid generator origin')
        symbols_rel = group['symbols']
        symbols_path = Path(symbols_rel)
        refuse(not symbols_path.is_absolute() and '..' not in symbols_path.parts and
               symbols_path.parts[:2] == ('reports', target['build_id']), 'invalid group symbol map path')
        smap = json.loads((root / symbols_rel).read_text())
        refuse(smap.get('build_id') == target['build_id'], 'generator symbol map build mismatch')
        for member in group['members']:
            refuse(SOURCE.fullmatch(member['compiled']) and member['compiled'].endswith('.cpp'),
                   'invalid generator unit path')
            key = (group['build_id'], member['rva'], member['size'])
            refuse(key not in seen and member['compiled'] not in compiled, 'duplicate generator member or unit')
            seen.add(key); compiled.add(member['compiled'])
            refuse(key in inv, 'generator member is not an inventory entry with the same size')
            refuse(inv[key]['name'] == member['name'], 'generator member name differs from inventory')
            refuse(re.fullmatch(r'[a-z0-9][a-z0-9.-]*', member['task_id']), 'invalid generator task id')
            task_dir = tasks / member['task_id']
            refuse(task_dir.resolve().is_relative_to(tasks), 'generator task escapes task root')
            task = json.loads((task_dir / 'task.json').read_text())
            fn = (task.get('functions') or [{}])[0]
            refuse(task.get('task_id') == member['task_id'] and
                   task.get('build_id') == key[0] and len(task.get('functions') or []) == 1 and
                   int(str(fn.get('rva')), 0) == key[1] and fn.get('size') == key[2] and
                   task.get('compiled') == member['compiled'] and task.get('recipe') == group['recipe'],
                   'generator task identity or recipe mismatch')
            refuse(smap.get('symbols', {}).get(fn.get('symbol')) == dict(rva=key[1], size=key[2]),
                   'generator symbol target mismatch')
            digest = tu_digest(root, include_closure(root, member['compiled']))
            refuse(digest == member['source_digest'], 'generator source digest mismatch')
            origins = re.findall(r'^// Origin: (.+)$', (root / member['compiled']).read_text(), re.M)
            refuse(len(origins) == 1, 'generator source needs one origin record')
            origin = json.loads(origins[0])
            refuse(all(origin.get(k) == group[k] for k in
                       ('generator_family', 'generator_version', 'template_digest')) and
                   origin.get('name_source') == member['name_source'], 'generator origin differs from manifest')
            refuse(stamp.input_digest(root, task_dir) == member['input_digest'], 'generator input digest mismatch')
            task['symbols'] = symbols_rel
            task['record_notes'] = ['Generator selection only; ordinary per-function confirmation and review required.']
            pending.append((task, member))
    # No writes until the whole selection has passed preflight.
    writes = []
    for task, member in pending:
        dest = root / '.local/flow/generator-confirm' / member['task_id']
        text = json.dumps(task, indent=2) + '\n'
        if (dest / 'task.json').exists():
            refuse((dest / 'task.json').read_text() == text, 'confirmation task already exists with different content')
        writes.append((dest, text, member))
    units = {}
    for dest, text, member in writes:
        stamp.write_new(dest / 'task.json', text)
        units[str(dest)] = [hexrva(member['rva'])]
    return units


def brief_confirm(root, fdir, manifests=None, tasks=None):
    states = function_states(root, fdir, online=False)
    if manifests:
        refuse(tasks is not None, '--tasks is required with --manifests')
        units = generator_confirm_units(root, manifests, tasks)
        stale = []
    else:
        refuse(tasks is None, '--tasks requires --manifests')
        units = {}
        for rva, s in states.items():
            if s['state'] == 'drafted-pass' and s.get('unit'):
                units.setdefault(s['unit'], []).append(rva)
        stale = sorted(r for r, s in states.items() if s['state'] == 'confirm-stale')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M')
    lst = Path(root) / '.local/flow' / f'confirm-{stamp}.txt'
    lst.parent.mkdir(parents=True, exist_ok=True)
    lst.write_text(''.join(f'{u}\n' for u in sorted(units)))
    private_units = []
    for unit in sorted(units):
        if drafts.read((Path(root) / unit) / 'harvest.json'):
            continue
        task = json.loads((Path(root) / unit / 'task.json').read_text())
        if not task.get('symbols', 'symbols.json').startswith('reports/'):
            private_units.append(unit)
    binding_step = ''
    if private_units:
        bind_list = lst.with_name(lst.stem + '-bind.txt')
        bind_list.write_text(''.join(f'{u}\n' for u in private_units))
        binding_step = f'''   Before confirmation, publish these units' private bindings with
   `python3 tools/verifier/bind.py --list {bind_list.relative_to(root).as_posix()} --unit-maps`.
   This uses the compiled candidate and task packs, publishes immutable per-unit repository maps
   through `tools/symbol_map.py`, and updates each task's map path. Keep existing repository map
   paths, provenance and history; do not merge private maps into the global map or invent origins.
   A binding or provenance refusal needs Engineer triage, never a weaker check.
'''
    text = f"""# Brief confirm-{stamp}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: strong role of the profile (Claude: Engineer), or the routine orchestrator with a shell when every step below is a
plain run. Reproduce the drafted passes on two runner hosts (docs/verification.md, Runner hosts).

Units with a passing function ({len(units)}), list file `{lst.relative_to(root).as_posix()}`:
""" + ''.join(f'- `{u}`: {", ".join(sorted(r, key=lambda x: int(x, 16)))}\n' for u, r in sorted(units.items())) + f"""
Records that no longer bind their unit ({len(stale)}): {', '.join(stale) or 'none'}.

1. Harvested units are confirmed from their immutable harvest commit automatically; do not edit
   their task or source. For legacy units only, remove from `task.json` functions that did not pass (their near-miss
   files stay), as earlier confirm runs did. Every remaining function must be an inventory entry.
{binding_step}\
2. `tools/verifier/confirm --list {lst.relative_to(root).as_posix()} --replace` (the runner hosts of
   `.local/verifier/runners.json`; docs/verification.md, Runner hosts. Boat is retired: never pass
   `--boat`). Re-confirm stale records' units the same way.
3. A function that does not reproduce stays unconfirmed: note it; never edit a record.
4. `python3 tools/check.py` must pass. Then `python3 tools/flow.py next-actions`.

Return a table: unit, functions reproduced, functions not reproduced, reason. Full output to
`.local/handoffs/confirm-{stamp}.md`.
Do not push, post publicly, mark `matched`, or start further agents.
"""
    path = Path(root) / BRIEFS / f'confirm-{stamp}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    log_event(fdir, 'confirm-brief', units=sorted(units), stale=stale)
    return path.relative_to(root).as_posix()


def brief_triage(root, fdir, group=None, units=None, held=False):
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M')
    lines = []
    if group:
        g = load_group(fdir, group)
        _, blocks = read_review(root, g, inventory(root)['functions'])
        for rva, b in sorted(blocks.items()):
            if b.get('verdict') in ('reject', 'escalate'):
                lines.append(f'- {rva}: {b.get("verdict")} ({b.get("escalation_category")}); the reasons are in '
                             f'`{REVIEWS}/{g["task_id"]}.md`, block `## {g["build_id"]} {rva} ...`')
        g['rejects_briefed'] = utc()
        save_group(fdir, g)
    if held:
        for rva, s in sorted(function_states(root, fdir, online=False).items()):
            if s.get('held') and not s.get('group'):
                lines.append(f'- {rva} ({s.get("name")}): {s["detail"]}; read that review\'s block for the reasons')
    for u in units or []:
        lines.append(f'- unit `{u}`: failed drafting; attempt history in `{u}/attempts.jsonl`, near-misses in `{u}/near-miss/`')
    text = f"""# Brief triage-{stamp}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: strong role of the profile (Claude: Engineer, Opus; claude-low: Sol). Triage, fix and re-draft; you did not draft these functions (if you
did, say so and stop). Gates: as recorded; G2 for reading reviews and packs.

""" + '\n'.join(lines) + """

For a reject: fix the blocking ground named in the review, re-run `attempt`, re-confirm, and leave
the function for a fresh Reviewer run (never the run that rejected it, never this triage run). For an escalate
`other`: resolve it, then the same. For a failed unit: analyse the first mismatch, fix or save a
near-miss with the reason. Never weaken the comparator, validator, lint or a record.
Write details to `.local/handoffs/triage-""" + stamp + """.md`; return a table: function, outcome, file.
Do not push, post publicly, mark `matched`, or start further agents.
"""
    path = Path(root) / BRIEFS / f'triage-{stamp}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    log_event(fdir, 'triage-brief', group=group, units=list(units or []), held=held)
    return path.relative_to(root).as_posix()


def brief_direction(root, fdir):
    ev = events(fdir)
    n = 1 + sum(e['event'] == 'direction-check' for e in ev)
    frictions = sorted((Path(root) / '.local/flow').glob('friction-*.md'))
    text = f"""# Brief direction-check-{n}

Follow `docs/anti-eu-bureaucracy.md`; report to the orchestrator within 90 minutes and follow its box rule.

Role: direction check (`.claude/agents/direction-check.md`; strong role of the profile), fresh context. Read only;
you edit nothing except your own output file.

Read:
- the newest friction report: `{frictions[-1].relative_to(root).as_posix() if frictions else 'none yet: run python3 tools/friction.py --write first'}`
- `python3 tools/flow.py status` output
- the ten newest files in `.local/handoffs/`
- the census: `findings/token-census.md` (or the branch the orchestrator names)

Write `.local/handoffs/direction-check-{n}.md` with: what is going well, what to change (profile
default, group size, Reviewer model, briefs, tooling), each with the evidence line it rests on,
and what to escalate to the maintainer. Profile default rule: if the cheap profile's pass rate in
the friction report is below the threshold it prints, recommend flipping the default to `full`.
Return a five-line summary. Do not push, post publicly, mark `matched`, or start further agents.
"""
    path = Path(root) / BRIEFS / f'direction-check-{n}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.relative_to(root).as_posix()


# ------------------------------------------------------------------ integration

def run(cmd, root, step, env=None, log_path=None):
    """Run one integration step; raise FlowError with its output on failure."""
    fd = inherited_lock() if 'tools/accept_function.py' in cmd else None
    if fd is not None:
        env = dict(os.environ if env is None else env, SKYRIM_FLOW_LOCK_FD=str(fd))
    if log_path is None:
        r = subprocess.run(cmd, cwd=root, capture_output=True, text=True, env=env,
                           pass_fds=() if fd is None else (fd,))
        output = (r.stderr.strip() + '\n' + r.stdout.strip()).strip() if r.returncode else ''
    else:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('w') as stream:
            r = subprocess.run(cmd, cwd=root, stdout=stream, stderr=subprocess.STDOUT, text=True, env=env,
                               pass_fds=() if fd is None else (fd,))
        output = log_path.read_text(errors='replace')
    if r.returncode:
        tail = '\n'.join(output.splitlines()[-15:])
        raise FlowError(f'STOPPED at {step} (exit {r.returncode}); nothing after it ran.\n{tail}')
    return r.stdout if log_path is None else output


PATHSPEC_ARG_BYTES = 32768


def path_batches(paths):
    """Bound path arguments, including pointer overhead, independently of inventory size."""
    batch, size = [], 0
    for path in sorted(set(paths)):
        cost = len(os.fsencode(path)) + 16
        refuse(cost <= PATHSPEC_ARG_BYTES, 'git pathspec exceeds argument budget')
        if batch and size + cost > PATHSPEC_ARG_BYTES:
            yield batch
            batch, size = [], 0
        batch.append(path)
        size += cost
    if batch:
        yield batch


def changed(root, paths):
    """The paths among `paths` that differ from HEAD (new, modified or deleted)."""
    if not paths:
        return []
    # Raw -z output: the status columns are positional, so the output must not be stripped.
    batches = list(path_batches(paths))
    refuse(len(batches) < 2 or not any(path.startswith(':') for batch in batches for path in batch),
           'Git magic pathspecs are not supported across status batches')
    result = set()
    for batch in batches:
        r = subprocess.run(['git', 'status', '--porcelain', '-z', '--no-renames', '--untracked-files=all', '--',
                            *batch], cwd=root, capture_output=True, text=True)
        refuse(r.returncode == 0, f'git status failed: {r.stderr.strip()}')
        result.update(entry[3:] for entry in r.stdout.split('\0') if len(entry) > 3)
    return sorted(result)


def integration_tree(fdir, name):
    return Path(fdir) / 'integrate' / name / 'tree'


def remove_tree(root, tree, *, prune=False):
    git(root, 'worktree', 'remove', '--force', str(tree), check=False)
    shutil.rmtree(tree, ignore_errors=True)
    if prune:
        git(root, 'worktree', 'prune', check=False)


def carry_into_tree(root, tree, approved, by_rva, harvests=None):
    """Copy, from the shared checkout into the integration tree, only what the approved functions
    need: their inventory entries, match records and translation-unit files. Other units, which a
    Drafter may still be editing, stay out of the commit and cannot block it."""
    files = set()
    snapshots = {}
    for rva in approved:
        fn = by_rva[rva]
        refuse(fn.get('report'), f'{fn["id"]} names no match record in data/progress.json')
        files.add(fn['report'])
        if fn.get('status') == 'matched':
            review = Path(fn['report']).with_suffix('.review.json').as_posix()
            if (root / review).is_file():
                files.add(review)
        record = json.loads((root / fn['report']).read_text())
        files.update(record['source']['translation_unit'])
        compiled = record['source']['compiled']
        h = (harvests or {}).get(compiled) if harvests is not None else drafts.source_for(root, compiled, fn['rva'])
        if h and not h.get('integrated'):
            refuse(h['digest'] == record['source']['digest'], f'{fn["id"]}: harvest differs from confirmed record')
            for rel in record['source']['translation_unit']:
                blob = drafts.git(root, 'show', f'{h["commit"]}:{rel}')
                refuse(rel not in snapshots or snapshots[rel] == blob, f'incompatible harvest closures: {rel}')
                snapshots[rel] = blob
        map_name = (record.get('symbol_map') or {}).get('path')
        if map_name:
            files.add(map_name)
            history = history_name(map_name)
            if (root / history).is_file():
                files.add(history)
    for rel in sorted(files):
        src, dst = root / rel, tree / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if rel in snapshots:
            dst.write_bytes(snapshots[rel])
        else:
            refuse(src.is_file(), f'{rel} is missing from the checkout')
            shutil.copyfile(src, dst)
    path = tree / 'data/progress.json'
    data = json.loads(path.read_text())
    index = {fn['id']: i for i, fn in enumerate(data['functions'])}
    for rva in approved:
        fn = by_rva[rva]
        refuse(fn['id'] in index, f'{fn["id"]} is not an inventory entry on origin; land its inventory row first')
        data['functions'][index[fn['id']]] = fn
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')
    return sorted(files)


def integration_base(root, branch, with_metadata=False, *, remote=None):
    """Carry explicit, precommitted family metadata without carrying unpublished source."""
    remote = remote or f'origin/{branch}'
    ahead = git(root, 'rev-list', '--count', f'{remote}..HEAD')
    if ahead == '0':
        return remote
    refuse(with_metadata, f'the checkout holds {ahead} commit(s) {remote} lacks; push or drop them first')
    refuse(subprocess.run(['git', 'merge-base', '--is-ancestor', remote, 'HEAD'], cwd=root).returncode == 0,
           'metadata commits must descend from current origin; merge moving main first')
    commits = git(root, 'rev-list', f'{remote}..HEAD').splitlines()
    paths = set()
    snapshots = {}
    for commit in commits:
        parents = git(root, 'rev-list', '--parents', '-n', '1', commit).split()
        refuse(len(parents) in (2, 3), 'metadata commits must be ordinary commits or public-base merges')
        public = [p for p in parents[1:] if subprocess.run(
            ['git', 'merge-base', '--is-ancestor', p, remote], cwd=root).returncode == 0]
        refuse(len(parents) == 2 or public, 'metadata merge must have a parent already on origin')
        parent = parents[1] if len(parents) == 2 else public[-1]
        names = git(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', '--no-renames', parent, commit).splitlines()
        deleted = git(root, 'diff-tree', '--no-commit-id', '--name-only', '-r', '--diff-filter=D', parent, commit)
        refuse(names and not deleted and all(re.fullmatch(
            r'reports/[a-z0-9][a-z0-9-]*/(?:families/[0-9a-f]{64}|family-batches/[a-z0-9][a-z0-9-]*)\.json', p)
            for p in names), 'unpublished commits contain changes other than family metadata')
        for path in names:
            if path not in snapshots:
                tip = subprocess.check_output(['git', 'show', f'HEAD:{path}'], cwd=root)
                snapshots[path] = [tip]
                if '/family-batches/' in path:
                    planned = dict(fr.read(root, path), commitment=None, sample=None)
                    snapshots[path].append((json.dumps(planned, indent=2, sort_keys=True,
                                                       allow_nan=False) + '\n').encode())
            historical = subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=root)
            refuse(historical in snapshots[path],
                   'unpublished metadata history differs from the reviewed tip or canonical planned batch')
        paths.update(names)
    fr.validate_metadata(root)
    for path in paths:
        fr.committed(root, path, fr.read(root, path))
    return git(root, 'rev-parse', 'HEAD')


def _legacy_integrate(root, fdir, name, branch='main', push=True, ci_wait=600, python=sys.executable, approved_only=False,
              with_metadata=False):
    """Accept the approve blocks of one group's saved review, check, commit, push and watch CI.

    --approved-only leaves reject and escalation blocks held while integrating only approvals;
    the full sampling gate and all acceptance checks remain mandatory.

    The commit is built in its own worktree (under the flow dir) at origin's `branch`, never in the
    shared checkout: only the approved functions' entries, records and unit files are carried over,
    so other sessions' uncommitted work neither enters the commit nor blocks it. The shared checkout
    is left as it was; `flow.py sync` brings it up to origin afterwards.

    Refuses before any change when the review is missing, malformed or holds a blocking escalation,
    when the sampling gate is not met, or when unpublished commits are not explicitly admitted metadata.
    Each later step stops at its first failure. Re-running resumes after the last finished step.
    """
    root = Path(root)
    g = load_group(fdir, name)
    refuse(not (g.get('integrated') or {}).get('batch'),
           'resume combined integration with integrate-groups and its full group selection')
    refuse(g['kind'] in ('review', 'family'), f'{name} is a sampling group; integrate its primary group {g.get("pair")}')
    data = inventory(root)
    family_group = g['kind'] == 'family'
    refuse(not (family_group and approved_only), '--approved-only applies only to individual review groups')
    if family_group:
        blocks = {r: {'verdict': 'approve'} for r in g['functions']}
    else:
        status, blocks = read_review(root, g, data['functions'])
        refuse(status != 'missing', f'review {REVIEWS}/{g["task_id"]}.md is not saved yet; wait for the Reviewer')
        refuse(status == 'ok', f'review {g["task_id"]} {status}; run: python3 tools/flow.py redo-review {name}')
        esc = [r for r, b in blocks.items() if b.get('verdict') == 'escalate' and b.get('escalation_category') in BLOCKING_ESCALATIONS]
        refuse(approved_only or not esc, f'blocking escalation for {", ".join(esc)}: escalate to the maintainer; group held')
        ok, problem = sampling_gate(root, fdir, g, data)
        refuse(ok, f'sampling gate: {problem}')
    approved = sorted((r for r, b in blocks.items() if b.get('verdict') == 'approve'
                       and (not g.get('subset_of') or r in g['functions'])), key=lambda r: int(r, 16))
    refuse(approved, 'the review has no approve block; nothing to integrate')
    family_group_hold(root, fdir, [fn['id'] for fn in data['functions'] if hexrva(fn['rva']) in approved])
    integ = g.get('integrated') or {}
    refuse(not integ or bool(integ.get('approved_only')) == approved_only, 'resume with the same --approved-only mode')
    refuse(not integ or bool(integ.get('with_metadata')) == with_metadata, 'resume with the same --with-metadata mode')
    review_file = str(review_path(root, g).resolve())
    tree = integration_tree(fdir, name)
    if not integ.get('commit'):
        build_started = time.monotonic()
        git(root, 'fetch', '--quiet', 'origin', branch)
        base = integration_base(root, branch, with_metadata)
        remove_tree(root, tree)
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), base)
        drafts.label(tree, 'flow-integrate', name, 'integration')
        by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == g['build_id']}
        carried = carry_into_tree(root, tree, approved, by_rva, g.get('harvests'))
        data = inventory(tree)
        by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == g['build_id']}
        done = all(by_rva[r]['status'] == 'matched' for r in approved)
        printed = list(carried)
        if not done:
            private = tree / REVIEWS
            private.parent.mkdir(parents=True, exist_ok=True)
            private.symlink_to((root / REVIEWS).resolve(), target_is_directory=True)
            if family_group:
                batch = fr.read(root, g['batch_path'])
                for path in (g['batch_path'], batch['family_path']):
                    fr.committed(root, path, fr.read(root, path))
                    fr.committed(tree, path, fr.read(root, path))
                cmd = [python, 'tools/accept_function.py', '--family-batch', g['batch_path'],
                       '--family-flow-dir', str(fdir.resolve()), '--profile', g.get('profile', profiles.DEFAULT)]
            else:
                cmd = [python, 'tools/accept_function.py', '--all-approved', '--review', review_file,
                       '--profile', g.get('profile', profiles.DEFAULT)]
                if g.get('subset_of'):
                    cmd += ['--functions', *approved]
            out = run(cmd, tree, 'accept_function.py',
                      env=dict(os.environ, SKYRIM_FLOW_DIR=str(fdir.resolve())))
            take = False
            for line in out.splitlines():
                if line.startswith('changed files'):
                    take = True
                elif take and line.startswith('  '):
                    printed.append(line.strip().split('  ')[0])
                elif take:
                    take = False
        if done:
            run([python, 'tools/build_index.py'], tree, 'build_index.py')
        run([python, 'tools/build_progress_svg.py'], tree, 'build_progress_svg.py')
        data = inventory(tree)
        paths = set(printed) | {'data/progress.json', 'reconstruction/INDEX.md', 'docs/progress.svg', 'docs/progress-map.svg'}
        for fn in data['functions']:
            if fn.get('report'):
                paths.add(fn['report'])
                rec = tree / fn['report']
                if rec.is_file():
                    paths.update(json.loads(rec.read_text())['source']['translation_unit'])
                rv = rec.with_name(rec.name.replace('.json', '.review.json'))
                if rv.is_file():
                    paths.add(rv.relative_to(tree).as_posix())
        files = changed(tree, paths)
        refuse(files, 'nothing changed to commit')
        git(tree, 'add', '--', *files)
        commit_date = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        run([python, 'tools/build_model_trend.py', '--pending-date', commit_date], tree, 'build_model_trend.py')
        trend_files = ['README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg']
        git(tree, 'add', '--', *trend_files)
        files = sorted(set(files) | set(changed(tree, trend_files)))
        run([python, 'tools/check.py', '--staged'], tree, 'check.py --staged')
        accepted = len(approved)
        msg = (f'Accept {accepted} function(s) of review group {name}\n\n'
               f'Review {g["task_id"]}: {accepted} approve, '
               f'{sum(b.get("verdict") == "reject" for b in blocks.values())} reject; integrated by tools/flow.py.\n\n'
               'Co-Authored-By: Claude <noreply@anthropic.com>\n')
        run(['git', 'commit', '--quiet', '-m', msg], tree, 'git commit',
            env=dict(os.environ, GIT_COMMITTER_DATE=commit_date))
        integ = {'commit': git(tree, 'rev-parse', 'HEAD'), 'files': files, 'accepted': accepted, 'checks': None,
                 'pushed': None, 'ci': None, 'approved_only': approved_only, 'with_metadata': with_metadata,
                 'wall_seconds': {'build': time.monotonic() - build_started}}
        g['integrated'] = integ
        save_group(fdir, g)
    if not integ.get('checks'):
        started = time.monotonic()
        pre_push_checks(root, integ['commit'], python)
        integ.setdefault('wall_seconds', {})['checks'] = time.monotonic() - started
        integ['checks'] = utc()
        save_group(fdir, g)
    if not push:
        return g
    if not integ.get('pushed'):
        started = time.monotonic()
        # Fast-forward only. When origin moved meanwhile the commit is dropped, so the next run
        # rebuilds it on the new origin and re-runs every check, rather than pushing a stale base.
        try:
            run(['git', 'push', 'origin', f'{integ["commit"]}:refs/heads/{branch}'], root, 'git push')
        except FlowError:
            g['integrated'] = None
            save_group(fdir, g)
            remove_tree(root, tree)
            raise
        import claims as github_claims
        github_claims.sync_safe(root)
        integ.setdefault('wall_seconds', {})['push'] = time.monotonic() - started
        integ['pushed'] = utc()
        save_group(fdir, g)
        log_event(fdir, 'integrated', group=name, accepted=integ['accepted'], commit=integ['commit'])
        remove_tree(root, tree)
        # Draft/worktree pruning is explicit opt-in via flow.py worktrees prune.
    if integ.get('ci') != 'green':
        started = time.monotonic()
        r = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                           cwd=root, capture_output=True, text=True)
        wall = integ.setdefault('wall_seconds', {})
        wall['ci'] = wall.get('ci', 0) + time.monotonic() - started
        integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(r.returncode, 'unavailable')
        save_group(fdir, g)
        log_event(fdir, 'ci', group=name, result=integ['ci'], commit=integ['commit'])
        refuse(integ['ci'] == 'green', f'CI {integ["ci"].upper()} for {integ["commit"]}: '
               + ('fix main or report the cause to the maintainer before any further push.\n' if integ['ci'] == 'red'
                  else 'run integrate again later to re-check.\n') + r.stdout.strip())
    return g



def _integration_origin_unchanged(root, base, destination, carried, build_id, rvas):
    changed_paths = sorted({path for batch in path_batches(carried)
                            for path in git(root, 'diff', '--name-only', base, destination, '--', *batch).splitlines()})
    refuse(not changed_paths, 'origin changed carried files; reconcile before retry: ' + ', '.join(changed_paths))
    old = json.loads(git(root, 'show', base + ':data/progress.json'))
    new = json.loads(git(root, 'show', destination + ':data/progress.json'))
    old_entries = {(fn['build_id'], hexrva(fn['rva'])): fn for fn in old['functions']}
    new_entries = {(fn['build_id'], hexrva(fn['rva'])): fn for fn in new['functions']}
    refuse(all(old_entries.get((build_id, rva)) == new_entries.get((build_id, rva)) for rva in rvas),
           'origin changed selected inventory entries; reconcile before retry')


def _legacy_integrate_groups(root, fdir, names, batch_name, branch='main', push=True,
                     ci_wait=600, python=sys.executable):
    """Integrate disjoint, fully approved review groups in one commit; keep each review intact."""
    root, fdir = Path(root), Path(fdir)
    refuse(re.fullmatch(r'[a-z0-9][a-z0-9-]{0,99}', batch_name) is not None, 'invalid integration batch name')
    refuse(len(names) >= 2 and len(set(names)) == len(names), 'name at least two different review groups')
    data = inventory(root)
    selected, approvals, identity = [], {}, {}
    for name in names:
        g = load_group(fdir, name)
        refuse(g['kind'] == 'review', 'combined integration accepts individual review groups only')
        status, blocks = read_review(root, g, data['functions'])
        refuse(status == 'ok', f'{name}: saved review {status}')
        approved = sorted((r for r, b in blocks.items() if b.get('verdict') == 'approve'
                           and (not g.get('subset_of') or r in g['functions'])), key=lambda r: int(r, 16))
        refuse(set(approved) == set(g['functions']) and approved,
               f'{name}: every selected function needs approval; use an approved subset for held functions')
        ok, why = sampling_gate(root, fdir, g, data)
        refuse(ok, f'{name}: sampling gate: {why}')
        refuse(not set(approved) & set(approvals), 'review groups overlap')
        prior = g.get('integrated') or {}
        refuse(not prior or prior.get('batch') == batch_name, f'{name}: already has another integration')
        approvals.update({r: name for r in approved})
        selected.append((g, approved, str(review_path(root, g).resolve())))
        identity[name] = {'task_id': g['task_id'], 'build_id': g['build_id'],
                          'profile': g.get('profile', profiles.DEFAULT), 'functions': approved,
                          'review_sha256': hashlib.sha256(review_path(root, g).read_bytes()).hexdigest()}
    refuse(len({g['build_id'] for g, _, _ in selected}) == 1
           and len({g.get('profile', profiles.DEFAULT) for g, _, _ in selected}) == 1,
           'combined groups must share build and profile')
    family_group_hold(root, fdir, [fn['id'] for fn in data['functions'] if hexrva(fn['rva']) in approvals])
    receipt = fdir / 'combined' / f'{batch_name}.json'
    transaction = json.loads(receipt.read_text()) if receipt.is_file() else {'groups': identity, 'integrated': None}
    refuse(transaction['groups'] == identity, 'combined integration selection or saved review changed')
    integ = transaction['integrated'] or {}
    tree = integration_tree(fdir, 'combined-' + batch_name)

    def save():
        transaction['integrated'] = integ
        atomic_write(receipt, (json.dumps(transaction, indent=2) + '\n').encode())
        for group, approved, _ in selected:
            current = load_group(fdir, group['name'])
            current['integrated'] = dict(integ, accepted=len(approved), batch=batch_name)
            save_group(fdir, current)

    if not integ.get('commit'):
        started = time.monotonic()
        git(root, 'fetch', '--quiet', 'origin', branch)
        refuse(git(root, 'rev-list', '--count', f'origin/{branch}..HEAD') == '0',
               'the checkout has commits origin lacks')
        by_rva = {hexrva(fn['rva']): fn for fn in data['functions'] if fn['build_id'] == selected[0][0]['build_id']}
        source_paths = set()
        for rva in approvals:
            fn = by_rva[rva]
            source_paths.add(fn['report'])
            record = fr.read(root, fn['report'])
            source_paths.update(record['source']['translation_unit'])
            map_name = (record.get('symbol_map') or {}).get('path')
            if map_name:
                source_paths.add(map_name)
                if (root / history_name(map_name)).is_file():
                    source_paths.add(history_name(map_name))
        _integration_origin_unchanged(root, git(root, 'rev-parse', 'HEAD'),
                                      git(root, 'rev-parse', f'origin/{branch}'), sorted(source_paths),
                                      selected[0][0]['build_id'], approvals)
        remove_tree(root, tree)
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), f'origin/{branch}')
        drafts.label(tree, 'flow-integrate', batch_name, 'integration')
        base_revision = git(tree, 'rev-parse', 'HEAD')
        by_rva = {hexrva(fn['rva']): fn for fn in data['functions'] if fn['build_id'] == selected[0][0]['build_id']}
        carried = set()
        for group, approved, _ in selected:
            carried.update(carry_into_tree(root, tree, approved, by_rva, group.get('harvests')))
        printed = sorted(carried)
        private = tree / REVIEWS
        private.parent.mkdir(parents=True, exist_ok=True)
        private.symlink_to((root / REVIEWS).resolve(), target_is_directory=True)
        requests = [dict(review=review_file, functions=approved,
                         profile=group.get('profile', profiles.DEFAULT))
                    for group, approved, review_file in selected]
        request_file = tree / '.local' / 'accept-reviews.json'
        request_file.write_text(json.dumps(requests) + '\n')
        out = run([python, 'tools/accept_function.py', '--review-batch', str(request_file)],
                  tree, 'accept_function.py review batch',
                  env=dict(os.environ, SKYRIM_FLOW_DIR=str(fdir.resolve())))
        take = False
        for line in out.splitlines():
            if line.startswith('changed files'):
                take = True
            elif take and line.startswith('  '):
                printed.append(line.strip().split('  ')[0])
            elif take:
                take = False
        run([python, 'tools/build_progress_svg.py'], tree, 'build_progress_svg.py')
        paths = set(printed) | {'data/progress.json', 'reconstruction/INDEX.md', 'docs/progress.svg', 'docs/progress-map.svg'}
        for fn in inventory(tree)['functions']:
            if fn.get('report'):
                paths.add(fn['report'])
                rec = tree / fn['report']
                paths.update(json.loads(rec.read_text())['source']['translation_unit'])
                review = rec.with_name(rec.name.replace('.json', '.review.json'))
                if review.is_file():
                    paths.add(review.relative_to(tree).as_posix())
        files = changed(tree, paths)
        refuse(files, 'nothing changed to commit')
        git(tree, 'add', '--', *files)
        commit_date = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
        run([python, 'tools/build_model_trend.py', '--pending-date', commit_date], tree, 'build_model_trend.py')
        trend = ['README.md', 'docs/model-trend.svg', 'docs/progress-trend.svg']
        git(tree, 'add', '--', *trend)
        files = sorted(set(files) | set(changed(tree, trend)))
        run([python, 'tools/check.py', '--staged'], tree, 'check.py --staged')
        message = f'Accept {len(approvals)} functions from {len(names)} review groups\n\nGroups: ' + ', '.join(names)
        run(['git', 'commit', '--quiet', '-m', message], tree, 'git commit',
            env=dict(os.environ, GIT_COMMITTER_DATE=commit_date))
        integ = {'commit': git(tree, 'rev-parse', 'HEAD'), 'accepted': len(approvals), 'files': files,
                 'checks': None, 'pushed': None, 'ci': None, 'batch': batch_name,
                 'wall_seconds': {'build': time.monotonic() - started},
                 'base_revision': base_revision, 'carried_paths': sorted(carried)}
        save()
    if not integ.get('checks'):
        started = time.monotonic()
        pre_push_checks(root, integ['commit'], python)
        integ['wall_seconds']['checks'] = time.monotonic() - started
        integ['checks'] = utc()
        save()
    if not push:
        return transaction
    if not integ.get('pushed'):
        started = time.monotonic()
        try:
            run(['git', 'push', 'origin', f'{integ["commit"]}:refs/heads/{branch}'], root, 'git push')
        except FlowError as error:
            if 'non-fast-forward' not in str(error) and 'fetch first' not in str(error):
                raise
            git(root, 'fetch', '--quiet', 'origin', branch)
            destination = git(root, 'rev-parse', f'origin/{branch}')
            _integration_origin_unchanged(root, integ['base_revision'], destination, integ['carried_paths'],
                                          selected[0][0]['build_id'], approvals)
            # Replay the unchanged reviewed selection on the new origin, through the same gates.
            integ['wall_seconds']['push'] = time.monotonic() - started
            transaction.setdefault('unpublished_attempts', []).append(integ)
            transaction['integrated'] = None
            atomic_write(receipt, (json.dumps(transaction, indent=2) + '\n').encode())
            for group, _, _ in selected:
                current = load_group(fdir, group['name'])
                current['integrated'] = None
                save_group(fdir, current)
            remove_tree(root, tree)
            return _legacy_integrate_groups(root, fdir, names, batch_name, branch, push, ci_wait, python)
        import claims as github_claims
        github_claims.sync_safe(root)
        integ['wall_seconds']['push'] = time.monotonic() - started
        integ['pushed'] = utc()
        save()
        for group, approved, _ in selected:
            log_event(fdir, 'integrated', group=group['name'], accepted=len(approved), commit=integ['commit'])
        remove_tree(root, tree)
        # Draft/worktree pruning is explicit opt-in via flow.py worktrees prune.
    if integ.get('ci') != 'green':
        started = time.monotonic()
        result = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                                cwd=root, capture_output=True, text=True)
        wall = integ['wall_seconds']
        wall['ci'] = wall.get('ci', 0) + time.monotonic() - started
        integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(result.returncode, 'unavailable')
        save()
        for group, _, _ in selected:
            log_event(fdir, 'ci', group=group['name'], result=integ['ci'], commit=integ['commit'])
        refuse(integ['ci'] == 'green', f'CI {integ["ci"].upper()} for {integ["commit"]}: {result.stdout.strip()}')
    return transaction


def integrate(root, fdir, name, branch='main', push=True, ci_wait=600, python=sys.executable,
              approved_only=False, with_metadata=False, *, run_lane=False):
    """Enqueue an individual review group; optionally run the one shared push lane."""
    import flow_lane
    item = flow_lane.enqueue(root, fdir, 'review', [name], branch, approved_only, with_metadata)
    return flow_lane.run_lane(root, fdir, branch, push, ci_wait, python) if (run_lane or not push) and not flow_lane.running(fdir) else item


def integrate_groups(root, fdir, names, batch_name, branch='main', push=True, ci_wait=600,
                     python=sys.executable, *, run_lane=False):
    """Enqueue the existing multi-group selection in the shared lane."""
    import flow_lane
    refuse(len(names) >= 2 and len(set(names)) == len(names), 'name at least two different review groups')
    item = flow_lane.enqueue(root, fdir, 'groups', names, branch, name=batch_name)
    return flow_lane.run_lane(root, fdir, branch, push, ci_wait, python) if (run_lane or not push) and not flow_lane.running(fdir) else item


def integrate_family(root, fdir, path, branch='main', push=True, *, run_lane=False):
    """Enqueue a committed family batch without changing its population or sampling gates."""
    import flow_lane
    item = flow_lane.enqueue(root, fdir, 'family', [path], branch)
    return flow_lane.run_lane(root, fdir, branch, push) if (run_lane or not push) and not flow_lane.running(fdir) else item


def sync(root, branch='main'):
    """Fast-forward the shared checkout to origin after an integration, without losing anyone's work.

    The integrated unit files usually sit in the checkout as untracked or modified copies, which
    `git merge` refuses to overwrite. A copy byte-identical to origin's version is dropped first
    (nothing is lost: the merge brings the same bytes back); any other difference stops the sync
    with the list of files, so a Drafter's newer edit is never overwritten."""
    root = Path(root)
    refuse(git(root, 'rev-parse', '--abbrev-ref', 'HEAD') == branch, f'the checkout is not on {branch}')
    git(root, 'fetch', '--quiet', 'origin', branch)
    target = f'origin/{branch}'
    if git(root, 'rev-parse', 'HEAD') == git(root, 'rev-parse', target):
        return []
    refuse(subprocess.run(['git', 'merge-base', '--is-ancestor', 'HEAD', target], cwd=root).returncode == 0,
           f'the checkout has commits {target} lacks; resolve by hand')
    incoming = [p for p in git(root, 'diff', '--name-only', '--no-renames', 'HEAD', target).splitlines() if p]
    local = {}
    if incoming:
        out = ''.join(subprocess.run(['git', 'status', '--porcelain', '-z', '--no-renames', '--untracked-files=all',
                                      '--', *batch], cwd=root, check=True, capture_output=True, text=True).stdout
                      for batch in path_batches(incoming))
        local = {e[3:]: e[:2] for e in out.split('\0') if len(e) > 3}
    conflicts, same = [], []
    for rel, code in sorted(local.items()):
        path = root / rel
        theirs = subprocess.run(['git', 'show', f'{target}:{rel}'], cwd=root, capture_output=True)
        if code.strip() in ('??', 'M') and path.is_file() and theirs.returncode == 0 and path.read_bytes() == theirs.stdout:
            same.append((rel, code.strip()))
        else:
            conflicts.append(rel)
    refuse(not conflicts, 'local changes differ from the integrated versions; resolve by hand: ' + ', '.join(conflicts))
    for rel, code in same:
        if code == '??':
            (root / rel).unlink()
        else:
            git(root, 'checkout', '--quiet', 'HEAD', '--', rel)
    git(root, 'merge', '--quiet', '--ff-only', target)
    return [rel for rel, _ in same]


def function_only_diff(root, base_revision, commit):
    """Only the lane's explicit base permits the function-only local check policy."""
    if not base_revision:
        return False
    paths = git(root, 'diff', '--no-renames', '--name-only', base_revision, commit).splitlines()
    generated = {'data/progress.json', 'docs/progress.svg', 'docs/progress-map.svg',
                 'docs/model-trend.svg', 'docs/progress-trend.svg'}
    if 'README.md' in paths:
        start, end = '<!-- model-trend-totals -->', '<!-- /model-trend-totals -->'
        blobs = [subprocess.run(['git', 'show', revision + ':README.md'], cwd=root,
                                capture_output=True, text=True) for revision in (base_revision, commit)]
        before, after = [blob.stdout if blob.returncode == 0 else '' for blob in blobs]
        def outside(text):
            if text.count(start) != 1 or text.count(end) != 1:
                return None
            prefix, tail = text.split(start)
            if end not in tail:
                return None
            return prefix, tail.split(end)[1]
        if outside(before) is not None and outside(before) == outside(after):
            generated.add('README.md')  # Only the generated totals; prose still needs full checks.
    return bool(paths) and all(p.startswith(('reconstruction/', 'reports/')) or p in generated
                               for p in paths)


def pre_push_checks(root, commit, python, *, candidate=False, log_dir=None, base_revision=None):
    """AGENTS.md checks on a clean exact commit; a lane candidate is already isolated."""
    if candidate:
        refuse(git(root, 'rev-parse', 'HEAD') == commit and not git(root, 'status', '--porcelain', '--untracked-files=no'),
               'lane candidate differs from its commit before checks')
        commands = [('check', [python, 'tools/check.py']),
                          ('tests', ([python, 'tools/test_suite.py'] if (Path(root) / 'tools/test_suite.py').is_file()
                                     else [python, '-m', 'unittest', 'discover', '-s', 'tests', '-v'])),
                          ('site', [python, 'tools/build_site.py'])]
        if function_only_diff(root, base_revision, commit):
            commands = commands[:1]
            print('Function-only lane tree: acceptance checks, check.py and exact-SHA CI; '
                  'full unit suite and site build run in CI', flush=True)
        for name, cmd in commands:
            options = {'log_path': Path(log_dir) / (name + '.log')} if log_dir is not None else {}
            run(cmd, root, {'check': 'check.py', 'tests': 'unit tests', 'site': 'build_site.py'}[name] + ' (lane tree)', **options)
        refuse(not git(root, 'status', '--porcelain', '--untracked-files=no'),
               'checks changed tracked candidate files')
        return
    tmp = Path(tempfile.mkdtemp(prefix='flow-check-'))
    tree = tmp / 'tree'
    git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), commit)
    drafts.label(tree, 'flow-check', commit, 'integration-check')
    try:
        run([python, 'tools/check.py'], tree, 'check.py (clean tree)')
        run([python, 'tools/test_suite.py'] if (tree / 'tools/test_suite.py').is_file()
            else [python, '-m', 'unittest', 'discover', '-s', 'tests'], tree, 'unit tests (clean tree)')
        run([python, 'tools/build_site.py'], tree, 'build_site.py (clean tree)')
    finally:
        git(root, 'worktree', 'remove', '--force', str(tree), check=False)
        shutil.rmtree(tmp, ignore_errors=True)


# ------------------------------------------------------------------ status

def status_table(root, fdir, online=True):
    states = function_states(root, fdir, online=online)
    counts = {s: 0 for s in STATES}
    for row in states.values():
        counts[row.get('state') or 'queued'] = counts.get(row.get('state') or 'queued', 0) + 1
    lines = ['state counts: ' + ', '.join(f'{k} {v}' for k, v in counts.items() if v)]
    for name, g in groups(fdir).items():
        integ = g.get('integrated') or {}
        lines.append(f'group {name} ({g["kind"]}, {len(g["functions"])} fn, reviewer {g["reviewer_model"]}, '
                     f'task {g["task_id"]}): dispatched {g.get("dispatched") or "no"}; sampled {len(g.get("sampled") or [])}; '
                     f'integrated {integ.get("commit", "no")[:12] if integ.get("commit") else "no"}; ci {integ.get("ci") or "-"}')
    for qdir, profile, u, state, who, claim in queue_units(root):
        if state in ('claimed', 'stale'):
            lines.append(f'claim {state}: {u["dir"]} by {who} ({profile})')
    return lines, states


def parser():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--flow-dir')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    p.add_argument('--offline', action='store_true', help='do not read origin (pushed state unknown)')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('worktrees')
    ws = s.add_subparsers(dest='worktrees_action', required=True)
    ws.add_parser('list')
    prune = ws.add_parser('prune')
    prune.add_argument('--dry-run', action='store_true')
    s = sub.add_parser('import-state')
    s.add_argument('source', type=Path)
    s.add_argument('--reviews', type=Path, required=True)
    s = sub.add_parser('session-start')
    s.add_argument('--profile', default=profiles.DEFAULT, choices=sorted(profiles.PROFILES))
    sub.add_parser('next-actions')
    s = sub.add_parser('reconfirm-dropped')
    s.add_argument('--resume')
    s.add_argument('--dry-run', action='store_true')
    s.add_argument('--wake-mac')
    s.add_argument('--allow-low-disk', action='store_true')
    s = sub.add_parser('status')
    s.add_argument('--functions', action='store_true')
    s = sub.add_parser('review-group')
    s.add_argument('--max', type=int, default=DEFAULT_GROUP_MAX)
    s.add_argument('--reviewer-model', help='override the profile\'s Reviewer (refused unless the rule admits it)')
    s = sub.add_parser('family-plan')
    s.add_argument('--spec', required=True)
    s.add_argument('--supersede', help='replace an unapproved family while preserving its history')
    s = sub.add_parser('family-dispatched')
    s.add_argument('path')
    s = sub.add_parser('family-approve')
    s.add_argument('path')
    s.add_argument('--review', required=True)
    s = sub.add_parser('family-batch')
    s.add_argument('family_path')
    s.add_argument('--name', required=True)
    s.add_argument('--seed', required=True)
    s.add_argument('--functions', nargs='+', required=True)
    s = sub.add_parser('family-draw')
    s.add_argument('path')
    s = sub.add_parser('family-pause')
    s.add_argument('path')
    s.add_argument('--reason', required=True)
    s = sub.add_parser('integrate-family')
    s.add_argument('--run', action='store_true', help='run the push lane after enqueueing')
    s.add_argument('path')
    s.add_argument('--no-push', action='store_true')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('dispatched')
    s.add_argument('group')
    s.add_argument('--rerun', action='store_true', help='the sampling re-run, not the Reviewer, was started')
    s = sub.add_parser('void-review')
    s.add_argument('group')
    s.add_argument('--reason', required=True)
    s.add_argument('--setup-failure', action='store_true')
    s.add_argument('--functions', nargs='+', help='RVAs to void; preserve the other review blocks')
    s = sub.add_parser('redo-review')
    s.add_argument('group')
    s = sub.add_parser('record-rerun')
    s.add_argument('group')
    s.add_argument('--compare', required=True)
    s = sub.add_parser('split-group')
    s.add_argument('group')
    s.add_argument('--functions', nargs='+', required=True)
    s = sub.add_parser('integrate')
    s.add_argument('--run', action='store_true', help='run the push lane after enqueueing')
    s.add_argument('group')
    s.add_argument('--approved-only', action='store_true', help='integrate approvals while leaving other functions held')
    s.add_argument('--with-metadata', action='store_true', help='carry only committed family metadata before acceptance')
    s.add_argument('--no-push', action='store_true', help='stop after the clean-tree checks')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('integrate-groups')
    s.add_argument('--run', action='store_true', help='run the push lane after enqueueing')
    s.add_argument('groups', nargs='+')
    s.add_argument('--name', required=True)
    s.add_argument('--no-push', action='store_true')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('integrate-labels')
    s.add_argument('--functions', nargs='+', required=True)
    s.add_argument('--branch', default='main')
    s.add_argument('--run', action='store_true')
    s.add_argument('--no-push', action='store_true')
    s = sub.add_parser('lane-run')
    s.add_argument('--min-free-gb', type=float, help='minimum free disk space (GB); default 3, or SKYRIM_LANE_MIN_FREE_GB')
    s.add_argument('--branch', default='main')
    s.add_argument('--no-push', action='store_true')
    s.add_argument('--ci-wait', type=int, default=600)
    s.add_argument('--resume', help='resume this exact unfinished run')
    for command in ('integrate', 'integrate-groups', 'integrate-family', 'integrate-labels', 'lane-run'):
        sub.choices[command].add_argument('--wait-lane', action=argparse.BooleanOptionalAction, default=True,
                                         help='wait for a busy lane (default); --no-wait-lane probes without waiting')
        sub.choices[command].add_argument('--soft-free-gb', type=float, help='soft disk floor; default 10 GB')
        sub.choices[command].add_argument('--allow-low-disk', action='store_true', help='explicitly override only the soft floor')
    sub.add_parser('lane-status')
    s = sub.add_parser('lane-retire')
    s.add_argument('run_id')
    s.add_argument('--reason', required=True)
    s = sub.add_parser('tooling-push')
    s.add_argument('--branch', default='main')
    s.add_argument('--ci-wait', type=int, default=600)
    s.add_argument('--resume')
    s.add_argument('--wait-lane', action=argparse.BooleanOptionalAction, default=True,
                   help='queue the committed tip and wait for its batch outcome (default)')
    s.add_argument('--soft-free-gb', type=float)
    s.add_argument('--allow-low-disk', action='store_true')
    s = sub.add_parser('cleanup')
    s.add_argument('--dry-run', action='store_true')
    s.add_argument('--prune-claims', action='store_true', help='also prune clean completed harvest checkouts; preserve refs')
    s.add_argument('--keep-task-prefix', action='append', default=[], help='retain draft tasks with this prefix')
    s = sub.add_parser('sync')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('brief')
    s.add_argument('kind', choices=('drafter', 'confirm', 'triage', 'rerun', 'direction'))
    s.add_argument('--profile', default=profiles.DEFAULT, choices=sorted(profiles.PROFILES))
    s.add_argument('--count', type=int, default=1)
    s.add_argument('--queue-dir', help='drafter queue kind, independent of the drafting profile')
    s.add_argument('--tier', choices=('first', 'fallback', 'strong'), default='first')
    s.add_argument('--group')
    s.add_argument('--units', nargs='+')
    s.add_argument('--manifests', nargs='+', help='generator selection manifests (confirm only)')
    s.add_argument('--tasks', type=Path, help='original generated task directory (confirm only)')
    s.add_argument('--held', action='store_true', help='functions held by a reject or escalate in an earlier review')
    s = sub.add_parser('baseline')
    s.add_argument('component', choices=('recipe', 'compiler', 'drafter_prompt', 'reviewer_prompt', 'reviewer_model',
                                          'acceptance_rule'))
    s.add_argument('value')
    s.add_argument('count', type=int)
    s = sub.add_parser('event')
    s.add_argument('kind', choices=('friction', 'direction-check'))
    s.add_argument('--note', default='')
    return p


def main(argv=None):
    a = parser().parse_args(argv)
    root = a.root
    fdir = flow_dir(root, a.flow_dir)
    if a.cmd == 'tooling-push' and a.flow_dir is None:
        try:
            fdir = af.active_flow_dir(root)
        except (af.Refused, OSError) as error:
            print(f'flow: {error}', file=sys.stderr)
            return 1
    if a.cmd == 'worktrees':
        import flow_worktrees
        return flow_worktrees.run(root, fdir, a.worktrees_action, getattr(a, 'dry_run', False))
    if a.cmd == 'import-state':
        fdir = af.active_flow_dir(root)
    if a.cmd in ('status', 'next-actions'):
        import flow_lane
        try:
            with tempfile.TemporaryDirectory(prefix='flow-read-') as directory:
                frozen = Path(directory) / 'flow'
                flow_lane.snapshot(fdir, frozen)
                return execute(a, root, frozen)
        except (FlowError, ValueError, OSError) as exc:
            print(f'flow: {exc}', file=sys.stderr)
            return 1
    if a.cmd in ('integrate', 'integrate-groups', 'integrate-family', 'integrate-labels', 'lane-run', 'lane-status',
                 'lane-retire', 'tooling-push', 'cleanup', 'sync', 'reconfirm-dropped'):
        return execute(a, root, fdir)
    # Readers take the same short scheduling lock as state mutations.
    with state_lock(fdir):
        return execute(a, root, fdir)


def execute(a, root, fdir):
    try:
        if a.cmd != 'import-state':
            require_complete(fdir)
        if a.cmd == 'import-state':
            from flow_import import import_state
            receipt = import_state(root, fdir, a.source, a.reviews)
            print(json.dumps({k: receipt[k] for k in ('source', 'groups', 'review_files', 'complete')}, indent=2, sort_keys=True))
        elif a.cmd == 'session-start':
            log_event(fdir, 'session-start', profile=a.profile)
            print(f'session started with profile {a.profile}; next: python3 tools/flow.py next-actions')
            print('\n'.join(profiles.show(a.profile)))
        elif a.cmd == 'reconfirm-dropped':
            import flow_reconfirm
            result = flow_reconfirm.execute(root, fdir, resume=a.resume, dry_run=a.dry_run,
                                            wake_mac=a.wake_mac, allow_low_disk=a.allow_low_disk)
            print(json.dumps(result, indent=2, sort_keys=True))
        elif a.cmd == 'next-actions':
            for i, (kind, text) in enumerate(next_actions(root, fdir, online=not a.offline), 1):
                print(f'{i}. [{kind}] {text}')
        elif a.cmd == 'status':
            lines, states = status_table(root, fdir, online=not a.offline)
            print('\n'.join(lines))
            if a.functions:
                for rva, s in sorted(states.items(), key=lambda kv: int(kv[0], 16)):
                    print(f'{rva}\t{s.get("state")}\t{s.get("group") or "-"}\t{s.get("profile") or "-"}\t{s.get("detail") or ""}')
        elif a.cmd == 'family-plan':
            path = plan_family(root, a.spec, fdir, a.supersede)
            print(path)
            print(family_brief(root, path, session_profile(fdir), fdir)[1])
        elif a.cmd == 'family-dispatched':
            task, _ = family_brief(root, a.path, session_profile(fdir), fdir)
            log_event(fdir, 'family-dispatched', task=task, family=a.path)
            print('family Reviewer dispatched: ' + task)
        elif a.cmd == 'family-approve':
            print(approve_family(root, fdir, a.path, a.review))
        elif a.cmd == 'family-batch':
            print(plan_family_batch(root, a.family_path, a.name, a.seed, a.functions))
            print('Engineer: commit the seed and population before family-draw; commit the draw before any acceptance.')
        elif a.cmd == 'family-draw':
            batch = draw_family_batch(root, a.path)
            print('sample: ' + ' '.join(batch['sample']))
            print('Engineer: commit the draw before reviewing or accepting the batch.')
        elif a.cmd == 'family-pause':
            pause_family(root, a.path, a.reason)
            print('family paused; assess accepted members and revoke invalidated evidence')
        elif a.cmd == 'review-group':
            made = review_group(root, fdir, a.max, a.reviewer_model)
            if not made:
                print('no confirmed function waits for a review group')
            for name in made:
                g = load_group(fdir, name)
                print(f'group {name}: {len(g["functions"])} function(s), brief {g["brief"]}'
                      + (f'; sampled {len(g["sampled"])} -> group {g["pair"]}, brief {load_group(fdir, g["pair"])["brief"]}, '
                         f're-run brief .local/briefs/rerun-{name}.md' if g['sampled'] else ''))
            print('next: python3 tools/flow.py next-actions')
        elif a.cmd == 'dispatched':
            g = load_group(fdir, a.group)
            g['rerun_dispatched' if a.rerun else 'dispatched'] = utc()
            save_group(fdir, g)
            log_event(fdir, 'rerun-dispatched' if a.rerun else 'dispatched', group=a.group, task_id=g['task_id'],
                      reviewer_model=g['reviewer_model'])
            print(f'{a.group} marked {"re-run " if a.rerun else ""}dispatched')
        elif a.cmd == 'void-review':
            done = void_review(root, fdir, a.group, a.reason, a.setup_failure, a.functions)
            print(f'{a.group}: retired {len(done)} verdict(s); regroup for a fresh review' if done
                  else f'{a.group}: reset unfulfilled dispatch; no saved verdict was changed')
        elif a.cmd == 'redo-review':
            g = redo_review(root, fdir, a.group)
            print(f'{a.group}: new task id {g["task_id"]}, brief {g["brief"]}; dispatch a fresh Reviewer with it')
        elif a.cmd == 'record-rerun':
            agree, other = record_rerun(root, fdir, a.group, a.compare)
            print(f'{a.group}: {len(agree)} AGREE' + (f'; NOT AGREE {", ".join(other)}: escalate' if other else ''))
            return 1 if other else 0
        elif a.cmd == 'split-group':
            g = split_group(root, fdir, a.group, a.functions)
            print(f'{g["name"]}: {len(g["functions"])} functions; parent and saved reviews unchanged')
            print(f'next: python3 tools/flow.py integrate {g["name"]} --approved-only')
        elif a.cmd in ('integrate', 'integrate-groups', 'integrate-family', 'integrate-labels'):
            import flow_lane
            kind = {'integrate': 'review', 'integrate-groups': 'groups',
                    'integrate-family': 'family', 'integrate-labels': 'label'}[a.cmd]
            selection = ([a.group] if kind == 'review' else a.groups if kind == 'groups'
                         else [a.path] if kind == 'family' else a.functions)
            item = flow_lane.enqueue(root, fdir, kind, selection, a.branch,
                                     getattr(a, 'approved_only', False), getattr(a, 'with_metadata', False),
                                     getattr(a, 'name', None))
            print(f'queued {item["id"]}: {kind}; next: python3 tools/flow.py lane-run')
            if a.run or a.no_push:
                if flow_lane.running(fdir) and not a.wait_lane:
                    print('push lane is already running; request remains queued for the next run')
                else:
                    print(json.dumps(flow_lane.run_lane(root, fdir, a.branch, not a.no_push,
                                     soft_free_gb=a.soft_free_gb, allow_low_disk=a.allow_low_disk,
                                     wait_lane=a.wait_lane), indent=2))
        elif a.cmd == 'lane-run':
            import flow_lane
            print(json.dumps(flow_lane.run_lane(root, fdir, a.branch, not a.no_push, a.ci_wait, min_free_gb=a.min_free_gb,
                             soft_free_gb=a.soft_free_gb, allow_low_disk=a.allow_low_disk, resume=a.resume,
                             wait_lane=a.wait_lane), indent=2))
        elif a.cmd == 'lane-status':
            import flow_lane
            with state_lock(fdir):
                items = [flow_lane.read(p) for p in sorted((fdir / 'lane/queue').glob('*.json'))]
                runs = [flow_lane.read(p) for p in sorted((fdir / 'lane/runs').glob('*.json'))]
                tooling = [flow_lane.read(p) for p in sorted((fdir / 'lane/tooling').glob('*.json'))]
                inputs = [flow_lane.read(p) for p in sorted((fdir / 'lane/tooling-queue').glob('*.json'))]
            active = flow_lane.running(fdir)
            print(json.dumps(dict(queue=items, tooling_inputs=inputs, runs=[flow_lane.run_status(root, fdir, r, active) for r in runs],
                                  tooling=[flow_lane.run_status(root, fdir, r, active) for r in tooling]), indent=2))
        elif a.cmd == 'lane-retire':
            import flow_lane
            print(json.dumps(flow_lane.retire(root, fdir, a.run_id, a.reason), indent=2))
        elif a.cmd == 'tooling-push':
            import flow_lane
            print(json.dumps(flow_lane.publish_tooling(root, fdir, a.branch, a.ci_wait, resume=a.resume, wait_lane=a.wait_lane,
                             soft_free_gb=a.soft_free_gb, allow_low_disk=a.allow_low_disk), indent=2))
        elif a.cmd == 'cleanup':
            import flow_cleanup
            print(json.dumps(flow_cleanup.cleanup(root, fdir, a.dry_run, a.prune_claims, a.keep_task_prefix), indent=2))
        elif a.cmd == 'sync':
            dropped = sync(root, a.branch)
            print(f'checkout at origin/{a.branch}; {len(dropped)} identical local cop(ies) replaced by the integrated files')
        elif a.cmd == 'brief':
            if a.kind == 'drafter':
                for path in brief_drafter(root, fdir, a.profile, a.count, a.queue_dir, a.tier):
                    print(path)
            elif a.kind == 'confirm':
                print(brief_confirm(root, fdir, a.manifests, a.tasks))
            elif a.kind == 'triage':
                refuse(a.group or a.units or a.held, 'brief triage needs --group, --units or --held')
                print(brief_triage(root, fdir, a.group, a.units, a.held))
            elif a.kind == 'rerun':
                refuse(a.group, 'brief rerun needs --group')
                g = load_group(fdir, a.group)
                data = inventory(root)
                by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == g['build_id']}
                print(write_rerun_brief(root, g, by_rva))
            else:
                print(brief_direction(root, fdir))
        elif a.cmd == 'baseline':
            v = versions(fdir)
            v.setdefault('baseline', {}).setdefault(a.component, {})[a.value] = a.count
            fdir.mkdir(parents=True, exist_ok=True)
            atomic_write(fdir / 'versions.json', (json.dumps(v, indent=2, sort_keys=True) + '\n').encode())
            log_event(fdir, 'baseline', component=a.component, value=a.value, count=a.count)
            print(f'baseline {a.component}={a.value}: {a.count}')
        elif a.cmd == 'event':
            log_event(fdir, a.kind, note=a.note)
            print(f'recorded {a.kind}')
    except (FlowError, af.Refused, wq.QueueError, ValueError, KeyError, TypeError, OSError) as exc:
        print(f'flow: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
