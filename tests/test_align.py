"""Tests for tools/verifier/align.py on synthetic, hand-written listings (no game data, no objdump)."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'verifier'))
import align  # noqa: E402

BASE = 0x140000000
START = 0x140001000
SYMBOLS = {'g_limit': 0x5000, 'g_other': 0x5008, '?Small@@YAXH@Z': 0x3000, '?Big@@YAXH@Z': 0x3100,
           '?Other@@YAXH@Z': 0x3200}

# An original toy function: save rbx, keep `this` in rdi, compare a field with a global and call
# one of two helpers. Rows: (label, bytes with ?? holes, text with {T}, reference).
BASE_ROWS = [
    (None, '48 89 5c 24 08', 'mov qword ptr [rsp + 0x8], rbx', None),
    (None, '57', 'push rdi', None),
    (None, '48 83 ec 20', 'sub rsp, 0x20', None),
    (None, '48 8b f9', 'mov rdi, rcx', None),
    (None, '8b 1d ?? ?? ?? ??', 'mov ebx, dword ptr [{T}]', ('rip', 'g_limit')),
    (None, '48 85 ff', 'test rdi, rdi', None),
    (None, '74 ??', 'je {T}', ('label', 'out')),
    (None, '8b 4f 10', 'mov ecx, dword ptr [rdi + 0x10]', None),
    (None, '3b cb', 'cmp ecx, ebx', None),
    (None, '73 ??', 'jae {T}', ('label', 'big')),
    (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Small@@YAXH@Z')),
    (None, 'eb ??', 'jmp {T}', ('label', 'store')),
    ('big', 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Big@@YAXH@Z')),
    ('store', '89 47 14', 'mov dword ptr [rdi + 0x14], eax', None),
    ('out', '48 8b 5c 24 30', 'mov rbx, qword ptr [rsp + 0x30]', None),
    (None, '48 83 c4 20', 'add rsp, 0x20', None),
    (None, '5f', 'pop rdi', None),
    (None, 'c3', 'ret', None),
]


def _fill(data, holes, value):
    raw = (value & ((1 << (8 * len(holes))) - 1)).to_bytes(len(holes), 'little')
    for i, b in zip(holes, raw):
        data[i] = f'{b:02x}'


def listing(rows, candidate=False, symbols=None):
    """llvm-objdump-style text for `rows`: the target at START with resolved fields, the candidate
    at 0 with zero fields and REL32 relocation rows."""
    symbols = SYMBOLS if symbols is None else symbols
    start = 0 if candidate else START
    addrs, layout, at = {}, [], start
    for label, hx, _, _ in rows:
        if label:
            addrs[label] = at
        layout.append(at)
        at += len(hx.split())
    out = ['', 'Disassembly of section .text:', '']
    for (label, hx, text, ref), addr in zip(rows, layout):
        data = hx.split()
        holes = [i for i, b in enumerate(data) if b == '??']
        nxt = addr + len(data)
        relocs = []
        arg = ''
        if ref and ref[0] == 'label':
            dest = addrs[ref[1]]
            _fill(data, holes, dest - nxt)
            arg = f'0x{dest:x}'
        elif ref:
            va = BASE + symbols.get(ref[1], 0x7000)
            if candidate:
                _fill(data, holes, 0)
                relocs.append((addr + holes[0], ref[1]))
                arg = f'0x{nxt:x}' if ref[0] == 'sym' else 'rip'
            else:
                _fill(data, holes, va - nxt)
                arg = f'0x{va:x}' if ref[0] == 'sym' else f'rip + 0x{va - nxt:x}'
        out.append(f'{addr:8x}: {" ".join(data)}\t{text.replace("{T}", arg)}')
        for field, name in relocs:
            out.append(f'\t\t{field:016x}:  IMAGE_REL_AMD64_REL32\t{name}')
    return '\n'.join(out) + '\n'


def run(target_rows, cand_rows, symbols=None, unwind=None):
    text, data = align.summarise(listing(target_rows), listing(cand_rows, candidate=True),
                                 symbols=SYMBOLS if symbols is None else symbols, image_base=BASE,
                                 unwind=unwind)
    return text, data


def replace(rows, index, row):
    out = list(rows)
    out[index] = row
    return out


SWAP = {'rbx': 'rdi', 'ebx': 'edi', 'rdi': 'rbx', 'edi': 'ebx'}


def swapped(rows):
    """rbx and rdi exchanged everywhere; one byte changes where a register field changes."""
    out = []
    for label, hx, text, ref in rows:
        new = re.sub(r'\b(rbx|ebx|rdi|edi)\b', lambda m: SWAP[m.group(1)], text)
        if new != text:
            data = hx.split()
            k = next(i for i in range(len(data) - 1, -1, -1) if data[i] != '??')
            data[k] = f'{int(data[k], 16) ^ 0x07:02x}'
            hx = ' '.join(data)
        out.append((label, hx, new, ref))
    return out


class Parsing(unittest.TestCase):
    def test_tab_directly_after_last_byte(self):
        rows = align.parse_listing('      1d: f7 83 8c 02 00 00 00 00 04 00\ttest\tdword ptr [rbx + 0x28c], 0x40000\n')
        self.assertEqual(len(rows[0][1]), 10)
        self.assertEqual(rows[0][2], 'test dword ptr [rbx + 0x28c], 0x40000')

    def test_lock_prefix_row_is_merged(self):
        text = ('  13: f0\tlock\n'
                '  14: ff 43 04\tinc\tdword ptr [rbx + 0x4]\n')
        rows = align.parse_listing(text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0][0], 0x13)
        self.assertEqual(rows[0][1], ['f0', 'ff', '43', '04'])
        ins = align.build(rows)[0]
        self.assertEqual(ins.mnem, 'lock inc')

    def test_relocation_rows_attach_to_the_instruction(self):
        rows = align.parse_listing(listing(BASE_ROWS, candidate=True))
        calls = [r for r in rows if r[2].startswith('call')]
        self.assertEqual([r[3][0][2] for r in calls], ['?Small@@YAXH@Z', '?Big@@YAXH@Z'])

    def test_references_resolve_to_rvas_on_both_sides(self):
        t = align.build(align.parse_listing(listing(BASE_ROWS)), base=BASE)
        c = align.build(align.parse_listing(listing(BASE_ROWS, candidate=True)), symbols=SYMBOLS, candidate=True)
        self.assertEqual([i.ref for i in t if i.ref], [i.ref for i in c if i.ref])
        self.assertIn(('rva', 0x5000), [i.ref for i in t])
        self.assertEqual([i.label for i in t if i.label is not None], [i.label for i in c if i.label is not None])

    def test_frame_marks_saves_but_not_local_stores(self):
        rows = BASE_ROWS[:5] + [(None, '89 5c 24 38', 'mov dword ptr [rsp + 0x38], ebx', None)] + BASE_ROWS[5:]
        t = align.build(align.parse_listing(listing(rows)), base=BASE)
        frame = [i.text.split(' ')[0] + ' ' + str(i.off) for i in t if i.frame]
        self.assertIn('mov 0', frame)
        store = next(i for i in t if 'rsp + 0x38' in i.text)
        self.assertFalse(store.frame, 'a store after the register was written is a local, not a save')


class Classes(unittest.TestCase):
    def classes(self, data):
        return set(data['classes'])

    def test_identical_is_zero_and_exact(self):
        text, data = run(BASE_ROWS, BASE_ROWS)
        self.assertEqual(data['distance'], 0)
        self.assertTrue(data['exact'])
        self.assertEqual(data['classes'], {})
        self.assertIn('identical', text)

    def test_one_branch_target(self):
        rows = replace(BASE_ROWS, 6, (None, '74 ??', 'je {T}', ('label', 'store')))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'block-order-or-branch-polarity'})
        self.assertEqual(data['edits']['shape'], 1)
        self.assertEqual(data['distance'], align.WEIGHT['branch'])

    def test_consistent_callee_saved_swap(self):
        text, data = run(BASE_ROWS, swapped(BASE_ROWS))
        self.assertEqual(data['register_map']['kind'], 'callee-saved bijection')
        self.assertEqual(data['register_map']['renamed'], {'rbx': 'rdi', 'rdi': 'rbx'})
        self.assertEqual(self.classes(data), {'register-renaming'})
        self.assertEqual(data['distance'], 2 * align.WEIGHT['rename-callee-saved'])
        self.assertEqual(data['edits']['shape'], 0)
        self.assertIn(12, data['cookbook_rules'])
        self.assertIn('cookbook 12', text)

    def test_caller_saved_renaming_costs_more(self):
        # The argument and the temporary that reuses its register both move to rdx.
        rows = replace(BASE_ROWS, 3, (None, '48 8b fa', 'mov rdi, rdx', None))
        rows = replace(rows, 7, (None, '8b 57 10', 'mov edx, dword ptr [rdi + 0x10]', None))
        rows = replace(rows, 8, (None, '3b d3', 'cmp edx, ebx', None))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(data['register_map']['renamed'], {'rcx': 'rdx'})
        self.assertEqual(data['register_map']['kind'], 'bijection with caller-saved')
        self.assertEqual(data['distance'], align.WEIGHT['rename-volatile'])
        self.assertNotIn(12, data['cookbook_rules'])

    def test_inconsistent_register_use(self):
        rows = replace(BASE_ROWS, 8, (None, '3b cf', 'cmp ecx, edi', None))
        _, data = run(BASE_ROWS, rows)
        self.assertIn('register-renaming', self.classes(data))
        self.assertGreaterEqual(data['distance'], align.WEIGHT['inconsistent-reg'])
        self.assertLess(data['register_map']['uses_agree'], data['register_map']['uses'])

    def test_extra_zero_store(self):
        rows = BASE_ROWS[:4] + [(None, '33 c0', 'xor eax, eax', None),
                                (None, '89 44 24 38', 'mov dword ptr [rsp + 0x38], eax', None)] + BASE_ROWS[4:]
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'extra-instruction'})
        self.assertEqual(data['distance'], 2 * align.WEIGHT['extra'])
        self.assertIn(9, data['cookbook_rules'])

    def test_missing_null_test(self):
        rows = BASE_ROWS[:5] + BASE_ROWS[7:]
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'missing-instruction'})
        self.assertEqual(data['distance'], 2 * align.WEIGHT['missing'])
        self.assertIn(1, data['cookbook_rules'])

    def test_operand_signedness(self):
        target = replace(BASE_ROWS, 7, (None, '0f b6 4f 10', 'movzx ecx, byte ptr [rdi + 0x10]', None))
        rows = replace(BASE_ROWS, 7, (None, '0f be 4f 10', 'movsx ecx, byte ptr [rdi + 0x10]', None))
        _, data = run(target, rows)
        self.assertEqual(self.classes(data), {'operand-width-or-signedness'})
        self.assertIn(6, data['cookbook_rules'])

    def test_operand_width(self):
        rows = replace(BASE_ROWS, 7, (None, '48 8b 4f 10', 'mov rcx, qword ptr [rdi + 0x10]', None))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'operand-width-or-signedness'})
        self.assertEqual(data['distance'], align.WEIGHT['width'])

    def test_reordered_independent_instructions(self):
        target = BASE_ROWS[:5] + [(None, 'b8 01 00 00 00', 'mov eax, 0x1', None)] + BASE_ROWS[5:]
        rows = BASE_ROWS[:4] + [(None, 'b8 01 00 00 00', 'mov eax, 0x1', None)] + BASE_ROWS[4:]
        _, data = run(target, rows)
        self.assertEqual(self.classes(data), {'reordered-instructions'})
        self.assertEqual(data['distance'], align.WEIGHT['moved'])
        self.assertIn(4, data['cookbook_rules'])

    def test_block_order_and_polarity(self):
        # The two calls laid out the other way round with the condition inverted.
        rows = BASE_ROWS[:9] + [
            (None, '72 ??', 'jb {T}', ('label', 'small')),
            (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Big@@YAXH@Z')),
            (None, 'eb ??', 'jmp {T}', ('label', 'store')),
            ('small', 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Small@@YAXH@Z')),
        ] + BASE_ROWS[13:]
        _, data = run(BASE_ROWS, rows)
        self.assertIn('block-order-or-branch-polarity', self.classes(data))
        self.assertIn(2, data['cookbook_rules'])

    def test_stack_frame(self):
        target = [r for r in BASE_ROWS]
        rows = replace(BASE_ROWS, 2, (None, '48 83 ec 30', 'sub rsp, 0x30', None))
        rows = replace(rows, 15, (None, '48 83 c4 30', 'add rsp, 0x30', None))
        _, data = run(target, rows)
        self.assertEqual(self.classes(data), {'prologue-or-unwind'})
        self.assertEqual(data['components']['body'], 0)
        self.assertGreater(data['components']['prologue'], 0)

    def test_extra_push_is_prologue(self):
        rows = BASE_ROWS[:2] + [(None, '56', 'push rsi', None)] + BASE_ROWS[2:16] + \
            [(None, '5e', 'pop rsi', None)] + BASE_ROWS[16:]
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'prologue-or-unwind'})
        self.assertEqual(data['components']['prologue'], 2 * align.WEIGHT['extra'])

    def test_different_callee(self):
        rows = replace(BASE_ROWS, 10, (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Other@@YAXH@Z')))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'callee-or-argument-setup'})
        self.assertEqual(data['components']['refs'], align.WEIGHT['wrong-ref'])

    def test_extra_argument_setup(self):
        rows = BASE_ROWS[:10] + [(None, 'ba 01 00 00 00', 'mov edx, 0x1', None)] + BASE_ROWS[10:]
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'callee-or-argument-setup'})
        self.assertEqual(data['components']['body'], align.WEIGHT['extra'])
        self.assertIn(5, data['cookbook_rules'])

    def test_displacement(self):
        rows = replace(BASE_ROWS, 13, ('store', '89 47 18', 'mov dword ptr [rdi + 0x18], eax', None))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'constant-or-displacement'})
        self.assertEqual(data['distance'], align.WEIGHT['constant'])

    def test_data_reference(self):
        rows = replace(BASE_ROWS, 4, (None, '8b 1d ?? ?? ?? ??', 'mov ebx, dword ptr [{T}]', ('rip', 'g_other')))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'reference-target'})
        self.assertEqual(data['components']['refs'], align.WEIGHT['wrong-ref'])

    def test_unresolved_reference(self):
        symbols = {k: v for k, v in SYMBOLS.items() if k != 'g_limit'}
        _, data = run(BASE_ROWS, BASE_ROWS, symbols=symbols)
        self.assertEqual(self.classes(data), {'reference-target'})
        self.assertEqual(data['distance'], align.WEIGHT['unresolved-ref'])
        self.assertFalse(data['exact'])

    def test_encoding_only(self):
        rows = replace(BASE_ROWS, 8, (None, '39 d9', 'cmp ecx, ebx', None))
        _, data = run(BASE_ROWS, rows)
        self.assertEqual(self.classes(data), {'encoding'})
        self.assertGreater(data['distance'], 0)


class Unwind(unittest.TestCase):
    # Version 1, prologue 6 bytes, 2 codes: alloc 0x20 at +6, push rbx (3) or rdi (7) at +1.
    T_HEX = '0106020006320130'
    C_HEX = '0106020006320170'

    def test_decode(self):
        info = align.decode_unwind(self.T_HEX)
        self.assertEqual(info['codes'], [(6, 'alloc', None, 0x20), (1, 'push', 'rbx', None)])

    def test_swap_explained_by_map(self):
        fields, explained = align.compare_unwind(self.T_HEX, self.C_HEX, {'rbx': 'rdi', 'rdi': 'rbx'})
        self.assertEqual(fields, [])
        self.assertTrue(explained)

    def test_register_set_differs_without_map(self):
        fields, _ = align.compare_unwind(self.T_HEX, self.C_HEX, {})
        self.assertEqual(fields, ['saved register set or order'])

    def test_frame_size(self):
        fields, _ = align.compare_unwind(self.T_HEX, '0106020006520130', {})
        self.assertEqual(fields, ['frame size'])


class Distance(unittest.TestCase):
    def test_zero_only_when_exact(self):
        variants = [replace(BASE_ROWS, 8, (None, '39 d9', 'cmp ecx, ebx', None)), swapped(BASE_ROWS),
                    BASE_ROWS[:5] + BASE_ROWS[7:]]
        for rows in variants:
            _, data = run(BASE_ROWS, rows)
            self.assertFalse(data['exact'])
            self.assertGreater(data['distance'], 0)

    def test_pure_swap_is_smaller_than_any_structural_difference(self):
        swap = run(BASE_ROWS, swapped(BASE_ROWS))[1]['distance']
        missing = run(BASE_ROWS, BASE_ROWS[:7] + BASE_ROWS[8:])[1]['distance']
        self.assertLess(swap, missing)
        self.assertLessEqual(swap, 0.5)

    def test_monotone_as_differences_are_fixed(self):
        # Three independent defects; fixing them one at a time never raises the distance.
        broken = replace(BASE_ROWS, 13, ('store', '89 47 18', 'mov dword ptr [rdi + 0x18], eax', None))
        broken = replace(broken, 10, (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Other@@YAXH@Z')))
        broken = broken[:5] + broken[7:]
        step1 = BASE_ROWS[:5] + BASE_ROWS[7:]
        step1 = replace(step1, 8, (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Other@@YAXH@Z')))
        step2 = BASE_ROWS[:5] + BASE_ROWS[7:]
        distances = [run(BASE_ROWS, rows)[1]['distance'] for rows in (broken, step1, step2, BASE_ROWS)]
        self.assertEqual(distances, sorted(distances, reverse=True))
        self.assertEqual(len(set(distances)), 4)
        self.assertEqual(distances[-1], 0)

    def test_components_sum_to_distance(self):
        rows = replace(swapped(BASE_ROWS), 10, (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Other@@YAXH@Z')))
        _, data = run(BASE_ROWS, rows)
        self.assertAlmostEqual(sum(data['components'].values()), data['distance'])


class Output(unittest.TestCase):
    def test_summary_is_short_and_has_no_bytes_or_instruction_text(self):
        rows = replace(swapped(BASE_ROWS), 10, (None, 'e8 ?? ?? ?? ??', 'call {T}', ('sym', '?Other@@YAXH@Z')))
        rows = rows[:5] + rows[7:]
        text, data = run(BASE_ROWS, rows)
        self.assertLessEqual(len(text.splitlines()), 12)
        for line in text.splitlines():
            self.assertNotRegex(line, r'\b[0-9a-f]{2} [0-9a-f]{2}\b')
            self.assertNotIn('ptr', line)
        blob = json.dumps(data)
        for _, _, row_text, _ in BASE_ROWS:
            if '{T}' not in row_text and ' ' in row_text:
                self.assertNotIn(row_text, blob)

    def test_listing_file_and_json_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'align.txt'
            text, data = align.summarise(listing(BASE_ROWS), listing(swapped(BASE_ROWS), candidate=True),
                                         symbols=SYMBOLS, image_base=BASE, listing_path=path)
            body = path.read_text()
        self.assertIn('Private aligned listing', body)
        renamed = [r for r in BASE_ROWS if re.search(r'\b(rbx|ebx|rdi|edi)\b', r[2])]
        self.assertEqual(sum(1 for line in body.splitlines() if line.startswith('r ')), len(renamed))
        self.assertEqual(data['schema'], align.SCHEMA)
        self.assertEqual(len(data['alignment']), len(BASE_ROWS))
        self.assertTrue(set(data['classes']) <= set(align.CLASSES))

    def test_rows_input_is_accepted(self):
        rows = align.parse_listing(listing(BASE_ROWS))
        _, data = align.summarise(rows, listing(BASE_ROWS, candidate=True), symbols=SYMBOLS, image_base=BASE)
        self.assertEqual(data['distance'], 0)

    def test_attempt_summary_never_raises(self):
        lines = align.attempt_summary('/nonexistent', None, None, '/nonexistent.obj',
                                      {'rva': 0x1000, 'size': 4, 'symbol': 'f'})
        self.assertEqual(len(lines), 1)
        self.assertIn('not available', lines[0])

    def test_unwind_from_diagnostics(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / 'diagnostics.json').write_text(json.dumps(
                {'report': {'reason': 'unwind-info-mismatch'}, 'raw': {'target': 'aa', 'candidate': 'bb'}}))
            self.assertEqual(align.unwind_from_diagnostics(tmp), ('aa', 'bb'))
            (Path(tmp) / 'diagnostics.json').write_text(json.dumps({'report': {'reason': 'code-byte-mismatch'}}))
            self.assertIsNone(align.unwind_from_diagnostics(tmp))


if __name__ == '__main__':
    unittest.main()
