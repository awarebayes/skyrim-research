import sys
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import primitive_leaf_generate as generator
import primitive_leaf_template_v1 as template
import lint_reconstruction


class PrimitiveTests(unittest.TestCase):
    def test_complete_shape_and_exact_constant(self):
        self.assertIsNone(generator.extract(bytes((194,0,0)),'empty'))
        code=bytes((184,120,86,52,18,195))
        self.assertEqual(generator.extract(code,'constant'),0x12345678)
        for bad,family in [(bytes((194,8,0)),'empty'),(bytes((195,)),'empty'),
                           (code+bytes((144,)),'constant'),(code[:-1],'constant'),
                           (code,'empty')]:
            with self.assertRaises(ValueError):generator.extract(bad,family)

    def test_parameters_are_bounded_and_families_distinct(self):
        self.assertNotEqual(template.origin('empty'),template.origin('constant'))
        for args in [(1,4,'empty','ordinary'),(1,6,'constant','ordinary',-1),
                     (1,6,'constant','ordinary',True),(1,6,'constant','teardown',5)]:
            with self.assertRaises(ValueError):template.emit(*args)

    def test_all_emission_kinds_lint_and_disclose_standins(self):
        for family,kind,value in [('empty','ordinary',None),('empty','teardown',None),
                                  ('constant','ordinary',0x12345678)]:
            size=3 if family=='empty' else 6
            e=template.emit(0x1234,size,family,kind,value)
            self.assertEqual(e['parameters']['entry_rva'],0x1234)
            self.assertIn('original function signature are unknown',e['header'])
            with tempfile.TemporaryDirectory() as directory:
                root=Path(directory)
                for rel in ['builds/target.json',template.RECIPE]:
                    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/rel).read_bytes())
                p=root/template.EVIDENCE;p.parent.mkdir(parents=True);p.write_text('synthetic fixture')
                base=root/'reconstruction'/e['area'];base.mkdir(parents=True)
                (base/(e['cls']+'.h')).write_text(e['header']);(base/(e['cls']+'.cpp')).write_text(e['source'])
                self.assertEqual(lint_reconstruction.lint_tree(root),[])


if __name__=='__main__':unittest.main()
