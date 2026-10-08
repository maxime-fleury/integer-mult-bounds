"""Focused checks for the reordered-circuit bit producer certificate."""
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'research' / 'ordered-chain'
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(HERE))
import measure
import witness

PINNED_KAPPA = Q(971668963, 25000000000000)
PINNED_BIT_ROOT = Q(3886826921, 10**14)


class OrderedChainWitness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = witness.run()
        cls.saved = json.loads((HERE / 'witness.json').read_text())

    def test_absorbing_margin_exceeds_pinned_kappa(self):
        margins = self.result['margins']
        self.assertEqual(len(margins), 7)
        self.assertEqual(self.result['constraints_count'], 47)
        self.assertGreater(min(Q(v) for v in margins.values()), PINNED_KAPPA)

    def test_kappa_is_the_grid_point_below_the_margin(self):
        kappa = Q(self.result['kappa'])
        margin = Q(self.result['absorbing_margin'])
        self.assertGreater(kappa, PINNED_KAPPA)
        self.assertLessEqual(kappa, margin)
        self.assertLess(margin - kappa, Q(1, 10**14))
        self.assertGreater(kappa, Q(1, 2**15))

    def test_negative_controls_are_all_rejected(self):
        self.assertEqual(sorted(self.result['negative_controls']),
                         ['next_kappa_grid', 'old_exposures', 'old_guard',
                          'original_prefix'])

    def test_saved_witness_matches(self):
        self.assertEqual(self.result, self.saved)


class OrderedChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = measure.run()
        cls.saved = json.loads((HERE / 'certificate.json').read_text())

    def test_producer_rows_satisfy_rank_identities(self):
        record = json.loads((HERE / 'producer-23.json').read_text())
        for name in ('baseline', 'variant'):
            row = record[name]
            self.assertEqual(row['v'], 1771)
            self.assertEqual(row['loss'], 23 * 22)
            self.assertEqual(sum(r * n for r, n in enumerate(row['histogram'])),
                             23 * row['R'] + 2 * row['loss'])
            self.assertEqual(row['R'], row['baseline_R'] - row['matching'])

    def test_variant_has_fewer_roles_and_smaller_role_volume(self):
        self.assertEqual(self.result['producer']['variant_R'], 37620)
        self.assertEqual(self.result['producer']['baseline_R'], 38776)
        self.assertLess(self.result['network']['W_variant'],
                        self.result['network']['W_baseline'])
        net = self.result['network']
        self.assertEqual(net['deficit'], net['N'] - net['L'])

    def test_variant_root_strictly_exceeds_baseline(self):
        root = self.result['root']
        ratio = Q(root['improvement_ratio'])
        self.assertGreater(ratio, Q(101, 100))
        self.assertLess(ratio, Q(102, 100))
        self.assertGreater(Q(root['variant_lower']), Q(root['baseline_upper']))

    def test_baseline_reproduces_the_pinned_bit_root(self):
        root = self.result['root']
        self.assertLessEqual(Q(root['baseline_lower']), PINNED_BIT_ROOT)
        self.assertGreaterEqual(Q(root['baseline_upper']), PINNED_BIT_ROOT)
        self.assertGreaterEqual(Q(root['variant_lower']), PINNED_BIT_ROOT)

    def test_saved_certificate_matches(self):
        self.assertEqual(self.result, self.saved)


if __name__ == '__main__':
    unittest.main()
