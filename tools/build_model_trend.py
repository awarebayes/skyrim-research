"""Generate attribution and cumulative trends from public first-parent history."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COLORS = {'Claude': '#e5796b', 'GPT / Codex': '#58a6ff',
          'Scripts and tools': '#d29922', 'Not reported': '#6e7681'}


class GitBlobs:
    def __init__(self):
        self.proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        self.cache = {}

    def read(self, revision, path):
        key = (revision, path)
        if key not in self.cache:
            self.proc.stdin.write(f'{"" if revision == ":" else revision}:{path}\n'.encode())
            self.proc.stdin.flush()
            header = self.proc.stdout.readline().split()
            if len(header) == 3:
                self.cache[key] = self.proc.stdout.read(int(header[2]))
                self.proc.stdout.read(1)
            else:
                self.cache[key] = None
        return self.cache[key]

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def model_claim(claim):
    if not isinstance(claim, str) or not claim.strip():
        return 'Not reported', 'Not reported'
    claim = claim.strip()
    if re.search(r'\b(generated|generator|stamp(?:\.py)?)\b', claim, re.I):
        return 'Scripts and tools', 'Scripts and tools'
    claim = re.sub(r'\bcodex\s+(?=gpt)', '', claim, flags=re.I)
    models = re.findall(r'\b(?:claude[- .]*)?(?:haiku|sonnet|opus|fable)(?:[- .\d]+\d)?|\b(?:gpt[- .\d]*|codex[- .]*)?(?:luna|terra|sol)(?:[- .\d]+\d)?|\bgpt[- .\d]+\d+|\bclaude\b|\bcodex\b', claim, re.I)
    unique = list(dict.fromkeys(m.strip(' .-').lower() for m in models))
    if len(unique) != 1:
        return 'Not reported', 'Not reported'
    model = unique[0]
    family = 'Claude' if re.search(r'claude|haiku|sonnet|opus|fable', model) else 'GPT / Codex'
    return family, model


def header_claim(source):
    if not source:
        return None
    header = source.decode('utf-8', errors='replace').split('#include', 1)[0][:6000]
    match = re.search(r'(?im)\bdrafted by\s+([^\n]+)', header)
    return match.group(1) if match else None


def attribution(fn, report, generated, source):
    # Only explicit drafter fields count; reviewer and verifier fields are unrelated.
    for record in (fn, report or {}):
        for field in ('drafter_model', 'drafter_worker', 'drafter'):
            claim = record.get(field)
            if isinstance(claim, dict):
                claim = claim.get('model') or claim.get('worker')
            if isinstance(claim, str) and claim.strip():
                family, model = model_claim(claim)
                return family, model, 'Per-function record'
    if fn['id'] in generated:
        return 'Scripts and tools', 'Scripts and tools', 'Family manifest'
    claim = header_claim(source)
    if claim:
        family, model = model_claim(claim)
        return family, model, 'Unit header'
    return 'Not reported', 'Not reported', 'No attribution'


def tracked_paths(revision, pattern):
    cmd = ['git', 'ls-files', '--cached', '--', pattern] if revision == ':' else ['git', 'ls-tree', '-r', '--name-only', revision, '--', pattern]
    return subprocess.check_output(cmd, cwd=ROOT, text=True).splitlines()


def generated_members(revision, blobs):
    members = set()
    for path in tracked_paths(revision, 'data/generator-groups'):
        doc = json.loads(blobs.read(revision, path))
        members.update(f"{doc['build_id']}-0x{m['rva']:x}" for m in doc.get('members', []))
    for path in tracked_paths(revision, 'reports'):
        if '/family-batches/' not in path or not path.endswith('.json'):
            continue
        doc = json.loads(blobs.read(revision, path))
        members.update(doc.get('population', []))
    return members


def history(revision, blobs, pending=None):
    shallow = subprocess.check_output(['git', 'rev-parse', '--is-shallow-repository'], cwd=ROOT, text=True).strip()
    if shallow != 'false':
        raise ValueError('A full Git history is required; this checkout is shallow.')
    lines = subprocess.check_output(['git', 'log', '--first-parent', '--reverse', '--format=%H %cI',
                                     revision, '--', 'data/progress.json'], cwd=ROOT, text=True).splitlines()
    if pending:
        lines.append(f': {pending}')
    current, rows = {}, defaultdict(lambda: {'families': Counter(), 'models': Counter(), 'sources': Counter(),
                                             'functions': 0, 'revoked_bytes': 0, 'correction_bytes': 0})
    generated = generated_members(':' if pending else revision, blobs)
    for line in lines:
        commit, timestamp = line.split()
        day = datetime.fromisoformat(timestamp).astimezone(timezone.utc).date().isoformat()
        data = json.loads(blobs.read(commit, 'data/progress.json'))
        matched = {(fn['build_id'], fn['rva']): fn for fn in data['functions'] if fn['status'] == 'matched'}
        row = rows[day]
        for key in current.keys() - matched.keys():
            row['revoked_bytes'] += current[key][0]
            del current[key]
        for key, fn in matched.items():
            if key in current:
                row['correction_bytes'] += fn['size'] - current[key][0]
                current[key] = (fn['size'], *current[key][1:])
                continue
            raw = blobs.read(commit, fn.get('report', ''))
            report = json.loads(raw) if raw else {}
            unit = report.get('source', {}).get('compiled', '')
            source = blobs.read(commit, unit) if unit else None
            family, model, origin = attribution(fn, report, generated, source)
            current[key] = (fn['size'], family, model, origin)
            row['families'][family] += fn['size']
            row['models'][model] += fn['size']
            row['sources'][origin] += fn['size']
            row['functions'] += 1
        row['total_bytes'] = sum(item[0] for item in current.values())
        row['total_functions'] = len(current)
    return dict(sorted(rows.items())), current


def chart_limit(values):
    ordered = sorted(values)
    if len(ordered) >= 3 and ordered[-1] > max(ordered[-2] * 2, 1):
        return max(ordered[-2] * 1.25, ordered[-1] * .25)
    return max(ordered[-1], 1)


def render(rows):
    dates = list(rows)
    if not dates:
        return '<svg xmlns="http://www.w3.org/2000/svg"><text x="10" y="20">No accepted functions recorded.</text></svg>\n'
    totals = [sum(rows[d]['families'].values()) for d in dates]
    limit = chart_limit(totals)
    width = max(840, 100 + len(dates) * 65)
    step, bar = (width - 100) / len(dates), min(38, (width - 100) / len(dates) * .7)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} 340" role="img" aria-label="Gross accepted bytes per UTC day by model family">',
             f'<rect width="{width}" height="340" rx="12" fill="#0d1117"/>',
             '<g font-family="sans-serif"><text x="24" y="32" fill="#e6edf3" font-size="18">New accepted bytes by model family</text>',
             '<text x="24" y="52" fill="#9ba3ad" font-size="12">Gross acceptances · KiB · UTC</text>']
    for i, (family, color) in enumerate(COLORS.items()):
        parts += [f'<rect x="{24+i*195}" y="65" width="10" height="10" fill="{color}"/>',
                  f'<text x="{39+i*195}" y="75" fill="#c9d1d9" font-size="11">{escape(family)}</text>']
    for n in range(5):
        y = 250 - n * 37
        parts += [f'<path d="M65 {y}H{width-25}" stroke="#30363d"/>',
                  f'<text x="57" y="{y+4}" fill="#9ba3ad" font-size="11" text-anchor="end">{limit*n/4/1024:.1f}</text>']
    for i, date in enumerate(dates):
        x = 65 + i * step + (step - bar) / 2
        used = 0
        for family, color in COLORS.items():
            value = rows[date]['families'][family]
            visible = max(0, min(value, limit - used))
            if visible:
                h = 148 * visible / limit
                y = 250 - 148 * min(used + visible, limit) / limit
                parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar:.2f}" height="{h:.2f}" fill="{color}"/>')
            used += value
        if totals[i] > limit:
            parts += [f'<path d="M{x:.2f} 112 l{bar:.2f} -8 M{x:.2f} 118 l{bar:.2f} -8" stroke="#0d1117" stroke-width="3"/>',
                      f'<text x="{x+bar/2:.2f}" y="96" fill="#e6edf3" font-size="11" text-anchor="middle">{totals[i]/1024:.1f} KiB</text>']
        count = len([m for m in rows[date]['models'] if m not in ('Not reported', 'Scripts and tools')])
        parts += [f'<text x="{x+bar/2:.2f}" y="272" fill="#9ba3ad" font-size="11" text-anchor="middle">{date[5:]}</text>',
                  f'<text x="{x+bar/2:.2f}" y="296" fill="#c9d1d9" font-size="11" text-anchor="middle">{count}</text>']
    parts.append('<text x="24" y="296" fill="#9ba3ad" font-size="11">Models</text></g></svg>\n')
    return '\n'.join(parts)


def render_cumulative(rows):
    dates = list(rows)
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 320" role="img" aria-label="Cumulative matched bytes and functions">',
             '<rect width="840" height="320" rx="12" fill="#0d1117"/><g font-family="sans-serif">',
             '<text x="24" y="32" fill="#e6edf3" font-size="18">Accepted progress · UTC</text>']
    for idx, (key, title, color) in enumerate((('total_bytes', 'Bytes matched, cumulative', '#3fb950'), ('total_functions', 'Functions matched, cumulative', '#58a6ff'))):
        left = 55 + idx * 410
        values = [rows[d][key] for d in dates]
        maximum = max(values, default=0) or 1
        parts.append(f'<text x="{left}" y="65" fill="#e6edf3" font-size="14">{title}</text>')
        for n in range(5):
            y = 260 - n * 40
            parts.append(f'<path d="M{left} {y}h330" stroke="#30363d"/>')
        if dates:
            coords = [(left + i * 330 / max(1, len(dates)-1), 260 - 150 * v / maximum) for i, v in enumerate(values)]
            points = ' '.join(f'{x:.1f},{y:.1f}' for x, y in coords)
            x, y = coords[-1]
            parts += [f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="3"/>',
                      f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{color}"/>',
                      f'<text x="{x:.1f}" y="{y-10:.1f}" text-anchor="end" fill="{color}" font-size="13">{values[-1]:,}</text>']
            for i in sorted({0, len(dates)-1}):
                parts.append(f'<text x="{coords[i][0]:.1f}" y="284" fill="#9ba3ad" font-size="11" text-anchor="middle">{dates[i]}</text>')
    return '\n'.join(parts + ['</g></svg>\n'])


def summary(rows):
    result = Counter()
    for row in rows.values():
        result.update(row['families'])
    return result


def readme_table(rows):
    totals = summary(rows)
    lines = ['| Model family | Gross accepted bytes |', '| --- | ---: |']
    lines += [f'| {family} | {totals[family]:,} |' for family in COLORS]
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--pending-date', help='UTC commit timestamp for staged integration data')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', args.revision + '^{commit}'], cwd=ROOT, text=True).strip()
    blobs = GitBlobs()
    try:
        rows, current = history(revision, blobs, args.pending_date)
    finally:
        blobs.close()
    (ROOT / 'docs/model-trend.svg').write_text(render(rows))
    (ROOT / 'docs/progress-trend.svg').write_text(render_cumulative(rows))
    path = ROOT / 'README.md'
    text = path.read_text()
    start, end = '<!-- model-trend-totals -->', '<!-- /model-trend-totals -->'
    text = text.split(start)[0] + start + '\n' + readme_table(rows) + '\n' + end + text.split(end, 1)[1]
    path.write_text(text)
    print(f'Generated trends; {len(current)} current accepted functions.')


if __name__ == '__main__':
    main()
