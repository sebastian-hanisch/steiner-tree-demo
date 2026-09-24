"""Plotly-Abbildungen: Stadtplan mit Terminals und gesperrten Straßen, Steinerbaum (Steinerpunkte als Rauten), Kou-Markowsky-Berman Schritt für Schritt, Ersparnis-Balken, Aufwandskurve, Sweeps.
Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht zoomen."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from stn_algorithm import branch_points

TREE_COLOR = "#2F6B65"
STEINER_COLOR = "#ff7f0e"
TERMINAL_COLOR = "#4c78a8"
ROOT_COLOR = "#2ca02c"
BLOCKED_COLOR = "rgba(214,39,40,0.35)"
STREET_COLOR = "rgba(150,150,150,0.35)"
METHOD_COLORS = {"kmb": "#4c78a8", "tm": "#7b3fbf", "tmr": "#d95f9b", "ls": "#e8a13a", "exact": "#2F6B65", "terminals": "#8c8c8c"}
METHOD_LABELS = {"terminals": "nur Terminals", "kmb": "Kou-Markowsky-Berman", "tm": "Takahashi-Matsuyama (Depot)", "tmr": "Takahashi-Matsuyama (beste Wurzel)", "ls": "Lokalsuche", "exact": "Exakt (Dreyfus-Wagner)"}


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height, legend_y=-0.1):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=legend_y), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _map_axes(fig, height=460):
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, autorange="reversed")
    return _base(fig, height)


def _height(inst):
    return 340 if inst.kind == "textbook" else 480


def _lines(fig, inst, pairs, color, width=2.6, dash="solid", name="", showlegend=False):
    pairs = list(pairs)
    if not pairs:
        return
    xs, ys = [], []
    for u, v in pairs:
        xs += [inst.xy[u][0], inst.xy[v][0], None]
        ys += [inst.xy[u][1], inst.xy[v][1], None]
    fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=width, dash=dash), name=name, hoverinfo="skip", showlegend=showlegend))


def _streets(fig, inst, blocked=True):
    _lines(fig, inst, [(u, v) for u, v, _w in inst.edges], STREET_COLOR, 1.0)
    if blocked:
        _lines(fig, inst, inst.blocked_edges, BLOCKED_COLOR, 1.2, "dot", "gesperrt", bool(inst.blocked_edges))


def _terminals(fig, inst, root=True):
    ts = list(inst.terminals)
    rest = ts[1:] if root else ts
    fig.add_trace(go.Scatter(x=[inst.xy[v][0] for v in rest], y=[inst.xy[v][1] for v in rest], mode="markers", marker=dict(size=13, color=TERMINAL_COLOR, line=dict(width=1.5, color="white")),
                             name="Terminal", hoverinfo="skip", showlegend=True))
    if root:
        fig.add_trace(go.Scatter(x=[inst.xy[ts[0]][0]], y=[inst.xy[ts[0]][1]], mode="markers", marker=dict(size=18, symbol="star", color=ROOT_COLOR, line=dict(width=1, color="white")),
                                 name="Depot", hoverinfo="skip", showlegend=True))


def _steiner(fig, inst, nodes, branch=None):
    """Steinerpunkte: Rauten; Verzweigungspunkte (Grad >= 3) orange gefüllt, Durchgangsknoten (Grad 2) hohl."""
    nodes = list(nodes)
    if not nodes:
        return
    branch = set(branch) if branch is not None else set(nodes)
    b = [v for v in nodes if v in branch]
    p = [v for v in nodes if v not in branch]
    if b:
        fig.add_trace(go.Scatter(x=[inst.xy[v][0] for v in b], y=[inst.xy[v][1] for v in b], mode="markers", marker=dict(size=13, symbol="diamond", color=STEINER_COLOR, line=dict(width=1.5, color="white")),
                                 name="Verzweigung (Steinerpunkt)", hoverinfo="skip", showlegend=True))
    if p:
        fig.add_trace(go.Scatter(x=[inst.xy[v][0] for v in p], y=[inst.xy[v][1] for v in p], mode="markers", marker=dict(size=8, symbol="diamond-open", color=STEINER_COLOR, line=dict(width=1.5)),
                                 name="Durchgang", hoverinfo="skip", showlegend=True))


def build_instance(inst):
    fig = go.Figure()
    _streets(fig, inst)
    _terminals(fig, inst)
    return _map_axes(fig, _height(inst))


def build_tree(inst, edges, steiner, closure=None):
    """Der Baum in Grün; Steinerpunkte als Rauten. Optional der Spannbaum über die Terminals (Metrik-Abschluss) als gerade graue Linien im Vergleich."""
    fig = go.Figure()
    _streets(fig, inst, blocked=False)
    if closure:
        _lines(fig, inst, [(a, b) for a, b, *_ in closure], "rgba(120,120,120,0.55)", 1.6, "dash", "nur Terminals (Luftlinie)", True)
    _lines(fig, inst, edges, TREE_COLOR, 3.6, name="Baum", showlegend=True)
    _steiner(fig, inst, steiner, branch_points(edges, inst.terminals))
    _terminals(fig, inst)
    return _map_axes(fig, _height(inst))


def build_kmb_step(inst, sol, k):
    """Kou-Markowsky-Berman nach `k` Schritten: 1..s Abschlusskanten als kürzeste Wege (der zuletzt hinzugekommene orange, frühere grün), Schritt s + 1 der Baum nach MST und Beschneiden
    (die dabei entfallenen Kanten rot gestrichelt)."""
    steps = sol.detail["steps"]
    s = len(steps)
    fig = go.Figure()
    _streets(fig, inst, blocked=False)
    if k <= s:
        done = []
        for st in steps[: max(0, k - 1)]:
            done += list(zip(st["path"], st["path"][1:]))
        _lines(fig, inst, [(min(a, b), max(a, b)) for a, b in done], TREE_COLOR, 3.2, name="frühere Wege", showlegend=bool(done))
        if k >= 1:
            p = steps[k - 1]["path"]
            _lines(fig, inst, [(min(a, b), max(a, b)) for a, b in zip(p, p[1:])], STEINER_COLOR, 5.0, name="neuer Weg", showlegend=True)
        nodes = {x for st in steps[:k] for x in st["path"]}
        _steiner(fig, inst, sorted(nodes - set(inst.terminals)), None)
    else:
        removed = [e for e in sol.detail["expanded"] if e not in set(sol.edges)]
        _lines(fig, inst, removed, "rgba(214,39,40,0.8)", 2.4, "dash", "entfallen (MST/Beschneiden)", bool(removed))
        _lines(fig, inst, sol.edges, TREE_COLOR, 3.6, name="Baum", showlegend=True)
        _steiner(fig, inst, sol.steiner, branch_points(sol.edges, inst.terminals))
    _terminals(fig, inst)
    return _map_axes(fig, _height(inst))


def build_saving_bars(savings, order):
    """Ersparnis je Verfahren gegen die Basislinie "nur Terminals" (%)."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[METHOD_LABELS[k] for k in order], y=[savings[k] for k in order], marker_color=[METHOD_COLORS[k] for k in order], text=[f"{savings[k]:.2f} %" for k in order], textposition="outside"))
    fig.update_yaxes(title_text="Ersparnis gegen \"nur Terminals\" (%)", rangemode="tozero")
    return _base(fig, 320)


def build_time_curve(rows):
    """Aufwand des exakten Wegs über die Terminalzahl: Zustände (Balken) und gemessene Sekunden (Linie), beides logarithmisch."""
    xs = [str(r["t"]) for r in rows]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Bar(x=xs, y=[r["states"] for r in rows], marker_color="rgba(76,120,168,0.25)", name="Zustände"), secondary_y=False)
    fig.add_trace(go.Scatter(x=xs, y=[max(r["seconds"], 1e-4) for r in rows], mode="lines+markers", line=dict(color="#d62728", width=2.6), name="Sekunden (gemessen)"), secondary_y=True)
    fig.update_xaxes(title_text="Terminals t", type="category")
    fig.update_yaxes(title_text="Zustände (Teilmenge, Knoten)", type="log", secondary_y=False)
    fig.update_yaxes(title_text="Sekunden", type="log", secondary_y=True, showgrid=False)
    return _base(fig, 340, legend_y=-0.3)


def build_sweep(rows, param_label, series, y_label, tick=None, log_y=False):
    """`series` = [(key, Name, Farbe)]: Median als Linie, 10. bis 90. Perzentil als Band (`<key>_lo`/`<key>_hi`)."""
    xs = [tick(r["value"]) if tick else str(r["value"]) for r in rows]
    fig = go.Figure()
    for key, name, color in series:
        ys = [None if r[key] != r[key] else r[key] for r in rows]
        lo = [None if r.get(f"{key}_lo", r[key]) != r.get(f"{key}_lo", r[key]) else r.get(f"{key}_lo", r[key]) for r in rows]
        hi = [None if r.get(f"{key}_hi", r[key]) != r.get(f"{key}_hi", r[key]) else r.get(f"{key}_hi", r[key]) for r in rows]
        rgb = tuple(int(color[i:i + 2], 16) for i in (1, 3, 5))
        if all(v is not None for v in lo + hi):
            fig.add_trace(go.Scatter(x=xs + xs[::-1], y=hi + lo[::-1], mode="lines", fill="toself", fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},0.13)", line=dict(width=0), showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines+markers", line=dict(color=color, width=2.5), name=name, connectgaps=False))
    fig.update_xaxes(title_text=param_label, type="category")
    fig.update_yaxes(title_text=y_label, type="log" if log_y else "linear")
    return _base(fig, 360, legend_y=-0.3)
