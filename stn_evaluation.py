"""Auswertung: was sparen Steinerpunkte gegenüber dem Spannbaum über die Terminals, und wie gut sind die Verfahren?

Verfahren auf derselben Instanz: die Basislinie "nur Terminals" (MST im Metrik-Abschluss über die Terminals), Kou-Markowsky-Berman (KMB), Takahashi-Matsuyama (TM mit dem Depot = kleinstes Terminal als Wurzel, TMR mit der besten Wurzel), Lokalsuche über Steinerpunkte
(vom besseren Start aus KMB/TM) und - für kleine Terminalzahlen - exakt (Dreyfus-Wagner). Alles ist deterministisch: Kennzahlen laufen über 5 feste Instanzen (Seeds 100000-100004), Median mit 10./90. Perzentil.

- **Ersparnis** (`saving_*`) = 1 - Kosten / Kosten der Basislinie "nur Terminals", in Prozent.
- **Steiner-Verhältnis** (`ratio`) = Basislinie / bester gefundener Baum (bei kleinen Instanzen: exakt); bekannte Schranken: <= 2 in Graphen, <= 3/2 im rechtwinkligen Gitter der Ebene (Hwang 1976).
- **Aufschlag** (`excess_*`) = Kosten des Verfahrens / Kosten des besten gefundenen Baums - 1 in Prozent: die Lücke der Heuristik (bei kleinen Instanzen ist der beste Baum der exakte).
- **Garantie** = 2 (1 - 1/t) x Optimum, gilt für KMB und TM."""

import time
from dataclasses import dataclass, replace
from functools import lru_cache

import numpy as np

import stn_algorithm as A
import stn_constants as C
import stn_scenario as S

INF = float("inf")


@dataclass(frozen=True)
class Settings:
    kind: str = "city"
    side: int = C.DEFAULT_SIDE
    t: int = C.DEFAULT_T
    blocked: float = C.DEFAULT_BLOCKED
    layout: str = "uniform"
    seed: int = C.DEFAULT_SEED


@lru_cache(maxsize=256)
def instance_of(settings):
    if settings.kind == "textbook":
        return S.textbook_instance()
    return S.generate(settings.side, min(settings.t, settings.side * settings.side), settings.blocked, settings.layout, settings.seed)


@dataclass
class Analysis:
    settings: Settings
    inst: object
    g: object                          # Graph
    mst_cost: float                    # Basislinie "nur Terminals"
    closure: list                      # Kanten (a, b, Abstand) des Metrik-Abschluss-MST
    sols: dict                         # Name -> Solution (kmb, tm, ls, exact)
    exact_offered: bool = False
    states: int = 0

    @property
    def t(self):
        return len(self.inst.terminals)

    @property
    def best_name(self):
        return min(self.sols, key=lambda k: (self.sols[k].cost, k))

    @property
    def best(self):
        return self.sols[self.best_name]

    @property
    def proved(self):
        return "exact" in self.sols

    @property
    def bound(self):
        """Garantiefaktor 2 (1 - 1/t)."""
        return 2.0 * (1.0 - 1.0 / self.t) if self.t > 1 else 1.0

    @property
    def ratio(self):
        return self.mst_cost / self.best.cost if self.best.cost > 0 else 1.0

    def saving(self, name):
        s = self.sols.get(name)
        return None if s is None or self.mst_cost <= 0 else 100.0 * (1.0 - s.cost / self.mst_cost)

    def excess(self, name):
        s = self.sols.get(name)
        return None if s is None or self.best.cost <= 0 else 100.0 * (s.cost / self.best.cost - 1.0)

    def n_branch(self, name):
        """Zahl der echten Verzweigungen (Nicht-Terminal-Knoten mit Grad >= 3) im Baum des Verfahrens."""
        return len(A.branch_points(self.sols[name].edges, self.inst.terminals))

    def steiner_degrees(self, name):
        s = self.sols[name]
        deg = {}
        for u, v in s.edges:
            deg[u] = deg.get(u, 0) + 1
            deg[v] = deg.get(v, 0) + 1
        return [deg[x] for x in s.steiner]


def exact_offered(inst):
    return inst.t <= C.N_EXACT


def analyse(settings):
    inst = instance_of(settings)
    g = A.Graph(inst)
    closure = A.closure_mst(g)
    mst_cost = sum(d for _a, _b, d in closure)
    kmb = A.kmb(g)
    tm = A.takahashi_matsuyama(g)
    tmr = A.best_takahashi_matsuyama(g)
    start = min((kmb, tm, tmr), key=lambda x: x.cost)
    sols = {"kmb": kmb, "tm": tm, "tmr": tmr, "ls": A.local_search(g, start.steiner)}
    a = Analysis(settings, inst, g, mst_cost, closure, sols, exact_offered=exact_offered(inst))
    if a.exact_offered:
        ex = A.dreyfus_wagner(g)
        sols["exact"] = ex.solution
        a.states = ex.states
    return a


# --- Kennzahlen über feste Instanzen ------------------------------------------------------------------------------------------------------------


def _stats(values):
    values = [v for v in values if v is not None and not np.isnan(v) and v != INF]
    if not values:
        return float("nan"), float("nan"), float("nan")
    return float(np.median(values)), float(np.percentile(values, 10)), float(np.percentile(values, 90))


def run_config(base, seeds=C.SWEEP_SEEDS, **changes):
    s0 = replace(base, **changes)
    rows = [analyse(replace(s0, seed=seed)) for seed in seeds]
    out = {"n_runs": len(rows), "offered_share": 100.0 * sum(r.exact_offered for r in rows) / len(rows), "ratio_max": float(max(r.ratio for r in rows)),
           "guarantee_violations": sum(1 for r in rows for k in ("kmb", "tm", "tmr") if r.sols[k].cost > r.bound * r.best.cost + 1e-9)}
    for nm in ("kmb", "tm", "tmr", "ls"):
        out[f"{nm}_optimal_share"] = 100.0 * sum(1 for r in rows if r.excess(nm) <= 1e-9) / len(rows)
    cols = [("cost", [r.best.cost for r in rows]), ("mst_cost", [r.mst_cost for r in rows]), ("ratio", [r.ratio for r in rows]),
            ("saving_best", [100.0 * (1.0 - r.best.cost / r.mst_cost) if r.mst_cost > 0 else 0.0 for r in rows]),
            ("n_steiner", [float(len(r.best.steiner)) for r in rows]), ("n_branch", [float(r.n_branch(r.best_name)) for r in rows]), ("n_edges", [float(len(r.best.edges)) for r in rows]), ("m", [float(r.inst.m) for r in rows])]
    for nm in ("kmb", "tm", "tmr", "ls"):
        cols.append((f"excess_{nm}", [r.excess(nm) for r in rows]))
        cols.append((f"saving_{nm}", [r.saving(nm) for r in rows]))
    for nm in ("kmb", "tm", "tmr", "ls"):
        cols.append((f"gap_{nm}_exact", [100.0 * (r.sols[nm].cost / r.sols["exact"].cost - 1.0) if r.proved else None for r in rows]))
    for key, values in cols:
        out[key], out[f"{key}_lo"], out[f"{key}_hi"] = _stats(values)
    return out


SWEEP_VALUES = {"t": (3, 5, 7, 9, 11, 13, 20, 30), "side": (5, 6, 8, 10, 12, 14), "blocked": C.BLOCKED_OPTIONS, "layout": C.LAYOUTS}
SWEEP_LABELS = {"t": "Terminals t", "side": "Gittergröße", "blocked": "Gesperrter Anteil", "layout": "Lage der Terminals"}
SWEEP_TICKS = {"blocked": lambda v: f"{v:.0%}", "layout": lambda v: C.LAYOUT_LABELS[v]}


def sweep(param, base=Settings(), values=None):
    values = SWEEP_VALUES[param] if values is None else values
    return [{"value": v, **run_config(base, **{param: v})} for v in values]


def quality(base, seeds=C.FEAS_SEEDS):
    """Wie gut sind die Verfahren? Über `seeds` Instanzen mit den Einstellungen von `base` (nur der Seed wechselt): Anteil, in dem KMB, TM, TMR und die Lokalsuche den besten Baum treffen, mittlere und größte Lücke,
    größtes und mittleres Steiner-Verhältnis, Anteil der Instanzen, in denen Steinerpunkte etwas sparen, Garantieverletzungen (müssen 0 sein)."""
    an = [analyse(replace(base, seed=seed)) for seed in seeds]
    m = len(an)
    out = {"n_runs": m, "exact_used": all(a.proved for a in an), "ratio_max": float(max(a.ratio for a in an)), "ratio_mean": float(np.mean([a.ratio for a in an])),
           "saves_share": 100.0 * sum(a.mst_cost > a.best.cost + 1e-9 for a in an) / m, "saving_mean": float(np.mean([a.saving(a.best_name) for a in an])),
           "saving_max": float(max(a.saving(a.best_name) for a in an)), "guarantee_violations": sum(1 for a in an for k in ("kmb", "tm", "tmr") if a.sols[k].cost > a.bound * a.best.cost + 1e-9)}
    for nm in ("kmb", "tm", "tmr", "ls"):
        ex = [a.excess(nm) for a in an]
        out[f"{nm}_optimal"] = 100.0 * sum(e <= 1e-9 for e in ex) / m
        out[f"{nm}_gap_mean"] = float(np.mean(ex))
        out[f"{nm}_gap_max"] = float(max(ex))
    out["ls_improves"] = 100.0 * sum(a.sols["ls"].cost < min(a.sols["kmb"].cost, a.sols["tm"].cost, a.sols["tmr"].cost) - 1e-9 for a in an) / m
    out["tm_beats_kmb"] = 100.0 * sum(a.sols["tm"].cost < a.sols["kmb"].cost - 1e-9 for a in an) / m
    out["kmb_beats_tm"] = 100.0 * sum(a.sols["kmb"].cost < a.sols["tm"].cost - 1e-9 for a in an) / m
    return out


def exact_time_curve(base, ts=None):
    """Aufwand des exakten Wegs über die Terminalzahl (gleicher Plan, Seed und Einstellungen von `base`): Zustände (Teilmenge, Knoten) und gemessene Sekunden. Die Sekunden sind eine Messung (Rechner-abhängig)."""
    ts = ts if ts is not None else list(range(4, C.N_EXACT + 1))
    rows = []
    for t in ts:
        inst = instance_of(replace(base, t=t))
        g = A.Graph(inst)
        t0 = time.perf_counter()
        ex = A.dreyfus_wagner(g)
        rows.append({"t": t, "states": ex.states, "seconds": time.perf_counter() - t0, "cost": ex.solution.cost})
    return rows
