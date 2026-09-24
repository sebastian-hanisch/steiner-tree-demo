"""Die Instanz dieser Demo: ein Stadtplan als gestörtes Gitter. Kreuzungen sind die Knoten, Straßen zwischen Nachbarn die Kanten (Länge = euklidischer Abstand der leicht verschobenen Kreuzungen);
ein Anteil der Straßen ist gesperrt (der Plan bleibt zusammenhängend). **Terminals** sind die Kreuzungen, die angeschlossen werden müssen (Depot und Kunden); jede andere Kreuzung ist ein
möglicher **Steinerpunkt**, an dem sich das Kabel verzweigen darf. Layouts der Terminals: gleichverteilt oder in Gruppen um wenige Mittelpunkte. Ein handgebautes Lehrbuchbeispiel (Plus auf 3 x 3).

Knoten sind von 0 bis n - 1 durchnummeriert (Zeile für Zeile); Kanten (u, v, w) mit u < v, sortiert."""

from dataclasses import dataclass

import numpy as np

import stn_constants as C
from stn_unionfind import UnionFind


@dataclass(frozen=True)
class Instance:
    xy: np.ndarray                 # (n, 2)
    edges: tuple                   # ((u, v, w), ...) sortiert
    terminals: tuple               # sortierte Knotennummern
    side: int
    kind: str = "city"
    layout: str = "uniform"
    blocked: float = 0.0
    seed: int = 0
    blocked_edges: tuple = ()      # gesperrte Straßen (u, v), nur zur Anzeige

    @property
    def n(self):
        return len(self.xy)

    @property
    def m(self):
        return len(self.edges)

    @property
    def t(self):
        return len(self.terminals)

    @property
    def steiner_candidates(self):
        ts = set(self.terminals)
        return tuple(v for v in range(self.n) if v not in ts)


def _grid_edges(side):
    out = []
    for r in range(side):
        for c in range(side):
            v = r * side + c
            if c + 1 < side:
                out.append((v, v + 1))
            if r + 1 < side:
                out.append((v, v + side))
    return out


def _connected(n, pairs):
    uf = UnionFind(n, "full")
    for u, v in pairs:
        uf.union(u, v)
    return uf.components == 1


def _block(n, pairs, share, rng):
    """Sperrt `share` der Straßen in zufälliger Reihenfolge, überspringt eine Sperrung, wenn der Plan sonst zerfiele. Gibt (verbleibende, gesperrte) zurück."""
    target = int(round(share * len(pairs)))
    order = [int(i) for i in rng.permutation(len(pairs))]
    kept = set(range(len(pairs)))
    removed = []
    for i in order:
        if len(removed) >= target:
            break
        trial = [pairs[j] for j in kept if j != i]
        if _connected(n, trial):
            kept.discard(i)
            removed.append(i)
    return [pairs[j] for j in sorted(kept)], [pairs[j] for j in sorted(removed)]


def _pick_terminals(side, t, layout, rng):
    n = side * side
    if layout == "uniform":
        return sorted(int(x) for x in rng.choice(n, size=t, replace=False))
    k = 3 if t >= 6 else 2
    centers = rng.choice(n, size=k, replace=False)
    cxy = np.array([[c % side, c // side] for c in centers], dtype=float)
    pts = np.array([[v % side, v // side] for v in range(n)], dtype=float)
    chosen = []
    taken = set()
    for i in range(t):
        g = i % k
        d = np.hypot(pts[:, 0] - cxy[g, 0], pts[:, 1] - cxy[g, 1]) + rng.uniform(0.0, 0.01, size=n)
        for v in np.argsort(d, kind="stable"):
            if int(v) not in taken:
                taken.add(int(v))
                chosen.append(int(v))
                break
    return sorted(chosen)


def generate(side=C.DEFAULT_SIDE, t=C.DEFAULT_T, blocked=C.DEFAULT_BLOCKED, layout="uniform", seed=C.DEFAULT_SEED, jitter=C.JITTER):
    if layout not in C.LAYOUTS:
        raise ValueError(f"unbekanntes Layout {layout}")
    side, t = int(side), int(t)
    n = side * side
    if not 1 <= t <= n:
        raise ValueError("Terminalzahl außerhalb")
    rng = np.random.default_rng([int(seed), 4242])
    xy = np.array([[c * C.SPACING, r * C.SPACING] for r in range(side) for c in range(side)], dtype=float)
    xy = xy + rng.uniform(-jitter, jitter, size=xy.shape) * C.SPACING
    kept, removed = _block(n, _grid_edges(side), float(blocked), rng)
    edges = tuple((u, v, float(np.hypot(*(xy[u] - xy[v])))) for u, v in kept)
    terminals = tuple(_pick_terminals(side, t, layout, rng))
    return Instance(xy, edges, terminals, side, "city", layout, float(blocked), int(seed), tuple(removed))


# --- Handgebautes Lehrbuchbeispiel ----------------------------------------------------------------------------------------------------------------


def textbook_instance():
    """Plus auf dem 3 x 3-Gitter (Kantenlänge 1, keine Sperren): Terminals W (Knoten 3), E (5), S (1) und N (7) um die Mitte (Knoten 4). Der Steinerpunkt in der Mitte verbindet alle vier mit Kosten 4; der
    Spannbaum über die Terminals kostet 6 (Verhältnis 3/2, das rechtwinklige Maximum)."""
    xy = np.array([[c, r] for r in range(3) for c in range(3)], dtype=float)
    edges = tuple((u, v, 1.0) for u, v in _grid_edges(3))
    return Instance(xy, edges, (1, 3, 5, 7), 3, "textbook")
