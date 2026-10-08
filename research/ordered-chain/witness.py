#!/usr/bin/env python3
"""Full witness for the reordered h=23 bit producer.

Reuses the pinned copied-reversed witness (`prior`), the fixed-middle copy
schedule and the balanced assembly, substituting only the recorded reordered
h=23 producer row. Yields the headline bit saving, the seven margins and the
final kappa for the reordered network.
"""
import argparse
from collections import Counter
from fractions import Fraction as Q
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
GRID = 10**14


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


prior = load('oc_prior', ROOT/'research/copied-reversed/witness.py')
fixedw = load('oc_fixed', ROOT/'research/copied-fixed-reversed/witness.py')
balanced = fixedw.balanced
js, read, moment = prior.js, prior.read, prior.moment
AC = prior.AC
PROFILE = ROOT/'research/copied-fixed-reversed/profile-25.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    """SHA-256 of a file's LF-normalised bytes, so a checkout cannot break it."""
    return sha256(Path(path).read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def ordered_axes():
    axes, _, _ = prior.inputs()
    record = read(HERE/'producer-23.json')['variant']
    require(record['h'] == 23 and record['v'] == 1771, 'ordered row dimension')
    require(record['loss'] == 23*22, 'ordered row loss')
    require(sum(r*n for r, n in enumerate(record['histogram']))
            == 23*record['R'] + 2*record['loss'], 'ordered row rank identity')
    rows = []
    for row in axes:
        row = dict(row)
        if row['h'] == 23:
            row.update(R=record['R'], loss=record['loss'],
                       histogram=record['histogram'], matching=record['matching'],
                       c=record['c'], q=record['q'], baseline_R=record['baseline_R'])
        rows.append(row)
    return rows


def counts():
    p = prior.counts(list(reversed(ordered_axes())))
    prof = read(PROFILE)
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
    require(sum(t*n for t, n in hist.items()) == p['W']*p['m'] - p['N'] + p['L'],
            'complete two-stage rank')
    require(all(0 < t < p['m'] and n > 0 for t, n in hist.items()), 'child domains')
    p['child_multiplicities'] = dict(sorted(hist.items()))
    p['maxchild'] = max(hist)
    return p


def bit_saving(bit):
    """Largest 1e-14 grid point whose strict moment still contracts."""
    m, W, rows = bit['m'], bit['W'], bit['child_multiplicities']

    def contracts(k):
        return moment(m, W, rows, Q(k, GRID))['upper'] < 1

    lo, hi = 0, 10**11
    require(contracts(lo), 'zero saving must contract')
    require(not contracts(hi), 'search bound must not contract')
    while lo + 1 < hi:
        mid = (lo + hi)//2
        if contracts(mid):
            lo = mid
        else:
            hi = mid
    a = Q(lo, GRID)
    require(contracts(lo) and not contracts(hi), 'grid bracket')
    require(moment(m, W, rows, a+Q(1, GRID))['lower'] > 1, 'next bit grid excluded')
    return a, moment(m, W, rows, a)


def run():
    bit = counts()
    a, exact = bit_saving(bit)
    phase_row = prior.inputs()[1]
    phase = prior.inherited.profile([phase_row, phase_row])
    f = prior.inherited.finite_bridge(bit, phase, [phase_row, phase_row])
    probe = balanced.assembly(f, a, Q(1, 10**20), a_complex=AC)
    margin = min(Q(v) for v in probe['margins'].values())
    kappa = Q((margin*GRID).__floor__(), GRID)
    if kappa >= margin:
        kappa -= Q(1, GRID)
    final = balanced.assembly(f, a, kappa, a_complex=AC)
    eventual = balanced.cutoffs(f, final)
    negatives = []
    for name, kwargs in [('next_kappa_grid', dict(kappa=kappa+Q(1, GRID))),
                         ('old_guard', dict(old_guard=True)),
                         ('old_exposures', dict(old_exposures=True)),
                         ('original_prefix', dict(original_prefix=True))]:
        try:
            balanced.assembly(f, kwargs.pop('a_bit', a), kwargs.pop('kappa', kappa),
                              a_complex=AC, **kwargs)
        except AssertionError:
            negatives.append(name)
        else:
            raise AssertionError('negative control accepted: '+name)
    return dict(status='Conditional reordered-aggregation witness; recorded finite '
                       'arithmetic with the pinned fixed-middle machinery',
                bit=dict(**{k: js(v) for k, v in exact.items() if k != 'logarithms'},
                         grid_point=str(a)),
                assembly=js(final), eventual_bounds=js(eventual),
                negative_controls=negatives, kappa=str(kappa),
                absorbing_margin=str(margin), margins=js(final['margins']),
                constraints_count=len(final['constraints']),
                provenance=dict(
                    producer_23_sha256=digest(HERE/'producer-23.json'),
                    profile_25_sha256=digest(PROFILE),
                    ordered_graph_sha256=digest(HERE/'ordered_graph.py')),
                scope='Updates only the h=23 producer row to the reordered aggregation; '
                      'the h=25 row, fixed profile, copied-centre schedule and assembly are '
                      'pinned. The reordering still needs the producer/matching and '
                      'physical-timeline audits of a full release.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE/'witness.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = run()
    if args.check:
        require(json.loads((HERE/'witness.json').read_text()) == result,
                'witness differs')
        print('PASS reordered witness: bit saving, seven margins, kappa, 47 constraints')
    else:
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n',
                               newline='\n')
        print('bit saving', result['bit']['saving'])
        print('kappa', result['kappa'])
        print('margin min', result['absorbing_margin'])
        print('constraints', result['constraints_count'])
        print('negatives', result['negative_controls'])
