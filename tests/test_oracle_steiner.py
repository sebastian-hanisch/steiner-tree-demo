"""Unabhängiges Orakel: das exakte Optimum (Dreyfus-Wagner) gegen (1) Aufzählung ALLER Kantenmengen auf winzigen Graphen mit Gleichständen und (2) ein ganzzahliges Programm (Mehr-Güter-Fluss, HiGHS
über scipy.optimize.milp) auf Stadtplänen; dazu Güte-Schranken der Heuristiken gegen dieses Optimum."""

import math
import random

import numpy as np
import pytest

import stn_algorithm as A
import stn_evaluation as ev
import stn_scenario as S
from brute import graph_instance


def _is_tree_with(terminals, edges):
    nodes = {x for e in edges for x in e[:2]}
    if len(terminals) == 1:
        return not edges
    if not set(terminals) <= nodes or len(edges) != len(nodes) - 1:
        return False
    parent = {x: x for x in nodes}

    def find(x):
        while parent[x] != x:
            x = parent[x]
        return x

    for u, v, _w in edges:
        a, b = find(u), find(v)
        if a == b:
            return False
        parent[a] = b
    return True


def _brute_edge_sets(inst):
    best = math.inf
    edges = list(inst.edges)
    for mask in range(1 << len(edges)):
        sel = [edges[i] for i in range(len(edges)) if mask >> i & 1]
        cost = sum(e[2] for e in sel)
        if cost < best and _is_tree_with(inst.terminals, sel):
            best = cost
    return best


def _milp_steiner(inst):
    scipy_opt = pytest.importorskip("scipy.optimize")
    from scipy.sparse import lil_matrix

    T = list(inst.terminals)
    root, others = T[0], T[1:]
    arcs = [(u, v, w) for u, v, w in inst.edges] + [(v, u, w) for u, v, w in inst.edges]
    na, K, n = len(arcs), len(others), inst.n
    nv = na + K * na
    c = np.zeros(nv)
    for a, (_u, _v, w) in enumerate(arcs):
        c[a] = w
    mat = lil_matrix((K * n + K * na, nv))
    lo, hi, r = [], [], 0
    for k, t in enumerate(others):
        for v in range(n):
            for a, (x, y, _w) in enumerate(arcs):
                if x == v:
                    mat[r, na + k * na + a] += 1
                if y == v:
                    mat[r, na + k * na + a] -= 1
            b = 1 if v == root else (-1 if v == t else 0)
            lo.append(b)
            hi.append(b)
            r += 1
    for k in range(K):
        for a in range(na):
            mat[r, na + k * na + a] = 1
            mat[r, a] = -1
            lo.append(-np.inf)
            hi.append(0)
            r += 1
    integrality = np.zeros(nv)
    integrality[:na] = 1
    res = scipy_opt.milp(c, constraints=scipy_opt.LinearConstraint(mat.tocsr(), lo, hi), integrality=integrality, bounds=scipy_opt.Bounds(0, 1))
    assert res.status == 0
    return float(res.fun)


def test_exact_equals_the_minimum_over_all_edge_sets_on_tiny_graphs():
    rng = random.Random(11)
    done = 0
    while done < 60:
        n = rng.randint(3, 6)
        perm = list(range(n))
        rng.shuffle(perm)
        es = {(min(a, b), max(a, b)) for a, b in zip(perm, perm[1:])}
        pairs = [(u, v) for u in range(n) for v in range(u + 1, n)]
        es |= set(rng.sample(pairs, rng.randint(0, 3)))
        if len(es) > 9:
            continue
        wmax = rng.choice([1, 2, 5])
        edges = [(u, v, float(rng.randint(1, wmax))) for u, v in sorted(es)]
        terminals = sorted(rng.sample(range(n), rng.randint(1, min(n, 4))))
        inst = graph_instance(n, edges, terminals)
        g = A.Graph(inst)
        assert A.dreyfus_wagner(g).solution.cost == pytest.approx(_brute_edge_sets(inst))
        done += 1


@pytest.mark.parametrize("seed", range(8))
def test_city_instances_exact_and_heuristics_against_the_integer_program(seed):
    rng = random.Random(seed)
    inst = S.generate(rng.choice([4, 5]), rng.randint(3, 6), rng.choice([0.0, 0.1, 0.3]), rng.choice(["uniform", "clusters"]), seed)
    opt = _milp_steiner(inst)
    g = A.Graph(inst)
    assert A.dreyfus_wagner(g).solution.cost == pytest.approx(opt)
    t = inst.t
    for sol in (A.kmb(g), A.takahashi_matsuyama(g), A.best_takahashi_matsuyama(g)):
        assert opt - 1e-9 <= sol.cost <= 2 * (1 - 1 / t) * opt + 1e-9
    a = ev.analyse(ev.Settings(side=inst.side, t=inst.t, blocked=inst.blocked, layout=inst.layout, seed=seed))
    assert a.best.cost == pytest.approx(opt) and a.ratio == pytest.approx(a.mst_cost / opt)


def test_textbook_plus_and_a_standard_preset_against_the_integer_program():
    tb = S.textbook_instance()
    assert _milp_steiner(tb) == pytest.approx(4.0)
    std = S.generate(8, 7, 0.1, "uniform", 35)
    assert _milp_steiner(std) == pytest.approx(A.dreyfus_wagner(A.Graph(std)).solution.cost)