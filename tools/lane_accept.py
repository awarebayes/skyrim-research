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
    with af.acceptance_batch(root):
        return _accept(root, requests, when, prepare_only=prepare_only)


def _accept(root, requests, when=None, *, prepare_only=False):
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
        return af.accept_reviews(root, [member], when, prepare_only=True, carry_accepted=True)

    def add(member, plan):
        af.refuse(bool(plan), 'nothing to accept')
        ids = {fn['id'] for _, fn, _, _ in plan[3]}
        af.refuse(not selected & ids, 'lane selections overlap')
        selected.update(ids)
        plans.append((member, plan))

    errors = (af.Refused, ValueError, KeyError, TypeError, OSError)
    saved, committed, provisional = {}, False, False
    stale_before = af.stale_ids(root, data)

    def remember(prepared):
        names = [af.PROGRESS, af.INDEX] + [af.review_record_path(fn) for _, fn, _, rv in prepared if rv is not None]
        for name in names:
            if name not in saved:
                path = root / name
                saved[name] = path.read_bytes() if path.is_file() else None

    def combine():
        new, prepared = copy.deepcopy(data), []
        for _, plan in plans:
            for index, fn, record, review in plan[3]:
                new['functions'][index] = plan[1]['functions'][index]
                prepared.append((index, fn, record, review))
        return new, prepared

    def prepare_individually(request):
        try:
            add(request, prepare_request(request))
        except errors as error:
            if request['kind'] == 'family':
                dropped.append(dict(request=request, reason=str(error)))
                return
            for function in request['functions']:
                member = dict(request, functions=[function])
                try:
                    add(member, prepare_request(member))
                except errors as member_error:
                    dropped.append(dict(request=member, reason=str(member_error)))

    try:
        reviews = [r for r in requests if r['kind'] == 'review']
        try:
            # p101's single preparation across individually reviewed requests remains the fast path.
            if reviews:
                plan = af.accept_reviews(root, reviews, when, prepare_only=True, carry_accepted=True)
                selected.update(fn['id'] for _, fn, _, _ in plan[3])
                plans.append((reviews, plan))
        except errors:
            for request in reviews:
                prepare_individually(request)
        for request in requests:
            if request['kind'] == 'label':
                prepare_individually(request)
        families = [r for r in requests if r['kind'] == 'family']
        if families and plans:
            new, prepared = combine()
            remember(prepared)
            # Use the ordinary transactional writer and every validator check. Only the derived
            # index waits until the final combined apply. The family gate then sees staged sample
            # approvals, including their private parser and second-pass/rerun safeguards.
            provisional = True
            af.apply(root, data, new, target, prepared, stale_before - selected, when,
                     rebuild_index=False, stage_only=True)
        for request in families:
            prepare_individually(request)
        if not plans:
            return dict(changed=[], accepted=[], dropped=dropped)
        new, prepared = combine()
        remember(prepared)
        accepted = [member for members, _ in plans for member in (members if isinstance(members, list) else [members])]
        result = dict(changed=[], accepted=accepted, dropped=dropped)
        # Failed members are re-carried by the runner; planning never leaves provisional matches.
        if not prepare_only and not dropped:
            result['changed'] = af.apply(root, data, new, target, prepared, stale_before - selected, when)
            committed = True
        return result
    finally:
        if not committed and provisional:
            for name, before in saved.items():
                path = root / name
                if before is None:
                    path.unlink(missing_ok=True)
                else:
                    path.write_bytes(before)
            af.invalidate_acceptance_batch(root)


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
