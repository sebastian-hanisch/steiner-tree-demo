"""Pläne: Erzeugung, Determinismus, Zusammenhang, Sperrungen, Jitter, Terminal-Layouts, Lehrbuchbeispiel."""

import numpy as np
import pytest

import stn_algorithm as A
import stn_constants as C
import stn_scenario as S
from stn_unionfind import UnionFind


def _connected(inst):
    uf = UnionFind(inst.n, "full")
    for u, v, _w in inst.edges:
        uf.union(u, v)
    return uf.components == 1


def test_generate_is_deterministic_and_well_formed():
    a, b = S.generate(8, 7, 0.2, "uniform", 5), S.generate(8, 7, 0.2, "uniform", 5)
    assert np.array_equal(a.xy, b.xy) and a.edges == b.edges and a.terminals == b.terminals and a.blocked_edges == b.blocked_edges
    assert a.n == 64 and a.t == 7 and a.side == 8 and a.kind == "city" and a.m + len(a.blocked_edges) == 2 * 8 * 7
    assert all(u < v and w > 0 for u, v, w in a.edges) and list(a.edges) == sorted(a.edges, key=lambda e: (e[0], e[1]))
    assert list(a.terminals) == sorted(set(a.terminals)) and len(a.terminals) == 7 and all(0 <= x < a.n for x in a.terminals)
    assert S.generate(8, 7, 0.2, "uniform", 6).terminals != a.terminals or S.generate(8, 7, 0.2, "uniform", 6).edges != a.edges
    assert set(a.steiner_candidates) == set(range(a.n)) - set(a.terminals)


def test_the_plan_stays_connected_for_every_blocked_share():
    for share in C.BLOCKED_OPTIONS:
        for seed in range(15):
            inst = S.generate(6, 5, share, "uniform", seed)
            assert _connected(inst)
            assert len(inst.blocked_edges) <= round(share * 2 * 6 * 5) + 0
    assert len(S.generate(8, 7, 0.0, "uniform", 3).blocked_edges) == 0
    assert len(S.generate(8, 7, 0.4, "uniform", 3).blocked_edges) == 45


def test_blocked_edges_are_exactly_the_missing_grid_streets():
    inst = S.generate(6, 5, 0.3, "uniform", 4)
    have = {(u, v) for u, v, _w in inst.edges}
    grid = {(min(u, v), max(u, v)) for u, v in S._grid_edges(6)}
    assert have | set(inst.blocked_edges) == grid and not have & set(inst.blocked_edges)


def test_jitter_perturbs_the_lengths_and_zero_jitter_gives_unit_lengths():
    plain = S.generate(5, 4, 0.0, "uniform", 2, jitter=0.0)
    assert all(w == pytest.approx(C.SPACING) for _u, _v, w in plain.edges)
    jit = S.generate(5, 4, 0.0, "uniform", 2)
    lens = [w for _u, _v, w in jit.edges]
    assert min(lens) < C.SPACING * 0.95 and max(lens) > C.SPACING * 1.05 and all(C.SPACING * (1 - 2 * C.JITTER) - 1e-9 <= w <= C.SPACING * (1 + 2 * C.JITTER) * 1.5 for w in lens)


def test_terminal_layouts():
    uni = [S.generate(10, 9, 0.0, "uniform", s) for s in range(20)]
    clu = [S.generate(10, 9, 0.0, "clusters", s) for s in range(20)]

    def spread(inst):
        pts = inst.xy[list(inst.terminals)]
        d = np.hypot(pts[:, None, 0] - pts[None, :, 0], pts[:, None, 1] - pts[None, :, 1])
        return d.sum() / (len(pts) * (len(pts) - 1))
    assert np.mean([spread(i) for i in clu]) < 0.75 * np.mean([spread(i) for i in uni])
    for inst in clu:
        assert inst.t == 9 and len(set(inst.terminals)) == 9 and inst.layout == "clusters"


def test_invalid_arguments_raise():
    with pytest.raises(ValueError):
        S.generate(5, 4, 0.0, "ring", 1)
    with pytest.raises(ValueError):
        S.generate(5, 0, 0.0, "uniform", 1)
    with pytest.raises(ValueError):
        S.generate(5, 26, 0.0, "uniform", 1)
    assert S.generate(5, 25, 0.0, "uniform", 1).t == 25


def test_textbook_plus():
    t = S.textbook_instance()
    assert t.kind == "textbook" and t.n == 9 and t.m == 12 and t.terminals == (1, 3, 5, 7) and t.steiner_candidates == (0, 2, 4, 6, 8)
    assert all(w == 1.0 for _u, _v, w in t.edges) and _connected(t)
    assert A.terminal_mst_cost(A.Graph(t)) == 6.0
