"""Bind a task's decorated names to target RVAs from a compiled candidate object (local only).

`tools/verifier/attempt` calls this after every compile, so a Drafter never runs a separate bind
step; `python3 tools/ghidra/export_pack.py bind --task <dir>` runs the same code by hand.

Compared functions (`task.json` `functions[].symbol`). The decorated name is whatever the
Drafter's declarations produce, so it is found in the object, in this order:

1. a hint in `<task dir>/bind-hints.json` whose RVA is the function's RVA;
2. the current symbol, if the object still defines it;
3. the one defined function whose qualified name (template arguments, return type and
   parameters dropped) equals the community name;
4. the one defined function whose member name (last component) equals the community name's.

Destructors are special. A virtual destructor's vtable slot 0 in the image is the scalar
(`??_G`) or vector (`??_E`) deleting destructor, not the plain `??1` the community name
`X::~X` demangles to, and the compiler emits all of them as separate functions. The task's
`functions[].destructor` (written by `annotate_destructors` from the pack: slot 0, a test of the
delete-flag argument and a call guarded by it) lists the decorated prefixes the target can be.
For such a function steps 2 to 4 are replaced by: the current symbol if its prefix is allowed,
else the one allowed destructor of the class in the object, else, when several are allowed and
defined, the one whose size equals the target's (closest otherwise), reported as a choice.

A hint whose RVA is a compared function's RVA but which does not end up naming it (not defined
in the object, ambiguous, or overridden) is reported as ignored and makes `main` fail; it is
never dropped silently.

A defined function is an external symbol at offset 0 of its own code section, which is what the
comparator requires anyway. When a previously bound symbol is gone and another is found, that is
reported as "decorated name changed" with both names, and the old map entry is removed (a stale
entry at the same RVA would be an undeclared alias).

References (relocations that leave a compared function). Each needs a map entry giving the RVA
the game encodes; in order:

1. a hint naming the symbol (decorated, or qualified as above); it replaces a different entry
   already in `symbols.json`, which is reported;
2. an entry already in `symbols.json`;
3. by position: the target's own relocated field at the same offset, decoded from the local
   image, when that RVA is one of the pack's listed references of this function (so a
   misaligned candidate cannot bind a wrong address: the decoded value must be a known target);
4. the one pack reference whose community name equals the symbol's qualified name, or failing
   that its member name.

The same applies to references made from the function's funclets (catch and unwind code the
comparator compares with it, found through its .pdata, unwind info and FuncInfo). For an unwind
funclet the pack's `object_lifetimes` adds the destructor calls of its state: by position at the
state's funclet RVA when the decoded value is one of them, by community name, or, when the state
lists exactly one call and the funclet leaves exactly one name unbound, that call.

Anything left is listed with the file to edit. The comparator still checks every binding: a
wrong RVA fails with relocation-target-mismatch, it cannot pass.

Where the map lives. A task whose `symbols` is the repository map (`reports/<build id>/...`) has
its new entries added through `tools/symbol_map.py`, the only writer of that map, with a
provenance entry saying bind found them. A rename or removal is applied only if it leaves every
match record in the checkout valid (a draft renaming its own function); otherwise bind refuses
and the change needs `tools/symbol_map.py add --allow-change`. A private `symbols.json` is edited
in place as before.

Thread-local variables (references by a SECREL relocation) are never bound by position or name:
only a hint `"<name>": "tls:0x<offset>"` binds one, as a `thread-local` map entry with that
TLS-template offset (docs/comparator-contract.md, "Thread-local variables"). `_tls_index` needs
no entry; the comparator takes it from the image's TLS directory. A `tls:` hint that no compared
SECREL reference uses is listed under ignored hints. A thread-local entry is published to the
repository map like any other, with a provenance entry giving its offset; because the comparator
checks every thread-local entry against the image's TLS template, adding one makes every match
record pinned to an earlier map version stale, so bind refuses it while such records exist and
the addition needs `tools/symbol_map.py add --allow-change` and re-confirmation of those records.

`bind-hints.json` (private, optional), keys are decorated names (`?...`) or qualified names as
the Drafter wrote them (`BSTimer::QGlobalTimeMultiplier`, `GetArmorKind`), values are RVAs:

    {"?GetArmorKind@@YAHPEAVTESObjectARMO@@@Z": "0x27edf0",
     "BSTimer::QGlobalTimeMultiplier": "0x20ccac8"}

A hint whose RVA is a compared function's RVA names that function's decorated or qualified name.
Use hints for targets without a community name, template members and renamed stand-ins; give
only RVAs listed in the function's pack (never guessed ones).
"""
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(REPO / 'tools'))
from pecoff import CoffObject, PeImage, SCN_CNT_CODE, STORAGE_EXTERNAL  # noqa: E402
import symbol_map as symbol_maps  # noqa: E402

UNBOUND = 'unbound:'
HINTS = 'bind-hints.json'
# Comparator reasons that mean "nothing was compared because a name is not bound", not a code difference.
BINDING_REASONS = {'function-symbol-missing', 'unresolved-symbol'}
REL32_TAIL = {0x04: 0, 0x05: 1, 0x06: 2, 0x07: 3, 0x08: 4, 0x09: 5}
ADDR32NB = 0x03
SECREL = 0x0B
TLS_HINT = re.compile(r'tls:(0x[0-9a-fA-F]+|[0-9]+)')
# Resolved by the comparator from the image's TLS directory, so it never gets a map entry.
DIRECTORY_SYMBOLS = {'_tls_index'}
UNDNAME = ('llvm-undname', '/opt/homebrew/opt/llvm/bin/llvm-undname', '/usr/local/opt/llvm/bin/llvm-undname')


def parse_rva(value):
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    if isinstance(value, str) and re.fullmatch(r'0x[0-9a-fA-F]+|[0-9]+', value):
        return int(value, 0)
    raise ValueError(f'not an RVA: {value!r}')


def find_undname(objdump=None):
    """llvm-undname, preferably next to the configured llvm-objdump."""
    names = []
    if objdump:
        names.append(str(Path(objdump).with_name('llvm-undname')))
    for name in names + [os.environ.get('SR_UNDNAME')] + list(UNDNAME):
        if name and (shutil.which(name) or (os.path.isfile(name) and os.access(name, os.X_OK))):
            return shutil.which(name) or name
    return None


def strip_templates(text):
    out, depth = [], 0
    for ch in text:
        if ch == '<':
            depth += 1
        elif ch == '>':
            depth = max(depth - 1, 0)
        elif depth == 0:
            out.append(ch)
    return ''.join(out)


def qualified(demangled):
    """`Scope::member` from a demangled declaration, without template arguments, types or parameters."""
    if not demangled:
        return None
    text = strip_templates(demangled)
    if '(' in text and 'operator' not in text:
        text = text[:text.index('(')]
    tokens = text.replace('*', ' ').replace('&', ' ').split()
    return tokens[-1] if tokens else None


def fallback_qualified(name):
    """Qualified name for plain `?member@Scope@...@@` decorations without a demangler; None otherwise."""
    m = re.match(r'\?([A-Za-z_]\w*)@((?:[A-Za-z_]\w*@)*)@', name)
    if not m:
        return None
    return '::'.join([x for x in reversed(m.group(2).split('@')) if x] + [m.group(1)])


def member(name):
    return name.split('::')[-1] if name else None


def community_qualified(name):
    parts = [p for p in strip_templates(name or '').split('::') if p]
    while parts and parts[0] in ('RE', 'Offset'):
        parts.pop(0)
    return '::'.join(parts) or None


class Names:
    """Qualified names of decorated symbols, demangled with llvm-undname when available."""

    def __init__(self, tool=None):
        self.tool, self.cache = tool, {}

    def load(self, names):
        todo = [n for n in names if n not in self.cache and n.startswith('?')]
        if todo and self.tool:
            out = subprocess.run([self.tool] + todo, capture_output=True, text=True, timeout=60).stdout
            blocks = [b.split('\n') for b in out.strip().split('\n\n')]
            for block in blocks:
                if len(block) >= 2 and not block[1].startswith('error'):
                    self.cache[block[0]] = qualified(block[1])
        for n in names:
            # Undecorated names (extern "C", tests) are their own qualified name; compiler-made
            # names such as __real@ or $unwind$ are never bound by name.
            plain = n if re.fullmatch(r'[A-Za-z_]\w*', n) and not n.startswith('__') else None
            self.cache.setdefault(n, fallback_qualified(n) if n.startswith('?') else plain)

    def __call__(self, name):
        self.load([name])
        return self.cache.get(name)


def defined_functions(obj):
    """{name: section} for external symbols at offset 0 of a code section (comparable functions)."""
    out = {}
    for sym in obj.symbols.values():
        if sym.storage == STORAGE_EXTERNAL and sym.section > 0 and sym.value == 0 \
                and obj.section(sym.section).flags & SCN_CNT_CODE:
            out[sym.name] = sym.section
    return out


def outgoing(obj, section):
    """[(relocation, target symbol)] in `section` whose target lies outside it."""
    sec = obj.section(section)
    out = []
    for rel in sec.relocs:
        target = obj.symbols[rel.symbol]
        if target.section != section:
            out.append((rel, target))
    return out


EH_DATA_SECTIONS = ('.pdata', '.xdata', '.rdata', '.data$r')


def funclets(obj, section, defined_sections):
    """{code section: state or None} of the funclets a function's exception data reaches.

    Starts at the function's own .pdata entries (only the entry whose begin address is in the
    function, so a shared .pdata does not pull in other functions), follows the unwind info, the
    C++ FuncInfo and its maps through data sections, and collects every code section reached that
    is not the function itself and does not define another function. This is the set the
    comparator compares as funclet code, so a reference made only from a funclet is bound too.
    The state is the unwind-map index of an unwind (destructor) funclet when the FH3 map is
    readable, which ties it to the pack's object-lifetime state of the same index.
    """
    group, found = [section], {}
    seen_data = set()
    while group:
        code = group.pop()
        queue = []
        for sec in obj.sections:
            if not sec.name.startswith('.pdata'):
                continue
            starts = {r.offset for r in sec.relocs if obj.symbols[r.symbol].section == code and r.offset % 12 == 0}
            queue += [obj.symbols[r.symbol].section for r in sec.relocs if r.offset - 8 in starts]
        while queue:
            index = queue.pop()
            if index <= 0 or index in seen_data or index == section or index in found:
                continue
            sec = obj.section(index)
            if sec.flags & SCN_CNT_CODE:
                if index not in defined_sections:
                    found[index] = None
                    group.append(index)
                continue
            if not sec.name.startswith(EH_DATA_SECTIONS):
                continue
            seen_data.add(index)
            queue += [obj.symbols[r.symbol].section for r in sec.relocs]
    for state, target in unwind_actions(obj, section):
        if target.section in found:
            found[target.section] = (state, target.value)
    return found


def unwind_actions(obj, section):
    """[(state, funclet symbol)] from the FH3 `$cppxdata$` FuncInfo of the function in `section`."""
    out = []
    for sym in obj.symbols.values():
        if not sym.name.startswith('$cppxdata$') or sym.section <= 0:
            continue
        info = obj.section(sym.section)
        rels = {r.offset: obj.symbols[r.symbol] for r in info.relocs}
        if info.data is None or not _reaches(obj, sym, section):
            continue
        try:
            max_state = struct.unpack_from('<I', info.data, sym.value + 4)[0]
        except struct.error:
            continue
        umap = rels.get(sym.value + 8)
        if umap is None or umap.section <= 0 or max_state > 4096:
            continue
        msec = obj.section(umap.section)
        mrels = {r.offset: obj.symbols[r.symbol] for r in msec.relocs}
        for i in range(max_state):
            action = mrels.get(umap.value + 8 * i + 4)
            if action is not None and action.section > 0:
                out.append((i, action))
    return out


def _reaches(obj, cppxdata, section):
    """Whether the FuncInfo `cppxdata` belongs to the function in `section` (its IP map starts there)."""
    info = obj.section(cppxdata.section)
    rels = {r.offset: obj.symbols[r.symbol] for r in info.relocs}
    ipmap = rels.get(cppxdata.value + 24)
    if ipmap is None or ipmap.section <= 0:
        return False
    return any(obj.symbols[r.symbol].section == section for r in obj.section(ipmap.section).relocs)


def lifetime_calls(repo, fn):
    """{state: [(rva, community qualified name or None)]} of a pack's object-lifetime destructor calls."""
    if not fn.get('pack'):
        return {}, {}
    path = Path(repo) / fn['pack'] / 'pack.json'
    if not path.is_file():
        return {}, {}
    life = json.loads(path.read_text()).get('object_lifetimes') or {}
    calls, places = {}, {}
    for st in life.get('states') or []:
        entries = []
        for text in st.get('calls') or []:
            head, _, rest = str(text).partition(' ')
            try:
                entries.append((parse_rva(head), community_qualified(rest.strip()) if rest.strip() else None))
            except ValueError:
                continue
        calls[st.get('state')] = entries
        if st.get('funclet'):
            places[st.get('state')] = parse_rva(st['funclet'])
    return calls, places


def by_position(image, fn_rva, rel):
    """The RVA the target's own field at the relocation's offset encodes, or None."""
    if image is None:
        return None
    try:
        field = image.read(fn_rva + rel.offset, 4, 'bind')[1]
    except Exception:
        return None
    if rel.kind in REL32_TAIL:
        (disp,) = struct.unpack('<i', field)
        return fn_rva + rel.offset + 4 + REL32_TAIL[rel.kind] + disp
    if rel.kind == ADDR32NB:
        return struct.unpack('<I', field)[0]
    return None


# MSVC special-name prefixes of the three destructor functions a class with a virtual destructor gets.
DTOR_KINDS = {'??1': 'destructor', '??_G': 'scalar deleting destructor', '??_E': 'vector deleting destructor'}
# Access codes of adjustor thunks (`[thunk]: ... adjustor{n}'`): a thunk is never the slot body itself.
THUNK_ACCESS = set('GHOPWX')
VOLATILE = {'A', 'C', 'D', 'R8', 'R9', 'R10', 'R11'}
WRITES = {'MOV', 'LEA', 'MOVZX', 'MOVSX', 'MOVSXD', 'XOR', 'SUB', 'ADD', 'OR', 'SHL', 'SHR', 'SAR', 'IMUL', 'POP',
          'CMOVZ', 'CMOVNZ', 'CMOVE', 'CMOVNE', 'SETZ', 'SETNZ', 'XCHG'}


def dtor_decoration(name):
    """(prefix, class) of a plain or deleting destructor's decorated name; None for others and thunks.

    Template class scopes (`?$...`) are not parsed; such destructors bind by the ordinary rules.
    """
    for prefix in ('??_G', '??_E', '??1'):
        if not name.startswith(prefix):
            continue
        rest = name[len(prefix):]
        if '@@' not in rest or rest.startswith('?'):
            return None
        scope, tail = rest.split('@@', 1)
        if not scope or not tail or tail[0] in THUNK_ACCESS or '?' in scope:
            return None
        return prefix, '::'.join(reversed(scope.split('@')))
    return None


def reg_family(op):
    """Architectural register of an operand (`EBX` -> `B`, `R8D` -> `R8`), or None for memory/immediates."""
    op = op.strip().upper()
    m = re.fullmatch(r'R(8|9|1[0-5])[DWB]?', op)
    if m:
        return 'R' + m.group(1)
    m = re.fullmatch(r'[RE]?([ABCD])X|([ABCD])L', op)
    if m:
        return m.group(1) or m.group(2)
    m = re.fullmatch(r'[RE]?(SI|DI|BP|SP)L?', op)
    return m.group(1) if m else None


def listing_instructions(text):
    """[(mnemonic, [operands])] from a pack listing (`  +0x01a  MOV EBX,EDX   [annotation]`)."""
    out = []
    for line in text.splitlines():
        m = re.match(r'\s*\+0x[0-9a-fA-F]+\s+(\S.*)$', line)
        if not m:
            continue
        insn = re.split(r'\s{2,}', m.group(1).strip())[0]
        mnem, _, ops = insn.partition(' ')
        out.append((mnem.upper(), [o.strip() for o in ops.split(',')] if ops.strip() else []))
    return out


def delete_flag_use(text):
    """(bits of the second argument that are tested, whether a call or jump follows the first test).

    Follows the x64 second argument (EDX) through register copies until it is overwritten or a
    call clobbers it, which is how a deleting destructor keeps its flag across the inlined body.
    """
    flag, bits, called = {'D'}, set(), False
    for mnem, ops in listing_instructions(text):
        if mnem in ('TEST', 'AND', 'BT') and len(ops) == 2 and reg_family(ops[0]) in flag:
            try:
                imm = int(ops[1], 0)
            except ValueError:
                imm = None
            if imm is not None:
                if mnem == 'BT':
                    imm = 1 << imm
                bits |= {b for b in (1, 2) if imm & b}
                continue
        if mnem == 'CALL' or (mnem == 'JMP' and ops and ops[0].startswith('0x')):
            called = called or bool(bits)
            flag -= VOLATILE
            continue
        if not ops:
            continue
        dst = reg_family(ops[0])
        src = reg_family(ops[1]) if len(ops) == 2 else None
        if dst is None:
            continue
        if mnem == 'MOV' and src in flag:
            flag.add(dst)
        elif dst in flag and mnem in WRITES:
            flag.discard(dst)
    return bits, called


def destructor_spec(community_name, name_how, listing):
    """Which destructor functions a target can be, with the evidence; None when it is not a destructor."""
    name = member(community_qualified(community_name)) or ''
    slot0 = (name_how or '').strip() == 'slot 0'
    if not name.startswith('~') and not slot0:
        return None
    bits, called = delete_flag_use(listing) if listing is not None else (set(), False)

    def spec(prefixes, evidence, decided):
        return {'symbols': list(prefixes), 'kind': ' or '.join(DTOR_KINDS[p] for p in prefixes),
                'decided': decided, 'evidence': evidence}
    if 2 in bits:
        return spec(['??_E'], 'tests bit 1 (array delete) of the flag argument', True)
    if bits and called:
        return spec(['??_G'], 'tests bit 0 of the flag argument and calls operator delete under it', True)
    if not name.startswith('~'):
        return None
    if bits:
        return spec(['??_G', '??_E'], 'tests the flag argument but no call follows', False)
    if listing is not None and not slot0:
        return spec(['??1'], 'no delete-flag test and not a vtable slot 0', True)
    return spec(['??_G', '??_E', '??1'], ('vtable slot 0 ' if slot0 else '')
                + ('without a delete-flag test' if listing is not None else 'and no listing in the pack'), False)


def annotate_destructors(task, repo=REPO):
    """Set or clear `destructor` on each compared function from its pack; True when anything changed."""
    changed = False
    for fn in task['functions']:
        if fn.get('role') == 'regression' or not fn.get('pack'):
            continue
        pack = Path(repo) / fn['pack']
        try:
            ident = json.loads((pack / 'pack.json').read_text()).get('identity', {})
        except (OSError, ValueError):
            continue
        listing = (pack / 'listing.txt').read_text() if (pack / 'listing.txt').is_file() else None
        spec = destructor_spec(fn.get('community_name'), ident.get('name_how'), listing)
        if spec != fn.get('destructor'):
            if spec is None:
                fn.pop('destructor', None)
            else:
                fn['destructor'] = spec
            changed = True
    return changed


def _raw_hints(task_dir):
    path = Path(task_dir) / HINTS
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f'{path}: must be a JSON object of name -> RVA')
    return {str(k): v for k, v in raw.items() if not str(k).startswith('_')}


def load_hints(task_dir):
    """name -> RVA hints; `tls:` values are thread-local offsets and are read by load_tls_hints."""
    return {k: parse_rva(v) for k, v in _raw_hints(task_dir).items()
            if not (isinstance(v, str) and v.startswith('tls:'))}


def load_tls_hints(task_dir):
    """name -> TLS-template offset from hints of the form "tls:0x<offset>"."""
    out = {}
    for k, v in _raw_hints(task_dir).items():
        if isinstance(v, str) and v.startswith('tls:'):
            m = TLS_HINT.fullmatch(v)
            if not m:
                raise ValueError(f'not a thread-local offset: {v!r}')
            out[k] = int(m.group(1), 0)
    return out


def pack_references(repo, fn):
    """[(target rva, [community qualified names])] of a function's pack, or []."""
    if not fn.get('pack'):
        return []
    path = Path(repo) / fn['pack'] / 'pack.json'
    if not path.is_file():
        return []
    out = []
    for r in json.loads(path.read_text()).get('references', []):
        names = [community_qualified(c['name']) for c in r.get('community_names', [])
                 if c.get('kind') not in ('vtable', 'rtti', 'nirtti')]
        out.append((r['target_rva'], [n for n in names if n]))
    return out


def bind(task_dir, obj_path, image_path=None, objdump=None, repo=REPO):
    """Update task.json and symbols.json in place; returns a report dict (see `describe`)."""
    task_dir = Path(task_dir)
    task = json.loads((task_dir / 'task.json').read_text())
    map_name = task.get('symbols', 'symbols.json')
    public = map_name.startswith('reports/')
    smap_path = (Path(repo) / map_name) if public else task_dir / map_name
    smap = json.loads(smap_path.read_text())
    before = json.loads(json.dumps(smap.get('symbols', {})))
    symbols = smap.setdefault('symbols', {})
    found = {}  # name -> (how, community name) for provenance of public additions
    obj = CoffObject(Path(obj_path).read_bytes())
    image = PeImage(Path(image_path).read_bytes()) if image_path and Path(image_path).is_file() else None
    hints = load_hints(task_dir)
    tls_hints = load_tls_hints(task_dir)
    tls_used = set()
    names = Names(find_undname(objdump))
    defined = defined_functions(obj)
    names.load(list(defined) + [s.name for s in obj.symbols.values()] + list(hints) + list(tls_hints))
    report = {'functions': [], 'references': [], 'unbound_functions': [], 'unbound_references': [],
              'unbound_thread_locals': [],
              'renamed': [], 'ignored_hints': [], 'destructor_choices': [], 'warnings': [], 'changed': False}
    if annotate_destructors(task, repo):
        report['changed'] = True

    def size_of(d):
        return obj.section(defined[d]).raw_size

    def hint_for(name):
        if name in hints:
            return hints[name]
        q = names(name)
        return hints.get(q) if q else None

    taken = set()
    for fn in task['functions']:
        rva = parse_rva(fn['rva'])
        old = fn.get('symbol') or ''
        community = community_qualified(fn.get('community_name'))
        how, new = None, None
        spec = fn.get('destructor')
        cls = community.rsplit('::', 1)[0] if community and '::' in community else None

        def dtor_ok(d):
            dec = dtor_decoration(d)
            return bool(spec and dec and dec[0] in spec['symbols'] and cls
                        and (dec[1] == cls or member(dec[1]) == member(cls)))
        hinted = [n for n, r in hints.items() if r == rva]
        for h in hinted:
            hits = [d for d in defined if d == h or names(d) == h]
            if len(hits) == 1:
                how, new = 'hint', hits[0]
                if spec and not dtor_ok(new):
                    report['warnings'].append(f'hint {h} for {hex(rva)} overrides the pack evidence for a '
                                              f'{spec["kind"]} ({spec["evidence"]})')
                break
        if spec is not None:
            if new is None and old in defined and dtor_ok(old):
                how, new = 'kept', old
            hits = sorted(d for d in defined if dtor_ok(d) and d not in taken)
            if new is None and len(hits) == 1:
                how, new = 'destructor kind', hits[0]
            elif new is None and hits:
                size = parse_rva(fn['size'])
                ranked = sorted(hits, key=lambda d: (abs(size_of(d) - size), d))
                new = ranked[0]
                exact = size_of(new) == size
                how = 'destructor kind, ' + ('size match' if exact else 'closest size')
                report['destructor_choices'].append({
                    'rva': hex(rva), 'bound': new, 'size': size,
                    'candidates': [{'symbol': d, 'size': size_of(d)} for d in ranked]})
        else:
            if new is None and old in defined:
                how, new = 'kept', old
            if new is None and community:
                hits = [d for d in defined if names(d) == community and d not in taken]
                if len(hits) == 1:
                    how, new = 'community name', hits[0]
            if new is None and community:
                hits = [d for d in defined if member(names(d)) == member(community) and d not in taken]
                if len(hits) == 1:
                    how, new = 'member name', hits[0]
        if new is None:
            candidates = sorted(d for d in defined if d not in taken)
            report['unbound_functions'].append({'rva': hex(rva), 'community_name': fn.get('community_name'),
                                                'symbol': old, 'defined_in_object': candidates[:12],
                                                'expected': spec})
            continue
        taken.add(new)
        if new != old:
            if old and not old.startswith(UNBOUND):
                report['renamed'].append({'rva': hex(rva), 'old': old, 'new': new})
                if symbols.get(old, {}).get('rva') == rva:
                    del symbols[old]
            fn['symbol'] = new
            report['changed'] = True
        entry = {'rva': rva, 'size': parse_rva(fn['size'])}
        if symbols.get(new) != entry:
            symbols[new] = entry
            found[new] = (how, fn.get('community_name'))
            report['changed'] = True
        report['functions'].append({'rva': hex(rva), 'symbol': new, 'how': how})

    bound_at = {parse_rva(f['rva']): f['symbol'] for f in report['functions']}
    for h, r in hints.items():
        # A hint at a compared function's RVA is meant to name it; one that does not must be seen.
        if r not in {parse_rva(f['rva']) for f in task['functions']}:
            continue
        got = bound_at.get(r)
        if got is not None and (got == h or names(got) == h):
            continue
        hits = [d for d in defined if d == h or names(d) == h]
        reason = ('not defined in the compiled object' if not hits else
                  f'matches {len(hits)} definitions' if len(hits) > 1 else f'{hex(r)} was bound to {got} instead')
        if not hits and dtor_decoration(h) and dtor_decoration(h)[0] != '??1':
            reason += ('; the compiler emits a deleting destructor only beside the vftable, i.e. in a unit '
                       'that defines a constructor or otherwise references the vftable')
        report['ignored_hints'].append({'hint': h, 'rva': hex(r), 'reason': reason})
    compared = {fn['symbol']: fn for fn in task['functions'] if fn['symbol'] in defined}
    own = set(compared)
    defined_sections = set(defined.values())
    for name, fn in compared.items():
        fn_rva = parse_rva(fn['rva'])
        refs = pack_references(repo, fn)
        known = {r for r, _ in refs}
        calls, places = lifetime_calls(repo, fn)
        life_known = {r for entries in calls.values() for r, _ in entries}
        life_refs = [(r, [n]) for entries in calls.values() for r, n in entries if n]
        extra = funclets(obj, defined[name], defined_sections)
        # (section, target RVA of its start or None, lifetime state or None, is a funclet)
        parts = [(defined[name], fn_rva, None, False)]
        for index, where in sorted(extra.items()):
            state = where[0] if where else None
            base = places[state] - where[1] if where and state in places else None
            parts.append((index, base, state, True))
        group = {p[0] for p in parts}
        for index, base, state, is_funclet in parts:
            pending = []
            for rel, target in outgoing(obj, index):
                ref = target.name
                if target.section in group or ref in own or ref in DIRECTORY_SYMBOLS:
                    continue
                if rel.kind == SECREL:
                    # A TLS offset is not an RVA: neither the pack's references nor the target's field
                    # name it, so only an explicit hint binds it.
                    q = names(ref)
                    key = ref if ref in tls_hints else q if q in tls_hints else None
                    if key is not None:
                        tls_used.add(key)
                    if ref in symbols:
                        continue
                    if key is None:
                        if ref not in report['unbound_thread_locals']:
                            report['unbound_thread_locals'].append(ref)
                        continue
                    symbols[ref] = {'kind': 'thread-local', 'tls_offset': tls_hints[key], 'size': None}
                    found[ref] = ('thread-local hint', None)
                    report['references'].append({'symbol': ref, 'tls_offset': hex(tls_hints[key]),
                                                 'how': 'thread-local hint',
                                                 **({'from': 'funclet'} if is_funclet else {})})
                    report['changed'] = True
                    continue
                hinted = hint_for(ref)
                if ref in symbols and hinted is not None and symbols[ref].get('rva') != hinted:
                    # An entry bound earlier by position from a misaligned candidate can name another
                    # listed target; the Drafter's hint is the later, explicit statement.
                    report['references'].append({'symbol': ref, 'rva': hex(hinted), 'how': 'hint, replaced '
                                                 + hex(symbols[ref]['rva'])})
                    symbols[ref] = {'rva': hinted, 'size': None}
                    found[ref] = ('hint, replaced', None)
                    report['changed'] = True
                if ref not in symbols:
                    pending.append((rel, target))
            for rel, target in pending:
                ref = target.name
                if ref in symbols:  # bound earlier in this loop
                    continue
                how, value = None, hint_for(ref)
                if value is not None:
                    how = 'hint'
                accept = known | life_known if is_funclet else known
                contradicted = False
                if value is None and base is not None:
                    pos = by_position(image, base, rel)
                    if pos is not None and pos in accept:
                        how, value = ('object lifetime position' if pos in life_known and pos not in known
                                      else 'position'), pos
                    contradicted = pos is not None and pos not in accept
                if value is None:
                    q = names(ref)
                    pool = refs + life_refs if is_funclet else refs
                    for key in (q, member(q)):
                        if not key:
                            continue
                        hits = {r for r, cns in pool for c in cns if (c == key if key == q else member(c) == key)}
                        if len(hits) == 1:
                            how, value = ('community name' if key == q else 'member name'), hits.pop()
                            break
                if value is None and is_funclet and state is not None and not contradicted:
                    # An unwind funclet destroys what its state owns: when the pack lists exactly one
                    # destructor call for that state and the funclet leaves exactly one name unbound,
                    # that is the call. The comparator still checks the encoded address.
                    targets = {r for r, _ in calls.get(state, [])}
                    names_left = {t.name for _, t in pending if t.name not in symbols and hint_for(t.name) is None}
                    if len(targets) == 1 and names_left == {ref}:
                        how, value = 'object lifetime', targets.pop()
                if value is None:
                    if ref not in report['unbound_references']:
                        report['unbound_references'].append(ref)
                    continue
                symbols[ref] = {'rva': value, 'size': None}
                found[ref] = (how, None)
                report['references'].append({'symbol': ref, 'rva': hex(value), 'how': how,
                                             **({'from': 'funclet'} if is_funclet else {})})
                report['changed'] = True
    for key, offset in tls_hints.items():
        if key not in tls_used:
            report['ignored_hints'].append({'hint': key, 'rva': f'tls:{hex(offset)}',
                                            'reason': 'no SECREL reference of a compared function or funclet has that name'})
    if report['changed']:
        if public:
            publish(Path(repo), map_name, smap, before, found)
        else:
            smap_path.write_text(json.dumps(smap, indent=2) + '\n')
        (task_dir / 'task.json').write_text(json.dumps(task, indent=2) + '\n')
    return report


def provenance_entry(name, entry, found):
    """Provenance of one entry bind publishes; a thread-local entry names its offset, never an RVA."""
    how = found.get(name, ('unknown', None))[0]
    if entry.get('kind') == 'thread-local':
        return {'name': name, 'tls_offset': hex(entry['tls_offset']), 'size_from': None, 'community_name': None,
                'note': f'bound by tools/verifier/bind.py ({how}) from a tls: bind hint; the offset is the one the '
                        'target code adds to the TLS block, the decorated name is the reconstruction\'s'}
    return {'name': name, 'rva': hex(entry['rva']), 'size_from': 'task' if entry.get('size') else None,
            'community_name': found.get(name, (None, None))[1],
            'note': f'bound by tools/verifier/bind.py ({how}) from the task pack; the decorated name is the '
                    'reconstruction\'s'}


def publish(repo, map_name, smap, before, found):
    """Apply bind's edits to the repository map through tools/symbol_map.py (see the module doc)."""
    after = smap['symbols']
    touched = {n: e for n, e in after.items() if before.get(n) != e}
    incoming = {'schema': 1, 'build_id': smap.get('build_id'), 'symbols': touched,
                '_provenance': {'entries': [provenance_entry(n, e, found) for n, e in touched.items()]}}
    removed = [n for n in before if n not in after]
    symbol_maps.apply_change(repo, map_name, incoming, remove=removed, allow_unpinned_change=True)


def describe(report, task_dir):
    """Short lines for the attempt output: what was bound, renamed or is still missing, and where to fix it."""
    lines = []
    bound = [f for f in report['functions'] if f['how'] != 'kept'] + report['references']
    if bound:
        lines.append('  bound: ' + '; '.join(
            f'{b.get("rva") or "tls+" + b.get("tls_offset", "?")} {"<-" if "symbol" in b else ""} {b["symbol"][:60]} ({b["how"]})' for b in bound[:6])
            + (f' ... {len(bound) - 6} more' if len(bound) > 6 else ''))
    for r in report['renamed']:
        lines.append(f'  decorated name changed for {r["rva"]}: {r["old"]} -> {r["new"]}')
    hints = Path(task_dir) / HINTS
    for c in report.get('destructor_choices', []):
        lines.append(f'  destructor {c["rva"]} ({c["size"]} B) bound to {c["bound"]} of '
                     + ', '.join(f'{x["symbol"]} {x["size"]} B' for x in c['candidates']))
    for w in report.get('warnings', []):
        lines.append(f'  WARNING {w}')
    for h in report.get('ignored_hints', []):
        lines.append(f'  WARNING bind hint {h["hint"]} -> {h["rva"]} ignored: {h["reason"]}')
    for f in report['unbound_functions']:
        spec = f.get('expected')
        if spec:
            lines.append(f'  UNBOUND function {f["rva"]} ({f["community_name"]}): the target is a {spec["kind"]} '
                         f'({spec["evidence"]}); the object defines no {"/".join(spec["symbols"])} of the class. '
                         'A deleting destructor is emitted beside the vftable, so the unit must define a '
                         f'constructor (or otherwise reference the vftable); or add a hint to {hints}')
        else:
            lines.append(f'  UNBOUND function {f["rva"]} ({f["community_name"]}): no unique definition in the object; '
                         f'add {{"<decorated or Class::Method name>": "{f["rva"]}"}} to {hints}')
        if f['defined_in_object']:
            lines.append('    defined in object: ' + ', '.join(f['defined_in_object'][:6]))
    for name in report['unbound_references']:
        lines.append(f'  UNBOUND reference {name}: add {{"{name}": "0x<rva from the pack table>"}} to {hints}')
    for name in report.get('unbound_thread_locals', []):
        lines.append(f'  UNBOUND thread-local {name}: add {{"{name}": "tls:0x<offset>"}} to {hints}; the offset is '
                     'the displacement the target adds to the TLS block, the same for every function using it')
    return lines


def preflight(task_dirs, repo=REPO):
    """Check selected functions and private reference maps before publishing any unit."""
    declarations = {}
    for directory in task_dirs:
        directory = Path(repo) / directory
        task = json.loads((directory / 'task.json').read_text())
        entries = [(f['symbol'], {'rva': f['rva']}) for f in task['functions']]
        private_map = directory / 'symbols.json'
        if private_map.is_file():
            objects = sorted(directory.glob('attempts/[0-9][0-9][0-9]/candidate.obj'))
            active = ({s.name for s in CoffObject(objects[-1].read_bytes()).symbols.values()}
                      if objects else None)
            entries += [(name, entry) for name, entry in
                        json.loads(private_map.read_text())['symbols'].items()
                        if active is None or name in active]
        for name, entry in entries:
            if 'rva' not in entry or name.startswith(UNBOUND) or name.startswith('??_7'):
                continue
            key = (task.get('build_id'), parse_rva(entry['rva']))
            previous = declarations.setdefault(key, name)
            if previous != name:
                raise ValueError(f'conflicting symbol declarations at {key[0]} {hex(key[1])}: '
                                 f'{previous} versus {name}')


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--task')
    p.add_argument('--list', type=Path, help='preflight every task before binding any task')
    p.add_argument('--object', default=None, help='Default: the newest attempts/<NNN>/candidate.obj')
    p.add_argument('--image', default=None, help='Default: .local/verifier/config.json "image"')
    a = p.parse_args(argv)
    if a.list:
        directories = [line.strip() for line in a.list.read_text().splitlines()
                       if line.strip() and not line.lstrip().startswith('#')]
        preflight(directories)
        for directory in directories:
            result = main(['--task', directory])
            if result:
                return result
        return 0
    if not a.task:
        p.error('--task or --list is required')
    task_dir = Path(a.task)
    obj = a.object
    if obj is None:
        objs = sorted(task_dir.glob('attempts/[0-9][0-9][0-9]/candidate.obj'))
        if not objs:
            raise SystemExit(f'no attempts/*/candidate.obj under {task_dir}; pass --object')
        obj = objs[-1]
    config = {}
    cfg = REPO / '.local/verifier/config.json'
    if cfg.is_file():
        config = json.loads(cfg.read_text())
    report = bind(task_dir, obj, a.image or config.get('image'), config.get('objdump'))
    print('\n'.join(describe(report, task_dir)) or '  nothing to bind')
    return 1 if (report['unbound_functions'] or report['unbound_references'] or report['unbound_thread_locals']
                 or report['ignored_hints']) else 0


if __name__ == '__main__':
    raise SystemExit(main())
