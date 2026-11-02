# Kabelkanal 3,5 mm — Mechanik-, Steck- und Druckvalidierung (`PASS`)

## 1. Netz- und Geometrieprüfung aller 4 Varianten (`scripts/mesh_tool.py validate` & `overhang`)

Alle 4 Varianten werden aus derselben parametrischen Funktion `build_channel_manifold(..., left_connector=..., right_connector=..., total_length_override=242.0)` in `scripts/kabelkanal_3_5mm.py` erzeugt (`X ∈ [-121,00, +121,00]`, `Y ∈ [-3,60, +3,60]`, `Z ∈ [0,00, 5,20]`):

| Variante / STL-Datei | Links (`-X`) | Rechts (`+X`) | Abmessungen [mm] | Facetten | Volumen [mm³] | Watertight / Euler / Degenerate |
| --- | --- | --- | --- | ---: | ---: | --- |
| `models/kabelkanal-3-5mm-abschluss-links.stl` | Glatter Abschluss | Überwurf-Kappe (`+X`) | `242,0 × 7,2 × 5,2` | `1042` | `5457,37` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-mitte-beidseitig.stl` (`kabelkanal-3-5mm.stl`) | Aufrast-Sattel (`-X`) | Überwurf-Kappe (`+X`) | `242,0 × 7,2 × 5,2` | `2340` | `5345,80` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-abschluss-rechts.stl` | Aufrast-Sattel (`-X`) | Glatter Abschluss | `242,0 × 7,2 × 5,2` | `1490` | `5486,70` | `True` / `2` / `0` (**PASS**) |
| `models/kabelkanal-3-5mm-einzeln-ohne-verbindung.stl` | Glatter Abschluss | Glatter Abschluss | `242,0 × 7,2 × 5,2` | `192` | `5598,27` | `True` / `2` / `0` (**PASS**) |

- **Überhangprüfung (`mesh_tool.py overhang`)**:
  - `ceilings (>= 89°)`: `0,00 mm²` (`max ceiling short span = 0,00 mm`, `PASS`)
  - Alle vier Varianten drucken auf der geschlossenen, angefasten Sichtseite (`Z_print = 0,00 mm`) mit nach oben offenem Rückseitenschlitz (`Z_print = 5,20 mm`) zu **100 % stützfrei**.

## 2. Volumen-Probes & Von-vorne-Aufrast-Prüfung (`verify_cable_channel_and_joint`)

Alle Prüfungen werden bei jedem Lauf von `scripts/kabelkanal_3_5mm.py` automatisiert für alle 4 Varianten durchgeführt und in `build/kabelkanal-3-5mm/verification_report.json` protokolliert:

| Prüfpunkt | Sollwert | Istwert | Status |
| --- | --- | --- | --- |
| Geschlossene Sichtseite vorne (`front_wall_probe`, `Z ∈ [0,15, 0,85]`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Rückseitiger Kabelschlitz (`rear_slot_probe`, `Z ∈ [4,40, 5,20]`) | `0,00 mm³` (durchgehend offen) | `0,0000 mm³` | **PASS** |
| Abgeflachte Rückseiten-Auflageflächen (`rear_flange_probe`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Enden-Probes (`left_outer_cheek_probe` / `right_inner_hood_probe`) für alle 4 Varianten | Sattel/Kappe `0,00 mm³`, glattes Ende `7,50` bzw. `6,21 mm³` | exakt bestätigt | **PASS** |
| Durchgehende `Ø 3,50 mm`-Kabel-Freigängigkeit in allen 4 Varianten (`242 mm`) & 2er-Verbund (`474 mm`) | `0,0000 mm³` Kollision | `0,0000 mm³` | **PASS** |
| 3er-Kette (`abschluss-links` + `mitte-beidseitig` + `abschluss-rechts`) in Endlage | `0,0000 mm³` Kollision | `0,0000 mm³` / `0,0000 mm³` | **PASS** |
| Elastischer Schnapp-Durchgang beim Aufdrücken von vorne (`25` Schritte) | `0,02 .. 2,50 mm³` (federnde Rastleiste) | `0,0684 mm³` | **PASS** |
| Axialer Formschluss des vertikalen T-Querstegs (`dx = +232,50 mm` Zugprobe) | `> 0,20 mm³` | `1,5918 mm³` | **PASS** |

## 3. OrcaSlicer-Druckvalidierung (`models/kabelkanal-3-5mm-print.3mf`)

- **Slicer**: OrcaSlicer CLI `2.3.1`
- **Drucker / Düse / Bett**: `Anycubic Kobra S1 0.4 nozzle`, `Textured PEI Plate` (`250 × 250 mm`)
- **Prozessprofil**: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` mit `layer_height = 0.16 mm`, `seam_position = random`, `ironing_type = top`, `wall_loops = 3`, `sparse_infill_density = 25%`
- **Filament (Slot 1)**: `Anycubic PLA White` (`#F4F5F7`)
- **Stützstruktur-Einstellung**: `enable_support = 1`, `support_type = tree(auto)`, `support_top_z_distance = 0.16 mm`, `support_bottom_z_distance = 0.16 mm`
- **Plattenbelegung (Platte 1)**: **Alle 4 Varianten** (`abschluss-links` bei `Y = 98 mm`, `mitte-beidseitig` bei `Y = 116 mm`, `abschluss-rechts` bei `Y = 134 mm`, `einzeln-ohne-verbindung` bei `Y = 152 mm`; je `242,00 mm` Maximallänge, `10,80 mm` lichter Abstand zwischen den Kanälen)
- **Verifizierte Slicer-Ergebnisse**:
  - **Druckzeit**: `1 h 01 min 44 s` (`3704 s`)
  - **Filamentverbrauch gesamt**: `26,23 g` (`8794,00 mm` / `21150 mm³`)
  - **Stützmaterial (`supportFilamentGrams`)**: **`0,00 g` (`0,00 mm`, `0` Stützpfad-Segmente)** — **PASS (100 % stützfrei)**
