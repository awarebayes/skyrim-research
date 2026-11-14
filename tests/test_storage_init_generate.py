"""Original synthetic contracts and EH structures; no target-derived fixtures."""
import hashlib
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import lint_reconstruction
from pecoff import FUNCINFO_MAGIC, PeImage, Reject
import storage_init_generate as generator
import storage_init_template_v1 as template
from storage_row_extract import extract_eh, extract_instructions


def rows(*text):
    return [[i, '', t, []] for i,t in enumerate(text)]


class SyntheticImage:
    funcinfo_entries = PeImage.funcinfo_entries

    def __init__(self):
        self.data = bytearray(2048)
        self.data[100:104] = struct.pack('<4B', 9, 0, 0, 0)
        struct.pack_into('<II', self.data, 104, 300, 400)
        struct.pack_into('<10I', self.data, 400, FUNCINFO_MAGIC, 2, 500, 0, 0, 0, 0, 0, 0, 1)
        struct.pack_into('<iIiI', self.data, 500, -1, 600, 0, 700)

    def read(self, at, size, what):
        if at < 0 or at + size > len(self.data):
            raise ValueError('synthetic read out of bounds')
        return None, bytes(self.data[at:at+size])


class StorageRowsTest(unittest.TestCase):
    def test_private_capture_rules_extract_each_operand(self):
        contract = [dict(pattern=r'mov r10d, (0x[0-9a-f]+)', captures={'value':dict(group=1)}),
                    dict(pattern=r'call (0x[0-9a-f]+)', captures={'target-rva':dict(group=1,relative=True)})]
        self.assertEqual(extract_instructions(rows('mov r10d, 0x123', 'call 0x9080'), 0x9000, contract),
                         {'value':0x123, 'target-rva':0x80})
        self.assertEqual(extract_instructions(rows('mov r10d, 0x456', 'call 0x9090'), 0x9000, contract),
                         {'value':0x456, 'target-rva':0x90})
        for code in (rows('mov r10d, 0x123'), rows('mov r11d, 0x123', 'call 0x9080'),
                     rows('mov r10d, 0x123', 'call 0x80')):
            with self.assertRaises(ValueError):
                extract_instructions(code, 0x9000, contract)

    def test_duplicate_and_unsupported_capture_rules_refuse(self):
        for contract in ([dict(pattern='(2)',captures={'v':dict(group=1,base=2)})],
                         [dict(pattern='(2)',captures={'v':dict(group=1)})]*2):
            with self.assertRaises(ValueError):
                extract_instructions(rows(*(['2']*len(contract))), 0, contract)

    def test_signed_eh_transitions_and_all_actions(self):
        result = extract_eh(SyntheticImage(), 10, {10:[100]}, 300)
        self.assertEqual(result['actions'], [(-1,600),(0,700)])
        self.assertEqual(result['unwind-states'], 2)
        self.assertEqual(result['funcinfo-rva'],400)

    def test_wrong_handler_ambiguous_unwind_and_missing_handler_refuse(self):
        for procedures, handler in (({},300), ({10:[100,100]},300), ({10:[100]},301)):
            with self.assertRaises(ValueError):
                extract_eh(SyntheticImage(),10,procedures,handler)
        image = SyntheticImage(); image.data[100]=1
        with self.assertRaises(ValueError):
            extract_eh(image,10,{10:[100]},300)

    def test_unsupported_eh_version_and_invalid_transition_refuse(self):
        image = SyntheticImage(); struct.pack_into('<I',image.data,400,1)
        with self.assertRaises(Reject):
            extract_eh(image,10,{10:[100]},300)
        image = SyntheticImage(); struct.pack_into('<i',image.data,500,2)
        with self.assertRaises(ValueError):
            extract_eh(image,10,{10:[100]},300)

    def test_generic_extractor_is_pinned_by_parameter_source(self):
        self.assertEqual(hashlib.sha256((ROOT/'tools/storage_row_extract.py').read_bytes()).hexdigest(),
                         generator.EXTRACTOR_SHA256)

    def test_template_lints_without_opaque_storage_or_size_claim(self):
        params={'count-offset':12,'storage-offset':24,'element-size':36}
        cls,h,cpp,origin=template.emit(0x9010,79,params)
        self.assertIn('+ 12',cpp);self.assertIn('+ 24',cpp)
        self.assertIn('count, 36)',cpp)
        self.assertIn('No size or complete layout is asserted',h)
        self.assertIn('static unsigned initialize(void* object)',h)
        self.assertNotIn('char[',h);self.assertNotIn('reserved[',h)
        self.assertEqual(origin['template_digest'],template.template_digest())
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p in ('builds/target.json',template.EVIDENCE,template.RECIPE):
                destination=root/p;destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_text((ROOT/p).read_text())
            area=root/'reconstruction/storage';area.mkdir(parents=True)
            (area/f'{cls}.h').write_text(h);(area/f'{cls}.cpp').write_text(cpp)
            self.assertEqual(lint_reconstruction.lint_tree(root),[])
        for bad in ({**params,'count-offset':3},{**params,'element-size':0}):
            with self.assertRaises(ValueError):
                template.emit(0x9010,79,bad)


if __name__=='__main__':
    unittest.main()
