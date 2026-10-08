#!/usr/bin/env python3
"""Exact certificate for the reordered-circuit bit producer (h=23).

Recomputes the fixed-middle (headline family) bit contraction root from the
recorded producer rows and the pinned `research/copied-fixed-reversed`
machinery. Pure standard-library Python: rebuilding the producer row itself
needs a C++17 compiler (see `ordered_graph.py`); this file only checks the
recorded finite arithmetic, exactly as the repository's other certificates do.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'scripts'))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


kh = load('kh_headroom', ROOT/'scripts/kappa_headroom.py')
cw = load('cw_witness', ROOT/'research/copied-reversed/witness.py')
RADIUS = 2**100


def rows(variant):
    record = json.loads((HERE/'producer-23.json').read_text())
    axes, _, _ = cw.inputs()
    out = []
    for row in axes:
        row = dict(row)
        if row['h'] == 23:
            source = record['variant' if variant else 'baseline']
            require(source['h'] == 23, 'row dimension')
            require(sum(r*n for r, n in enumerate(source['histogram']))
                    == 23*source['R'] + 2*source['loss'], 'producer rank identity')
            require(source['loss'] == 23*22, 'retained-total loss')
            row.update(R=source['R'], loss=source['loss'], histogram=source['histogram'],
                       matching=source['matching'], c=source['c'], q=source['q'],
                       baseline_R=source['baseline_R'])
        out.append(row)
    return out


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    """SHA-256 of a file's LF-normalised bytes, so a checkout cannot break it."""
    return sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def bit_histogram(variant):
    p = cw.counts(list(reversed(rows(variant))))
    prof = json.loads((ROOT/'research/copied-fixed-reversed/profile-25.json').read_text())
    h = prof['h']
    copied = list(prof['blocks'])
    copied[h] -= h
    copied[1] += h
    copies = p['N']//prof['v']
    replacement = Counter({t: n*copies for t, n in enumerate(copied) if t and n})
    before = p['parts']['internal_25']
    require(sum(t*n for t, n in before.items())
            == sum(t*n for t, n in replacement.items()), 'fixed-profile rank mass')
    p['parts']['internal_25'] = replacement
    hist = sum(p['parts'].values(), Counter())
    hist = {int(t): int(n) for t, n in hist.items() if n}
    return hist, p['m'], p['W'], p['N'], p['L']


def root(hist, m, W):
    lo, hi = kh.root_bounds(hist, m, W)
    return Q((lo*RADIUS).__floor__(), RADIUS), Q((hi*RADIUS).__ceil__(), RADIUS)


def run():
    base_hist, m, W0, N, L = bit_histogram(False)
    var_hist, m, W1, _, _ = bit_histogram(True)
    base_lo, base_hi = root(base_hist, m, W0)
    var_lo, var_hi = root(var_hist, m, W1)
    require(var_lo > base_hi, 'variant root does not strictly exceed the baseline')
    require(W1 < W0, 'variant role volume must fall')
    return dict(
        artifact='ordered-chain (h=23 reordered sum aggregation)',
        circuit=dict(point_order='aligned (unchanged)',
                     aggregation='sequential chain, sorted by (support cardinality, mask) desc',
                     baseline_aggregation='inherited balanced halving'),
        producer=dict(baseline_R=38776, variant_R=37620,
                      baseline_matching=1324, variant_matching=4044,
                      baseline_c=34764, variant_c=36328, q=5336,
                      h=23, v=1771, loss=506),
        network=dict(m=m, N=N, L=L, W_baseline=W0, W_variant=W1,
                     deficit=N-L,                     deficit_over_W_baseline=str(Q(N-L, W0)),
                     deficit_over_W_variant=str(Q(N-L, W1))),
        root=dict(baseline_lower=str(base_lo), baseline_upper=str(base_hi),
                  variant_lower=str(var_lo), variant_upper=str(var_hi),
                  improvement_ratio=str(var_lo/base_hi),
                  scope='fixed-middle (headline) family, h=25 row unchanged'),
        provenance=dict(
            producer_23_sha256=digest(HERE/'producer-23.json'),
            axes_sha256=digest(ROOT/'certificates/copied-centers-bit-axes.json'),
            profile_sha256=digest(ROOT/'research/copied-fixed-reversed/profile-25.json')),
        scope='Exact finite arithmetic on a recorded alternative producer row. '
              'The reordering is a scalar-circuit change and would require the '
              'producer/matching and physical-timeline audits of a full release '
              'before any headline change; this file makes no such claim.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE/'certificate.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run()
    text = json.dumps(result, indent=2, sort_keys=True)+'\n'
    if args.check:
        require(json.loads((HERE/'certificate.json').read_text()) == result,
                'certificate differs')
        print('PASS ordered-chain baseline/variant roots and role-volume drop')
    else:
        args.output.write_text(text, newline='\n')
        print('variant root in ['+result['root']['variant_lower']+', '
              + result['root']['variant_upper']+']')
