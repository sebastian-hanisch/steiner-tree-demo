"""Steiner-Baum in Graphen (STP): gegeben ein Graph mit Kantenlängen und eine Menge von Terminals, gesucht der kürzeste Baum, der alle Terminals verbindet - Zwischenknoten (**Steinerpunkte**) sind frei wählbar.
NP-schwer; der Spannbaum über die Terminals ist der Sonderfall "keine Steinerpunkte".

**Kernsatz:** jeder Steinerbaum ist ein Baum auf T + X für eine Menge X von Steinerpunkten, also ist OPT = min über X von MST(G[T + X]) (MST des von T + X induzierten Teilgraphen).

Verfahren: **Kou-Markowsky-Berman** (`kmb`, 1981: MST im Metrik-Abschluss über die Terminals, Kanten zu kürzesten Wegen expandieren, MST des Teilgraphen, Nicht-Terminal-Blätter beschneiden; Güte <= 2(1 - 1/t)),
**Takahashi-Matsuyama** (`takahashi_matsuyama`, 1980: der Baum wächst, jeweils das nächste Terminal über den kürzesten Weg; ebenfalls <= 2(1 - 1/t)), eine **Lokalsuche** über Steinerpunkte (`local_search`: einen
Knoten einfügen oder entfernen, bewertet mit dem MST des induzierten Teilgraphen) und **exakt** nach Dreyfus-Wagner (`dreyfus_wagner`, 1971: dynamische Programmierung über Teilmengen der Terminals, O(3^t * n)).
Alle deterministisch (Schlüssel: Länge, dann Knotennummern)."""

import math
from dataclasses import dataclass, field

import numpy as np

from stn_unionfind import UnionFind

EPS = 1e-9


class Graph:
    """Der Stadtplan als Graph: Kantenlängen, Nachbarlisten, Abstände und Nachfolger aller Knotenpaare (Floyd-Warshall, numpy)."""

    def __init__(self, inst):
        self.n = inst.n
        self.terminals = tuple(inst.terminals)
        self.w = {(u, v): float(w) for u, v, w in inst.edges}
        self.edges = sorted(self.w)
        self.adj = [[] for _ in range(self.n)]
        for (u, v), w in self.w.items():
            self.adj[u].append(v)
            self.adj[v].append(u)
        for a in self.adj:
            a.sort()
        self.dist, self.nxt = all_pairs(self.n, self.w)

    def path(self, u, v):
        """Knotenfolge eines kürzesten Wegs u -> v."""
        out = [u]
        while u != v:
            u = int(self.nxt[u, v])
            out.append(u)
        return out

    def path_edges(self, u, v):
        p = self.path(u, v)
        return [(min(a, b), max(a, b)) for a, b in zip(p, p[1:])]

    def cost(self, edges):
        return math.fsum(self.w[e] for e in edges)


def all_pairs(n, w):
    """Abstände und Nachfolger-Matrix aller Knotenpaare (Floyd-Warshall); `w` = {(u, v): Länge} mit u < v. nxt[i, j] = erster Knoten auf dem kürzesten Weg i -> j (-1: unerreichbar)."""
    dist = np.full((n, n), np.inf)
    nxt = np.full((n, n), -1, dtype=int)
    np.fill_diagonal(dist, 0.0)
    for i in range(n):
        nxt[i, i] = i
    for (u, v), x in w.items():
        if x < dist[u, v]:
            dist[u, v] = dist[v, u] = x
            nxt[u, v], nxt[v, u] = v, u
    for k in range(n):
        via = dist[:, k:k + 1] + dist[k:k + 1, :]
        better = via < dist - 1e-12
        if better.any():
            dist = np.where(better, via, dist)
            nxt = np.where(better, nxt[:, k:k + 1], nxt)
    return dist, nxt


@dataclass
class Solution:
    method: str
    edges: list                                    # (u, v) mit u < v
    cost: float
    steiner: list                                  # Steinerpunkte (Knoten des Baums, die keine Terminals sind)
    detail: dict = field(default_factory=dict)


def make_solution(method, g, edges, detail=None):
    edges = sorted({(min(u, v), max(u, v)) for u, v in edges})
    nodes = {x for e in edges for x in e}
    ts = set(g.terminals)
    return Solution(method, edges, g.cost(edges), sorted(nodes - ts), dict(detail or {}))


def kruskal_edges(g, edge_list):
    """Kruskal auf den gegebenen Kanten (Schlüssel (Länge, u, v)); gibt den aufspannenden Wald zurück."""
    uf = UnionFind(g.n, "full")
    return [e for e in sorted(edge_list, key=lambda e: (g.w[e], e)) if uf.union(e[0], e[1])]


def prune(g, edges):
    """Nicht-Terminal-Blätter wiederholt entfernen."""
    edges = set(edges)
    ts = set(g.terminals)
    while True:
        deg = {}
        for u, v in edges:
            deg[u] = deg.get(u, 0) + 1
            deg[v] = deg.get(v, 0) + 1
        leaves = {x for x, d in deg.items() if d == 1 and x not in ts}
        if not leaves:
            return sorted(edges)
        edges = {e for e in edges if e[0] not in leaves and e[1] not in leaves}


def is_steiner_tree(g, edges):
    """Alle Kanten aus G, azyklisch, zusammenhängend, alle Terminals enthalten (für ein Terminal: leerer Baum)."""
    edges = list(edges)
    if len(set(edges)) != len(edges) or any(e not in g.w for e in edges):
        return False
    nodes = {x for e in edges for x in e} | set(g.terminals)
    if len(g.terminals) == 1 and not edges:
        return True
    if not set(g.terminals) <= {x for e in edges for x in e}:
        return False
    uf = UnionFind(g.n, "full")
    if not all(uf.union(u, v) for u, v in edges):
        return False
    return len({uf.find(x) for x in nodes}) == 1


def branch_points(edges, terminals):
    """Nicht-Terminal-Knoten mit Grad >= 3 im Baum: die echten Verzweigungen (Steinerpunkte im engeren Sinn); Steinerknoten mit Grad 2 sind nur Durchgang."""
    deg = {}
    for u, v in edges:
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    ts = set(terminals)
    return sorted(x for x, d in deg.items() if d >= 3 and x not in ts)


def leaves_are_terminals(g, edges):
    deg = {}
    for u, v in edges:
        deg[u] = deg.get(u, 0) + 1
        deg[v] = deg.get(v, 0) + 1
    ts = set(g.terminals)
    return all(x in ts for x, d in deg.items() if d == 1)


# --- Baseline: Spannbaum über die Terminals im Metrik-Abschluss -----------------------------------------------------------------------------------


def closure_mst(g):
    """MST über die Terminals mit den Abständen des Graphen (Metrik-Abschluss): Kanten (a, b, Abstand). Ohne Steinerpunkt-Optimierung - die Basislinie "nur Terminals"."""
    T = g.terminals
    pairs = sorted((float(g.dist[a, b]), a, b) for i, a in enumerate(T) for b in T[i + 1:])
    uf = UnionFind(g.n, "full")
    return [(a, b, d) for d, a, b in pairs if uf.union(a, b)]


def terminal_mst_cost(g):
    return math.fsum(d for _a, _b, d in closure_mst(g))


# --- Kou-Markowsky-Berman -------------------------------------------------------------------------------------------------------------------------


def kmb(g):
    """Kou-Markowsky-Berman. `detail['steps']`: je Abschlusskante (a, b, Abstand, Pfad); `detail['expanded']`: Kanten der Vereinigung der Pfade; `detail['closure']`: die Abschlusskanten."""
    T = g.terminals
    if len(T) <= 1:
        return make_solution("kmb", g, [], {"steps": [], "expanded": [], "closure": []})
    closure = closure_mst(g)
    steps, expanded = [], set()
    for a, b, d in closure:
        p = g.path(a, b)
        steps.append({"a": a, "b": b, "dist": d, "path": p})
        expanded.update((min(x, y), max(x, y)) for x, y in zip(p, p[1:]))
    tree = prune(g, kruskal_edges(g, expanded))
    return make_solution("kmb", g, tree, {"steps": steps, "expanded": sorted(expanded), "closure": [(a, b) for a, b, _d in closure]})


# --- Takahashi-Matsuyama --------------------------------------------------------------------------------------------------------------------------


def takahashi_matsuyama(g, root=None):
    """Der Baum wächst von `root` (Standard: kleinstes Terminal); in jedem Schritt wird das dem Baum nächste Terminal über den kürzesten Weg angeschlossen (Gleichstand: kleinster Abstand, dann
    kleinstes Terminal, dann kleinster Baumknoten). `detail['order']`: Reihenfolge der angeschlossenen Terminals."""
    T = list(g.terminals)
    root = T[0] if root is None else root
    if root not in T:
        raise ValueError("Wurzel ist kein Terminal")
    nodes = {root}
    edges = set()
    rest = [x for x in T if x != root]
    order = [root]
    while rest:
        best = None
        for r in rest:
            for v in sorted(nodes):
                key = (float(g.dist[v, r]), r, v)
                if best is None or key < best:
                    best = key
        _d, r, v = best
        for e in g.path_edges(v, r):
            edges.add(e)
        nodes.update(g.path(v, r))
        rest.remove(r)
        order.append(r)
    return make_solution("tm", g, edges, {"order": order, "root": root})


def best_takahashi_matsuyama(g):
    """Takahashi-Matsuyama mit jedem Terminal als Wurzel; das billigste Ergebnis (Gleichstand: kleinste Wurzel)."""
    sols = [takahashi_matsuyama(g, r) for r in g.terminals]
    return min(sols, key=lambda s: (s.cost, s.detail["root"]))


# --- Lokalsuche über Steinerpunkte ----------------------------------------------------------------------------------------------------------------


def induced_tree(g, nodes):
    """Der beschnittene MST des von `nodes` induzierten Teilgraphen; None, wenn er nicht zusammenhängt."""
    nodes = set(nodes)
    edges = [e for e in g.edges if e[0] in nodes and e[1] in nodes]
    mst = kruskal_edges(g, edges)
    if len(mst) != len(nodes) - 1:
        return None
    return prune(g, mst)


def local_search(g, start_nodes):
    """Lokalsuche: Menge X von Steinerpunkten (Start: `start_nodes`); Kosten(X) = beschnittener MST des induzierten Teilgraphen G[T + X]. Beste Verbesserung je Runde durch Einfügen eines Nachbarknotens
    von T + X oder Entfernen eines Steinerpunkts, streng fallende Kosten; Ende im lokalen Optimum."""
    ts = set(g.terminals)
    X = set(start_nodes) - ts
    cur = induced_tree(g, ts | X)
    if cur is None:
        raise ValueError("Startmenge verbindet die Terminals nicht")
    cost = g.cost(cur)
    rounds = 0
    while True:
        cand = []
        base = ts | X
        for v in range(g.n):
            if v in base:
                continue
            if any(x in base for x in g.adj[v]):
                cand.append(("add", v))
        cand += [("del", x) for x in sorted(X)]
        best = None
        for kind, v in cand:
            Y = X | {v} if kind == "add" else X - {v}
            tree = induced_tree(g, ts | Y)
            if tree is None:
                continue
            c = g.cost(tree)
            if c < cost - EPS and (best is None or c < best[0] - EPS):
                best = (c, Y, tree)
        if best is None:
            return make_solution("ls", g, cur, {"rounds": rounds})
        cost, X, cur = best
        X = {x for e in cur for x in e} - ts
        rounds += 1


# --- Exakt: Dreyfus-Wagner ------------------------------------------------------------------------------------------------------------------------


@dataclass
class ExactResult:
    solution: object
    states: int                                    # Zahl der (Teilmenge, Knoten)-Zustände


def dreyfus_wagner(g):
    """Exakter Steinerbaum: dp[S][v] = kürzester Baum, der die Terminals in S und den Knoten v verbindet. Erste Terminals als Teilmengen-Bits, das letzte Terminal als Wurzel;
    dp[S][v] = min_u (min_{A + B = S} dp[A][u] + dp[B][u]) + dist(u, v). O(3^(t-1) * n)."""
    T = list(g.terminals)
    if len(T) <= 1:
        return ExactResult(make_solution("exact", g, []), 0)
    q, sub = T[-1], T[:-1]
    k = len(sub)
    n = g.n
    full = (1 << k) - 1
    dp = np.full((1 << k, n), np.inf)
    split = np.zeros((1 << k, n), dtype=int)
    arg = np.zeros((1 << k, n), dtype=int)
    for i in range(k):
        dp[1 << i] = g.dist[:, sub[i]]
    for S in range(1, full + 1):
        if S & (S - 1) == 0:
            continue
        low = S & -S
        rest = S ^ low
        best = np.full(n, np.inf)
        bestA = np.zeros(n, dtype=int)
        s = rest
        while True:
            if s != rest:
                A = low | s
                cand = dp[A] + dp[S ^ A]
                better = cand < best - 1e-12
                best = np.where(better, cand, best)
                bestA = np.where(better, A, bestA)
            if s == 0:
                break
            s = (s - 1) & rest
        M = best[:, None] + g.dist
        arg[S] = np.argmin(M, axis=0)
        dp[S] = M[arg[S], np.arange(n)]
        split[S] = bestA
    edges = set()

    def build(S, v):
        if S & (S - 1) == 0:
            i = S.bit_length() - 1
            edges.update(g.path_edges(v, sub[i]))
            return
        u = int(arg[S][v])
        edges.update(g.path_edges(v, u))
        A = int(split[S][u])
        build(A, u)
        build(S ^ A, u)

    build(full, q)
    tree = prune(g, kruskal_edges(g, edges))
    sol = make_solution("exact", g, tree, {"dp_value": float(dp[full][q])})
    return ExactResult(sol, int(((1 << k) - 1) * n))
