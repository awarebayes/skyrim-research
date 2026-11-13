import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from family_census import rank


def row(rva, size=4, shape='s', masked='m', kind='ordinary', names=''):
    return dict(rva=hex(rva), size=str(size), shape=shape, masked=masked,
                kind=kind, names=names, family='synthetic')


class CensusTests(unittest.TestCase):
    def test_shape_and_size_are_both_part_of_identity(self):
        groups = rank([row(1), row(2), row(3, size=8)])
        self.assertEqual([(g['members'], g['size']) for g in groups], [(2, 4), (1, 8)])
        self.assertEqual(groups[0]['rows'][0]['rva'], '0x1')

    def test_exclusions_apply_before_counting_and_ranking(self):
        groups = rank([row(1), row(2, masked='held'), row(3, kind='eh-funclet'),
                       row(4, shape=''), row(5), row(6, names='public')], [5], ['held'])
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]['members'], 2)
        self.assertEqual(groups[0]['named'], 1)

    def test_byte_and_member_orders_can_differ(self):
        groups = rank([row(1), row(2), row(3, size=30, shape='big')])
        self.assertEqual([g['byte_rank'] for g in groups], [2, 1])
        self.assertEqual([g['label'] for g in groups], ['F001', 'F002'])

    def test_invalid_population_is_refused(self):
        for rows in ([row(1), row(1)], [row(1, size=0)]):
            with self.assertRaises(ValueError):
                rank(rows)


if __name__ == '__main__':
    unittest.main()
