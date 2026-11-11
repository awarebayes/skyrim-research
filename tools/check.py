"""Validate metadata and common publication mistakes; never compares Skyrim bytes."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from compare import COMPARATOR_VERSION, CONTRACT_VERSION, REPORT_SCHEMA, comparator_source_sha256, sanitized
from source_digest import DIGEST_METHOD, INCLUDE_ROOTS, include_closure, recipe_flag_problem, tu_digest
from lint_reconstruction import lint_tree

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
REVIEW_RECORD_SCHEMA = 1
REVIEW_FIELDS = {'review_record_schema', 'function_id', 'build_id', 'rva', 'size', 'source_digest_method',
                 'source_digest', 'reviewer_model', 'review_task_id', 'verdict', 'escalation_category',
                 'review_sha256', 'review_date'}
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
    require(isinstance(record, dict) and record.get('match_record_schema') == MATCH_RECORD_SCHEMA,
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

    # The map decides placement, alias and overlap checks, so the one the runs used is pinned too.
    map_ref = record.get('symbol_map') or {}
    map_path = public_path(map_ref.get('path'), {'reports'}, 'symbol map', root)
    require(map_ref.get('sha256') == file_sha256(root, map_path), 'Match record: symbol map hash is stale')
    symbol_map = json.loads((root / map_path).read_text())
    require(symbol_map.get('schema') == 1 and symbol_map.get('build_id') == target['build_id'],
            'Match record: symbol map is for another build')

    runs = record.get('runs')
    require(isinstance(runs, list) and len(runs) >= MIN_HOSTS, f'Match record: needs at least {MIN_HOSTS} runs')
    compiled_on, compared_on, symbols = set(), set(), set()
    object_hosts = {}
    current_comparator = comparator_source_sha256()
    for run in runs:
        require(isinstance(run, dict) and text(run.get('compiled_on')) and text(run.get('compared_on')),
                'Match record: each run names the host that compiled and the host that compared')
        compiled_on.add(run['compiled_on'])
        compared_on.add(run['compared_on'])
        report = run.get('report')
        require(isinstance(report, dict), 'Match record: run without a comparator report')
        sanitized(report)
        require(report.get('report_schema') == REPORT_SCHEMA and report.get('contract_version') == CONTRACT_VERSION,
                'Match record: report schema or contract version differs from this comparator')
        comparator = report.get('comparator') or {}
        require(comparator.get('version') == COMPARATOR_VERSION
                and comparator.get('source_sha256') == current_comparator,
                'Match record: report comes from a different comparator version; re-run it')
        require(report.get('acceptance') == 'not-evaluated', 'Match record: report was edited (acceptance)')
        require(report.get('result') == 'pass' and report.get('reason') == 'all-checks-passed',
                'Match record: report result is not pass')
        ident = report.get('function') or {}
        require(ident.get('build_id') == target['build_id'] == fn['build_id']
                and ident.get('rva') == fn['rva'] and ident.get('size') == fn['size'] and text(ident.get('symbol')),
                'Match record: report function identity differs from the inventory entry')
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
        require(cov.get('code_bytes_total') == fn['size']
                and integer(cov.get('code_bytes_exact')) and integer(cov.get('code_bytes_by_reference'))
                and cov['code_bytes_exact'] + cov['code_bytes_by_reference'] == fn['size']
                and cov.get('unwind') in {'covered', 'none-in-range'},
                'Match record: report coverage is incomplete')
    require(len(symbols) == 1, 'Match record: runs compared different symbols')
    entry = (symbol_map.get('symbols') or {}).get(next(iter(symbols)))
    require(isinstance(entry, dict) and entry.get('rva') == fn['rva'] and entry.get('size') == fn['size'],
            'Match record: symbol map does not place the function at the inventory range')
    require(len(compiled_on) >= MIN_HOSTS and len(compared_on) >= MIN_HOSTS,
            f'Match record: runs must come from at least {MIN_HOSTS} compile hosts and {MIN_HOSTS} compare hosts')
    # Host names are self-reported. Without /Brepro, two clean compiles do not yield the same object
    # (COFF time stamp and path records differ), so one object under two compile hosts means one
    # run was relabelled, not repeated. A deterministic recipe would trip this and needs a gate change.
    shared = sorted(h for hosts in object_hosts.values() if len(hosts) > 1 for h in hosts)
    require(not shared, f'Match record: one candidate object is claimed by compile hosts {", ".join(shared)}; '
            'runs from different hosts must have different object hashes')
    check_build(record.get('build'), flags, unit, runs)
    return record


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


def validate_review(fn, record, root=None):
    """Require a sanitized Reviewer `approve` bound to this function and to the source the record matched.

    The record is the policy's public trace of the Reviewer step: the full review stays private under
    .local/reviews/ and is bound by its hash. Binding the function identity and the translation-unit
    digest means an approval cannot be carried over to other source or another function; any source
    change makes it stale together with the match record.
    """
    root = ROOT if root is None else root
    name = review_record_path(fn)
    require((root / name).is_file(), f'Review record: {name} is missing; matched needs a Reviewer approve')
    try:
        review = json.loads((root / name).read_text())
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f'Review record: {name} is not JSON ({exc})') from None
    require(isinstance(review, dict) and review.get('review_record_schema') == REVIEW_RECORD_SCHEMA,
            'Review record: unknown review_record_schema')
    # Only known fields: free text here would be an unreviewed publication channel.
    require(set(review) == REVIEW_FIELDS, f'Review record: fields must be exactly {sorted(REVIEW_FIELDS)}')
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
    return review


def validate(data, target, root=None):
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
    seen, ranges = set(), []
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
        if fn['status'] == 'matched':
            validate_review(fn, validate_match(fn, target, root), root)
        elif fn.get('report') is not None:
            # A record awaiting review must still be consistent with the integrated tree.
            validate_match(fn, target, root)
    matched = {review_record_path(fn) for fn in data['functions'] if fn['status'] == 'matched'}
    reports = (ROOT if root is None else root) / 'reports'
    for path in sorted(reports.glob('*/*.review.json')) if reports.is_dir() else []:
        name = path.relative_to(reports.parent).as_posix()
        # A leftover approval would read as acceptance of an entry the inventory does not accept.
        require(name in matched, f'Review record: {name} belongs to no matched inventory entry')
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


def lint(root, names=None):
    """The mechanical source rules of tools/lint_reconstruction.py, as a validation failure."""
    problems = lint_tree(root, names)
    require(not problems, 'Reconstruction lint: ' + '; '.join(problems[:5])
            + (f' (and {len(problems) - 5} more)' if len(problems) > 5 else ''))


def load(staged=False):
    if not staged:
        data = validate(json.loads((ROOT / 'data/progress.json').read_text()),
                        json.loads((ROOT / 'builds/target.json').read_text()))
        # Tracked and not-yet-added files alike, so a Drafter's new source is linted before staging.
        names = subprocess.check_output(['git', 'ls-files', '--cached', '--others', '--exclude-standard', '-z',
                                         '--', 'reconstruction'], cwd=ROOT).decode('utf-8').split('\0')
        lint(ROOT, sorted({n for n in names if n and (ROOT / n).is_file()}))
        return data
    # Match records, source and recipe are checked as staged too, so the index gets its own tree.
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.check_call(['git', 'checkout-index', '--all', f'--prefix={tmp}/'], cwd=ROOT)
        root = Path(tmp)
        data = validate(json.loads((root / 'data/progress.json').read_text()),
                        json.loads((root / 'builds/target.json').read_text()), root)
        lint(root)
        return data


def inspect_payload(name, payload, mode='100644'):
    path = Path(name)
    require(mode in {'100644', '100755'}, f'{name}: symlink/submodule not approved')
    require(not any(p.lower() in {'.local', 'private', 'dist'} or p.lower().endswith('.rep') for p in path.parts),
            f'{name}: private/generated path')
    require(path.suffix.lower() not in BLOCKED, f'{name}: prohibited extension')
    require(path.name.lower() not in {'.env', '.ds_store'} and not path.name.lower().startswith('.env.'),
            f'{name}: private config')
    require(len(payload) <= 1024 * 1024, f'{name}: exceeds 1 MiB limit')
    require(b'\0' not in payload, f'{name}: binary content')
    try:
        payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError(f'{name}: non-UTF-8 content') from exc
    require(not payload.startswith(b'version https://git-lfs.github.com/spec/v1'), f'{name}: LFS prohibited')


def check_git(root=ROOT, staged=False):
    records = subprocess.check_output(['git', 'ls-files', '--stage', '-z'], cwd=root).split(b'\0')
    count = 0
    for record in filter(None, records):
        meta, rawname = record.split(b'\t', 1)
        mode, sha, stage = meta.decode().split()
        name = rawname.decode('utf-8')
        require(stage == '0', f'{name}: unresolved conflict')
        # Index blobs matter: a staged binary may have been replaced by harmless text on disk.
        inspect_payload(name, subprocess.check_output(['git', 'cat-file', 'blob', sha], cwd=root), mode)
        if not staged:
            path = root / name
            require(path.is_file() and not path.is_symlink(), f'{name}: missing file/symlink')
            inspect_payload(name, path.read_bytes(), mode)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--staged', action='store_true', help='Check index blobs and staged metadata')
    args = parser.parse_args()
    try:
        load(staged=args.staged)
        count = check_git(staged=args.staged)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print(f'PASS: metadata and {count} tracked files. No Skyrim byte comparison performed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
