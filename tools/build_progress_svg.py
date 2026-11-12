"""Render the README progress pictures, docs/progress.svg and docs/progress-map.svg, from tracked data only.

Inputs: data/progress.json, data/scope.json and the match records referenced by accepted
functions. The output is deterministic and self-contained: no timestamps, fonts, scripts or images.

The picture is drawn at the width GitHub shows a README image, so its text is never scaled down,
and no text is clipped to a shape: anything that needs a label gets a row or a column of its own.

progress.svg is the summary. progress-map.svg is the class map: one cell per function, grouped by
area and class, with every class name written out above its cells instead of fitted inside them.

    python3 tools/build_progress_svg.py            write both pictures
    python3 tools/build_progress_svg.py --check    fail if either picture is out of date
"""
import argparse
from collections import Counter
from html import escape
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'docs/progress.svg'
MAP_OUTPUT = ROOT / 'docs/progress-map.svg'
W, PAD = 840, 20
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
BG, TEXT, MUTED, TRACK = '#0d1117', '#e6edf3', '#9ba3ad', '#21262d'
GREEN, AMBER, GREY, DARK = '#3fb950', '#d29922', '#6e7681', '#30363d'
MIN_MARK = 2.0  # a nonzero count is never drawn thinner than this

# Scope categories are drawn as one segment per treatment, in this order.
GROUPS = (('in_scope', None, GREY),
          ('out_of_scope', 'Middleware and runtime', 'url(#hx)'),
          ('separate', 'Compiler-generated code', DARK))
TREATMENT_NOTE = {'out_of_scope': 'Out of scope', 'separate': 'Tracked separately'}


def fmt(v):
    return f'{v:.1f}'.rstrip('0').rstrip('.')


def thousands(n):
    return f'{n:,}'


def megabytes(n):
    return f'{n / 1e6:.1f} MB'


def pct(part, whole):
    return f'{100 * part / whole:.3f}%' if part else '0%'


def wrap(text, width):
    """Greedy word wrap by character count; the SVG has no font metrics to measure with."""
    lines, line = [], ''
    for word in text.split():
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f'{line} {word}'.strip()
    return lines + [line] if line else lines


def load(root):
    progress = json.loads((root / 'data/progress.json').read_text())
    scope = json.loads((root / 'data/scope.json').read_text())
    return progress, scope


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


def stats(progress, root):
    fns = progress['functions']
    counts = Counter(fn['status'] for fn in fns)
    matched = [fn for fn in fns if fn['status'] == 'matched']
    units = [unit_of(fn, root) for fn in matched]
    return dict(counts=counts, matched=len(matched), matched_bytes=sum(fn['size'] for fn in matched),
                named=sum(1 for fn in matched if fn.get('named') is True),
                tracked=len(fns), areas=Counter(a for a, _ in units), classes=Counter(c for _, c in units if c))


def scope_groups(scope):
    """[(title, fill, functions, bytes, estimated, member labels)] for the treatments that have code."""
    out = []
    for treatment, title, fill in GROUPS:
        cats = sorted((c for c in scope['categories'] if c['treatment'] == treatment), key=lambda c: -c['bytes'])
        if not cats:
            continue
        out.append(dict(treatment=treatment, title=title or cats[0]['label'], fill=fill,
                        functions=sum(c['functions'] for c in cats), bytes=sum(c['bytes'] for c in cats),
                        estimated=any(c['basis'] == 'estimated' for c in cats),
                        members=[c['label'] for c in cats] if title else []))
    return out


def scope_bar(scope, st, x, y, w):
    """One stacked bar of the executable's code by bytes, and under it a column of text per segment."""
    groups = scope_groups(scope)
    total = sum(g['bytes'] for g in groups)
    gap, bar_h = 2, 30
    out = [f'<text x="{x}" y="{y}" class="st">Code in the executable, by size</text>']
    by = y + 12
    sx = x
    usable = w - gap * (len(groups) - 1)
    for g in groups:
        sw = usable * g['bytes'] / total
        out.append(f'<rect x="{fmt(sx)}" y="{by}" width="{fmt(sw)}" height="{bar_h}" rx="3" fill="{g["fill"]}"/>')
        if g['treatment'] == 'in_scope':
            mx = sx
            in_progress = st['counts']['mapped'] + st['counts']['analyzed'] + st['counts']['reconstructed']
            for color, n in ((GREEN, st['counts']['matched']), (AMBER, in_progress)):
                if n:
                    mw = max(MIN_MARK, sw * n / g['functions'])
                    out.append(f'<rect x="{fmt(mx)}" y="{by}" width="{fmt(mw)}" height="{bar_h}" fill="{color}"/>')
                    mx += mw
        sx += sw + gap

    col_w = w / len(groups)
    ty = by + bar_h + 24
    lines = 0
    for i, g in enumerate(groups):
        cx = x + i * col_w
        est = ' est.' if g['estimated'] else ''
        out.append(f'<rect x="{fmt(cx)}" y="{ty - 11}" width="12" height="12" rx="2" fill="{g["fill"]}"/>')
        out.append(f'<text x="{fmt(cx + 19)}" y="{ty}" class="lb">{escape(g["title"])}</text>')
        out.append(f'<text x="{fmt(cx)}" y="{ty + 20}" class="rl">{thousands(g["functions"])} functions{est} · '
                   f'{megabytes(g["bytes"])}</text>')
        if g['treatment'] == 'in_scope':
            detail = [f'{thousands(st["counts"]["matched"])} accepted, {thousands(st["counts"]["mapped"])} mapped so far']
        else:
            detail = wrap(f'{TREATMENT_NOTE[g["treatment"]]}: ' + ', '.join(g['members']), int((col_w - 16) / 6.4))
        for j, line in enumerate(detail):
            out.append(f'<text x="{fmt(cx)}" y="{ty + 38 + j * 16}" class="fn">{escape(line)}</text>')
        lines = max(lines, len(detail))
    return ''.join(out), ty + 38 + (lines - 1) * 16


def bars(title, rows, x, y, w, total):
    """Horizontal bars: label, track with a coloured fill, count at the right edge. rows: (label, value, color)."""
    out = [f'<text x="{x}" y="{y}" class="st">{escape(title)}</text>']
    track_x, track_w = x + 170, w - 170 - 48
    for i, (label, value, color) in enumerate(rows):
        ry = y + 16 + i * 26
        out.append(f'<text x="{x}" y="{ry + 11}" class="rl">{escape(label)}</text>')
        out.append(f'<rect x="{track_x}" y="{ry}" width="{track_w}" height="12" rx="3" fill="{TRACK}"/>')
        if value:
            out.append(f'<rect x="{track_x}" y="{ry}" width="{fmt(max(MIN_MARK, track_w * value / total))}" height="12" rx="3" fill="{color}"/>')
        out.append(f'<text x="{x + w}" y="{ry + 11}" class="rl" text-anchor="end">{thousands(value)}</text>')
    return ''.join(out), y + 16 + len(rows) * 26 - 14


CELL = 4          # smallest cell pitch; a tile is never so small that its cells would be finer
TILE_H = 24       # height of a class tile: room for one label line
TILE_GAP = 2
NAME_PX = 7.4     # generous per-character width of the 12 px label font; nothing is clipped to a tile


def tile(key, x, y, w, h, n, done, label):
    """One class: a w*h rectangle divided into n cells, the first `done` of them green, with the label
    written over the cells. Cells are solid rectangles under a grid of background-coloured lines, so a
    tile costs a handful of elements whatever n is."""
    # Rows are chosen for near-square cells with few empty places in the last row.
    def cost(rows):
        cols = -(-n // rows)
        return 3 * (rows * cols - n) / n + abs(math.log((w / cols) / (h / rows)))
    rows = min(range(1, max(1, int(h // CELL)) + 1), key=cost)
    cols = -(-n // rows)
    cw, ch = w / cols, h / rows

    def fill(count, color):
        full, rest = divmod(count, cols)
        out = ''
        if full:
            out += f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(full * ch)}" fill="{color}"/>'
        if rest:
            out += f'<rect x="{fmt(x)}" y="{fmt(y + full * ch)}" width="{fmt(rest * cw)}" height="{fmt(ch)}" fill="{color}"/>'
        return out

    grid = (f'<pattern id="g{key}" x="{fmt(x)}" y="{fmt(y)}" width="{cw:.3f}" height="{ch:.3f}" patternUnits="userSpaceOnUse">'
            f'<path d="M{cw - 0.5:.3f} 0V{ch:.3f}M0 {ch - 0.5:.3f}H{cw:.3f}" stroke="{BG}" stroke-width="1"/></pattern>'
            f'<rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}" fill="url(#g{key})"/>')
    text = f'<text x="{fmt(x + 5)}" y="{fmt(y + 16.5)}" class="bl">{escape(label)}</text>'
    return fill(n, GREY) + fill(done, GREEN) + grid + text


def flow(items, width):
    """Pack (min_width, payload) items into rows left to right; rows that are mostly full are
    stretched to the full width so the tiles form a wall. Returns [[(x_offset, w, payload)]]."""
    rows, row, used = [], [], 0
    for min_w, payload in items:
        if row and used + TILE_GAP + min_w > width:
            rows.append(row)
            row, used = [], 0
        used += (TILE_GAP if row else 0) + min_w
        row.append((min_w, payload))
    if row:
        rows.append(row)
    out = []
    for row in rows:
        free = width - TILE_GAP * (len(row) - 1)
        total = sum(w for w, _ in row)
        scale = free / total if total >= 0.6 * free else 1
        placed, x = [], 0
        for w, payload in row:
            placed.append((x, w * scale, payload))
            x += w * scale + TILE_GAP
        out.append(placed)
    return out


def map_areas(scope, st):
    """In-scope areas with a known class, largest first and the catch-all area last; each class
    carries how many of its functions are accepted."""
    out = []
    for b in scope['areas']['blocks']:
        if b['treatment'] != 'in_scope' or not b['classes']:
            continue
        classes = [dict(name=c['name'], functions=c['functions'], done=min(st['classes'].get(c['name'], 0), c['functions']))
                   for c in sorted(b['classes'], key=lambda c: (-c['functions'], c['name'])) if c['functions'] > 0]
        out.append(dict(id=b['id'], label=b['label'], functions=b['functions'], classes=classes,
                        other=b.get('other_classes')))
    return sorted(out, key=lambda a: (a['id'] == 'other', -a['functions'], a['id']))


def render_map(root=ROOT):
    progress, scope = load(root)
    st = stats(progress, root)
    build = progress['target_build_id']
    areas = map_areas(scope, st)
    pop = scope['areas']['population']
    drawn = sum(a['functions'] for a in areas)
    shown = sum(c['done'] for a in areas for c in a['classes'])
    inner = W - 2 * PAD
    body = [f'<text x="{PAD}" y="42" class="h">Class map</text>',
            f'<text x="{W - PAD}" y="42" class="rl mu" text-anchor="end">Skyrim Special Edition · build {escape(build)}</text>',
            f'<text x="{PAD}" y="68" class="rl mu">One cell is one function, whatever its size. In-scope code with a known class: '
            f'{thousands(drawn)} of {thousands(pop["functions"])} functions (measured).</text>',
            f'<rect x="{PAD}" y="79" width="11" height="11" fill="{GREEN}"/>'
            f'<text x="{PAD + 18}" y="89" class="rl mu">accepted byte match; {shown} of the {st["matched"]} accepted functions are in a '
            f'class named here</text>']
    y = 128
    key = 0
    for a in areas:
        body.append(f'<text x="{PAD}" y="{y}" class="st">{escape(a["label"])}</text>'
                    f'<text x="{W - PAD}" y="{y}" class="rl mu" text-anchor="end">{thousands(a["functions"])} functions</text>')
        y += 10
        items = []
        for c in a['classes']:
            label = f'{c["name"]}  {c["done"]}/{thousands(c["functions"])}' if c['done'] else c['name']
            min_w = max(len(label) * NAME_PX + 10, c['functions'] * CELL * CELL / TILE_H)
            items.append((min(min_w, inner), (label, c)))
        for row in flow(items, inner):
            for dx, w, (label, c) in row:
                body.append(tile(key, PAD + dx, y, w, TILE_H, c['functions'], c['done'], label))
                key += 1
            y += TILE_H + TILE_GAP
        other = a['other']
        if other and other['functions'] > 0:
            h = max(TILE_H, CELL * -(-other['functions'] // (inner // CELL)))
            body.append(tile(key, PAD, y, inner, h, other['functions'], 0,
                             f'{thousands(other["classes"])} other classes  {thousands(other["functions"])}'))
            key += 1
            y += h + TILE_GAP
        y += 34

    not_classed = next((b['functions'] for b in scope['areas']['blocks'] if b['id'] == 'unattributed'), 0)
    out_of_scope = sum(b['functions'] for b in scope['areas']['blocks'] if b['treatment'] == 'out_of_scope')
    body.append(f'<text x="{PAD}" y="{y}" class="fn">Not drawn: {thousands(not_classed)} functions with no known class and '
                f'{thousands(out_of_scope)} in out-of-scope middleware · generated from tracked data · no game data</text>')
    H = y + PAD

    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Class map of the Skyrim Special Edition byte-matching reconstruction, build {escape(build)}">',
            f'<title>Class map, build {escape(build)}</title>',
            style(),
            f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>']
    return '\n'.join(head + body + ['</svg>']) + '\n'


def style():
    return ('<style>'
            f'text{{font-family:{FONT};fill:{TEXT};white-space:pre}}'
            '.h{font-size:26px;font-weight:600}.st{font-size:15px;font-weight:600}.lb{font-size:13px;font-weight:600}'
            f'.bl{{font-size:12px;font-weight:600;stroke:{BG};stroke-width:3px;paint-order:stroke;stroke-linejoin:round}}'
            f'.rl{{font-size:13px}}.fn{{font-size:12px;fill:{MUTED}}}.mu{{fill:{MUTED}}}</style>')


def render(root=ROOT):
    progress, scope = load(root)
    st = stats(progress, root)
    den = scope['denominators']['functions_excluding_funclets_and_thunks']
    build = progress['target_build_id']
    inner = W - 2 * PAD
    body = []

    body.append(f'<text x="{PAD}" y="42" class="h">{st["matched"]} accepted byte-matches</text>')
    body.append(f'<text x="{W - PAD}" y="42" class="rl mu" text-anchor="end">Skyrim Special Edition · build {escape(build)}</text>')
    mb = st['matched_bytes']
    body.append(f'<text x="{PAD}" y="68" class="rl mu">{st["matched"]} of {thousands(den["functions"])} functions = '
                f'{pct(st["matched"], den["functions"])} (measured: every function in the image except EH funclets and thunks)</text>')
    body.append(f'<text x="{PAD}" y="88" class="rl mu">{thousands(mb)} of {thousands(den["bytes"])} bytes = '
                f'{pct(mb, den["bytes"])} (measured, same denominator)</text>')

    svg, bottom = scope_bar(scope, st, PAD, 128, inner)
    body.append(svg)

    sy = bottom + 44
    col_w = (inner - 40) / 2
    counts = st['counts']
    status_rows = [('Accepted', counts['matched'], GREEN),
                   ('Accepted, names checked', st['named'], GREEN),
                   ('Mapped, no match yet', counts['mapped'], AMBER)]
    svg, b1 = bars(f'Functions by status ({st["tracked"]} tracked)', status_rows, PAD, sy, col_w, max(st['tracked'], 1))
    body.append(svg)
    area_dirs = sorted(p.name for p in (root / 'reconstruction').iterdir() if p.is_dir() and any(p.glob('*.cpp')))
    area_rows = sorted(((a, st['areas'].get(a, 0), GREEN) for a in area_dirs), key=lambda r: (-r[1], r[0]))
    svg, b2 = bars('Accepted functions by area', area_rows, PAD + col_w + 40, sy, col_w,
                   max(max(st['areas'].values(), default=1), 1))
    body.append(svg)

    fy = max(b1, b2) + 40
    body.append(f'<text x="{PAD}" y="{fy}" class="fn">est. = heuristic estimate · measured = counted on the pinned image · '
                'generated from data/progress.json and data/scope.json · no game data</text>')
    H = fy + PAD

    head = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" '
            f'aria-label="Progress of the Skyrim Special Edition byte-matching reconstruction, build {escape(build)}">',
            f'<title>Reconstruction progress, build {escape(build)}</title>',
            style(),
            '<defs><pattern id="hx" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<rect width="6" height="6" fill="{TRACK}"/><rect width="2" height="6" fill="#484f58"/></pattern></defs>',
            f'<rect width="{W}" height="{H}" rx="6" fill="{BG}"/>']
    return '\n'.join(head + body + ['</svg>']) + '\n'


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--check', action='store_true', help='fail when a picture is out of date')
    args = ap.parse_args(argv)
    pictures = ((OUTPUT, render()), (MAP_OUTPUT, render_map()))
    if args.check:
        stale = [path.relative_to(ROOT) for path, svg in pictures if not path.exists() or path.read_text() != svg]
        if stale:
            print(f'FAIL: {", ".join(map(str, stale))} out of date; run python3 tools/build_progress_svg.py', file=sys.stderr)
            return 1
        print('PASS: progress pictures are current')
        return 0
    for path, svg in pictures:
        path.write_text(svg)
        print(f'Wrote {path} ({len(svg.encode()):,} bytes)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
