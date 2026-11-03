# Kabelkanal 3,5 mm — Mechanik-, Steck- und Druckvalidierung (`PASS`)

## 1. Netz- und Geometrieprüfung aller 5 Varianten in `models/kabelkanal-3-5mm-print.3mf` & `models/kabelkanal-3-5mm-view.3mf`

Alle 5 Druckvarianten werden aus derselben parametrischen Funktion `build_channel_manifold(..., left_connector=..., right_connector=..., total_length_override=...)` in `scripts/kabelkanal_3_5mm.py` erzeugt und direkt in die beiden 3MF-Deliverables (`models/kabelkanal-3-5mm-print.3mf` und `models/kabelkanal-3-5mm-view.3mf`) geschrieben (keine separaten STL-Dateien; `Y ∈ [-3,40, +3,40]`, `Z ∈ [0,00, 5,40]`, Innenbohrung **`Ø 4,30 mm`**, Rückseitenschlitz **`3,20 mm`** mit **`3,90 mm`** Einführtrichter):

| Variante (Objekt in `-print.3mf` / `-view.3mf`) | Links (`-X`) | Rechts (`+X`) | Abmessungen [mm] | Facetten | Volumen [mm³] | Watertight / Euler / Degenerate |
| --- | --- | --- | --- | ---: | ---: | --- |
| `kabelkanal-3-5mm-abschluss-links` | Glatter Abschluss | Überwurf-Kappe (`+X`) | `242,0 × 6,8 × 5,4` | `1050` | `4630,15` | `True` / `2` / `0` (**PASS**) |
| `kabelkanal-3-5mm-mitte-beidseitig` | Aufrast-Sattel (`-X`) | Überwurf-Kappe (`+X`) | `242,0 × 6,8 × 5,4` | `2326` | `4526,41` | `True` / `2` / `0` (**PASS**) |
| `kabelkanal-3-5mm-abschluss-rechts` | Aufrast-Sattel (`-X`) | Glatter Abschluss | `242,0 × 6,8 × 5,4` | `1468` | `4637,55` | `True` / `2` / `0` (**PASS**) |
| `kabelkanal-3-5mm-einzeln-ohne-verbindung` | Glatter Abschluss | Glatter Abschluss | `242,0 × 6,8 × 5,4` | `192` | `4741,30` | `True` / `2` / `0` (**PASS**) |
| `kabelkanal-3-5mm-10cm-rechts` | Glatter Abschluss | Überwurf-Kappe (`+X`) | `100,0 × 6,8 × 5,4` | `1056` | `1848,07` | `True` / `2` / `0` (**PASS**) |

- **Überhangprüfung (`mesh_tool.py overhang`) & Ursachenbehebung für das 3-zu-2-Supportverhalten**:
  - **Ursache des bisherigen 3-zu-2-Unterschieds**:
    1. *Geometrisch*: Die **3 Varianten mit `+X`-Überwurf-Kappe** (`abschluss-links`, `mitte-beidseitig`, `10cm-rechts`) hatten bei `Y_SADDLE_SPINE = 1,45 mm` (`y_spine_hood = 1,57 mm`) auf `Z = 0,00 mm` nur `2,30 - 1,57 = 0,73 mm` schmale First-Layer-Auflagestege (`< 2` Extrusionsbreiten = nur `1` Kontaktpunkt im First Layer), während die **2 Varianten mit `-X`-Aufrast-Sattel** (`mitte-beidseitig`, `abschluss-rechts`) an der Sattelspitze eine `39,2°`-Überhangschräge (`nz = -0,775`) besaßen.
    2. *3MF-Prozess-Metadaten*: In `Metadata/project_settings.config` standen die Prozess-Overrides fälschlich in `different_settings_to_system[1]` statt in `different_settings_to_system[0]`, und die Datei trug `version = 02.06.00.51` mit 93 neuen OrcaSlicer-2.4.2-Schlüsseln. Beim Öffnen in AnycubicSlicerNext `2.0.0.3` wurden deshalb die Prozess-Overrides (`seam_position=random`, `ironing_type=top`, `support_threshold_angle=30`, `support_critical_regions_only=1`) verworfen (`SupportSpotsGenerator` lief für die 3 Objekte mit `<metadata key="enable_support" value="1"/>`).
  - **Lösung**:
    1. `Y_SADDLE_SPINE = 1,15 mm` (`y_spine_hood = 1,27 mm`) verbreitert die First-Layer-Auflage der `+X`-Überwurf-Kappe auf **`1,03 mm` je Seite** (`>= 2` volle Extrusionslinien), `Z_SADDLE_SHOULDER = 1,68 mm` + `1,10 * delta_y_key` sowie `±0,42 / ±0,48 mm` Rastleisten-Rampen heben alle Verbinder-Überhänge auf **`>= 50,8° .. 69,4°` gegen die Horizontale** (`<= 39,2°` von der Vertikalen; Gesamtbauteil `<= 45,0°` von der Vertikalen).
    2. `different_settings_to_system[0]` speichert nun alle 23 Prozess-Overrides (`seam_position=random`, `ironing_type=top` [„Alle Oberflächen"], `layer_height=0.16`, `enable_support=1`, `support_type=tree(auto)` usw.) im `2.0.0.3`-kompatiblen Schema (`print_settings_id = "0.16mm Standard @Anycubic Kobra S1 0.4 nozzle"`).
  - `unsupported area (> 45° from vertical)`: **`0,00 mm²` (`0,0 %`)** auf allen 5 Varianten.
  - `ceilings (>= 89°)`: **`0,00 mm²`** (`max ceiling short span = 0,00 mm`, `PASS`).

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
| Elastischer Schnapp-Durchgang beim Aufdrücken von vorne (`25` Schritte) | `0,02 .. 2,50 mm³` (federnde Rastleiste) | `0,0527 mm³` | **PASS** |
| Axialer Formschluss des vertikalen T-Querstegs (`dx = +232,50 mm` Zugprobe) | `> 0,20 mm³` | `0,5222 mm³` | **PASS** |
| Nachgiebigkeit Rückseitenschlitz (`slot_compliance` ggü. v1) | `< 0,25` Kraftverhältnis | `stiffness_ratio = 0,419`, `force_ratio = 0,168` (~6× leichter), `energy_ratio = 0,067` (~15× leichter) | **PASS (CAD; Praxistest offen)** |

## 3. OrcaSlicer-Druckvalidierung (`models/kabelkanal-3-5mm-print.3mf`)

- **Slicer**: OrcaSlicer CLI `2.3.1` & AnycubicSlicerNext `2.0.0.3` Schema-Kompatibilität
- **Drucker / Düse / Bett**: `Anycubic Kobra S1 0.4 nozzle`, `Textured PEI Plate` (`250 × 250 mm`)
- **Prozessprofil**: `0.16mm Standard @Anycubic Kobra S1 0.4 nozzle` mit `layer_height = 0.16 mm`, `seam_position = random` (**Naht: Zufall**), `ironing_type = top` (**Bügeln: Alle Oberflächen**, `15` Bügel-Pfade im G-Code), `wall_loops = 2`, `sparse_infill_density = 20%`, `xy_hole_compensation = 0.08 mm`, vollständig hinterlegt in `different_settings_to_system[0]`
- **Filament (Slot 1)**: `Anycubic PLA White` (`#F4F5F7`)
- **Stützstruktur-Einstellung**: `enable_support = 1`, `support_type = tree(auto)`, `support_top_z_distance = 0.16 mm`, `support_bottom_z_distance = 0.16 mm`
- **Plattenbelegung (Platte 1)**: **Alle 5 Varianten** (`abschluss-links` 242 mm bei `Y = 89 mm`, `mitte-beidseitig` 242 mm bei `Y = 107 mm`, `abschluss-rechts` 242 mm bei `Y = 125 mm`, `einzeln-ohne-verbindung` 242 mm bei `Y = 143 mm`, `10cm-rechts` 100 mm bei `Y = 161 mm`; `11,20 mm` lichter Abstand zwischen den Kanälen)
- **Verifizierte Slicer-Ergebnisse**:
  - **Druckzeit**: `1 h 00 min 17 s` (`3617 s`)
  - **Filamentverbrauch gesamt**: `24,81 g` (`8318,06 mm` / `20010 mm³`)
  - **Stützmaterial (`supportFilamentGrams`)**: **`0,00 g` (`0,00 mm`, `0` Stützpfad-Segmente auf allen 5 Varianten)** — **PASS (100 % stützfrei)**
