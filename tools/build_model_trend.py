"""Render daily accepted bytes by source-header attribution from first-parent Git history.

Run from a full checkout: python3 tools/build_model_trend.py
Only committed data is used; the output is a dated snapshot and does not change match records.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
COLORS = {'Claude': '#e5796b', 'GPT / Codex': '#58a6ff', 'Other model': '#bc8cff',
          'Generated / tools': '#d29922', 'Mixed': '#dbb6ef', 'Unknown': '#6e7681'}


class GitBlobs:
    def __init__(self):
        self.proc = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def read(self, revision, path):
        self.proc.stdin.write(f'{revision}:{path}\n'.encode())
        self.proc.stdin.flush()
        header = self.proc.stdout.readline().split()
        if len(header) != 3:
            return None
        result = self.proc.stdout.read(int(header[2]))
        self.proc.stdout.read(1)
        return result

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()


def classify(source):
    """Conservative classification of a unit header, never reviewer or cost records."""
    if not source:
        return 'Unknown'
    # The attribution must occur in the introductory comments, not a function body.
    header = source.decode('utf-8', errors='replace').split('#include', 1)[0][:6000]
    match = re.search(r'(?im)\bdrafted by\s+([^\n]+)', header)
    if not match:
        return 'Unknown'
    claim = match.group(1).lower()
    if re.search(r'\b(generated|generator|stamp\.py)\b', claim):
        return 'Generated / tools'
    families = set()
    if re.search(r'\b(claude|haiku|sonnet|opus)\b', claim):
        families.add('Claude')
    if re.search(r'\b(gpt|codex|luna|terra|sol)\b', claim):
        families.add('GPT / Codex')
    if re.search(r'\b(gemini|qwen)\b', claim):
        families.add('Other model')
    if len(families) > 1 or (families and re.search(r'\bassisted by\b', claim)):
        return 'Mixed'
    return next(iter(families)) if families else 'Unknown'


def history(revision, blobs):
    shallow = subprocess.check_output(['git', 'rev-parse', '--is-shallow-repository'], cwd=ROOT, text=True).strip()
    if shallow != 'false':
        raise ValueError('A full Git history is required; this checkout is shallow.')
    lines = subprocess.check_output(['git', 'log', '--first-parent', '--reverse', '--format=%H %cI',
                                     revision, '--', 'data/progress.json'], cwd=ROOT, text=True).splitlines()
    current, rows = {}, defaultdict(Counter)
    for line in lines:
        commit, timestamp = line.split()
        day = datetime.fromisoformat(timestamp).astimezone(timezone.utc).date().isoformat()
        data = json.loads(blobs.read(commit, 'data/progress.json'))
        matched = {(fn['build_id'], fn['rva']): fn for fn in data['functions'] if fn['status'] == 'matched'}
        for key in current.keys() - matched.keys():
            rows[day]['revoked_bytes'] += current[key][0]
            del current[key]
        for key, fn in matched.items():
            if key in current:
                # Size corrections are changes to the accepted total, not new model output.
                rows[day]['correction_bytes'] += fn['size'] - current[key][0]
                current[key] = (fn['size'], current[key][1])
                continue
            report_raw = blobs.read(commit, fn.get('report', ''))
            try:
                unit = json.loads(report_raw)['source']['compiled']
                source = blobs.read(commit, unit)
            except (TypeError, KeyError, ValueError):
                source = None
            family = classify(source)
            current[key] = (fn['size'], family)
            rows[day][family] += fn['size']
    return dict(sorted(rows.items())), current


def render(rows, revision):
    dates = [d for d, row in rows.items() if any(row[k] for k in COLORS) or row['revoked_bytes'] or row['correction_bytes']]
    if not dates:
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 840 100"><text x="20" y="50">No accepted functions recorded.</text></svg>\n'
    sums = [sum(rows[d][k] for k in COLORS) for d in dates]
    maximum = max(sums) or 1
    width = max(840, 100 + len(dates) * 65)
    chart_w = width - 100
    step = chart_w / len(dates)
    bar = min(38, step * .7)
    height = 355
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             '<title id="title">Accepted bytes per day by source-header attribution</title>',
             f'<desc id="desc">Gross accepted bytes by UTC day, based on source header claims, through {escape(revision[:12])}. Generated, mixed, and unknown labels are separate.</desc>',
             f'<rect width="{width}" height="{height}" rx="12" fill="#0d1117"/>',
             '<g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif">',
             '<text x="24" y="32" fill="#e6edf3" font-size="18" font-weight="700">Accepted code by attribution</text>',
             '<text x="24" y="52" fill="#9ba3ad" font-size="12">Gross accepted KiB per UTC day · source-header claims</text>']
    for i, (label, color) in enumerate(COLORS.items()):
        x = 24 + (i % 3) * 210
        y = 75 + (i // 3) * 20
        parts += [f'<rect x="{x}" y="{y-9}" width="10" height="10" fill="{color}"/>',
                  f'<text x="{x+15}" y="{y}" fill="#c9d1d9" font-size="11">{escape(label)}</text>']
    for n in range(5):
        y = 285 - n * 42
        val = maximum * n / 4 / 1024
        parts += [f'<path d="M65 {y}H{width-25}" stroke="#30363d"/>',
                  f'<text x="57" y="{y+4}" fill="#9ba3ad" font-size="11" text-anchor="end">{val:.1f}</text>']
    for i, date in enumerate(dates):
        x = 65 + i * step + (step - bar) / 2
        y = 285.0
        for family, color in COLORS.items():
            value = rows[date][family]
            h = 168 * value / maximum
            if h:
                y -= h
                parts.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar:.2f}" height="{h:.2f}" fill="{color}"/>')
        parts.append(f'<text x="{x+bar/2:.2f}" y="308" fill="#9ba3ad" font-size="11" text-anchor="middle">{date[5:]}</text>')
    revoked = sum(row['revoked_bytes'] for row in rows.values())
    corrected = sum(row['correction_bytes'] for row in rows.values())
    parts.append(f'<text x="24" y="338" fill="#9ba3ad" font-size="11">'
                 f'Through {escape(revision[:12])} · revoked {revoked:,} bytes · size corrections {corrected:+,} bytes</text>')
    parts.append('</g></svg>\n')
    return '\n'.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revision', default='HEAD', help='last commit to include (default HEAD)')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/model-trend.svg')
    parser.add_argument('--json', type=Path, help='optional output of daily aggregate counts')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', 'rev-parse', '--verify', args.revision + '^{commit}'], cwd=ROOT, text=True).strip()
    blobs = GitBlobs()
    try:
        rows, current = history(revision, blobs)
    finally:
        blobs.close()
    args.output.write_text(render(rows, revision))
    if args.json:
        args.json.write_text(json.dumps({'revision': revision, 'days': rows}, indent=2) + '\n')
    print(f'Wrote {args.output}; {len(current)} current accepted functions; through {revision[:12]}')


if __name__ == '__main__':
    main()
