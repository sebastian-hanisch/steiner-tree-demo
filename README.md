# Steiner-Baum – Kou-Markowsky-Berman, Takahashi-Matsuyama, Lokalsuche, exakt – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-steiner-tree-demo.streamlit.app/)**

Achtes Stück der **Spannbaum-Reihe** der "Konzepte"-Reihe für die Website "Sebastian Hanisch – Operations Research und Machine Learning". Bisher verliefen die Kanten nur **zwischen den Kunden**. In einem Leitungsnetz darf man aber an **Kreuzungen verzweigen, die selbst kein Kunde sind** - **Steinerpunkte** -, und das kann den Baum kürzer machen. Gegeben ist ein Stadtplan (Kreuzungen, Straßen mit Länge, ein Teil der Straßen gesperrt) und eine Menge von **Terminals** (Depot und Kunden); gesucht ist der kürzeste Baum im Plan, der alle Terminals verbindet - mit beliebigen Zwischenknoten. Das **Steiner-Baum-Problem in Graphen** ist **NP-schwer**; der Spannbaum über die Terminals (mit den Abständen im Plan) ist der Sonderfall ohne Steinerpunkte und dient als **Basislinie**. Die Demo misst, **was Steinerpunkte sparen**, wie gut **Kou-Markowsky-Berman** (KMB), **Takahashi-Matsuyama** (TM) und eine **Lokalsuche über Steinerpunkte** gegen das **exakte Optimum** (**Dreyfus-Wagner**, nur für wenige Terminals) abschneiden und was Sperrungen und Gruppierung ändern. Der Kernsatz macht das Optimum überprüfbar: jeder Steinerbaum ist ein Baum auf Terminals plus einer Menge X von Steinerpunkten, also ist **OPT = min über X von MST(G[T ∪ X])** (MST des induzierten Teilgraphen).

**Einordnung in die Reihe:** die Reihe hat elf Stücke, alle sind gebaut, dies ist das achte:

```
Kruskal (Wurzel)                                                                           [gebaut: kruskal-demo]
 ├─ Prim (Kontrast: wächst von einem Punkt)                                                [gebaut: prim-demo]
 ├─ Borůvka (Kontrast: alle Komponenten parallel)                                          [gebaut: boruvka-demo]
 ├─ Euklidischer MST (keine n²-Kantenliste, Delaunay)                                      [gebaut: euclidean-mst-demo]
 ├─ Gerichteter Spannbaum (Chu-Liu/Edmonds)                                                [gebaut: arborescence-demo]
 ├─ Bottleneck-/Grad-/Hop-beschränkter Spannbaum                                           [gebaut: constrained-mst-demo]
 │    └─ Kapazitierter MST                                                                 [gebaut: cmst-demo]
 ├─ Steiner-Baum                                                                           [DIESES STÜCK]
 │    └─ Prize-Collecting Steiner-Baum                                                     [gebaut: pcst-demo]
 ├─ MST-Sensitivität & dynamischer MST                                                     [gebaut: mst-sensitivity-demo]
 └─ Zufällige Spannbäume & Kirchhoff                                                       [gebaut: random-spanning-tree-demo]
```

Ergebnis in Kürze: **Steinerpunkte sparen auf dem Stadtplan im Mittel 8,6 % gegenüber dem Spannbaum über die Terminals (Plan 8 x 8, 7 Terminals; in 92 % der Instanzen etwas, im Einzelfall bis 20,5 %), in Gruppen nur 2,1 % (in 50 % der Fälle). KMB ist das schwächste Verfahren: er trifft den besten Baum bei 7 Terminals nur in 26 % der Instanzen (mittlere Lücke 5,1 %, größte gut 20 %). Takahashi-Matsuyama hängt stark von der Wurzel ab: mit dem Depot als Start 30 % optimal (mittlere Lücke 3,2 %), mit der besten Wurzel 56 % (1,2 %). Die Lokalsuche verbessert den Start nur in 6 % der Instanzen und ist in 62 % optimal.** Die Garantie 2 (1 − 1/t) x Optimum wurde nie verletzt; die Lücken liegen weit darunter.

| Frage | Ergebnis (Plan 8 x 8, 7 Terminals, 10 % gesperrte Straßen, gleichverteilte Terminals, sofern nicht anders angegeben; **Median** über 5 feste Instanzen, Seeds 100000–100004; vollständig deterministisch) |
|---|---|
| **Ist der Kernsatz und Dreyfus-Wagner richtig?** | ✅ ja, direkt geprüft: Dreyfus-Wagner gleich dem Minimum über **alle** Steinerpunkt-Mengen (Brute-Force auf 200 Zufallsgraphen mit Gleichständen und 40 Plänen); der Kernsatz zusätzlich gegen eine davon unabhängige Aufzählung **aller Bäume** in 60 Kleingraphen |
| **Was sparen Steinerpunkte?** | Ersparnis des besten Baums gegen "nur Terminals" bei t = 3/4/5/7/9/11/13: **9,4/14,4/14,3/14,3/5,8/8,8/8,4 %**; Steiner-Verhältnis (nur Terminals / bester Baum) 1,10/1,17/1,17/1,17/1,06/1,10/1,09; ab 20/30 Terminals (ohne exaktes Verfahren): 5,6/2,1 % |
| **Über viele Instanzen** (50 Instanzen, exakt) | t = 7: Steinerpunkte sparen in **92 %** der Instanzen, im Mittel **8,6 %**, höchstens 20,5 % (größtes Verhältnis 1,26); t = 11: 98 % / 8,5 % / 17,9 % (1,22); t = 9 mit 30 % Sperrung: 100 % / 11,6 % / 20,2 % (1,25) |
| **Gruppierte Terminals** | ⚠️ sparen kaum: t = 9 in Gruppen: Steinerpunkte sparen nur in **50 %** der Instanzen, im Mittel **2,1 %** (gleichverteilt: Median 5,8 % gegen 5,0 % in Gruppen); bei t = 7: Median-Ersparnis 14,3 % gleichverteilt gegen 0,0 % in Gruppen |
| **Sperrungen** | Ersparnis bei 0/10/20/30/40 % gesperrten Straßen: **6,7/14,3/11,4/15,4/18,0 %** - im Trend mehr, aber nicht monoton; Verzweigungen im besten Baum 1/3/2/2/2 |
| **Plangröße** | Ersparnis bei 5/6/8/10/12/14 Kreuzungen je Seite: 10,9/1,1/14,3/9,7/8,4/9,9 % - kein klarer Trend (5 Instanzen je Wert) |
| **Wie gut ist KMB?** | Aufschlag gegen das Optimum (Median) bei t = 3/4/5/7/9/11/13: **0/+7,6/+10,2/+8,2/+6,1/+6,8/+6,8 %**; optimal in 60/0/20/0/40/20/20 % der Instanzen; über 50 Instanzen (t = 7): optimal in 26 %, mittlere Lücke 5,12 %, größte 20,11 %; t = 11: 2 %, 5,76 %, 14,35 % |
| **Wie gut ist Takahashi-Matsuyama?** | Mit **Depot als Wurzel**: Aufschlag im Median 0/+6,3/0/+6,3/0/+1,4/+2,9 %, optimal in 80/0/60/0/60/40/20 %; mit **bester Wurzel**: Median-Aufschlag 0 bei jedem t, optimal in 80/60/80/60/80/80/60 %. Über 50 Instanzen (t = 7): Depot optimal 30 % (mittlere Lücke 3,21 %, größte 15,52 %), beste Wurzel 56 % (1,18 %, 6,18 %) |
| **KMB gegen TM** | TM (Depot) schlägt KMB in **40 %** der Instanzen (t = 7; t = 11: 72 %), KMB schlägt TM in **10 %** (t = 11: 4 %) - KMB ist nicht durchgehend schlechter |
| **Wie gut ist die Lokalsuche?** | Median-Aufschlag 0 bei jedem t und jeder Sperrung, aber über 50 Instanzen (t = 7) nur **62 % optimal** (mittlere Lücke 1,08 %, größte 6,18 %); sie verbessert den Start (bestes von KMB/TM) in 6 % (t = 11: 22 %); auf großen Plänen bleibt sie hängen: Lücke gegen das Optimum bei 5/6/8/10/12/14 Kreuzungen je Seite 0/0/0/**2,25**/0,17/**2,33** % |
| **Wie viele Verzweigungen?** | Verzweigungen (Nicht-Terminal-Knoten mit Grad ≥ 3) im besten Baum bei t = 3/4/5/7/9/11/13: 1/1/2/3/1/3/2; die übrigen Steinerknoten sind nur Durchgang (Grad 2) - im Standardfall 9 Steinerknoten, davon 3 Verzweigungen |
| **Das Steiner-Verhältnis** | ✅ ≤ 2 in jedem Graphen (Test über Zufallsgraphen und Pläne); auf dem **ungestörten, ungesperrten Gitter** höchstens **1,40** in 300 Instanzen (Schranke 3/2, Hwang 1976), mit 20 % gesperrten Straßen 1,36; das Lehrbuch-Plus erreicht 1,5 |
| **Aufwand des exakten Wegs** | Zustände (Teilmenge, Kreuzung) = (2^(t−1) − 1) · n, der Rechenaufwand wächst mit 3^t; auf dem 8 x 8-Plan bei t = 4/8/12: 448/8128/131 008 Zustände; gemessen ca. 1 s bei t = 13, 3 s bei t = 14 (Plan 10 x 10) - deshalb nur bis t = 13 |

## Was die Demo zeigt

1. **Der Steinerbaum in Aktion** (Schritt-Slider): **Der Plan** (Kreuzungen, Straßen, gesperrte Straßen rot gepunktet, Terminals) → **Kou-Markowsky-Berman** (Slider über die Schritte: die t − 1 Kanten des Spannbaums über die Terminals als **kürzeste Wege im Plan**, der neue Weg orange; im letzten Schritt Spannbaum der vereinigten Wege und Beschneiden, entfallene Kanten rot gestrichelt; Rauten = Steinerknoten, gefüllt = Verzweigung, hohl = nur Durchgang) → **Der Steinerbaum** (Umschalter Bester Fund / Exakt / KMB / Takahashi-Matsuyama (Depot) / (beste Wurzel) / Lokalsuche / nur Terminals; die gestrichelte Luftlinie zeigt den Spannbaum über die Terminals im Vergleich; darunter die Ersparnis je Verfahren als Balken).
2. **Was sparen Steinerpunkte?** Ersparnis, Verzweigungen, Aufschlag von KMB und TM, Steiner-Verhältnis, Garantie 2 (1 − 1/t) und wie weit KMB und TM tatsächlich darunter liegen, TM mit bester Wurzel, Lokalsuche, Beleg, ob das Optimum bewiesen ist.
3. **🎲 Wie gut sind die Verfahren?** (auf Abruf): 50 Instanzen - Anteil optimal je Verfahren, mittlere und größte Lücke, KMB gegen TM, Anteil der Instanzen, in denen Steinerpunkte sparen, größtes Steiner-Verhältnis, Garantieverletzungen.
4. **⏱️ Was kostet der exakte Weg?** (auf Abruf): Zustände und gemessene Sekunden über die Terminalzahl.
5. **📐 Sweeps** über Terminals, Plangröße, gesperrten Anteil und Lage der Terminals: Ersparnis, Aufschlag der Verfahren, Verzweigungen (5 feste Instanzen, Median, 10.–90. Perzentil-Band).
6. **🚧 Grenzen:** Tabelle "Annahme – was passiert – wer setzt an".

Regler: Instanz (Stadtplan / **Lehrbuchbeispiel** Plus), Gittergröße (5–14 Kreuzungen je Seite), Terminals t (3–30), gesperrter Anteil (0–40 %), Lage der Terminals (gleichverteilt / in Gruppen), Seed (+ 🎲), Baumauswahl. Alle Regler wirken auf Plan, Terminals oder Anzeige; das Lehrbuchbeispiel blendet die Planregler aus. Kein Zufall im Kern.

## Messwerte der Presets

| Preset | Instanz | Ergebnis |
|---|---|---|
| Standardfall (Voreinstellung) | Plan 8 x 8 (64 Kreuzungen, 11 gesperrte Straßen), 7 Terminals, Seed 35 | "nur Terminals" 170,42; Optimum 161,69 (−5,12 %) mit einer Verzweigung; KMB, TM, Lokalsuche und exakt finden dasselbe |
| Lehrbuchbeispiel (Plus) | 3 x 3, 4 Terminals | Optimum **4** (Steinerpunkt in der Mitte) gegen 6 (Verhältnis 3/2, −33,33 %); KMB und TM mit Depot als Wurzel finden nur 6, TM mit der besten Wurzel und die Lokalsuche die 4 |
| KMB weit über dem Optimum | Seed 62 | KMB und TM (Depot) 195,87 = "nur Terminals" (+18,22 % über dem Optimum 165,68); TM mit bester Wurzel und Lokalsuche 167,29 (+0,97 %) |
| Lokalsuche bleibt hängen | Seed 56 | Lokalsuche 166,75 (+8,71 % über dem Optimum 153,39), KMB 171,22 (+11,62 %); das Optimum hat 2 Verzweigungen, die Lokalsuche 1 |
| KMB schlägt Takahashi-Matsuyama | Seed 53 | KMB 161,11 (+4,63 %), TM (Depot) 176,07 (+14,35 %); TM mit bester Wurzel, Lokalsuche und exakt 153,98 |
| Viele Terminals (t = 13) | Plan 10 x 10 | alle Heuristiken 302,76 (+1,50 % über dem Optimum 298,29); Optimum mit 4 Verzweigungen, die Heuristiken mit 2; Ersparnis 6,84 % gegen 320,20 |
| Starke Sperrung (40 %) | 45 von 112 Straßen | "nur Terminals" 312,14, Optimum 251,72 (−19,36 %), 5 Verzweigungen; alle Verfahren finden es |
| Gruppierte Terminals | t = 9 | Steinerpunkte sparen nichts (99,47 gegen 99,47) |

Das **Lehrbuchbeispiel** ist von Hand nachzurechnen: Terminals W, E, S, N um die Mitte M des 3 x 3-Gitters, Straßen der Länge 1. Ohne Steinerpunkt kostet der Spannbaum über die Terminals 2 + 2 + 2 = 6 (jede Terminalkante ist zwei Straßen lang); mit M als Steinerpunkt genügen vier Straßen: 4. KMB und TM mit dem Depot als Wurzel gehen die Wege einzeln und zahlen 6; TM mit der besten Wurzel findet 4. Die Einzelinstanz weicht von den Medianen ab - die Mediane sind die belastbaren Zahlen; die Presets prüfen sich zusätzlich über die 5 festen Instanzen gegen eine gemessene Spannweite des Medians der Ersparnis (`tests/test_presets.py`).

## Modell und Verfahren

- **Instanz** (`stn_scenario.py`): Stadtplan als gestörtes Gitter (Seite x Seite Kreuzungen, Verschiebung bis 15 % des Abstands), Straßen zwischen Nachbarn mit euklidischer Länge; ein Anteil der Straßen gesperrt (zufällige Reihenfolge, eine Sperrung, die den Plan zerlegte, wird übersprungen); Terminals gleichverteilt oder in 2 bis 3 Gruppen um wenige Mittelpunkte; das Depot ist das Terminal mit der kleinsten Knotennummer. Lehrbuchbeispiel: Plus auf 3 x 3.
- **Basislinie "nur Terminals"** (`closure_mst`): MST über die Terminals mit den Abständen im Plan (Metrik-Abschluss, Floyd-Warshall in numpy).
- **Kou-Markowsky-Berman** (`kmb`): MST im Metrik-Abschluss → jede Kante durch einen kürzesten Weg ersetzen → MST der Vereinigung der Wege → Nicht-Terminal-Blätter abschneiden. Garantie höchstens 2 (1 − 1/t) x Optimum.
- **Takahashi-Matsuyama** (`takahashi_matsuyama`): Start am Depot (kleinstes Terminal); in jedem Schritt das dem Baum nächste Terminal über den kürzesten Weg anhängen (Gleichstand: kleinster Abstand, dann kleinstes Terminal, dann kleinster Baumknoten). `best_takahashi_matsuyama` probiert jedes Terminal als Start und nimmt das billigste Ergebnis (TMR). Dieselbe Garantie.
- **Lokalsuche** (`local_search`): Start = Steinerknoten des besten der drei Heuristik-Ergebnisse; Kosten(X) = beschnittener MST des von T ∪ X induzierten Teilgraphen; beste Verbesserung durch Einfügen eines Nachbarknotens oder Entfernen eines Steinerpunkts, streng fallend.
- **Exakt** (`dreyfus_wagner`): dynamische Programmierung über die Teilmengen der ersten t − 1 Terminals mit dem letzten als Wurzel: `D[S][v] = min_u (min_{A+B=S} D[A][u] + D[B][u]) + d(u, v)`, numpy-vektorisiert über die Kreuzungen; Rückverfolgung zum Baum, der Baum gleich dem DP-Wert (Test). Wird bis t = 13 angeboten.
- **Verzweigung** = Nicht-Terminal-Knoten mit Grad ≥ 3 im Baum; die übrigen Steinerknoten sind Durchgang.

## Was nicht funktioniert hat / Grenzen

- **Erwartung "KMB ist eine brauchbare Standardheuristik" - nur mit Vorbehalt:** er ist bei 7 Terminals nur in 26 % der Instanzen optimal und liegt im Median 6 bis 10 % über dem Optimum; im Preset "KMB weit über dem Optimum" spart er gegenüber der Basislinie gar nichts (+18,22 % über dem Optimum).
- **Erwartung "TM ist KMB überlegen" - nur mit dem richtigen Start:** mit dem Depot als Wurzel ist TM in 40 % der Instanzen besser, aber in 10 % schlechter als KMB (Preset "KMB schlägt Takahashi-Matsuyama": +4,63 % gegen +14,35 %); erst die beste Wurzel macht TM stark (56 % optimal). Im ersten Entwurf dieser Demo zählte nur TM mit bester Wurzel - dann schlug KMB TM in keiner der untersuchten Instanzen; das lag an t Versuchen gegen einen (unfairer Vergleich), deshalb hier beides.
- **Erwartung "die Lokalsuche schließt die Lücke" - widerlegt:** sie verbessert den Start nur in 6 % (t = 7) bzw. 22 % (t = 11) der Instanzen und bleibt bei großen Plänen um bis zu 2,3 % über dem Optimum (Preset "Lokalsuche bleibt hängen": +8,71 %). Einfügen und Entfernen einzelner Knoten reicht nicht, wenn erst ein ganzer Umweg gleichzeitig entfällt.
- **Erwartung "mehr Sperrungen, mehr Ersparnis" - nur im Trend:** 6,7/14,3/11,4/15,4/18,0 % bei 0 bis 40 %, nicht monoton (5 Instanzen je Wert).
- **Steinerpunkte sind hier nur Kreuzungen (Graph-Steiner):** das euklidische Steiner-Problem mit frei wählbaren Punkten in der Ebene ist ein anderes (bekannte Konstante 2/√3 ≈ 1,155 - hier weder gebaut noch nachgemessen); die Schranke 3/2 (Hwang 1976) gilt für das rechtwinklige Gitter und wird nur auf dem ungestörten Gitter geprüft (höchstens 1,40 in 300 Instanzen).
- **Exakt ist klein:** Dreyfus-Wagner wächst mit 3^t und wird bis t = 13 angeboten; der Stand der Technik (Reduktionen, Branch-and-Cut, SCIP-Jack, PACE 2018) löst Instanzen mit tausenden Terminals - nicht gebaut. Auch die LP-Verfahren von Byrka, Grandoni, Rothvoß und Sanità (2013, Näherungsgüte ln 4 + ε ≈ 1,39) sind nur genannt. Aufschläge bei t > 13 sind Abstände zwischen Heuristiken, keine Lücken zum Optimum.
- **Synthetisches Modell:** gestörtes Gitter, Länge als einzige Kosten, keine Kapazität, keine Kosten für Steinerpunkte; 5 feste Instanzen je Wert für die Sweeps, 50 für die Verteilungen.
- **Nachfolger (inzwischen gebaut):** Prize-Collecting Steiner-Baum (`pcst-demo`), Sensitivität (`mst-sensitivity-demo`), zufällige Spannbäume (`random-spanning-tree-demo`).

## Verifikation

- **Kernsatz und Exaktheit:** Dreyfus-Wagner gleich Brute-Force über alle Steinerpunkt-Mengen (200 Zufallsgraphen mit 5 bis 10 Knoten, 2 bis 5 Terminals, Gleichstände; 40 Gitterpläne); der Kernsatz gleich einer davon unabhängigen Aufzählung aller Bäume (60 Kleingraphen); Sonderfälle 1 Terminal (Kosten 0), 2 Terminals (kürzester Weg), alle Knoten Terminals (MST).
- **Gültigkeit:** jede Ausgabe ist ein Baum im Plan (Kanten aus dem Graphen, azyklisch, zusammenhängend), enthält alle Terminals, hat nur Terminals als Blätter; Kosten gleich der Kantensumme.
- **Garantien und Schrankenkette:** Optimum ≤ Lokalsuche ≤ Start ≤ Heuristik, KMB, TM und TMR höchstens 2 (1 − 1/t) x Optimum (200 Zufallsgraphen und 60 Pläne mit Sperrungen und Gruppierung); Basislinie ≤ 2 x Optimum; auf dem ungestörten Gitter ≤ 3/2; die Lokalsuche endet in einem lokalen Optimum ihrer Nachbarschaft (nachgeprüft über alle Einfüge- und Entfernkandidaten).
- **Graph-Werkzeuge:** Floyd-Warshall gleich Dijkstra (60 Graphen, alle Paare), Pfade kürzest und einfach; parallele Kanten, Unerreichbares, Beschneiden, Kruskal-Hilfen einzeln getestet.
- **KMB-Buchführung:** t − 1 Schritte, Summe der Abstände gleich der Basislinie, jeder Weg kürzest.
- **Schwierige Fixtures** (per Skriptsuche gefunden, gegen Brute-Force bestätigt): KMB strikt über dem Optimum, TM schlägt KMB und umgekehrt, die Wurzel entscheidet über TM, die Lokalsuche verbessert den Start bzw. bleibt hängen.
- **Zahlen:** jede Zahl in App-Text und README ist in `tests/test_claims.py` über die echten Auswertungsfunktionen (`ev.analyse`, `ev.run_config`, `ev.sweep`, `ev.quality`, `ev.exact_time_curve`) belegt; die Sekundenangaben des exakten Wegs sind Messungen und nicht Teil der Tests.

## Lokal starten

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements-dev.txt
streamlit run app.py
python -m pytest tests -v
```

## Literatur

- Takahashi, H., & Matsuyama, A. (1980). *An approximate solution for the Steiner problem in graphs.* Mathematica Japonica 24(6), 573–577.
- Kou, L., Markowsky, G., & Berman, L. (1981). *A fast algorithm for Steiner trees.* Acta Informatica 15, 141–145.
- Dreyfus, S. E., & Wagner, R. A. (1971). *The Steiner problem in graphs.* Networks 1(3), 195–207.
- Hwang, F. K. (1976). *On Steiner minimal trees with rectilinear distance.* SIAM Journal on Applied Mathematics 30(1), 104–114.
- Byrka, J., Grandoni, F., Rothvoß, T., & Sanità, L. (2013). *Steiner tree approximation via iterative randomized rounding.* Journal of the ACM 60(1) (nur genannt, nicht gebaut).

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Spannbäume: vom Kruskal bis zum Zufallsbaum](https://sebastianhanisch.net/konzepte-spannbaum.html).
