"""Render docs/progress.svg, the README progress picture, from tracked data only.

Inputs: data/progress.json, data/scope.json, data/costs.json (optional), and the match records
referenced by accepted functions. The output is deterministic and self-contained: no timestamps,
fonts, scripts or images. Fine cell grids come from <pattern> fills, so the file stays small
regardless of how many functions a block stands for.

    python3 tools/build_progress_svg.py            write docs/progress.svg
    python3 tools/build_progress_svg.py --check    fail if docs/progress.svg is out of date
"""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/progress.svg'
W, BASE_H = 1000, 640
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
BG, TEXT, MUTED = '#0d1117', '#e6edf3', '#8b949e'
GREEN, AMBER, GREY, TRACK = '#2ea043', '#d29922', '#6e7681', '#6e7681'
MIN_MARK = 2.0       # progress too small to see is still drawn this tall, and the footnote says so
MIN_BLOCK_AREA = 500  # blocks below this many px^2 are listed in a footnote instead of drawn


def fmt(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def squarify(items, x, y, w, h):
    """Squarified treemap. items: (key, size) sorted descending; returns {key: (x, y, w, h)}."""
    total = sum(size for _, size in items)
    scale = w * h / total
    rest = [(k, size * scale) for k, size in items]
    out = {}

    def worst(row, side):
        s = sum(a for _, a in row)
        return max(max(side * side * a / (s * s), s * s / (side * side * a)) for _, a in row)

    while rest:
        side = min(w, h)
        row = [rest.pop(0)]
        while rest and worst(row + [rest[0]], side) <= worst(row, side):
            row.append(rest.pop(0))
        s = sum(a for _, a in row)
        if w >= h:  # lay the row as a column on the left
            col = s / h
            cy = y
            for k, a in row:
                out[k] = (x, cy, col, a / col)
                cy += a / col
            x, w = x + col, w - col
        else:
            rowh = s / w
            cx = x
            for k, a in row:
                out[k] = (cx, y, a / rowh, rowh)
                cx += a / rowh
            y, h = y + rowh, h - rowh
    return out


def thousands(n):
    return f'{n:,}'


def compact(n):
    return f'{n / 1e6:.2f}M' if n >= 1e6 else f'{n / 1e3:.0f}k' if n >= 1e4 else thousands(n)


def load(root):
    progress = json.loads((root / 'data/progress.json').read_text())
    scope = json.loads((root / 'data/scope.json').read_text())
    costs_file = root / 'data/costs.json'
    costs = json.loads(costs_file.read_text()) if costs_file.exists() else None
    return progress, scope, costs


def unit_of(fn, root):
    """(area, class) of an accepted function's unit, read from its match record."""
    try:
        record = json.loads((root / fn['report']).read_text())
        parts = record['source']['compiled'].split('/')
        if parts[0] == 'reconstruction' and len(parts) > 2:
            return parts[1], parts[-1].rsplit('.', 1)[0]
    except (KeyError, OSError, ValueError):
        pass
    return 'unknown', None


def area_of(fn, root):
    """Reconstruction area of an accepted function, read from its match record."""
    return unit_of(fn, root)[0]


def stats(progress, root):
    fns = progress['functions']
    counts = Counter(fn['status'] for fn in fns)
    matched = [fn for fn in fns if fn['status'] == 'matched']
    units = [unit_of(fn, root) for fn in matched]
    areas = Counter(a for a, _ in units)
    return dict(counts=counts, matched=len(matched), matched_bytes=sum(fn['size'] for fn in matched),
                named=sum(1 for fn in matched if fn.get('named') is True),
                tracked=len(fns), areas=areas, classes=Counter(c for _, c in units if c))


def defs():
    return (
        f'<pattern id="cg" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="{GREY}"/></pattern>'
        f'<pattern id="cn" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="{GREEN}"/></pattern>'
        f'<pattern id="ca" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="{AMBER}"/></pattern>'
        f'<pattern id="cd" width="12" height="12" patternUnits="userSpaceOnUse"><rect width="11" height="11" fill="#2ea043"/>'
        f'<rect x="11" width="1" height="12" fill="#12331b"/><rect y="11" width="12" height="1" fill="#12331b"/></pattern>'
        '<pattern id="hx" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
        '<rect width="7" height="7" fill="#11161d"/><rect width="2" height="7" fill="#262d37"/></pattern>'
        '<pattern id="hs" width="6" height="6" patternUnits="userSpaceOnUse">'
        '<rect width="6" height="6" fill="#11161d"/><rect width="6" height="1.5" fill="#2d3541"/></pattern>'
    )


def block(key, rect, label, sub, fill, mark=None, fraction=0.0, light=False):
    """One treemap block: fill pattern, optional progress from the top, label clipped to the block."""
    x, y, w, h = rect
    g = [f'<clipPath id="k-{key}"><rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}"/></clipPath>',
         f'<g clip-path="url(#k-{key})">',
         f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="{fill}"/>']
    if mark:
        top = y
        for pattern, share in mark:
            height = max(MIN_MARK, share * h)
            g.append(f'<rect x="{fmt(x)}" y="{fmt(top)}" width="{fmt(w)}" height="{fmt(height)}" fill="url(#{pattern})"/>')
            top += height
    g.append(f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="none" stroke="{BG}" stroke-width="1.5"/>')
    if w > 34 and h > 18:
        g.append(f'<text x="{fmt(x + 5)}" y="{fmt(y + 14)}" class="bl">{escape(label)}</text>')
        if sub and h > 32:
            g.append(f'<text x="{fmt(x + 5)}" y="{fmt(y + 27)}" class="bs">{escape(sub)}</text>')
    g.append('</g>')
    return ''.join(g)


def game_treemap(scope, stats_, x, y, w, h):
    cats = sorted(scope['categories'], key=lambda c: -c['bytes'])
    area_px = w * h
    total = sum(c['bytes'] for c in cats)
    drawn = [c for c in cats if c['bytes'] / total * area_px >= MIN_BLOCK_AREA]
    skipped = [c for c in cats if c not in drawn]
    layout = squarify([(c['id'], c['bytes']) for c in drawn], x, y, w, h)
    out = []
    game = next(c for c in cats if c['id'] == 'game')
    for c in drawn:
        est = ' est.' if c['basis'] == 'estimated' else ''
        sub = f'{thousands(c["functions"])} fns{est}, {compact(c["bytes"])} B'
        if c['id'] == 'game':
            denominator = game['functions']
            mark = [('cn', stats_['counts']['matched'] / denominator),
                    ('ca', (stats_['counts']['mapped'] + stats_['counts']['analyzed'] + stats_['counts']['reconstructed']) / denominator)]
            out.append(block(c['id'], layout[c['id']], c['label'], sub, 'url(#cg)', mark))
        else:
            fill = 'url(#hx)' if c['treatment'] == 'out_of_scope' else 'url(#hs)'
            out.append(block(c['id'], layout[c['id']], c['label'], sub, fill))
    return ''.join(out), skipped


def census_treemap(scope, x, y, w, h):
    blocks = sorted(scope['structure_census']['blocks'], key=lambda b: -b['functions'])
    layout = squarify([(b['id'], b['functions']) for b in blocks], x, y, w, h)
    return ''.join(block('s-' + b['id'], layout[b['id']], b['label'],
                         f'{thousands(b["functions"])} fns, {compact(b["bytes"])} B', 'url(#cd)') for b in blocks)


AREA_PANEL_H = 430


def area_panel(scope, stats_, x, y, w, h):
    """Nested treemap: one block per area (area = bytes), inside it one labelled block per large
    class plus one for the remaining classes. Marks show accepted functions of a class's unit."""
    areas = scope['areas']
    # Functions with no known class are stated in the heading rather than drawn: at their true
    # share they would leave the class blocks too small to label.
    blocks = sorted((b for b in areas['blocks'] if b['bytes'] > 0 and b['id'] != 'unattributed'),
                    key=lambda b: (-b['bytes'], b['id']))
    un = next((b for b in areas['blocks'] if b['id'] == 'unattributed'), {'functions': 0, 'bytes': 0})
    pop = areas['population']
    shown = sum(b['functions'] for b in blocks)
    out = [f'<text x="{x}" y="{fmt(y - 26)}" class="st">Ordinary code by area and class: {thousands(shown)} of '
           f'{thousands(pop["functions"])} functions have a known class</text>',
           f'<text x="{x}" y="{fmt(y - 10)}" class="hs">Area = bytes (measured). Class from the image RTTI vftables or an '
           f'approved id name; not drawn: {thousands(un["functions"])} functions ({compact(un["bytes"])} B) with no class '
           f'known. {thousands(areas["classes_passing_checks"]["value"])} of '
           f'{thousands(areas["classes_with_primary_vftable"]["value"])} vftable classes pass the community checks.</text>']
    layout = squarify([(b['id'], b['bytes']) for b in blocks], x, y, w, h)
    for b in blocks:
        bx, by, bw, bh = layout[b['id']]
        fill = 'url(#hx)' if b['treatment'] == 'out_of_scope' else ('url(#hs)' if b['id'] == 'unattributed' else 'url(#cg)')
        out.append(f'<rect x="{fmt(bx)}" y="{fmt(by)}" width="{fmt(bw)}" height="{fmt(bh)}" fill="#161b22" '
                   f'stroke="{BG}" stroke-width="2"/>')
        head = 15 if bh > 40 and bw > 60 else 0
        if head:
            out.append(f'<clipPath id="ah-{b["id"]}"><rect x="{fmt(bx)}" y="{fmt(by)}" width="{fmt(bw)}" height="{head}"/>'
                       f'</clipPath><text x="{fmt(bx + 4)}" y="{fmt(by + 11)}" class="bs" clip-path="url(#ah-{b["id"]})">'
                       f'{escape(b["label"])} · {thousands(b["functions"])} fns · {compact(b["bytes"])} B</text>')
        items = [(c['name'], c) for c in b['classes'] if c['bytes'] > 0]
        if b.get('other_classes') and b['other_classes']['bytes'] > 0:
            oc = b['other_classes']
            items.append((f'{thousands(oc["classes"])} other classes', oc))
        if not items:
            est = b.get('adjacent_estimate')
            items = [('no class known', b)]
            if est:
                items = [('no class known', {'functions': b['functions'] - est['functions'],
                                             'bytes': b['bytes'] - est['bytes']}),
                         ('between two methods of one class (est.)', est)]
        items = [(k, v) for k, v in items if v['bytes'] > 0]
        inner = (bx + 1, by + head + 1, bw - 2, bh - head - 2)
        if inner[2] <= 2 or inner[3] <= 2 or not items:
            continue
        sub = squarify([(str(i), v['bytes']) for i, (_, v) in enumerate(items)], *inner)
        for i, (name, v) in enumerate(items):
            done = stats_['classes'].get(name, 0) if v.get('functions') else 0
            mark = [('cn', done / v['functions'])] if done else None
            out.append(block(f'a-{b["id"]}-{i}', sub[str(i)], name,
                             f'{thousands(v["functions"])} fns, {compact(v["bytes"])} B', fill, mark))
    return ''.join(out)


def pct(part, whole):
    return f'{100 * part / whole:.3f}%' if part else '0%'


def bars(title, rows, x, y, w, total=None, colors=None):
    """Horizontal bars in the reference's style: label, grey track with a coloured fill, count at the right edge."""
    out = [f'<text x="{x}" y="{y}" class="st">{escape(title)}</text>']
    top = max([v for _, v, _ in rows] + [1]) if total is None else total
    track_x, track_w = x + 138, w - 138 - 70
    for i, (label, value, shown) in enumerate(rows):
        ry = y + 10 + i * 20
        fill = (colors or {}).get(label, AMBER)
        out.append(f'<text x="{x}" y="{ry + 12}" class="rl">{escape(label)}</text>')
        out.append(f'<rect x="{track_x}" y="{ry}" width="{track_w}" height="14" fill="{TRACK}"/>')
        if value:
            out.append(f'<rect x="{track_x}" y="{ry}" width="{fmt(max(2, track_w * value / top))}" height="14" fill="{fill}"/>')
        out.append(f'<text x="{x + w}" y="{ry + 12}" class="rl" text-anchor="end">{escape(shown)}</text>')
    return ''.join(out)


def cost_rows(costs):
    if not costs or not costs.get('records'):
        return [], 0.0, 0
    out_tokens, boat, n = Counter(), 0.0, 0
    for r in costs['records']:
        out_tokens[r['role']] += r['tokens']['output']
        boat += r.get('boat_seconds') or 0
        n += 1
    rows = [(role, v, compact(v)) for role, v in sorted(out_tokens.items(), key=lambda kv: (-kv[1], kv[0]))]
    return rows, boat / 3600, n


def render(root=ROOT):
    progress, scope, costs = load(root)
    st = stats(progress, root)
    den = scope['denominators']['functions_excluding_funclets_and_thunks']
    census = scope['structure_census']['primary_unwind_entries']
    build = progress['target_build_id']
    panel = AREA_PANEL_H if scope.get('areas') else 0
    H = BASE_H + panel
    LX, LW, RX, RW = 8, 585, 605, 387
    TY, TH = 76, 270

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
             f'aria-label="Progress of the Skyrim Special Edition byte-matching reconstruction, build {escape(build)}">',
             f'<title>Reconstruction progress, build {escape(build)}</title>',
             '<style>'
             f'text{{font-family:{FONT};fill:{TEXT}}}'
             '.h{font-size:17px}.hs{font-size:11px;fill:#8b949e}.st{font-size:15px}.rl{font-size:12.5px}'
             '.bl{font-size:12px;font-weight:600;stroke:#0d1117;stroke-width:2.5px;paint-order:stroke;fill:#fff}'
             '.bs{font-size:10px;stroke:#0d1117;stroke-width:2.5px;paint-order:stroke;fill:#e6edf3}'
             '.fn{font-size:10.5px;fill:#8b949e}</style>',
             f'<defs>{defs()}</defs>',
             f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    mb = st['matched_bytes']
    parts.append(f'<text x="{LX}" y="22" class="h">Game code: {st["matched"]} accepted byte-matches</text>')
    parts.append(f'<text x="{LX}" y="40" class="hs">{st["matched"]} of {thousands(den["functions"])} functions = '
                 f'{pct(st["matched"], den["functions"])} (measured: image functions excl. EH funclets, thunks)</text>')
    parts.append(f'<text x="{LX}" y="54" class="hs">{thousands(mb)} of {thousands(den["bytes"])} bytes = '
                 f'{pct(mb, den["bytes"])} (measured, same denominator; includes middleware)</text>')
    game = next(c for c in scope['categories'] if c['id'] == 'game')
    parts.append(f'<text x="{LX}" y="68" class="hs">Ordinary game code: {thousands(game["functions"])} functions est.; '
                 f'no percentage for an estimate</text>')

    tm, skipped = game_treemap(scope, st, LX, TY, LW, TH)
    parts.append(tm)

    parts.append(f'<text x="{RX}" y="22" class="h">Unwind data decoded: {thousands(census["decoded"])} of {thousands(census["value"])}</text>')
    parts.append(f'<text x="{RX}" y="40" class="hs">primary unwind entries the comparator decodes (measured census)</text>')
    parts.append(f'<text x="{RX}" y="54" class="hs">Decodable by the comparator, not matched. Area = functions.</text>')
    jt = scope['structure_census']['jump_table_candidates']
    parts.append(f'<text x="{RX}" y="68" class="hs">Jump-table candidates: {thousands(jt["value"])} est., inside the blocks</text>')
    parts.append(census_treemap(scope, RX, TY, RW, TH))

    # legend
    ly = TY + TH + 14
    legend = [('url(#cn)', 'accepted'), ('url(#ca)', 'in progress (mapped)'), ('url(#cg)', 'not started'),
              ('url(#hx)', 'out of scope'), ('url(#hs)', 'tracked separately')]
    lx = LX
    for fill, text in legend:
        parts.append(f'<rect x="{lx}" y="{ly - 9}" width="12" height="10" fill="{fill}" stroke="#30363d" stroke-width="0.5"/>'
                     f'<text x="{lx + 17}" y="{ly}" class="fn">{text}</text>')
        lx += 17 + len(text) * 5.6 + 14

    # lower sections
    sy = ly + 30
    counts = st['counts']
    review_pending = 0
    status_rows = [('Accepted (matched)', counts['matched'], thousands(counts['matched'])),
                   ('Names checked', st['named'], thousands(st['named'])),
                   ('Awaiting review', review_pending, thousands(review_pending)),
                   ('Mapped, no match yet', counts['mapped'], thousands(counts['mapped']))]
    parts.append(bars(f'Functions by status ({st["tracked"]} tracked)', status_rows, LX, sy, LW, total=max(st['tracked'], 1),
                      colors={'Accepted (matched)': GREEN}))
    area_dirs = sorted(p.name for p in (root / 'reconstruction').iterdir() if p.is_dir() and any(p.glob('*.cpp')))
    area_rows = [(a, st['areas'].get(a, 0), thousands(st['areas'].get(a, 0))) for a in area_dirs]
    parts.append(bars('Units by area (functions accepted)', area_rows, LX, sy + 100, LW, total=max(max(st['areas'].values(), default=1), 1),
                      colors={a: GREEN for a, _, _ in area_rows}))

    rows, boat_h, n = cost_rows(costs)
    if rows:
        parts.append(bars(f'Cost so far: output tokens by role ({n} runs)', rows, RX, sy, RW, total=max(v for _, v, _ in rows)))
        by = sy + 10 + len(rows) * 20 + 14
        parts.append(f'<text x="{RX}" y="{by + 12}" class="rl">Boat compute</text>'
                     f'<text x="{RX + RW}" y="{by + 12}" class="rl" text-anchor="end">{boat_h:.2f} h</text>')
        parts.append(f'<text x="{RX}" y="{by + 30}" class="fn">Counts from the cost ledger; shares of shared work are partly estimated.</text>')
    else:
        parts.append(f'<text x="{RX}" y="{sy}" class="st">Cost so far</text><text x="{RX}" y="{sy + 20}" class="rl">No cost ledger recorded.</text>')

    if panel:
        parts.append(area_panel(scope, st, LX, BASE_H + 20, W - 2 * LX, panel - 75))
    skipped_text = ', '.join(c['label'] + ' ' + thousands(c['functions']) for c in skipped)
    notes = ['Marks show the share of a block from the top; progress under 2 px is drawn 2 px tall.',
             f'est. = estimated by a heuristic; measured = counted on the pinned image. Not drawn (too small): {skipped_text} functions.']
    for i, line in enumerate(notes):
        parts.append(f'<text x="{LX}" y="{H - 36 + i * 13}" class="fn">{escape(line)}</text>')
    parts.append(f'<text x="{LX}" y="{H - 10}" class="fn">Build {escape(build)} · generated from data/progress.json, '
                 'data/scope.json, data/costs.json · no game data</text>')
    parts.append('</svg>')
    return '\n'.join(parts) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='fail when docs/progress.svg is out of date')
    args = ap.parse_args(argv)
    svg = render()
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != svg:
            print('FAIL: docs/progress.svg is out of date; run python3 tools/build_progress_svg.py', file=sys.stderr)
            return 1
        print('PASS: docs/progress.svg is current')
        return 0
    OUTPUT.write_text(svg)
    print(f'Wrote {OUTPUT} ({len(svg.encode()):,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
