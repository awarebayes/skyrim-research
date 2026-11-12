"""tools/check_origin.py on original synthetic sources: parsing, normalisation, triviality, hits."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import check_origin as co  # noqa: E402


def names(text):
    return [(f['class'], f['name']) for f in co.functions(co.clean(text))]


class Parsing(unittest.TestCase):
    def test_out_of_line_inline_and_namespaces(self):
        text = '''
        #include "x.h"
        namespace NS {
        class Widget : public Base<int> {
        public:
            int Size() const noexcept { return size; }  // { not a brace
            Widget() : size{ 0 }, flags(1) { Init(); }
            T& operator[](unsigned a_pos) { return data[a_pos]; }
            enum class Kind { kA, kB };
            int size{ 3 };
        };
        bool Widget::Equals(const Widget& a_other) const
        {
            if (a_other.size != size) { return false; }
            return true;
        }
        }
        static const char* s = "}{";
        '''
        self.assertEqual(names(text), [('Widget', 'Size'), ('Widget', 'Widget'), ('Widget', 'operator[]'),
                                       ('Widget', 'Equals')])

    def test_control_flow_and_lambdas_are_not_functions(self):
        text = 'void f() { if (x) { g(); } auto l = [](int a) { return a; }; }\nint table[] = { 1, 2 };'
        self.assertEqual(names(text), [(None, 'f')])

    def test_destructor_and_template_member(self):
        text = 'template <class T> Box<T>::~Box() { Release(); }\ntemplate <class T> void Box<T>::Set(T* p) { ptr = p; }'
        self.assertEqual(names(text), [('Box', '~Box'), ('Box', 'Set')])


class Normalise(unittest.TestCase):
    def test_locals_params_asserts_and_this_are_canonical(self):
        a = co.normalise('assert(a_n > 0); int total = 0; this->count = a_n; total += a_n; return total;', ['a_n'])
        b = co.normalise('SKSE_ASSERT(n); int sum = 0; count = n; sum += n; return sum;', ['n'])
        self.assertEqual(a, b)

    def test_members_and_callees_are_not_renamed(self):
        a = co.normalise('return GetRTTI()->name;')
        b = co.normalise('return GetRTTI()->other;')
        self.assertNotEqual(a, b)

    def test_trivial(self):
        for body in ('', 'return nullptr;', 'return false;', 'return 0x10;', 'return this;',
                     'return Kind::kA;', 'return data.objectReference;', 'return a->b;'):
            self.assertTrue(co.trivial(co.normalise(body)), body)
        for body in ('return data[a_pos];', 'return f();', 'return a == b;', 'x = 1; return x;',
                     'return static_cast<bool>(a);'):
            self.assertFalse(co.trivial(co.normalise(body, ['a_pos'])), body)


class Units(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        upstream = self.root / 'ng'
        (upstream / 'src').mkdir(parents=True)
        (upstream / 'src/Thing.cpp').write_text('''namespace RE {
bool Thing::Same(Thing* a_other)
{
    assert(a_other);
    return a_other != nullptr && std::strcmp(GetName(), a_other->GetName()) == 0;
}
Thing* Thing::Self() { return this; }
int Thing::Renamed(int a) { int r = a * 3 + 7; return r - 1; }
void Thing::Different() { Log("x"); Flush(); Reset(1, 2, 3); }
}''')
        fork = self.root / 'fork'
        (fork / 'src').mkdir(parents=True)
        (fork / 'src/Thing.cpp').write_text((upstream / 'src/Thing.cpp').read_text())
        self.clones = [co.Clone('Owner/NG', upstream, 'MIT', ('src',), None),
                       co.Clone('powerof3/CommonLibSSE', fork, 'GPL-3.0', ('src',), None)]
        co.FORKS['powerof3/CommonLibSSE'] = 'Owner/NG'
        self.unit = self.root / 'reconstruction/x/Thing.cpp'
        self.unit.parent.mkdir(parents=True)

    def tearDown(self):
        co.FORKS['powerof3/CommonLibSSE'] = 'CharmedBaryon/CommonLibSSE-NG'
        self.tmp.cleanup()

    def write(self, header):
        self.unit.write_text(header + '''#include "Thing.h"
bool Thing::Same(Thing* other)
{
    return other != nullptr && std::strcmp(GetName(), other->GetName()) == 0;
}
Thing* Thing::Self() { return this; }
int Thing::Other(int b) { int q = b * 3 + 7; return q - 1; }
void Thing::Different() { Compute(); }
''')

    def hits(self):
        return co.check_unit([self.unit], self.clones, root=self.root)

    def test_adapted_trivial_fork_and_undeclared(self):
        self.write('// Thing members.\n')
        hits = self.hits()
        by = {(h['repo'], h['function']): h for h in hits}
        same = by[('Owner/NG', 'Thing::Same')]
        self.assertEqual(same['similarity'], 1.0)
        self.assertFalse(same['trivial'])
        self.assertFalse(same['declared'])
        self.assertIsNone(same['fork_of'])
        self.assertEqual(by[('powerof3/CommonLibSSE', 'Thing::Same')]['fork_of'], 'Owner/NG')
        self.assertTrue(by[('Owner/NG', 'Thing::Self')]['trivial'])
        self.assertIsNone(by[('Owner/NG', 'Thing::Self')]['declared'])
        # Limits: a renamed method is not compared; a different body is under the threshold.
        self.assertNotIn(('Owner/NG', 'Thing::Other'), by)
        self.assertNotIn(('Owner/NG', 'Thing::Different'), by)
        self.assertIn('NOT', co.describe(same))
        self.assertIn('adapted, NOT declared', co.function_lines('Thing::Same', hits))
        self.assertIn('none at or above', co.function_lines('Thing::Missing', hits))

    def test_declared_needs_method_and_file(self):
        self.write('// Adapted code: Same from Owner/NG src/Thing.h (MIT).\n')
        self.assertFalse(next(h for h in self.hits() if h['function'] == 'Thing::Same')['declared'])
        self.write('// Adapted code: Same from Owner/NG src/Thing.cpp (MIT).\n')
        self.assertTrue(next(h for h in self.hits() if h['function'] == 'Thing::Same')['declared'])
        self.write('// Adapted code: Other from Owner/NG src/Thing.cpp (MIT).\n')
        self.assertFalse(next(h for h in self.hits() if h['function'] == 'Thing::Same')['declared'])

    def test_sibling_needs_its_line(self):
        self.assertFalse(co.declared('// Same: see src/Thing.cpp', 'momusdigital/fnv_decomp', 'src/Thing.cpp', 'Same'))
        self.assertTrue(co.declared('// Same parallels FNV.\n// Sibling source: momusdigital/fnv_decomp@91e1b6e8 '
                                    'src/Thing.cpp:3', 'momusdigital/fnv_decomp', 'src/Thing.cpp', 'Same'))

    def test_threshold(self):
        self.write('')
        self.assertTrue(any(h['function'] == 'Thing::Same' for h in co.check_unit([self.unit], self.clones,
                                                                                   threshold=0.99, root=self.root)))
        self.assertEqual([h for h in co.check_unit([self.unit], self.clones, threshold=1.01, root=self.root)], [])


if __name__ == '__main__':
    unittest.main()
