# Kabelkanal 3,5 mm (schlankes Profil, Öffnung hinten, von vorne aufsteckbar, weiß) — Maß- und Konstruktionsdokumentation

## 1. Aufgabenstellung & Randbedingungen

- **Bauteil**: Maximal langer, schlanker, weißer Kabelkanal (`kabelkanal-3-5mm`) für ein Rundkabel mit **Ø 3,50 mm**, Rückseite abgeflacht mit **rückseitiger Kabel-Einclipsöffnung (`hinten`)**, komplett **geschlossener Sichtseite (`vorne`)** und **ohne Stützen (`0,00 g` Support bei `enable_support=1, tree(auto)`)** auf dem Anycubic Kobra S1 Combo + ACE Pro druckbar.
- **Steckverbindung („von vorne in einem Zug aufstecken")**: Schlanke **Von-vorne-Aufrast-Überblattung (`Saddle-Hood-Joint`)** ohne doppelwandige koaxiale Muffe. Wenn Segment 1 bereits an der Wand / auf dem Kabel sitzt, wird Segment 2 **von vorne in einem Zug (`-Z` in Einbaulage)** gleichzeitig auf das Kabel und über den Sattelzapfen von Segment 1 gedrückt. Ein vertikaler T-Quersteg (`KEY_RIB_PROTRUSION = 0,34 mm`) verriegelt beide Kanäle formschlüssig gegen axiales Auseinanderziehen (`±X`), während eine horizontale Rastleiste (`SNAP_BEAD_PROTRUSION = 0,22 mm`) das Abheben nach vorne (`+Z`) sichert.
- **Druckbettlimit & 5 Modul-Varianten (+ 35 mm Passungs-Teststück)**: Anycubic Kobra S1 (`250,0 mm × 250,0 mm`). Alle **fünf Druckvarianten** liegen gemeinsam auf **Platte 1** von `models/kabelkanal-3-5mm-print.3mf` (`Y = 89 / 107 / 125 / 143 / 161 mm`, `18,0 mm` Mittenabstand = `11,2 mm` lichter Abstand):
  1. `models/kabelkanal-3-5mm-mitte-beidseitig.stl` (sowie `models/kabelkanal-3-5mm.stl`): **Mittelkanal (`242,00 mm`)** mit Verbindung links (`-X` Aufrast-Sattel) und rechts (`+X` Überwurf-Kappe), `232,00 mm` Netto-Rastermaß.
  2. `models/kabelkanal-3-5mm-abschluss-links.stl`: **Abschlusskanal für links (`242,00 mm`)**, links (`-X`) glatter Abschluss ohne Sattel-Abstufung (bei durchgehender Kabelbohrung und Rückseitenschlitz), Verbindung nur rechts (`+X` Überwurf-Kappe).
  3. `models/kabelkanal-3-5mm-abschluss-rechts.stl`: **Abschlusskanal für rechts (`242,00 mm`)**, Verbindung nur links (`-X` Aufrast-Sattel), rechts (`+X`) glatter Abschluss ohne Überwurf-Aussparung (`232,00 mm` Sichtprofil + `10,00 mm` Sattel).
  4. `models/kabelkanal-3-5mm-einzeln-ohne-verbindung.stl`: **Einzel-/Kurzkanal ohne Verbindungen (`242,00 mm`)**, weder links (`-X`) noch rechts (`+X`) mit Verbinder, volle Druckplattenlänge (`242,00 mm`).
  5. `models/kabelkanal-3-5mm-10cm-rechts.stl`: **10 cm Pass-/Abschlussstück (`100,00 mm`)**, links (`-X`) glatter Abschluss ohne Verbindung, Verbindung nur rechts (`+X` Überwurf-Kappe).
  - Zusätzlich wird `models/kabelkanal-3-5mm-teststueck-35mm.stl` (`35,00 mm` Kurz-Prüfmuster mit beidseitigen Verbindern, `~0,7 g` PLA / `~4 min` Druckzeit) exportiert, um das reale Einclipsen des vorhandenen Kabels vorab schnell testen zu können.

## 2. Recherche wiederverwendbarer 3D-Assets (`research-reusable-3d-assets`)

- **Ergebnis**: Funktionales, parametrisches Konstruktionsbauteil ohne organisches/skulpturales Freiform-Motiv. Standard-Kabelkanäle sind für ein einzelnes `3,5 mm`-Kabel zu breit/hoch (`>= 10 × 10 mm`) und besitzen keine einteilige Von-vorne-Aufrast-Überblattung.
- **Entscheidung**: Vollparametrische Eigenkonstruktion in Python (`scripts/kabelkanal_3_5mm.py`) gemäß `create-ascii-stl`, `reversible-fdm-joints` und `orcaslicer-support-minimization`. Lizenz/Provenienz: Eigenkonstruktion Repository (`MIT`).

## 3. Maß- und Toleranztabelle (`research-part-specs`) — Revision v2 nach realem Drucktest

Nach dem ersten realen Drucktest meldete der Benutzer, dass sich das `3,5 mm`-Kabel nicht in den Kanal eindrücken ließ („das Kabel läss sich nicht reindrücken das ist zu massiv") und auch im Kanalinneren mehr Platz benötigt wird („ggf. inner auch etwas mehr als nur die 3.5mm plaz lassen"). In Revision v2 wurden daher **Innenbohrung, Schlitz-Engstelle, Einführtrichter, Rastlippenhöhe, Wandstärke der Federwangen und Slicer-Wandlinien** gezielt überarbeitet:

| Parameter | Symbol im Skript | Alt (v1) [mm] | Neu (v2) [mm] | Herkunft / Begründung | Vertrauen |
| --- | --- | ---: | ---: | --- | --- |
| Kabel-Nenndurchmesser | `CABLE_DIAMETER` | `3,50` | `3,50` | Benutzervorgabe („für ein Kabel der Stärke 3,5mm") | Bestätigt (Benutzer) |
| Radialspiel / Durchmesserspiel Bohrung | `CABLE_RADIAL_CLEARANCE` | `0,18` (`+0,36` Ø) | **`0,40` (`+0,80` Ø)** | Großzügiges Innenspiel gegen Kabel-Toleranzen, Mantelwelligkeit und FDM-Innenschrumpfung | Konstruktions-Schätzwert (Testdruck empfohlen) |
| Innenbohrung Kabelkanal | `2 * BORE_RADIUS` | `Ø 3,86` (`R = 1,93`) | **`Ø 4,30` (`R = 2,15`)** | Zentrum bei `Z_print = 3,10 mm` (`Z ∈ [0,95, 5,25] mm`), nimmt selbst einen `Ø 4,10 mm`-Prüfdorn mit `0,0000 mm³` Kollision auf; `0,95 mm` (6 Layer) geschlossene Sichtwand vorne | Abgeleitet (CAD-verifiziert; reales Kabel noch zu testen) |
| Schlankes Außenprofil (`Breite × Höhe`) | `OUTER_WIDTH × OUTER_HEIGHT` | `7,20 × 5,20` | **`6,80 × 5,40`** | Schmalere Außenbreite (`6,80 mm`) reduziert die seitliche Wandstärke neben der `Ø 4,30 mm`-Bohrung gezielt auf elastische **`1,25 mm` Federwangen** | Benutzervorgabe („zu massiv" -> elastisch) |
| Seitliche Federwandstärke (auf Bohrungsmittellinie) | `Y_OUTER - BORE_RADIUS` | `1,67` (3 Wände = massiv) | **`1,25` (2 Wände)** | Biegesteifigkeit $\propto (1,25 / 1,67)^3 = \mathbf{0,419}$ (**58 % weicher**); mit `wall_loops = 2` und `xy_hole_compensation = 0,08 mm` deutlich nachgiebiger | Elastizitätsrechnung / Schätzwert |
| Rückseitige Einclips-Engstelle (Throat) | `SLOT_THROAT_WIDTH` | `2,75` (`0,75` Hinterschnitt) | **`3,20` (`0,30` Hinterschnitt)** | Nur noch **`0,15 mm` Auslenkung je Seite** nötig (statt `0,375 mm`), hält das `3,50 mm`-Kabel dennoch formschlüssig (`3,20 mm < 3,50 mm`) | Konstruktions-Schätzwert (Testdruck mit realem Kabel offen) |
| Rückseitige Einclips-Fase (Einführtrichter) | `SLOT_ENTRY_WIDTH` | `3,10` (`< 3,50` Kabel!) | **`3,90` (`±1,95`, `0,58` tief)** | Trichteröffnung (`3,90 mm`) ist jetzt **breiter als das `3,50 mm`-Kabel**, sodass sich das Kabel vor dem Eindrücken selbst im Schlitz zentriert | Funktionsmaß |
| Vertikale Rastlippen-Steghöhe am Throat | `Z_THROAT_TOP - z_throat_bot` | `0,497` | **`0,284`** | Kurze, abgerundete Rastnase (`Z = 4,54 .. 4,82 mm`); theoretische Eindrückkraft sinkt auf **`16,8 %` (~6× leichter)**, Eindrückarbeit auf **`6,7 %` (~15× leichter)** gegenüber v1 | Mechanische Modellrechnung |
| Sichtseite vorne (`Z_print = 0,00 mm`) | `FRONT_BEVEL` | `1,20 × 45°` | **`1,10 × 45°`** | Geschlossene, glatte Sichtfront (`4,60 mm` Stirnspiegel + beidseitig `1,10 mm × 45°` Fase, `0,00 mm²` kritischer Überhang) | Stützfrei-Nachweis |
| Abgeflachte Rückseite (`hinten`, `Z_print = 5,40 mm`) | `Y_OUTER - Y_ENTRY` | `2 × 2,05` | **`2 × 1,45`** | Zwei plane Wandauflagestreifen (`Y ∈ [-3,40, -1,95]` und `[+1,95, +3,40]`), im Druck per `ironing_type=top` geglättet | Konstruktionsmaß |
| Längen der 5 Druckvarianten (+ Prüfstück) | `VARIANT_SPECS` | `4 × 242,00` | **`4 × 242,00` + `1 × 100,00` (+ `35,00`)** | 4× Maximallänge (`242,00 mm`: Links, Mitte, Rechts, Einzeln) + 1× **`100,00 mm` (`10 cm`) mit Verbindung nur rechts (`+X`)** gemeinsam auf Platte 1 | Benutzervorgabe |
| Überblattungslänge (Sattel / Kappe) | `CONNECTOR_LENGTH` / `SOCKET_DEPTH` | `10,00` / `10,10` | **`10,00` / `10,10`** | `-X` innerer Aufrast-Sattel (`10,00 mm`, `Z_SADDLE_SHOULDER = 1,32 mm` für `>= 45°` stützfreie Fase), `+X` äußere Überwurf-Kappe (`10,10 mm`) | FDM-Passung |
| Sattelbreite / Wangenstärke Kappe | `2 * Y_SADDLE_BASE` | `4,80` (`±2,40`) | **`5,00` (`±2,50`)** | `0,35 mm` Sattelwand um die `Ø 4,30 mm`-Bohrung + `0,78 mm` äußere Überwurf-Wange (`0,12 mm` Flankenspiel je Seite) | FDM-Passung |
| Vertikaler T-Quersteg (`±X`-Formschluss) | `KEY_RIB_PROTRUSION` / `KEY_SLOT_DEPTH` | `0,34` / `0,36` | **`0,20` / `0,22`** | Bei `5,00 mm` vor der Schulter: verhindert axiales Auseinanderziehen (`0,6075 mm³` Formschluss-Eingriff) | Funktionsmaß |
| Horizontale Rastleiste (`±Z`-Click-Lock) | `SNAP_BEAD_PROTRUSION` / `SNAP_GROOVE_DEPTH` | `0,22` / `0,24` | **`0,18` / `0,20`** | Bei `Z_print = 3,35 mm`: rastet beim Aufdrücken von vorne ein (`0,0863 mm³` Schnapp-Durchgang, `0,0000 mm³` Kollision in Endlage) | Funktionsmaß |

> **Hinweis zum physischen Passungsrisiko (`research-part-specs`)**: Die neuen Maße (`Ø 4,30 mm` Innenbohrung, `3,20 mm` Throat, `3,90 mm` Einführtrichter, `1,25 mm` Federwangen mit 2 Wandlinien und `xy_hole_compensation = 0,08 mm`) sind rechnerisch und per Volumen-Probe auf ~6× geringere Eindrückkraft ausgelegt, stellen jedoch bis zum erneuten realen Probedruck mit dem konkreten `3,5 mm`-Kabel des Benutzers (z. B. mit `models/kabelkanal-3-5mm-teststueck-35mm.stl`) einen **Konstruktions-Schätzwert** dar.

## 4. Druckorientierung & OrcaSlicer-Nachweis (`0,00 g` Support)

- **Druckorientierung (`models/kabelkanal-3-5mm.stl`, `models/kabelkanal-3-5mm-print.3mf`)**:
  Die geschlossene Sichtseite (`vorne`) liegt auf der Textured-PEI-Bauplatte (`Z_print = 0,00 mm`), während die abgeflachte, geschlitzte Rückseite (`hinten`) und die Überwurf-Kappentasche nach oben (`+Z_print = 5,20 mm`) öffnen und per `ironing_type = top` geglättet werden. Dadurch entsteht im Druck **keine geschlossene Tunneldecke über einem offenen Bodenschlitz**, sodass OrcaSlicer `2.3.1` mit `enable_support=1` und `support_type=tree(auto)` exakt **`0,00 g` Support (`0` Stützpfade)** erzeugt.
- **Einbaulage (`models/kabelkanal-3-5mm-view.3mf`, `docs/images/kabelkanal-3-5mm-presentation.png`)**:
  Um `180°` um die X-Achse gedreht (`_to_installed_wall_mesh`), sodass die flache, geschlitzte Rückseite (`hinten`) an der Wand anliegt (`Z_wall = 0,00 mm`), die geschlossene Sichtseite (`vorne`) zum Betrachter zeigt (`Z_wall = +5,20 mm`) und das Folgesegment in einem Zug von vorne (`-Z_wall`) auf Kabel und Sattelzapfen gedrückt wird.

