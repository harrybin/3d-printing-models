# Kabelkanal 3,5 mm (schlankes Profil, Öffnung hinten, von vorne aufsteckbar, weiß) — Maß- und Konstruktionsdokumentation

## 1. Aufgabenstellung & Randbedingungen

- **Bauteil**: Maximal langer, schlanker, weißer Kabelkanal (`kabelkanal-3-5mm`) für ein Rundkabel mit **Ø 3,50 mm**, Rückseite abgeflacht mit **rückseitiger Kabel-Einclipsöffnung (`hinten`)**, komplett **geschlossener Sichtseite (`vorne`)** und **ohne Stützen (`0,00 g` Support bei `enable_support=1, tree(auto)`)** auf dem Anycubic Kobra S1 Combo + ACE Pro druckbar.
- **Steckverbindung („von vorne in einem Zug aufstecken")**: Schlanke **Von-vorne-Aufrast-Überblattung (`Saddle-Hood-Joint`)** ohne doppelwandige koaxiale Muffe. Wenn Segment 1 bereits an der Wand / auf dem Kabel sitzt, wird Segment 2 **von vorne in einem Zug (`-Z` in Einbaulage)** gleichzeitig auf das Kabel und über den Sattelzapfen von Segment 1 gedrückt. Ein vertikaler T-Quersteg (`KEY_RIB_PROTRUSION = 0,34 mm`) verriegelt beide Kanäle formschlüssig gegen axiales Auseinanderziehen (`±X`), während eine horizontale Rastleiste (`SNAP_BEAD_PROTRUSION = 0,22 mm`) das Abheben nach vorne (`+Z`) sichert.
- **Druckbettlimit & 4 Modul-Varianten**: Anycubic Kobra S1 (`250,0 mm × 250,0 mm`). Alle **vier Varianten** nutzen die maximale gerade Bettlänge entlang der X-Achse (`242,00 mm` Gesamtlänge bei `4,00 mm` Randabstand je Seite) und liegen gemeinsam auf **Platte 1** von `models/kabelkanal-3-5mm-print.3mf`:
  1. `models/kabelkanal-3-5mm-mitte-beidseitig.stl` (sowie `models/kabelkanal-3-5mm.stl`): **Mittelkanal** mit Verbindung links (`-X` Aufrast-Sattel) und rechts (`+X` Überwurf-Kappe), `242,00 mm` Gesamtlänge (`232,00 mm` Netto-Rastermaß).
  2. `models/kabelkanal-3-5mm-abschluss-links.stl`: **Abschlusskanal für links**, links (`-X`) glatter Abschluss ohne Sattel-Abstufung (bei durchgehender Kabelbohrung und Rückseitenschlitz), Verbindung nur rechts (`+X` Überwurf-Kappe), volle **`242,00 mm` nutzbare Kanallänge**.
  3. `models/kabelkanal-3-5mm-abschluss-rechts.stl`: **Abschlusskanal für rechts**, Verbindung nur links (`-X` Aufrast-Sattel), rechts (`+X`) glatter Abschluss ohne Überwurf-Aussparung (bei durchgehender Kabelbohrung und Rückseitenschlitz), `242,00 mm` Gesamtlänge (`232,00 mm` Sichtprofil + `10,00 mm` Sattel).
  4. `models/kabelkanal-3-5mm-einzeln-ohne-verbindung.stl`: **Einzel-/Kurzkanal ohne Verbindungen** (weder links `-X` noch rechts `+X`), auf ausdrücklichen Benutzerwunsch ebenfalls mit **maximaler Druckplattenlänge (`242,00 mm`)**.

## 2. Recherche wiederverwendbarer 3D-Assets (`research-reusable-3d-assets`)

- **Ergebnis**: Funktionales, parametrisches Konstruktionsbauteil ohne organisches/skulpturales Freiform-Motiv. Standard-Kabelkanäle sind für ein einzelnes `3,5 mm`-Kabel zu breit/hoch (`>= 10 × 10 mm`) und besitzen keine einteilige Von-vorne-Aufrast-Überblattung.
- **Entscheidung**: Vollparametrische Eigenkonstruktion in Python (`scripts/kabelkanal_3_5mm.py`) gemäß `create-ascii-stl`, `reversible-fdm-joints` und `orcaslicer-support-minimization`. Lizenz/Provenienz: Eigenkonstruktion Repository (`MIT`).

## 3. Maß- und Toleranztabelle (`research-part-specs`)

| Parameter | Symbol im Skript | Maß [mm] | Herkunft / Begründung | Vertrauen |
| --- | --- | ---: | --- | --- |
| Kabel-Nenndurchmesser | `CABLE_DIAMETER` | `3,50` | Benutzervorgabe („für ein Kabel der Stärke 3,5mm") | Bestätigt (Benutzer) |
| Radialspiel Kabelkanal | `CABLE_RADIAL_CLEARANCE` | `0,18` | `+0,36 mm` Durchmesserspiel (`Ø 3,86 mm`) für spannungsfreies Einlegen | FDM-Erfahrungswert |
| Innenbohrung Kabelkanal | `2 * BORE_RADIUS` | `3,86` (`R = 1,93`) | Zentrum bei `Z_print = 3,05 mm` (`Z_wall = 2,15 mm`), `1,12 mm` geschlossene Sichtwand vorne | Abgeleitet |
| Schlankes Außenprofil (`Breite × Höhe`) | `OUTER_WIDTH × OUTER_HEIGHT` | `7,20 × 5,20` | Gegenüber `10,80 × 6,80 mm` um `33 %` schmaler und `24 %` flacher durch Wegfall der Koaxialmuffe | Benutzervorgabe („sehr massiv" -> schlank) |
| Sichtseite vorne (`Z_print = 0,00 mm`) | `FRONT_BEVEL` | `1,20 × 45°` | Geschlossene, glatte Sichtfront (`4,80 mm` Stirnspiegel + beidseitig `1,20 mm × 45°` Fase, selbsttragend) | Stützfrei-Nachweis |
| Abgeflachte Rückseite (`hinten`, `Z_print = 5,20 mm`) | `Y_OUTER - Y_ENTRY` | `2 × 2,05` | Zwei plane Wandauflagestreifen (`Y ∈ [-3,60, -1,55]` und `[+1,55, +3,60]`), im Druck per `ironing_type=top` geglättet | Konstruktionsmaß |
| Rückseitige Einclips-Engstelle (Throat) | `SLOT_THROAT_WIDTH` | `2,75` (`±1,375`) | `0,75 mm` Hinterschnitt auf der abgeflachten Rückseite (`hinten`) hält das `3,50 mm`-Kabel sicher im Kanal | Benutzervorgabe („Öffnung hinten") |
| Rückseitige Einclips-Fase (Trichter) | `SLOT_ENTRY_WIDTH` | `3,10` (`±1,55`) | Selbstzentrierender Einführtrichter auf der Rückseite zum Eindrücken des Kabels | Funktionsmaß |
| Gesamtlänge / Netto-Verlegelänge | `MAX_TOTAL_LENGTH` / `BODY_NET_LENGTH` | `242,00` / `232,00` | `250,00 mm` Druckbett minus `2 × 4,00 mm` Rand; alle `4` Varianten je `242,00 mm` lang auf Platte 1 (`Y = 98 / 116 / 134 / 152 mm`) | Bettlimit Kobra S1 |
| Überblattungslänge (Sattel / Kappe) | `CONNECTOR_LENGTH` / `SOCKET_DEPTH` | `10,00` / `10,10` | `-X` innerer Aufrast-Sattel (`10,00 mm`), `+X` äußere Überwurf-Kappe (`10,10 mm`, `0,10 mm` Axialspiel) | FDM-Passung |
| Sattelbreite / Wangenstärke Kappe | `2 * Y_SADDLE_BASE` | `4,80` (`±2,40`) | Erlaubt `1,04 mm` starke äußere Überwurf-Wangen innerhalb der `7,20 mm` Gesamtbreite (`0,16 mm` Flankenspiel) | FDM-Passung |
| Vertikaler T-Quersteg (`±X`-Formschluss) | `KEY_RIB_PROTRUSION` / `KEY_SLOT_DEPTH` | `0,34` / `0,36` | Bei `5,00 mm` vor der Schulter: verhindert axiales Auseinanderziehen (`1,59 mm³` Formschluss-Eingriff) | Funktionsmaß |
| Horizontale Rastleiste (`±Z`-Click-Lock) | `SNAP_BEAD_PROTRUSION` / `SNAP_GROOVE_DEPTH` | `0,22` / `0,24` | Rastet beim Aufdrücken von vorne hörbar ein (`0,068 mm³` Schnapp-Durchgang, `0,0000 mm³` Kollision in Endlage) | Funktionsmaß |

## 4. Druckorientierung & OrcaSlicer-Nachweis (`0,00 g` Support)

- **Druckorientierung (`models/kabelkanal-3-5mm.stl`, `models/kabelkanal-3-5mm-print.3mf`)**:
  Die geschlossene Sichtseite (`vorne`) liegt auf der Textured-PEI-Bauplatte (`Z_print = 0,00 mm`), während die abgeflachte, geschlitzte Rückseite (`hinten`) und die Überwurf-Kappentasche nach oben (`+Z_print = 5,20 mm`) öffnen und per `ironing_type = top` geglättet werden. Dadurch entsteht im Druck **keine geschlossene Tunneldecke über einem offenen Bodenschlitz**, sodass OrcaSlicer `2.3.1` mit `enable_support=1` und `support_type=tree(auto)` exakt **`0,00 g` Support (`0` Stützpfade)** erzeugt.
- **Einbaulage (`models/kabelkanal-3-5mm-view.3mf`, `docs/images/kabelkanal-3-5mm-presentation.png`)**:
  Um `180°` um die X-Achse gedreht (`_to_installed_wall_mesh`), sodass die flache, geschlitzte Rückseite (`hinten`) an der Wand anliegt (`Z_wall = 0,00 mm`), die geschlossene Sichtseite (`vorne`) zum Betrachter zeigt (`Z_wall = +5,20 mm`) und das Folgesegment in einem Zug von vorne (`-Z_wall`) auf Kabel und Sattelzapfen gedrückt wird.

