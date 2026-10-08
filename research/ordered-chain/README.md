# Reordered sum aggregation: a candidate h=23 bit producer

A bounded research experiment on the **bit** finite network, the current
bottleneck of the conditional exponent (`kappa < a < b < 1/32`; see
[the headroom analysis](../../docs/research/kappa-headroom.md)).

## Result

Changing one thing in the h=23 producer — the inherited `total()` aggregates
its summands by balanced halving, this candidate aggregates them as a single
sequential chain sorted by `(support cardinality, support mask)` descending —
moves the exact matched carrier roles and the implied saving:

| quantity | pinned (PR39) | this candidate |
| --- | ---: | ---: |
| h=23 matched carrier roles `R` | 38,776 | **37,620** |
| role volume `W` | 188,181,929 | **185,523,129** |
| fixed-middle bit root `a*` | 3.88682692005e-5 | **3.9310300305e-5** |

That is **+1.137%** on the headline (fixed-middle) family, with the h=25 row and
every other pinned artifact unchanged. The gain comes from the role volume: the
rank deficit `N - L = 1,846,900` is fixed, so `a* ~ (N-L)/(m W L1)` rises as `W`
falls. The carrier matching itself was also re-solved at minimum cost over the
new edge set (SciPy) and adds only `+0.0016%`, so the effect is the reordering,
not the matching.

A hedge against the "cheap transformation" objection: the chain adds gates
(`c` 34,764 -> 36,328) but admits many more carrier matches (1,324 -> 4,044), and
`R = c + q - matches` falls. All summands are still added once with disjoint
supports, and the scalar circuit is re-verified exactly.

## Full witness

Substituting only the recorded reordered h=23 row into the pinned copied-reversed
witness and the fixed-middle assembly gives a complete conditional exponent:

| quantity | pinned (PR39) | this candidate |
| --- | ---: | ---: |
| headline `kappa` | `971668963/25000000000000` = 3.886675852e-5 | **`982718877/25000000000000` = 3.930875508e-5** |
| absorbing margin (min of 7) | — | `122844688499631465934500245689377/3125122844688499754310623000000000000` |
| assembly constraints | — | 47 |

All seven strict exponent margins move with the bit root, the four negative
controls (`next_kappa_grid`, `old_guard`, `old_exposures`, `original_prefix`)
are still rejected, and `kappa > 2^-15` continues to hold with a slightly larger
cushion. `witness.json` is the recorded result; `witness.py --check` recomputes
and compares it exactly.

## Method

- `ordered_graph.py` builds `SharedPointCircuit(h, local, aligned_points)` with a
  local `PairedExclusionCircuit` whose `total()` is the sorted sequential chain.
- The producer pipeline (`match_exported_dag`, `positive.py`, `match_positive_dag`)
  regenerates the row; `build/orders` holds the local prototype. The matchers
  contain no `__int128`, so they build with MSVC as well as GCC/Clang.
- `measure.py` recomputes the fixed-middle bit contraction root from the recorded
  rows with the repository's exact rational enclosures (standard library only).

## What is and is not checked

Checked: the scalar circuit's complete partial-output supports (`verify()`), the
producer rank identities `sum r*n = h*R + 2*loss` and `loss = h(h-1)`, the
copied-centre and fixed-profile rank masses, the exact contraction roots of both
families, the containment of the pinned bit saving `3886826921/10^14` in the
recomputed baseline interval (so the substitution really does reproduce the
pinned family), the full witness margins, the grid-point `kappa` and the four
rejected negative controls (`tests/test_ordered_chain.py`, 9 checks).

Provenance digests are taken over LF-normalised bytes, so a checkout's line
endings cannot invalidate them.

**Not** checked, and required before any headline change: the reordered row is
*recorded*, not rebuilt by the checked pipeline (`producer-23.json` came from the
local MSVC prototype in `build/orders`), so the producer / carrier-matching and
physical-timeline / dirty-basis audits a reordered circuit needs are still open,
as are regeneration of the pinned certificates and patches and the h=25
fixed-basis profile for a reordered h=25 (blocked here because
`full_profiles25.cpp` uses `__int128`, which MSVC lacks). The generic
(not fixed-middle) family is already `+2.38%` with both dimensions reordered;
the h=25 fixed profile is what caps the headline number here.

## Reproduce

```sh
python3 research/ordered-chain/measure.py            # bit-root certificate
python3 research/ordered-chain/witness.py            # full kappa witness
make ordered-chain-check                             # recheck both
python3 -m unittest discover -s tests -p 'test_ordered_chain.py' -v
```

Rebuilding `producer-23.json` needs a C++17 compiler:
`python3 -c "import research.ordered_chain.ordered_graph ..."` is not shipped as
a target; the recorded row plus `measure.py` is the checked artifact.

## Attribution

Base circuits: jacklightChen/integer-mult-bounds PR7 at
`6725c6a17b17871a35353fd29157f4ed851bc114`; selected retained-total handoff by
icekylinx (Apache-2.0). Reordered-aggregation and this experiment by the
maintainer line of this checkout, with AI assistance. The stacked-order idea
follows the community climbed-order work (Rohan Arun, PR47/48) on the exclusion
circuits.
