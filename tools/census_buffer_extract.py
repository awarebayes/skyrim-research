"""Extract complete operand/reference columns from an explicit private population.

This is a research aid, not an enrollment filter or comparator. A private role
file can name measured operands (for example an element stride) and attach
inferences to instruction offsets. Inferences never become measured facts.
No image content, reference addresses or semantic recipes are embedded here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent / 'analysis'))
import imagemodel
import x64
from pecoff import PeImage


def sha(data):
    return hashlib.sha256(data).hexdigest()


def extract(image, rva, size):
    if type(rva) is not int or type(size) is not int or rva <= 0 or size <= 0:
        raise ValueError('invalid member identity')
    section, code = image.read(rva, size, 'private operand extraction')
    if not section.flags & 0x20000000:
        raise ValueError('member is not executable')
    fields, instructions, flags, end = imagemodel.field_records(
        code, rva, size, image.image_base, rva + size)
    if flags or end != size:
        raise ValueError('unsupported or incomplete instruction range')
    boundaries = {off for off, _ in instructions}
    references = []
    for off, width, kind, tail, target in fields:
        if kind != 'REL32' or width != 4:
            raise ValueError('unsupported reference kind')
        # Recalculate instead of trusting a decoder-provided target.
        actual = rva + off + width + tail + int.from_bytes(code[off:off+width], 'little', signed=True)
        if target != actual:
            raise ValueError('reference target disagrees')
        image.section_for(target)
        references.append(dict(offset=off, width=width, kind=kind, tail=tail, target_rva=target))
    rows, callbacks = [], []
    for off, ins in instructions:
        row = dict(offset=off, length=ins.length, opcode=list(ins.opcode),
                   flow=ins.flow, reg=ins.reg, base=ins.base, index=ins.index,
                   encoding=code[off:off+ins.length].hex(),
                   encoding_sha256=sha(code[off:off+ins.length]))
        if ins.imm:
            start, width = ins.imm
            raw = code[off+start:off+start+width]
            row['immediate'] = dict(offset=off+start, width=width,
                                    unsigned=int.from_bytes(raw, 'little'),
                                    signed=int.from_bytes(raw, 'little', signed=True))
        if ins.disp:
            start, width, value = ins.disp
            row['displacement'] = dict(offset=off+start, width=width, signed=value)
        if ins.rel is not None:
            target = ins.target - image.image_base
            if rva <= target < rva + size:
                if target-rva not in boundaries:
                    raise ValueError('local branch is not an instruction boundary')
                row['local_target'] = target-rva
        row['references'] = [ref for ref in references if off <= ref['offset'] < off+ins.length]
        if ins.flow == x64.ICALL:
            # A RIP target is an indirect-call slot, not the function it contains.
            callbacks.append(dict(instruction=off, slot_kind='rip' if ins.rip is not None else 'register-or-object',
                                  references=row['references'], base=ins.base, index=ins.index,
                                  displacement=row.get('displacement'), reg=ins.reg))
        rows.append(row)
    return dict(rva=rva, size=size, code_sha256=sha(code), instructions=rows,
                references=references, callback_slots=callbacks)


def annotate(member, roles):
    """Resolve private semantic annotations; absent/changed operands fail closed."""
    by_offset = {row['offset']: row for row in member['instructions']}
    measured, inferred = {}, {}
    for name, spec in roles.get('measured', {}).items():
        row = by_offset.get(spec['instruction'])
        if row is None or row['opcode'] != spec['opcode']:
            raise ValueError('semantic operand opcode differs: ' + name)
        field = spec['field']
        if field not in ('immediate', 'displacement', 'references', 'local_target') or field not in row:
            raise ValueError('semantic operand is absent: ' + name)
        measured[name] = dict(instruction=row['offset'], operand=row[field])
    for name, spec in roles.get('inferred', {}).items():
        evidence = spec['instructions']
        if not evidence or any(off not in by_offset for off in evidence):
            raise ValueError('inference has missing evidence: ' + name)
        inferred[name] = dict(description=spec['description'], instructions=evidence,
                              confidence=spec['confidence'], status='inferred-unverified')
    return dict(measured=measured, inferred=inferred)


def columns(members):
    """All correlated rows are retained; columns summarize variation only."""
    result = {}
    for member in members:
        for row in member['instructions']:
            for key, value in row.items():
                if key != 'offset':
                    result.setdefault(f'{row["offset"]}:{key}', set()).add(json.dumps(value, sort_keys=True))
    return {key: dict(distinct=len(values), values=[json.loads(v) for v in sorted(values)])
            for key, values in sorted(result.items())}


def private_output(path):
    path = Path(path).resolve()
    if '.local' not in path.parts:
        raise ValueError('extraction output must remain under .local')
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path('.local/verifier/config.json'))
    parser.add_argument('--target', type=Path, default=Path('builds/target.json'))
    parser.add_argument('--population', type=Path, required=True, help='private census group JSON')
    parser.add_argument('--roles', type=Path, help='private semantic operand annotations')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = private_output(args.out)
    target = json.loads(args.target.read_text())
    blob = Path(json.loads(args.config.read_text())['image']).read_bytes()
    if target.get('status') != 'pinned' or sha(blob) != target['image_sha256']:
        raise ValueError('image does not match pinned target')
    population = json.loads(args.population.read_text())
    roles = json.loads(args.roles.read_text()) if args.roles else {}
    image, seen, members = PeImage(blob), set(), []
    for entry in population['rows']:
        rva = int(entry['rva'], 16)
        size = int(entry['size'])
        if rva in seen or size != population['size']:
            raise ValueError('duplicate member or inconsistent extent')
        seen.add(rva)
        member = extract(image, rva, size)
        member['semantics'] = annotate(member, roles)
        members.append(member)
    if not members or len(members) != population['members']:
        raise ValueError('population count disagrees')
    result = dict(schema=1, build_id=target['build_id'], image_sha256=sha(blob),
                  extractor_sha256=sha(Path(__file__).read_bytes()),
                  population_sha256=sha(args.population.read_bytes()),
                  roles_sha256=sha(args.roles.read_bytes()) if args.roles else None,
                  limitations='Operand facts and labelled hypotheses only; no source, behavior or match proof.',
                  members=members, columns=columns(members))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + '\n')
    print(f'Extracted {len(members)} members; {len(result["columns"])} operand columns; private output only.')


if __name__ == '__main__':
    main()
