"""Generate an offline-capable report from validated public metadata."""
from collections import Counter
from html import escape
import json
from string import Template
import subprocess
from check import ROOT, load


def render(data, revision):
    counts = Counter(fn['status'] for fn in data['functions'])
    pipeline = ''.join(f'<li><span>{label}</span><strong>{counts[state]:,}</strong></li>' for state, label in
                       [('mapped', 'Mapped'), ('analyzed', 'Analyzed'), ('reconstructed', 'Reconstructed'), ('matched', 'Byte matched')])
    items = []
    for item in data['work_items']:
        title = escape(item['title'])
        if item['issue_url']:
            title = f'<a href="{escape(item["issue_url"], quote=True)}">{title} ↗</a>'
        items.append(f'<article class="work" data-state="{item["status"]}"><div class="work-top">'
                     f'<span class="tag {item["status"]}">{escape(item["status"])}</span>'
                     f'<span class="owner">{escape(item["owner"])}</span></div><h3>{title}</h3>'
                     f'<p>{escape(item["acceptance"])}</p></article>')
    events = ''.join(f'<li><time>{escape(e["date"])}</time><div><h3>{escape(e["title"])}</h3>'
                     f'<p>{escape(e["detail"])}</p></div></li>' for e in reversed(data['milestones']))
    tasks = Counter(item['status'] for item in data['work_items'])
    return Template((ROOT / 'site/index.html').read_text()).substitute(
        phase=escape(data['phase']), updated=escape(data['updated_at']), revision=escape(revision),
        target=escape(data['target_build_id'] or 'Not pinned'), inventory=len(data['functions']),
        matched=counts['matched'], matched_bytes=sum(fn['size'] for fn in data['functions'] if fn['status'] == 'matched'),
        scope=escape(data['scope']['notes']), pipeline=pipeline, work=''.join(items), events=events,
        planned=tasks['planned'], active=tasks['active'], blocked=tasks['blocked'], done=tasks['done'])


def main():
    data = load()
    try:
        revision = subprocess.check_output(['git', 'rev-parse', '--short=12', 'HEAD'], cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
        if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
            revision += ' (local changes)'
    except subprocess.CalledProcessError:
        revision = 'uncommitted bootstrap'
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    (output / 'index.html').write_text(render(data, revision))
    (output / 'style.css').write_text((ROOT / 'site/style.css').read_text())
    (output / 'progress.json').write_text(json.dumps(data, indent=2) + '\n')
    (output / '.nojekyll').touch()
    print(f'Built {output / "index.html"}; source {revision}; no game data included.')


if __name__ == '__main__':
    main()
