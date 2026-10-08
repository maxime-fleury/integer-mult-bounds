"""Exact headroom identities and ceilings for the pinned bit network."""
from fractions import Fraction as Q
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import kappa_headroom as kh


class Headroom(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(kh.CERT.read_text())
        cls.bit = cls.data["bit"]
        cls.asm = cls.data["assembly"]
        cls.m = cls.bit["counts"]["m"]
        cls.W = cls.bit["counts"]["W"]
        cls.s = cls.bit["counts"]["total_rank"]
        cls.hist = kh.histogram(cls.bit["counts"])

    def test_rank_identity_and_child_domain(self):
        self.assertEqual(sum(t * n for t, n in self.hist.items()), self.s)
        self.assertEqual(self.s, self.W * self.m - self.bit["counts"]["N"]
                         + self.bit["counts"]["L"])
        for t, n in self.hist.items():
            self.assertTrue(0 < t < self.m and n > 0)

    def test_contraction_is_increasing_and_brackets_pinned_saving(self):
        a_lo, a_hi = kh.root_bounds(self.hist, self.m, self.W)
        self.assertLess(a_lo, Q(self.bit["saving"]))
        self.assertLessEqual(Q(self.bit["saving"]), a_hi)
        low = kh.scaled_moment_bounds(self.hist, self.m, a_lo)[1]
        high = kh.scaled_moment_bounds(self.hist, self.m, a_hi)[0]
        self.assertLess(low, high)

    def test_naive_uniform_saving_is_strictly_smaller(self):
        a_lo, _ = kh.root_bounds(self.hist, self.m, self.W)
        naive = kh.log_bounds(Q(self.W * self.m, self.s))[0] / kh.log_bounds(Q(self.m))[1]
        self.assertLess(naive, a_lo)

    def test_concentrated_ceiling_covers_every_width_distribution(self):
        # For every histogram with sum_t t n_t = s, the root is at most the
        # root of the relaxation concentrated at the largest child width m-1.
        c_lo, c_hi = kh.root_bounds({self.m - 1: Q(self.s, self.m - 1)},
                                    self.m, self.W)
        a_lo, _ = kh.root_bounds(self.hist, self.m, self.W)
        self.assertLess(a_lo, c_lo)
        self.assertLess(c_hi, Q(1, 32))
        self.assertGreater(Q(c_lo, a_lo), 200)

    def test_certified_assembly_ceiling(self):
        p = {k: Q(v) for k, v in self.asm["parameters"].items()}
        self.assertLess(p["a_bit"], p["a_complex"])
        self.assertLess(p["a_complex"], Q(1, 32))
        self.assertLess(min(Q(v) for v in self.asm["margins"].values()), p["a_bit"])
        self.assertLess(p["kappa"], p["a_bit"])

    def test_deficit_scaling_is_increasing(self):
        roots = []
        for factor in (1, 2, 3):
            s_f = self.W * self.m - factor * (self.bit["counts"]["N"] - self.bit["counts"]["L"])
            roots.append(kh.root_bounds({self.m - 1: Q(s_f, self.m - 1)},
                                        self.m, self.W))
        for (lo_a, _), (lo_b, _) in zip(roots, roots[1:]):
            self.assertLess(lo_a, lo_b)

    def test_saved_receipt_matches(self):
        saved = json.loads((ROOT / "certificates/kappa-headroom.json").read_text())
        self.assertEqual(kh.run(), saved)


if __name__ == "__main__":
    unittest.main()
