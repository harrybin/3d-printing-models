# Kabelkanal 3,5 mm — Mechanik-, Steck- und Druckvalidierung (`PASS`)

## 1. Netz- und Geometrieprüfung aller 5 Varianten + 35 mm Prüfstück (`scripts/mesh_tool.py validate` & `overhang`)

Alle 5 Druckvarianten sowie das `35,0 mm`-Passungs-Prüfstück werden aus derselben parametrischen Funktion `build_channel_manifold(..., left_connector=..., right_connector=..., total_length_override=...)` in `scripts/kabelkanal_3_5mm.py` erzeugt (`Y ∈ [-3,40, +3,40]`, `Z ∈ [0,00, 5,40]`, Innenbohrung **`Ø 4,30 mm`**, Rückseitenschlitz **`3,20 mm`** mit **`3,90 mm`** Einführtrichter):

| Variante / STL-Datei | Links (`-X`) | Rechts (`+X`) | Abmessungen [mm] | Facetten | Volumen [mm³] | Watertight / Euler / Degenerate |
| --- | --- | --- | --- | ---: | ---: | --- |
| `models/kabelkanal-3-5mm-abschluss-links.stl` | Glatter Abschluss | Überwurf-Kappe (`+X`) | `242,0 × 6,8 × 5,4` | `1038` | `4621,64` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-mitte-beidseitig.stl` (`kabelkanal-3-5mm.stl`) | Aufrast-Sattel (`-X`) | Überwurf-Kappe (`+X`) | `242,0 × 6,8 × 5,4` | `2318` | `4527,33` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-abschluss-rechts.stl` | Aufrast-Sattel (`-X`) | Glatter Abschluss | `242,0 × 6,8 × 5,4` | `1472` | `4646,99` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-einzeln-ohne-verbindung.stl` | Glatter Abschluss | Glatter Abschluss | `242,0 × 6,8 × 5,4` | `192` | `4741,30` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-10cm-rechts.stl` | Glatter Abschluss | Überwurf-Kappe (`+X`) | `100,0 × 6,8 × 5,4` | `1032` | `1839,56` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-teststueck-35mm.stl` | Aufrast-Sattel (`-X`) | Überwurf-Kappe (`+X`) | `35,0 × 6,8 × 5,4` | `2318` | `472,49` | `True` / `2` / `0` (**PASS**) |

- **Überhangprüfung (`mesh_tool.py overhang`)**:
  - `unsupported area (> 45° from vertical)`: **`0,00 mm²` (`0,0 %`)**
  - `ceilings (>= 89°)`: **`0,00 mm²`** (`max ceiling short span = 0,00 mm`, `PASS`)
  - Alle Varianten drucken auf der geschlossenen, angefasten Sichtseite (`Z_print = 0,00 mm`) mit nach oben offenem Rückseitenschlitz (`Z_print = 5,40 mm`) zu **100 % stützfrei**.

## 2. Volumen-Probes, Einclips-Elastizität & Von-vorne-Aufrast-Prüfung (`verify_cable_channel_and_joint`)

Alle Prüfungen werden bei jedem Lauf von `scripts/kabelkanal_3_5mm.py` automatisiert für alle 5 Varianten durchgeführt und in `build/kabelkanal-3-5mm/verification_report.json` protokolliert:

| Prüfpunkt | Sollwert | Istwert | Status |
| --- | --- | --- | --- |
| Geschlossene Sichtseite vorne (`front_wall_probe`, `Z ∈ [0,15, 0,85]`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Rückseitiger Kabelschlitz (`rear_slot_probe`, `Z ∈ [4,55, 5,40]`) | `0,00 mm³` (durchgehend offen) | `0,0000 mm³` | **PASS** |
| Abgeflachte Rückseiten-Auflageflächen (`rear_flange_probe`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Enden-Probes (`left_outer_cheek_probe` / `right_inner_hood_probe`) für alle 5 Varianten | Sattel/Kappe `0,00 mm³`, glattes Ende `4,50` bzw. `4,97 mm³` | exakt bestätigt | **PASS** |
| Durchgehende `Ø 3,50 mm`-Kabel- & `Ø 4,10 mm`-Prüfdorn-Freigängigkeit in der `Ø 4,30 mm`-Bohrung | `0,0000 mm³` Kollision | `0,0000 mm³` / `0,0000 mm³` | **PASS** |
| 3er-Kette (`abschluss-links` + `mitte-beidseitig` + `abschluss-rechts`) & `10cm-rechts` + `mitte-beidseitig` | `0,0000 mm³` Kollision | `0,0000 mm³` | **PASS** |
| Elastischer Schnapp-Durchgang beim Aufdrücken von vorne (`25` Schritte) | `0,02 .. 2,50 mm³` (federnde Rastleiste) | `0,0863 mm³` | **PASS** |
| Axialer Formschluss des vertikalen T-Querstegs (`dx = +232,50 mm` Zugprobe) | `> 0,20 mm³` | `0,6075 mm³` | **PASS** |
| Nachgiebigkeit Rückseitenschlitz (`slot_compliance` ggü. v1) | `< 0,25` Kraftverhältnis | `stiffness_ratio = 0,419`, `force_ratio = 0,168` (~6× leichter), `energy_ratio = 0,067` (~15× leichter) | **PASS (CAD; Praxistest offen)** |

## 3. OrcaSlicer-Druckvalidierung (`models/kabelkanal-3-5mm-print.3mf`)

- **Slicer**: OrcaSlicer CLI `2.3.1`
- **Drucker / Düse / Bett**: `Anycubic Kobra S1 0.4 nozzle`, `Textured PEI Plate` (`250 × 250 mm`)
- **Prozessprofil**: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` mit `layer_height = 0.16 mm`, `seam_position = random`, `ironing_type = top`, `wall_loops = 2`, `sparse_infill_density = 20%`, `xy_hole_compensation = 0.08 mm`
- **Filament (Slot 1)**: `Anycubic PLA White` (`#F4F5F7`)
- **Stützstruktur-Einstellung**: `enable_support = 1`, `support_type = tree(auto)`, `support_top_z_distance = 0.16 mm`, `support_bottom_z_distance = 0.16 mm`
- **Plattenbelegung (Platte 1)**: **Alle 5 Varianten** (`abschluss-links` 242 mm bei `Y = 89 mm`, `mitte-beidseitig` 242 mm bei `Y = 107 mm`, `abschluss-rechts` 242 mm bei `Y = 125 mm`, `einzeln-ohne-verbindung` 242 mm bei `Y = 143 mm`, `10cm-rechts` 100 mm bei `Y = 161 mm`; `11,20 mm` lichter Abstand zwischen den Kanälen)
- **Verifizierte Slicer-Ergebnisse**:
  - **Druckzeit**: `1 h 00 min 30 s` (`3630 s`)
  - **Filamentverbrauch gesamt**: `24,82 g` (`8320,63 mm` / `20010 mm³`)
  - **Stützmaterial (`supportFilamentGrams`)**: **`0,00 g` (`0,00 mm`, `0` Stützpfad-Segmente)** — **PASS (100 % stützfrei)**
