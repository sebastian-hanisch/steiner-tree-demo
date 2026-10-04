"""Steiner-Baum – Kou-Markowsky-Berman, Takahashi-Matsuyama, Lokalsuche, exakt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Achtes Stück der Spannbaum-Reihe der "Konzepte"-Reihe: bisher durften Kanten nur zwischen den Kunden verlaufen. In einem Leitungsnetz darf man aber an Kreuzungen verzweigen, die selbst kein Kunde sind
(Steinerpunkte) - das kann den Baum kürzer machen. Das Steiner-Baum-Problem in Graphen ist NP-schwer. Gemessen werden die Ersparnis gegenüber dem Spannbaum über die Terminals, die Güte von
Kou-Markowsky-Berman (1981) und Takahashi-Matsuyama (1980) und einer Lokalsuche gegen das exakte Optimum (Dreyfus-Wagner 1971), der Einfluss von Sperrungen und Gruppierung und der Aufwand des exakten Wegs.

Lauffähig mit: streamlit run app.py
"""

from dataclasses import replace

import streamlit as st

import stn_constants as C
from stn_evaluation import SWEEP_LABELS, SWEEP_TICKS, Settings, analyse, exact_time_curve, quality, sweep
from stn_presets import (
    apply_preset,
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    store_from_widget,
    sync_query_params,
)
from stn_visualization import (
    METHOD_LABELS,
    build_instance,
    build_kmb_step,
    build_saving_bars,
    build_sweep,
    build_time_curve,
    build_tree,
)

st.set_page_config(page_title="Steiner-Baum – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _sweep(param, base):
    return sweep(param, base)


@st.cache_data(show_spinner=False)
def _quality(base):
    return quality(base)


@st.cache_data(show_spinner=False)
def _time_curve(base):
    return exact_time_curve(base)


def pct(x):
    return f"{x:+.2f} %"


def num(x):
    return f"{x:.2f}"


st.title("🌿 Steiner-Baum – Verzweigen an Kreuzungen")
st.markdown(
    """
**Achtes Stück der Spannbaum-Reihe.** Bisher verliefen die Kanten nur **zwischen den Kunden**. In einem Leitungsnetz darf man aber an **Kreuzungen verzweigen, die selbst kein Kunde sind** - **Steinerpunkte** -, und das kann den
Baum deutlich kürzer machen. Gegeben ist ein Stadtplan (Kreuzungen und Straßen mit Länge) und eine Menge von **Terminals** (Depot und Kunden); gesucht ist der kürzeste Baum im Plan, der alle Terminals verbindet - mit beliebigen
Zwischenknoten. Das **Steiner-Baum-Problem in Graphen** ist **NP-schwer**; der Spannbaum über die Terminals ist der Sonderfall ohne Steinerpunkte.

Hier wird gemessen, **was Steinerpunkte sparen**, wie gut zwei klassische Heuristiken - **Kou-Markowsky-Berman** (MST im Metrik-Abschluss, Wege expandieren) und **Takahashi-Matsuyama** (der Baum wächst Terminal um Terminal) -
und eine **Lokalsuche über Steinerpunkte** gegen das **exakte Optimum** (Dreyfus-Wagner, nur für wenige Terminals) abschneiden und was Sperrungen und Gruppierung ändern.
"""
)
st.caption(
    "Setzt auf [kruskal-demo](https://github.com/sebastian-hanisch/kruskal-demo) auf (der Spannbaum über die Terminals ist die Basislinie); Kartenkulisse wie in [constrained-mst-demo](https://github.com/sebastian-hanisch/constrained-mst-demo) und "
    "[cmst-demo](https://github.com/sebastian-hanisch/cmst-demo). Nachfolger: [pcst-demo](https://github.com/sebastian-hanisch/pcst-demo) (Prize-Collecting Steiner-Baum), [mst-sensitivity-demo](https://github.com/sebastian-hanisch/mst-sensitivity-demo) (Sensitivität), [random-spanning-tree-demo](https://github.com/sebastian-hanisch/random-spanning-tree-demo) (zufällige Spannbäume)."
)

with st.expander("So funktionieren die Verfahren", expanded=True):
    st.markdown(
        """
1. **Kernsatz:** jeder Steinerbaum ist ein Baum auf den Terminals **plus einer Menge X von Steinerpunkten**; das Optimum ist also der kürzeste Spannbaum des von Terminals + X induzierten Teilplans, über alle X. Die Aufgabe ist, ein gutes X zu finden.
2. **Kou-Markowsky-Berman (KMB):** Abstände zwischen den Terminals im Plan → Spannbaum darüber → jede Kante durch ihren kürzesten Weg im Plan ersetzen → Spannbaum der Vereinigung → Blätter, die keine Terminals sind, abschneiden. Garantie: höchstens 2 (1 − 1/t) x Optimum.
3. **Takahashi-Matsuyama (TM):** der Baum startet an einem Terminal (hier dem Depot); in jedem Schritt wird das dem Baum nächste Terminal über den kürzesten Weg angehängt. Gleiche Garantie. **TM mit der besten Wurzel** probiert jedes Terminal als Start.
4. **Lokalsuche:** vom besseren Start aus einen Steinerpunkt einfügen oder entfernen, wenn der Spannbaum des Teilplans dadurch kürzer wird.
5. **Exakt (Dreyfus-Wagner):** dynamische Programmierung über alle Teilmengen der Terminals, Aufwand etwa 3^t x Kreuzungen - deshalb nur bis 13 Terminals.
        """
    )

if C.PRESETS:
    st.caption("🎯 Schnellstart – ein Beispielszenario laden:")
    preset_names = list(C.PRESETS.keys())
    for row in (preset_names[:4], preset_names[4:]):
        if not row:
            continue
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                st.button(name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}")

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

ss = st.session_state
with st.sidebar:
    st.header("⚙️ Einstellungen")
    kind = st.radio("Instanz", options=list(C.KINDS), format_func=lambda v: C.KIND_LABELS[v], key="kind_select",
                    help="Stadtplan: gestörtes Gitter mit gesperrten Straßen. Lehrbuchbeispiel: vier Terminals im Plus auf 3 x 3, von Hand nachzurechnen.")
    if kind != "textbook":
        side = st.slider("Gittergröße (Kreuzungen je Seite)", *bounds("side_slider"), value=int(ss["side_slider"]), key="side_widget", on_change=store_from_widget, args=("side_slider",),
                         help="Der Plan hat Seite x Seite Kreuzungen; je mehr Kreuzungen, desto mehr mögliche Steinerpunkte.")
        t = st.slider("Terminals t", *bounds("t_slider"), value=int(ss["t_slider"]), key="t_widget", on_change=store_from_widget, args=("t_slider",),
                      help=f"Depot und Kunden. Das exakte Optimum wird bis t = {C.N_EXACT} angeboten; darüber vergleicht die Demo die Heuristiken untereinander.")
        blocked = st.select_slider("Gesperrter Anteil der Straßen", options=list(C.BLOCKED_OPTIONS), value=float(ss["blocked_select"]), key="blocked_widget", on_change=store_from_widget, args=("blocked_select",),
                                   format_func=lambda v: f"{v:.0%}", help="Sperrungen machen direkte Wege umständlicher (der Plan bleibt zusammenhängend).")
        layout = st.radio("Lage der Terminals", options=list(C.LAYOUTS), format_func=lambda v: C.LAYOUT_LABELS[v], key="layout_widget", on_change=store_from_widget, args=("layout_select",),
                          index=list(C.LAYOUTS).index(ss["layout_select"]), help="Gleichverteilt über den Plan oder in 2 bis 3 Gruppen (dann sparen Steinerpunkte kaum).")
        seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), value=int(ss["seed_input"]), key="seed_widget", step=1, on_change=store_from_widget, args=("seed_input",))
        st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    else:
        side, t, blocked, layout, seed = C.DEFAULT_SIDE, C.DEFAULT_T, 0.0, "uniform", C.DEFAULT_SEED

sync_query_params({"kind_select": kind, "side_slider": int(ss["side_slider"]), "t_slider": int(ss["t_slider"]), "blocked_select": float(ss["blocked_select"]), "layout_select": ss["layout_select"],
                   "seed_input": int(ss["seed_input"]), "tree_select": ss["tree_select"]})

settings = Settings(kind, int(side), int(t), float(blocked), layout, int(seed))
with st.spinner("Rechne..."):
    a = _analysis(settings)
inst = a.inst
g = a.g
best = a.best

# --- In Aktion ---------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Der Steinerbaum in Aktion")
STEP_LABELS = {1: "1 · Der Plan", 2: "2 · Kou-Markowsky-Berman", 3: "3 · Der Steinerbaum"}
step = st.select_slider("Schritt", options=list(STEP_LABELS), key="stn_step", format_func=lambda s: STEP_LABELS[s])

if step == 1:
    st.markdown(f"**{inst.n} Kreuzungen**, **{inst.m} befahrbare Straßen**" + (f", {len(inst.blocked_edges)} gesperrt (rot gepunktet)" if inst.blocked_edges else "") +
                f"; **{inst.t} Terminals** (Depot ⭐ und Kunden). Jede andere Kreuzung ist ein möglicher Steinerpunkt. Der Spannbaum über die Terminals (Abstände im Plan) kostet **{num(a.mst_cost)}**.")
    st.plotly_chart(build_instance(inst), width="stretch", key="s1_map")
    st.caption("Blau = Terminal, grün = Depot; graue Linien = Straßen, rot gepunktet = gesperrte Straßen.")
elif step == 2:
    kmb = a.sols["kmb"]
    steps = kmb.detail["steps"]
    smax = len(steps) + 1
    if "stn_k" in ss:
        ss["stn_k"] = min(max(0, int(ss["stn_k"])), smax)
    k = st.slider("Schritt der Heuristik", 0, smax, key="stn_k", help="0 = nur die Terminals; 1 bis t − 1 = je ein Weg des Spannbaums über die Terminals; der letzte Schritt = Spannbaum der Vereinigung, Blätter abgeschnitten.") if smax > 0 else 0
    if k == 0:
        st.markdown(f"**Schritt 0 von {smax}:** die {inst.t} Terminals, noch nichts verbunden.")
    elif k < smax:
        st_ = steps[k - 1]
        st.markdown(f"**Schritt {k} von {smax}:** der Spannbaum über die Terminals verbindet {st_['a']} und {st_['b']} (Abstand im Plan {num(st_['dist'])}); im Plan ist das der **kürzeste Weg über {len(st_['path']) - 1} Straßen**, orange.")
    else:
        st.markdown(f"**Schritt {smax} von {smax}:** Spannbaum der vereinigten Wege, Blätter ohne Terminal abgeschnitten: **Kosten {num(kmb.cost)}**, {num(a.saving('kmb'))} % Ersparnis gegen \"nur Terminals\" ({num(a.mst_cost)}); "
                    f"{a.n_branch('kmb')} Verzweigung(en).")
    st.plotly_chart(build_kmb_step(inst, kmb, k), width="stretch", key=f"s2_map_{k}")
    st.caption("Grün = frühere Wege bzw. der fertige Baum, orange = neuer Weg, Rauten = Steinerknoten (gefüllt: Verzweigung, hohl: nur Durchgang), rot gestrichelt = beim letzten Schritt entfallen.")
else:
    options = list(C.TREE_OPTIONS)
    if ss.get("tree_widget") not in options:
        ss.pop("tree_widget", None)
    cur = ss["tree_select"] if ss["tree_select"] in options else options[0]
    tree_key = st.radio("Baum zeigen", options=options, format_func=lambda v: C.TREE_LABELS[v], key="tree_widget", horizontal=True, index=options.index(cur), on_change=store_from_widget, args=("tree_select",),
                        help="Bester Fund = billigster Baum unter allen Verfahren (bei kleiner Terminalzahl das Optimum). \"Nur Terminals\": der Spannbaum über die Terminals mit den Abständen im Plan, als Luftlinie gezeichnet.")
    name = a.best_name if tree_key == "best" else tree_key
    if tree_key == "terminals":
        st.plotly_chart(build_tree(inst, [], [], a.closure), width="stretch", key="s3_terminals")
        st.markdown(f"**Nur Terminals:** Kosten **{num(a.mst_cost)}** (Summe der Abstände im Plan) - die Basislinie ohne Steinerpunkte; die gestrichelten Linien sind Luftlinien, real folgt jede dem kürzesten Weg im Plan.")
    elif name not in a.sols:
        st.warning(f"{C.TREE_LABELS.get(tree_key, tree_key)}: das exakte Verfahren wird nur bis t = {C.N_EXACT} Terminals angeboten (hier t = {inst.t}).")
        st.plotly_chart(build_tree(inst, best.edges, best.steiner), width="stretch", key="s3_none")
    else:
        sol = a.sols[name]
        st.plotly_chart(build_tree(inst, sol.edges, sol.steiner, a.closure if name == a.best_name else None), width="stretch", key=f"s3_map_{name}")
        st.markdown(f"**{C.TREE_LABELS.get(name, name)}:** Kosten **{num(sol.cost)}**, **{num(a.saving(name))} % Ersparnis** gegen \"nur Terminals\" ({num(a.mst_cost)}); {a.n_branch(name)} Verzweigung(en), "
                    f"{len(sol.steiner)} Steinerknoten insgesamt." + ("" if name == a.best_name else f" {pct(a.excess(name))} über dem besten Fund ({METHOD_LABELS[a.best_name] if a.best_name in METHOD_LABELS else a.best_name})."))
    order = ["terminals"] + [k for k in ("kmb", "tm", "tmr", "ls", "exact") if k in a.sols]
    savings = {"terminals": 0.0, **{k: a.saving(k) for k in a.sols}}
    st.plotly_chart(build_saving_bars(savings, order), width="stretch", key="saving_bars")
    st.caption("Ersparnis gegen die Basislinie \"nur Terminals\". Ein fehlender Balken heißt: das Verfahren wird bei dieser Größe nicht angeboten.")

st.markdown("---")

# --- Kennzahlen --------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ⚙️ Was sparen Steinerpunkte?")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Ersparnis", f"{a.saving(a.best_name):.2f} %", delta=f"Fund: {C.TREE_LABELS.get(a.best_name, a.best_name)}", delta_color="off")
m2.metric("Verzweigungen", str(a.n_branch(a.best_name)), delta=f"{len(best.steiner)} Steinerknoten", delta_color="off")
m3.metric("KMB", "optimal" if a.excess("kmb") <= 1e-9 else pct(a.excess("kmb")), delta="gegen besten Fund", delta_color="off")
m4.metric("Takahashi-Matsuyama", "optimal" if a.excess("tm") <= 1e-9 else pct(a.excess("tm")), delta="Depot als Wurzel", delta_color="off")
ex_txt = f"Exakt bewiesen ({a.states} Zustände): das Optimum ist der beste Fund." if a.proved else f"Kein exaktes Verfahren bei t = {a.t} > {C.N_EXACT}: 'bester Fund' ist die beste Heuristik."
st.caption(f"Ersparnis = 1 − Kosten des besten Baums / Kosten \"nur Terminals\" ({num(a.mst_cost)}). Steiner-Verhältnis (nur Terminals / bester Baum): {a.ratio:.3f}. Garantie von KMB und TM: höchstens {a.bound:.2f} x Optimum "
           f"(gemessen: KMB {a.sols['kmb'].cost / best.cost:.3f}, TM {a.sols['tm'].cost / best.cost:.3f}). TM mit der besten Wurzel: {pct(a.excess('tmr'))}, Lokalsuche: {pct(a.excess('ls'))}. {ex_txt}")

st.markdown("---")

# --- Experimente auf Abruf ---------------------------------------------------------------------------------------------------------------------

base = replace(settings, seed=0)
if kind != "textbook":
    st.subheader("🎲 Wie gut sind die Verfahren?")
    st.caption("50 Instanzen mit den Einstellungen der Seitenleiste (nur der Seed wechselt): wie oft trifft jedes Verfahren den besten Baum, wie groß ist die Lücke, wie oft sparen Steinerpunkte überhaupt?")
    if st.button("Qualitäts-Experiment über 50 Instanzen (dauert einige Sekunden)", key="quality_start"):
        ss["quality_done"] = ss.get("quality_done", set()) | {base}
    if base in ss.get("quality_done", set()):
        with st.spinner("Rechne..."):
            q = _quality(base)
        q1, q2, q3, q4 = st.columns(4)
        q1.metric("Steinerpunkte sparen", f"{q['saves_share']:.0f} %", delta=f"im Mittel {q['saving_mean']:.1f} %", delta_color="off")
        q2.metric("KMB optimal", f"{q['kmb_optimal']:.0f} %", delta=f"mittlere Lücke {q['kmb_gap_mean']:.2f} %", delta_color="off")
        q3.metric("TM (Depot) optimal", f"{q['tm_optimal']:.0f} %", delta=f"mittlere Lücke {q['tm_gap_mean']:.2f} %", delta_color="off")
        q4.metric("Lokalsuche optimal", f"{q['ls_optimal']:.0f} %", delta=f"mittlere Lücke {q['ls_gap_mean']:.2f} %", delta_color="off")
        st.caption(f"Über {q['n_runs']} Instanzen; " + ("Lücken gegen das exakte Optimum. " if q["exact_used"] else "Lücken gegen den besten gefundenen Baum (bei dieser Größe ohne exaktes Verfahren). ")
                   + f"TM mit der besten Wurzel ist in {q['tmr_optimal']:.0f} % optimal (mittlere Lücke {q['tmr_gap_mean']:.2f} %, größte {q['tmr_gap_max']:.1f} %); KMB größte Lücke {q['kmb_gap_max']:.1f} %, TM {q['tm_gap_max']:.1f} %; "
                   f"TM (Depot) schlägt KMB in {q['tm_beats_kmb']:.0f} %, KMB schlägt TM in {q['kmb_beats_tm']:.0f} %; die Lokalsuche verbessert den Start in {q['ls_improves']:.0f} %. Größtes Steiner-Verhältnis {q['ratio_max']:.3f} "
                   f"(Mittel {q['ratio_mean']:.3f}), größte Ersparnis {q['saving_max']:.1f} %, Garantieverletzungen: {q['guarantee_violations']}.")
    st.markdown("---")

    st.subheader("⏱️ Was kostet der exakte Weg?")
    st.caption("Dreyfus-Wagner über die Terminalzahl auf demselben Plan: die Zahl der Zustände (Teilmenge, Kreuzung) wächst mit 2^t, der Rechenaufwand mit 3^t.")
    if st.button("Aufwandskurve berechnen (dauert einige Sekunden)", key="time_start"):
        ss["time_done"] = ss.get("time_done", set()) | {base}
    if base in ss.get("time_done", set()):
        with st.spinner("Rechne..."):
            rows_t = _time_curve(base)
        st.plotly_chart(build_time_curve(rows_t), width="stretch", key="time_curve")
        st.caption("Die Sekunden sind eine Messung auf diesem Rechner und schwanken; die Zustandszahlen sind exakt.")
    st.markdown("---")

    st.subheader("📐 Sweeps")
    sweep_param = st.selectbox("Welcher Regler soll durchgefahren werden?", list(SWEEP_LABELS), format_func=lambda v: SWEEP_LABELS[v], key="sweep_select")
    metric_opts = {"saving": "Ersparnis gegen \"nur Terminals\"", "excess": "Aufschlag der Verfahren", "branches": "Verzweigungen"}
    if ss.get("sweep_metric") not in metric_opts:
        ss.pop("sweep_metric", None)
    metric = st.radio("Kennzahl", options=list(metric_opts), format_func=lambda v: metric_opts[v], key="sweep_metric", horizontal=True)
    if st.button("Sweep über 5 feste Instanzen berechnen (kann einige Sekunden dauern)", key="sweep_start"):
        ss["sweep_done"] = ss.get("sweep_done", set()) | {(sweep_param, base)}
    if (sweep_param, base) in ss.get("sweep_done", set()):
        with st.spinner("Rechne den Sweep über 5 feste Instanzen..."):
            rows_s = _sweep(sweep_param, base)
        series = {
            "saving": ([("saving_best", "bester Fund", "#2F6B65"), ("saving_kmb", "KMB", "#4c78a8"), ("saving_tm", "TM (Depot)", "#7b3fbf")], "Ersparnis gegen \"nur Terminals\" (%)"),
            "excess": ([("excess_kmb", "KMB", "#4c78a8"), ("excess_tm", "TM (Depot)", "#7b3fbf"), ("excess_tmr", "TM (beste Wurzel)", "#d95f9b"), ("excess_ls", "Lokalsuche", "#e8a13a")], "Aufschlag gegen den besten Fund (%)"),
            "branches": ([("n_branch", "Verzweigungen des besten Baums", "#2F6B65"), ("n_steiner", "Steinerknoten insgesamt", "#e8a13a")], "Anzahl"),
        }[metric]
        st.plotly_chart(build_sweep(rows_s, SWEEP_LABELS[sweep_param], series[0], series[1], tick=SWEEP_TICKS.get(sweep_param)), width="stretch", key="sweep_chart")
        st.caption("Median über 5 feste Instanzen (Seeds 100000–100004), Band = 10. bis 90. Perzentil. Der Aufschlag ist gegen den besten gefundenen Baum gemessen - bei bis zu 13 Terminals ist das das exakte Optimum. "
                   "Die übrigen Regler stehen wie in der Seitenleiste.")
    st.markdown("---")

# --- Grenzen -----------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Steinerpunkte sparen viel** | Im Mittel 8,6 % und in 92 % der Instanzen etwas (Plan 8 x 8, 7 Terminals), im Einzelfall bis 20,5 %; in Gruppen sparen sie nur in 50 % der Fälle, im Mittel 2,1 %. | - |
| **KMB reicht** | Er ist bei 7 Terminals nur in 26 % der Instanzen optimal (mittlere Lücke 5,12 %, größte 20,11 %); Takahashi-Matsuyama mit Depot als Wurzel liegt im Mittel bei 3,21 % Lücke, mit der besten Wurzel bei 1,18 %. | Lokalsuche, Reduktionen, Branch-and-Cut (SCIP-Jack, nicht gebaut) |
| **Die Lokalsuche findet das Optimum** | Nein: sie ist bei 7 Terminals in 62 % der Instanzen optimal (größte Lücke 6,18 %); Einfügen und Entfernen einzelner Knoten reicht nicht für jede Umgehung. | Stärkere Nachbarschaften (nicht gebaut) |
| **Exakt lösbar** | Nur bis 13 Terminals (Dreyfus-Wagner, Aufwand etwa 3^t); darüber vergleicht die Demo die Heuristiken nur untereinander. Der Stand der Technik löst Steiner-Bäume mit tausenden Terminals über Reduktionen und Branch-and-Cut. | SCIP-Jack, PACE 2018 (nicht gebaut) |
| **Graph statt freier Ebene** | Steinerpunkte sind hier nur Kreuzungen des Plans; das euklidische Steiner-Problem mit frei wählbaren Punkten ist ein anderes (Verhältnis 2/√3 statt 3/2). | - |
| **Synthetisches Modell** | Gestörtes Gitter, Länge als einzige Kosten, keine Kapazität, keine Steinerpunkt-Kosten. | Echte Netze |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Problem.** Gegeben ein zusammenhängender Graph $G = (V, E)$ mit Längen $c_e > 0$ und Terminals $T \subseteq V$. Gesucht ist ein Baum $S \subseteq E$ minimaler Länge, dessen Knotenmenge $T$ enthält. Für $|T| = |V|$ ist es der
MST, für $|T| = 2$ der kürzeste Weg, dazwischen ist es NP-schwer.

**Kernsatz.** $\mathrm{OPT} = \min_{X \subseteq V \setminus T} \mathrm{MST}\big(G[T \cup X]\big)$: jeder Steinerbaum ist ein Baum auf $T \cup X$ für seine Menge $X$ von Steinerknoten, und der billigste Baum auf einer festen Knotenmenge ist der MST des induzierten Teilgraphen.

**Garantie.** KMB und Takahashi-Matsuyama liefern höchstens $2 (1 - 1/t)$ mal das Optimum; der Spannbaum über den Metrik-Abschluss der Terminals ist höchstens $2$ mal so lang wie der Steinerbaum, im rechtwinkligen Gitter der
Ebene höchstens $3/2$ mal (Hwang 1976).

**Exakt.** Dreyfus-Wagner: $D[S][v]$ = kürzester Baum, der die Terminals in $S$ und den Knoten $v$ verbindet; $D[S][v] = \min_u \big( \min_{A \cup B = S} D[A][u] + D[B][u] \big) + d(u, v)$. Aufwand $O(3^{t} n + 2^{t} n^2)$.

**Literatur.** Takahashi, H., & Matsuyama, A. (1980). *An approximate solution for the Steiner problem in graphs.* Mathematica Japonica 24(6), 573-577. Kou, L., Markowsky, G., & Berman, L. (1981). *A fast algorithm for Steiner trees.*
Acta Informatica 15, 141-145. Dreyfus, S. E., & Wagner, R. A. (1971). *The Steiner problem in graphs.* Networks 1(3), 195-207. Hwang, F. K. (1976). *On Steiner minimal trees with rectilinear distance.* SIAM Journal on Applied Mathematics 30(1),
104-114. Byrka, J., Grandoni, F., Rothvoß, T., & Sanità, L. (2013). *Steiner tree approximation via iterative randomized rounding.* Journal of the ACM 60(1) (nur genannt, nicht gebaut).

Implementiert in `stn_algorithm.py` (Verfahren), `stn_scenario.py` (Pläne), `stn_evaluation.py` (Kennzahlen, Sweeps, Experimente).
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Spannbäume: vom Kruskal bis zum Zufallsbaum](https://sebastianhanisch.net/konzepte-spannbaum.html)."
)
