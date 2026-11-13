import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import lint_reconstruction
import static_resource_generate as generator
import static_resource_template_v1 as template
import static_context_resource_template_v2 as initializer_v2


def rows(*texts):
    return [[0, '', text, []] for text in texts]


class StaticResourceGeneratorTest(unittest.TestCase):
    def test_initializer_extracts_each_cleanup_and_tls_binding(self):
        code = rows('call 0x1010', 'lea rcx, [rip] # 0x1020',
                    'mov edx, 0x30', 'lea rcx, [rip] # 0x1040', 'jmp 0x1050')
        actions = [0x60, 0x70]
        helpers = [rows('call 0x1080'), rows('jmp 0x1090')]
        self.assertEqual(generator.extract(code, 0x1000, 0x7c40, actions, helpers),
                         {'manager-rva': 16, 'atexit-rva': 80, 'object-rva': 32,
                          'teardown-rva': 64, 'tls-offset': 48,
                          'storage-destroy-rva': 128, 'context-destroy-rva': 144})
        for bad_code, bad_actions, bad_helpers in (
                (code[:-1], actions, helpers), (code, actions[:1], helpers),
                (code, actions, [rows(), helpers[1]]),
                (code + rows('mov edx, 0x31'), actions, helpers),
                (code, actions, [rows('call 0x1080', 'call 0x1090'), helpers[1]])):
            with self.assertRaises(ValueError):
                generator.extract(bad_code, 0x1000, 0x7c40, bad_actions, bad_helpers)

    def test_teardown_extracts_runtime_action_without_copying_seed_addresses(self):
        code = rows('call 0x1110', 'lea rcx, [rip] # 0x1120',
                    'lea rcx, [rip] # 0x1130', 'lea rcx, [rip] # 0x1130', 'call 0x1140')
        result = generator.extract(code, 0x1000, 0x173c120, [0x150], [])
        self.assertEqual(result, {'manager-rva': 0x110, 'cleanup-rva': 0x140,
                                 'empty-rva': 0x120, 'object-rva': 0x130,
                                 'terminate-rva': 0x150})
        with self.assertRaises(ValueError):
            generator.extract(code, 0x1000, 0x173c120, [], [])
        with self.assertRaises(ValueError):
            generator.extract(code[:3] + rows('lea rcx, [rip] # 0x1150') + code[4:],
                              0x1000, 0x173c120, [0x150], [])
        with self.assertRaises(ValueError):
            generator.extract(code, 0x1000, 0x8640, [0x150], [])

    def test_revised_initializer_discloses_possible_sibling_lineage_in_every_file(self):
        cls, header, cpp, origin, _ = initializer_v2.emit(0x7c40, 106, 0x7c40)
        for text in (header, cpp):
            self.assertIn('Sibling source: momusdigital/fnv_decomp@91e1b6e8', text)
            self.assertIn('src/staging/blk_00cc0000_o2.cpp:13192', text)
            self.assertIn('no licence is granted', text)
            self.assertNotIn('no external implementation source reused', text)
        self.assertEqual(origin['version'], '2')
        self.assertNotEqual(origin['template_digest'], template.template_digest())
        with self.assertRaises(ValueError):
            initializer_v2.emit(0x173c120, 67, 0x173c120)

    def test_distinct_families_lint_and_limit_claim_scope(self):
        origins = []
        for producer, cluster, size, wording in ((template, 0x7c40, 106, 'Only the generated initializer'),
                                       (template, 0x173c120, 67, 'Only the generated teardown'),
                                       (initializer_v2, 0x7c40, 106, 'Only the generated initializer')):
            cls, header, cpp, origin, params = producer.emit(cluster, size, cluster)
            origins.append(origin)
            self.assertIn(wording, header)
            self.assertEqual(params, {'entry-rva': cluster, 'size': size})
            self.assertEqual(origin['template_digest'], producer.template_digest())
            with tempfile.TemporaryDirectory() as d:
                root = Path(d)
                (root / 'builds').mkdir()
                (root / 'builds/target.json').write_text((ROOT / 'builds/target.json').read_text())
                evidence = root / template.EVIDENCE
                evidence.parent.mkdir(parents=True); evidence.write_text('fixture')
                recipe = root / template.RECIPE
                recipe.parent.mkdir(parents=True); recipe.write_text('{}')
                area = root / 'reconstruction/static'; area.mkdir()
                (area / f'{cls}.h').write_text(header)
                (area / f'{cls}.cpp').write_text(cpp)
                self.assertEqual(lint_reconstruction.lint_tree(root), [])
            with self.assertRaises(ValueError):
                producer.emit(cluster, size + 1, cluster)
        self.assertNotEqual(origins[0]['family'], origins[1]['family'])
