"""tools/analysis/inline_census.py on original synthetic code (no game data)."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'analysis'))
import inline_census as ic  # noqa: E402
import x64  # noqa: E402

# An inline helper: test a global flag, read two members, call a fixed function.
HELPER = ['803d0000000000',   # cmp byte [rip+0], 0      (the global; patched per host)
          '7405',             # je +5
          '488b4108',         # mov rax, [rcx+8]
          '4885c0',           # test rax, rax
          '488b4910',         # mov rcx, [rcx+0x10]
          'e800000000']       # call helper target (patched per host)


def assemble(parts):
    return b''.join(bytes.fromhex(p) for p in parts)


def host_code(prefix, suffix, flag_rva, call_rva, rva):
    """Code of a function at `rva` that inlines HELPER between its own prefix and suffix."""
    parts = list(prefix) + HELPER + list(suffix) + ['c3']
    code = bytearray(assemble(parts))
    off = len(assemble(prefix))
    disp_at = off + 2
    next_ip = rva + off + 7
    code[disp_at:disp_at + 4] = (flag_rva - next_ip).to_bytes(4, 'little', signed=True)
    call_off = off + len(assemble(HELPER[:-1]))
    code[call_off + 1:call_off + 5] = (call_rva - (rva + call_off + 5)).to_bytes(4, 'little', signed=True)
    return bytes(code)


def tokens_of(code, rva):
    insns = x64.decode_range(code, 0, len(code), rva)
    return ic.tokenize(insns, code, rva, len(code), 0, 0)


class CensusTests(unittest.TestCase):
    def setUp(self):
        self.hosts = {
            # Neighbouring instructions differ in kind, so only the helper itself is shared.
            1: host_code(['31c0', '0fafc1'], ['8bc2', '03c1'], 0x9000, 0x7000, 0x1000),
            2: host_code(['4c8bc1', '33d2'], ['ffc0'], 0x9000, 0x7000, 0x2000),
            3: host_code(['2bc2'], ['0bc1', 'ffc8'], 0x9000, 0x7000, 0x3000),
            4: host_code(['8bc1'], ['2bc2'], 0x9100, 0x7100, 0x4000),   # same shape, other targets
        }
        self.rvas = {1: 0x1000, 2: 0x2000, 3: 0x3000, 4: 0x4000}

    def build(self, min_hosts=3):
        c = ic.Census(k_long=6, k_short=4, min_hosts=min_hosts)
        for h, code in self.hosts.items():
            toks, offs, anch = tokens_of(code, self.rvas[h])
            c.add(h, toks, anch)
        return c

    def test_shared_body_found_with_targets_kept(self):
        c = self.build()
        bodies, per_host = ic.find_bodies(c, {})
        self.assertEqual(len(bodies), 1)
        (b,) = bodies.values()
        self.assertEqual(b['hosts'], 3)
        self.assertEqual(b['instructions'], len(HELPER))
        self.assertEqual(per_host[4], [])

    def test_twin_is_a_small_function_with_the_body(self):
        c = self.build()
        bodies, _ = ic.find_bodies(c, {})
        twin_code = host_code([], [], 0x9000, 0x7000, 0x5000)
        toks, _, _ = tokens_of(twin_code, 0x5000)
        ic.find_twins(bodies, c, {99: [t for t in toks if t]})
        self.assertEqual(next(iter(bodies.values()))['twin'], 99)

    def test_separators_and_epilogue(self):
        code = assemble(['53', '4883ec20', '488b4108', '488b5c2430', '4883c420', '5b', 'c3'])
        toks, offs, _ = tokens_of(code, 0x1000)
        self.assertEqual([t != 0 for t in toks], [False, False, True, False, False, False, False])

    def test_self_repeat_ignores_branch_sense(self):
        # The same member walk inlined twice, once ending in jne and once in je.
        code = assemble(['488b4008', '4885c0', '75f8', '488bcb', '488b4308', '4885c0', '7405', '33c0', 'c3'])
        insns = x64.decode_range(code, 0, len(code), 0x1000)
        relaxed, spec = [0] * len(insns), bytearray(len(insns))
        ic.tokenize(insns, code, 0x1000, len(code), 0, 0, False, relaxed, spec)
        groups = ic.self_repeats(relaxed, spec, 3)
        self.assertEqual(groups, [[(0, 3), (4, 7)]])

    def test_per_function_record_format(self):
        row = {'rva': '0x1000', 'via_representative': None, 'bodies': [['b:1', [[4, 30]]]], 'self_repeats': []}
        bodies = {'b:1': {'instructions': 6, 'hosts': 3, 'self_repeats': 0, 'twin': None, 'references': [],
                          'guess': None}}
        rec = ic.per_function_record(row, bodies, 'build', {'k_long': 6})
        self.assertEqual(rec['schema'], ic.PER_FUNCTION_SCHEMA)
        self.assertEqual(rec['bodies'][0]['places'], [[4, 30]])
        self.assertEqual(rec['self_repeats'], [])


if __name__ == '__main__':
    unittest.main()
