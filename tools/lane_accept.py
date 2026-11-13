#!/usr/bin/env python3
"""Prepare lane requests through the ordinary acceptance gates; apply and index once."""
import argparse
import copy
import json
from pathlib import Path
import accept_function as af
from check_source_digest import source_digest_cache


@source_digest_cache()
def accept(root, requests, when=None, *, prepare_only=False):
    root = Path(root)
    when = when or af.now_utc()
    data, target = af.load(root)
    plans, dropped, selected = [], [], set()
    def prepare_request(member):
        if member['kind'] == 'family':
            return af.accept_family_batch(root, member['path'], when, member['profile'],
                                          root / '.local/flow', prepare_only=True)
        if member['kind'] == 'label':
            ids = af.resolve_selection(root, data, member['functions'])
            return af.label_only(root, ids, when, prepare_only=True)
        return af.accept_reviews(root, [member], when, prepare_only=True)

    def add(member, plan):
        af.refuse(bool(plan), 'nothing to accept')
        ids = {fn['id'] for _, fn, _, _ in plan[3]}
        af.refuse(not selected & ids, 'lane selections overlap')
        selected.update(ids)
        plans.append((member, plan))

    reviews = [r for r in requests if r['kind'] == 'review']
    errors = (af.Refused, ValueError, KeyError, TypeError, OSError)
    try:
        # Normal path: p101's one validation across every individually reviewed request.
        if reviews:
            plan = af.accept_reviews(root, reviews, when, prepare_only=True)
            ids = {fn['id'] for _, fn, _, _ in plan[3]}
            selected.update(ids)
            plans.append((reviews, plan))
        remaining = [r for r in requests if r['kind'] != 'review']
    except errors:
        remaining = requests
    for request in remaining:
        try:
            add(request, prepare_request(request))
        except errors as error:
            # A family defect holds the batch; do not shrink its committed population.
            if request['kind'] == 'family':
                dropped.append(dict(request=request, reason=str(error)))
                continue
            for function in request['functions']:
                member = dict(request, functions=[function])
                try:
                    add(member, prepare_request(member))
                except errors as member_error:
                    dropped.append(dict(request=member, reason=str(member_error)))
    if not plans:
        return dict(changed=[], accepted=[], dropped=dropped)
    new, prepared = copy.deepcopy(data), []
    for member, plan in plans:
        for index, fn, record, review in plan[3]:
            new['functions'][index] = plan[1]['functions'][index]
            prepared.append((index, fn, record, review))
    accepted = [member for members, _ in plans for member in (members if isinstance(members, list) else [members])]
    result = dict(changed=[], accepted=accepted, dropped=dropped)
    # If any member failed, the runner first re-carries only the successes. No index is written yet.
    if not prepare_only and not dropped:
        result['changed'] = af.apply(root, data, new, target, prepared, af.stale_ids(root, data) - selected, when)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--requests', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True)
    p.add_argument('--prepare-only', action='store_true')
    args = p.parse_args()
    inputs = json.loads(args.requests.read_text())
    result = accept(args.root, inputs, prepare_only=args.prepare_only)
    args.result.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
