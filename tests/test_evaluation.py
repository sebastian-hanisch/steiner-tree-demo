"""Auswertung: Analysis-Felder, Kennzahlen über feste Instanzen, Sweeps, Qualitäts-Experiment, Aufwandskurve, Determinismus."""

from dataclasses import replace

import pytest

import stn_algorithm as A
import stn_constants as C
import stn_evaluation as ev

BASE = ev.Settings(seed=0)


def test_analyse_fields_are_consistent():
    a = ev.analyse(ev.Settings())
    assert a.t == 7 and a.exact_offered and a.proved and set(a.sols) == {"kmb", "tm", "tmr", "ls", "exact"}
    for name, s in a.sols.items():
        assert A.is_steiner_tree(a.g, s.edges) and A.leaves_are_terminals(a.g, s.edges), name
        assert s.cost == pytest.approx(a.g.cost(s.edges))
    assert a.best.cost == pytest.approx(a.sols["exact"].cost) and a.excess(a.best_name) == pytest.approx(0.0, abs=1e-9)
    assert a.mst_cost == pytest.approx(A.terminal_mst_cost(a.g)) and a.ratio == pytest.approx(a.mst_cost / a.best.cost) and a.bound == pytest.approx(2.0 * (1 - 1 / 7))
    assert a.saving("exact") == pytest.approx(100.0 * (1 - a.best.cost / a.mst_cost)) and a.saving("nope") is None and a.excess("nope") is None
    assert a.n_branch("exact") == len(A.branch_points(a.sols["exact"].edges, a.inst.terminals)) and all(d >= 2 for d in a.steiner_degrees("exact"))
    assert a.states == (2 ** 6 - 1) * a.inst.n


def test_exact_is_only_offered_up_to_the_terminal_limit():
    small = ev.analyse(ev.Settings(side=6, t=C.N_EXACT))
    big = ev.analyse(ev.Settings(side=6, t=C.N_EXACT + 1))
    assert small.proved and not big.proved and "exact" not in big.sols and big.states == 0
    assert big.best_name in ("kmb", "tm", "tmr", "ls")


def test_terminal_count_is_clamped_to_the_number_of_crossings():
    a = ev.analyse(ev.Settings(side=5, t=30))
    assert a.t == 25


def test_analyse_is_deterministic():
    for kw in (dict(), dict(kind="textbook"), dict(t=13, side=10), dict(layout="clusters", t=9, blocked=0.4)):
        a, b = ev.analyse(ev.Settings(**kw)), ev.analyse(ev.Settings(**kw))
        assert {k: (s.cost, s.edges) for k, s in a.sols.items()} == {k: (s.cost, s.edges) for k, s in b.sols.items()}


def test_run_config_uses_five_fixed_instances_and_ignores_the_seed():
    a, b = ev.run_config(replace(BASE, seed=1)), ev.run_config(replace(BASE, seed=999))
    assert a["n_runs"] == 5 and a["saving_best"] == b["saving_best"] and a["cost"] == b["cost"]
    assert C.SWEEP_SEEDS == tuple(range(100000, 100005)) and C.FEAS_SEEDS == tuple(range(200000, 200050))


def test_run_config_bands_shares_and_guarantees():
    r = ev.run_config(replace(BASE, t=6))
    for key in ("saving_best", "excess_kmb", "n_branch", "ratio"):
        assert r[f"{key}_lo"] - 1e-9 <= r[key] <= r[f"{key}_hi"] + 1e-9
    for k in ("kmb_optimal_share", "tm_optimal_share", "tmr_optimal_share", "ls_optimal_share", "offered_share"):
        assert 0.0 <= r[k] <= 100.0
    assert r["guarantee_violations"] == 0 and r["ratio_max"] >= r["ratio"] and r["offered_share"] == 100.0
    assert r["gap_kmb_exact"] >= -1e-9 and r["gap_tm_exact"] >= -1e-9 and r["gap_tmr_exact"] >= -1e-9 and r["gap_ls_exact"] >= -1e-9


def test_sweeps_have_one_row_per_value():
    rows = ev.sweep("blocked", replace(BASE, side=5, t=4))
    assert [r["value"] for r in rows] == list(C.BLOCKED_OPTIONS)
    rows = ev.sweep("t", replace(BASE, side=6), values=(3, 5))
    assert [r["value"] for r in rows] == [3, 5]
    assert [r["value"] for r in ev.sweep("layout", replace(BASE, side=6, t=5))] == ["uniform", "clusters"]
    assert ev.SWEEP_TICKS["blocked"](0.2) == "20%" and ev.SWEEP_TICKS["layout"]("clusters") == C.LAYOUT_LABELS["clusters"]


def test_quality_experiment_reports_consistent_shares():
    q = ev.quality(replace(BASE, side=6, t=5), seeds=range(200000, 200012))
    assert q["n_runs"] == 12 and q["exact_used"] and q["guarantee_violations"] == 0
    for k in ("kmb_optimal", "tm_optimal", "tmr_optimal", "ls_optimal", "saves_share", "ls_improves", "tm_beats_kmb", "kmb_beats_tm"):
        assert 0.0 <= q[k] <= 100.0
    assert q["kmb_gap_max"] >= q["kmb_gap_mean"] >= -1e-9 and q["ratio_max"] >= q["ratio_mean"] >= 1.0 - 1e-9 and q["tm_beats_kmb"] + q["kmb_beats_tm"] <= 100.0 + 1e-9


def test_exact_time_curve_counts_states_exactly():
    rows = ev.exact_time_curve(replace(BASE, side=6), ts=[4, 5, 6])
    assert [r["t"] for r in rows] == [4, 5, 6]
    assert [r["states"] for r in rows] == [(2 ** (t - 1) - 1) * 36 for t in (4, 5, 6)]
    assert all(r["seconds"] >= 0 and r["cost"] > 0 for r in rows)
