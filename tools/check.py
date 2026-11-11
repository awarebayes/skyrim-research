"""Validate metadata and common publication mistakes; never compares Skyrim bytes."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BLOCKED = set('.exe .dll .pdb .obj .o .lib .a .so .dylib .dmp .mdmp .bin .bsa .ba2 .esm .esp .esl .nif .dds .pex .hkx .ess .skse .gdt .gpr .idb .i64 .zip .7z .iso .vhdx .qcow2 .png .jpg .jpeg .pdf'.split())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip())


def integer(value):
    return type(value) is int and value >= 0


def validate(data, target):
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
        require(fn['status'] != 'matched', 'Matching disabled until reviewed comparator is implemented')
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
        require((ROOT / path).is_file(), 'Evidence does not exist')
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


def load(staged=False):
    def read(name):
        if staged:
            return json.loads(subprocess.check_output(['git', 'show', ':' + name], cwd=ROOT))
        return json.loads((ROOT / name).read_text())
    return validate(read('data/progress.json'), read('builds/target.json'))


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
