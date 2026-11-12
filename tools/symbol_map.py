"""Version history of a public symbol map, and the one sanctioned way to change the map.

A match record pins the SHA-256 of the symbol map its runs used. Adding unrelated entries must not
invalidate it; changing or removing an entry it could have used must. The history file beside
the map (`symbol-map.history.json`) lists map versions as name sets, each with the SHA-256 the
map file had then:

    {"schema": 1, "map": "reports/<build id>/symbol-map.json",
     "versions": [{"sha256": "...", "base": null, "added": [names]},
                  {"sha256": "...", "base": 0, "added": [names]}, ...]}

A version's names are its base version's names plus `added`. Nothing in the history is trusted:
the old map file is rebuilt from the *current* map restricted to the version's names (same key
order, entries, fold groups and provenance entries) and serialized canonically, and that rebuild
must hash to the version's SHA-256. A match therefore proves, by SHA-256 collision resistance,
that every entry of that version is present and identical now, whatever the history claims. A
version that no longer rebuilds is a failure of the whole history unless it is marked
`superseded` (written only by this tool when it changes or removes an entry), and a record pinned
to a superseded or unknown version is stale.

A pass also depended on what the old map did *not* contain: the comparator rejects a map entry
that aliases or overlaps the function or a funclet, an `__ImageBase` other than 0, a `_tls_index`
other than the TLS directory's slot, a thread-local entry outside the image's TLS template (and
any thread-local entry at all for an image without a usable TLS directory), and treats EH handler
names specially. `carry_forward_problem` refuses to carry a record across additions that could
have changed its result, including an addition at or in a funclet range the reports give (and any
addition at all for a function with funclets whose reports give no consistent ranges).

Entries are `{"rva", "size"}` or `{"kind": "thread-local", "tls_offset", "size"}`, the second
written in that key order. Overlap and ordering rules compare RVA entries with RVA entries and
thread-local entries with thread-local entries (by TLS-template offset), never across.

Usage (paths relative to the repository root):

    python3 tools/symbol_map.py verify --map reports/<build id>/symbol-map.json
    python3 tools/symbol_map.py add --map reports/<build id>/symbol-map.json --from NEW.json \\
        [--history NEW.history.json] [--remove NAME ...] [--allow-change] [--dry-run]

`add` takes entries (and their provenance entries and new fold groups) from a symbol-map-shaped
file: names it lacks are left alone, names it shares must be identical. It refuses a change,
removal, an entry sharing an RVA, TLS offset or range with an existing one, an `__ImageBase` or
`_tls_index` addition, or anything that would turn a currently valid match record stale, unless
`--allow-change` is given; it then lists the records it made stale. `--history` imports versions
of another checkout's history (a worktree branch) that still rebuild from the result, so records
confirmed there stay valid after integration.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

from compare import IMAGE_BASE, THREAD_LOCAL, TLS_INDEX, load_symbol_map
from pecoff import EH_HANDLERS, Reject

ROOT = Path(__file__).resolve().parents[1]
HISTORY_SCHEMA = 1
VERSION_FIELDS = {'sha256', 'base', 'added', 'superseded'}
# Names the comparator treats by presence, beyond resolving them, and the entry kinds it accepts.
# carry_forward_problem has a rule for each; tests/test_symbol_map.py fails if compare.py comes to
# name a symbol or entry kind that is not listed here.
PRESENCE_NAMES = frozenset({IMAGE_BASE, TLS_INDEX}) | frozenset(EH_HANDLERS)
ENTRY_KINDS = frozenset({THREAD_LOCAL})
THREAD_LOCAL_KEYS = ['kind', 'tls_offset', 'size']
RVA_KEYS = ['rva', 'size']


def is_thread_local(entry):
    return isinstance(entry, dict) and 'kind' in entry


def span(entry):
    """(address space, start, size or None): RVA entries and thread-local offsets never overlap."""
    if is_thread_local(entry):
        return 'tls', entry['tls_offset'], entry.get('size')
    return 'rva', entry['rva'], entry.get('size')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _no_duplicates(pairs):
    keys = [k for k, _ in pairs]
    dup = sorted({k for k in keys if keys.count(k) > 1})
    require(not dup, f'duplicate JSON key {dup[0]!r}' if dup else '')
    return dict(pairs)


def strict_loads(text, what):
    """JSON with duplicate keys refused: json.loads would silently keep the last value."""
    try:
        return json.loads(text, object_pairs_hook=_no_duplicates)
    except ValueError as exc:
        raise ValueError(f'{what}: {exc}') from None


def serialize(value):
    """The one byte form the map and history are written in; rebuilds hash this form."""
    return (json.dumps(value, indent=2) + '\n').encode()


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def history_name(map_name):
    require(map_name.endswith('.json'), f'symbol map {map_name} must end in .json')
    return map_name[:-len('.json')] + '.history.json'


def provenance_entries(smap):
    prov = smap.get('_provenance')
    return prov.get('entries') if isinstance(prov, dict) and isinstance(prov.get('entries'), list) else None


def check_map(smap, what='symbol map'):
    """Shape the comparator accepts, plus one provenance entry per symbol when provenance is listed."""
    require(isinstance(smap, dict) and isinstance(smap.get('build_id'), str), f'{what}: needs a build_id')
    try:
        load_symbol_map({'build_id': smap['build_id']}, smap)
    except Reject as exc:
        raise ValueError(f'{what}: {exc.reason}: {exc.detail}') from None
    # One spelling per entry, so the same entry cannot appear in two byte forms (the comparator
    # ignores extra keys and key order, a version rebuild does not).
    for name, entry in smap['symbols'].items():
        if is_thread_local(entry):
            require(list(entry) == THREAD_LOCAL_KEYS,
                    f'{what}: thread-local entry {name} must have exactly the keys kind, tls_offset, size, in that order')
        else:
            require(list(entry) == RVA_KEYS, f'{what}: entry {name} must have exactly the keys rva, size, in that order')
    entries = provenance_entries(smap)
    if entries is not None:
        names = [e.get('name') if isinstance(e, dict) else None for e in entries]
        require(sorted(names, key=str) == sorted(smap['symbols']),
                f'{what}: _provenance.entries must name every symbol exactly once')


def subset(current, names):
    """The map with only `names`: what an earlier version was if nothing it held has changed."""
    out = {}
    for key, value in current.items():
        if key == 'symbols':
            out[key] = {n: e for n, e in value.items() if n in names}
        elif key == 'folds':
            out[key] = [g for g in value if all(n in names for n in g)]
        elif key == '_provenance' and provenance_entries(current) is not None:
            out[key] = {k: ([e for e in v if e['name'] in names] if k == 'entries' else v) for k, v in value.items()}
        else:
            out[key] = value
    return out


def version_names(versions):
    """Name set of every version, in order; a base always precedes the versions built on it."""
    out = []
    for v in versions:
        out.append((set() if v['base'] is None else out[v['base']]) | set(v['added']))
    return out


class MapState:
    """The current map and every version of it whose content is proven present and unchanged."""

    def __init__(self, current, current_sha, valid, superseded):
        self.current, self.current_sha = current, current_sha
        self.valid = valid            # sha256 -> frozenset of names, rebuilt and hash-checked
        self.superseded = superseded  # sha256 of versions this tool retired after a change

    def names_for(self, pinned):
        """Names of the version with hash `pinned`, or a ValueError saying why it is stale."""
        if pinned in self.valid:
            return self.valid[pinned]
        if pinned in self.superseded:
            raise ValueError('symbol map hash is stale: an entry of the pinned map version was changed or removed')
        raise ValueError('symbol map hash is stale: the pinned map version is not in the symbol map history')


def check_history(map_name, map_bytes, history):
    """MapState for a map and its history (None: no history file), or ValueError if they disagree."""
    current = strict_loads(map_bytes, map_name)
    check_map(current, map_name)
    current_sha = sha256(map_bytes)
    names = frozenset(current['symbols'])
    if history is None:
        return MapState(current, current_sha, {current_sha: names}, set())
    what = 'symbol map history'
    require(serialize(current) == map_bytes,
            f'{map_name} is not in canonical form (json indent 2 and a final newline); write it with tools/symbol_map.py')
    require(isinstance(history, dict) and set(history) == {'schema', 'map', 'versions'}
            and history['schema'] == HISTORY_SCHEMA and history['map'] == map_name,
            f'{what}: needs schema {HISTORY_SCHEMA}, map {map_name} and versions')
    versions = history['versions']
    require(isinstance(versions, list) and versions, f'{what}: versions must be a non-empty list')
    shas = set()
    for i, v in enumerate(versions):
        require(isinstance(v, dict) and {'sha256', 'base', 'added'} <= set(v) <= VERSION_FIELDS,
                f'{what}: version {i} needs sha256, base and added')
        require(isinstance(v['sha256'], str) and len(v['sha256']) == 64 and v['sha256'] not in shas,
                f'{what}: version {i} sha256 is malformed or repeated')
        shas.add(v['sha256'])
        require(v['base'] is None or (type(v['base']) is int and 0 <= v['base'] < i),
                f'{what}: version {i} base must name an earlier version')
        require(isinstance(v['added'], list) and all(isinstance(n, str) for n in v['added'])
                and len(set(v['added'])) == len(v['added']), f'{what}: version {i} added must list names once')
        require('superseded' not in v or v['superseded'] is True, f'{what}: version {i} superseded must be true or absent')
    valid, superseded = {}, set()
    held_by = version_names(versions)
    for i, v in enumerate(versions):
        base = set() if v['base'] is None else held_by[v['base']]
        require(not base & set(v['added']), f'{what}: version {i} adds a name its base already has')
        if v.get('superseded'):
            superseded.add(v['sha256'])
            continue
        held = held_by[i]
        require(held <= names, f'{what}: version {i} names entries the map no longer has but is not superseded')
        require(sha256(serialize(subset(current, held))) == v['sha256'],
                f'{what}: version {i} does not rebuild from the current map (an entry, fold or provenance '
                'entry it held changed, or the map was reordered); change the map only with tools/symbol_map.py')
        valid[v['sha256']] = frozenset(held)
    head = versions[-1]
    require(head['sha256'] == current_sha and valid.get(current_sha) == names,
            f'{what}: the last version must be the current map ({map_name} changed outside tools/symbol_map.py)')
    return MapState(current, current_sha, valid, superseded)


_CACHE = {}


def load_state(root, map_name):
    """MapState from files under `root`; cached per content for one check run."""
    map_bytes = (root / map_name).read_bytes()
    hist_path = root / history_name(map_name)
    hist_bytes = hist_path.read_bytes() if hist_path.is_file() else None
    key = (str(root), map_name, sha256(map_bytes), None if hist_bytes is None else sha256(hist_bytes))
    if key not in _CACHE:
        history = None if hist_bytes is None else strict_loads(hist_bytes, history_name(map_name))
        _CACHE[key] = check_history(map_name, map_bytes, history)
    return _CACHE[key]


def overlaps(rva, size, start, end):
    """Whether a map entry could alias or overlap [start, end) in the comparator's checks."""
    return start <= rva < end or bool(size and rva < end and start < rva + size)


def carry_forward_problem(state, names, rva, size, reports):
    """Why entries added since version `names` could have changed this pass, or None.

    A pass never resolved a name its map lacked (the comparator fails such a reference with
    `unresolved-symbol`), so an addition matters only where the comparator reads the map by presence
    (docs/comparator-contract.md, "Aliases, folds and overlaps" and "Thread-local variables"):
    an added entry at or inside the function range or named as the function, an `__ImageBase` or
    `_tls_index` entry, any thread-local entry, an EH handler name for a function with handler data,
    an entry at or inside a funclet range the reports give, or any entry at all for a function with
    funclets whose reports give no consistent ranges, might turn it into a fail.
    """
    added = {n: e for n, e in state.current['symbols'].items() if n not in names}
    if not added:
        return None
    if IMAGE_BASE in added:
        return f'{IMAGE_BASE} was added to the map'
    if TLS_INDEX in added:
        # Checked against the image's TLS directory slot whenever the map names it.
        return f'{TLS_INDEX} was added to the map'
    for name, entry in added.items():
        kind = entry.get('kind') if isinstance(entry, dict) else 'not an object'
        needed = 'tls_offset' if kind == THREAD_LOCAL else 'rva'
        if kind not in (None, THREAD_LOCAL) or needed not in entry:
            return f'added entry {name} is of no kind this rule knows'
        if kind == THREAD_LOCAL:
            # Every thread-local entry is checked against the image's TLS template, and the first
            # one makes the comparator require a TLS directory at all. The pinned runs did not
            # check this entry, and reports carry no template bounds that would show it inside.
            return f'thread-local entry {name} was added, which the comparator checks against the image TLS template'
    functions = {(r.get('function') or {}).get('symbol') for r in reports if isinstance(r, dict)}
    if set(added) & functions:
        return f'added entry {sorted(set(added) & functions)[0]} names the function'
    for name, entry in added.items():
        if overlaps(entry['rva'], entry.get('size'), rva, rva + size):
            return f'added entry {name} lies at or in the function range'
    coverage = [(r.get('coverage') or {}) for r in reports]
    if any(c.get('funclet_sections') for c in coverage):
        ranges = funclet_ranges(coverage, rva, size)
        if ranges is None:
            return 'the function has funclets whose ranges its reports do not give consistently, so no addition can be shown unrelated'
        for name, entry in added.items():
            for start, length in ranges:
                if overlaps(entry['rva'], entry.get('size'), start, start + length):
                    return f'added entry {name} lies at or in a funclet range'
    if set(added) & set(EH_HANDLERS) and any((c.get('eh') or {}).get('handlers') for c in coverage):
        return 'an EH handler name was added and the function has handler data'
    return None


def funclet_ranges(coverage, rva, size):
    """The [start, length] target ranges of the compared funclets all reports agree on, or None.

    The comparator rejects a map entry overlapping a funclet it binds; the ranges must account for
    every funclet byte it compared, so a report listing fewer funclets than it compared gives None.
    Ranges must be disjoint from each other and from the function `[rva, rva + size)`, which every
    consistent pass shows (the comparator refuses overlapping funclets); anything else is not
    trusted to describe what was compared. The comparator lists them in binding order, not address
    order, so they are sorted for the disjointness check, after the runs are compared as listed.
    """
    lists = [c.get('funclet_ranges') for c in coverage]
    first = lists[0]
    if not isinstance(first, list) or any(other != first for other in lists[1:]):
        return None
    if not all(isinstance(r, list) and len(r) == 2 and all(type(v) is int and v >= 0 for v in r) and r[1] > 0
               for r in first):
        return None
    if any(type(c.get('funclet_sections')) is not int or type(c.get('funclet_bytes_total')) is not int
           or len(first) != c['funclet_sections'] or sum(r[1] for r in first) != c['funclet_bytes_total']
           for c in coverage):
        return None
    ordered = sorted(first)
    if any(a[0] + a[1] > b[0] for a, b in zip(ordered, ordered[1:])):
        return None
    if any(overlaps(start, length, rva, rva + size) or overlaps(rva, size, start, start + length)
           for start, length in ordered):
        return None
    return [tuple(r) for r in ordered]


def record_problem(state, record):
    """None if a match record's pinned map still binds, else why it is stale (record shape is check.py's job)."""
    try:
        pinned = (record.get('symbol_map') or {}).get('sha256')
        if pinned == state.current_sha:
            return None
        names = state.names_for(pinned)
        reports = [run['report'] for run in record['runs']]
        ident = reports[0]['function']
        return carry_forward_problem(state, names, ident['rva'], ident['size'], reports)
    except ValueError as exc:
        return str(exc)
    except (KeyError, TypeError, IndexError):
        return 'malformed match record'


def match_records(root, map_name):
    """(path, record) for every match record under reports/ that pins `map_name`."""
    out = []
    for path in sorted((root / 'reports').glob('*/*.json')):
        if path.name.endswith(('.review.json', '.history.json')):
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and (record.get('symbol_map') or {}).get('path') == map_name:
            out.append((path.relative_to(root).as_posix(), record))
    return out


# -- changing the map -------------------------------------------------------------------------


def _insert_sorted(order, rva_of, name):
    """Insert after the last name whose RVA is not greater, so existing relative order is kept."""
    at = 0
    for i, n in enumerate(order):
        if rva_of(n) <= rva_of(name):
            at = i + 1
    order.insert(at, name)


def incoming_entry(name, entry):
    """An incoming entry in its canonical form: `{rva, size}` (a missing size written as null), or a
    thread-local entry rewritten as kind, tls_offset, size (`size` required, null or positive)."""
    require(isinstance(entry, dict), f'incoming entry {name} must be an object')
    if 'kind' not in entry:
        require(set(entry) <= set(RVA_KEYS) and type(entry.get('rva')) is int,
                f'incoming entry {name} must be {{rva, size}} or {{kind: "thread-local", tls_offset, size}}')
        return {'rva': entry['rva'], 'size': entry.get('size')}
    size = entry.get('size')
    require(set(entry) == set(THREAD_LOCAL_KEYS) and entry['kind'] == THREAD_LOCAL
            and type(entry['tls_offset']) is int and entry['tls_offset'] >= 0
            and (size is None or (type(size) is int and size > 0)),
            f'incoming entry {name} must be {{rva, size}} or {{kind: "thread-local", tls_offset, size}}')
    return {'kind': THREAD_LOCAL, 'tls_offset': entry['tls_offset'], 'size': size}


def plan(current, incoming, remove=(), allow_change=False):
    """The merged map and what merging `incoming` into `current` adds, changes, removes and refuses."""
    require(isinstance(incoming, dict) and isinstance(incoming.get('symbols'), dict), 'incoming map needs symbols')
    require(incoming.get('build_id') == current['build_id'], 'incoming map is for another build')
    cur = current['symbols']
    inc = {name: incoming_entry(name, entry) for name, entry in incoming['symbols'].items()}
    refusals = []
    added = [n for n in inc if n not in cur]
    for name in (IMAGE_BASE, TLS_INDEX):
        if name in added:
            # The comparator checks these by presence for every function, so the addition can
            # change any earlier pass (carry_forward_problem stales every record pinned before it).
            refusals.append(f'adds {name}, which every match record pinned to an earlier map version did not have')
    changed = [n for n in inc if n in cur and inc[n] != cur[n]]
    removed = list(dict.fromkeys(remove))
    for name in removed:
        require(name in cur, f'cannot remove {name}: not in the map')
        require(name not in inc, f'cannot both remove and keep {name}')
    cur_prov = provenance_entries(current)
    inc_prov = {e['name']: e for e in (provenance_entries(incoming) or []) if isinstance(e, dict) and 'name' in e}
    if cur_prov is not None:
        old = {e['name']: e for e in cur_prov}
        for name in added:
            require(name in inc_prov, f'incoming entry {name} has no _provenance entry')
            # A thread-local entry has no address, so a provenance entry giving one would mislead.
            require(not is_thread_local(inc[name]) or 'rva' not in inc_prov[name],
                    f'_provenance entry for thread-local {name} gives an rva')
        changed += [n for n in inc_prov if n in old and n not in changed and n not in removed and inc_prov[n] != old[n]]
        top_cur = {k: v for k, v in current['_provenance'].items() if k != 'entries'}
        inc_top = incoming.get('_provenance')
        # Description keys the incoming file leaves out are kept; one it gives differently is a change.
        top_inc = dict(top_cur, **{k: v for k, v in inc_top.items() if k != 'entries'}) \
            if isinstance(inc_top, dict) else top_cur
        top_changed = top_inc != top_cur
    else:
        top_changed = False
    if changed:
        refusals.append(f'changes existing entries: {", ".join(sorted(set(changed)))}')
    if removed:
        refusals.append(f'removes entries: {", ".join(removed)}')
    if top_changed:
        refusals.append('changes the _provenance description of the whole map')
    keep = [n for n in cur if n not in removed]
    shadowing = []
    for name in added:
        space, start, size = span(inc[name])
        for other in keep:
            o_space, o_start, o_size = span(cur[other] if other not in changed else inc[other])
            if o_space == space and (o_start == start or overlaps(start, size, o_start, o_start + (o_size or 1))
                                     or overlaps(o_start, o_size, start, start + (size or 1))):
                shadowing.append(f'added entry {name} shares an address or range with existing entry {other}')
    folded = [set(g) for g in incoming.get('folds', [])]
    for i, name in enumerate(added):
        for other in added[i + 1:]:
            if span(inc[name])[:2] == span(inc[other])[:2] and not any({name, other} <= g for g in folded):
                what = 'an RVA' if span(inc[name])[0] == 'rva' else 'a TLS offset'
                shadowing.append(f'added entries {name} and {other} share {what} without a fold group')
    refusals += shadowing

    new = copy.deepcopy(current)
    symbols = {n: new['symbols'][n] for n in keep}
    for name in changed:
        if name in inc:
            symbols[name] = copy.deepcopy(inc[name])
    order = list(symbols)
    for name in added:
        symbols[name] = copy.deepcopy(inc[name])
        # RVA entries first by RVA, then thread-local entries by offset.
        _insert_sorted(order, lambda n: span(symbols[n])[:2], name)
    new['symbols'] = {n: symbols[n] for n in order}
    folds = [[n for n in g if n not in removed] for g in new.get('folds', [])]
    folds = [g for g in folds if len(g) > 1]
    known = [sorted(g) for g in folds]
    retire = set()
    for group in incoming.get('folds', []):
        if sorted(group) in known:
            continue
        if all(n in added for n in group):
            folds.append(list(group))
            known.append(sorted(group))
        else:
            refusals.append(f'new fold group {group} names existing entries')
            if allow_change:
                folds.append(list(group))
                # A group of old names alone would appear in rebuilds of the versions holding them.
                if not any(n in added for n in group):
                    retire |= set(group)
    if 'folds' in new or folds:
        new['folds'] = folds
    if cur_prov is not None:
        prov = {e['name']: copy.deepcopy(e) for e in cur_prov if e['name'] not in removed}
        for name in list(added) + [n for n in changed if n in inc_prov]:
            prov[name] = copy.deepcopy(inc_prov[name])
        aligned = [e['name'] for e in cur_prov] == list(current['symbols'])
        names_order = list(new['symbols']) if aligned else [e['name'] for e in cur_prov if e['name'] in prov] + \
            [n for n in new['symbols'] if n not in {e['name'] for e in cur_prov}]
        new['_provenance'] = dict(top_inc if top_changed else top_cur)
        new['_provenance']['entries'] = [prov[n] for n in names_order]
        # Keep the description keys where they were.
        new['_provenance'] = {k: new['_provenance'][k] for k in current['_provenance']} | \
            {k: v for k, v in new['_provenance'].items() if k not in current['_provenance']}
    check_map(new, 'resulting map')
    return {'map': new, 'added': added, 'changed': sorted(set(changed)), 'removed': removed,
            'refusals': refusals, 'shadowing': shadowing, 'retire': retire, 'whole_map_changed': top_changed}


def new_history(map_name, state, history, new_map, added, retired, imported=()):
    """History after writing `new_map`, and how many versions of another history it imported.

    `retired` names (or True for all) supersede every version that held them. An imported version
    is kept only if the new map rebuilds to its hash, so the other history is never trusted.
    """
    if history is None:
        history = {'schema': HISTORY_SCHEMA, 'map': map_name,
                   'versions': [{'sha256': state.current_sha, 'base': None, 'added': list(state.current['symbols'])}]}
    history = copy.deepcopy(history)
    versions = history['versions']
    for v, held in zip(versions, version_names(versions)):
        if not v.get('superseded') and (retired is True or held & set(retired)):
            v['superseded'] = True
    sha = sha256(serialize(new_map))
    if versions[-1]['sha256'] != sha:
        require(all(v['sha256'] != sha for v in versions), 'the resulting map repeats an earlier version')
        if versions[-1].get('superseded'):
            versions.append({'sha256': sha, 'base': None, 'added': list(new_map['symbols'])})
        else:
            versions.append({'sha256': sha, 'base': len(versions) - 1, 'added': list(added)})
    count = 0
    for name_set, version_sha in imported:
        if any(v['sha256'] == version_sha for v in versions) or not name_set <= set(new_map['symbols']):
            continue
        if sha256(serialize(subset(new_map, name_set))) != version_sha:
            continue
        held_by = version_names(versions)
        bases = [i for i, v in enumerate(versions[:-1]) if not v.get('superseded') and held_by[i] <= name_set]
        base = max(bases, key=lambda i: len(held_by[i])) if bases else None
        rest = sorted(name_set - (held_by[base] if base is not None else set()))
        # Inserted before the head, which must stay last; bases point at earlier entries only.
        versions.insert(len(versions) - 1, {'sha256': version_sha, 'base': base, 'added': rest})
        count += 1
    return history, count


def other_versions(history):
    """(names, sha256) of every non-superseded version in another checkout's history."""
    versions = history['versions']
    return [(frozenset(held), v['sha256']) for v, held in zip(versions, version_names(versions))
            if not v.get('superseded')]


def apply_change(root, map_name, incoming, remove=(), allow_change=False, other_history=None, dry_run=False,
                 allow_unpinned_change=False):
    """Merge `incoming` into the map under `root`; returns a summary dict. Refusals raise ValueError.

    `allow_unpinned_change` (the bind step) permits changes and removals that leave every match
    record under `root` valid, such as renaming a draft's own entry; shadowing never.
    """
    state = load_state(root, map_name)
    hist_path = root / history_name(map_name)
    history = strict_loads(hist_path.read_bytes(), history_name(map_name)) if hist_path.is_file() else None
    # The first version is the file as it is now, and a version must rebuild byte for byte.
    require(history is not None or serialize(state.current) == (root / map_name).read_bytes(),
            f'{map_name} is not in canonical form, so records pinned to it could not be carried; '
            'rewrite it canonically and re-confirm those records first')
    result = plan(state.current, incoming, remove, allow_change)
    new_map, refusals = result['map'], result['refusals']
    retired = True if result['whole_map_changed'] else \
        set(result['changed']) | set(result['removed']) | result['retire']
    imported = other_versions(other_history) if other_history is not None else ()
    history, count = new_history(map_name, state, history, new_map, result['added'], retired, imported)
    map_bytes = serialize(new_map)
    new_state = check_history(map_name, map_bytes, history)
    stale = []
    for path, record in match_records(root, map_name):
        if record_problem(state, record) is None:
            problem = record_problem(new_state, record)
            if problem is not None:
                stale.append((path, problem))
    if stale:
        refusals.append(f'makes {len(stale)} valid match record(s) stale')
    summary = dict(result, map=None, stale_records=stale, sha256=sha256(map_bytes),
                   versions=len(history['versions']), imported=count)
    tolerated = allow_unpinned_change and not stale and not result['shadowing']
    if refusals and not allow_change and not tolerated:
        raise ValueError('refused (pass --allow-change to apply and make the listed records stale): '
                         + '; '.join(refusals) + ''.join(f'\n  stale: {p}: {why}' for p, why in stale))
    if not dry_run:
        (root / map_name).write_bytes(map_bytes)
        hist_path.write_bytes(serialize(history))
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    sub = parser.add_subparsers(dest='command', required=True)
    verify = sub.add_parser('verify', help='Check the history and say which match records still bind')
    verify.add_argument('--map', required=True)
    add = sub.add_parser('add', help='Add entries from a symbol-map-shaped file')
    add.add_argument('--map', required=True)
    add.add_argument('--from', dest='source', required=True, type=Path)
    add.add_argument('--history', type=Path, help="another checkout's history whose versions to import")
    add.add_argument('--remove', action='append', default=[], help='entry to remove (needs --allow-change)')
    add.add_argument('--allow-change', action='store_true',
                     help='apply changes, removals and shadowing additions; affected records become stale')
    add.add_argument('--dry-run', action='store_true')
    parser.add_argument('--root', type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    root = args.root
    try:
        if args.command == 'verify':
            state = load_state(root, args.map)
            records = match_records(root, args.map)
            print(f'PASS: {args.map} history: {len(state.valid)} valid version(s), '
                  f'{len(state.superseded)} superseded; current {state.current_sha[:12]}')
            bad = 0
            for path, record in records:
                problem = record_problem(state, record)
                pinned = (record.get('symbol_map') or {}).get('sha256', '')
                how = 'current' if pinned == state.current_sha else 'carried'
                print(f'  {path}: {"stale: " + problem if problem else how}')
                bad += bool(problem)
            return 1 if bad else 0
        incoming = strict_loads(args.source.read_bytes(), str(args.source))
        other = strict_loads(args.history.read_bytes(), str(args.history)) if args.history else None
        summary = apply_change(root, args.map, incoming, args.remove, args.allow_change, other, args.dry_run)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    verb = 'would write' if args.dry_run else 'wrote'
    print(f'{verb} {args.map}: {len(summary["added"])} added, {len(summary["changed"])} changed, '
          f'{len(summary["removed"])} removed; sha256 {summary["sha256"]}; {summary["versions"]} version(s)')
    for path, why in summary['stale_records']:
        print(f'  now stale: {path}: {why}')
    for refusal in summary['refusals']:
        print(f'  allowed by --allow-change: {refusal}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
