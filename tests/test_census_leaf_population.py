import sys
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import census_leaf_population as generator
import census_leaf_population_template_v1 as template
import lint_reconstruction
import accept_function
import family_review


def rows(*instructions):
    return [[0, '', instruction, []] for instruction in instructions]


class PopulationTests(unittest.TestCase):
    def test_exact_member_reference_and_complete_shape(self):
        self.assertEqual(generator.extract(rows('jmp 0x1234'), 0x1000, 'forward'), {'target-rva': 0x234})
        self.assertEqual(generator.extract(rows('lea rax, [rip + 0x10] # 0x1456', 'ret'),
                                           0x1000, 'address'), {'target-rva': 0x456})
        for kind, instructions in [('forward', rows('call 0x1234')), ('forward', rows('jmp 0x100')),
                                   ('forward', rows('jmp 0x1234', 'ret')),
                                   ('address', rows('lea rcx, [rip] # 0x1456', 'ret')),
                                   ('address', rows('lea rax, [rip] # 0x1456'))]:
            with self.assertRaises(ValueError):
                generator.extract(instructions, 0x1000, kind)

    def test_both_templates_preserve_unknown_ownership_and_lint(self):
        for kind, size in [('forward', 5), ('address', 8)]:
            owner, method, h, cpp, symbol, external = template.emit(kind, 0x1234, size)
            self.assertIn('Owning system and original signature are unknown', h)
            self.assertIn('GUESS(low) STANDIN', cpp)
            self.assertIn(external.split('@')[1] if external.startswith('?') else external, cpp)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                for name in ('builds/target.json', template.RECIPE, template.EVIDENCE):
                    path = root / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes((ROOT / name).read_bytes())
                area = root / 'reconstruction/leaves'
                area.mkdir(parents=True)
                (area / f'{owner}.h').write_text(h)
                (area / f'{owner}.cpp').write_text(cpp)
                self.assertEqual(lint_reconstruction.lint_tree(root), [])

    def test_no_source_overwrite_and_no_wrong_extent(self):
        for kind, size in [('forward', 8), ('address', 5)]:
            with self.assertRaises(ValueError):
                template.emit(kind, 0x1234, size)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'unit.cpp'
            generator.write_new(path, 'first')
            with self.assertRaises(ValueError):
                generator.write_new(path, 'second')

    def test_report_linking_is_atomic_for_missing_population_or_wrong_metadata(self):
        for failure in ('missing-member', 'wrong-last-binding'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                out = root / '.local/cohort'
                out.mkdir(parents=True)
                progress = dict(functions=[dict(id=f'fixture-{rva}', rva=rva) for rva in range(20)])
                data = root / 'data/progress.json'
                data.parent.mkdir()
                data.write_text('unchanged inventory')
                tasks, parameters = [], {}
                for rva in range(20):
                    task = out / str(rva)
                    task.mkdir()
                    params = dict(rva=rva, size=5, kind='forward', **{'target-rva': 100 + rva})
                    metadata = dict(origin=template.origin('forward'), family_parameters=params, name_source='GUESS(low)')
                    (task / 'task.json').write_text(json.dumps(dict(functions=[dict(rva=rva, family_metadata=metadata)])))
                    tasks.append(str(task))
                    parameters[rva] = metadata
                (out / 'all.txt').write_text('\n'.join(tasks))
                members = list(range(21 if failure == 'missing-member' else 20))
                (out / 'population.json').write_text(json.dumps(dict(build_id=template.BUILD, members=members)))

                def record(fn, *_):
                    result = dict(parameters[fn['rva']])
                    if failure == 'wrong-last-binding' and fn['rva'] == 19:
                        result['name_source'] = 'GUESS(high)'
                    return result

                with patch.object(generator, 'ROOT', root), patch.object(accept_function, 'load', return_value=(progress, {})), \
                        patch.object(accept_function, 'validate_match', side_effect=record), \
                        patch.object(family_review, 'binding', return_value={'synthetic': True}):
                    with self.assertRaises(ValueError):
                        generator.records_to_spec('forward', out)
                self.assertEqual(data.read_text(), 'unchanged inventory')
                self.assertFalse((out / 'family-spec.json').exists())
                self.assertTrue(all('report' not in fn for fn in progress['functions']))
