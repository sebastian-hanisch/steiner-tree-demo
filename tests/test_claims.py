"""Jede Zahl, die App-Text, Preset-Hilfen und README nennen, wird hier über die echten Auswertungsfunktionen (ev.analyse / ev.run_config / ev.sweep / ev.quality / ev.exact_time_curve) und die Verfahren belegt -
nie über ein Ad-hoc-Skript. Kosten sind Gleitkommazahlen, Kennzahlen daher auf Rundungsstellen verglichen; Anteile und Zähler sind ganzzahlig."""

from dataclasses import replace
from functools import lru_cache

import pytest

import stn_algorithm as A
import stn_constants as C
import stn_evaluation as ev
import stn_scenario as S

BASE = ev.Settings(seed=0)


@lru_cache(maxsize=None)
def _ana(**kw):
    return ev.analyse(ev.Settings(**kw))


@lru_cache(maxsize=None)
def _sweep(param, values=None, **kw):
    return ev.sweep(param, replace(BASE, **kw), values=values)


@lru_cache(maxsize=None)
def _quality(**kw):
    return ev.quality(replace(BASE, **kw))


def _col(rows, key, digits=2):
    return [None if r[key] != r[key] else round(r[key], digits) for r in rows]


def r2(x):
    return round(x, 2)


# --- Preset-Hilfen (jeweils die Einzelinstanz des Presets) ------------------------------------------------------------------------------------------


def test_preset_standard_case():
    a = _ana()
    assert a.inst.n == 64 and len(a.inst.blocked_edges) == 11 and a.t == 7
    assert r2(a.mst_cost) == 170.42 and r2(a.best.cost) == 161.69 and r2(a.saving("exact")) == 5.12 and a.n_branch("exact") == 1
    assert all(r2(a.sols[k].cost) == 161.69 for k in ("kmb", "tm", "tmr", "ls", "exact")) and a.best_name == "exact"


def test_preset_textbook_plus():
    a = _ana(kind="textbook")
    assert a.mst_cost == 6.0 and a.sols["exact"].cost == 4.0 and r2(a.saving("exact")) == 33.33 and a.ratio == pytest.approx(1.5)
    assert a.sols["kmb"].cost == 6.0 and a.sols["tm"].cost == 6.0 and a.sols["tmr"].cost == 4.0 and a.sols["ls"].cost == 4.0


def test_preset_kmb_far_above_the_optimum():
    a = _ana(seed=62)
    assert r2(a.sols["kmb"].cost) == 195.87 and r2(a.sols["tm"].cost) == 195.87 and r2(a.mst_cost) == 195.87 and r2(a.sols["exact"].cost) == 165.68
    assert r2(a.excess("kmb")) == 18.22 and r2(a.sols["tmr"].cost) == 167.29 and r2(a.sols["ls"].cost) == 167.29 and r2(a.excess("tmr")) == 0.97


def test_preset_local_search_gets_stuck():
    a = _ana(seed=56)
    assert r2(a.sols["ls"].cost) == 166.75 and r2(a.sols["exact"].cost) == 153.39 and r2(a.excess("ls")) == 8.71 and r2(a.sols["kmb"].cost) == 171.22 and r2(a.excess("kmb")) == 11.62
    assert a.n_branch("exact") == 2 and a.n_branch("ls") == 1


def test_preset_kmb_beats_takahashi_matsuyama():
    a = _ana(seed=53)
    assert r2(a.sols["kmb"].cost) == 161.11 and r2(a.excess("kmb")) == 4.63 and r2(a.sols["tm"].cost) == 176.07 and r2(a.excess("tm")) == 14.35
    assert all(r2(a.sols[k].cost) == 153.98 for k in ("tmr", "ls", "exact"))


def test_preset_many_terminals():
    a = _ana(side=10, t=13)
    assert all(r2(a.sols[k].cost) == 302.76 for k in ("kmb", "tm", "tmr", "ls")) and r2(a.sols["exact"].cost) == 298.29 and r2(a.excess("kmb")) == 1.5
    assert a.n_branch("exact") == 4 and a.n_branch("kmb") == 2 and r2(a.mst_cost) == 320.20 and r2(a.saving("exact")) == 6.84


def test_preset_strong_blocking():
    a = _ana(blocked=0.4)
    assert a.inst.m + len(a.inst.blocked_edges) == 112 and len(a.inst.blocked_edges) == 45
    assert r2(a.mst_cost) == 312.14 and r2(a.best.cost) == 251.72 and r2(a.saving("exact")) == 19.36 and a.n_branch("exact") == 5
    assert all(r2(a.sols[k].cost) == 251.72 for k in ("kmb", "tm", "tmr", "ls"))


def test_preset_grouped_terminals():
    a = _ana(t=9, layout="clusters")
    assert r2(a.mst_cost) == 99.47 and r2(a.best.cost) == 99.47 and r2(a.saving("exact")) == 0.0
    q = _quality(t=9, layout="clusters")
    assert q["saves_share"] == 50.0 and round(q["saving_mean"], 1) == 2.1


# --- Ersparnis --------------------------------------------------------------------------------------------------------------------------------


def test_saving_over_the_terminal_count():
    rows = _sweep("t", values=(3, 4, 5, 7, 9, 11, 13))
    assert [r["value"] for r in rows] == [3, 4, 5, 7, 9, 11, 13]
    assert _col(rows, "saving_best") == [9.37, 14.44, 14.25, 14.28, 5.76, 8.79, 8.36]
    assert _col(rows, "ratio") == [1.10, 1.17, 1.17, 1.17, 1.06, 1.10, 1.09] and _col(rows, "n_branch", 0) == [1.0, 1.0, 2.0, 3.0, 1.0, 3.0, 2.0]
    assert [r["guarantee_violations"] for r in rows] == [0] * 7 and all(r["offered_share"] == 100.0 for r in rows)


def test_larger_instances_have_no_exact_reference_and_save_less():
    rows = _sweep("t", values=(20, 30))
    assert _col(rows, "saving_best") == [5.63, 2.11] and [r["offered_share"] for r in rows] == [0.0, 0.0]
    assert _col(rows, "excess_kmb") == [5.96, 0.96] and _col(rows, "excess_tm") == [0.84, 0.0]


def test_saving_over_the_blocked_share_is_not_monotone():
    rows = _sweep("blocked")
    assert [r["value"] for r in rows] == [0.0, 0.1, 0.2, 0.3, 0.4]
    assert _col(rows, "saving_best") == [6.67, 14.28, 11.37, 15.36, 17.99] and _col(rows, "ratio_max") == [1.13, 1.23, 1.20, 1.28, 1.26]
    assert _col(rows, "n_branch", 0) == [1.0, 3.0, 2.0, 2.0, 2.0] and _col(rows, "n_steiner", 0) == [8.0, 9.0, 10.0, 11.0, 14.0]


def test_saving_over_the_plan_size_is_not_monotone():
    rows = _sweep("side", values=(5, 6, 8, 10, 12, 14))
    assert _col(rows, "saving_best") == [10.93, 1.06, 14.28, 9.65, 8.36, 9.9] and _col(rows, "n_steiner", 0) == [4.0, 7.0, 9.0, 14.0, 15.0, 25.0]


def test_grouped_terminals_save_less_but_only_sometimes():
    rows = _sweep("layout", values=("uniform", "clusters"))
    assert _col(rows, "saving_best") == [14.28, 0.0] and _col(rows, "n_branch", 0) == [3.0, 0.0]
    rows = _sweep("layout", values=("uniform", "clusters"), t=9)
    assert _col(rows, "saving_best") == [5.76, 4.97]


def test_steiner_ratio_bounds():
    worst = 0.0
    for seed in range(300):
        inst = S.generate(4 + seed % 4, 3 + seed % 8, 0.0, "uniform", 400 + seed, jitter=0.0)
        g = A.Graph(inst)
        worst = max(worst, A.terminal_mst_cost(g) / A.dreyfus_wagner(g).solution.cost)
    assert round(worst, 4) == 1.4 and worst <= 1.5
    worst = 0.0
    for seed in range(300):
        inst = S.generate(6, 3 + seed % 8, 0.2, "uniform", 900 + seed, jitter=0.0)
        g = A.Graph(inst)
        worst = max(worst, A.terminal_mst_cost(g) / A.dreyfus_wagner(g).solution.cost)
    assert round(worst, 4) == 1.3636


# --- Güte der Verfahren -----------------------------------------------------------------------------------------------------------------------


def test_heuristic_gaps_over_the_terminal_count():
    rows = _sweep("t", values=(3, 4, 5, 7, 9, 11, 13))
    assert _col(rows, "excess_kmb") == [0.0, 7.58, 10.19, 8.23, 6.11, 6.76, 6.79] and _col(rows, "excess_tm") == [0.0, 6.3, 0.0, 6.3, 0.0, 1.43, 2.93]
    assert _col(rows, "excess_tmr") == [0.0] * 7 and _col(rows, "excess_ls") == [0.0] * 7
    assert [r["kmb_optimal_share"] for r in rows] == [60.0, 0.0, 20.0, 0.0, 40.0, 20.0, 20.0] and [r["tm_optimal_share"] for r in rows] == [80.0, 0.0, 60.0, 0.0, 60.0, 40.0, 20.0]
    assert [r["tmr_optimal_share"] for r in rows] == [80.0, 60.0, 80.0, 60.0, 80.0, 80.0, 60.0] and [r["ls_optimal_share"] for r in rows] == [80.0, 60.0, 80.0, 80.0, 80.0, 80.0, 100.0]


def test_gaps_over_the_blocked_share():
    rows = _sweep("blocked")
    assert _col(rows, "excess_kmb") == [5.4, 8.23, 6.44, 4.25, 3.94] and _col(rows, "excess_tm") == [5.08, 6.3, 5.03, 4.25, 0.0]
    assert _col(rows, "excess_tmr") == [0.0] * 5 and _col(rows, "excess_ls") == [0.0] * 5


def test_the_local_search_gets_stuck_on_larger_plans():
    rows = _sweep("side", values=(5, 6, 8, 10, 12, 14))
    assert _col(rows, "gap_ls_exact") == [0.0, 0.0, 0.0, 2.25, 0.17, 2.33] and _col(rows, "excess_tmr") == [0.0, 0.0, 0.0, 4.06, 0.17, 2.33]
    assert _col(rows, "excess_kmb") == [8.83, 1.07, 8.23, 10.13, 6.27, 8.09] and _col(rows, "excess_tm") == [2.77, 0.03, 6.3, 7.6, 0.17, 7.69]


def test_quality_over_fifty_instances():
    for kw, saves, smean, smax, kmb, tm, tmr, ls, ls_imp, tm_kmb, kmb_tm, kgm, kgx, ratio_max in (
        (dict(t=7), 92.0, 8.61, 20.51, (26.0, 5.12, 20.11), (30.0, 3.21, 15.52), (56.0, 1.18, 6.18), (62.0, 1.08, 6.18), 6.0, 40.0, 10.0, 5.12, 20.11, 1.26),
        (dict(t=11), 98.0, 8.51, 17.91, (2.0, 5.76, 14.35), (16.0, 2.98, 10.73), (36.0, 1.26, 10.73), (50.0, 0.79, 4.37), 22.0, 72.0, 4.0, 5.76, 14.35, 1.22),
        (dict(t=9, blocked=0.3), 100.0, 11.64, 20.22, (20.0, 4.87, 13.97), (40.0, 2.3, 12.49), (64.0, 0.6, 6.64), (76.0, 0.35, 6.0), 16.0, 66.0, 6.0, 4.87, 13.97, 1.25),
        (dict(t=9, layout="clusters"), 50.0, 2.1, 16.42, (58.0, 1.24, 12.85), (76.0, 0.48, 8.86), (94.0, 0.04, 1.03), (96.0, 0.02, 1.03), 2.0, 28.0, 2.0, 1.24, 12.85, 1.2),
    ):
        q = _quality(**kw)
        assert q["n_runs"] == 50 and q["exact_used"] and q["guarantee_violations"] == 0, kw
        assert (q["saves_share"], round(q["saving_mean"], 2), round(q["saving_max"], 2), round(q["ratio_max"], 2)) == (saves, smean, smax, ratio_max), kw
        assert (q["kmb_optimal"], round(q["kmb_gap_mean"], 2), round(q["kmb_gap_max"], 2)) == kmb, kw
        assert (q["tm_optimal"], round(q["tm_gap_mean"], 2), round(q["tm_gap_max"], 2)) == tm, kw
        assert (q["tmr_optimal"], round(q["tmr_gap_mean"], 2), round(q["tmr_gap_max"], 2)) == tmr, kw
        assert (q["ls_optimal"], round(q["ls_gap_mean"], 2), round(q["ls_gap_max"], 2)) == ls, kw
        assert (q["ls_improves"], q["tm_beats_kmb"], q["kmb_beats_tm"]) == (ls_imp, tm_kmb, kmb_tm), kw


def test_the_kmb_and_tm_guarantee_is_never_violated_in_any_sweep():
    for param, values in (("t", (3, 5, 9)), ("blocked", (0.0, 0.4)), ("side", (5, 8)), ("layout", ("uniform", "clusters"))):
        assert all(r["guarantee_violations"] == 0 for r in _sweep(param, values=values))


def test_exact_effort_counts_states_two_to_the_t():
    rows = ev.exact_time_curve(BASE, ts=[4, 8, 12])
    assert [r["states"] for r in rows] == [7 * 64, 127 * 64, 2047 * 64]
