"""Rank a private instruction-shape census after explicit population exclusions.

Shape keys come from the existing whole-image census. Adding the measured size
prevents its padding-insensitive skeleton from merging different extents. This
is a planning aid, never a comparator or evidence of source equivalence.
"""
import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path


def rank(rows, excluded_rvas=(), excluded_masked=()):
    excluded_rvas, excluded_masked = set(excluded_rvas), set(excluded_masked)
    groups = collections.defaultdict(list)
    seen = set()
    for row in rows:
        rva = int(row['rva'], 16)
        if rva in seen:
            raise ValueError('duplicate census identity')
        seen.add(rva)
        if (row['kind'] == 'eh-funclet' or rva in excluded_rvas
                or row['masked'] in excluded_masked or not row['shape']):
            continue
        size = int(row['size'])
        if size <= 0:
            raise ValueError('non-positive function extent')
        groups[(row['shape'], size)].append(row)
    result = []
    for (shape, size), members in groups.items():
        members.sort(key=lambda row: int(row['rva'], 16))
        result.append(dict(shape=shape, size=size, members=len(members),
                           bytes=size * len(members),
                           named=sum(bool(row['names']) for row in members),
                           kinds=dict(collections.Counter(row['kind'] for row in members)),
                           families=dict(collections.Counter(row['family'] for row in members)),
                           rows=members))
    result.sort(key=lambda group: (-group['members'], -group['bytes'], group['shape']))
    byte_order = sorted(result, key=lambda group: (-group['bytes'], -group['members'], group['shape']))
    for i, group in enumerate(byte_order, 1):
        group['byte_rank'] = i
    for i, group in enumerate(result, 1):
        group.update(count_rank=i, label=f'F{i:03d}')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--census', type=Path, required=True)
    parser.add_argument('--exclusions', type=Path, required=True,
                        help='private JSON with rvas and masked keys')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if '.local' not in out.parts:
        parser.error('census outputs must remain under .local')
    exclusions = json.loads(args.exclusions.read_text())
    with args.census.open(newline='') as file:
        groups = rank(list(csv.DictReader(file, delimiter='\t')),
                      exclusions['rvas'], exclusions['masked'])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(dict(
        census_sha256=hashlib.sha256(args.census.read_bytes()).hexdigest(),
        exclusions_sha256=hashlib.sha256(args.exclusions.read_bytes()).hexdigest(),
        groups=groups), indent=2) + '\n')
    print(f'{len(groups)} groups; {sum(g["members"] for g in groups)} functions; '
          f'{sum(g["bytes"] for g in groups)} bytes')


if __name__ == '__main__':
    main()
