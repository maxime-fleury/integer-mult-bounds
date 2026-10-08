#!/usr/bin/env python3
"""Exact headroom of the conditional exponent in the pinned community witness.

Reads only the pinned PR39 certificate and its certified assembly. It
recomputes, in exact rational arithmetic with outward-rounded logarithm and
exponential enclosures, the contraction functional that fixes the bit saving

    M(a) = sum_t (t n_t / (m W)) (m/t)^a = 1,

equivalently  sum_t n_t (t/m)^(1-a) = W.  From the exact child histogram it
brackets the true root a*, proves the structural ceilings

    a < b < 1/32   (certified balanced assembly)      and
    a* <= concentrated(m, W, s)   (relaxation over every histogram),

and decomposes the log budget L1 = sum_t (t n_t/(m W)) log(m/t) that controls
a* ~ (N-L)/(m W L1).  No new network is constructed and no stronger exponent
is claimed: this file quantifies the available headroom and its levers.
"""
import argparse
from fractions import Fraction as Q
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CERT = ROOT / 'research/copied-fixed-reversed/certificate.json'
GRID = 10**30
TERMS = 80


def require(condition, message):
    if not condition:
        raise ValueError(message)


def floor_grid(x):
    n = (x * GRID).numerator
    d = (x * GRID).denominator
    return Q(n // d, GRID)


def ceil_grid(x):
    n = (x * GRID).numerator
    d = (x * GRID).denominator
    return Q(-((-n) // d), GRID)


def log_unit(x):
    """Rigorous rational enclosure of log(x) for 1 <= x <= 2."""
    require(1 <= x <= 2, 'logarithm range')
    z = (x - 1) / (x + 1)
    lo = 2 * sum((z**(2*j+1) / (2*j+1) for j in range(TERMS)), Q(0))
    return lo, lo + 2 * z**(2*TERMS+1) / ((2*TERMS+1) * (1 - z*z))


def log_bounds(x):
    """Outward-rounded rational enclosure of log(x) for x >= 1."""
    require(x >= 1, 'logarithm domain')
    k = 0
    while x > 2:
        x /= 2
        k += 1
    lo, hi = log_unit(x)
    l2, u2 = log_unit(Q(2))
    return floor_grid(lo + k*l2), ceil_grid(hi + k*u2)


def exp_bounds(y):
    """Outward-rounded rational enclosure of exp(y) for y >= 0."""
    require(y >= 0, 'exponential domain')
    l2lo, l2hi = log_bounds(Q(2))
    k = int(y / l2hi)
    while k * l2hi > y:
        k -= 1
    while (k + 1) * l2lo <= y:
        k += 1
    rlo, rhi = y - k*l2hi, y - k*l2lo
    require(0 <= rlo and rhi < l2hi, 'binary scaling')

    def series(r):
        term = total = Q(1)
        for j in range(1, 13):
            term *= r / j
            total += term
        return total, total + term*r/13/(1 - r/14)

    elo, ehi = series(rlo)[0], series(rhi)[1]
    require(rlo < 14 and rhi < 14, 'series range')
    return floor_grid(2**k * elo), ceil_grid(2**k * ehi)


def scaled_moment_bounds(counts, m, a):
    """Enclose sum_t counts[t] (t/m)^(1-a), the contraction form equal to W."""
    beta = 1 - a
    lo = hi = Q(0)
    for t, c in counts.items():
        require(0 < t < m and c >= 0, 'child domain')
        llo, lhi = log_bounds(Q(m, t))
        elo = 1 / exp_bounds(beta*lhi)[1]
        ehi = 1 / exp_bounds(beta*llo)[0]
        lo += c*elo
        hi += c*ehi
    return floor_grid(lo), ceil_grid(hi)


class AboveCeiling(Exception):
    """The relaxed root lies above the certified-assembly ceiling."""


def root_bounds(counts, m, W, hi=Q(1, 32), steps=400):
    """Bracket the unique root of scaled_moment(counts) = W in (0, hi]."""
    lo = Q(0)
    require(scaled_moment_bounds(counts, m, lo)[1] < W, 'root below zero')
    if not scaled_moment_bounds(counts, m, hi)[0] > W:
        raise AboveCeiling('relaxed root above the 1/32 certified ceiling')
    for _ in range(steps):
        if hi - lo <= Q(1, 2**140):
            break
        mid = (lo + hi) / 2
        low, high = scaled_moment_bounds(counts, m, mid)
        if high < W:
            lo = mid
        elif low > W:
            hi = mid
        else:
            break
    return lo, hi


def histogram(counts):
    return {int(t): int(n) for t, n in counts['child_multiplicities'].items()}


def run():
    raw = CERT.read_bytes()
    data = json.loads(raw)
    bit, assembly = data['bit'], data['assembly']
    m, W, s = bit['counts']['m'], bit['counts']['W'], bit['counts']['total_rank']
    N, L = bit['counts']['N'], bit['counts']['L']
    hist = histogram(bit['counts'])

    require(sum(t*n for t, n in hist.items()) == s, 'rank identity')
    require(s == W*m - N + L, 'two-stage rank identity')
    require(all(0 < t < m and n > 0 for t, n in hist.items()), 'child domain')
    deficit = N - L

    weights = {t: Q(t*n, m*W) for t, n in hist.items()}
    require(sum(weights.values()) == Q(s, m*W), 'weight sum')
    l1_lo = l1_hi = Q(0)
    budget = []
    for t in sorted(hist):
        llo, lhi = log_bounds(Q(m, t))
        l1_lo += weights[t]*llo
        l1_hi += weights[t]*lhi
        budget.append(dict(width=t, children=hist[t], rank=t*hist[t],
                           weight=[str(floor_grid(weights[t])), str(ceil_grid(weights[t]))],
                           log_contribution=[str(floor_grid(weights[t]*llo)),
                                             str(ceil_grid(weights[t]*lhi))]))
    budget.sort(key=lambda r: Q(r['log_contribution'][1]), reverse=True)

    a_lo, a_hi = root_bounds(hist, m, W)
    require(a_lo < Q(bit['saving']) <= a_hi, 'pinned saving not bracketed')

    s_conc = Q(s, m-1)
    conc = {m-1: s_conc}
    c_lo, c_hi = root_bounds(conc, m, W)

    p = {k: Q(v) for k, v in assembly['parameters'].items()}
    a_bit, a_complex, kappa = p['a_bit'], p['a_complex'], p['kappa']
    require(a_bit < a_complex < Q(1, 32), 'certified saving ordering')
    require(min(Q(v) for v in assembly['margins'].values()) < a_bit, 'margin ordering')
    require(kappa < a_lo <= a_bit <= a_hi, 'headline below the root')

    def scaled_deficit_row(factor):
        s_f = W*m - factor*deficit
        try:
            lo_f, hi_f = root_bounds({m-1: Q(s_f, m-1)}, m, W)
        except AboveCeiling:
            return dict(factor=factor, exceeds_certified_ceiling=True,
                        note='concentrated root is above 1/32 at this deficit scaling')
        return dict(factor=factor, lower=str(lo_f), upper=str(hi_f))

    return dict(
        certificate='research/copied-fixed-reversed/certificate.json',
        certificate_sha256=sha256(raw).hexdigest(),
        rounds='rational 80-term atanh log and 12-term exp enclosures, outward 10^-30 rounding',
        network=dict(m=m, W=W, total_rank=s, N=N, L=L, deficit=deficit,
                     child_calls=sum(hist.values()), width1_children=hist[1],
                     deficit_over_W=str(floor_grid(Q(deficit, W))),
                     child_calls_over_W=str(floor_grid(Q(sum(hist.values()), W)))),
        identity=dict(sum_t_n_equals_s=True, s_equals_mW_minus_N_plus_L=True),
        contraction=dict(
            form='sum_t (t n_t/(m W))(m/t)^a = 1  <=>  sum_t n_t (t/m)^(1-a) = W',
            root_lower=str(a_lo), root_upper=str(a_hi),
            pinned_saving=bit['saving'],
            naive_uniform_saving=str(floor_grid(log_bounds(Q(W*m, s))[0]
                                                / log_bounds(Q(m))[1])),
            sharpness='root / naive uniform'),
        log_budget=dict(lower=str(l1_lo), upper=str(l1_hi),
                        first_order_root_over_deficit=str(floor_grid(
                            Q(deficit, 1) / (m*W*l1_hi))),
                        by_width=budget),
        ceilings=dict(
            concentrated_root_lower=str(c_lo), concentrated_root_upper=str(c_hi),
            concentration_headroom=str(floor_grid(c_lo / a_hi)),
            certified_saving_below_one_over32=True,
            kappa_below_one_over32=True,
            kappa_below_root=True,
            note='a<b<1/32 and the kappa margin are certified slacks; the '
                 'concentrated root bounds every histogram with this (m,W,s).'),
        deficit_scaling=dict(
            factors=[2, 3, 4, 5, 10],
            concentrated_roots=[scaled_deficit_row(f) for f in (2, 3, 4, 5, 10)],
            first_order='a* is first-order linear in the deficit N-L for fixed (m,W,L1)'),
        scope='Headroom and lever arithmetic only. The network, its saving and the '
              'pinned assembly are inputs; no new finite network, patch or exponent '
              'is constructed, and the inheritied #109 hypotheses remain assumed.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'certificates/kappa-headroom.json')
    parser.add_argument('--check', type=Path)
    args = parser.parse_args()
    receipt = run()
    if args.check:
        require(receipt == json.loads(args.check.read_text()), 'headroom receipt differs')
        print('PASS headroom root, log budget, ceilings and deficit scaling')
        return
    text = json.dumps(receipt, indent=2, sort_keys=True) + '\n'
    if args.output:
        args.output.write_text(text)
    print('root a* in [' + receipt['contraction']['root_lower'] + ', '
          + receipt['contraction']['root_upper'] + ']')
    print('concentrated ceiling a* <= ' + receipt['ceilings']['concentrated_root_upper'])
    print('headroom factor ' + receipt['ceilings']['concentration_headroom']
          + '; kappa < 1/32')


if __name__ == '__main__':
    main()
