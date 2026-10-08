#!/usr/bin/env python3
"""Selected triple graph with a sequential, support-sorted sum aggregation.

This is `scripts/partial_swap/graph.py` with one change to the local
`PairedExclusionCircuit` in `scripts/partial_swap/paired.py`: the inherited
`ExclusionCircuit.total` aggregates its summands by balanced halving, while
this variant aggregates them in one sequential chain sorted by
`(support cardinality, support mask)` descending. Every summand is still added
once with disjoint supports, so the scalar circuit computes the same partial
outputs; only the interning tree changes, which changes the carrier edge set
and therefore the matched role count `R`.

Base circuit modules are jacklightChen/integer-mult-bounds PR7 at
`6725c6a17b17871a35353fd29157f4ed851bc114`, retained under their notices; the
selected retained-total handoff is icekylinx's. This variant is exploratory and
is not wired into `make verify`.
"""
from partial_swap.shared import SharedPointCircuit
from partial_swap.paired import PairedExclusionCircuit
from partial_swap.graph import aligned_points, export  # noqa: F401


def make_local(h, ordered=True):
    class Local(PairedExclusionCircuit):
        def total(self, values):
            values = [x for x in values if x]
            if ordered:
                values = sorted(values, key=lambda n: (self.support[n].bit_count(),
                                                       self.support[n]), reverse=True)
            result = 0
            for node in values:
                result = self.add(result, node)
            return result
    return Local(h-1)


def graph(h, ordered=True):
    local = make_local(h, ordered)
    total = local.pair(list(range(h-1)))[0]
    local.outputs[()] = total
    stack = [total]
    while stack:
        node = stack.pop()
        if not node or node in local.active:
            continue
        local.active.add(node)
        if local.args[node]:
            stack.extend(local.args[node])
    local.additions = sum(local.args[n] is not None for n in local.active)
    return SharedPointCircuit(h, local, point_order=aligned_points)
