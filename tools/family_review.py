"""Family review bindings and deterministic, precommitted batch selection.

Private approvals stay in .local/reviews; public manifests contain only structured metadata.
Git ordering is checked by the acceptance tool; CI checks the published bindings and draw.
"""
import hashlib
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import subprocess

ID = re.compile(r'[a-z0-9][a-z0-9-]*\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
ORIGIN_FIELDS = {'family', 'version', 'template_digest'}
FAMILY_FIELDS = {'family_schema', 'origin', 'binding', 'template_source', 'parameter_source',
                 'parameter_ranges', 'first_members', 'review', 'paused', 'pause_reason'}
BATCH_FIELDS = {'batch_schema', 'family_path', 'family_sha256', 'seed', 'population',
                'members', 'commitment', 'sample'}
REVIEW_FIELDS = {'review_task_id', 'reviewer_model', 'profile', 'review_sha256', 'spec_sha256'}


def require(ok, why):
    if not ok:
        raise ValueError('Family review: ' + why)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def unique_fields(pairs):
    out = {}
    for key, value in pairs:
        require(key not in out, 'duplicate JSON field: ' + key)
        out[key] = value
    return out


def read(root, name):
    return json.loads((Path(root) / name).read_text(), object_pairs_hook=unique_fields)


def write(root, name, value):
    path = Path(root) / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')


def public_path(name, prefix):
    require(isinstance(name, str) and name.startswith(prefix) and '\\' not in name
            and not Path(name).is_absolute() and '..' not in Path(name).parts,
            'invalid public metadata path')
    return name


def origin_valid(origin):
    require(isinstance(origin, dict) and set(origin) == ORIGIN_FIELDS, 'origin needs family, version, template_digest')
    require(all(isinstance(origin[k], str) and ID.fullmatch(origin[k]) for k in ('family', 'version')),
            'invalid family or version')
    require(isinstance(origin['template_digest'], str) and HASH.fullmatch(origin['template_digest']),
            'invalid template digest')


def binding(fn, record):
    report = record['runs'][0]['report']
    return {'build_id': fn['build_id'], 'image_sha256': report['target']['image_sha256'],
            'recipe_sha256': record['recipe']['sha256'], 'compiler': report['recipe'],
            'toolchain_sha256': record['toolchain_pin']['sha256'], 'comparator': report['comparator']}


def member_digest(fn, record):
    return digest({'function_id': fn['id'], 'build_id': fn['build_id'], 'rva': fn['rva'], 'size': fn['size'],
                   'source_digest': record['source']['digest'], 'name': fn['name'], 'name_origin': fn['name_origin'],
                   'origin': record.get('origin'),
                   'family_parameters': record.get('family_parameters'), 'name_source': record.get('name_source'),
                   'binding': binding(fn, record)})


def in_ranges(parameters, ranges):
    if isinstance(ranges, dict) and set(ranges) == {'rows'} and isinstance(ranges['rows'], list):
        if not isinstance(parameters, dict):
            return False
        return any(set(parameters) == set(row) and all(type(parameters[k]) is type(row[k])
                   and parameters[k] == row[k] for k in row) for row in ranges['rows'] if isinstance(row, dict))
    if not isinstance(parameters, dict) or not isinstance(ranges, dict) or set(parameters) != set(ranges):
        return False
    for key, value in parameters.items():
        rule = ranges[key]
        if set(rule) == {'min', 'max'}:
            if type(value) is not int or not rule['min'] <= value <= rule['max']:
                return False
        elif set(rule) == {'values'}:
            if not any(type(value) is type(v) and value == v for v in rule['values']):
                return False
        else:
            return False
    return True


def exact_ranges(rows):
    """Preserve correlations between observed parameter values."""
    require(isinstance(rows, list) and rows, 'reviewed parameter rows missing')
    unique = {json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False): row for row in rows}
    result = {'rows': [unique[k] for k in sorted(unique)]}
    validate_ranges(result)
    return result


def validate_ranges(ranges):
    require(isinstance(ranges, dict) and ranges, 'reviewed parameter ranges missing')
    if set(ranges) == {'rows'} and isinstance(ranges['rows'], list):
        rows = ranges['rows']
        require(bool(rows) and all(isinstance(row, dict) and row for row in rows), 'reviewed parameter rows missing')
        keys = set(rows[0])
        require(all(isinstance(k, str) and ID.fullmatch(k) for k in keys), 'invalid parameter name')
        require(all(set(row) == keys and all(type(v) in (str, int, bool) for v in row.values())
                    for row in rows), 'invalid parameter row')
        from check import naming_finding_problem
        require(all(not isinstance(v, str) or naming_finding_problem(v) is None
                    for row in rows for v in row.values()), 'unsafe parameter enumeration')
        serial = [json.dumps(row, sort_keys=True, separators=(',', ':')) for row in rows]
        require(len(set(serial)) == len(serial), 'duplicate parameter row')
        return
    for key, rule in ranges.items():
        require(isinstance(key, str) and ID.fullmatch(key) and isinstance(rule, dict), 'invalid parameter range')
        numeric = set(rule) == {'min', 'max'} and all(type(rule[k]) is int for k in ('min', 'max'))
        choices = (set(rule) == {'values'} and isinstance(rule['values'], list) and bool(rule['values'])
                   and all(type(v) in (str, int, bool) for v in rule['values']))
        require((numeric and rule['min'] <= rule['max']) or choices, 'invalid parameter range')
        if choices:
            from check import naming_finding_problem
            require(all(not isinstance(v, str) or naming_finding_problem(v) is None for v in rule['values']),
                    'unsafe parameter enumeration')


def name_source_valid(label):
    require(isinstance(label, str) and label.isascii() and len(label) <= 300,
            'name_source must be a public symbol source or labelled guess')
    from check import naming_finding_problem
    require(naming_finding_problem(label) is None, 'unsafe name_source label')
    require(re.fullmatch(r'GUESS\((low|medium|high)\)', label) or
            re.fullmatch(r'(COMMUNITY|EXE_RTTI|SIBLING)\([^\n()]+\)', label),
            'name_source must be a public symbol source or labelled guess')


def spec(family):
    return {k: v for k, v in family.items() if k not in ('review', 'paused', 'pause_reason', 'superseded_by')}


def family_key(family):
    key = {'origin': family['origin'], 'binding': family['binding']}
    if family.get('supersedes'):
        key.update(supersedes=family['supersedes'], parameter_ranges=family['parameter_ranges'])
    return digest(key)


def validate_family(family, approved=True):
    require(isinstance(family, dict) and FAMILY_FIELDS <= set(family) <= FAMILY_FIELDS | {'supersedes', 'superseded_by'}
            and type(family['family_schema']) is int and family['family_schema'] == 1,
            'unknown family manifest schema')
    origin_valid(family['origin'])
    for field in ('supersedes', 'superseded_by'):
        if field in family:
            public_path(family[field], f'reports/{family["binding"]["build_id"]}/families/')
    if family.get('superseded_by'):
        require(family['review'] is None and family['paused'], 'superseded family must be unapproved and paused')
    validate_ranges(family['parameter_ranges'])
    require(type(family['paused']) is bool, 'paused must be boolean')
    require(isinstance(family['pause_reason'], str), 'pause_reason must be text')
    from check import naming_finding_problem
    require(not family['pause_reason'] or naming_finding_problem(family['pause_reason']) is None, 'unsafe pause reason')
    bound = family['binding']
    require(isinstance(bound, dict) and set(bound) == {'build_id', 'image_sha256', 'recipe_sha256',
            'compiler', 'toolchain_sha256', 'comparator'}, 'invalid family target binding')
    require(isinstance(bound['build_id'], str) and ID.fullmatch(bound['build_id']), 'invalid family build id')
    require(all(isinstance(bound[k], str) and HASH.fullmatch(bound[k]) for k in
                ('image_sha256', 'recipe_sha256', 'toolchain_sha256')), 'invalid family binding digest')
    require(isinstance(bound['compiler'], dict) and set(bound['compiler']) ==
            {'recipe_sha256', 'compiler_binary_sha256', 'compiler_version', 'flags'}, 'invalid compiler binding')
    require(isinstance(bound['comparator'], dict) and set(bound['comparator']) == {'version', 'source_sha256'},
            'invalid comparator binding')
    first = family['first_members']
    require(isinstance(first, dict) and len(first) == 20 and all(ID.fullmatch(k) and isinstance(v, str)
            and HASH.fullmatch(v) for k, v in first.items()), 'family review must bind the first 20 members')
    for field in ('template_source', 'parameter_source'):
        source = family[field]
        require(isinstance(source, dict) and set(source) == {'path', 'sha256'}, 'invalid template or extraction source')
        public_path(source['path'], '')
        require(source['path'].split('/')[0] in ('tools', 'reconstruction'), 'source must be tracked tooling or template')
        require(isinstance(source['sha256'], str) and HASH.fullmatch(source['sha256']), 'source lacks digest')
    require(family['template_source']['sha256'] == family['origin']['template_digest'], 'template digest mismatch')
    if approved:
        review = family['review']
        require(isinstance(review, dict) and set(review) == REVIEW_FIELDS, 'unreviewed family')
        require(review['spec_sha256'] == digest(spec(family)), 'family review spec digest mismatch')
        require(isinstance(review['review_task_id'], str) and ID.fullmatch(review['review_task_id'])
                and isinstance(review['review_sha256'], str) and HASH.fullmatch(review['review_sha256']),
                'invalid family approval')
        require(review['profile'] in ('cheap', 'full', 'claude-low')
                and isinstance(review['reviewer_model'], str)
                and re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]*', review['reviewer_model']), 'invalid family reviewer profile or model')


def check_member(family, fn, record, ranges=True):
    origin_valid(record.get('origin'))
    require(record['origin'] == family['origin'], 'family version or template digest mismatch')
    require(binding(fn, record) == family['binding'], 'family target, recipe, compiler or comparator binding mismatch')
    name_source_valid(record.get('name_source'))
    require(not ranges or in_ranges(record.get('family_parameters'), family['parameter_ranges']),
            'member parameter outside reviewed ranges; use individual review')


def draw(seed, population):
    """Hash ranking is stable across Python versions; ties break by function id."""
    n = min(len(population), max(20, math.ceil(len(population) / 20)))
    return sorted(sorted(population, key=lambda fid: (digest([seed, fid]), fid))[:n])


def validate_batch(batch, family, fn=None, record=None, planned=False):
    require(isinstance(batch, dict) and set(batch) == BATCH_FIELDS
            and type(batch['batch_schema']) is int and batch['batch_schema'] == 1,
            'unknown family batch schema')
    population = batch['population']
    require(isinstance(population, list) and population and all(isinstance(v, str) and ID.fullmatch(v) for v in population)
            and population == sorted(set(population)), 'invalid or repeated batch population')
    require(isinstance(batch['seed'], str) and len(batch['seed']) <= 200 and ID.fullmatch(batch['seed']),
            'draw seed must be a public lowercase identifier')
    require(isinstance(batch['members'], dict) and set(batch['members']) == set(population)
            and all(isinstance(v, str) and HASH.fullmatch(v) for v in batch['members'].values()), 'invalid batch member bindings')
    require(batch['family_sha256'] == digest(spec(family)), 'batch family spec mismatch')
    if planned and batch['sample'] is None and batch['commitment'] is None:
        return
    require(batch['sample'] == draw(batch['seed'], population), 'tampered sample seed or population')
    require(isinstance(batch['commitment'], str) and re.fullmatch(r'[0-9a-f]{40,64}', batch['commitment']),
            'sample has no pre-draw commitment')
    if fn is not None:
        require(fn['id'] in population and batch['members'][fn['id']] == member_digest(fn, record),
                'member differs from committed population')


def git(root, *args):
    p = subprocess.run(['git', *args], cwd=root, capture_output=True, text=True)
    require(p.returncode == 0, 'git ordering evidence unavailable: ' + ' '.join(args[:2]))
    return p.stdout.strip()


def committed(root, path, value, ref='HEAD'):
    try:
        saved = json.loads(git(root, 'show', f'{ref}:{path}'))
    except (ValueError, json.JSONDecodeError):
        raise ValueError('Family review: commit the batch metadata before continuing') from None
    require(saved == value, 'commit the batch metadata before continuing')


def no_prior_acceptance(root, population, ref, members):
    for rev in git(root, 'log', '--format=%H', ref, '--', 'data/progress.json').splitlines():
        data = json.loads(git(root, 'show', f'{rev}:data/progress.json'))
        for fn in data['functions']:
            if fn['id'] in population and fn['status'] == 'matched':
                record = json.loads(git(root, 'show', f'{rev}:{fn["report"]}'))
                require(member_digest(fn, record) != members[fn['id']],
                        'sample drawn after an acceptance in its population')


def ordering(root, path, batch, before_accept=True):
    planned = dict(batch, commitment=None, sample=None)
    committed(root, path, planned, batch['commitment'])
    git(root, 'merge-base', '--is-ancestor', batch['commitment'], 'HEAD')
    no_prior_acceptance(root, batch['population'], batch['commitment'], batch['members'])
    if before_accept:
        committed(root, path, batch)
        # The first commit containing this draw must precede every population acceptance.
        history = git(root, 'log', '--reverse', '--format=%H', '--', path).splitlines()
        draw_commit = next((rev for rev in history if json.loads(git(root, 'show', f'{rev}:{path}')) == batch), None)
        require(draw_commit is not None, 'draw was not recorded before acceptance')
        no_prior_acceptance(root, batch['population'], draw_commit, batch['members'])


def private_approval(root, family, profile):
    import accept_function as af
    review = family['review']
    path = Path(root) / '.local/reviews' / (review['review_task_id'] + '.family.json')
    base = (Path(root) / '.local/reviews').resolve()
    require(path.resolve().is_relative_to(base) and path.is_file(), 'saved approving family review missing')
    blob = path.read_bytes()
    require(hashlib.sha256(blob).hexdigest() == review['review_sha256'], 'saved family review digest mismatch')
    doc = json.loads(blob, object_pairs_hook=unique_fields)
    expected = {'family_review_schema', 'review_task_id', 'reviewer_model', 'profile', 'spec_sha256',
                'fresh_context', 'drafted_or_triaged', 'verdict', 'escalation_category', 'checks'}
    require(isinstance(doc, dict) and set(doc) == expected and doc['family_review_schema'] == 1,
            'malformed saved family review')
    require(doc['spec_sha256'] == digest(spec(family)), 'family review spec digest mismatch')
    require(all(doc[k] == review[k] for k in ('review_task_id', 'reviewer_model', 'profile')), 'family reviewer binding differs')
    require(doc['profile'] == profile and af.reviewer_admitted(root, doc['reviewer_model'], profile),
            'family review model is not admitted for this profile')
    require(doc['fresh_context'] is True and doc['drafted_or_triaged'] is False,
            'family Reviewer must be fresh and independent')
    require(doc['verdict'] == 'approve' and doc['escalation_category'] == 'none', 'family review does not approve')
    checks = ('plausible_source', 'provenance', 'claim_scope', 'publication_hygiene', 'parameter_extraction',
              'target_binding', 'name_sources', 'first_20')
    require(doc['checks'] == dict.fromkeys(checks, 'pass'), 'family review lacks passing checks')
    for field in ('template_source', 'parameter_source'):
        src = family[field]
        require(hashlib.sha256((Path(root) / src['path']).read_bytes()).hexdigest() == src['sha256'],
                'template or extraction source changed; start a new family')
    return doc


@lru_cache(maxsize=8)
def _public_family_batch(family_blob, batch_blob):
    """Validate shared metadata once per exact content pair, never per path or mtime.

    Callers still read both files for every member and check all member-specific
    bindings. The cached dictionaries are private and are only read by that check.
    """
    family = json.loads(family_blob.decode(), object_pairs_hook=unique_fields)
    validate_family(family)
    batch = json.loads(batch_blob.decode(), object_pairs_hook=unique_fields)
    validate_batch(batch, family)
    return family, batch, digest(batch)


def validate_public_review(root, fn, record, review):
    evidence = review['family_evidence']
    require(isinstance(evidence, dict) and set(evidence) == {'family_path', 'batch_path', 'batch_sha256', 'member_sha256'},
            'invalid sanitized family evidence')
    family_path = public_path(evidence['family_path'], f'reports/{fn["build_id"]}/families/')
    batch_path = public_path(evidence['batch_path'], f'reports/{fn["build_id"]}/family-batches/')
    family, batch, batch_digest = _public_family_batch(
        (Path(root) / family_path).read_bytes(), (Path(root) / batch_path).read_bytes())
    require(batch['family_path'] == evidence['family_path'], 'batch names another family')
    member_hash = member_digest(fn, record)
    require(fn['id'] in batch['population'] and batch['members'][fn['id']] == member_hash,
            'member differs from committed population')
    check_member(family, fn, record)
    require(fn['id'] not in batch['sample'], 'sampled member needs its own approving review')
    require(review['naming_findings'] == ['Family approval does not assess individual names.'],
            'family approval does not establish individual names')
    require(evidence['batch_sha256'] == batch_digest and evidence['member_sha256'] == member_hash,
            'sanitized family evidence digest mismatch')
    import accept_function as af
    require(af.reviewer_admitted(root, family['review']['reviewer_model'], family['review']['profile']),
            'family review model is not admitted')
    require(all(review[k] == family['review'][k] for k in ('review_task_id', 'reviewer_model', 'review_sha256')),
            'sanitized record names another family review')


def supersession_binding(old, replacement):
    """Retirement preserves the family and evidence pins; source revisions are new versions."""
    require(replacement['origin']['family'] == old['origin']['family']
            and replacement['binding'] == old['binding'], 'family supersession binding mismatch')
    if replacement['origin'] != old['origin']:
        require(replacement['origin']['version'] != old['origin']['version']
                and replacement['origin']['template_digest'] != old['origin']['template_digest'],
                'changed family source requires a new version and template digest')


def check_superseded(root, path, family):
    """A retired manifest cannot hide a pause without a matching replacement."""
    replacement_path = public_path(family['superseded_by'],
                                   f'reports/{family["binding"]["build_id"]}/families/')
    require(replacement_path != str(path), 'family cannot supersede itself')
    replacement = read(root, replacement_path)
    validate_family(replacement, approved=replacement['review'] is not None)
    require(replacement.get('supersedes') == str(path), 'family supersession binding mismatch')
    supersession_binding(family, replacement)


def validate_metadata(root):
    """Validate family files even before a member relies on them."""
    root = Path(root)
    for path in sorted((root / 'reports').glob('*/families/*.json')):
        family = read(root, path.relative_to(root))
        validate_family(family, approved=family['review'] is not None)
        require(path.parent.parent.name == family['binding']['build_id'], 'family manifest belongs to another build')
        if family.get('superseded_by'):
            check_superseded(root, path.relative_to(root).as_posix(), family)
    for path in sorted((root / 'reports').glob('*/family-batches/*.json')):
        batch = read(root, path.relative_to(root))
        family = read(root, public_path(batch['family_path'], f'reports/{path.parent.parent.name}/families/'))
        validate_family(family)
        validate_batch(batch, family, planned=True)
