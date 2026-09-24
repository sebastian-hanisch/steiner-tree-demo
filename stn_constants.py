"""Konstanten der Steiner-Baum-Demo: Instanz-Geometrie, Regler, gemessene Werte, Presets."""
SPACING = 10.0
JITTER = 0.15
SIDE_MIN, SIDE_MAX, DEFAULT_SIDE = 5, 14, 8
T_MIN, T_MAX, DEFAULT_T = 3, 30, 7
BLOCKED_OPTIONS = (0.0, 0.1, 0.2, 0.3, 0.4)
DEFAULT_BLOCKED = 0.1
SEED_MAX = 999999
DEFAULT_SEED = 35
KINDS = ("city", "textbook")
KIND_LABELS = {"city": "Stadtplan (Gitter)", "textbook": "Lehrbuchbeispiel (Plus, 4 Terminals)"}
LAYOUTS = ("uniform", "clusters")
LAYOUT_LABELS = {"uniform": "gleichverteilt", "clusters": "in Gruppen"}
SWEEP_SEEDS = tuple(range(100000, 100005))
FEAS_SEEDS = tuple(range(200000, 200050))
N_EXACT = 13
TREE_OPTIONS = ("best", "exact", "kmb", "tm", "tmr", "ls", "terminals")
TREE_LABELS = {"best": "Bester Fund", "exact": "Exakt", "kmb": "Kou-Markowsky-Berman", "tm": "Takahashi-Matsuyama (Depot)", "tmr": "Takahashi-Matsuyama (beste Wurzel)", "ls": "Lokalsuche", "terminals": "nur Terminals"}
DEFAULT_TREE = "best"

_BASE = {"kind": "city", "side": 8, "t": 7, "blocked": 0.1, "layout": "uniform", "seed": 35, "tree": "best"}
PRESETS = {
    "Standardfall (Voreinstellung)": dict(_BASE),
    "Lehrbuchbeispiel (Plus)": {**_BASE, "kind": "textbook"},
    "KMB weit über dem Optimum": {**_BASE, "seed": 62, "tree": "kmb"},
    "Lokalsuche bleibt hängen": {**_BASE, "seed": 56, "tree": "ls"},
    "KMB schlägt Takahashi-Matsuyama": {**_BASE, "seed": 53, "tree": "tm"},
    "Viele Terminals (t = 13)": {**_BASE, "side": 10, "t": 13},
    "Starke Sperrung (40 %)": {**_BASE, "blocked": 0.4},
    "Gruppierte Terminals": {**_BASE, "t": 9, "layout": "clusters"},
}
PRESET_HELP = {
    "Standardfall (Voreinstellung)": "Stadtplan 8 x 8 (64 Kreuzungen, 11 gesperrte Straßen), 7 Terminals, Seed 35: der Spannbaum über die Terminals kostet 170.42, der optimale Steinerbaum 161.69 (−5.12 %) mit einer Verzweigung. KMB, Takahashi-Matsuyama, Lokalsuche und exakt finden hier alle das Optimum.",
    "Lehrbuchbeispiel (Plus)": "Plus auf 3 x 3, vier Terminals um die Mitte: der Steinerpunkt in der Mitte verbindet alle mit Kosten 4, der Spannbaum über die Terminals kostet 6 (Verhältnis 3/2, −33.33 %). KMB und Takahashi-Matsuyama mit dem Depot als Wurzel finden nur 6, Takahashi-Matsuyama mit der besten Wurzel die 4.",
    "KMB weit über dem Optimum": "Seed 62: KMB und Takahashi-Matsuyama (Depot) kosten 195.87 - genau so viel wie \"nur Terminals\", also +18.22 % über dem Optimum 165.68; Takahashi-Matsuyama mit der besten Wurzel und die Lokalsuche finden 167.29 (+0.97 %).",
    "Lokalsuche bleibt hängen": "Seed 56: die Lokalsuche endet bei 166.75 (+8.71 % über dem Optimum 153.39), KMB bei 171.22 (+11.62 %); das Optimum hat 2 Verzweigungen, die Lokalsuche nur 1.",
    "KMB schlägt Takahashi-Matsuyama": "Seed 53: KMB 161.11 (+4.63 % über dem Optimum), Takahashi-Matsuyama mit dem Depot als Wurzel 176.07 (+14.35 %); mit der besten Wurzel, mit der Lokalsuche und exakt 153.98.",
    "Viele Terminals (t = 13)": "Plan 10 x 10, 13 Terminals: alle Heuristiken 302.76 (+1.50 % über dem Optimum 298.29); das Optimum hat 4 Verzweigungen, die Heuristiken 2. Ersparnis des Optimums gegen \"nur Terminals\" (320.20): 6.84 %.",
    "Starke Sperrung (40 %)": "40 % der Straßen gesperrt (45 von 112): \"nur Terminals\" 312.14, Optimum 251.72 (−19.36 %) mit 5 Verzweigungen; alle Verfahren finden es. Im Sweep über den gesperrten Anteil sparen Steinerpunkte bei 0 % im Median 6.67 %, bei 40 % 17.99 % (nicht monoton).",
    "Gruppierte Terminals": "9 Terminals in Gruppen, Seed 35: Steinerpunkte sparen nichts (99.47 gegen 99.47). Über 50 Instanzen sparen sie nur in 50 % der Fälle, im Mittel 2.1 %.",
}
# Beobachtete Spannweite der Kennzahl (MEDIAN über die 5 festen Instanzen Seeds 100000-100004) je Preset, mit Sicherheitsabstand: (Kennzahl, untere, obere Grenze).
PRESET_EXPECTED_BANDS = {
    "Standardfall (Voreinstellung)": ("saving_best", 10.0, 19.0),
    "Lehrbuchbeispiel (Plus)": ("saving_best", 33.0, 33.7),
    "KMB weit über dem Optimum": ("saving_best", 10.0, 19.0),
    "Lokalsuche bleibt hängen": ("saving_best", 10.0, 19.0),
    "KMB schlägt Takahashi-Matsuyama": ("saving_best", 10.0, 19.0),
    "Viele Terminals (t = 13)": ("saving_best", 8.0, 14.0),
    "Starke Sperrung (40 %)": ("saving_best", 14.0, 22.0),
    "Gruppierte Terminals": ("saving_best", 2.5, 8.0),
}
