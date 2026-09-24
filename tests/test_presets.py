"""Presets: gültige Einstellungen, Kennzahl-Bänder über die 5 festen Instanzen, Permalink-Spezifikation."""

import pytest

import stn_constants as C
import stn_evaluation as ev
import stn_presets as P

KEYS = {"kind", "side", "t", "blocked", "layout", "seed", "tree"}


def _settings(p):
    return ev.Settings(p["kind"], p["side"], p["t"], p["blocked"], p["layout"], p["seed"])


def test_presets_have_help_and_full_settings():
    assert len(C.PRESETS) == 8 and set(C.PRESET_HELP) == set(C.PRESETS) and set(C.PRESET_EXPECTED_BANDS) == set(C.PRESETS)
    for name, p in C.PRESETS.items():
        assert set(p) == KEYS, name
        assert p["kind"] in C.KINDS and p["tree"] in C.TREE_OPTIONS and p["layout"] in C.LAYOUTS and p["blocked"] in C.BLOCKED_OPTIONS
        assert C.SIDE_MIN <= p["side"] <= C.SIDE_MAX and C.T_MIN <= p["t"] <= C.T_MAX and p["seed"] <= C.SEED_MAX
        assert len(C.PRESET_HELP[name]) > 40


def test_default_preset_is_the_default_setting():
    assert _settings(C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    for key, state_key in P.PRESET_KEYS.items():
        assert P.SETTING_SPECS[state_key].default == C.PRESETS["Standardfall (Voreinstellung)"][key]


@pytest.mark.parametrize("name", list(C.PRESET_EXPECTED_BANDS))
def test_preset_key_metric_lies_in_its_band(name):
    metric, lo, hi = C.PRESET_EXPECTED_BANDS[name]
    r = ev.run_config(_settings(C.PRESETS[name]))
    assert lo <= r[metric] <= hi, (name, metric, r[metric])


def test_every_preset_analyses():
    for name, p in C.PRESETS.items():
        a = ev.analyse(_settings(p))
        assert a.best.cost > 0 and a.proved, name


def test_setting_specs_cover_all_widget_keys_and_permalink_names_are_unique():
    assert set(P.WIDGET_KEYS) <= set(P.SETTING_SPECS)
    urls = [s.url_param for s in P.SETTING_SPECS.values()]
    assert len(urls) == len(set(urls))
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


@pytest.mark.parametrize("state_key,bad", [("kind_select", "grid"), ("blocked_select", "0.15"), ("layout_select", "ring"), ("tree_select", "nope")])
def test_permalink_casters_reject_invalid_choices(state_key, bad):
    with pytest.raises(ValueError):
        P.SETTING_SPECS[state_key].caster(bad)
    default = P.SETTING_SPECS[state_key].default
    assert P.SETTING_SPECS[state_key].caster(str(default)) == default


def test_permalink_casters_accept_valid_values():
    assert P.SETTING_SPECS["blocked_select"].caster("0.4") == 0.4 and P.SETTING_SPECS["layout_select"].caster("clusters") == "clusters"
    assert P.SETTING_SPECS["side_slider"].lo == C.SIDE_MIN and P.SETTING_SPECS["t_slider"].hi == C.T_MAX
