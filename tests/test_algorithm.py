"""Die Korrektheitskette der Verfahren (zuerst, vor jeder Messung): Kernsatz und Dreyfus-Wagner gegen Brute-Force, Gültigkeit, Garantien, Schrankenkette, Steiner-Verhältnis, Graph-Werkzeuge, Sonderfälle,
Buchführung, schwierige Fixtures."""

import heapq
import math

import numpy as np
import pytest

import stn_algorithm as A
import stn_constants as C
import stn_scenario as S
from brute import brute_steiner, brute_trees, graph_instance, random_graph_instance
from fixtures import FIXTURES, fixture


def _graphs(count=150):
    for seed in range(count):
        n = 5 + seed % 6
        yield random_graph_instance(n, 2 + seed % 6, 2 + seed % 4, seed, integer=seed % 3 == 0)


def _bound(t):
    return 2.0 * (1.0 - 1.0 / t) if t > 1 else 1.0


def _all_heuristics(g):
    return [A.kmb(g), A.takahashi_matsuyama(g), A.best_takahashi_matsuyama(g)]


# --- 1. Kernsatz und Exaktheit ----------------------------------------------------------------------------------------------------------------


def test_dreyfus_wagner_matches_the_brute_force_over_all_steiner_node_sets():
    for inst in _graphs(200):
        g = A.Graph(inst)
        ref = brute_steiner(inst)
        ex = A.dreyfus_wagner(g)
        assert ex.solution.cost == pytest.approx(ref), inst.terminals
        assert ex.solution.detail["dp_value"] == pytest.approx(ref)
        assert A.is_steiner_tree(g, ex.solution.edges) and A.leaves_are_terminals(g, ex.solution.edges)


def test_the_core_theorem_holds_independently_of_the_node_set_formulation():
    for seed in range(60):
        n = 5 + seed % 3
        inst = random_graph_instance(n, 2 + seed % 4, 2 + seed % 3, 900 + seed, integer=seed % 2 == 0)
        assert brute_trees(inst) == pytest.approx(brute_steiner(inst))


def test_grid_instances_match_brute_force():
    for seed in range(40):
        inst = S.generate(4, 3 + seed % 3, 0.2 * (seed % 3) / 2, "uniform", seed)
        g = A.Graph(inst)
        assert A.dreyfus_wagner(g).solution.cost == pytest.approx(brute_steiner(inst))


# --- 2. Gültigkeit ----------------------------------------------------------------------------------------------------------------------------


def test_every_output_is_a_steiner_tree_with_terminal_leaves_only():
    for inst in _graphs(150):
        g = A.Graph(inst)
        sols = _all_heuristics(g) + [A.dreyfus_wagner(g).solution]
        start = min(sols[:3], key=lambda s: s.cost)
        sols.append(A.local_search(g, start.steiner))
        for s in sols:
            assert A.is_steiner_tree(g, s.edges) and A.leaves_are_terminals(g, s.edges), s.method
            assert s.cost == pytest.approx(sum(g.w[e] for e in s.edges))
            assert set(s.steiner) == {x for e in s.edges for x in e} - set(inst.terminals)


# --- 3. Garantien und Schrankenkette ----------------------------------------------------------------------------------------------------------


def test_guarantees_and_bound_chain():
    for inst in _graphs(200):
        g = A.Graph(inst)
        opt = A.dreyfus_wagner(g).solution.cost
        t = len(inst.terminals)
        heur = _all_heuristics(g)
        for s in heur:
            assert opt - 1e-9 <= s.cost <= _bound(t) * opt + 1e-9, (s.method, inst.terminals)
        start = min(heur, key=lambda s: s.cost)
        ls = A.local_search(g, start.steiner)
        assert opt - 1e-9 <= ls.cost <= start.cost + 1e-9
        assert A.terminal_mst_cost(g) >= opt - 1e-9


def test_guarantees_on_city_instances_with_blocked_streets():
    for seed in range(60):
        inst = S.generate(6, 3 + seed % 8, 0.1 * (seed % 5), "uniform" if seed % 2 == 0 else "clusters", 300 + seed)
        g = A.Graph(inst)
        opt = A.dreyfus_wagner(g).solution.cost
        for s in _all_heuristics(g):
            assert opt - 1e-9 <= s.cost <= _bound(inst.t) * opt + 1e-9
        assert A.terminal_mst_cost(g) <= 2.0 * opt + 1e-9


def test_local_search_is_a_local_optimum_of_its_neighbourhood():
    for seed in range(40):
        inst = S.generate(5, 3 + seed % 5, 0.1 * (seed % 4), "uniform", 700 + seed)
        g = A.Graph(inst)
        ls = A.local_search(g, A.kmb(g).steiner)
        ts = set(inst.terminals)
        X = set(ls.steiner)
        for v in range(g.n):
            if v in ts:
                continue
            Y = X - {v} if v in X else (X | {v} if any(x in ts | X for x in g.adj[v]) else None)
            if Y is None:
                continue
            tree = A.induced_tree(g, ts | Y)
            if tree is not None:
                assert g.cost(tree) >= ls.cost - 1e-9


def test_local_search_rejects_a_start_that_does_not_connect_the_terminals():
    inst = graph_instance(4, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0)], (0, 3))
    g = A.Graph(inst)
    with pytest.raises(ValueError):
        A.local_search(g, [])
    assert A.local_search(g, [1, 2]).cost == 3.0


# --- 4. Steiner-Verhältnis --------------------------------------------------------------------------------------------------------------------


def test_steiner_ratio_is_at_most_two_in_graphs_and_three_halves_on_the_plain_grid():
    for inst in _graphs(120):
        g = A.Graph(inst)
        assert A.terminal_mst_cost(g) <= 2.0 * A.dreyfus_wagner(g).solution.cost + 1e-9
    worst = 0.0
    for seed in range(120):
        side = 4 + seed % 3
        inst = S.generate(side, 3 + seed % 6, 0.0, "uniform", 400 + seed, jitter=0.0)
        g = A.Graph(inst)
        worst = max(worst, A.terminal_mst_cost(g) / A.dreyfus_wagner(g).solution.cost)
    assert worst <= 1.5 + 1e-9 and worst > 1.0


def test_textbook_plus_by_hand():
    inst = S.textbook_instance()
    g = A.Graph(inst)
    assert A.terminal_mst_cost(g) == 6.0 and A.dreyfus_wagner(g).solution.cost == 4.0
    assert brute_steiner(inst) == 4.0
    ex = A.dreyfus_wagner(g).solution
    assert ex.steiner == [4] and A.branch_points(ex.edges, inst.terminals) == [4]
    assert A.kmb(g).cost == 6.0 and A.takahashi_matsuyama(g).cost == 6.0 and A.best_takahashi_matsuyama(g).cost == 4.0
    assert A.local_search(g, A.kmb(g).steiner).cost == 4.0


# --- 5. Graph-Werkzeuge -----------------------------------------------------------------------------------------------------------------------


def _dijkstra(n, w, s):
    adj = [[] for _ in range(n)]
    for (u, v), x in w.items():
        adj[u].append((v, x))
        adj[v].append((u, x))
    dist = [math.inf] * n
    dist[s] = 0.0
    heap = [(0.0, s)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, x in adj[u]:
            if d + x < dist[v]:
                dist[v] = d + x
                heapq.heappush(heap, (dist[v], v))
    return dist


def test_all_pairs_matches_dijkstra_and_paths_are_shortest():
    for inst in _graphs(60):
        g = A.Graph(inst)
        for s in range(g.n):
            ref = _dijkstra(g.n, g.w, s)
            assert np.allclose(g.dist[s], ref)
            for t in range(g.n):
                p = g.path(s, t)
                assert p[0] == s and p[-1] == t and len(set(p)) == len(p)
                assert sum(g.w[(min(a, b), max(a, b))] for a, b in zip(p, p[1:])) == pytest.approx(ref[t])


def test_all_pairs_keeps_the_cheaper_of_parallel_edges_and_marks_unreachable():
    d, nxt = A.all_pairs(3, {(0, 1): 5.0})
    assert d[0, 1] == 5.0 and math.isinf(d[0, 2]) and nxt[0, 2] == -1 and d[1, 1] == 0.0


def test_induced_tree_and_prune_and_kruskal_helpers():
    inst = graph_instance(5, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 5.0), (0, 3, 2.0), (3, 4, 1.0)], (0, 2))
    g = A.Graph(inst)
    assert A.induced_tree(g, {0, 1, 2, 3, 4}) is not None
    assert A.induced_tree(g, {0, 2}) is None
    assert A.prune(g, [(0, 1), (1, 2), (2, 3), (3, 4)]) == [(0, 1), (1, 2)]
    forest = A.kruskal_edges(g, g.edges)
    assert len(forest) == 4 and g.cost(forest) == pytest.approx(5.0)
    assert not A.is_steiner_tree(g, [(0, 1)]) and not A.is_steiner_tree(g, [(0, 1), (1, 2), (0, 2)]) and not A.is_steiner_tree(g, [(0, 4)])


# --- 6. Sonderfälle ---------------------------------------------------------------------------------------------------------------------------


def test_special_cases_one_two_and_all_terminals():
    for seed in range(40):
        n = 6 + seed % 3
        base = random_graph_instance(n, 4, 2, seed)
        g1 = A.Graph(graph_instance(n, base.edges, (0,)))
        assert A.dreyfus_wagner(g1).solution.cost == 0.0 and A.kmb(g1).cost == 0.0 and A.takahashi_matsuyama(g1).cost == 0.0
        a, b = 0, 1 + seed % (n - 1)
        g2 = A.Graph(graph_instance(n, base.edges, (a, b)))
        assert A.dreyfus_wagner(g2).solution.cost == pytest.approx(g2.dist[a, b]) and A.kmb(g2).cost == pytest.approx(g2.dist[a, b]) and A.takahashi_matsuyama(g2).cost == pytest.approx(g2.dist[a, b])
        gall = A.Graph(graph_instance(n, base.edges, tuple(range(n))))
        mst = g2.cost(A.kruskal_edges(gall, gall.edges))
        assert A.dreyfus_wagner(gall).solution.cost == pytest.approx(mst) and A.kmb(gall).cost == pytest.approx(mst) and A.takahashi_matsuyama(gall).cost == pytest.approx(mst)


def test_collinear_terminals_on_a_path_and_a_star_graph():
    path = graph_instance(6, [(i, i + 1, 2.0) for i in range(5)], (0, 3, 5))
    g = A.Graph(path)
    assert A.dreyfus_wagner(g).solution.cost == 10.0 and A.kmb(g).cost == 10.0 and A.takahashi_matsuyama(g).cost == 10.0
    star = graph_instance(6, [(0, i, 1.0) for i in range(1, 6)], (1, 2, 3, 4, 5))
    gs = A.Graph(star)
    ex = A.dreyfus_wagner(gs).solution
    assert ex.cost == 5.0 and ex.steiner == [0] and A.branch_points(ex.edges, star.terminals) == [0]
    assert A.terminal_mst_cost(gs) == 8.0 and A.kmb(gs).cost == 5.0


def test_equal_lengths_everywhere_and_determinism():
    edges = [(u, v, 1.0) for u in range(6) for v in range(u + 1, 6)]
    inst = graph_instance(6, edges, (0, 2, 4))
    g = A.Graph(inst)
    assert A.dreyfus_wagner(g).solution.cost == 2.0 and A.kmb(g).cost == 2.0
    for inst in list(_graphs(20)):
        g = A.Graph(inst)
        a, b = A.kmb(g), A.kmb(g)
        assert (a.edges, a.cost) == (b.edges, b.cost)
        a, b = A.dreyfus_wagner(g).solution, A.dreyfus_wagner(g).solution
        assert (a.edges, a.cost) == (b.edges, b.cost)


def test_takahashi_matsuyama_root_must_be_a_terminal_and_order_covers_all_terminals():
    inst = random_graph_instance(8, 5, 4, 3)
    g = A.Graph(inst)
    with pytest.raises(ValueError):
        A.takahashi_matsuyama(g, root=[v for v in range(8) if v not in inst.terminals][0])
    s = A.takahashi_matsuyama(g)
    assert sorted(s.detail["order"]) == sorted(inst.terminals) and s.detail["root"] == inst.terminals[0]
    assert A.best_takahashi_matsuyama(g).cost <= s.cost + 1e-9


# --- 7. Buchführung von KMB ---------------------------------------------------------------------------------------------------------------------


def test_kmb_steps_are_the_closure_mst_edges_expanded_to_shortest_paths():
    for inst in _graphs(60):
        g = A.Graph(inst)
        k = A.kmb(g)
        t = len(inst.terminals)
        assert len(k.detail["steps"]) == t - 1 and len(k.detail["closure"]) == t - 1
        assert math.fsum(st["dist"] for st in k.detail["steps"]) == pytest.approx(A.terminal_mst_cost(g))
        for st in k.detail["steps"]:
            assert st["path"][0] == st["a"] and st["path"][-1] == st["b"] and g.cost(g.path_edges(st["a"], st["b"])) == pytest.approx(st["dist"])
        assert set(k.edges) <= set(k.detail["expanded"]) and k.cost <= A.terminal_mst_cost(g) + 1e-9


# --- 8. Schwierige Fixtures (gegen Brute-Force bestätigt) -----------------------------------------------------------------------------------------


@pytest.mark.parametrize("name", list(FIXTURES))
def test_fixture_values_are_confirmed_by_brute_force_and_the_algorithms(name):
    inst, f = fixture(name)
    g = A.Graph(inst)
    assert brute_steiner(inst) == pytest.approx(f["opt"], abs=1e-3) and A.dreyfus_wagner(g).solution.cost == pytest.approx(f["opt"], abs=1e-3)
    k, tm, tmr = A.kmb(g), A.takahashi_matsuyama(g), A.best_takahashi_matsuyama(g)
    start = min((k, tm, tmr), key=lambda s: s.cost)
    ls = A.local_search(g, start.steiner)
    assert (k.cost, tm.cost, tmr.cost, ls.cost) == pytest.approx((f["kmb"], f["tm"], f["tmr"], f["ls"]), abs=1e-3)


def test_kmb_can_be_strictly_worse_than_the_optimum_and_tm_can_beat_kmb():
    _inst, f = fixture("kmb_worse")
    assert f["kmb"] > f["opt"] + 0.5 and f["tm"] == pytest.approx(f["opt"])
    _inst, f = fixture("tm_beats_kmb")
    assert f["tm"] < f["kmb"] - 0.5


def test_kmb_can_beat_takahashi_matsuyama_with_the_depot_as_root():
    _inst, f = fixture("kmb_beats_tm")
    assert f["kmb"] < f["tm"] - 0.3 and f["kmb"] == pytest.approx(f["opt"])


def test_the_root_matters_for_takahashi_matsuyama():
    _inst, f = fixture("tmr_beats_tm")
    assert f["tmr"] < f["tm"] - 1.0 and f["tmr"] == pytest.approx(f["opt"])


def test_local_search_can_improve_its_start_and_can_get_stuck():
    _inst, f = fixture("ls_improves")
    assert f["ls"] < min(f["kmb"], f["tm"], f["tmr"]) - 0.5 and f["ls"] == pytest.approx(f["opt"])
    _inst, f = fixture("ls_stuck")
    assert f["ls"] > f["opt"] + 0.5


def test_constants_consistent():
    assert C.N_EXACT >= 10 and C.T_MAX <= C.SIDE_MAX ** 2
