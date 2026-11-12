"""Starting files for a reconstruction unit and a compact per-function sheet, from a task directory.

A Drafter with a small context (or a short tool-output limit) fails on paperwork and long files
more often than on code: a unit has to start with the right header lines and labels before the
lint accepts it, and the pack facts for one function are spread over several files. This module
renders both from what the pack export already wrote under `.local/`:

- `skeleton_files(task_dir)` -> (header path, header text, source path, source text): a header
  comment with every line the lint asks for, `Labels: v2` label lines for the names it declares,
  the class shell (base include or stand-ins sized from the image, community declarations of the
  compared functions) and one stub per compared function. Each stub body is the statement
  `SKELETON_TODO_BODY;`, an undeclared name, so an unfilled stub never compiles and so can never
  pass the comparator; the paperwork placeholders `SKELETON_TODO_MODEL` and `SKELETON_TODO_ORIGIN`
  are words the lint refuses in any tracked, staged or accepted file (lint_reconstruction.py,
  "skeleton not filled").
- `sheet_pages(task_dir, rva)`: one function's facts (signature, convention, references, memory
  operands, sibling pointers, listing, decompiler output) cut into pages of at most SHEET_CAP
  characters, so one page always fits one tool output.

`community_label` and `skeleton` are the contributor-flow skeleton writer's (`tools/contrib.py`
`start`) functions, kept call-compatible so that tool can import them from here instead of
carrying its own copy.
"""
import json
from pathlib import Path, PurePosixPath
import re
import sys
import textwrap

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lint_reconstruction import SKELETON_MARKER  # noqa: E402,F401 (re-exported for the CLIs and tests)

BODY_MARKER = 'SKELETON_TODO_BODY'
MODEL_MARKER = 'SKELETON_TODO_MODEL'
ORIGIN_MARKER = 'SKELETON_TODO_ORIGIN'
# One page of a sheet. Small enough for the shortest tool-output limit seen in Drafter runs
# (long instruction files came back cut off), large enough for a whole small function's listing.
SHEET_CAP = 4000

# Pinned community naming sources (SOURCES.md) that tools/check_labels.py and check_origin.py read
# from .local/sources/: repository -> (clone path, revision, licence word of its labels).
COMMUNITY_SOURCES = {
    'CharmedBaryon/CommonLibSSE-NG': ('.local/sources/CommonLibSSE-NG', 'b93280e832f263dbef44e44cbe2936622a02f91a', 'MIT'),
    'powerof3/CommonLibSSE': ('.local/sources/CommonLibSSE-po3', '654e55f7979c1733033d5dbef176e43827bac944', 'GPL-3.0'),
    'meh321/AddressLibraryDatabase': ('.local/sources/AddressLibraryDatabase', '0379cb6fdaa0d68e69ef9ad1a2d39caa6611ac91',
                                      'permission'),
}
# Shorter spellings of the same sources in pack and inventory name-source text, checked in this
# order after the full repository names (NG before po3: "CommonLibSSE" is a prefix of both).
SOURCE_ALIASES = (
    ('CommonLibSSE-NG', 'CharmedBaryon/CommonLibSSE-NG'),
    ('CommonLibSSE-po3', 'powerof3/CommonLibSSE'),
    ('powerof3', 'powerof3/CommonLibSSE'),
    ('meh321', 'meh321/AddressLibraryDatabase'),
    ('Address Library name', 'meh321/AddressLibraryDatabase'),
)
GPL_NOTE = '// Declarations derived from powerof3/CommonLibSSE are GPL-3.0 (its licence).'
BUILTIN = {'void', 'bool', 'char', 'short', 'int', 'long', 'float', 'double', 'unsigned', 'signed', 'const',
           'volatile', 'auto', 'std', 'virtual', 'static', 'inline', 'override', 'final', 'struct', 'class',
           'enum', 'typename', 'nullptr', 'true', 'false', 'wchar_t', 'char16_t', 'char32_t', 'size_t', 'RE'}


class SkeletonError(Exception):
    pass


# ------------------------------------------------------------------ inline Ni bases
#
# A deleting destructor that stores the NiRefObject vftable and decrements the object counter
# itself has the whole base chain inlined. The shared NiObject.h declares ~NiRefObject and
# ~NiObject out of line, so a unit that includes it gets a call to a separate base destructor
# instead and misses by a few bytes. Such units get local stand-ins with inline destructors, the
# form of the accepted reconstruction/netimmerse/NiExtraData.h and NiInterpolator.h.
INLINE_BASE_REFS = ('VTABLE_NiRefObject', 'NiRefObject::TotalObjectCount')
INLINE_BASE_ROOTS = ('NiRefObject', 'NiObject')
_NG = 'COMMUNITY(CharmedBaryon/CommonLibSSE-NG@b93280e, MIT)'
# Opaque declarations from the pinned NG headers: no object layout or enum values inferred.
# BSTEvent.h, NiPointer.h, NiAllocator.h, BSStorage.h and BSIMusicTrack.h.
SUPPORT_DECLARATIONS = {
    'BSTEventSource': 'template <class Event> class BSTEventSource;',
    'NiPointer': 'template <class T> class NiPointer;',
    'BSEventNotifyControl': 'enum class BSEventNotifyControl : int;',
    'NiMemEventType': 'enum class NiMemEventType : int;',
    'BSStorageDefs::ErrorCode': 'namespace BSStorageDefs { enum class ErrorCode : int; }',
    'BSStorageDefs::SeekMode': 'namespace BSStorageDefs { enum class SeekMode : int; }',
    'TrackType': 'enum class TrackType : std::uint32_t;',
}
_NI_SLOTS = [
    ('const NiRTTI*', 'GetRTTI() const'), ('NiNode*', 'AsNode()'), ('NiSwitchNode*', 'AsSwitchNode()'),
    ('BSFadeNode*', 'AsFadeNode()'), ('BSMultiBoundNode*', 'AsMultiBoundNode()'), ('BSGeometry*', 'AsGeometry()'),
    ('NiTriStrips*', 'AsTriStrips()'), ('BSTriShape*', 'AsTriShape()'),
    ('BSSegmentedTriShape*', 'AsSegmentedTriShape()'), ('BSSubIndexTriShape*', 'AsSubIndexTriShape()'),
    ('BSDynamicTriShape*', 'AsDynamicTriShape()'), ('NiGeometry*', 'AsNiGeometry()'),
    ('NiTriBasedGeom*', 'AsNiTriBasedGeom()'), ('NiTriShape*', 'AsNiTriShape()'), ('NiParticles*', 'AsParticlesGeom()'),
    ('BSLines*', 'AsLinesGeom()'), ('bhkNiCollisionObject*', 'AsBhkNiCollisionObject()'),
    ('bhkBlendCollisionObject*', 'AsBhkBlendCollisionObject()'),
    ('bhkAttachmentCollisionObject*', 'AsBhkAttachmentCollisionObject()'), ('bhkRigidBody*', 'AsBhkRigidBody()'),
    ('bhkLimitedHingeConstraint*', 'AsBhkLimitedHingeConstraint()'),
    ('NiObject*', 'CreateClone(NiCloningProcess& a_cloning)'), ('void', 'LoadBinary(NiStream& a_stream)'),
    ('void', 'LinkObject(NiStream& a_stream)'), ('bool', 'RegisterStreamables(NiStream& a_stream)'),
    ('void', 'SaveBinary(NiStream& a_stream)'), ('bool', 'IsEqual(NiObject* a_object)'),
    ('void', 'ProcessClone(NiCloningProcess& a_cloning)'), ('void', 'PostLinkObject(NiStream& a_stream)'),
    ('bool', 'StreamCanSkip()'), ('const NiRTTI*', 'GetStreamableRTTI() const'),
    ('std::uint32_t', 'GetBlockAllocationSize() const'), ('NiObjectGroup*', 'GetGroup() const'),
    ('void', 'SetGroup(NiObjectGroup* a_group)'), ('NiControllerManager*', 'AsNiControllerManager()'),
]
INLINE_BASE_FORWARD = sorted({ret.rstrip('*').split()[-1] for ret, _ in _NI_SLOTS if ret.endswith('*')}
                             | {'NiStream', 'NiCloningProcess', 'NiObjectGroup'})


def inline_base_blocks():
    """The NiRefObject and NiObject stand-ins with inline destructors, as header text."""
    names = [sig.split('(')[0] for _, sig in _NI_SLOTS]
    slots = [f'    virtual {ret} {sig};  // {i:02X}' for i, (ret, sig) in enumerate(_NI_SLOTS, 2)]
    return '\n'.join([
        f'// NiRefObject: STANDIN {_NG}',
        f'// ~NiRefObject, DeleteThis, _refCount, _pad0C: {_NG}',
        '// ms_totalObjects: GUESS(low); NG reaches the counter through GetTotalObjectCount()',
        'class NiRefObject',
        '{',
        'public:',
        '    // Inline because the target inlines it into the compared deleting destructor.',
        '    virtual ~NiRefObject()',
        '    {',
        '        // hot path: the engine drops the shared object counter atomically on every destruction',
        '        _InterlockedDecrement(&ms_totalObjects);',
        '    }',
        '    virtual void DeleteThis();  // 01',
        '',
        '    static volatile long ms_totalObjects;',
        '',
        '    std::uint32_t _refCount{ 0 };  // 08',
        '    std::uint32_t _pad0C;          // 0C',
        '};',
        'static_assert(sizeof(NiRefObject) == 0x10, "NiRefObject size");',
        '',
        f'// NiObject: STANDIN {_NG} EXE_RTTI',
        '// Slots in NG\'s order, declared without bodies (only the order matters here).',
        f'// ~NiObject, {", ".join(names)}: {_NG}',
        'class NiObject : public NiRefObject',
        '{',
        'public:',
        '    // Inline (empty) for the same reason as ~NiRefObject.',
        '    ~NiObject() override {}  // 00',
        *slots,
        '};',
        'static_assert(sizeof(NiObject) == 0x10, "NiObject size");',
        ''])


def inlines_ni_base(fn):
    """True when a compared deleting destructor does the NiRefObject cleanup itself (its references
    include the NiRefObject vftable or the object counter), so no base destructor is called."""
    kind = (fn.get('destructor') or {}).get('kind') or ''
    if 'deleting' not in kind:
        return False
    refs = readme_section(fn.get('readme') or '', 'References leaving the function')
    return any(marker in refs for marker in INLINE_BASE_REFS)


# ------------------------------------------------------------------ labels

def community_label(name_source):
    """The COMMUNITY(...) label an inventory or pack name source supports, and its licence word."""
    text = name_source or ''
    repo = next((r for r in COMMUNITY_SOURCES if r in text), None)
    if repo is None:
        repo = next((full for alias, full in SOURCE_ALIASES if alias in text), None)
    if repo is None:
        return None, None
    _path, rev, licence = COMMUNITY_SOURCES[repo]
    return f'COMMUNITY({repo}@{rev[:7]}, {licence})', licence


def is_gpl(label):
    return bool(label) and 'GPL' in label


# ------------------------------------------------------------------ the contributor-flow writer

def skeleton(fn, cls, method, area, drafted_by, recipe):
    """(.h text, .cpp text) of a new one-function unit, as tools/contrib.py `start` writes it: the
    signature is a placeholder and the body empty. Kept for that caller; task directories use
    `skeleton_files`, which knows signatures and refuses to compile until a body is written."""
    target = fn['build_id']
    label, licence = community_label(fn.get('name_source'))
    label = label or 'GUESS(low)'
    gpl = licence and 'GPL' in licence
    lic_line = [GPL_NOTE] if gpl else []
    is_dtor = method.startswith('~')
    decl = f'virtual {method}();' if is_dtor else f'void {method}();'
    h = '\n'.join([
        f'// Type declarations for the {cls} translation unit (build {target}).',
        '//',
        '// Labels: v2',
        '// Source exposure: binary-analysis (a local listing of the contributor\'s own copy of the pinned image).',
        *lic_line,
        '// Community names are unverified. Only the members the compared code needs are declared.',
        f'// {cls}: {label}',
        f'// {method}: {label}',
        '#pragma once',
        '',
        f'class {cls} {{',
        'public:',
        '    // Placeholder signature: replace the return and parameter types with the real ones.',
        f'    {decl}',
        '};',
        ''])
    cpp = '\n'.join([
        f'// {cls}::{method}, build {target}, RVA 0x{fn["rva"]:x}, {fn["size"]} bytes.',
        '//',
        '// Labels: v2',
        f'// Evidence: {fn["evidence"]}.',
        f'// Source exposure: binary-analysis. Drafted by {drafted_by}.',
        *lic_line,
        '// A byte match shows that this source and recipe produce the checked code; it does not verify the',
        '// community name or that the original source looked like this.',
        f'// Recipe: {recipe} (compile this file alone).',
        f'// Only {method} is compared.',
        f'#include "{cls}.h"',
        '',
        f'{cls}::{method}()' if is_dtor else f'void {cls}::{method}()',
        '{',
        '}',
        ''])
    return h, cpp


# ------------------------------------------------------------------ task directory inputs

def load_unit(task_dir, repo=None):
    """The facts a skeleton or sheet needs from a unit task directory and the packs it names."""
    repo = Path(repo or REPO)
    task_dir = Path(task_dir)
    try:
        task = json.loads((task_dir / 'task.json').read_text())
    except (OSError, ValueError) as exc:
        raise SkeletonError(f'{task_dir}: no readable task.json ({exc}); give a unit task directory, '
                            'not a group directory') from None
    compiled = task.get('compiled') or ''
    m = re.fullmatch(r'reconstruction/([a-z][a-z0-9_]*)/([A-Z][A-Za-z0-9_]*)\.cpp', compiled)
    if not m:
        raise SkeletonError(f'{task_dir}/task.json: compiled must be reconstruction/<area>/<Class>.cpp')
    brief_path = task_dir / 'BRIEF.md'
    brief = brief_path.read_text() if brief_path.is_file() else ''
    material = [Path(repo) / p for p in (task.get('export') or {}).get('class_material', [])]
    functions = []
    for f in task.get('functions') or []:
        pack = Path(repo) / f['pack'] if f.get('pack') else None
        functions.append(dict(f, pack_dir=pack, pack_json=_json(pack / 'pack.json') if pack else {},
                              readme=_text(pack / 'README.md') if pack else ''))
    return {'dir': task_dir, 'task': task, 'area': m.group(1), 'cls': m.group(2), 'compiled': compiled,
            'header': f'reconstruction/{m.group(1)}/{m.group(2)}.h', 'brief': brief,
            'material': material, 'functions': functions}


def _json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return {}


def _text(path):
    try:
        return Path(path).read_text()
    except OSError:
        return ''


def brief_evidence(brief):
    m = re.search(r'Evidence: cite `((?:findings|reports)/[^`]+)`', brief)
    return m.group(1) if m else None


def brief_shared_headers(brief):
    """{class: include path} from the brief's "Shared headers" list."""
    return dict(re.findall(r'^- `(\w+)`: `#include "([^"]+)"`', brief, re.M))


def class_chain(material_dirs, cls):
    """(bases of each class, size of each class) from the class material's skeleton.h, which the
    pack export derives from the image RTTI and the operator delete size of each class."""
    bases, sizes = {}, {}
    for d in material_dirs:
        text = _text(Path(d) / 'skeleton.h')
        for m in re.finditer(r'^(?:class|struct)\s+(\w+)(?:\s*:\s*([^{\n]+))?\s*$', text, re.M):
            bases.setdefault(m.group(1), re.findall(r'(?:public|protected|private)\s+(?:virtual\s+)?:*(\w+)',
                                                    m.group(2) or ''))
        for m in re.finditer(r'static_assert\(sizeof\((\w+)\)\s*==\s*(0x[0-9A-Fa-f]+|\d+)', text):
            sizes.setdefault(m.group(1), int(m.group(2), 0))
    return bases, sizes


def ancestors(bases, cls):
    out, seen, cur = [], {cls}, cls
    while bases.get(cur):
        cur = bases[cur][0]
        if cur in seen:
            break
        seen.add(cur)
        out.append(cur)
    return out


def excerpt_label(material_dirs, packs):
    """Label of the community class declaration the pack quotes (its first line names the source)."""
    for d in list(material_dirs) + list(packs):
        first = _text(Path(d) / 'class-excerpt.h').split('\n', 1)[0]
        if first:
            label, _ = community_label(first)
            if label:
                return label
    return None


def community_declaration(fn, material_dirs, method):
    decl = re.search(r'Community declaration: `([^`]+)`', fn.get('readme') or '')
    if decl:
        return decl.group(1)
    for d in material_dirs:
        lines = _text(Path(d) / 'skeleton.h').splitlines()
        for i, line in enumerate(lines):
            if re.search(rf'//\s*\w+::{re.escape(method)}:', line) and i + 1 < len(lines):
                m = re.search(r'community declaration:\s*(.+)$', lines[i + 1])
                if m:
                    return m.group(1).strip()
    return None


# ------------------------------------------------------------------ declarations

def split_declaration(decl):
    """(return type, parameter text, trailing qualifiers, is virtual, is static) of a one-line
    community declaration, or None when it is not a plain function declaration."""
    code = re.sub(r'\[\[[^\]]*\]\]', ' ', decl.split('//', 1)[0])
    code = re.sub(r'\{.*\}\s*;?\s*$', '', code).strip().rstrip(';').strip()
    code = re.sub(r'\bRE::', '', code)
    # The pinned recipe is C++14; use byte-sized storage for C++17 byte pointer declarations.
    code = code.replace('std::byte', 'std::uint8_t')
    open_ = code.find('(')
    if open_ < 0:
        return None
    depth, close = 0, -1
    for i in range(open_, len(code)):
        depth += {'(': 1, ')': -1}.get(code[i], 0)
        if depth == 0:
            close = i
            break
    if close < 0:
        return None
    head, params, tail = code[:open_].strip(), code[open_ + 1:close].strip(), code[close + 1:]
    virtual = bool(re.search(r'\b(virtual|override)\b', code))
    static = bool(re.search(r'\bstatic\b', head))
    head = re.sub(r'\b(virtual|static|inline|constexpr|explicit)\b', ' ', head)
    words = head.split()
    if len(words) < 2:
        return None
    ret = ' '.join(words[:-1]).replace(' *', '*').replace(' &', '&')
    tail = re.sub(r'\b(override|final)\b|=\s*0\b|=\s*default\b|=\s*delete\b', ' ', tail)
    quals = ' '.join(tail.split())
    params = '' if params == 'void' else ' '.join(params.split())
    return ret, params, quals, virtual, static


def without_defaults(params):
    out, depth, cur = [], 0, ''
    for ch in params + ',':
        if ch in '(<':
            depth += 1
        elif ch in ')>':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur.split('=', 1)[0].strip())
            cur = ''
        else:
            cur += ch
    return ', '.join(p for p in out if p)


def base_constructor(text, base):
    """Parameters of the included base's first declared constructor when it has no default one
    (a derived constructor must then pass them on), else None."""
    found = [m.group(1).strip() for m in re.finditer(rf'^\s*(?:explicit\s+)?{re.escape(base)}\s*\(([^)]*)\)\s*;',
                                                     text, re.M)]
    if not found or any(f in ('', 'void') for f in found):
        return None
    return ' '.join(found[0].split())


def argument_names(params):
    return [re.findall(r'(\w+)\s*(?:\[[^\]]*\])?$', p.strip())[0] for p in without_defaults(params).split(',')
            if re.findall(r'(\w+)\s*(?:\[[^\]]*\])?$', p.strip())]


def type_names(text):
    """(names used through a pointer or reference, names used by value) in a declaration part."""
    by_ref, by_value = [], []
    for m in re.finditer(r'(?<![\w:])((?:[A-Za-z_]\w*::)*[A-Za-z_]\w*)(\s*[*&])?', text):
        name, indirect = m.group(1), m.group(2)
        first = name.split('::')[0]
        if first in BUILTIN or name.startswith('std::') or not first[:1].isupper() or re.fullmatch(r'a_\w+', name):
            continue
        (by_ref if indirect else by_value).append(name)
    return by_ref, by_value


# ------------------------------------------------------------------ the skeleton

def method_of(fn, cls):
    name = fn.get('community_name') or ''
    method = name.split('::')[-1] if '::' in name else name
    if method in ('ctor', cls):
        return 'ctor'
    if method.startswith('~') or method in ('dtor', 'Destructor'):
        return 'dtor'
    return method


def plan(unit, repo=None):
    """Everything both files say, computed once so the header and the source agree."""
    repo = Path(repo or REPO)
    cls, task = unit['cls'], unit['task']
    packs = [f['pack_dir'] for f in unit['functions'] if f.get('pack_dir')]
    bases, sizes = class_chain(unit['material'], cls)
    chain = ancestors(bases, cls)
    shared = brief_shared_headers(unit['brief'])
    if not shared:
        shared = {p.stem: '../' + p.relative_to(Path(repo) / 'reconstruction').as_posix()
                  for p in (Path(repo) / 'reconstruction').glob('*/*.h') if p.stem != cls}
    # The inline form needs the chain to end in NiObject -> NiRefObject, the only roots it writes.
    inline_base = (chain[-2:] == list(reversed(INLINE_BASE_ROOTS))
                   and any(inlines_ni_base(f) for f in unit['functions']))
    include, standins = None, []
    for anc in chain:
        shared_path = (repo / unit['header']).parent / shared[anc] if anc in shared else None
        if (shared_path and shared_path.is_file() and '// TODO type ' not in _text(shared_path)
                and not inline_base):
            include = (anc, shared[anc])
            break
        standins.append(anc)
    if include is None:
        # No ancestor has a header (or the inline form needs every base local): the whole chain
        # becomes stand-ins up to its root.
        standins = list(chain)
    standins.reverse()
    included_text = ''
    if include:
        path = (Path(repo) / unit['header']).parent / include[1]
        included_text = _text(path)
    elif inline_base:
        included_text = inline_base_blocks() + '\n'.join(f'class {t};' for t in INLINE_BASE_FORWARD)
    class_label = excerpt_label(unit['material'], packs)
    members = []
    for f in unit['functions']:
        ident = (f.get('pack_json') or {}).get('identity') or {}
        label, _ = community_label(ident.get('name_source'))
        method = method_of(f, cls)
        decl = None if method in ('ctor', 'dtor') else community_declaration(f, unit['material'], method)
        members.append({'fn': f, 'method': method, 'label': label, 'decl': decl,
                        'parts': split_declaration(decl) if decl else None})
        class_label = class_label or label
    # Repeated bare `dtor` names are not evidence that distinct RVAs are one C++ destructor.
    # Keep each address separately draftable without inventing subobject ownership or a signature.
    ambiguous = [m for m in members if m['method'] == 'dtor' and not m['fn'].get('destructor')]
    if len(ambiguous) > 1:
        for m in ambiguous:
            rva = m['fn']['rva']
            rva = int(rva, 16) if isinstance(rva, str) else rva
            m.update(method=f'UnknownDtor_{rva:x}', label=None)
    return {'cls': cls, 'task': task, 'chain': chain, 'bases': bases, 'sizes': sizes, 'include': include,
            'included_text': included_text, 'standins': standins, 'class_label': class_label,
            'inline_base': inline_base,
            'members': members, 'rtti': bool(chain) or cls in sizes}


def defined_in(text, name):
    return bool(re.search(rf'\b(?:class|struct|enum(?:\s+class|\s+struct)?|using|typedef)\s+{re.escape(name)}\b', text))


def skeleton_files(task_dir, drafted_by=None, repo=None):
    """(header path, header text, source path, source text) for a unit task directory."""
    repo = Path(repo or REPO)
    unit = load_unit(task_dir, repo)
    p = plan(unit, repo)
    cls, build = p['cls'], unit['task'].get('build_id')
    task_id = unit['task'].get('task_id') or Path(task_dir).name
    recipe = unit['task'].get('recipe')
    evidence = brief_evidence(unit['brief'])
    labels = {}  # label text -> names, in first-seen order

    def add(names, label):
        labels.setdefault(label, [])
        for n in names if isinstance(names, list) else [names]:
            if n not in labels[label]:
                labels[label].append(n)

    if p['class_label']:
        add(cls, p['class_label'] + (' EXE_RTTI' if p['rtti'] else ''))
    elif p['rtti']:
        add(cls, 'EXE_RTTI')
    else:
        add(cls, 'GUESS(low)')
    for s in p['standins']:
        if not (p['inline_base'] and s in INLINE_BASE_ROOTS):  # those blocks carry their own labels
            add(s, 'STANDIN EXE_RTTI')

    forward, todo_types, decls, defs, notes = [], [], [], [], []
    event_types = set()
    has_ctor = any(m['method'] == 'ctor' for m in p['members'])
    has_dtor = any(m['method'] == 'dtor' for m in p['members'])
    ctor_params = base_constructor(p['included_text'], p['include'][0]) if p['include'] else None
    if has_dtor and not has_ctor:
        params = ctor_params or ''
        init = ''
        if ctor_params:
            direct = p['standins'][-1] if p['standins'] else p['include'][0]
            init = f'\n    : {direct}({", ".join(argument_names(ctor_params))})'
        decls.append(f'{cls}({params});')
        defs.append('\n'.join([
            '// Not compared: defined so that the compiler emits the vftable and, beside it, the',
            '// deleting destructor that is compared (cookbook rule 14).',
            f'{cls}::{cls}({without_defaults(params)}){init}',
            '{',
            '}']))
    for m in p['members']:
        f, method = m['fn'], m['method']
        rva, size = int(str(f['rva']), 16) if isinstance(f['rva'], str) else f['rva'], f['size']
        where = f'RVA 0x{rva:x}, {size} bytes, {f.get("community_name")}'
        kind = (f.get('destructor') or {}).get('kind')
        if method == 'ctor':
            if m['label']:
                # Labelled under the name the community source gives the function (meh321's list
                # calls constructors `ctor`), which is the name check_labels.py can find there.
                add(f'{f.get("community_name")}', m['label'])
            decls.append(f'{cls}();  // compared: 0x{rva:x}')
            head = f'{cls}::{cls}()'
        elif method == 'dtor':
            if m['label']:
                add(f'{cls}::~{cls}', m['label'])
            decls.append(f'virtual ~{cls}();  // compared: 0x{rva:x}' + (f' ({kind})' if kind else ''))
            head = f'{cls}::~{cls}()'
            if kind and 'deleting' in kind and p['inline_base']:
                where += (f'; compared as the {kind}. The target does the NiRefObject cleanup itself, so keep '
                          'this empty definition and the constructor: the inline base destructors in the header '
                          'make the compiler produce the same body')
            elif kind and 'deleting' in kind:
                where += (f'; compared as the {kind}. If the target calls a separate destructor, keep only '
                          'the declaration and delete this definition (cookbook rule 18)')
        elif m['parts']:
            ret, params, quals, virtual, static = m['parts']
            if m['label']:
                add(f'{cls}::{method}', m['label'])
            prefix = 'static ' if static else 'virtual ' if virtual else ''
            decls.append(f'{prefix}{ret} {method}({params}){" " + quals if quals else ""};  // compared: 0x{rva:x}')
            head = f'{ret} {cls}::{method}({without_defaults(params)}){" " + quals if quals else ""}'
            by_ref, by_value = type_names(f'{ret} ({params})')
            for t in SUPPORT_DECLARATIONS:
                if t in by_ref + by_value and not defined_in(p['included_text'], t):
                    event_types.add(t)
                    add(t, 'STANDIN ' + _NG)
            for t in by_ref:
                if t in event_types:
                    continue
                if '::' in t:
                    todo_types.append((t, 'nested type: declare a stand-in for it or change the type'))
                elif (t != cls and t not in forward and not defined_in(p['included_text'], t)
                      and t not in (INLINE_BASE_FORWARD if p['inline_base'] else ())):
                    forward.append(t)
                    if m['label']:
                        add(t, 'STANDIN ' + m['label'])
            for t in by_value:
                if (t != cls and t not in event_types and t not in forward
                        and not defined_in(p['included_text'], t) and t not in (x for x, _ in todo_types)):
                    todo_types.append((t, 'used by value: declare it (an enum or a small class) before the class'))
        else:
            if m['label']:
                add(f'{cls}::{method}', m['label'])
            else:
                add(f'{cls}::{method}', 'GUESS(low)')
            decls.append(f'void {method}();  // compared: 0x{rva:x}; TODO signature: no community declaration, '
                         'read it from the listing')
            head = f'void {cls}::{method}()'
        if method == 'dtor' and p['inline_base'] and kind and 'deleting' in kind:
            # Nothing to write: the empty body plus the inline bases is the accepted form.
            defs.append('\n'.join([*comment_lines(f'Body done: {where}.'), head, '{', '}']))
            continue
        defs.append('\n'.join([*comment_lines(f'TODO body: {where}.'), head, '{', f'    {BODY_MARKER};', '}']))

    # Stand-ins and the class itself, padded to the image sizes so offsets line up from the start.
    pads, blocks = [], []
    parent = p['include'][0] if p['include'] else None
    # Size of the class built so far: a stand-in without a known image size adds nothing, so its
    # derived class pads from the nearest known size below it.
    running = p['sizes'].get(parent) if parent else 0x8
    for s in p['standins']:
        if p['inline_base'] and s in INLINE_BASE_ROOTS:
            if s == INLINE_BASE_ROOTS[-1]:
                blocks.append(inline_base_blocks())
            parent, running = s, 0x10
            continue
        body, assert_line, running = pad_lines(s, running, p['sizes'], pads)
        base = f' : public {parent}' if parent else ''
        inherit = [f'    using {parent}::{parent};'] if ctor_params and parent else []
        vptr = [f'    virtual ~{s}() = default;'] if parent is None else []
        if vptr:
            add(f'{s}::~{s}', 'GUESS(low)')
        blocks.append('\n'.join([f'class {s}{base}', '{', 'public:', *inherit, *vptr, *body, '};', *assert_line, '']))
        parent = s
    body, assert_line, running = pad_lines(cls, running, p['sizes'], pads)
    base = f' : public {parent}' if parent else ''
    cls_block = [f'class {cls}{base}', '{', 'public:', *[f'    {d}' for d in decls]]
    if parent is None and not any(d.startswith('virtual ') for d in decls) and p['rtti']:
        cls_block.append('    void* unknown00;  // primary vftable storage')
        pads.append('unknown00')
    if body:
        cls_block += ['', '    // TODO members: replace part of the padding with the members the bodies read,',
                      '    // keeping every offset and the size check true.', *body]
    cls_block += ['};', *assert_line, '']
    if pads:
        add(pads, 'GUESS(low)')

    gpl = any(is_gpl(label) for label in labels)
    label_lines = [f'// {", ".join(names)}: {label}' for label, names in labels.items() if names]
    header = [
        f'// {cls} declarations for build {build}.',
        '//',
        '// Labels: v2',
        f'// Task: {task_id}',
        '// Source exposure: mixed (names and declarations from community headers; base classes, sizes and',
        '// the compared functions from the pinned image).',
        *([GPL_NOTE] if gpl else []),
        '// Started from a tools/skeleton.py skeleton: stand-ins carry only what the compared code needs, and',
        '// community names are unverified.',
        *base_form_lines(p),
        *label_lines,
        '#pragma once',
        '',
        *(['#include <intrin.h>'] if p['inline_base'] else []),
        '#include <cstdint>',
        '#include <cstddef>',
    ]
    if p['include']:
        header.append(f'#include "{p["include"][1]}"')
    header.append('')
    if p['inline_base']:
        header += [f'class {t};' for t in INLINE_BASE_FORWARD] + ['']
    if forward:
        header += [f'class {t};' for t in forward] + ['']
    for t in sorted(event_types):
        header += [SUPPORT_DECLARATIONS[t], '']
    for t, why in todo_types:
        header.append(f'// TODO type {t}: {why}.')
    if todo_types:
        header.append('')
    extra_bases = p['bases'].get(cls, [])[1:]
    if extra_bases:
        header += [f'// TODO bases: the image also lists {", ".join(extra_bases)} after the first base; add them '
                   'in that order if a compared function needs them (cookbook rule 25).', '']
    header += blocks + cls_block

    compared = [f'//   RVA 0x{(int(str(m["fn"]["rva"]), 16) if isinstance(m["fn"]["rva"], str) else m["fn"]["rva"]):x}, '
                f'{m["fn"]["size"]} bytes: {m["fn"].get("community_name")}' for m in p['members']]
    source = [
        f'// {cls} functions for build {build}.',
        '//',
        '// Labels: v2',
        f'// Task: {task_id}',
        '// Source exposure: mixed (names and declarations from community headers; the listing of the pinned',
        '// image).',
        *([GPL_NOTE] if gpl else []),
        f'// Evidence: {evidence or "SKELETON_TODO_EVIDENCE (the findings/ file the brief names)"}',
        f'// Recipe: {recipe} (compile this file alone).',
        f'// Drafted by {drafted_by or MODEL_MARKER + " (the model or person who writes the bodies)"}, starting from',
        '// a tools/skeleton.py skeleton.',
        '// Compared functions:',
        *compared,
        f'// Adapted bodies: {ORIGIN_MARKER} (write "none" when attempt prints no "origin advice" line;',
        '// otherwise name each adapted body, its upstream file, revision and licence).',
        '// A byte match shows that this source and recipe produce the checked code; it does not verify the',
        '// community names or that the original source looked like this.',
        f'#include "{cls}.h"',
        '',
        '\n\n'.join(defs),
        '',
    ]
    return unit['header'], '\n'.join(header), unit['compiled'], '\n'.join(source)


def base_form_lines(p):
    """Header comment lines saying which base form the skeleton chose, and why."""
    if p['inline_base']:
        return comment_lines('Base form: inline stand-ins. The compared deleting destructor does the NiRefObject '
                             'cleanup itself (it stores that vftable and decrements the object counter), so '
                             'NiRefObject and NiObject are declared here with inline destructors instead of '
                             'including the shared NiObject.h, whose out-of-line destructors would add a call.')
    if p['include']:
        return comment_lines(f'Base form: shared header {p["include"][1]} for {p["include"][0]}.')
    return comment_lines('Base form: local stand-ins (no ancestor has a shared header).') if p['standins'] else []


def comment_lines(text, width=100):
    return ['// ' + line for line in textwrap.wrap(text, width - 3, break_long_words=False, break_on_hyphens=False)]


def pad_lines(cls, start, sizes, pads):
    """(padding member lines, size check lines, size after this class) for a stand-in or the unit's
    class; `start` is the size of the class below it, None when unknown."""
    size = sizes.get(cls)
    if size is None:
        return [], [], start
    if start is None or size < start:
        return [], [], None
    if size == start:
        return [], [f'static_assert(sizeof({cls}) == 0x{size:X}, "{cls} size");'], size
    # Not unkNN or padNN: the community headers use those spellings for real members, and a made-up
    # name that collides with one reads as a mislabelled community name.
    name = f'unknown{start:02X}'
    pads.append(name)
    return ([f'    std::uint8_t {name}[0x{size - start:X}];  // {start:02X}'],
            [f'static_assert(sizeof({cls}) == 0x{size:X}, "{cls} size");'], size)


def write_skeleton(task_dir, drafted_by=None, repo=None):
    """Write both files; refuse when either exists. Returns the two repository paths."""
    repo = Path(repo or REPO)
    h_rel, h_text, cpp_rel, cpp_text = skeleton_files(task_dir, drafted_by, repo)
    existing = [rel for rel in (h_rel, cpp_rel) if (Path(repo) / rel).exists()]
    if existing:
        raise SkeletonError(f'{" and ".join(existing)} already exist{"s" if len(existing) == 1 else ""}; '
                            'not overwritten. Edit the existing files, or move them to '
                            f'{Path(task_dir).as_posix()}/near-miss/ first if you want a fresh start.')
    for rel, text in ((h_rel, h_text), (cpp_rel, cpp_text)):
        path = Path(repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'x') as out:  # 'x': never replace a file created since the check above
            out.write(text)
    p = plan(load_unit(task_dir, repo), repo)
    hints = {f'{p["cls"]}::{m["method"]}': m['fn']['rva'] for m in p['members']
             if m['method'].startswith('UnknownDtor_')}
    if hints:
        hint_path = Path(task_dir) / 'bind-hints.json'
        previous = _json(hint_path)
        hint_path.write_text(json.dumps(dict(hints, **previous), indent=2) + '\n')
    return h_rel, cpp_rel


# ------------------------------------------------------------------ the sheet

def readme_section(readme, title):
    m = re.search(rf'^## {re.escape(title)}[^\n]*\n(.*?)(?=^## |\Z)', readme or '', re.S | re.M)
    return m.group(1).strip() if m else ''


def brief_rules(brief):
    m = re.search(r'Cookbook rules these listings point to[^\n]*\n((?:- [^\n]*\n?)+)', brief)
    return m.group(1).strip() if m else ''


def brief_sibling(brief):
    m = re.search(r'^#+ Sibling source[^\n]*\n(.*?)(?=^#+ |\Z)', brief, re.S | re.M)
    if not m:
        return ''
    keep = [line for line in m.group(1).splitlines() if line.startswith('- ') or line.startswith('Small named')]
    return '\n'.join(keep)


def sibling_snippet(brief, rva, repo=None, limit=40):
    """The FNV body of the same-named method the brief points to for `rva`, up to `limit` lines."""
    repo = Path(repo or REPO)
    m = re.search(rf'^- `0x{rva:x}`: `[^`]+` `((?:src|include)/[^`:]+):(\d+)`', brief, re.M)
    if not m:
        return ''
    rel = PurePosixPath(m.group(1))
    if '..' in rel.parts:
        return ''
    lines = _text(Path(repo) / '.local/sources/fnv_decomp' / rel).splitlines()
    start = int(m.group(2)) - 1
    out, depth, opened = [], 0, False
    for line in lines[start:start + limit]:
        out.append(line)
        depth += line.count('{') - line.count('}')
        opened = opened or '{' in line
        if opened and depth <= 0:
            break
    return '\n'.join(out)


def function_sheet(unit, fn, sibling=False, repo=None):
    repo = Path(repo or REPO)
    rva = int(str(fn['rva']), 16) if isinstance(fn['rva'], str) else fn['rva']
    readme = fn.get('readme') or ''
    pack = fn.get('pack_dir')
    kind = (fn.get('destructor') or {}).get('kind')
    symbol = fn.get('symbol') or ''
    out = [f'# 0x{rva:x} {fn.get("community_name")} ({fn["size"]} bytes)', '',
           f'Unit: {unit["compiled"]} (+ .h). Task dir: {Path(unit["dir"]).as_posix()}.',
           f'Compared symbol: {"not bound yet (attempt binds it from your object)" if symbol.startswith("unbound:") else symbol}.']
    if kind:
        out.append(f'Kind: {kind} (the slot-0 body, `??_G`; cookbook rules 14 and 18).')
    cautions = (fn.get('pack_json') or {}).get('cautions') or []
    if cautions:
        out.append('Cautions: ' + '; '.join(cautions) + '.')
    conv = readme_section(readme, 'Calling and return convention')
    conv = '\n'.join(line for line in conv.splitlines() if line.startswith('- '))
    out += ['', '## Signature and registers', conv or '- No community declaration; derive the signature from the listing.']
    refs = readme_section(readme, 'References leaving the function')
    refs = '\n'.join(line for line in refs.splitlines() if line.startswith('|'))
    out += ['', '## Calls and data it references (bind names to these RVAs only)', refs or '- none']
    mem = readme_section(readme, 'Observed memory operands (non-stack)')
    mem = '\n'.join(line for line in mem.splitlines() if line.startswith('|'))
    if mem:
        out += ['', '## Memory operands (offsets from the register; RCX is `this` at entry)', mem]
    rules = brief_rules(unit['brief'])
    if rules:
        out += ['', '## Cookbook rules the brief names for this unit', rules]
    sib = brief_sibling(unit['brief'])
    if sib:
        out += ['', '## Sibling (FNV; shape and names only, never offsets; label SIBLING if you take a name)', sib]
        snippet = sibling_snippet(unit['brief'], rva, repo) if sibling else ''
        if snippet:
            out += ['', '```cpp', snippet, '```']
    # Column padding is trailing blanks; dropping it keeps more of the listing on one page.
    listing = '\n'.join(line.rstrip() for line in _text(pack / 'listing.txt').splitlines()).strip() if pack else ''
    out += ['', '## Target listing', '```', listing or '(no listing in the pack)', '```']
    decomp = _text(pack / 'decompiled.c').rstrip() if pack else ''
    if decomp:
        out += ['', '## Decompiler output (a hint; often wrong in details)', '```c', decomp, '```']
    return '\n'.join(out) + '\n'


def paginate(text, cap=SHEET_CAP):
    """Pages of at most `cap` characters, cut at line ends (a longer line is cut inside)."""
    pages, cur = [], ''
    for line in text.splitlines(keepends=True):
        while len(line) > cap:
            if cur:
                pages.append(cur)
                cur = ''
            pages.append(line[:cap])
            line = line[cap:]
        if len(cur) + len(line) > cap:
            pages.append(cur)
            cur = ''
        cur += line
    if cur or not pages:
        pages.append(cur)
    return pages


def find_function(unit, rva_text):
    try:
        rva = int(rva_text, 16)
    except ValueError:
        raise SkeletonError(f'{rva_text} is not an RVA like 0x4aa860') from None
    for f in unit['functions']:
        if (int(str(f['rva']), 16) if isinstance(f['rva'], str) else f['rva']) == rva:
            return f
    listed = ', '.join(str(f['rva']) for f in unit['functions'])
    raise SkeletonError(f'0x{rva:x} is not a function of this unit (its functions: {listed})')


# Room kept on every page for the "page N of M" footer.
FOOTER_ROOM = 300


def sheet_pages(task_dir, rva_text, sibling=False, cap=SHEET_CAP, repo=None):
    repo = Path(repo or REPO)
    unit = load_unit(task_dir, repo)
    fn = find_function(unit, rva_text)
    return paginate(function_sheet(unit, fn, sibling, repo), cap - FOOTER_ROOM)


def overview(task_dir, cap=SHEET_CAP, repo=None):
    """The unit's one-page index: files, functions and the command for each function's sheet."""
    repo = Path(repo or REPO)
    unit = load_unit(task_dir, repo)
    kind = unit['task'].get('drafter_kind') or ('normal' if any(
        f['size'] > 64 for f in unit['functions']) else 'small')
    d = Path(task_dir).as_posix()
    lines = [f'# Unit {unit["cls"]} ({unit["task"].get("task_id")})', '',
             f'Files: {unit["header"]} and {unit["compiled"]}. Budget: {unit["task"].get("max_attempts")} counted attempts.',
             f'Unit kind: {kind}. Card: docs/drafter-card-{kind}.md.',
             '', '| RVA | bytes | name | sheet pages |', '|---|---|---|---|']
    for f in unit['functions']:
        n = len(paginate(function_sheet(unit, f, repo=repo), cap - FOOTER_ROOM))
        lines.append(f'| {f["rva"]} | {f["size"]} | {f.get("community_name")} | {n} |')
    lines += ['', f'Read one function: python3 tools/sheet.py {d} --function <rva> [--page N]']
    return '\n'.join(lines) + '\n'


SHEET_VARIANTS = {False: '.md', True: '.fnv.md'}


def sheet_name(rva, page, pages, sibling):
    """File name of one sheet page: sheet-0x<rva>[-p<N>].md, or .fnv.md for the FNV variant."""
    stem = f'sheet-0x{rva:x}' if pages == 1 else f'sheet-0x{rva:x}-p{page}'
    return stem + SHEET_VARIANTS[bool(sibling)]


def is_variant(path, sibling):
    return path.name.endswith('.fnv.md') == bool(sibling)


def write_sheets(task_dir, sibling=False, cap=SHEET_CAP, repo=None):
    """sheet.md (the index) and sheet-<rva>[-p<N>].md for each function, all in the task directory.

    With `sibling` the FNV variant is written instead (sheet.fnv.md, sheet-<rva>.fnv.md: the same
    pages plus the FNV body of a same-named method). The two variants live side by side because
    not every model that drafts from one queue is cleared to read FNV text; `sheets.json` records
    which variants exist so a runbook or a check can tell them apart. Returns the files written."""
    repo = Path(repo or REPO)
    unit = load_unit(task_dir, repo)
    d = Path(task_dir)
    for old in d.glob('sheet*.md'):
        if is_variant(old, sibling):
            old.unlink()
    index = d / ('sheet' + SHEET_VARIANTS[bool(sibling)])
    written = [index]
    index.write_text(overview(task_dir, cap, repo))
    for f in unit['functions']:
        rva = int(str(f['rva']), 16) if isinstance(f['rva'], str) else f['rva']
        pages = paginate(function_sheet(unit, f, sibling, repo), cap - FOOTER_ROOM)
        for i, page in enumerate(pages, 1):
            name = sheet_name(rva, i, len(pages), sibling)
            nxt = (f'\n(page {i} of {len(pages)}; next: {sheet_name(rva, i + 1, len(pages), sibling)})\n'
                   if i < len(pages) else (f'\n(page {i} of {len(pages)}, last)\n' if len(pages) > 1 else ''))
            (d / name).write_text(page + nxt)
            written.append(d / name)
    record = _json(d / 'sheets.json') or {}
    record.setdefault('variants', {})['fnv' if sibling else 'plain'] = {
        'sibling_snippets': bool(sibling), 'files': [w.name for w in written]}
    (d / 'sheets.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
    return written


def write_sheet_variants(task_dir, which=None, cap=SHEET_CAP, repo=None):
    """Write the variants `which` asks for: None both, False the plain one, True the FNV one."""
    out = []
    for sibling in ((False, True) if which is None else (bool(which),)):
        out += write_sheets(task_dir, sibling, cap, repo)
    return out
