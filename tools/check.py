"""Validate metadata and common publication mistakes; never compares Skyrim bytes."""
import argparse
from datetime import datetime
import functools
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from compare import COMPARATOR_VERSION, CONTRACT_VERSION, REPORT_SCHEMA, comparator_source_sha256, sanitized
from source_digest import DIGEST_METHOD, INCLUDE_ROOTS, recipe_flag_problem, tu_digest
from check_source_digest import include_closure, source_digest_cache
from lint_reconstruction import lint_tree
import cost_ledger
import symbol_map as symbol_maps
import compare_internal
import compare_runtime
import compare as legacy_comparator

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = set('.exe .dll .pdb .obj .o .lib .a .so .dylib .dmp .mdmp .bin .bsa .ba2 .esm .esp .esl .nif .dds .pex .hkx .ess .skse .gdt .gpr .idb .i64 .zip .7z .iso .vhdx .qcow2 .png .jpg .jpeg .pdf'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value):
    return type(value) is int and value >= 0


SHA256 = re.compile(r'[0-9a-f]{64}')
MATCH_RECORD_SCHEMA = 2
# What every compile host must have done beyond the recipe (tools/verifier/unit_build.py): the
# flag it adds to the recipe's and the environment variables it removes before compiling.
BUILD_ADDED_FLAGS = ['/showIncludes']
BUILD_CLEARED_ENV = ['CL', 'EXTERNAL_INCLUDE', 'INCLUDE', 'LIB', 'LIBPATH', '_CL_']
BUILD_FIELDS = {'claim', 'added_flags', 'cleared_environment', 'hosts'}
BUILD_HOST_FIELDS = {'command_flags', 'object_sha256', 'repository_files_opened', 'opened_equals_closure'}
REVIEW_FIELDS = {'review_record_schema', 'function_id', 'build_id', 'rva', 'size', 'source_digest_method',
                 'source_digest', 'reviewer_model', 'review_task_id', 'verdict', 'escalation_category',
                 'review_sha256', 'review_date'}
# Schema 2 adds the delta-review binding (docs/verification.md, "Stale acceptances and delta reviews").
# Schema 1 records stay valid as full reviews; tools/accept_function.py writes schema 3 (below).
REVIEW_DELTA_FIELDS = {'review_kind', 'previous_source_digest', 'previous_review_sha256',
                       'previous_code_section_sha256', 'code_section_sha256'}
# Schema 3 adds the naming tier (docs/verification.md, "Tier 2"): the Reviewer's non-blocking
# naming findings, and the `label-only` kind written without a Reviewer pass when the compared
# code section is unchanged ("Label-only re-acceptance").
REVIEW_NAMING_FIELDS = {'naming_findings'}
REVIEW_SCHEMA_FIELDS = {1: REVIEW_FIELDS, 2: REVIEW_FIELDS | REVIEW_DELTA_FIELDS,
                        3: REVIEW_FIELDS | REVIEW_DELTA_FIELDS | REVIEW_NAMING_FIELDS}
# Family records keep all ordinary source/code bindings and add the family and committed batch.
# Schema 3 remains the format for individual reviews and is not made legacy by this addition.
REVIEW_SCHEMA_FIELDS[4] = REVIEW_SCHEMA_FIELDS[3] | {'family_evidence'}
REVIEW_RECORD_SCHEMA = 3
# Records below REVIEW_RECORD_SCHEMA predate the four-check review format, so check.py accepts one
# only if it is one of the records that existed when that format took effect (commit e51d00a): this
# file lists their paths and the SHA-256 of their canonical JSON (legacy_review_digest). A list
# kept outside the records is used rather than a date bound, because `review_date` is a field of
# the record itself and a hand-written record can carry any date; to pass, a forged legacy record
# would also need an edit to this tracked tool file, which a diff shows.
LEGACY_REVIEW_RECORDS = Path(__file__).resolve().parent / 'legacy_review_records.json'
REVIEW_KINDS = {'full', 'delta'}
LABEL_ONLY = 'label-only'
REVIEW_KINDS_BY_SCHEMA = {2: REVIEW_KINDS, 3: REVIEW_KINDS | {LABEL_ONLY}, 4: {'family'}}
# Naming findings are the one free-text field published in a Reviewer record, so they are held to
# a mechanical filter against code, bytes and private paths; the Reviewer is told they are public.
MAX_NAMING_FINDINGS = 20
MAX_NAMING_FINDING_LEN = 300
NAMING_FINDING_BANNED = (
    (re.compile(r'[{}]'), 'a brace (code)'),
    (re.compile(r'```'), 'a code fence'),
    (re.compile(r'\.local\b|/Users/|/home/|(?<![A-Za-z])[A-Za-z]:[\\/]'), 'a private or absolute path'),
    (re.compile(r'[0-9A-Fa-f]{16}'), 'a run of 16 or more hex digits'),
    (re.compile(r'(?<![0-9A-Za-z])[0-9A-Fa-f]{2}(?: [0-9A-Fa-f]{2}){3}(?![0-9A-Za-z])'), 'hex byte pairs'),
    # The 0x-prefixed run is checked in naming_finding_problem: field offsets such as 0x10, 0x18, 0x20
    # read like bytes but ascend, so the run needs more than a pattern.
    (re.compile(r'(?<![0-9A-Za-z])[0-9A-Fa-f]{2}(?:\s*[,;:-]\s*[0-9A-Fa-f]{2}){3}(?![0-9A-Za-z])'),
     'separated hex byte pairs'),
    # Shorter than the 16-digit rule, but mixing digits and letters, as packed bytes do; a run right
    # after `@` is a short commit pin in a community label citation.
    (re.compile(r'(?<![0-9A-Za-z@])(?=[0-9A-Fa-f]*[0-9])(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{10,}(?![0-9A-Za-z])'),
     'a packed run of 10 or more hex digits'),
    (re.compile(r'\\[xX][0-9A-Fa-f]{2}(?:\s*\\[xX][0-9A-Fa-f]{2})'), 'escaped bytes'),
    (re.compile(r'(?<![0-9A-Za-z])~[/\\]'), 'a private or absolute path'),
    (re.compile(r'\[\s*(?:[re]?(?:ax|bx|cx|dx|si|di|bp|sp|ip)|r(?:[89]|1[0-5])[dwb]?|[xy]mm\d+)\b', re.I),
     'a bracketed register operand (disassembly)'),
    (re.compile(r'\b(?:byte|[dq]?word|[xyz]mmword|tbyte)\s+ptr\b|\bptr\s*\[', re.I), 'a ptr operand (disassembly)'),
)
# Per-function hash of the candidate's compared code sections, written by the comparator into each
# report's `candidate` block (docs/comparator-contract.md, "Report"). Records made before comparator
# version 2 lack it, so it stays optional; a delta review requires it.
CODE_SECTION_KEY = 'code_section_sha256'
REVIEW_VERDICTS = {'approve', 'reject', 'escalate'}
ESCALATION_CATEGORIES = {'none', 'provenance', 'legal', 'systemic', 'other'}
MODEL_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')
TOOLCHAIN_PIN = 'tools/verifier/pinned.sha256'
MIN_HOSTS = 2


def is_hash(value):
    return isinstance(value, str) and bool(SHA256.fullmatch(value))


def file_sha256(root, name):
    return hashlib.sha256((root / name).read_bytes()).hexdigest()


def public_path(name, prefixes, what, root):
    require(text(name), f'Match record: missing {what} path')
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts and path.parts[0] in prefixes,
            f'Match record: {what} must be under {"/".join(sorted(prefixes))}/')
    require((root / path).is_file(), f'Match record: {what} {name} does not exist')
    return path.as_posix()


def pinned_compiler_sha256(root):
    for line in (root / TOOLCHAIN_PIN).read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == 'cl.exe':
            return parts[0]
    raise ValueError(f'{TOOLCHAIN_PIN} names no cl.exe')


def check_unit(root, compiled, unit, what):
    """Require the listed translation unit to be exactly the compiled file's quoted-include closure.

    The digest only hashes the files a record lists, so an omitted header could change later without
    making the record stale; deriving the list closes that. Angle-bracket includes are toolchain and
    SDK headers outside the repository, bound by the pinned toolchain hash rather than this digest.
    """
    try:
        closure = include_closure(root, compiled)
    except (ValueError, OSError) as exc:
        raise ValueError(f'{what}: translation unit of {compiled}: {exc}') from None
    missing = sorted(set(closure) - set(unit))
    extra = sorted(set(unit) - set(closure))
    require(not missing, f'{what}: translation_unit omits files {compiled} includes: {", ".join(missing)}')
    require(not extra, f'{what}: translation_unit lists files {compiled} does not include: {", ".join(extra)}')



def check_runtime_actions(report, symbol_map):
    """Consistency of verified CRT dependencies; image proof stays private."""
    actions = (report.get('coverage') or {}).get('runtime_actions', [])
    require(isinstance(actions, list), 'Match record: runtime actions must be a list')
    keys = {'symbol', 'rva', 'size', 'iat_rva', 'module', 'import'}
    encoded = []
    for action in actions:
        require(isinstance(action, dict) and set(action) == keys
                and action['symbol'] == action['import'] == '__std_terminate'
                and action['module'] == 'vcruntime140.dll' and integer(action['size']) and action['size'] == 6
                and integer(action['rva']) and integer(action['iat_rva']),
                'Match record: invalid runtime action identity')
        entry = symbol_map['symbols'].get(action['symbol'])
        require(entry == {'rva': action['rva'], 'size': 6},
                'Match record: runtime action differs from the pinned symbol map')
        encoded.append(json.dumps(action, sort_keys=True))
    require(len(set(encoded)) == len(encoded), 'Match record: duplicate runtime action')
    return json.dumps(sorted(encoded))

def validate_match(fn, target, root=None):
    """`check_match` with the inventory entry, record and unit named in any failure."""
    try:
        return check_match(fn, target, root)
    except ValueError as exc:
        record = fn.get('report') or 'no record'
        unit = None
        try:
            unit = json.loads(((ROOT if root is None else root) / record).read_text())['source']['compiled']
        except (OSError, ValueError, KeyError, TypeError):
            pass
        raise ValueError(f'{exc} [entry {fn.get("id")}, record {record}, unit {unit or "unknown"}]') from None


def check_match(fn, target, root=None):
    """Tie a `matched` inventory entry to integrated source, pinned inputs and comparator reports.

    Every check here is repeatable from public files alone, which is all CI has: it shows that the
    published reports are consistent with the published source, recipe, toolchain pin, target
    manifest and comparator, not that a comparison against the game took place. It is checked for
    every entry that names a record, so a record awaiting review cannot go stale unnoticed; the
    Reviewer approval that acceptance also needs is validate_review (docs/verification.md).
    """
    root = ROOT if root is None else root
    record_path = public_path(fn.get('report'), {'reports'}, 'report', root)
    try:
        record = json.loads((root / record_path).read_text())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Match record: {record_path} is not JSON ({exc})') from None
    require(isinstance(record, dict) and record.get('match_record_schema') in (MATCH_RECORD_SCHEMA, 3),
            'Match record: unknown match_record_schema')
    require(record.get('function_id') == fn['id'], 'Match record: function_id is not this inventory entry')

    source = record.get('source') or {}
    require(source.get('digest_method') == DIGEST_METHOD, 'Match record: unknown source digest method')
    unit = source.get('translation_unit')
    require(isinstance(unit, list) and unit, 'Match record: translation_unit must list the source files')
    unit = [public_path(name, {'reconstruction'}, 'source file', root) for name in unit]
    require(len(set(unit)) == len(unit), 'Match record: translation_unit lists a file twice')
    compiled = source.get('compiled')
    require(compiled in unit, 'Match record: the compiled file is not part of the translation unit')
    check_unit(root, compiled, unit, 'Match record')
    digest = tu_digest(root, unit)
    require(source.get('digest') == digest, 'Match record: source digest is stale for the integrated source')

    recipe_ref = record.get('recipe') or {}
    recipe_path = public_path(recipe_ref.get('path'), {'reconstruction'}, 'recipe', root)
    recipe_sha = file_sha256(root, recipe_path)
    require(recipe_ref.get('sha256') == recipe_sha, 'Match record: recipe hash is stale')
    recipe = json.loads((root / recipe_path).read_text())
    compiler = recipe.get('compiler') or {}
    require(is_hash(compiler.get('binary_sha256')) and text(compiler.get('version')),
            'Match record: recipe does not pin a compiler hash and version')
    flags = recipe.get('flags')
    require(isinstance(flags, list) and flags and all(text(f) for f in flags), 'Match record: recipe has no flags')
    # Include-path and forced-include flags would let the compiler read headers the closure does not
    # model; the allowed roots are the closure's own INCLUDE_ROOTS, so the two cannot drift.
    problem = recipe_flag_problem(flags)
    require(problem is None, f'Match record: recipe flags: {problem}; only /I {" or /I ".join(INCLUDE_ROOTS)} '
            'may name an include path')

    pin = record.get('toolchain_pin') or {}
    require(pin.get('path') == TOOLCHAIN_PIN, f'Match record: toolchain_pin must be {TOOLCHAIN_PIN}')
    require(pin.get('sha256') == file_sha256(root, TOOLCHAIN_PIN), 'Match record: toolchain pin is stale')
    require(compiler['binary_sha256'] == pinned_compiler_sha256(root),
            'Match record: recipe compiler is not the pinned cl.exe')
    require(text(record.get('reproduction')), 'Match record: missing reproduction command')

    # The map decides resolution, placement, alias and overlap checks, so the version the runs used
    # is pinned. A record pinned to an earlier version stays valid only if that version's entries
    # are all present and unchanged (proven by rebuilding it from the current map, see
    # tools/symbol_map.py) and nothing added since could have changed the result; that last part
    # needs the reports, so it is checked after the runs below.
    map_ref = record.get('symbol_map') or {}
    map_path = public_path(map_ref.get('path'), {'reports'}, 'symbol map', root)
    map_state = symbol_maps.load_state(root, map_path)
    pinned_names = None
    if map_ref.get('sha256') != map_state.current_sha:
        try:
            pinned_names = map_state.names_for(map_ref.get('sha256'))
        except ValueError as exc:
            raise ValueError(f'Match record: {exc}') from None
    symbol_map = map_state.current
    require(symbol_map.get('schema') == 1 and symbol_map.get('build_id') == target['build_id'],
            'Match record: symbol map is for another build')

    runs = record.get('runs')
    require(isinstance(runs, list) and len(runs) >= MIN_HOSTS, f'Match record: needs at least {MIN_HOSTS} runs')
    internal = record['match_record_schema'] == 3
    first = runs[0].get('report') if isinstance(runs[0], dict) else None
    identity = first.get('comparator') if isinstance(first, dict) else None
    runtime = not internal and isinstance(identity, dict) and identity.get('version') == compare_runtime.COMPARATOR_VERSION
    engine = compare_internal if internal else compare_runtime if runtime else legacy_comparator
    require(not internal or map_ref.get('sha256') == map_state.current_sha,
            'Match record: internal prototype requires the exact current symbol map')
    identities, runtime_actions = set(), set()
    compiled_on, compared_on, symbols = set(), set(), set()
    object_hosts = {}
    current_comparator = engine.comparator_source_sha256()
    for run in runs:
        require(isinstance(run, dict) and text(run.get('compiled_on')) and text(run.get('compared_on')),
                'Match record: each run names the host that compiled and the host that compared')
        compiled_on.add(run['compiled_on'])
        compared_on.add(run['compared_on'])
        report = run.get('report')
        require(isinstance(report, dict), 'Match record: run without a comparator report')
        sanitized(without_code_section(report))
        require(report.get('report_schema') == engine.REPORT_SCHEMA and report.get('contract_version') == engine.CONTRACT_VERSION,
                'Match record: report schema or contract version differs from this comparator')
        comparator = report.get('comparator') or {}
        require(comparator.get('version') == engine.COMPARATOR_VERSION
                and comparator.get('source_sha256') == current_comparator,
                'Match record: report comes from a different comparator version; re-run it')
        require(report.get('acceptance') == 'not-evaluated', 'Match record: report was edited (acceptance)')
        require(report.get('result') == 'pass' and report.get('reason') == 'all-checks-passed',
                'Match record: report result is not pass')
        ident = report.get('function') or {}
        require(ident.get('build_id') == target['build_id'] == fn['build_id']
                and ident.get('rva') == fn['rva'] and ident.get('size') == fn['size'] and text(ident.get('symbol')),
                'Match record: report function identity differs from the inventory entry')
        if internal:
            try:
                compare_internal.check_internal_identity({
                    'task_schema': 2, 'symbol': ident['symbol'], 'internal_identity': ident.get('internal_identity'),
                    'source_revision': digest, 'source_path': compiled})
            except compare_internal.Reject as exc:
                raise ValueError(f'Match record: invalid internal identity: {exc.detail}') from None
            identity = ident['internal_identity']
            require(identity['object_sha256'] == (report.get('candidate') or {}).get('object_sha256'),
                    'Match record: internal identity names another object')
            identities.add(json.dumps({k: v for k, v in identity.items() if k != 'object_sha256'}, sort_keys=True))
            symbols.add(identity['map_key'])
        else:
            require('internal_identity' not in ident, 'Match record: internal identity needs schema 3')
            symbols.add(ident['symbol'])
        src = report.get('source') or {}
        require(src.get('source_revision') == digest and src.get('path') == compiled,
                'Match record: report was produced from other source than the integrated file')
        tgt = report.get('target') or {}
        require(tgt.get('image_sha256') == tgt.get('expected_image_sha256') == target['image_sha256'],
                'Match record: report target image is not the pinned image')
        used = report.get('recipe') or {}
        require(used.get('recipe_sha256') == recipe_sha and used.get('compiler_binary_sha256') == compiler['binary_sha256']
                and used.get('compiler_version') == compiler['version'] and used.get('flags') == flags,
                'Match record: report recipe differs from the pinned recipe')
        require(is_hash((report.get('candidate') or {}).get('object_sha256')),
                'Match record: report does not name its candidate object')
        object_hosts.setdefault(report['candidate']['object_sha256'], set()).add(run['compiled_on'])
        cov = report.get('coverage') or {}
        if internal or runtime:
            runtime_actions.add(check_runtime_actions(report, symbol_map))
        require(cov.get('code_bytes_total') == fn['size']
                and integer(cov.get('code_bytes_exact')) and integer(cov.get('code_bytes_by_reference'))
                and cov['code_bytes_exact'] + cov['code_bytes_by_reference'] == fn['size']
                and cov.get('unwind') in {'covered', 'none-in-range'},
                'Match record: report coverage is incomplete')
    require(not (internal or runtime) or len(runtime_actions) == 1, 'Match record: runs compared different runtime actions')
    require(not internal or len(identities) == 1, 'Match record: runs compared different internal identities')
    require(len(symbols) == 1, 'Match record: runs compared different symbols')
    if pinned_names is not None:
        problem = symbol_maps.carry_forward_problem(map_state, pinned_names, fn['rva'], fn['size'],
                                                    [run['report'] for run in runs])
        require(problem is None, f'Match record: symbol map hash is stale: {problem}')
    entry = (symbol_map.get('symbols') or {}).get(next(iter(symbols)))
    require(isinstance(entry, dict) and entry.get('rva') == fn['rva'] and entry.get('size') == fn['size'],
            'Match record: symbol map does not place the function at the inventory range')
    # The pin says which map version the runs used; only the comparator's own hash of the bytes it
    # read shows that they did.
    require(all(run['report'].get('symbol_map_sha256') == map_ref.get('sha256') for run in runs),
            'Match record: a report did not read the pinned symbol map (symbol_map_sha256 differs from the pin)')
    require(len(compiled_on) >= MIN_HOSTS and len(compared_on) >= MIN_HOSTS,
            f'Match record: runs must come from at least {MIN_HOSTS} compile hosts and {MIN_HOSTS} compare hosts')
    # Host names are self-reported. Without /Brepro, two clean compiles do not yield the same object
    # (COFF time stamp and path records differ), so one object under two compile hosts means one
    # run was relabelled, not repeated. A deterministic recipe would trip this and needs a gate change.
    shared = sorted(h for hosts in object_hosts.values() if len(hosts) > 1 for h in hosts)
    require(not shared, f'Match record: one candidate object is claimed by compile hosts {", ".join(shared)}; '
            'runs from different hosts must have different object hashes')
    check_build(record.get('build'), flags, unit, runs)
    record_code_section(record)
    return record


def without_code_section(report):
    """The report with its code-section hash set aside for `sanitized`, which allows hex only in
    the comparator's own hash keys; record_code_section checks that field as a SHA-256 itself."""
    candidate = report.get('candidate')
    if not isinstance(candidate, dict) or CODE_SECTION_KEY not in candidate:
        return report
    return dict(report, candidate={k: v for k, v in candidate.items() if k != CODE_SECTION_KEY})


def record_code_section(record):
    """The per-function code-section hash the record's runs agree on, or None if they carry none.

    The section holding one function is the same for every compile of the same source and recipe
    (time stamps and object paths live elsewhere), so runs that disagree cannot both describe
    this unit. A delta review relies on this hash being unchanged between the approved record and
    the new one, so it must be all-or-nothing across runs.
    """
    values = [((run.get('report') or {}).get('candidate') or {}).get(CODE_SECTION_KEY) for run in record['runs']]
    if all(v is None for v in values):
        return None
    require(all(is_hash(v) for v in values),
            f'Match record: every run or none must give candidate.{CODE_SECTION_KEY} as a SHA-256')
    require(len(set(values)) == 1, f'Match record: runs disagree on candidate.{CODE_SECTION_KEY}')
    return values[0]


def check_build(build, flags, unit, runs):
    """Require the record's build facts to be present and consistent with its runs and unit.

    The facts are what each compile host wrote into its build record: the flags it actually passed
    to cl, the environment it cleared, the object it produced and the repository files the
    compiler reported opening. CI cannot observe a compile, so this checks that the facts are
    there, name exactly the flags and variables the verifier is defined to use, belong to the
    runs' compile hosts and objects and list this unit; it cannot check that they are true, and
    the record says so in `claim`.
    """
    require(isinstance(build, dict) and set(build) == BUILD_FIELDS,
            f'Match record: build must have exactly the fields {sorted(BUILD_FIELDS)}')
    require(text(build['claim']) and 'self-reported' in build['claim'],
            'Match record: build.claim must state that the build facts are self-reported')
    require(build['added_flags'] == BUILD_ADDED_FLAGS,
            f'Match record: build.added_flags must be {BUILD_ADDED_FLAGS}')
    require(build['cleared_environment'] == BUILD_CLEARED_ENV,
            f'Match record: build.cleared_environment must be {BUILD_CLEARED_ENV}')
    hosts = build['hosts']
    objects = {}
    for run in runs:
        objects.setdefault(run['compiled_on'], set()).add(run['report']['candidate']['object_sha256'])
    require(isinstance(hosts, dict) and set(hosts) == set(objects),
            'Match record: build.hosts must name exactly the compile hosts of the runs')
    for name, host in hosts.items():
        require(isinstance(host, dict) and set(host) == BUILD_HOST_FIELDS,
                f'Match record: build.hosts.{name} must have exactly the fields {sorted(BUILD_HOST_FIELDS)}')
        require(host['command_flags'] == flags + BUILD_ADDED_FLAGS,
                f'Match record: build.hosts.{name}.command_flags are not the recipe flags plus the added flags')
        require(objects[name] == {host['object_sha256']},
                f'Match record: build.hosts.{name}.object_sha256 is not the object its runs compared')
        require(host['opened_equals_closure'] is True and host['repository_files_opened'] == sorted(unit),
                f'Match record: build.hosts.{name} does not report opening exactly the translation unit')


def review_record_path(fn):
    """Where a function's sanitized Reviewer record lives: one per (build id, RVA), beside the reports."""
    return f'reports/{fn["build_id"]}/0x{fn["rva"]:x}.review.json'



def check_internal_admission(record):
    """Only compiler-generated initializer/teardown helpers are admitted internal functions."""
    if record.get('match_record_schema') != 3:
        return
    for run in record['runs']:
        symbol = run['report']['function']['symbol']
        require(re.fullmatch(r'\?\?__([EF]).+@@YAXXZ', symbol) is not None,
                'Internal acceptance requires a compiler-generated static initializer or teardown')

def validate_review(fn, record, root=None):
    """Require a sanitized Reviewer `approve` bound to this function and to the source the record matched.

    The record is the policy's public trace of the Reviewer step: the full review stays private under
    .local/reviews/ and is bound by its hash. Binding the function identity and the translation-unit
    digest means an approval cannot be carried over to other source or another function; any source
    change makes it stale together with the match record.
    """
    check_internal_admission(record)
    root = ROOT if root is None else root
    name = review_record_path(fn)
    require((root / name).is_file(), f'Review record: {name} is missing; matched needs a Reviewer approve')
    try:
        review = json.loads((root / name).read_text())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Review record: {name} is not JSON ({exc})') from None
    require(isinstance(review, dict) and review.get('review_record_schema') in REVIEW_SCHEMA_FIELDS,
            'Review record: unknown review_record_schema')
    expected = REVIEW_SCHEMA_FIELDS[review['review_record_schema']]
    # Only known fields: free text here would be an unreviewed publication channel.
    require(set(review) == expected, f'Review record: fields must be exactly {sorted(expected)}')
    require(review['function_id'] == fn['id'] and review['build_id'] == fn['build_id']
            and review['rva'] == fn['rva'] and review['size'] == fn['size'],
            'Review record: it reviewed another function than this inventory entry')
    require(review['source_digest_method'] == DIGEST_METHOD and review['source_digest'] == record['source']['digest'],
            'Review record: it reviewed other source than the match record binds')
    require(isinstance(review['reviewer_model'], str) and bool(MODEL_ID.fullmatch(review['reviewer_model'])),
            'Review record: names no reviewer model')
    require(isinstance(review['review_task_id'], str) and bool(re.fullmatch(r'[a-z0-9][a-z0-9-]*', review['review_task_id'])),
            'Review record: invalid review_task_id')
    require(review['verdict'] in REVIEW_VERDICTS and review['escalation_category'] in ESCALATION_CATEGORIES,
            'Review record: unknown verdict or escalation category')
    require(review['verdict'] == 'approve', f'Review record: verdict is {review["verdict"]}, not approve')
    require(review['escalation_category'] == 'none', 'Review record: an approve carries no escalation category')
    require(is_hash(review['review_sha256']), 'Review record: review_sha256 is not a SHA-256')
    date = review['review_date']
    try:
        valid_date = datetime.fromisoformat(date).date().isoformat() == date
    except (TypeError, ValueError):
        valid_date = False
    require(valid_date, 'Review record: invalid review_date')
    if review['review_record_schema'] >= 2:
        check_review_kind(review, record)
    if review['review_record_schema'] == 4:
        import family_review
        family_review.validate_public_review(root, fn, record, review)
    # Last, so a malformed legacy record is reported for what is wrong with it.
    require(review['review_record_schema'] >= REVIEW_RECORD_SCHEMA or legacy_review_allowed(name, review),
            f'Review record: {name} is schema {review["review_record_schema"]}, which is accepted only for '
            f'the unchanged records listed in tools/{LEGACY_REVIEW_RECORDS.name}; re-review it')
    return review


def legacy_review_digest(review):
    """SHA-256 of a Reviewer record's canonical JSON (sorted keys, no whitespace)."""
    return hashlib.sha256(json.dumps(review, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


@functools.lru_cache(maxsize=None)
def _legacy_review_records():
    try:
        listed = json.loads(LEGACY_REVIEW_RECORDS.read_text())['records']
    except (OSError, ValueError, KeyError, TypeError):
        return frozenset()
    return frozenset((path, digest) for path, digest in listed.items())


def legacy_review_allowed(name, review):
    """Whether a below-current-schema record is one of the listed pre-format records, unchanged."""
    return (name, legacy_review_digest(review)) in _legacy_review_records()


def naming_finding_problem(item):
    """Why one naming finding may not be published, or None (docs/verification.md, Reviewer record)."""
    if not isinstance(item, str) or not item.strip():
        return 'a naming finding must be a non-empty string'
    if len(item) > MAX_NAMING_FINDING_LEN:
        return f'a naming finding is longer than {MAX_NAMING_FINDING_LEN} characters'
    if not all(' ' <= c <= '~' for c in item):
        return 'a naming finding must be one line of printable ASCII'
    for pattern, what in NAMING_FINDING_BANNED:
        if pattern.search(item):
            return f'a naming finding holds {what}'
    if byte_run(item):
        return 'a naming finding holds 0x-prefixed byte runs'
    return None


BYTE_RUN = re.compile(r'(?<![0-9A-Za-z])0[xX][0-9A-Fa-f]{2}(?:\s*[ ,;:-]\s*0[xX][0-9A-Fa-f]{2}){3,}(?![0-9A-Za-z])')


def byte_run(item):
    """Four or more byte-sized (two-digit) `0x` values in a row, unless they strictly ascend and are
    fewer than eight: a short ascending list is field offsets, and a byte sequence that happens to
    ascend leaks at most seven bytes. One- or three-digit values are offsets or sizes, not bytes."""
    for match in BYTE_RUN.finditer(item):
        values = [int(v, 16) for v in re.findall(r'0[xX]([0-9A-Fa-f]{2})', match.group())]
        if len(values) >= 8 or any(b <= a for a, b in zip(values, values[1:])):
            return True
    return False


def check_naming_findings(findings, allow_unknown):
    """A list of publishable naming findings; `None` (not recorded) only where `allow_unknown`."""
    if findings is None:
        require(allow_unknown, 'Review record: naming_findings must be a list (empty when none are open)')
        return
    require(isinstance(findings, list) and len(findings) <= MAX_NAMING_FINDINGS,
            f'Review record: naming_findings must be a list of at most {MAX_NAMING_FINDINGS} items')
    for item in findings:
        problem = naming_finding_problem(item)
        require(problem is None, f'Review record: {problem}')


def check_review_kind(review, record):
    """Schema 2: a full review binds the record's code-section hash if it has one; a delta review
    re-approves an earlier approval from the unit diff and is valid only while the compared code
    section is the one the earlier approval saw.

    The validator sees only the tree, so the earlier record is not available here: that the
    previous hash is what the earlier match record carried, and that the earlier approve existed,
    is checked by tools/accept_function.py from the superseded review record or git history when
    it writes this record. What is checked here is that the claim is complete and agrees with the
    current record.
    """
    kind = review['review_kind']
    kinds = REVIEW_KINDS_BY_SCHEMA[review['review_record_schema']]
    require(kind in kinds, f'Review record: review_kind must be one of {sorted(kinds)}')
    if review['review_record_schema'] >= 3:
        # A label-only record carries the findings of the approval it extends, which predate the
        # field when that approval was a schema 1 or 2 record.
        check_naming_findings(review['naming_findings'], allow_unknown=kind == LABEL_ONLY)
    current = record_code_section(record)
    if kind in ('full', 'family'):
        require(review['previous_source_digest'] is None and review['previous_review_sha256'] is None
                and review['previous_code_section_sha256'] is None,
                'Review record: a full review names no previous digest, review or code-section hash')
        require(review['code_section_sha256'] == current,
                'Review record: code_section_sha256 differs from the match record')
        return
    require(is_hash(review['previous_source_digest']) and review['previous_source_digest'] != review['source_digest'],
            'Review record: a delta review needs a previous_source_digest other than source_digest')
    require(is_hash(review['previous_review_sha256']), 'Review record: a delta review needs previous_review_sha256')
    require(current is not None, f'Review record: a delta review needs a match record whose runs give '
            f'candidate.{CODE_SECTION_KEY}')
    require(review['code_section_sha256'] == current,
            'Review record: code_section_sha256 differs from the match record')
    require(review['previous_code_section_sha256'] == current,
            'Review record: the compared code section changed since the approved digest; a delta review '
            'does not cover that, a full review is needed')
    if kind == LABEL_ONLY:
        # No Reviewer read this digest: the record extends the approval it names, so it carries that
        # approval's review hash rather than one of its own.
        require(review['previous_review_sha256'] == review['review_sha256'],
                'Review record: a label-only record carries the review hash of the approval it extends '
                '(previous_review_sha256 equals review_sha256)')


STALE_UNIT = 'unit changed'
STALE_REVIEW = 'review behind'


def _json_or_none(path):
    try:
        value = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def acceptance_staleness(fn, root=None):
    """Why a `matched` entry's acceptance no longer binds the integrated source, or None.

    `unit changed`: the compiled file's include closure no longer has the digest the match record
    binds (re-confirm). `review behind`: the record is current but the Reviewer record binds an
    earlier digest (re-review, full or delta). Only digests are compared here, so a record that is
    broken for another reason is reported by check_match, not hidden behind this state.
    """
    return _staleness(fn, ROOT if root is None else root)[0]


def _staleness(fn, root):
    """(state, detail, compiled file) for acceptance_staleness and its message."""
    record = _json_or_none(root / fn['report']) if text(fn.get('report')) else None
    source = (record or {}).get('source')
    if not isinstance(source, dict) or not text(source.get('compiled')):
        return None, None, None
    compiled, unit = source['compiled'], source.get('translation_unit')
    # Paths outside reconstruction/ are a malformed record, not a unit that moved on.
    if not isinstance(unit, list) or not all(isinstance(n, str) and n.startswith('reconstruction/') for n in unit + [compiled]):
        return None, None, compiled
    try:
        digest = tu_digest(root, include_closure(root, compiled))
    except (ValueError, OSError):
        return None, None, compiled
    if digest != source.get('digest'):
        try:
            check_unit(root, compiled, unit, 'Match record')
            detail = 'Match record: source digest is stale for the integrated source'
        except ValueError as exc:
            detail = str(exc)
        return STALE_UNIT, detail, compiled
    review = _json_or_none(root / review_record_path(fn))
    if review is not None and review.get('source_digest') != digest:
        return STALE_REVIEW, 'Review record: it reviewed other source than the match record binds', compiled
    return None, None, compiled


def stale_message(fn, root=None):
    state, detail, compiled = _staleness(fn, ROOT if root is None else root)
    remedy = ('re-confirm with tools/verifier/confirm, then re-review' if state == STALE_UNIT else
              're-review (a delta review from the approved digest is allowed)')
    return (f'Stale acceptance ({state}): {detail}; {remedy} and accept with tools/accept_function.py '
            f'(docs/verification.md, "Stale acceptances and delta reviews") '
            f'[entry {fn["id"]}, record {fn.get("report")}, unit {compiled or "unknown"}]')


def check_named(fn, review):
    """Tier 2 (docs/verification.md, "Tier 2"): `named` is a boolean on a `matched` entry, and
    `true` needs a schema 3 Reviewer record with no open naming finding. The label-check half needs
    private checkouts, so tools/accept_function.py checks it when it sets the field."""
    if 'named' not in fn:
        return
    require(fn['status'] == 'matched', f'Function {fn["id"]}: named is set on an entry that is not matched')
    require(type(fn['named']) is bool, f'Function {fn["id"]}: named must be true or false')
    if fn['named'] and review is not None:
        require(review.get('review_record_schema', 0) >= 3 and review.get('naming_findings') == [],
                f'Function {fn["id"]}: named is true but its Reviewer record lists open naming findings '
                'or predates them (schema 3 with naming_findings [] needed)')


def validate(data, target, root=None, stale_ok=False):
    """Validate the inventory; `stale_ok` (for tools that are about to clear staleness) skips the
    `matched` checks of stale entries instead of failing on them: True for every entry, or a set of
    function ids that may be stale. The result is never acceptance."""
    require(data['schema_version'] == target['schema_version'] == 1, 'Unknown schema version')
    require(text(data['phase']), 'Missing phase')
    require(datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00')).utcoffset() is not None,
            'updated_at needs timezone')
    require(target['status'] in {'unselected', 'pinned'}, 'Unknown target status')
    if target['status'] == 'unselected':
        require(all(target[k] is None for k in ('build_id', 'store', 'version', 'architecture', 'image_sha256')),
                'Unselected target must not imply pinned identity')
    else:
        require(all(text(target[k]) for k in ('build_id', 'store', 'version')), 'Incomplete target identity')
        require(re.fullmatch(r'[a-z0-9][a-z0-9-]*', target['build_id']), 'Invalid build id')
        require(target['architecture'] == 'x86-64', 'Target must be Skyrim SE x86-64')
        require(isinstance(target['image_sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', target['image_sha256']),
                'Target needs SHA-256')
    require(data['target_build_id'] == target['build_id'], 'Progress and manifest targets differ')
    require(text(data['scope']['notes']), 'Missing scope notes')
    require(data['scope']['functions'] is None and data['scope']['bytes'] is None,
            'Measured scope needs a reviewed inventory/schema extension; bootstrap totals stay null')
    seen, ranges, stale = set(), [], []
    require(isinstance(data['functions'], list), 'functions must be a list')
    for fn in data['functions']:
        require(target['status'] == 'pinned', 'Pin target before recording functions')
        require(fn['build_id'] == target['build_id'], 'Function belongs to another build')
        require(text(fn['id']) and fn['id'] not in seen, 'Duplicate/missing function identity')
        seen.add(fn['id'])
        require(fn['status'] in {'mapped', 'analyzed', 'reconstructed', 'matched'}, 'Invalid function state')
        require(integer(fn['rva']) and integer(fn['size']) and fn['size'] > 0, 'Invalid function range')
        start, end = fn['rva'], fn['rva'] + fn['size']
        require(not any(start < b and a < end for a, b in ranges), 'Overlapping function ranges')
        ranges.append((start, end))
        require(text(fn['name']) and text(fn['owner']), 'Function needs name and owner')
        require(fn['name_origin'] in {'EXE_RTTI', 'COMMUNITY', 'OBSERVED', 'GUESS'}, 'Missing name provenance')
        require(text(fn['evidence']), 'Missing evidence')
        path = Path(fn['evidence'])
        require(not path.is_absolute() and '..' not in path.parts and path.parts[0] in {'findings', 'reports'},
                'Evidence must reference public findings or reports')
        require(((ROOT if root is None else root) / path).is_file(), 'Evidence does not exist')
        state = acceptance_staleness(fn, root) if fn['status'] == 'matched' else None
        if state is not None:
            # An accepted function whose unit moved on is reported by name, all at once, instead of
            # failing on the first digest check; it still blocks until re-confirmed and re-reviewed.
            if state == STALE_REVIEW:
                validate_match(fn, target, root)
            stale.append((fn['id'], stale_message(fn, root)))
            check_named(fn, None)
        elif fn['status'] == 'matched':
            check_named(fn, validate_review(fn, validate_match(fn, target, root), root))
        elif 'named' in fn:
            check_named(fn, None)
        elif fn.get('report') is not None:
            # A record awaiting review must still be consistent with the integrated tree.
            validate_match(fn, target, root)
    matched = {review_record_path(fn) for fn in data['functions'] if fn['status'] == 'matched'}
    reports = (ROOT if root is None else root) / 'reports'
    for path in sorted(reports.glob('*/*.review.json')) if reports.is_dir() else []:
        name = path.relative_to(reports.parent).as_posix()
        # A leftover approval would read as acceptance of an entry the inventory does not accept.
        require(name in matched, f'Review record: {name} belongs to no matched inventory entry')
    tolerated = (lambda _: True) if stale_ok is True else (lambda i: bool(stale_ok) and i in stale_ok)
    blocking = [message for function_id, message in stale if not tolerated(function_id)]
    require(not blocking, '; '.join(blocking))
    # A history is checked even when no record leans on it, so a forged or broken one fails early.
    for path in sorted(reports.glob('*/*.history.json')) if reports.is_dir() else []:
        name = path.relative_to(reports.parent).as_posix()
        map_name = name[:-len('.history.json')] + '.json'
        require((reports.parent / map_name).is_file(), f'{name}: no symbol map {map_name} beside it')
        symbol_maps.load_state(reports.parent, map_name)
    import family_review
    family_review.validate_metadata(ROOT if root is None else root)
    seen = set()
    for item in data['work_items']:
        require(isinstance(item['id'], str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*', item['id'])
                and item['id'] not in seen, 'Duplicate/invalid work id')
        seen.add(item['id'])
        require(item['status'] in {'planned', 'active', 'blocked', 'done'}, 'Invalid task state')
        require(all(text(item[k]) for k in ('title', 'owner', 'acceptance')), 'Incomplete work item')
        url = item['issue_url']
        require(url is None or (isinstance(url, str) and re.fullmatch(
            r'https://github\.com/awarebayes/skyrim-research/issues/[1-9][0-9]*', url)), 'Invalid issue URL')
    for event in data['milestones']:
        require(datetime.fromisoformat(event['date']).date().isoformat() == event['date'], 'Invalid date')
        require(text(event['title']) and text(event['detail']), 'Incomplete milestone')
    return data


def lint(root, names=None, skeleton_ok=()):
    """The mechanical source rules of tools/lint_reconstruction.py, as a validation failure."""
    problems = lint_tree(root, names, skeleton_ok)
    require(not problems, 'Reconstruction lint: ' + '; '.join(problems[:5])
            + (f' (and {len(problems) - 5} more)' if len(problems) > 5 else ''))


def check_index(root, data):
    """The generated status table must be what tools/build_index.py renders from this data."""
    from build_index import INDEX, render_index  # here, not at the top: build_index imports this module
    path = root / INDEX
    require(path.is_file() and path.read_text() == render_index(data, root),
            f'{INDEX} is out of date with data/progress.json and the records; run python3 tools/build_index.py')


def check_progress_svg(root):
    """The README pictures must be what tools/build_progress_svg.py (its --check) renders from this tree."""
    import build_progress_svg  # here, not at the top: it reads the same data files and is optional to load
    for name, render in (('docs/progress.svg', build_progress_svg.render),
                         ('docs/progress-map.svg', build_progress_svg.render_map)):
        path = root / name
        require(path.is_file() and path.read_text() == render(root),
                f'{name} is out of date with the tracked data; run python3 tools/build_progress_svg.py')


COST_LEDGER = 'data/costs.json'


def check_costs(root, data):
    """The cost ledger's schema and allocations (docs/costs.md), against this inventory.

    An allocation to a function the inventory no longer holds would attribute cost to nothing,
    so the ledger is checked against the same progress data as everything else here.
    """
    path = root / COST_LEDGER
    if not path.is_file():
        return
    try:
        cost_ledger.validate(json.loads(path.read_text()), data)
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f'Cost ledger {COST_LEDGER}: {exc}') from None


def load(staged=False):
    if not staged:
        data = validate(json.loads((ROOT / 'data/progress.json').read_text()),
                        json.loads((ROOT / 'builds/target.json').read_text()))
        # Tracked and not-yet-added files alike, so a Drafter's new source is linted before staging.
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z',
                                         '--', 'reconstruction'], cwd=ROOT).decode('utf-8').split('\0')
        # A skeleton placeholder marks a Drafter's unfinished unit; it is tolerated only while git
        # does not track the file, so --staged, a CI checkout and acceptance still refuse it.
        untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z',
                                             '--', 'reconstruction'], cwd=ROOT).decode('utf-8').split('\0')
        lint(ROOT, sorted({n for n in names if n and (ROOT / n).is_file()}), skeleton_ok=set(untracked) - {''})
        check_index(ROOT, data)
        check_costs(ROOT, data)
        check_progress_svg(ROOT)
        return data
    # Match records, source and recipe are checked as staged too, so the index gets its own tree.
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.check_call(['git', 'checkout-index', '--all', f'--prefix={tmp}/'], cwd=ROOT)
        root = Path(tmp)
        data = validate(json.loads((root / 'data/progress.json').read_text()),
                        json.loads((root / 'builds/target.json').read_text()), root)
        lint(root)
        check_index(root, data)
        check_costs(root, data)
        check_progress_svg(root)
        return data


# Only generated, validated inventories may grow past the ordinary publication size cap.
LARGE_INVENTORIES = {'data/progress.json', 'reconstruction/INDEX.md'}
LARGE_REPORT_INVENTORY = re.compile(
    r'reports/[a-z0-9][a-z0-9-]*/(?:symbol-map(?:\.history)?\.json|families/[^/]+\.json)')


def inspect_payload(name, payload, mode='100644'):
    path = Path(name)
    require(mode in {'100644', '100755'}, f'{name}: symlink/submodule not approved')
    require(not any(p.lower() in {'.local', 'private', 'dist'} or p.lower().endswith('.rep') for p in path.parts),
            f'{name}: private/generated path')
    require(path.suffix.lower() not in BLOCKED, f'{name}: prohibited extension')
    require(path.name.lower() not in {'.env', '.ds_store'} and not path.name.lower().startswith('.env.'),
            f'{name}: private config')
    large = name in LARGE_INVENTORIES or LARGE_REPORT_INVENTORY.fullmatch(name) is not None
    limit_mib = 32 if large else 1
    require(len(payload) <= limit_mib * 1024 * 1024, f'{name}: exceeds {limit_mib} MiB limit')
    require(b'\0' not in payload, f'{name}: binary content')
    try:
        payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError(f'{name}: non-UTF-8 content') from exc
    require(not payload.startswith(b'version https://git-lfs.github.com/spec/v1'), f'{name}: LFS prohibited')
    if large and len(payload) > 1024 * 1024 and path.suffix == '.json':
        data = json.loads(payload)
        if path.name == 'symbol-map.json':
            symbol_maps.check_map(data, name)


def index_blob(objects, sha, name):
    """Read exactly one requested blob from Git's batch protocol."""
    objects.stdin.write(sha.encode('ascii') + b'\n')
    objects.stdin.flush()
    header = objects.stdout.readline().split()
    require(len(header) == 3 and header[0] == sha.encode('ascii') and header[1] == b'blob'
            and header[2].isdigit(), f'{name}: invalid index blob response')
    size = int(header[2])
    # No permitted file exceeds this bound; inspect_payload applies its exact per-path limit.
    require(size <= 32 * 1024 * 1024, f'{name}: exceeds 32 MiB limit')
    payload = objects.stdout.read(size)
    require(len(payload) == size and objects.stdout.read(1) == b'\n', f'{name}: truncated index blob')
    return payload


def check_git(root=ROOT, staged=False):
    records = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root).split(b'\0')
    count = 0
    with subprocess.Popen(['git', 'cat-file', '--batch'], cwd=root,
                          stdin=subprocess.PIPE, stdout=subprocess.PIPE) as objects:
        for record in filter(None, records):
            meta, rawname = record.split(b'\t', 1)
            mode, sha, stage = meta.decode().split()
            name = rawname.decode('utf-8')
            require(stage == '0', f'{name}: unresolved conflict')
            # Index blobs matter: a staged binary may have been replaced by harmless text on disk.
            inspect_payload(name, index_blob(objects, sha, name), mode)
            if not staged:
                path = root / name
                require(path.is_file() and not path.is_symlink(), f'{name}: missing file/symlink')
                inspect_payload(name, path.read_bytes(), mode)
            count += 1
        objects.stdin.close()
        require(objects.wait() == 0, 'git cat-file failed')
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Check index blobs and staged metadata')
    args = parser.parse_args()
    try:
        with source_digest_cache():
            load(staged=args.staged)
        count = check_git(staged=args.staged)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print(f'PASS: metadata and {count} tracked files. No Skyrim byte comparison performed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
