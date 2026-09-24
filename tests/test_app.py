"""AppTest-Rauchtests: Voreinstellung, jedes Preset, jeder Schritt und jede KMB-Stufe, alle Instanztypen und Bäume, Randwerte, Würfel-Knopf, Permalink-Grenzen, Instanzwechsel, Experimente und Sweeps auf Abruf, Footer."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import stn_constants as C

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _run(step=1, **state):
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in state.items():
        at.session_state[k] = v
    at.run()
    if step != 1:
        at.select_slider(key="stn_step").set_value(step).run()
    return at


def _ok(at):
    assert not at.exception, [e.value for e in at.exception]


def _metric(at, label):
    return next(m for m in at.metric if m.label.startswith(label))


def test_default_run_has_no_exception_and_shows_the_four_metrics():
    at = _run()
    _ok(at)
    assert {"Ersparnis", "Verzweigungen", "KMB", "Takahashi-Matsuyama"} <= {m.label for m in at.metric}
    assert _metric(at, "Ersparnis").value == "5.12 %" and _metric(at, "Verzweigungen").value == "1" and _metric(at, "KMB").value == "optimal" and _metric(at, "Takahashi").value == "optimal"


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_button_runs(name):
    at = _run()
    next(b for b in at.button if b.key == f"preset_{name}").click().run()
    _ok(at)
    p = C.PRESETS[name]
    ss = at.session_state
    assert (ss["kind_select"], ss["side_slider"], ss["t_slider"], ss["blocked_select"], ss["layout_select"], ss["seed_input"], ss["tree_select"]) == (p["kind"], p["side"], p["t"], p["blocked"], p["layout"], p["seed"], p["tree"])
    assert at.metric and at.get("plotly_chart")


@pytest.mark.parametrize("step", [1, 2, 3])
def test_every_step_runs_for_every_kind(step):
    for kind in C.KINDS:
        for t in (4, 14):
            at = _run(kind_select=kind, t_slider=t, side_slider=6, stn_step=step)
            _ok(at)
            assert at.get("plotly_chart") and at.session_state["stn_step"] == step


def test_every_tree_view_runs():
    for tree in C.TREE_OPTIONS:
        at = _run(step=3, tree_select=tree)
        _ok(at)
        assert at.get("plotly_chart") and any("Kosten" in m.value for m in at.markdown)
    at = _run(step=3, tree_select="exact", t_slider=20, side_slider=8)
    _ok(at)
    assert any("nur bis t = 13" in w.value for w in at.warning)


def test_kmb_slider_walks_through_all_steps_including_the_final_one():
    at = _run(step=2)
    _ok(at)
    smax = int(at.slider(key="stn_k").max)
    assert smax == 7
    for k in (0, 3, smax):
        at.slider(key="stn_k").set_value(k).run()
        _ok(at)
        assert any(x.value.startswith(f"**Schritt {k} von {smax}:**") for x in at.markdown)
    assert any("kürzeste Weg" in x.value for x in at.markdown)
    assert any("Ersparnis gegen" in x.value and "Verzweigung(en)" in x.value for x in at.markdown)
    at.session_state["kind_select"] = "textbook"
    at.run()
    _ok(at)
    assert at.session_state["stn_k"] <= int(at.slider(key="stn_k").max) == 4


@pytest.mark.parametrize("kw", [
    dict(side_slider=C.SIDE_MIN, t_slider=C.T_MIN), dict(side_slider=C.SIDE_MAX, t_slider=C.T_MAX), dict(side_slider=C.SIDE_MIN, t_slider=C.T_MAX), dict(blocked_select=C.BLOCKED_OPTIONS[-1]),
    dict(layout_select="clusters", t_slider=13), dict(layout_select="clusters", t_slider=C.T_MAX, side_slider=C.SIDE_MAX, blocked_select=0.4), dict(kind_select="textbook"), dict(t_slider=13, side_slider=10),
])
def test_extreme_settings_run(kw):
    for step in (1, 2, 3):
        _ok(_run(step=step, **kw))


def test_dice_button_changes_the_seed():
    at = _run()
    old = at.session_state["seed_input"]
    next(b for b in at.button if b.label == "🎲 Neue Instanz generieren").click().run()
    _ok(at)
    assert at.session_state["seed_input"] != old


def test_permalink_values_are_clamped_and_invalid_choices_fall_back_to_the_default():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(side="99", t="1", blocked="0.15", layout="ring", tree="nope", kind="nope").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["side_slider"], ss["t_slider"], ss["blocked_select"], ss["layout_select"], ss["tree_select"], ss["kind_select"]) == (C.SIDE_MAX, C.T_MIN, C.DEFAULT_BLOCKED, "uniform", C.DEFAULT_TREE, "city")


def test_permalink_accepts_valid_values():
    at = AppTest.from_file(APP, default_timeout=240)
    for k, v in dict(kind="city", side="10", t="9", blocked="0.3", layout="clusters", seed="7", tree="kmb").items():
        at.query_params[k] = v
    at.run()
    _ok(at)
    ss = at.session_state
    assert (ss["side_slider"], ss["t_slider"], ss["blocked_select"], ss["layout_select"], ss["seed_input"], ss["tree_select"]) == (10, 9, 0.3, "clusters", 7, "kmb")


def test_sidebar_shows_only_the_controls_that_matter():
    plain = _run()
    assert any(w.key == "side_widget" for w in plain.slider) and any(w.key == "t_widget" for w in plain.slider) and any(w.key == "blocked_widget" for w in plain.select_slider)
    assert any(r.key == "layout_widget" for r in plain.radio) and any(n.key == "seed_widget" for n in plain.number_input)
    tb = _run(kind_select="textbook")
    assert not any(w.key == "side_widget" for w in tb.slider) and not any(n.key == "seed_widget" for n in tb.number_input) and not any(r.key == "layout_widget" for r in tb.radio)


def test_changing_the_instance_while_on_step_three_does_not_crash():
    at = _run(step=3, tree_select="exact")
    _ok(at)
    for kw in (dict(kind_select="textbook"), dict(kind_select="city", t_slider=20), dict(t_slider=4, side_slider=5), dict(layout_select="clusters")):
        for k, v in kw.items():
            at.session_state[k] = v
        at.run()
        _ok(at)


def test_large_instance_offers_no_exact_method_but_states_it():
    at = _run(t_slider=20, side_slider=8)
    _ok(at)
    assert any("Kein exaktes Verfahren bei t = 20 > 13" in c.value for c in at.caption)


def test_quality_experiment_runs_on_demand():
    at = _run(t_slider=5, side_slider=6)
    next(b for b in at.button if b.key == "quality_start").click().run()
    _ok(at)
    assert {"Steinerpunkte sparen", "KMB optimal", "TM (Depot) optimal", "Lokalsuche optimal"} <= {m.label for m in at.metric}


def test_time_curve_runs_on_demand():
    at = _run(side_slider=5)
    next(b for b in at.button if b.key == "time_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


@pytest.mark.parametrize("param", ["t", "side", "blocked", "layout"])
@pytest.mark.parametrize("metric", ["saving", "excess", "branches"])
def test_sweeps_run_on_demand_for_every_metric(param, metric):
    at = _run(side_slider=5, t_slider=4, sweep_metric=metric)
    at.selectbox(key="sweep_select").set_value(param).run()
    next(b for b in at.button if b.key == "sweep_start").click().run()
    _ok(at)
    assert at.get("plotly_chart")


def test_the_textbook_has_no_experiments():
    tb = _run(kind_select="textbook")
    assert not any(b.key in ("quality_start", "time_start", "sweep_start") for b in tb.button)


def test_footer_limits_and_literature_are_present():
    at = _run()
    assert any("Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net)" in c.value for c in at.caption)
    assert any("Wo die Annahmen enden" in s.value for s in at.subheader)
    assert any("Takahashi, H., & Matsuyama, A. (1980)" in m.value and "Kou, L., Markowsky, G., & Berman, L. (1981)" in m.value and "Dreyfus, S. E., & Wagner, R. A. (1971)" in m.value for m in at.markdown)
