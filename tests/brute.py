"""Referenzen nur für die Tests: Brute-Force-Steinerbaum über alle Steinerpunkt-Mengen, Zufallsgraphen."""

from itertools import combinations

import numpy as np

import stn_algorithm as A
import stn_scenario as S


def graph_instance(n, edges, terminals):
    """Instanz aus einem beliebigen Graphen (Kanten (u, v, w), u < v)."""
    return S.Instance(np.zeros((n, 2)), tuple(sorted(edges)), tuple(sorted(terminals)), side=0)


def random_graph_instance(n, extra, t, seed, integer=False):
    """Zusammenhängender Zufallsgraph: zufälliger Pfad über alle Knoten plus `extra` weitere Kanten; Längen zufällig (ganzzahlig 1..5 bei integer=True: viele Gleichstände)."""
    rng = np.random.default_rng([seed, 8080])
    pairs = set()
    perm = [int(x) for x in rng.permutation(n)]
    for a, b in zip(perm, perm[1:]):
        pairs.add((min(a, b), max(a, b)))
    allp = [(u, v) for u in range(n) for v in range(u + 1, n)]
    for j in rng.permutation(len(allp))[:extra]:
        pairs.add(allp[int(j)])
    edges = [(u, v, float(rng.integers(1, 6)) if integer else float(np.round(rng.uniform(1, 10), 3))) for u, v in sorted(pairs)]
    terminals = [int(x) for x in rng.choice(n, size=t, replace=False)]
    return graph_instance(n, edges, terminals)


def brute_steiner(inst):
    """Kleinste Kosten über alle Steinerpunkt-Mengen X: beschnittener MST des induzierten Teilgraphen G[T + X] (Kernsatz)."""
    g = A.Graph(inst)
    ts = set(inst.terminals)
    cands = [v for v in range(inst.n) if v not in ts]
    best = None
    for r in range(len(cands) + 1):
        for X in combinations(cands, r):
            tree = A.induced_tree(g, ts | set(X))
            if tree is not None:
                c = g.cost(tree)
                if best is None or c < best - 1e-9:
                    best = c
    return best


def brute_trees(inst):
    """Alle Bäume in G, die die Terminals enthalten und nur Terminals als Blätter haben (nur für sehr kleine Graphen): kleinste Kosten - unabhängig vom Kernsatz."""
    g = A.Graph(inst)
    edges = g.edges
    ts = set(inst.terminals)
    best = None
    n = inst.n
    for r in range(len(ts) - 1, n):
        for combo in combinations(edges, r):
            nodes = {x for e in combo for x in e}
            if len(nodes) != r + 1 or not ts <= nodes:
                continue
            if A.is_steiner_tree(g, combo):
                c = g.cost(combo)
                if best is None or c < best - 1e-9:
                    best = c
    return best
