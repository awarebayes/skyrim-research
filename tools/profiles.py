#!/usr/bin/env python3
"""Operating profiles: which model does each role, and which documents, kit and attempt limits a
Drafter gets. The data is tools/profiles.json; model ids live only there, since they change.

    python3 tools/profiles.py                 # one line per profile: rough cost
    python3 tools/profiles.py --show <name>   # roles (provider, model, effort, harness), documents, limits
    python3 tools/profiles.py --json

Roles: `orchestrator` (drives docs/orchestrator-runbook.md), `drafter`, `reviewer`, `strong`
(triage of near-misses and rejects, direction checks, tooling). A profile is an operating choice,
never a match criterion: every profile's output passes the same comparator, two-host
confirmation, lint and Reviewer gate (docs/verification.md). A Reviewer model the acceptance rule
does not admit is refused by tools/flow.py whatever a profile says.

`cheap` is the default because weak-model drafting on the small card, skeleton and sheet kit passes
the same gate at a fraction of the cost. The default stays conditional on that evidence: the
friction report (tools/friction.py) shows the pass rate per profile and flags the cheap profile
below `cheap_min_pass_rate`, and a direction check then recommends flipping the default back.
"""
import argparse
import json
from pathlib import Path

DATA = json.loads((Path(__file__).resolve().parent / 'profiles.json').read_text())
DEFAULT = DATA['default']
CHEAP_MIN_PASS_RATE = DATA['cheap_min_pass_rate']
PROFILES = DATA['profiles']
ROLES = ('orchestrator', 'drafter', 'reviewer', 'strong')


def get(name=None):
    name = name or DEFAULT
    if name not in PROFILES:
        raise ValueError(f'unknown profile {name!r}; choose one of {", ".join(sorted(PROFILES))}')
    return dict(PROFILES[name], name=name)


def role(name, which):
    """The role entry (provider, model, effort, harness) of a profile."""
    return get(name)['roles'][which]


def model_label(entry):
    return f'{entry["model"]}' + (f' ({entry["effort"]})' if entry.get('effort') else '') + f' via {entry["harness"]}'


def cost_lines():
    return [PROFILES[n]['cost'] + (' [default]' if n == DEFAULT else '') for n in PROFILES]


def show(name):
    p = get(name)
    lines = [f'profile {name}: {p["summary"]}']
    for r in ROLES:
        e = p['roles'][r]
        alt = '; or ' + ', '.join(model_label(a) for a in e.get('alternatives', [])) if e.get('alternatives') else ''
        lines.append(f'  {r}: {model_label(e)}{alt}' + (f'  [needs: {e["requires"]}]' if e.get('requires') else ''))
    lines += [f'  drafter documents: {", ".join(p["project_docs"])}', f'  kit: {p["kit"]}',
              f'  queue: {p["queue_dir"]}; stuck after {p["stuck_after"]} attempts without progress',
              f'  {p["cost"]}']
    return lines


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument('--json', action='store_true')
    p.add_argument('--show')
    a = p.parse_args(argv)
    try:
        if a.json:
            print(json.dumps(DATA, indent=2))
        elif a.show:
            print('\n'.join(show(a.show)))
        else:
            print('\n'.join(cost_lines()))
    except ValueError as exc:
        print(f'profiles: {exc}')
        return 2
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
