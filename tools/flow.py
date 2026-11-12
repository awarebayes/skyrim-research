#!/usr/bin/env python3
"""Pipeline state and next steps, so a routine orchestrator executes a list instead of tracking state.

    python3 tools/flow.py session-start                  # mark the start of a work session
    python3 tools/flow.py next-actions                   # the exact next steps, in order
    python3 tools/flow.py status [--functions]           # counts per state, groups, stale claims
    python3 tools/flow.py review-group [--max 18]        # group confirmed functions, pick the sample, write briefs
    python3 tools/flow.py dispatched <group>             # a Reviewer was started on that group's brief
    python3 tools/flow.py redo-review <group>            # new task id after a review the parser refused
    python3 tools/flow.py record-rerun <group> --compare FILE   # sampling re-run result (AGREE/DISAGREE rows)
    python3 tools/flow.py integrate <group> [--no-push]  # accept, check, commit, push, watch CI, in its own worktree; stops at the first failure
    python3 tools/flow.py sync                           # fast-forward the shared checkout after an integration
    python3 tools/flow.py brief drafter|confirm|triage|rerun|direction ...   # write a brief file under .local/briefs/
    python3 tools/flow.py baseline <component> <value> <count>  # versions already past their first 20 (an Opus call)
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
import subprocess
import sys
import tempfile

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import accept_function as af  # noqa: E402
import profiles  # noqa: E402
from source_digest import tu_digest  # noqa: E402
import work_queue as wq  # noqa: E402

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
QUEUE_PROFILE = {'small': 'cheap', 'full': 'full'}
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
    fdir.mkdir(parents=True, exist_ok=True)
    with open(fdir / 'events.jsonl', 'a') as out:
        out.write(json.dumps(dict(detail, event=event, time=utc()), sort_keys=True) + '\n')


def events(fdir):
    path = fdir / 'events.jsonl'
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()] if path.is_file() else []


def groups(fdir):
    gdir = fdir / 'groups'
    return {p.stem: json.loads(p.read_text()) for p in sorted(gdir.glob('*.json'))} if gdir.is_dir() else {}


def save_group(fdir, g):
    (fdir / 'groups').mkdir(parents=True, exist_ok=True)
    (fdir / 'groups' / f'{g["name"]}.json').write_text(json.dumps(g, indent=2, sort_keys=True) + '\n')


def load_group(fdir, name):
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
        profile = QUEUE_PROFILE.get(qdir.name, qdir.name)
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
                    r.setdefault('profile', QUEUE_PROFILE.get(qdir.name, qdir.name))
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
        digest = tu_digest(root, rec['source']['translation_unit'])
    except (OSError, ValueError, KeyError):
        return 'confirm-stale'
    return 'confirmed' if len(hosts) >= 2 and digest == rec['source'].get('digest') else 'confirm-stale'


def git(root, *args, check=True):
    r = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
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


def review_path(root, task_id):
    return Path(root) / REVIEWS / f'{task_id}.md'


def read_review(root, g, functions):
    """(status, {rva: block}) of a group's saved review: status 'missing', 'malformed: <why>' or 'ok'."""
    path = review_path(root, g['task_id'])
    if not path.is_file():
        return 'missing', {}
    try:
        text = path.read_text(encoding='utf-8')
        title, header, blocks = af.review_blocks(text)
        af.refuse(title == g['task_id'], f'title is {title!r}, not {g["task_id"]!r}')
        af.refuse_malformed(header, blocks, functions)
        af.refuse(header.get('fresh_context') == 'yes', 'fresh_context is not yes')
        af.refuse(header.get('drafted_or_triaged_any_reviewed_function') == 'no', 'drafted_or_triaged is not no')
        af.refuse(bool(header.get('reviewer_model')), 'no reviewer_model')
        want = 'yes' if g['kind'] == 'sampling' else 'no'
        af.refuse(header.get('sampling_second_pass') == want, f'sampling_second_pass is not {want}')
    except (af.Refused, UnicodeDecodeError) as exc:
        return f'malformed: {exc}', {}
    out = {}
    for parts, body in blocks:
        if len(parts) == 3 and parts[0] == g['build_id'] and re.fullmatch(r'0x[0-9a-f]+', parts[1]):
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

def function_states(root, fdir, branch='main', online=True):
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
    return {'recipe': rec['recipe']['sha256'][:12], 'compiler': rec['toolchain_pin']['sha256'][:12],
            'drafter_prompt': f'{profile}:{file_hash(card) if card.startswith("docs/") else card}',
            'reviewer_prompt': file_hash('.claude/agents/reviewer.md') + file_hash('docs/reviewer-runbook.md'),
            'reviewer_model': reviewer_class(model),
            'acceptance_rule': hashlib.sha256((file_hash('docs/verification.md') + file_hash('tools/accept_function.py'))
                                              .encode()).hexdigest()[:12]}


def accepted_counts(root, fdir, states):
    """{component: {value: count}} of functions accepted through flow groups, plus recorded baselines."""
    counts = {}
    for comp, vals in versions(fdir).get('baseline', {}).items():
        for v, n in vals.items():
            counts.setdefault(comp, {})[v] = n
    for g in groups(fdir).values():
        if g['kind'] != 'review':
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


# ------------------------------------------------------------------ reviewer model

# Phrases by which the acceptance rule admits a Reviewer class besides Opus. Until docs/verification.md
# holds one, that class is refused, so a profile cannot enable a Reviewer the rule does not admit.
ADMITTING_PHRASES = {'sonnet': 'Sonnet class by default', 'terra': 'Terra class as the Reviewer'}


def reviewer_class(model):
    m = (model or '').lower()
    return next((c for c in ('opus', 'sonnet', 'terra', 'sol', 'haiku', 'luna', 'fable') if c in m), m)


def allowed_reviewer_models(root):
    """Reviewer classes the acceptance rule admits: Opus, plus each class whose phrase it contains."""
    text = (Path(root) / 'docs/verification.md').read_text()
    return tuple(c for c, phrase in ADMITTING_PHRASES.items() if phrase in text) + ('opus',)


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


def review_group(root, fdir, max_size=DEFAULT_GROUP_MAX, reviewer_model=None, seed='flow'):
    """Group every confirmed function not yet in a review group, unit by unit; returns new group names."""
    root = Path(root)
    allowed = allowed_reviewer_models(root)
    if reviewer_model:
        refuse(reviewer_class(reviewer_model) in allowed,
               f'reviewer model {reviewer_model} is not admitted by docs/verification.md (admitted: {", ".join(allowed)})')
        entry = {'model': reviewer_model, 'harness': 'codex' if reviewer_class(reviewer_model) in ('terra', 'sol') else 'claude-code'}
    else:
        entry = dict(profiles.role(session_profile(fdir), 'reviewer'))
        if reviewer_class(entry['model']) not in allowed:
            # The stricter Reviewer stands in until the rule admits the profile's one.
            print(f'note: the rule does not admit a {entry["model"]} Reviewer yet; using opus', file=sys.stderr)
            entry = {'model': 'opus', 'harness': 'claude-code'}
    model = entry['model']
    states = function_states(root, fdir, online=False)
    data = inventory(root)
    by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == data['target_build_id']}
    todo = [r for r, s in states.items() if s['state'] == 'confirmed' and not s.get('group')]
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
        if g['kind'] == 'review':
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
        g = {'name': name, 'kind': 'review', 'task_id': f'review-flow-{name}', 'build_id': data['target_build_id'],
             'functions': batch, 'created': utc(), 'source_revision': head, 'reviewer_model': model,
             'reviewer_harness': entry.get('harness', 'claude-code'),
             'components': comps, 'sampled': sample, 'pair': f'{name}-s' if sample else None,
             'dispatched': None, 'rerun': None, 'integrated': None}
        g['brief'] = write_review_brief(root, g, by_rva)
        save_group(fdir, g)
        if sample:
            s = dict(g, name=f'{name}-s', kind='sampling', task_id=f'review-flow-{name}-s', functions=sample,
                     reviewer_model='opus', reviewer_harness='claude-code', pair=name, sampled=sample, components={})
            s['brief'] = write_review_brief(root, s, by_rva)
            save_group(fdir, s)
            write_rerun_brief(root, g, by_rva)
        log_event(fdir, 'review-group', group=name, functions=batch, sampled=sample, reviewer_model=model)
        made.append(name)
    return made


def write_review_brief(root, g, by_rva):
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

Role: Reviewer (`docs/reviewer-runbook.md`; in Claude Code `.claude/agents/reviewer.md`), fresh
context, model {g['reviewer_model']}. Task id:
`{g['task_id']}`. Plan step 5 / fan-out review (AGENTS.md "Fan-out design", "Review").
{'This is the sampling safeguard second pass: an independent review of functions another Reviewer is reviewing in group ' + g['pair'] + '. Write `sampling_second_pass: yes`.' if sampling else 'Write `sampling_second_pass: no`.'}

Gates in force: G2 (you may read reconstructed source and, where listed, the private packs under
`.local/packs/`; never quote them). G3/G4/G5 are not needed: run no verifier, no Boat, no network.

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

## Steps

1. Run `python3 tools/review_packet.py --template {' '.join(g['functions'])}` and review every
   function with the checklist in `docs/reviewer-runbook.md`.
2. Do not open any other file under `.local/reviews/` or `.local/handoffs/`: this review must be
   independent.
3. Write your review document, exactly in the runbook's output format, with the title
   `# Review {g['task_id']}`, to `.local/reviews/{g['task_id']}.md`. Create it once; never edit or
   overwrite it afterwards. If that file already exists, stop and return `exists` in the table.
4. Return only the short table from the runbook ("Return message"), nothing else.

Do not push, post publicly, mark `matched`, edit any other file, or start further agents.
"""
    path = root / BRIEFS / f'{g["task_id"]}.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    return path.relative_to(root).as_posix()


def write_rerun_brief(root, g, by_rva):
    root = Path(root)
    units = sorted({unit_of(root, by_rva[r])[0] for r in g['sampled']})
    sample = {'seed': f'flow:{g["name"]}', 'reviewed': {u: [r for r in g['sampled'] if unit_of(root, by_rva[r])[0] == u]
                                                        for u in units}, 'label_only': {}}
    sdir = root / '.local/flow/rerun' / g['name']
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / 'sample.json').write_text(json.dumps(sample, indent=2) + '\n')
    text = f"""# Brief rerun-{g['name']}

Role: Engineer (or the routine orchestrator with a shell). Task: the sampling safeguard's
from-scratch comparator re-run for group {g['name']} ({len(g['sampled'])} functions), on a clean
checkout (docs/verification.md, Sampling safeguard). Gates: as recorded for confirm runs.

1. `git worktree add --detach .local/flow/rerun/{g['name']}/tree {g['source_revision']}`, then copy
   the unit files of these units from the main working tree if they are uncommitted:
   {', '.join(f'`{u}`' for u in units)}. Link `.local` into it as earlier re-runs did.
2. In that tree: `tools/verifier/confirm --list <file with the units' task dirs> --out .local/flow/rerun/{g['name']}/out`.
3. `python3 tools/sampling_packet.py --sample .local/flow/rerun/{g['name']}/sample.json --rerun .local/flow/rerun/{g['name']}/out/<build id> --compare-out .local/flow/rerun/{g['name']}/compare.txt`
4. `python3 tools/flow.py record-rerun {g['name']} --compare .local/flow/rerun/{g['name']}/compare.txt`
5. Remove the worktree. Return a table: function, AGREE/DISAGREE; and the compare file path.

Never edit the comparator, the records or the compare file to get AGREE; a DISAGREE is escalated.
Do not push, post publicly, mark `matched`, or start further agents.
"""
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


def redo_review(root, fdir, name):
    """A fresh Reviewer under a new task id after a review the parser refused (never edit the file)."""
    g = load_group(fdir, name)
    m = re.fullmatch(r'(.*?)(?:-r(\d+))?', g['task_id'])
    g['task_id'] = f'{m.group(1)}-r{int(m.group(2) or 1) + 1}'
    g['dispatched'] = None
    data = inventory(root)
    by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == data['target_build_id']}
    g['brief'] = write_review_brief(root, g, by_rva)
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
    if g['rerun']['not_agree']:
        return False, f'DISAGREE: re-run did not agree for {", ".join(g["rerun"]["not_agree"])}'
    return True, None


# ------------------------------------------------------------------ next actions

def next_actions(root, fdir, branch='main', now=None, online=True):
    """[(kind, text)] with kind 'stop', 'run', 'dispatch', 'wait' or 'done', in the order to do them."""
    import time
    now = time.time() if now is None else now
    root = Path(root)
    data = inventory(root)
    states = function_states(root, fdir, branch, online)
    gs = groups(fdir)
    stops, acts, waits = [], [], []
    profile = session_profile(fdir)
    s_entry = profiles.role(profile, 'strong')
    strong = (f'the strong role ({profiles.model_label(s_entry)}'
              + ('; Agent tool subagent_type engineer)' if s_entry['harness'] == 'claude-code' else '; a Codex session)'))
    for name, g in gs.items():
        if g.get('superseded_by'):
            continue
        status, blocks = read_review(root, g, data['functions'])
        if status.startswith('malformed'):
            acts.append(('run', f'python3 tools/flow.py redo-review {name}    # {g["task_id"]} {status}; never edit the saved review'))
            continue
        if g['kind'] == 'sampling':
            if status == 'missing' and not g.get('dispatched'):
                acts.append(dispatch_line(g))
            elif status == 'missing':
                waits.append(('wait', f'Reviewer for {name} ({g["task_id"]}) is running; its file appears at {REVIEWS}/{g["task_id"]}.md'))
            continue
        if g.get('sampled') and not g.get('rerun') and not g.get('rerun_dispatched'):
            acts.append(('dispatch', f'sampling re-run for {name}: {strong} with brief .local/briefs/rerun-{name}.md, '
                         f'or run its commands yourself. Then: python3 tools/flow.py dispatched {name} --rerun'))
        if status == 'missing':
            if not g.get('dispatched'):
                acts.append(dispatch_line(g))
            else:
                waits.append(('wait', f'Reviewer for {name} ({g["task_id"]}) is running; its file appears at {REVIEWS}/{g["task_id"]}.md'))
            continue
        esc = [(r, b.get('escalation_category')) for r, b in blocks.items() if b.get('verdict') == 'escalate']
        for rva, cat in esc:
            if cat in BLOCKING_ESCALATIONS:
                stops.append(('stop', f'ESCALATE to the maintainer: Reviewer escalated {rva} in {name} ({cat}); hold group {name}'))
        if any(c in BLOCKING_ESCALATIONS for _, c in esc):
            continue
        integ = g.get('integrated') or {}
        approved = [r for r, b in blocks.items() if b.get('verdict') == 'approve']
        if approved and integ.get('ci') != 'green':
            ok, problem = sampling_gate(root, fdir, g, data)
            if ok:
                acts.append(('run', f'python3 tools/flow.py integrate {name}'))
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
    if any(s['state'] == 'confirmed' and not s.get('group') for s in states.values()):
        acts.append(('run', 'python3 tools/flow.py review-group'))
    held = [r for r, s in states.items() if s.get('held') and not s.get('group')]
    if held and not any(e.get('event') == 'triage-brief' and e.get('held') for e in events(fdir)):
        acts.append(('run', f'python3 tools/flow.py brief triage --held    # {len(held)} function(s) held by an earlier '
                     f'reject; then start {strong} with the brief'))
    # Drafting.
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
    for unit, s in sorted(failed.items()):
        if s.get('profile') == 'cheap' and Path(unit).name not in full_queued:
            acts.append(('run', f'python3 tools/work_queue.py --queue-dir {QUEUES}/full add {unit}    # failed under cheap; '
                         'one try under full (refused when the unit has no attempts left: then brief triage)'))
        elif not any(e.get('event') == 'triage-brief' and unit in e.get('units', []) for e in events(fdir)):
            acts.append(('run', f'python3 tools/flow.py brief triage --units {unit}    # failed under {s.get("profile")}; '
                         f'then start {strong} with the brief'))
    by_profile = {}
    for qdir, profile, u, state, *_ in units:
        by_profile.setdefault(profile, {'open': 0, 'live': 0})
        by_profile[profile]['open'] += state == 'open'
        by_profile[profile]['live'] += state == 'claimed'
    for profile, c in sorted(by_profile.items()):
        if c['open'] and not c['live']:
            n = min(c['open'], 3)
            acts.append(('run', f'python3 tools/flow.py brief drafter --profile {profile} --count {n}    '
                         f'# {c["open"]} open unit(s); then dispatch one Drafter per brief it prints'))
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
    return out or [('done', 'nothing to do')]


def dispatch_line(g):
    entry = {'model': g['reviewer_model'], 'harness': g.get('reviewer_harness', 'claude-code'), 'effort': 'high'}
    prompt = (f'Read docs/reviewer-runbook.md and follow it. Your brief is {g["brief"]}.' if entry['harness'] == 'codex'
              else f'Read {g["brief"]} and follow it.')
    return ('dispatch', f'Reviewer for {g["name"]}: {start_worker(entry, prompt, "reviewer")}. '
            f'Then: python3 tools/flow.py dispatched {g["name"]}')


# ------------------------------------------------------------------ other briefs

def brief_drafter(root, fdir, profile, count=1):
    p = profiles.get(profile)
    paths = []
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M')
    for i in range(1, count + 1):
        label = f'{profile}-{stamp}-{i}'
        text = f"""# Brief drafter-{label}

Role: Drafter, profile `{profile}` ({profiles.model_label(p['roles']['drafter'])}). Gates: G2 for Claude models (sheets with FNV
text); Luna-class models read only the non-`.fnv.md` sheets. No Boat, no git, no network.

Read `docs/drafter-runbook.md` and follow it exactly. Your worker label is `<model>-{stamp}-{i}`
(for example `haiku-{stamp}-{i}`); pass `--profile {profile}` to `next`. Queue directory:
`{p['queue_dir']}` (pass `--queue-dir {p['queue_dir']}` to every work_queue.py call).
Documents: {', '.join(p['project_docs'])}. Stop on a function after {p['stuck_after']} counted
attempts with no change in its first mismatch; the unit budget is what `attempt` prints.

Return only the short table from the runbook ("Return message"); full details go to the queue.
Do not push, post publicly, mark `matched`, or start further agents.
"""
        path = Path(root) / BRIEFS / f'drafter-{label}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        paths.append(path.relative_to(root).as_posix())
    log_event(fdir, 'drafter-brief', profile=profile, briefs=paths)
    return paths


def brief_confirm(root, fdir):
    states = function_states(root, fdir, online=False)
    units = {}
    for rva, s in states.items():
        if s['state'] == 'drafted-pass' and s.get('unit'):
            units.setdefault(s['unit'], []).append(rva)
    stale = sorted(r for r, s in states.items() if s['state'] == 'confirm-stale')
    stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M')
    lst = Path(root) / '.local/flow' / f'confirm-{stamp}.txt'
    lst.parent.mkdir(parents=True, exist_ok=True)
    lst.write_text(''.join(f'{u}\n' for u in sorted(units)))
    text = f"""# Brief confirm-{stamp}

Role: strong role of the profile (Claude: Engineer), or the routine orchestrator with a shell when every step below is a
plain run. Reproduce the drafted passes on two runner hosts (docs/verification.md, Runner hosts).

Units with a passing function ({len(units)}), list file `{lst.relative_to(root).as_posix()}`:
""" + ''.join(f'- `{u}`: {", ".join(sorted(r, key=lambda x: int(x, 16)))}\n' for u, r in sorted(units.items())) + f"""
Records that no longer bind their unit ({len(stale)}): {', '.join(stale) or 'none'}.

1. For each unit, remove from its `task.json` only functions that did not pass (their near-miss
   files stay), as earlier confirm runs did. Every remaining function must be an inventory entry.
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

Role: strong role of the profile (Claude: Engineer, Opus; claude-low: Sol). Triage, fix and re-draft; you did not draft these functions (if you
did, say so and stop). Gates: as recorded; G2 for reading reviews and packs.

""" + '\n'.join(lines) + """

For a reject: fix the blocking ground named in the review, re-run `attempt`, re-confirm, and leave
the function for a fresh Reviewer (never the one who rejected it, never you). For an escalate
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

def run(cmd, root, step):
    """Run one integration step; raise FlowError with its output on failure."""
    r = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    if r.returncode:
        tail = '\n'.join((r.stderr.strip() + '\n' + r.stdout.strip()).strip().splitlines()[-15:])
        raise FlowError(f'STOPPED at {step} (exit {r.returncode}); nothing after it ran.\n{tail}')
    return r.stdout


def changed(root, paths):
    """The paths among `paths` that differ from HEAD (new, modified or deleted)."""
    if not paths:
        return []
    # Raw -z output: the status columns are positional, so the output must not be stripped.
    r = subprocess.run(['git', 'status', '--porcelain', '-z', '--no-renames', '--untracked-files=all', '--',
                        *sorted(set(paths))], cwd=root, capture_output=True, text=True)
    refuse(r.returncode == 0, f'git status failed: {r.stderr.strip()}')
    return sorted({entry[3:] for entry in r.stdout.split('\0') if len(entry) > 3})


def integration_tree(fdir, name):
    return Path(fdir) / 'integrate' / name / 'tree'


def remove_tree(root, tree):
    git(root, 'worktree', 'remove', '--force', str(tree), check=False)
    shutil.rmtree(tree, ignore_errors=True)
    git(root, 'worktree', 'prune', check=False)


def carry_into_tree(root, tree, approved, by_rva):
    """Copy, from the shared checkout into the integration tree, only what the approved functions
    need: their inventory entries, match records and translation-unit files. Other units, which a
    Drafter may still be editing, stay out of the commit and cannot block it."""
    files = set()
    for rva in approved:
        fn = by_rva[rva]
        refuse(fn.get('report'), f'{fn["id"]} names no match record in data/progress.json')
        files.add(fn['report'])
        files.update(json.loads((root / fn['report']).read_text())['source']['translation_unit'])
    for rel in sorted(files):
        src, dst = root / rel, tree / rel
        refuse(src.is_file(), f'{rel} is missing from the checkout')
        dst.parent.mkdir(parents=True, exist_ok=True)
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


def integrate(root, fdir, name, branch='main', push=True, ci_wait=600, python=sys.executable):
    """Accept the approve blocks of one group's saved review, check, commit, push and watch CI.

    The commit is built in its own worktree (under the flow dir) at origin's `branch`, never in the
    shared checkout: only the approved functions' entries, records and unit files are carried over,
    so other sessions' uncommitted work neither enters the commit nor blocks it. The shared checkout
    is left as it was; `flow.py sync` brings it up to origin afterwards.

    Refuses before any change when the review is missing, malformed or holds a blocking escalation,
    when the sampling gate is not met, or when the shared checkout holds commits origin lacks.
    Each later step stops at its first failure. Re-running resumes after the last finished step.
    """
    root = Path(root)
    g = load_group(fdir, name)
    refuse(g['kind'] == 'review', f'{name} is a sampling group; integrate its primary group {g.get("pair")}')
    data = inventory(root)
    status, blocks = read_review(root, g, data['functions'])
    refuse(status != 'missing', f'review {REVIEWS}/{g["task_id"]}.md is not saved yet; wait for the Reviewer')
    refuse(status == 'ok', f'review {g["task_id"]} {status}; run: python3 tools/flow.py redo-review {name}')
    esc = [r for r, b in blocks.items() if b.get('verdict') == 'escalate' and b.get('escalation_category') in BLOCKING_ESCALATIONS]
    refuse(not esc, f'blocking escalation for {", ".join(esc)}: escalate to the maintainer; group held')
    ok, problem = sampling_gate(root, fdir, g, data)
    refuse(ok, f'sampling gate: {problem}')
    approved = sorted((r for r, b in blocks.items() if b.get('verdict') == 'approve'), key=lambda r: int(r, 16))
    refuse(approved, 'the review has no approve block; nothing to integrate')
    integ = g.get('integrated') or {}
    review_file = str((root / REVIEWS / f'{g["task_id"]}.md').resolve())
    tree = integration_tree(fdir, name)
    if not integ.get('commit'):
        git(root, 'fetch', '--quiet', 'origin', branch)
        ahead = git(root, 'rev-list', '--count', f'origin/{branch}..HEAD')
        refuse(ahead == '0', f'the checkout holds {ahead} commit(s) origin/{branch} lacks; push or drop them first')
        remove_tree(root, tree)
        tree.parent.mkdir(parents=True, exist_ok=True)
        git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), f'origin/{branch}')
        by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == g['build_id']}
        carried = carry_into_tree(root, tree, approved, by_rva)
        data = inventory(tree)
        by_rva = {f'0x{fn["rva"]:x}': fn for fn in data['functions'] if fn['build_id'] == g['build_id']}
        done = all(by_rva[r]['status'] == 'matched' for r in approved)
        printed = list(carried)
        if not done:
            out = run([python, 'tools/accept_function.py', '--all-approved', '--review', review_file], tree, 'accept_function.py')
            take = False
            for line in out.splitlines():
                if line.startswith('changed files'):
                    take = True
                elif take and line.startswith('  '):
                    printed.append(line.strip().split('  ')[0])
                elif take:
                    take = False
        data = inventory(tree)
        paths = set(printed) | {'data/progress.json', 'reconstruction/INDEX.md', 'docs/progress.svg'}
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
        run([python, 'tools/check.py', '--staged'], tree, 'check.py --staged')
        accepted = len(approved)
        msg = (f'Accept {accepted} function(s) of review group {name}\n\n'
               f'Review {g["task_id"]}: {accepted} approve, '
               f'{sum(b.get("verdict") == "reject" for b in blocks.values())} reject; integrated by tools/flow.py.\n\n'
               'Co-Authored-By: Claude <noreply@anthropic.com>\n')
        git(tree, 'commit', '--quiet', '-m', msg)
        integ = {'commit': git(tree, 'rev-parse', 'HEAD'), 'files': files, 'accepted': accepted, 'checks': None,
                 'pushed': None, 'ci': None}
        g['integrated'] = integ
        save_group(fdir, g)
    if not integ.get('checks'):
        pre_push_checks(root, integ['commit'], python)
        integ['checks'] = utc()
        save_group(fdir, g)
    if not push:
        return g
    if not integ.get('pushed'):
        # Fast-forward only. When origin moved meanwhile the commit is dropped, so the next run
        # rebuilds it on the new origin and re-runs every check, rather than pushing a stale base.
        try:
            run(['git', 'push', 'origin', f'{integ["commit"]}:refs/heads/{branch}'], root, 'git push')
        except FlowError:
            g['integrated'] = None
            save_group(fdir, g)
            remove_tree(root, tree)
            raise
        integ['pushed'] = utc()
        save_group(fdir, g)
        log_event(fdir, 'integrated', group=name, accepted=integ['accepted'], commit=integ['commit'])
        remove_tree(root, tree)
    if integ.get('ci') != 'green':
        r = subprocess.run([python, 'tools/ci_status.py', '--commit', integ['commit'], '--wait', str(ci_wait)],
                           cwd=root, capture_output=True, text=True)
        integ['ci'] = {0: 'green', 1: 'red', 2: 'pending'}.get(r.returncode, 'unavailable')
        save_group(fdir, g)
        log_event(fdir, 'ci', group=name, result=integ['ci'], commit=integ['commit'])
        refuse(integ['ci'] == 'green', f'CI {integ["ci"].upper()} for {integ["commit"]}: '
               + ('fix main or report the cause to the maintainer before any further push.\n' if integ['ci'] == 'red'
                  else 'run integrate again later to re-check.\n') + r.stdout.strip())
    return g


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
        out = subprocess.run(['git', 'status', '--porcelain', '-z', '--no-renames', '--untracked-files=all', '--', *incoming],
                             cwd=root, capture_output=True, text=True).stdout
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


def pre_push_checks(root, commit, python):
    """AGENTS.md pre-push checks in a clean detached worktree, away from other sessions' files."""
    tmp = Path(tempfile.mkdtemp(prefix='flow-check-'))
    tree = tmp / 'tree'
    git(root, 'worktree', 'add', '--quiet', '--detach', str(tree), commit)
    try:
        run([python, 'tools/check.py'], tree, 'check.py (clean tree)')
        run([python, '-m', 'unittest', 'discover', '-s', 'tests'], tree, 'unit tests (clean tree)')
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


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--flow-dir')
    p.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    p.add_argument('--offline', action='store_true', help='do not read origin (pushed state unknown)')
    sub = p.add_subparsers(dest='cmd', required=True)
    s = sub.add_parser('session-start')
    s.add_argument('--profile', default=profiles.DEFAULT, choices=sorted(profiles.PROFILES))
    sub.add_parser('next-actions')
    s = sub.add_parser('status')
    s.add_argument('--functions', action='store_true')
    s = sub.add_parser('review-group')
    s.add_argument('--max', type=int, default=DEFAULT_GROUP_MAX)
    s.add_argument('--reviewer-model', help='override the profile\'s Reviewer (refused unless the rule admits it)')
    s = sub.add_parser('dispatched')
    s.add_argument('group')
    s.add_argument('--rerun', action='store_true', help='the sampling re-run, not the Reviewer, was started')
    s = sub.add_parser('redo-review')
    s.add_argument('group')
    s = sub.add_parser('record-rerun')
    s.add_argument('group')
    s.add_argument('--compare', required=True)
    s = sub.add_parser('integrate')
    s.add_argument('group')
    s.add_argument('--no-push', action='store_true', help='stop after the clean-tree checks')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('sync')
    s.add_argument('--branch', default='main')
    s = sub.add_parser('brief')
    s.add_argument('kind', choices=('drafter', 'confirm', 'triage', 'rerun', 'direction'))
    s.add_argument('--profile', default=profiles.DEFAULT, choices=sorted(profiles.PROFILES))
    s.add_argument('--count', type=int, default=1)
    s.add_argument('--group')
    s.add_argument('--units', nargs='+')
    s.add_argument('--held', action='store_true', help='functions held by a reject or escalate in an earlier review')
    s = sub.add_parser('baseline')
    s.add_argument('component', choices=('recipe', 'compiler', 'drafter_prompt', 'reviewer_prompt', 'reviewer_model',
                                          'acceptance_rule'))
    s.add_argument('value')
    s.add_argument('count', type=int)
    s = sub.add_parser('event')
    s.add_argument('kind', choices=('friction', 'direction-check'))
    s.add_argument('--note', default='')
    a = p.parse_args(argv)
    root = a.root
    fdir = flow_dir(root, a.flow_dir)
    try:
        if a.cmd == 'session-start':
            log_event(fdir, 'session-start', profile=a.profile)
            print(f'session started with profile {a.profile}; next: python3 tools/flow.py next-actions')
            print('\n'.join(profiles.show(a.profile)))
        elif a.cmd == 'next-actions':
            for i, (kind, text) in enumerate(next_actions(root, fdir, online=not a.offline), 1):
                print(f'{i}. [{kind}] {text}')
        elif a.cmd == 'status':
            lines, states = status_table(root, fdir, online=not a.offline)
            print('\n'.join(lines))
            if a.functions:
                for rva, s in sorted(states.items(), key=lambda kv: int(kv[0], 16)):
                    print(f'{rva}\t{s.get("state")}\t{s.get("group") or "-"}\t{s.get("profile") or "-"}\t{s.get("detail") or ""}')
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
        elif a.cmd == 'redo-review':
            g = redo_review(root, fdir, a.group)
            print(f'{a.group}: new task id {g["task_id"]}, brief {g["brief"]}; dispatch a fresh Reviewer with it')
        elif a.cmd == 'record-rerun':
            agree, other = record_rerun(root, fdir, a.group, a.compare)
            print(f'{a.group}: {len(agree)} AGREE' + (f'; NOT AGREE {", ".join(other)}: escalate' if other else ''))
            return 1 if other else 0
        elif a.cmd == 'integrate':
            g = integrate(root, fdir, a.group, a.branch, push=not a.no_push)
            integ = g['integrated']
            print(f'{a.group}: accepted {integ["accepted"]}, commit {integ["commit"]}, checks {integ["checks"]}, '
                  f'pushed {integ.get("pushed") or "no"}, CI {integ.get("ci") or "not checked"}')
            if integ.get('pushed'):
                print('next: python3 tools/flow.py sync    # bring the shared checkout up to origin')
        elif a.cmd == 'sync':
            dropped = sync(root, a.branch)
            print(f'checkout at origin/{a.branch}; {len(dropped)} identical local cop(ies) replaced by the integrated files')
        elif a.cmd == 'brief':
            if a.kind == 'drafter':
                for path in brief_drafter(root, fdir, a.profile, a.count):
                    print(path)
            elif a.kind == 'confirm':
                print(brief_confirm(root, fdir))
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
            (fdir / 'versions.json').write_text(json.dumps(v, indent=2, sort_keys=True) + '\n')
            log_event(fdir, 'baseline', component=a.component, value=a.value, count=a.count)
            print(f'baseline {a.component}={a.value}: {a.count}')
        elif a.cmd == 'event':
            log_event(fdir, a.kind, note=a.note)
            print(f'recorded {a.kind}')
    except (FlowError, wq.QueueError) as exc:
        print(f'flow: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
