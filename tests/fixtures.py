"""Per Skriptsuche gefundene kleine Instanzen (fest verdrahtet): Kanten (u, v, Länge), Terminals und die Kosten (Optimum, KMB, TM mit Wurzel = kleinstes Terminal, TM mit der besten Wurzel, Lokalsuche). Gegen Brute-Force bestätigt."""

from brute import graph_instance


FIXTURES = {
    "kmb_worse": dict(n=6, edges=[(0, 2, 8.393), (1, 2, 7.972), (1, 4, 8.745), (1, 5, 6.688), (2, 4, 3.668), (3, 4, 6.127), (3, 5, 3.795)], terminals=(0, 1, 3), opt=26.16, kmb=26.848, tm=26.16, tmr=26.16, ls=26.16),
    "tm_beats_kmb": dict(n=6, edges=[(0, 2, 8.393), (1, 2, 7.972), (1, 4, 8.745), (1, 5, 6.688), (2, 4, 3.668), (3, 4, 6.127), (3, 5, 3.795)], terminals=(0, 1, 3), opt=26.16, kmb=26.848, tm=26.16, tmr=26.16, ls=26.16),
    "tmr_beats_tm": dict(n=6, edges=[(0, 2, 6.994), (0, 5, 2.871), (1, 2, 2.308), (1, 4, 5.399), (1, 5, 8.192), (2, 5, 6.73), (3, 4, 8.653), (4, 5, 3.178)], terminals=(1, 3, 5), opt=17.23, kmb=20.023, tm=20.023, tmr=17.23, ls=17.23),
    "ls_improves": dict(n=6, edges=[(0, 1, 7.821), (0, 3, 8.021), (1, 5, 8.697), (2, 3, 5.885), (2, 4, 7.803), (2, 5, 6.913), (3, 4, 2.607), (3, 5, 4.726), (4, 5, 8.454)], terminals=(1, 2, 4), opt=21.915, kmb=23.413, tm=22.943, tmr=22.943, ls=21.915),
    "ls_stuck": dict(n=7, edges=[(0, 2, 5.195), (0, 3, 8.638), (0, 6, 9.831), (1, 2, 6.587), (1, 6, 2.792), (2, 4, 8.908), (2, 6, 3.84), (3, 5, 4.102), (3, 6, 5.603), (4, 5, 6.8), (5, 6, 8.337)], terminals=(0, 3, 4, 6), opt=23.546, kmb=25.143, tm=25.143, tmr=25.143, ls=25.143),
    "kmb_beats_tm": dict(n=8, edges=[(0, 1, 1.874), (0, 4, 1.289), (0, 7, 7.214), (1, 3, 8.065), (2, 4, 7.848), (2, 6, 4.548), (3, 5, 1.195), (3, 6, 1.531), (4, 5, 6.779), (5, 7, 4.715)], terminals=(1, 3, 4, 6, 7), opt=17.383, kmb=17.383, tm=17.818, tmr=17.383, ls=17.383),
}


def fixture(name):
    f = FIXTURES[name]
    return graph_instance(f["n"], f["edges"], f["terminals"]), f
