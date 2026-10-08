# Exponent headroom: what a push toward κ = 1 would require

Date: 2026-10-08. Exact analysis of the pinned PR39 bit network
(`research/copied-fixed-reversed/certificate.json`), produced with
[`scripts/kappa_headroom.py`](../../scripts/kappa_headroom.py) and its
[receipt](../../certificates/kappa-headroom.json). This is arithmetic on the
pinned witness; it constructs no new network and claims no new exponent.

## Result in one line

`kappa = 1` (that is, an `O(n)` time bound) is **not reachable in this
framework**. Two independent ceilings bind long before it:

- the certified balanced assembly forces `a < b < 1/32`, hence `kappa < 1/32`;
- the pinned bit network's own contraction root is at most `0.009806`
  (`~252x` its current saving), whatever the child-width distribution.

The interesting number is therefore not `1`, it is the gap between the current
`kappa = 3.8867e-5` and those ceilings.

## The contraction functional

A recursive layer at parameter `m` with role volume `W` and child
multiplicities `n_t` contracts exactly when

```
M(a) = sum_t (t n_t / (m W)) (m/t)^a  =  1
     <=>  sum_t n_t (t/m)^(1-a)  =  W.
```

The second form is convenient: `(t/m)^(1-a)` increases in the child width `t`,
so the root `a*` is **maximised by concentrating rank mass at the largest
child width** `m-1`.

Pinned inputs: `m = 575`, `W = 188181929`, `s = sum_t t n_t = 108202762275`,
`N = 4073300`, `L = 2226400`. Exact `80`-term logarithm and `12`-term
exponential enclosures (outward `10^-30`) give

| quantity | value |
| --- | --- |
| root bracket `a*` | `[3.88682692005e-5, 3.88682692289e-5]` |
| pinned saving `a` | `3886826921/10^14 = 3.886826921e-5` |
| naive uniform `-log(s/(Wm))/log m` | `2.6861e-6` |
| sharpness `a* / naive` | `14.47` |
| child calls `sum_t n_t` | `2697045067 = 14.33 · W` |
| rank deficit `N - L` | `1846900` |
| `deficit / W` | `9.8144e-3` |
| log budget `L1 = sum_t w_t log(m/t)` | `[0.439091, 0.439103]` |

The first-order identity `a* ~ (N-L)/(m W L1)` reproduces the root
(`3.887e-5`). So the saving is **the rank deficit per role, devalued by the
logarithmic spread of the child widths**. The pinned witness is already close
to its own root, so parameter tuning cannot move it.

## Ceiling A — the assembly caps κ at 1/32

The balanced assembly's strict slacks include `complex_above_bit = b - a > 0`
and `complex_below_one_over32 = 1/32 - b > 0`
([`structured_bulk_assembly.py`](../../scripts/structured_bulk_assembly.py)),
and every margin is itself an exponent saving with `kappa < min(margins)`.
Hence

```
kappa < a < b < 1/32 = 0.03125.
```

This is a property of the certified assembly, not of all possible analyses,
but it holds for the whole current parameter family: **no finite network can
push the headline past 3.125% here.**

## Ceiling B — the network caps a* at ~0.0098

For any histogram with `sum_t t n_t = s`, monotonicity of `(t/m)^(1-a)` in `t`
gives

```
sum_t n_t (t/m)^(1-a)  >=  (s/(m-1)) ((m-1)/m)^(1-a).
```

The relaxed root of `(s/(m-1)) ((m-1)/m)^(1-a) = W` (all rank mass at width
`m-1`) is `0.009806`; equivalently, to first order, `a* <= deficit / W`.
Every width distribution of this `(m, W, s)` therefore has

```
a* <= 0.009806  (252.3x the current saving),  and  a* < deficit/W < 1/2 always.
```

To approach `a* = 1` one would need `deficit/W -> 1`, impossible because
`deficit = N - L < N` while `W = 2N + B1 + B2 > 2N`.

## Where the budget actually goes

`L1` splits by child width as follows (share of the log budget):

| width | share of `L1` | note |
| --- | ---: | --- |
| 1 | 26.3% | `1968720627` children |
| 23, 25 | 30.2% | the two central banks |
| 525, 529 | 17.4% | near-full-width children |
| 481 | 1.5% | data block |
| widths `< 23` | 51.0% | every small child |

The width-1 mass dominates and comes almost entirely from the copied-centre
internal histograms:

| source part | width-1 children | share |
| --- | ---: | ---: |
| `internal_23` | 1183039500 | 60.1% |
| `internal_25` | 691995227 | 35.2% |
| `data` (singletons) | 73319400 | 3.7% |
| `growth_23` + `growth_25` | 16293200 | 0.8% |
| `paid_correction` | 4073300 | 0.2% |

This is not hypothetical: the fixed-middle-basis step from PR #37 to PR #39
cut `internal_25`'s width-1 mass by about `45%`, and that alone raised the bit
saving from `3.8509e-5` to `3.8868e-5` (`+0.93%`). The lever is real and only
partly spent.

## Ranked levers

1. **Width concentration — up to `252x`.** Every child of width below `23`
   contributes `51%` of `L1`. Any producer/matching whose copied-centre rank
   profile deposits mass at rank `1` or `h` instead of the middle reduces the
   `(h-r)` and `r` residues that generate width-1 children. Applying the
   fixed-basis mechanism of PR #39 to `h = 23` (still the larger
   contributor) is the immediate experiment.
2. **Deficit scaling — first-order linear.** `a* ~ (N-L)/(m W L1)`.
   Concentrated roots: `x2 -> 0.0196`, `x3 -> 0.0294`, `x4` already exceeds
   the `1/32` assembly ceiling. So a `3x` deficit broadly saturates what the
   current assembly can carry; the network side and the assembly side must be
   improved together.
3. **Role volume `W` — the other half of lever 2.** `W = 188181929 =
   2N + B1 + B2` with `B1 + B2 = 180035329`, so `deficit/W` is under `2%`.
   Reducing the `h=25`/`h=23` matched role counts (`R = 51299`) is a direct
   multiplier on `deficit/W` and cuts `L1` at the same time.
4. **Data profile — small.** Shrinking the `9` reversed-corner singletons to
   `0` removes only `0.0098` of `L1` (`~2%` of the saving); the internal
   histograms dominate.
5. **Complex network — not binding.** `b = 7.17e-5 > a`, so improving it alone
   changes nothing until the bit network passes it.

## What "goal κ = 1" should mean here

κ = 1 is an `O(n)` claim and is out of reach by at least two orders of
magnitude on each ceiling. A defensible target sequence is `2^-15 -> 2^-14`
(gap `x2.0`, reachable by roughly a `2x` width/deficit improvement), then
`2^-13` (`x4`), at which point the `1/32` assembly ceiling and a `~16x`
width-concentration gain both start to bind. Beyond that the sorted order of
the recursive framework itself — not its constants — has to change.

## Tested: the carrier matching is already optimal

The partial-swap matchers contain no `__int128`, so the producer path was
rebuilt here with MSVC (the repo's own pipeline otherwise needs GCC/Clang).
Both certified producers reproduce exactly: `h=23` gives `R=38776`, `h=25`
gives `R=51299`, with byte-identical rank histograms.

With that pipeline I instrumented the matcher (`DUMP_EDGES` mode) to list every
admissible carrier edge with its exact signed rank change, and solved the
maximum-cardinality matching minimising the induced bit log budget `L1` — the
quantity this analysis ranks as the first lever. Exact result: for both `h=23`
and `h=25` the minimiser reproduces the pinned histogram, so

- `R` cannot be lowered by re-matching: the pinned matching already attains
  maximum cardinality (`R = c + q - matches`), and
- the pinned histogram already minimises `L1` among maximum-cardinality
  matchings.

So the carrier-matching lever is exhausted for this graph. The two remaining
levers are the ones listed above that a re-match cannot reach: a larger rank
deficit `N - L`, and a **different edge set** (a reordered circuit). Only a
circuit change moves `R`; the precedent for that step (climbed summand orders
on exclusion circuits) is worth roughly `0.1%` per step, while the multi-percent
jumps have come from new circuit constructions rather than from re-matching.

This experiment is a local prototype (it needs a C++ compiler and SciPy); it is
not part of `make verify` and changes no pinned artifact.

## Tested: a reordered sum aggregation does move kappa

The same rebuilt pipeline shows that the **edge set** is a live lever. Replacing
the h=23 producer's balanced-halving `total()` with a single sequential chain
sorted by `(support cardinality, support mask)` descending lowers the matched
carrier roles `38,776 -> 37,620`, the role volume `W` `188,181,929 ->
185,523,129`, and raises the fixed-middle bit root by **`+1.137%`**
(`3.88682692005e-5 -> 3.9310300305e-5`) with every other pinned row unchanged.
Installed into the pinned fixed-middle witness, the reordered row gives a full
conditional `kappa = 982718877/25000000000000 = 3.930875508e-5` (pinned
`971668963/25000000000000`), with all seven margins still strict and the four
negative controls rejected. The same change on h=25 (generic family) gives
`+2.38%` for both dimensions; the fixed-middle headline is capped by the h=25
fixed-basis profile, which this checkout cannot rebuild without `__int128`. See
[the reordered-aggregation candidate](../../research/ordered-chain/README.md).
Integrating it into a headline needs the producer/matching and physical-timeline
audits of a full release; the recorded finite arithmetic is checked by
`make ordered-chain-check`.

## Verify

```sh
make kappa-headroom-check
python3 scripts/kappa_headroom.py
python3 -m unittest discover -s tests -p 'test_kappa_headroom.py' -v
```

Scope: exact arithmetic on the pinned certificate. The upstream #109
hypotheses, the written common-basis/CRT proofs and the producer/matching
interfaces remain assumed as in the release; this analysis neither verifies
them nor produces a stronger multiplication bound.
