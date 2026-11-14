#!/usr/bin/env python3
"""Additional pre-review hygiene, separate from validator/acceptance predicates."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import lint_reconstruction as existing


def origin_statement_problems(name, text):
    header = existing.leading_comment(text)
    statement = re.search(r'\b(?:original implementation|original reconstruction|original declarations|'
                          r'original code|original work|adapted from|derived from|reconstructed from|generated from)\b', header, re.I)
    # A name-origin label or "Source exposure" alone says nothing about the code's origin.
    explicit = re.search(r'^\s*(?://+|/\*+|\*+)?\s*(?:body origin|implementation origin|code origin|provenance|origin)\s*:\s*\S',
                         header, re.I | re.M)
    if not explicit and not statement:
        return [f'{name}: missing reconstruction origin statement in leading header']
    return []


def truncated_mit_problems(name, text):
    problems = []
    for run in existing.comment_runs(text):
        joined = existing.normalised(' '.join(run))
        if not re.search(r'\b(?:MIT licen[cs]e|permission is hereby|the software is provided|in no event shall)\b', joined, re.I):
            continue
        start = joined.find(existing.MIT_BODY_START)
        end = joined.find(existing.MIT_BODY_END, max(start, 0))
        complete = start >= 0 and end >= 0 and 'Copyright' in joined[:start]
        if complete:
            body = joined[start:end + len(existing.MIT_BODY_END)]
            complete = hashlib.sha256(body.encode()).hexdigest() == existing.MIT_BODY_SHA256
        if not complete:
            problems.append(f'{name}: truncated or altered MIT notice; retain the complete copyright, permission and disclaimer')
    return problems


def lint_files(root, names):
    root = Path(root).resolve()
    problems = []
    for name in sorted(set(names)):
        path = root / name
        if path.suffix not in ('.h', '.cpp'):
            continue
        if not path.resolve().is_relative_to(root) or not path.is_file():
            problems.append(f'{name}: source path missing or outside repository')
            continue
        text = path.read_text()
        problems += origin_statement_problems(name, text)
        problems += truncated_mit_problems(name, text)
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=existing.ROOT)
    parser.add_argument('--functions', nargs='+')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args(argv)
    names = list(args.files)
    try:
        if args.functions:
            data = json.loads((args.root / 'data/progress.json').read_text())
            wanted = set(args.functions)
            selected = []
            for value in sorted(wanted):
                matches = [fn for fn in data['functions'] if value in (fn['id'], hex(fn['rva']))]
                if len(matches) != 1:
                    raise ValueError(f'{value}: expected exactly one function identity; found {len(matches)}')
                selected += matches
            for fn in selected:
                record = json.loads((args.root / fn['report']).read_text())
                names += record['source']['translation_unit']
        if not names:
            parser.error('supply files or --functions')
        problems = lint_files(args.root, names)
    except (ValueError, OSError, KeyError) as error:
        problems = [str(error)]
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == '__main__':
    raise SystemExit(main())
