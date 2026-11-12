"""Tests for tools/verifier/permute.py on original synthetic C++ (no game data, no Boat machine)."""
import copy
import difflib
import json
from pathlib import Path
import random
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import permute  # noqa: E402

# An original toy unit: a counter with a lookup, written for these tests.
UNIT = '''// toy unit
#include "Toy.h"

int Helper(int a_value);

bool Toy::Probe(Node* a_node, unsigned int a_limit)
{
    // leading comment kept with the first statement
    int total = 0;
    unsigned int count;
    Node* next = a_node->next;
    Fill(&count);
    if (a_node == nullptr) {
        return false;
    }
    if (a_node->flags & 4) {
        total = Helper(a_node->value);
    } else {
        total = a_node->value + 1;
    }
    for (unsigned int i = 0; i < a_limit; ++i) {
        total += Helper(i);
    }
    while (next) {
        next = next->next;
    }
    if (total > 3 && a_limit != 0) {
        count = a_limit;
        count++;
    }
    Helper(a_node->value);
    int kind = a_node->kind;
    switch (kind) {
    case 1:
        return true;
    default:
        break;
    }
    return total < static_cast<int>(a_limit) + a_node->value;
}

int Toy::Other()
{
    return Value() + 1;
}
'''


def body_unit():
    return permute.Unit(UNIT, 'Toy::Probe')


class Tokens(unittest.TestCase):
    def test_round_trip(self):
        toks, tail = permute.lex(UNIT)
        self.assertEqual(permute.emit_toks(toks) + tail, UNIT)

    def test_find_body_and_parse(self):
        u = body_unit()
        self.assertTrue(UNIT[u.start:u.end].startswith('{'))
        self.assertTrue(UNIT[u.start:u.end].rstrip().endswith('}'))
        self.assertEqual(u.with_body(u.body_of(u.block)), UNIT)
        kinds = [type(s).__name__ for s in u.block.stmts]
        self.assertEqual(kinds, ['Simple', 'Simple', 'Simple', 'Simple', 'If', 'If', 'Loop', 'Loop', 'If', 'Simple',
                                 'Simple', 'Loop', 'Simple'])

    def test_several_bodies(self):
        u = permute.Unit(UNIT, 'Toy::Probe', ['Toy::Other'])
        self.assertEqual(len(u.spans), 2)
        self.assertEqual(u.with_body(u.body_of(u.forest())), UNIT)
        forest = copy.deepcopy(u.forest())
        rng = random.Random(2)
        names = []
        for _ in range(40):
            names += permute.mutate_forest(forest, rng, 1)
        text = u.with_body(u.body_of(forest))
        permute.Unit(text, 'Toy::Probe', ['Toy::Other'])
        self.assertTrue(any(n.endswith('@1') for n in names), names)
        self.assertTrue(any('@' not in n for n in names), names)
        with self.assertRaises(ValueError):
            permute.Unit(UNIT, 'Toy::Probe', ['Toy::Probe'])

    def test_out_init(self):
        src = 'void T::F()\n{\n    char* message = nullptr;\n    Format(&message);\n    Free(message);\n}\n'
        u = permute.Unit(src, 'T::F')
        tree = copy.deepcopy(u.block)
        self.assertTrue(permute.m_out_init(tree, random.Random(0)))
        self.assertIn('char* message;', u.body_of(tree))
        self.assertTrue(permute.m_out_init(tree, random.Random(0)))
        self.assertIn('char* message = nullptr;', u.body_of(tree))

    def test_definition_must_be_unique(self):
        with self.assertRaises(ValueError):
            permute.find_body(UNIT + '\nbool Toy::Probe(Node* a, unsigned int b)\n{\n    return true;\n}\n',
                              'Toy::Probe')
        with self.assertRaises(ValueError):
            permute.find_body(UNIT, 'Toy::Missing')

    def test_decl_info(self):
        u = body_unit()
        names = [permute.decl_info(s) and permute.decl_info(s)[1] for s in u.block.stmts[:3]]
        self.assertEqual(names, ['total', 'count', 'next'])
        self.assertIsNone(permute.decl_info(u.block.stmts[-1]))


def apply_one(name, seed=0):
    u = body_unit()
    tree = copy.deepcopy(u.block)
    rng = random.Random(seed)
    for _ in range(20):
        if permute.MUTATIONS[name][0](tree, rng):
            return u.body_of(tree)
    return None


def diff(a, b):
    return [line for line in difflib.ndiff(a.splitlines(), b.splitlines()) if line[:1] in '+-']


class Mutations(unittest.TestCase):
    def test_every_mutation_applies_and_reparses(self):
        base = body_unit().body_of(body_unit().block)
        for name in permute.MUTATIONS:
            with self.subTest(name=name):
                out = apply_one(name)
                self.assertIsNotNone(out, f'{name} found no site in the toy unit')
                self.assertNotEqual(out, base)
                block, tail = permute.parse_body(out)
                self.assertEqual(permute.emit(block, tail), out)

    def test_if_invert(self):
        out = apply_one('if-invert')
        self.assertIn('if (!(a_node->flags & 4))', ' '.join(out.split()))

    def test_compare_flip(self):
        u = body_unit()
        tree = copy.deepcopy(u.block)
        lst = tree.stmts[4].cond
        site = permute.binary_sites(lst, set(permute.FLIP))[0]
        permute.swap_operands(lst, *site, permute.FLIP[lst[site[1]].text])
        self.assertEqual(permute.emit_toks(lst).strip(), 'nullptr == a_node')

    def test_template_angle_is_not_a_comparison(self):
        toks, _ = permute.lex('return total < static_cast<int>(a_limit);')
        sites = permute.binary_sites(toks, set(permute.FLIP))
        self.assertEqual(sites, [])

    def test_declaration_is_not_a_product(self):
        src = 'void T::F()\n{\n    Zone* zone;\n    Zone& ref = Get();\n    int n = a * b;\n}\n'
        u = permute.Unit(src, 'T::F')
        sites = permute.expr_sites(u.block, permute.COMMUTE)
        self.assertEqual([permute.emit_toks(lst[s:e]).strip() for lst, (s, k, e) in sites], ['a * b'])

    def test_loop_form_round(self):
        u = body_unit()
        tree = copy.deepcopy(u.block)
        rng = random.Random(3)
        seen = set()
        for _ in range(40):
            t = copy.deepcopy(tree)
            if permute.m_loop_form(t, rng):
                seen.add(' '.join(u.body_of(t).split()))
        joined = '\n'.join(seen)
        self.assertIn('while ( i < a_limit) {', joined.replace('while (i', 'while ( i'))
        self.assertIn('for (; next;)', joined.replace('for (;next;)', 'for (; next;)'))

    def test_early_return_nest_and_flatten(self):
        src = 'void T::F(int a)\n{\n    if (a) {\n        return;\n    }\n    G();\n}\n'
        u = permute.Unit(src, 'T::F')
        tree = copy.deepcopy(u.block)
        self.assertTrue(permute.m_early_return(tree, random.Random(0)))
        nested = ' '.join(u.body_of(tree).split())
        self.assertIn('else {', nested)
        self.assertTrue(permute.m_early_return(tree, random.Random(0)))
        self.assertEqual(' '.join(u.body_of(tree).split()), ' '.join(u.body_of(u.block).split()))

    def test_temp_inline_single_use(self):
        src = 'int T::F(P* p)\n{\n    int v = p->Get();\n    return v + 1;\n}\n'
        u = permute.Unit(src, 'T::F')
        tree = copy.deepcopy(u.block)
        self.assertTrue(permute.m_temp_inline(tree, random.Random(0)))
        self.assertEqual(' '.join(u.body_of(tree).split()), '{ return static_cast<int>(p->Get()) + 1; }')

    def test_temp_inline_refuses_written_local(self):
        src = 'int T::F(P* p)\n{\n    int v = p->Get();\n    v += 2;\n    return v;\n}\n'
        u = permute.Unit(src, 'T::F')
        self.assertFalse(permute.m_temp_inline(copy.deepcopy(u.block), random.Random(0)))

    def test_temp_introduce_names_a_repeated_member(self):
        src = 'int T::F(P* p)\n{\n    G(p->m);\n    return p->m;\n}\n'
        u = permute.Unit(src, 'T::F')
        tree = copy.deepcopy(u.block)
        self.assertTrue(permute.m_temp_introduce(tree, random.Random(0)))
        self.assertEqual(' '.join(u.body_of(tree).split()), '{ auto v0 = p->m; G(v0); return v0; }')

    def test_temp_introduce_refuses_written_member(self):
        src = 'int T::F(P* p)\n{\n    G(p->m);\n    p->m = 2;\n    return p->m;\n}\n'
        u = permute.Unit(src, 'T::F')
        self.assertFalse(permute.m_temp_introduce(copy.deepcopy(u.block), random.Random(0)))

    def test_and_split_and_join(self):
        src = 'void T::F(int a, int b)\n{\n    if (a && b) {\n        G();\n    }\n}\n'
        u = permute.Unit(src, 'T::F')
        tree = copy.deepcopy(u.block)
        self.assertTrue(permute.m_and_split(tree, random.Random(0)))
        self.assertEqual(' '.join(u.body_of(tree).split()), '{ if (a) { if (b) { G(); } } }')
        self.assertTrue(permute.m_and_split(tree, random.Random(1)))
        self.assertEqual(' '.join(u.body_of(tree).split()), '{ if (a && b) { G(); } }')

    def test_increment_forms(self):
        src = 'void T::F(int i)\n{\n    i++;\n}\n'
        u = permute.Unit(src, 'T::F')
        outs = set()
        for seed in range(12):
            tree = copy.deepcopy(u.block)
            permute.m_increment(tree, random.Random(seed))
            outs.add(' '.join(u.body_of(tree).split()))
        self.assertEqual(outs, {'{ ++i; }', '{ i += 1; }', '{ i = i + 1; }'})

    def test_int_type_and_switch_width(self):
        src = 'void T::F(int a)\n{\n    std::uint32_t n = 0;\n    switch (a) {\n    default:\n        break;\n    }\n}\n'
        u = permute.Unit(src, 'T::F')
        outs = set()
        for seed in range(30):
            tree = copy.deepcopy(u.block)
            permute.m_int_type(tree, random.Random(seed))
            outs.add(' '.join(u.body_of(tree).split()))
        self.assertTrue(any('std::int32_t n' in o for o in outs))
        self.assertTrue(any('switch (static_cast<std::uint32_t>(a))' in o for o in outs))

    def test_deterministic_for_a_seed(self):
        def run(seed):
            u = body_unit()
            tree = copy.deepcopy(u.block)
            applied = permute.mutate(tree, random.Random(seed), 4)
            return applied, u.body_of(tree)
        self.assertEqual(run(7), run(7))
        self.assertNotEqual(run(7), run(8))

    def test_random_stacks_always_reparse(self):
        u = body_unit()
        rng = random.Random(11)
        for _ in range(300):
            tree = copy.deepcopy(u.block)
            permute.mutate(tree, rng, rng.randint(1, 5))
            out = u.body_of(tree)
            block, tail = permute.parse_body(out)
            self.assertEqual(permute.emit(block, tail), out)
            permute.Unit(u.with_body(out), 'Toy::Probe')


class Payload(unittest.TestCase):
    def test_round_trip(self):
        obj = {'cands': [['v00001', '{ return 1; }']], 'span': [3, 9]}
        self.assertEqual(permute.decode_payload(permute.encode_payload(obj)), obj)

    def test_function_hash_ignores_nothing_but_addresses_and_text(self):
        a = '   0: 48 89 5c 24 08\tmov qword ptr [rsp + 0x8], rbx\n   5: c3\tret\n'
        b = '   0: 48 89 5c 24 08\tmov qword ptr [rsp+8], rbx\n   5: c3\tret\n'
        c = '   0: 48 89 5c 24 10\tmov qword ptr [rsp + 0x10], rbx\n   5: c3\tret\n'
        self.assertEqual(permute.function_hash(a), permute.function_hash(b))
        self.assertNotEqual(permute.function_hash(a), permute.function_hash(c))


class SearchLoop(unittest.TestCase):
    """The search against a local scorer: distance = token edits to a hidden target body."""

    def scorer_for(self, target_body):
        target = [t.text for t in permute.lex(target_body)[0]]

        def score(cands):
            rows = []
            for c in cands:
                toks = [t.text for t in permute.lex('\n'.join(c['body']))[0]]
                sm = difflib.SequenceMatcher(a=target, b=toks, autojunk=False)
                d = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != 'equal')
                rows.append({'id': c['id'], 'st': 'ok', 'd': d, 'ex': d, 'n': len(toks), 'nt': len(target),
                             'h': str(hash(tuple(toks)))})
            return rows
        return score

    def test_recovers_perturbed_bodies(self):
        # Two random rule steps away from the target, as in the recovery test of docs/ideas-next.md
        # P3. The scorer here compares text, so the perturbation uses only rules whose inverse
        # spelling is in the catalogue (an inlined temporary comes back as a cast, never as the
        # original declaration, although the object code may well be the same).
        invertible = ['decl-swap', 'decl-move', 'decl-split', 'if-invert', 'early-return', 'and-split',
                      'compare', 'commute', 'test-form', 'increment']
        u = body_unit()
        target_body = u.body_of(u.block)
        recovered = 0
        for seed in range(6):
            start = copy.deepcopy(u.block)
            permute.mutate(start, random.Random(seed), 2, names=invertible)
            perturbed = permute.Unit(u.with_body(u.body_of(start)), 'Toy::Probe')
            search = permute.Search(perturbed, self.scorer_for(target_body), lambda text: [], random.Random(1),
                                    batch=24, patience=20, budget=10 ** 6, log=lambda m: None)
            result = search.run()
            self.assertLessEqual(result['best']['d'], result['start']['d'])
            recovered += result['status'] == 'distance-0'
        self.assertGreaterEqual(recovered, 4)

    def test_lint_gate_drops_candidates(self):
        u = body_unit()
        calls = []

        def lint(text):
            calls.append(text)
            return [] if text == UNIT else ['refused']
        search = permute.Search(u, self.scorer_for('{ return 0; }'), lint, random.Random(1),
                                batch=4, patience=2, budget=10 ** 6, log=lambda m: None)
        result = search.run()
        self.assertEqual(result['candidates'], 1)  # only the base was scored
        self.assertGreater(result['lint_rejected'], 0)
        self.assertEqual(result['status'], 'patience')

    def test_base_must_pass_lint(self):
        u = body_unit()
        search = permute.Search(u, self.scorer_for('{}'), lambda text: ['bad'], random.Random(1), log=lambda m: None)
        self.assertEqual(search.run()['status'], 'base-lint-failed')

    def test_budget_stops(self):
        u = body_unit()
        ticks = iter([0, 0] + [10 ** 6] * 1000)
        search = permute.Search(u, self.scorer_for('{ return 0; }'), lambda text: [], random.Random(1),
                                budget=5, log=lambda m: None, clock=lambda: next(ticks))
        self.assertEqual(search.run()['status'], 'budget')

    def test_seen_set_keys_on_object_hash(self):
        u = body_unit()

        def score(cands):
            return [{'id': c['id'], 'st': 'ok', 'd': 5, 'ex': 5, 'n': 1, 'nt': 1, 'h': 'same'} for c in cands]
        search = permute.Search(u, score, lambda text: [], random.Random(1), batch=4, patience=3,
                                budget=10 ** 6, log=lambda m: None)
        result = search.run()
        self.assertEqual(result['unique_objects'], 1)
        self.assertTrue(all(not r.get('new_object', False) for r in search.history[1:]))


class LintRoot(unittest.TestCase):
    def test_lint_gate_runs_the_repository_lint(self):
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / 'src'
            (src / 'reconstruction/toys').mkdir(parents=True)
            (src / 'reconstruction/toys/Toy.cpp').write_text('#include "Toy.h"\n')
            (src / 'reconstruction/toys/Toy.h').write_text('#pragma once\n')
            root = permute.make_lint_root(Path(tmp) / 'lint', src, ['reconstruction/toys/Toy.cpp',
                                                                   'reconstruction/toys/Toy.h'])
            check = permute.lint_gate(root, 'reconstruction/toys/Toy.cpp', 'sse-steam-1-7-104')
            problems = check('#include "Toy.h"\nvoid F() { __asm { nop } }\n')
            self.assertTrue(any('inline assembly' in p for p in problems), problems)


if __name__ == '__main__':
    unittest.main()
