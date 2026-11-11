"""Generate an offline-capable report from validated public metadata."""
from collections import Counter
from html import escape
import json
from string import Template
import subprocess
from check import ROOT, load


def plural(n, word, many=None):
    return f'{n:,} ' + (word if n == 1 else many or word + 's')


def phase_summary(data, counts, tasks):
    """The phase blurb, derived from the data so it cannot go stale when the data moves on."""
    if not data['target_build_id']:
        return 'No target build is pinned yet; work before that is tooling and method.'
    parts = [f'Target {data["target_build_id"]} is pinned.',
             f'{plural(len(data["functions"]), "function")} inventoried, '
             f'{plural(counts["matched"], "accepted byte match", "accepted byte matches")}.']
    upcoming = [item for state in ('active', 'blocked', 'planned') for item in data['work_items']
                if item['status'] == state]
    if upcoming:
        parts.append(f'{plural(len(upcoming), "open work item")}; '
                     f'{"in progress" if upcoming[0]["status"] == "active" else upcoming[0]["status"]}: '
                     f'{upcoming[0]["title"]}.')
    else:
        parts.append(f'All {plural(tasks["done"], "work item")} done; no open work item recorded.')
    return ' '.join(parts)


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
    # Derived from the validated inventory so the page cannot claim a gate state or total the data lacks.
    matched = counts['matched']
    matched_note = ('Matching gate implemented; no function accepted yet' if not matched else
                    'Each: comparator pass on 2+ hosts and a Reviewer approve')
    matched_bytes_note = 'No function accepted yet' if not matched else 'Sum of accepted functions\' sizes'
    phase_blurb = phase_summary(data, counts, tasks)
    scope_note = ('Scope remains unknown; no completion percentage' if data['scope']['functions'] is None
                  else f'{data["scope"]["functions"]:,} functions in measured scope')
    return Template((ROOT / 'site/index.html').read_text()).substitute(
        phase=escape(data['phase']), phase_blurb=escape(phase_blurb), updated=escape(data['updated_at']), revision=escape(revision),
        target=escape(data['target_build_id'] or 'Not pinned'), inventory=len(data['functions']),
        matched=matched, matched_note=escape(matched_note), matched_bytes_note=escape(matched_bytes_note),
        scope_note=escape(scope_note), matched_bytes=sum(fn['size'] for fn in data['functions'] if fn['status'] == 'matched'),
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
