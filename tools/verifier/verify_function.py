"""Run the comparator for one candidate function and print a short sanitized summary.

A task description file (JSON) bundles what stays fixed across reconstruction attempts:

    {"verify_task_schema": 1,
     "task": {...contract task: task_id, build_id, target_image_sha256, rva, size, symbol,
              source_revision, source_path, recipe_sha256...},
     "recipe": "recipe.json",          # paths are relative to the description file
     "symbols": "symbols.json",
     "manifest": null}                 # null or absent: builds/target.json of this checkout

The candidate object, its build record and the target image are given per run. The wrapper
calls tools/compare.py unchanged, so every decision is the comparator's; the wrapper only
checks that what comes back is a sanitized report and refuses to summarize anything else.

Outputs: the comparator's sanitized JSON report at --report, raw byte-level diagnostics only
under the checkout's .local/ directory, and a one-screen summary on stdout that never contains
code bytes. A `pass` is comparator evidence for the acceptance rule in docs/verification.md;
it does not make a function `matched`.
Exit status: 0 pass, 1 fail, 2 the comparator could not produce a report.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[2]
COMPARE = REPO / 'tools' / 'compare.py'
PRIVATE_ROOT = REPO / '.local'
DEFAULT_DIAGNOSTICS = PRIVATE_ROOT / 'verifier' / 'diagnostics'
TASK_SCHEMA = 1
HEX_RUN = re.compile(r'[0-9a-fA-F]{16,}')
HASH_KEYS = {'image_sha256', 'expected_image_sha256', 'object_sha256', 'code_section_sha256', 'recipe_sha256',
             'compiler_binary_sha256', 'source_sha256', 'source_revision'}

# One line of next-step guidance per reason code, so a reconstruction loop can act on the
# result without seeing bytes. Codes not listed fall back to the comparator's own detail.
HINTS = {
    'all-checks-passed': 'Every byte, the unwind info, EH data and funclets agree. Keep the inputs; ask for a second-host re-run.',
    'code-byte-mismatch': 'Same length, different code. Revisit types, field offsets, control flow or flags.',
    'function-size-mismatch': 'Candidate length differs from the target range. Code shape or inlining differs.',
    'relocation-target-mismatch': 'A call or data reference resolves to the wrong RVA, or the symbol map is wrong.',
    'unresolved-symbol': 'The candidate references a symbol the map does not place. Inline it or add a mapped name.',
    'unsupported-relocation': 'The candidate uses a relocation contract v1 cannot check (e.g. ADDR64).',
    'unwind-coverage-missing': 'Target has unwind info here and the candidate has none: prologue/frame differs.',
    'unwind-coverage-extra': 'Candidate has unwind info the target lacks: prologue/frame differs.',
    'unwind-info-mismatch': 'Prologue or saved-register layout differs from the target.',
    'unwind-entry-crosses-boundary': 'The task range cuts through a target .pdata entry; the range is wrong.',
    'unsupported-unwind': 'Unwind info version 2: outside contract v2.',
    'unwind-chain-mismatch': 'A chained .pdata entry names another parent: prolog split or register saves differ.',
    'unwind-entry-overlap': '.pdata entries overlap; the target range or the object is malformed.',
    'unsupported-eh-handler': 'Handler other than __CxxFrameHandler3, __C_specific_handler or a GS check.',
    'eh-handler-mismatch': 'Target uses another handler: try/catch vs destructors vs __try, or /GS differs.',
    'eh-data-mismatch': 'EH tables differ (states, try ranges, catch adjectives/offsets): scopes or locals differ.',
    'eh-reference-mismatch': 'An EH table points elsewhere: a different IP boundary, catch type or missing funclet.',
    'eh-catch-type-mismatch': 'A catch clause names another type than the target.',
    'eh-funcinfo-unsupported': 'FuncInfo shape the contract does not decode.',
    'eh-data-unaccounted': 'Candidate EH data has bytes or relocations the target structures do not explain.',
    'eh-data-overlap': 'Two EH structures share bytes in the candidate.',
    'eh-unexpected-relocation': 'A relocation sits on an integer EH field.',
    'eh-unrelocated-reference': 'A non-null EH reference has no relocation.',
    'eh-reference-kind': 'An EH reference points to data where code is expected, or the reverse.',
    'eh-funclet-overlap': 'A funclet would sit over the function or another funclet in the target.',
    'function-symbol-missing': 'The object does not define the task symbol. Check the declaration and mangling.',
    'candidate-boundary-unsupported': 'Symbol is not external, not at offset 0 of its own section, or shares it (/Gy?).',
    'image-hash-mismatch': 'Wrong target image: its SHA-256 is not the pinned one.',
    'manifest-mismatch': 'Task and target manifest disagree on build id or image hash.',
    'object-provenance-mismatch': 'The build record names a different object than the one given.',
    'stale-source-revision': 'The build record names another source revision than the task.',
    'stale-recipe': 'The recipe file or build record differs from the recipe the task pins.',
}


class TaskFileError(Exception):
    pass


def sha256(blob):
    return hashlib.sha256(blob).hexdigest()


def load_task_file(path):
    """Return (task, recipe path, symbols path, manifest path) from a task description file."""
    path = Path(path)
    try:
        spec = json.loads(path.read_text())
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TaskFileError(f'cannot read task description: {exc}') from None
    if not isinstance(spec, dict) or spec.get('verify_task_schema') != TASK_SCHEMA:
        raise TaskFileError(f'task description needs verify_task_schema {TASK_SCHEMA}')
    if not isinstance(spec.get('task'), dict):
        raise TaskFileError('task description needs a "task" object')
    base = path.resolve().parent

    def ref(key, required=True):
        value = spec.get(key)
        if value is None and not required:
            return None
        if not isinstance(value, str) or not value.strip():
            raise TaskFileError(f'task description needs a path for {key!r}')
        return (base / value).resolve()

    manifest = ref('manifest', required=False) or REPO / 'builds' / 'target.json'
    return spec['task'], ref('recipe'), ref('symbols'), manifest


def under(path, root):
    path, root = Path(path).resolve(), Path(root).resolve()
    return path == root or root in path.parents


def mask(text):
    """Strip anything that could be bytes from free text before it is printed or stored."""
    return HEX_RUN.sub('<hex>', text)


def check_report(report):
    """Refuse to summarize anything that is not a well-formed, sanitized, non-accepting report."""
    if not isinstance(report, dict) or report.get('acceptance') != 'not-evaluated':
        raise ValueError('report does not carry acceptance: not-evaluated')
    if report.get('result') not in ('pass', 'fail'):
        raise ValueError('report result is neither pass nor fail')
    if (report['result'] == 'pass') != (report.get('reason') == 'all-checks-passed'):
        raise ValueError('report result and reason disagree')

    def walk(value, key=''):
        if isinstance(value, dict):
            for k, v in value.items():
                walk(v, k)
        elif isinstance(value, list):
            for v in value:
                walk(v, key)
        elif isinstance(value, str) and key not in HASH_KEYS and HEX_RUN.search(value):
            raise ValueError(f'report field {key!r} holds a long hex run')
    walk(report)
    return report


def short(value):
    return value[:12] if isinstance(value, str) else value


def summarize(report, report_path, diagnostics_path):
    fn = report.get('function') or {}
    cov = report.get('coverage') or {}
    recipe = report.get('recipe') or {}
    lines = [
        f"verify_function: {report['result'].upper()}  reason={report['reason']}",
        f"  task        {report.get('task_id')}",
        f"  function    build={fn.get('build_id')} rva=0x{fn.get('rva', 0):x} size={fn.get('size')} symbol={fn.get('symbol')}",
        f"  detail      {mask(str(report.get('detail')))}",
        f"  hint        {HINTS.get(report['reason'], 'see the comparator contract for this reason code')}",
        f"  coverage    total={cov.get('code_bytes_total')} exact={cov.get('code_bytes_exact')} "
        f"by_reference={cov.get('code_bytes_by_reference')} relocations={cov.get('relocations_by_type')}",
        f"  unwind      {cov.get('unwind')} entries={cov.get('unwind_entries')} bytes={cov.get('unwind_bytes_exact')}",
        f"  inputs      object={short((report.get('candidate') or {}).get('object_sha256'))} "
        f"recipe={short(recipe.get('recipe_sha256'))} compiler={recipe.get('compiler_version')}",
        f"  acceptance  {report['acceptance']} (a pass is review evidence only; nothing becomes matched)",
        f"  report      {report_path}",
    ]
    if diagnostics_path is not None and Path(diagnostics_path).exists():
        lines.append(f'  private     {diagnostics_path} (byte-level context; stays under .local/)')
    return '\n'.join(lines)


def error_record(task, exit_code, stderr):
    """Record of a run where the comparator wrote no report: inputs unreadable or refused."""
    return {'verify_function': 'comparator-error', 'acceptance': 'not-evaluated', 'result': 'error',
            'comparator_exit': exit_code, 'task_id': task.get('task_id') if isinstance(task, dict) else None,
            'detail': mask(stderr.strip())[-400:]}


def run(task_file, obj, build_record, image, report_path, diagnostics=None, python=sys.executable):
    """Return (exit status, summary text). Writes the report (or an error record) to report_path."""
    task, recipe, symbols, manifest = load_task_file(task_file)
    report_path = Path(report_path).resolve()
    if diagnostics is None:
        task_id = task.get('task_id') if isinstance(task.get('task_id'), str) else 'unknown-task'
        try:
            tag = sha256(Path(obj).read_bytes())[:12]
        except OSError:
            tag = 'unreadable'
        diagnostics = DEFAULT_DIAGNOSTICS / re.sub(r'[^a-z0-9-]', '-', task_id) / f'{tag}.json'
    diagnostics = Path(diagnostics).resolve()
    if not under(diagnostics, PRIVATE_ROOT):
        raise TaskFileError(f'diagnostics must stay under {PRIVATE_ROOT}')
    if report_path == diagnostics:
        raise TaskFileError('report and diagnostics paths must differ')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    for stale in (report_path, diagnostics):
        if stale.exists():
            stale.unlink()
    # The comparator reads one plain task; the description's other fields only locate inputs.
    flat_task = diagnostics.with_name(diagnostics.stem + '.task.json')
    flat_task.parent.mkdir(parents=True, exist_ok=True)
    flat_task.write_text(json.dumps(task, indent=2, sort_keys=True) + '\n')
    # Not isolated mode: compare.py imports pecoff from its own directory.
    cmd = [python, str(COMPARE), '--task', str(flat_task), '--manifest', str(manifest),
           '--recipe', str(recipe), '--build-record', str(build_record), '--object', str(obj),
           '--image', str(image), '--symbols', str(symbols), '--report', str(report_path),
           '--diagnostics', str(diagnostics)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode not in (0, 1) or not report_path.exists():
        record = error_record(task, proc.returncode, proc.stderr)
        report_path.write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
        return 2, (f"verify_function: ERROR  comparator exit {proc.returncode}, no comparison report\n"
                   f"  detail      {record['detail']}\n  record      {report_path}")
    report = check_report(json.loads(report_path.read_text()))
    expected = 0 if report['result'] == 'pass' else 1
    if proc.returncode != expected:
        raise ValueError(f'comparator exit {proc.returncode} disagrees with result {report["result"]}')
    return expected, summarize(report, report_path, diagnostics)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--task-file', required=True, type=Path, help='Task description JSON (see above)')
    parser.add_argument('--object', required=True, type=Path, help='Candidate COFF object')
    parser.add_argument('--build-record', required=True, type=Path, help='Build record written when compiling')
    parser.add_argument('--image', required=True, type=Path, help='Pinned target image')
    parser.add_argument('--report', required=True, type=Path, help='Where to write the sanitized JSON report')
    parser.add_argument('--diagnostics', type=Path,
                        help='Private diagnostics path under .local/ (default: .local/verifier/diagnostics/...)')
    args = parser.parse_args()
    try:
        status, text = run(args.task_file, args.object, args.build_record, args.image, args.report, args.diagnostics)
    except (TaskFileError, ValueError, OSError) as exc:
        print(f'verify_function: ERROR  {mask(str(exc))}', file=sys.stderr)
        return 2
    print(text)
    return status


if __name__ == '__main__':
    raise SystemExit(main())
