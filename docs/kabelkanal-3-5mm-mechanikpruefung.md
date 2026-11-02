# Kabelkanal 3,5 mm — Mechanik-, Steck- und Druckvalidierung (`PASS`)

## 1. Netz- und Geometrieprüfung (`scripts/mesh_tool.py validate` & `overhang`)

- **Datei**: `models/kabelkanal-3-5mm.stl` (ASCII STL)
- **Abmessungen (`extents`)**: `242,000 mm × 7,200 mm × 5,200 mm` (`bounds`: `X ∈ [-121,00, +121,00]`, `Y ∈ [-3,60, +3,60]`, `Z ∈ [0,00, 5,20]`)
- **Netzstatus**:
  - `watertight`: `True` (`PASS`)
  - `winding_consistent`: `True` (`PASS`)
  - `euler_number`: `2` (geschlossener Körper ohne Fehlbohrungen, `PASS`)
  - `degenerate_faces`: `0` (`PASS`)
  - `facets`: `2148`
- **Überhangprüfung (`mesh_tool.py overhang models/kabelkanal-3-5mm.stl`)**:
  - `bed contact area`: `1110,06 mm²`
  - `unsupported area (> 45°)`: `4,85 mm² (0,1 %)` (nur Mikro-Übergangsfacetten der Schnapp-Rastleiste)
  - `ceilings (>= 89°)`: `0,00 mm²` (`max ceiling short span = 0,00 mm`, `PASS`)

## 2. Volumen-Probes & Von-vorne-Aufrast-Prüfung (`verify_cable_channel_and_joint`)

Alle Prüfungen werden bei jedem Lauf von `scripts/kabelkanal_3_5mm.py` automatisiert durchgeführt und in `build/kabelkanal-3-5mm/verification_report.json` protokolliert:

| Prüfpunkt | Sollwert | Istwert | Status |
| --- | --- | --- | --- |
| Geschlossene Sichtseite vorne (`front_wall_probe`, `Z ∈ [0,15, 0,85]`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Rückseitiger Kabelschlitz (`rear_slot_probe`, `Z ∈ [4,40, 5,20]`) | `0,00 mm³` (durchgehend offen) | `0,0000 mm³` | **PASS** |
| Abgeflachte Rückseiten-Auflageflächen (`rear_flange_probe`) | `8,40 mm³` (100 % massiv) | `8,4000 mm³` | **PASS** |
| Durchgehende `Ø 3,50 mm`-Kabel-Freigängigkeit über 2 Segmente (`474 mm`) | `0,0000 mm³` Kollision | `0,0000 mm³` | **PASS** |
| Kollisionsvolumen in verrasteter Endlage (`dz = 0,00 mm`, `dx = 232,00 mm`) | `0,0000 mm³` | `0,0000 mm³` | **PASS** |
| Elastischer Schnapp-Durchgang beim Aufdrücken von vorne (`25` Schritte) | `0,02 .. 2,50 mm³` (federnde Rastleiste) | `0,0684 mm³` | **PASS** |
| Axialer Formschluss des vertikalen T-Querstegs (`dx = +232,50 mm` Zugprobe) | `> 0,20 mm³` | `1,5918 mm³` | **PASS** |

## 3. OrcaSlicer-Druckvalidierung (`models/kabelkanal-3-5mm-print.3mf`)

- **Slicer**: OrcaSlicer CLI `2.3.1`
- **Drucker / Düse / Bett**: `Anycubic Kobra S1 0.4 nozzle`, `Textured PEI Plate` (`250 × 250 mm`)
- **Prozessprofil**: `0.20mm Standard @Anycubic Kobra S1 0.4 nozzle` mit `layer_height = 0.16 mm`, `seam_position = random`, `ironing_type = top`, `wall_loops = 3`, `sparse_infill_density = 25%`
- **Filament (Slot 1)**: `Anycubic PLA White` (`#F4F5F7`)
- **Stützstruktur-Einstellung**: `enable_support = 1`, `support_type = tree(auto)`, `support_top_z_distance = 0.16 mm`, `support_bottom_z_distance = 0.16 mm`
- **Plattenbelegung (Platte 1)**: `2×` `kabelkanal-3-5mm` (`je 242,00 mm`, zusammen **`464,00 mm` Netto-Verlegelänge**)
- **Verifizierte Slicer-Ergebnisse**:
  - **Druckzeit**: `32 min 03 s` (`1923 s`)
  - **Filamentverbrauch gesamt**: `12,80 g` (`4292,61 mm` / `10320 mm³`)
  - **Stützmaterial (`supportFilamentGrams`)**: **`0,00 g` (`0,00 mm`, `0` Stützpfad-Segmente)** — **PASS (100 % stützfrei)**
