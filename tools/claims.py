#!/usr/bin/env python3
"""Shared GitHub batch claims and the project's public work queue.

Local settings: .local/claims-config.json may contain project_login, family_roots and
cluster_lists. Cluster lists are JSON objects with build_id and clusters, each with
members (RVA integers or hex strings). They become half-open ranges of function starts.
Only the publication builder below may turn local state into issue text.
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
import tempfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'awarebayes/skyrim-research'
MARKER = 'skyrim-claim-v1'
MANAGED = '<!-- skyrim-project-claim -->'
BODY_LIMIT = 60000
TTL = 600
CLAIM_LAPSE = timedelta(hours=24)
TOKEN = re.compile(r'(?<![A-Za-z0-9])0x([0-9a-fA-F]+)\b')
ENTRY = re.compile(r'0x([0-9a-fA-F]+)(?:-0x([0-9a-fA-F]+))?(?:\s+[^\r\n]+)?')


def rva(value):
    return int(value, 16) if isinstance(value, str) else int(value)


def stamp(value):
    try:
        return datetime.fromisoformat(str(value).replace('Z', '+00:00')).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def live(item, now=None):
    return (now or datetime.now(timezone.utc)) - stamp(item.get('updated_at')) < CLAIM_LAPSE


def parse_issue(issue):
    """One parser for legacy titles, PR titles and the versioned batch block."""
    title, body = issue.get('title') or '', issue.get('body') or ''
    block = re.search(r'```[^\n]*\n' + MARKER + r' ([A-Za-z0-9._-]+)\n(.*?)\n```', body, re.S)
    entries = []
    if block:
        build = block[1]
        for line in block[2].splitlines():
            match = ENTRY.fullmatch(line.strip())
            if not match:
                continue
            start = int(match[1], 16)
            end = int(match[2], 16) if match[2] else start + 1
            if end > start:
                entries.append((start, end))
    else:
        build_match = re.match(r'claim: ([A-Za-z0-9._-]+) ', title)
        build = build_match[1] if build_match else None
        entries = [(int(m[1], 16), int(m[1], 16) + 1) for m in TOKEN.finditer(title)]
    for a, b in issue.get('claim_takeovers', []):
        entries = [(x, min(y, a)) for x, y in entries if x < a and y > x] + [
            (max(x, b), y) for x, y in entries if y > b and y > x]
    assignees = [a['login'] for a in issue.get('assignees') or []]
    author = assignees[0] if assignees else (issue.get('user') or {}).get('login')
    return dict(number=issue['number'], title=title, body=body, build_id=build, entries=entries,
                author=author, assignees=assignees, updated_at=issue.get('updated_at'),
                url=issue.get('html_url'), pull_request='pull_request' in issue,
                created_at=issue.get('created_at'))


class ClaimIndex(dict):
    """Point lookup with ranges, without expanding potentially enormous intervals."""
    def __init__(self, items=(), build=None):
        super().__init__()
        self.records = [it for it in items if build is None or it.get('build_id') in (None, build)]
        self.ranges = []
        for it in self.records:
            for start, end in it['entries']:
                if end == start + 1:
                    self.setdefault(start, []).append(it)
                else:
                    self.ranges.append((start, end, it))

    def get(self, key, default=None):
        found = list(super().get(key, []))
        for start, end, it in self.ranges:
            if start <= key < end and it not in found:
                found.append(it)
        return found or default

    def overlaps(self, entries, me=None, active=True):
        return [it for it in self.records if (not active or live(it)) and
                (not me or me not in (it.get('assignees') or [it.get('author')])) and
                any(a < d and c < b for a, b in entries for c, d in it['entries'])]


def claimed(index, address, me=None):
    return [it for it in index.get(address, []) if live(it) and
            (not me or me not in (it.get('assignees') or [it.get('author')]))]


def load_json(path, default=None):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {} if default is None else default


def git_json(root, ref='HEAD'):
    p = subprocess.run(['git', 'show', f'{ref}:data/progress.json'], cwd=root, capture_output=True, text=True)
    if p.returncode:
        raise ValueError(f'cannot read tracked inventory at {ref}')
    return json.loads(p.stdout)


def activity(api, repo, raw):
    """Comments and linked PR activity also renew the containing claim."""
    updated = raw.get('updated_at')
    if not (raw.get('comments') or raw.get('body')):
        return updated
    for page in range(1, 101):
        events = api(f'repos/{repo}/issues/{raw["number"]}/timeline?per_page=100&page={page}')
        for event in events:
            for match in re.finditer(r'<!-- skyrim-claim-takeover-v1 (0x[0-9a-f]+)-(0x[0-9a-f]+) -->',
                                     event.get('body') or ''):
                a, b = int(match[1], 16), int(match[2], 16)
                if a < b:
                    raw.setdefault('claim_takeovers', []).append((a, b))
            dates = [event.get('updated_at'), event.get('created_at')]
            linked = (event.get('source') or {}).get('issue') or {}
            if 'pull_request' in linked:
                dates.append(linked.get('updated_at'))
            for value in filter(None, dates):
                if not updated or stamp(value) > stamp(updated):
                    updated = value
        if len(events) < 100:
            return updated
    raise RuntimeError('claim timeline pagination limit reached')


class GitHub:
    def __init__(self, root=ROOT, runner=None):
        self.root, self.runner = Path(root), runner or subprocess.run

    def run(self, *args, body=None):
        # Body text goes through stdin, never shell interpolation or a command-line argument.
        cmd = ['gh', *map(str, args)]
        if body is not None:
            if len(body) >= BODY_LIMIT:
                raise ValueError('refusing issue body at or above 60,000 characters')
            cmd += ['--body-file', '-']
        for attempt in range(2):
            p = self.runner(cmd, cwd=self.root, input=body, capture_output=True, text=True)
            if p.returncode == 0:
                return p.stdout.strip()
            if attempt == 0 and 'rate limit' in p.stderr.lower():
                continue
            raise RuntimeError('gh command failed: ' + ' '.join(map(str, args[:2])))

    def api(self, path):
        return json.loads(self.run('api', path))

    def user(self):
        return self.api('user')['login']

    def issues(self):
        result = []
        for page in range(1, 101):
            rows = self.api(f'repos/{REPO}/issues?state=open&per_page=100&page={page}')
            for raw in rows:
                it = parse_issue(raw)
                if it['entries']:
                    raw['updated_at'] = activity(self.api, REPO, raw)
                    result.append(parse_issue(raw))
            if len(rows) < 100:
                return result
        raise RuntimeError('open issue pagination limit reached')

    def label(self):
        self.run('label', 'create', 'claim', '--repo', REPO, '--color', '1d76db',
                 '--description', 'Function work claimed by a contributor or the project', '--force')

    def create(self, title, body, me):
        if len(body) >= BODY_LIMIT:
            raise ValueError('refusing issue body at or above 60,000 characters')
        self.label()
        url = self.run('issue', 'create', '--repo', REPO, '--title', title, '--assignee', me,
                       '--label', 'claim', body=body)
        return int(url.rstrip('/').split('/')[-1])

    def edit(self, number, title, body, me):
        self.run('issue', 'edit', number, '--repo', REPO, '--title', title, '--add-assignee', me, body=body)

    def comment(self, number, text):
        self.run('issue', 'comment', number, '--repo', REPO, body=text)

    def close(self, number, reason=None):
        self.run('issue', 'close', number, '--repo', REPO, '--comment', reason or
                 'All functions in this claim are accepted on origin/main. Closing the claim.')


def cached(root, refresh=False, gh=None, cache_dir=None):
    base = Path(cache_dir) if cache_dir else Path(root) / '.local'
    path = base / 'claims-cache.json'
    saved = load_json(path)
    if not refresh and time.time() - saved.get('fetched', 0) < TTL:
        return ClaimIndex(saved.get('items', [])), saved.get('login')
    try:
        gh = gh or GitHub(root)
        login, items = gh.user(), gh.issues()
    except (OSError, ValueError, RuntimeError):
        print('warning: GitHub claims unavailable; using stale claims cache', file=sys.stderr)
        return ClaimIndex(saved.get('items', [])), saved.get('login')
    try:
        base.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w', dir=base, prefix='claims-', suffix='.tmp', delete=False) as out:
            json.dump(dict(fetched=time.time(), login=login, items=items), out)
            temp = Path(out.name)
        temp.replace(path)
    except OSError:
        print('warning: could not save claims cache; using the fetched claims', file=sys.stderr)
    return ClaimIndex(items), login


def project_claims(root, refresh=False):
    root = Path(root)
    # Scratch queues outside a repository cannot refer to this project's claims.
    if not (root / 'data/progress.json').is_file():
        return ClaimIndex(), None
    index, login = cached(root, refresh)
    config = load_json(root / '.local/claims-config.json')
    build = load_json(root / 'data/progress.json').get('target_build_id')
    return ClaimIndex(index.records, build), config.get('project_login') or login


def scope(entries, public, build):
    names = sorted({f['name'].rsplit('::', 1)[0] for f in public['functions']
                    if f['build_id'] == build and f.get('name') and '::' in f['name'] and
                    any(a <= f['rva'] < b for a, b in entries)})
    # Names have already been read from the committed inventory, never from a queue or listing.
    names = [n for n in names if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_:<> ,*&~.-]*', n)]
    if names:
        text = ', '.join(names[:3]) + (f' and {len(names) - 3} more' if len(names) > 3 else '')
        if len(text) < 150:
            return text
    return f'0x{min(a for a, _ in entries):x}-0x{max(b for _, b in entries):x}'


def body(build, entries, public, me, total=None, done=0, managed=False):
    if not re.fullmatch(r'[A-Za-z0-9._-]+', build) or not re.fullmatch(r'[A-Za-z0-9-]+', me):
        raise ValueError('invalid build id or GitHub login')
    names = {f['rva']: f.get('name') for f in public['functions'] if f['build_id'] == build}
    lines = []
    for a, b in entries:
        if not 0 <= a < b <= 2**64:
            raise ValueError('invalid claim interval')
        text = f'0x{a:x}' if b == a + 1 else f'0x{a:x}-0x{b:x}'
        name = names.get(a) if b == a + 1 else None
        if name and re.fullmatch(r'[A-Za-z_~][A-Za-z0-9_:<> ,*&~().=+!\[\]/-]*', name):
            text += ' ' + name
        lines.append(text)
    total = len(entries) if total is None else total
    text = (f'Claimant: @{me}\nBuild: {build}\nScope: {scope(entries, public, build)}\n'
            f'Functions: {total}\nAccepted on origin/main: {done} / {total}\n\n'
            'This claim lapses after 24 hours without activity (a comment, an update or a linked pull request); anyone may then take it over.\n'
            'Only public metadata belongs in this issue.\n\n'
            + (MANAGED + '\n' if managed else '') + f'```text\n{MARKER} {build}\n' + '\n'.join(lines) + '\n```\n')
    if len(text) >= BODY_LIMIT:
        raise ValueError('refusing issue body at or above 60,000 characters')
    return text


def parts(build, entries, public, me, managed=False, counts=None):
    entries = sorted(set(entries))
    if not entries:
        return []
    def split(chunk):
        try:
            count = sum((counts or {}).get(e, 1) for e in chunk)
            body(build, chunk, public, me, count, managed=managed)
            return [chunk]
        except ValueError:
            if len(chunk) == 1:
                raise
            middle = len(chunk) // 2
            return split(chunk[:middle]) + split(chunk[middle:])
    chunks = split(entries)
    result = []
    for i, chunk in enumerate(chunks, 1):
        count = sum((counts or {}).get(e, 1) for e in chunk)
        title = f'claim: {build} {scope(chunk, public, build)} ({count} functions)'
        if len(chunks) > 1:
            title += f' (part {i} of {len(chunks)})'
        done = sum(f['status'] == 'matched' and f['build_id'] == build and
                   any(a <= f['rva'] < b for a, b in chunk) for f in public['functions'])
        result.append((title, body(build, chunk, public, me, count, done, managed), chunk))
    return result


def members(doc):
    """Extract addresses only; arbitrary other fields of private manifests never reach output."""
    values = doc.get('members', doc.get('functions', doc.get('first_members', [])))
    if isinstance(values, dict):
        values = list(values)
    result = set()
    for value in values:
        if isinstance(value, dict):
            value = value.get('rva')
        if isinstance(value, str) and re.search(r'(?:^|[- ])0x[0-9a-fA-F]+$', value):
            value = '0x' + value.rsplit('0x', 1)[1]
        if value is not None:
            result.add(rva(value))
    return result


def planned_family(root, path):
    doc = load_json(path)
    if doc.get('superseded_by'):
        return set()
    found = members(doc)
    import family_review as fr
    inventory = load_json(Path(root) / 'data/progress.json')
    for fn in inventory.get('functions', []):
        if not fn.get('report') or fn['build_id'] != doc.get('binding', {}).get('build_id'):
            continue
        record = load_json(Path(root) / fn['report'])
        if (record.get('origin') == doc.get('origin') and
                fr.in_ranges(record.get('family_parameters'), doc.get('parameter_ranges', {})) and
                fr.binding(fn, record) == doc['binding']):
            found.add(fn['rva'])
    return found


def collect(root, public, family_roots=(), cluster_lists=()):
    """Group queue, flow, planned family and cluster addresses; never publish their labels/paths."""
    import work_queue
    root = Path(root)
    build = public['target_build_id']
    accepted = {f['rva'] for f in public['functions'] if f['build_id'] == build and f['status'] == 'matched'}
    groups = []
    seen = set()
    config = load_json(root / '.local/claims-config.json')
    for family_root in [root, *config.get('family_roots', []), *family_roots]:
        base = Path(family_root)
        for p in sorted((base / 'reports' / build / 'families').glob('*.json')):
            addresses = planned_family(base, p) - accepted - seen
            if addresses:
                groups.append(([(a, a + 1) for a in sorted(addresses)], {}))
                seen |= addresses
    for file in [*config.get('cluster_lists', []), *cluster_lists]:
        doc = load_json(file)
        if doc.get('build_id') != build:
            raise ValueError('cluster list build does not match inventory')
        for cluster in doc.get('clusters', []):
            addresses = members(cluster)
            if not addresses or addresses <= accepted:
                continue
            intervals = [(rva(v['start']), rva(v['end'])) for v in cluster.get('ranges', [])]
            if not intervals:
                intervals = [(a, a + 1) for a in sorted(addresses)]
            if any(not 0 <= a < b <= 2**64 for a, b in intervals):
                raise ValueError('invalid static cluster range')
            if any(not any(a <= address < b for a, b in intervals) for address in addresses):
                raise ValueError('static ranges do not cover their member starts')
            counts = {e: sum(e[0] <= a < e[1] for a in addresses) for e in intervals}
            groups.append((intervals, counts))
            seen |= addresses
    for path in sorted((root / '.local/queue').glob('*/queue.tsv')):
        addresses = {rva(a) for unit in work_queue.read_queue(path.parent) for a in unit['functions']} - accepted - seen
        if addresses:
            groups.append(([(a, a + 1) for a in sorted(addresses)], {}))
            seen |= addresses
    # flow knows private report state and review groups, including functions not in a queue.
    import flow
    states = flow.function_states(root, flow.flow_dir(root), online=False)
    addresses = {rva(a) for a, state in states.items() if state.get('state') not in ('accepted', 'pushed')} - accepted - seen
    if addresses:
        groups.append(([(a, a + 1) for a in sorted(addresses)], {}))
    return build, groups


def active_entries(root, public, family_roots=()):
    """Find work still in the pipeline, without treating static cluster reservations as active."""
    root = Path(root)
    if not (root / 'data/progress.json').is_file():
        return []
    build = public['target_build_id']
    accepted = {f['rva'] for f in public['functions'] if f['build_id'] == build and f['status'] == 'matched'}
    config = load_json(root / '.local/claims-config.json')
    addresses = set()
    for family_root in [root, *config.get('family_roots', []), *family_roots]:
        base = Path(family_root)
        for path in (base / 'reports' / build / 'families').glob('*.json'):
            addresses |= planned_family(base, path)
    import flow
    states = flow.function_states(root, flow.flow_dir(root), online=False)
    active = {'queued', 'drafting', 'drafted-pass', 'confirmed', 'review-pending', 'approved'}
    addresses |= {rva(a) for a, state in states.items() if state.get('state') in active}
    return [(a, a + 1) for a in addresses - accepted]


def keep_alive(gh, issue, active, done, total):
    now = datetime.now(timezone.utc)
    age = now - stamp(issue.get('updated_at'))
    if (CLAIM_LAPSE / 2 < age < CLAIM_LAPSE and
            any(a < d and c < b for a, b in issue['entries'] for c, d in active)):
        gh.comment(issue['number'], f'Progress: {done} / {total} accepted; work remains active.')


def publish(root, gh, public, family_roots=(), cluster_lists=(), dry_run=False):
    me = load_json(Path(root) / '.local/claims-config.json').get('project_login') or gh.user()
    build, groups = collect(root, public, family_roots, cluster_lists)
    existing = gh.issues()
    active = active_entries(root, public, family_roots)
    index = ClaimIndex(existing, build)
    used, plans = set(), []
    for entries, counts in groups:
        # Whole groups are held on a range overlap; point-only groups can safely skip individual starts.
        conflicts = index.overlaps(entries, me)
        if conflicts:
            for it in conflicts:
                print(f'skip overlap with claim #{it["number"]} by {it["author"]}', file=sys.stderr)
            entries = [e for e in entries if not index.overlaps([e], me)]
        if not entries:
            continue
        for title, text, chunk in parts(build, entries, public, me, True, counts):
            prior = next((it for it in existing if it['number'] not in used and MANAGED in it.get('body', '')
                          and it.get('build_id') == build and it.get('author') == me and
                          any(a < d and c < b for a, b in chunk for c, d in it['entries'])), None)
            if prior:
                used.add(prior['number'])
                # Preserve already accepted members so sync can report and close the original scope.
                all_entries = sorted(set(prior['entries']) | set(chunk))
                total_match = re.search(r'^Functions: (\d+)$', prior['body'], re.M)
                additions = [e for e in chunk if not any(a <= e[0] and e[1] <= b for a, b in prior['entries'])]
                total = (int(total_match[1]) if total_match else len(prior['entries'])) + sum(counts.get(e, 1) for e in additions)
                accepted = {f['rva'] for f in public['functions'] if f['build_id'] == build and f['status'] == 'matched'}
                done = sum(any(a <= r < b for a, b in all_entries) for r in accepted)
                try:
                    text = body(build, all_entries, public, me, total, done, True)
                except ValueError:
                    # Keep a full issue's original scope and split its additions into new issues.
                    previous_total = int(total_match[1]) if total_match else len(prior['entries'])
                    old_done = sum(any(a <= r < b for a, b in prior['entries']) for r in accepted)
                    old_text = body(build, prior['entries'], public, me, previous_total, old_done, True)
                    action = 'unchanged' if prior['body'] == old_text else 'update'
                    old_title = f'claim: {build} {scope(prior["entries"], public, build)} ({previous_total} functions)'
                    plans.append((action, prior, old_title, old_text))
                    for extra_title, extra_body, _ in parts(build, additions, public, me, True, counts):
                        plans.append(('open', None, extra_title, extra_body))
                    continue
                title = f'claim: {build} {scope(all_entries, public, build)} ({total} functions)'
                suffix = re.search(r' \(part [0-9]+ of [0-9]+\)$', prior['title'])
                if suffix:
                    title += suffix[0]
            action = 'unchanged' if prior and prior['body'] == text and prior['title'] == title else ('update' if prior else 'open')
            plans.append((action, prior, title, text))
    if len(plans) > 15:
        raise ValueError('publish would exceed 15 issues; consolidate the local groups')
    for action, prior, title, text in plans:
        print(f'{action}: ' + (f'#{prior["number"]} ' if prior else '') + title)
        if dry_run:
            print(text)
        elif action == 'open':
            number = gh.create(title, text, me)
            print(f'https://github.com/{REPO}/issues/{number}')
            # Resolve a concurrent external claim using the same older-wins rule as contrib.
            parsed = parse_issue(dict(number=number, title=title, body=text))
            rivals = ClaimIndex(gh.issues(), build).overlaps(parsed['entries'], me)
            if any(it['number'] < number for it in rivals):
                gh.close(number, 'Withdrawn: an older overlapping claim won the publication race.')
                raise ValueError('an older overlapping claim won the publication race')
        elif action == 'update':
            gh.edit(prior['number'], title, text, me)
        elif action == 'unchanged':
            match = re.search(r'^Accepted on origin/main: (\d+) / (\d+)$', text, re.M)
            if match:
                keep_alive(gh, prior, active, int(match[1]), int(match[2]))
    return plans


def sync(root, gh=None):
    gh = gh or GitHub(root)
    public = git_json(root, 'origin/main')
    me = load_json(Path(root) / '.local/claims-config.json').get('project_login') or gh.user()
    active = active_entries(root, public)
    for it in gh.issues():
        if MARKER not in it.get('body', '') or it['author'] != me:
            continue
        functions = [f for f in public['functions'] if f['build_id'] == it.get('build_id') and
                     any(a <= f['rva'] < b for a, b in it['entries'])]
        done = sum(f['status'] == 'matched' for f in functions)
        match = re.search(r'^Functions: (\d+)$', it['body'], re.M)
        if not match:
            continue
        total = int(match[1])
        text = re.sub(r'^Accepted on origin/main: \d+ / \d+$', f'Accepted on origin/main: {done} / {total}', it['body'], flags=re.M)
        if text != it['body']:
            gh.edit(it['number'], it['title'], text, me)
        if done == total and total > 0:
            gh.close(it['number'])
        elif text == it['body'] and it.get('build_id') == public['target_build_id']:
            keep_alive(gh, it, active, done, total)
        print(f'#{it["number"]}: accepted {done}/{total}' + ('; closed' if done == total else ''))


def sync_safe(root):
    try:
        sync(root)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'warning: claim sync failed ({exc}); integration remains successful', file=sys.stderr)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--cache-dir', type=Path)
    sub = p.add_subparsers(dest='cmd', required=True)
    for cmd in ('list', 'check', 'publish', 'sync'):
        s = sub.add_parser(cmd)
        s.add_argument('--refresh', action='store_true')
        if cmd == 'check':
            s.add_argument('rvas', nargs='+')
        if cmd == 'publish':
            s.add_argument('--dry-run', action='store_true')
            s.add_argument('--family-root', type=Path, action='append', default=[])
            s.add_argument('--cluster-list', type=Path, action='append', default=[])
    a = p.parse_args(argv)
    try:
        gh = GitHub(a.root)
        if a.cmd == 'publish':
            publish(a.root, gh, git_json(a.root), a.family_root, a.cluster_list, a.dry_run)
        elif a.cmd == 'sync':
            sync(a.root, gh)
        else:
            index, _ = cached(a.root, a.refresh, gh, a.cache_dir)
            public = git_json(a.root)
            build = public['target_build_id']
            index = ClaimIndex(index.records, build)
            if a.cmd == 'check':
                for address in a.rvas:
                    hits = claimed(index, rva(address))
                    print(address + ': ' + (', '.join(f'#{it["number"]} @{it["author"]}' for it in hits) or 'unclaimed'))
            else:
                print('issue\tassignee\tcount\tdone\tage (days)')
                for it in index.records:
                    if not live(it):
                        continue
                    rows = [f for f in public['functions'] if f['build_id'] == build and
                            any(x <= f['rva'] < y for x, y in it['entries'])]
                    count = re.search(r'^Functions: (\d+)$', it['body'], re.M)
                    total = int(count[1]) if count else len(rows)
                    age = (datetime.now(timezone.utc) - stamp(it.get('created_at') or it['updated_at'])).days
                    print(f'{it["number"]}\t{it["author"]}\t{total}\t{sum(f["status"] == "matched" for f in rows)}\t{age}')
    except (OSError, ValueError, RuntimeError) as exc:
        print(f'claims: {exc}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
