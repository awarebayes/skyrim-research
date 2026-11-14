"""Synthetic private-contract pin tests; no target-derived predicates or bytes."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import storage_init_generate_v2 as generator
import storage_init_template_v1 as old_template
import storage_init_template_v2 as template


class ContractPinTests(unittest.TestCase):
    def test_pin_accepts_only_the_exact_reviewed_artifact(self):
        blob = b'{"synthetic": true}\n'
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(generator,'CONTRACT_SHA256',hashlib.sha256(blob).hexdigest()):
            path=Path(tmp)/'contract.json';path.write_bytes(blob)
            self.assertEqual(generator.load_contract(path),{'synthetic':True})
            for changed in (b'{"synthetic": false}\n',b'{ "synthetic": true }\n'):
                path.write_bytes(changed)
                with self.assertRaisesRegex(ValueError,'pinned digest'):
                    generator.load_contract(path)

    def test_replacement_is_only_the_same_unaccepted_owned_extent(self):
        member={'rva':0x9020,'size':79}
        old=dict(member,status='mapped',name='StorageInit9020::initialize')
        self.assertTrue(generator.replacement_allowed([old],member))
        for existing in ([],[old,old],[dict(old,status='matched')],[dict(old,size=80)],
                         [dict(old,rva=0x9021)],[dict(old,name='Unowned::method')]):
            self.assertFalse(generator.replacement_allowed(existing,member))

    def test_new_family_keeps_the_natural_source_body(self):
        params={'count-offset':12,'storage-offset':24,'element-size':36}
        _,old_h,old_cpp,old_origin=old_template.emit(0x9020,79,params)
        _,h,cpp,origin=template.emit(0x9020,79,params)
        self.assertEqual(h,old_h)
        strip=lambda text:'\n'.join(line for line in text.splitlines() if not line.startswith('// Origin:'))
        self.assertEqual(strip(cpp),strip(old_cpp))
        self.assertEqual(origin['version'],'2');self.assertNotEqual(origin,old_origin)
        self.assertNotEqual(template.template_digest(),old_template.template_digest())


if __name__=='__main__':unittest.main()
