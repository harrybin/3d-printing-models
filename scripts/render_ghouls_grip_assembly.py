"""Render the German step-by-step guide from unchanged delivered 3MF bodies.

Run with the catalog venv. Blender renders the presentation-only translations;
Pillow adds captions, part labels and a contact sheet. No print files are written.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_ghouls_grip_exploded import digest, layout, validate_render


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "ghouls-grip-view.3mf"
WORK = ROOT / "build" / "ghouls-grip-assembly"
OUT = ROOT / "docs" / "images"
NS = {"m": "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"}
INK, TEAL = "#243447", "#007F82"
PART_STEP = {
    "chest": 2, "slider": 3, "drive-pinion": 3, "drive-skull-knob": 3,
    "lid-follower-rack": 4, "pivot-pin-follower": 4,
    "lid-transfer-input": 4, "lid-transfer-idler": 4,
    "scissor-drive-gear": 6, "platform": 7, "forearm": 7,
    "forearm-output-gear": 7,
    "hand-palm": 9, "candy-dish": 9,
    "lid": 10, "lid-crank": 10, "crank-spacer": 10,
}
for plane in (0, 1):
    for mirrored in ("False", "True"):
        PART_STEP[f"arm-{plane}-{mirrored}"] = 5
    for role in ("floor", "slider", "centre", "fixed", "slot"):
        PART_STEP[f"pivot-pin-{role}-{plane}"] = (
            8 if role in ("fixed", "slot") else 5)
for index in range(3):
    PART_STEP[f"idler-gear-{index}"] = 7
    PART_STEP[f"pivot-pin-idler-{index}"] = 7
for finger in ("thumb", "index", "middle", "ring", "little"):
    PART_STEP[f"hand-finger-{finger}"] = 9

FRAMES = (
    dict(step=2, slug="02", title="Teile vorbereiten und sortieren",
         pose="deployed", mode="inventory",
         labels=("chest", "hand-palm", "candy-dish"),
         action="42 Druckteile nach Farbe und Funktion sortieren. Schale optional.",
         check="Zusätzlich: 6 Filamentstücke Ø1,75 mm in 198 / 14 / 5 / 5 / 10 / 16 mm."),
    dict(step=3, slug="03a", title="Schlitten auf die Bodenführungen setzen",
         pose="retracted", mode="slider", labels=("slider",),
         action="Ca. 5,5 mm nach +X versetzt senkrecht aufdrücken, bis die Schnappfinger einrasten.",
         check="Geschlossener Kastenrahmen mit Querstreben: gleitet verwindungssteif ohne Aufbiegen."),
    dict(step=3, slug="03b", title="Ritzel und Totenkopf montieren",
         pose="retracted", mode="drive",
         labels=("drive-pinion", "drive-skull-knob"),
         action="Ritzel von innen durch die Vorderwand; Knauf außen auf die D-Welle.",
         check="Mit 14-mm-Filamentstift quer sichern. Knauf drehen, nicht drücken."),
    dict(step=4, slug="04", title="Folger und Deckel-Transfer einsetzen",
         pose="retracted", mode="follower",
         labels=("lid-follower-rack", "pivot-pin-follower",
                 "lid-transfer-input", "lid-transfer-idler"),
         action="Folger absenken; Folger-Pressstift (ohne Schlitz, 13,1 mm) bis fast zur Wand eindrücken.",
         check="2× Transferrad mit Zapfen axial in −X einschieben, außen mit je 5-mm-Filament sichern."),
    dict(step=5, slug="05", title="Die beiden Scherenpaare aufbauen",
         pose="retracted", mode="scissors",
         labels=("arm-0-False", "arm-1-True", "pivot-pin-floor-0",
                 "pivot-pin-slider-0", "pivot-pin-centre-0"),
         action="Ganz lang (2× Boden 21,6 mm) von innen nach außen; lang (2× Schlitten 14,4 mm) unten.",
         check="Kurz (2× Mitte 11,6 mm) in die Armkreuzungen. Obere Gelenke bleiben noch offen."),
    dict(step=6, slug="06", title="Eingangszahnrad vor dem Hubjoch einsetzen",
         pose="intermediate", mode="input",
         labels=("scissor-drive-gear",),
         action="Zahnrad von +Y auf das obere Armauge; Passstift in das Armloch setzen.",
         check="Scherenstellung 48°. Hubjoch erst danach einsetzen; oberen Pin später sichern."),
    dict(step=7, slug="07", title="Hubjoch und Unterarm vormontieren",
         pose="deployed", mode="platform",
         labels=("platform", "forearm", "forearm-output-gear",
                 "idler-gear-1", "pivot-pin-idler-1"),
         action="Unterarm zwischen die Ohren; D-Welle durchschieben, 10-mm-Querstift setzen.",
         check="3× langer Splint (Zwischenrad 14,6 mm, wie Schlittenstift) sichert die 3 Zwischenräder."),
    dict(step=8, slug="08", title="Hubjoch versetzt in die Schere einsetzen",
         pose="deployed", mode="join",
         labels=("platform", "scissor-drive-gear", "pivot-pin-fixed-1",
                 "pivot-pin-fixed-0", "pivot-pin-slot-0", "pivot-pin-slot-1"),
         action="78°: erst 3 mm versetzt absenken, dann entlang der 64°-Achslinie in Eingriff.",
         check="Oben sichern: 1× ganz lang (Zahnrad 19,6 mm) an +Y; 3× ganz kurz (10,0 mm) an den 3 übrigen Augen."),
    dict(step=9, slug="09", title="Handfläche, Finger und Schale aufstecken",
         pose="deployed", mode="hand",
         labels=("hand-palm", "hand-finger-index", "hand-finger-thumb", "candy-dish"),
         action="Handgelenk: 16-mm-Querstift. Finger: Zeige → Mittel → Ring → kleiner → Daumen.",
         check="Schale zuletzt aufstecken. Finger und Schale sind lösbar, nicht verriegelt."),
    dict(step=10, slug="10", title="Kurbel und Hülse am losen Deckel einsetzen",
         pose="intermediate", mode="lid",
         labels=("lid-crank", "crank-spacer"),
         action="In die 25-mm-Haube erst die Kurbel einlegen und 5,6 mm nach +X in die Tasche schieben.",
         check="Erst dadurch wird dahinter Platz für die 15,8-mm-Distanzhülse frei (zusammen 26,8 mm)."),
    dict(step=11, slug="11", title="Deckel ansetzen und Scharnier sichern",
         pose="intermediate", mode="hinge", labels=("lid",),
         action="108° offen: 3 mm nach hinten (+Y) versetzt absenken, danach nach vorn schieben.",
         check="Scherenstellung 48°. 198-mm-Filament von der Stirnseite durch alle Augen führen."),
    dict(step=12, slug="12", title="Ohne Last langsam prüfen",
         pose="deployed", mode="test", labels=(),
         action="Am Totenkopf ausfahren und genau rückwärts einfahren. Nicht über Endlagen drehen.",
         check="Bei Knacken, Widerstand oder Zahnüberspringen stoppen. Nicht in die Mechanik greifen."),
)
LABELS = {
    "chest": "Truhe", "slider": "Schlitten",
    "drive-pinion": "Ritzel / D-Welle", "drive-skull-knob": "Totenkopf",
    "lid-follower-rack": "Folger",
    "pivot-pin-follower": "Folger-Pressstift (ohne Schlitz)",
    "lid-transfer-input": "Transfer 1",
    "lid-transfer-idler": "Transfer 2", "arm-0-False": "Scherenpaar vorn",
    "arm-1-True": "Scherenpaar hinten",
    "pivot-pin-floor-0": "Splint ganz lang (2× Boden)",
    "pivot-pin-slider-0": "Splint lang (2× Schlitten)",
    "pivot-pin-centre-0": "Splint kurz (2× Scherenmitte)",
    "scissor-drive-gear": "Eingangszahnrad", "platform": "Hubjoch",
    "forearm": "Unterarm", "forearm-output-gear": "Abtriebsrad / D-Welle",
    "idler-gear-1": "Zwischenräder",
    "pivot-pin-idler-1": "Splint lang (3× Zwischenrad)",
    "hand-palm": "Handfläche",
    "hand-finger-index": "Zeigefinger", "hand-finger-thumb": "Daumen",
    "candy-dish": "Schale (optional)",     "lid-crank": "Deckelkurbel (11,0 mm)",
    "crank-spacer": "Distanzhülse (15,8 mm)", "lid": "Deckelbaugruppe",
    "pivot-pin-fixed-1": "Ganz lang (1× Zahnrad)",
    "pivot-pin-fixed-0": "Ganz kurz (Fest −Y)",
    "pivot-pin-slot-0": "Ganz kurz (Langloch −Y)",
    "pivot-pin-slot-1": "Ganz kurz (Langloch +Y)",
}


def selection(frame):
    mode, step = frame["mode"], frame["step"]
    if mode in ("inventory", "test"):
        return set(PART_STEP), set(PART_STEP)
    focus = {name for name, first in PART_STEP.items() if first == step}
    context = {name for name, first in PART_STEP.items() if first < step}
    if mode == "slider":
        return {"chest", "slider"}, {"slider"}
    if mode == "drive":
        return {"slider", "drive-pinion", "drive-skull-knob"}, {
            "drive-pinion", "drive-skull-knob"}
    if mode == "platform":
        return focus, focus
    if mode == "join":
        focus |= {name for name, first in PART_STEP.items() if first == 7}
        return (focus | context) - {"chest"}, focus
    if mode == "hand":
        return focus | {"forearm"}, focus
    if mode == "lid":
        return focus, focus
    if mode == "hinge":
        return set(PART_STEP), {"lid", "lid-crank", "crank-spacer"}
    return (focus | context) - {"chest"}, focus


def offset(name, frame):
    mode = frame["mode"]
    if mode == "inventory":
        return layout(name)[1]
    if mode == "slider":
        return (0, 0, 70)
    if mode == "drive":
        return (0, -65 if name.endswith("knob") else 35, 0)
    if mode == "follower":
        if name == "lid-follower-rack":
            return (0, 0, 45)
        if name == "pivot-pin-follower":
            return (0, 35, 45)
        return (45, 0 if name.endswith("input") else 15, 20)
    if mode == "scissors":
        side = -1 if name.endswith("-0") or name.startswith("arm-0") else 1
        return (0, side * (38 if name.startswith("pivot-pin") else 12), 55)
    if mode == "input":
        return (0, 45, 10)
    if mode == "platform":
        if name == "platform":
            return (0, 0, 0)
        if name == "forearm":
            return (0, -20, 45)
        return (0, 70 if name.startswith("pivot-pin") else 40, 15)
    if mode == "join":
        return (0, 0, 80) if PART_STEP[name] == 8 else (0, 0, 60)
    if mode == "hand":
        if name == "hand-palm":
            return (0, 0, 40)
        if name == "candy-dish":
            return (65, 0, 90)
        i = ("thumb", "index", "middle", "ring", "little").index(
            name.removeprefix("hand-finger-"))
        return (-35, (i - 2) * 12, 85)
    if mode == "lid":
        if name == "lid":
            return (0, 0, 0)
        return (-40 if name == "crank-spacer" else 0, -35, -25)
    if mode == "hinge":
        return (0, 3, 60)
    return (0, 0, 0)


def render_all():
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector
    from build_ghouls_grip_blender_scene import _reset_scene, _transform_vertex

    _reset_scene()
    with ZipFile(SOURCE) as archive:
        root = ET.fromstring(archive.read("3D/3dmodel.model"))
    resources = {obj.get("id"): obj for obj in root.findall("m:resources/m:object", NS)}
    bases = root.findall("m:resources/m:basematerials/m:base", NS)
    colours = []
    for base in bases:
        value = base.get("displaycolor").removeprefix("#")
        colours.append(tuple(int(value[i:i+2], 16) / 255 for i in (0, 2, 4)) + (1,))
    poses = {pose: {} for pose in ("deployed", "intermediate", "retracted")}
    for item in root.findall("m:build/m:item", NS):
        node = resources[item.get("objectid")]
        pose, _, name = node.get("name", "").partition("-")
        if pose not in poses:
            continue
        vertices = [
            _transform_vertex(tuple(float(v.get(axis)) for axis in ("x", "y", "z")),
                              item.get("transform"))
            for v in node.findall("m:mesh/m:vertices/m:vertex", NS)
        ]
        faces = [tuple(int(t.get(axis)) for axis in ("v1", "v2", "v3"))
                 for t in node.findall("m:mesh/m:triangles/m:triangle", NS)]
        mesh = bpy.data.meshes.new(f"{pose}_{name}")
        mesh.from_pydata(vertices, [], faces)
        mesh.update()
        obj = bpy.data.objects.new(f"frozen_{pose}_{name}", mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.color = colours[int(node.get("pindex", "0"))]
        obj["original_color"] = obj.color[:]
        obj.hide_select = True
        obj.hide_render = True
        poses[pose][name] = obj
    for pose, parts in poses.items():
        if set(parts) != set(PART_STEP):
            raise ValueError(f"Unexpected source BOM for {pose}")
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    shade = scene.display.shading
    shade.light, shade.color_type = "STUDIO", "OBJECT"
    shade.show_shadows = True
    shade.show_cavity = True
    shade.cavity_type = "BOTH"
    shade.curvature_ridge_factor = 1.5
    shade.curvature_valley_factor = 1.2
    shade.show_specular_highlight = True
    scene.render.film_transparent = True
    scene.display.render_aa = "32"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 850
    scene.render.resolution_percentage = 100
    camera_data = bpy.data.cameras.new("assembly_camera")
    camera = bpy.data.objects.new("assembly_camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type, camera_data.clip_end = "ORTHO", 10000
    WORK.mkdir(parents=True, exist_ok=True)
    evidence = {}
    for frame in FRAMES:
        selected, focus = selection(frame)
        projections = []
        for panel in (0, 1):
            pose = "retracted" if frame["mode"] == "test" and panel == 0 else frame["pose"]
            parts = poses[pose]
            for other_pose in poses.values():
                for obj in other_pose.values():
                    obj.hide_render = True
            for name in selected:
                obj = parts[name]
                obj.hide_render = False
                obj.location = Vector(offset(name, frame) if panel == 0 and name in focus else (0, 0, 0))
                # Neutral context makes the new parts readable without changing their material colors.
                obj.color = obj["original_color"] if name in focus else (0.47, 0.53, 0.57, 1)
            bpy.context.view_layer.update()
            corners = [parts[name].matrix_world @ Vector(c)
                       for name in selected for c in parts[name].bound_box]
            low = Vector(tuple(min(p[i] for p in corners) for i in range(3)))
            high = Vector(tuple(max(p[i] for p in corners) for i in range(3)))
            center = (low + high) / 2
            direction = Vector((700, -1100, 1300))
            if frame["mode"] in ("platform", "input", "join"):
                direction = Vector((600, 1200, 700))
            if frame["mode"] == "lid":
                direction = Vector((-800, -1300, -600))
            camera.location = center + direction
            camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            bpy.context.view_layer.update()
            inv = camera.matrix_world.inverted()
            projected = [inv @ p for p in corners]
            width = max(p.x for p in projected) - min(p.x for p in projected)
            height = max(p.y for p in projected) - min(p.y for p in projected)
            camera_data.ortho_scale = max(width, height * 1100 / 850) * 1.23
            camera.location += camera.rotation_euler.to_matrix() @ Vector((
                (max(p.x for p in projected) + min(p.x for p in projected)) / 2,
                (max(p.y for p in projected) + min(p.y for p in projected)) / 2, 0))
            bpy.context.view_layer.update()
            points = {}
            for name in selected:
                obj = parts[name]
                p = obj.matrix_world @ (sum((Vector(c) for c in obj.bound_box), Vector()) / 8)
                screen = world_to_camera_view(scene, camera, p)
                points[name] = [screen.x * 1100, (1 - screen.y) * 850]
            for corner in corners:
                point = world_to_camera_view(scene, camera, corner)
                if not 0 <= point.x <= 1 or not 0 <= point.y <= 1:
                    raise ValueError(f"Clipped body in {frame['slug']}")
            path = WORK / f"{frame['slug']}-{panel}.png"
            scene.render.filepath = str(path)
            scene.render.image_settings.file_format = "PNG"
            bpy.ops.render.render(write_still=True)
            projections.append(points)
        evidence[frame["slug"]] = {
            "parts": sorted(selected), "focus": sorted(focus),
            "pose": frame["pose"], "panels": projections,
        }
    (WORK / "projection.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")


def compose_all():
    from PIL import Image, ImageDraw, ImageFont

    def font(size, bold=False):
        path = Path("C:\\Windows\\Fonts") / ("segoeuib.ttf" if bold else "segoeui.ttf")
        return ImageFont.truetype(str(path) if path.exists() else
                                  ("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)

    evidence = json.loads((WORK / "projection.json").read_text(encoding="utf-8"))
    outputs = []
    for frame in FRAMES:
        image = Image.new("RGB", (2400, 1420), "#F3F6F7")
        draw = ImageDraw.Draw(image)
        draw.rectangle((0, 0, 2400, 12), fill=TEAL)
        draw.text((55, 35), f"THE GHOUL’S GRIP  /  BAUANLEITUNG  /  ABSCHNITT {frame['step']}",
                  font=font(26, True), fill=TEAL)
        draw.text((52, 85), frame["title"], font=font(48, True), fill=INK)
        mode = frame["mode"]
        subtitles = ("A  Teile getrennt / Darstellung vor dem Fügen",
                     "B  Ergebnis / Teile in Einbaulage")
        if mode == "inventory":
            subtitles = ("A  Druckteile und Baugruppen", "B  So gehört die Baugruppe zusammen")
        if mode == "test":
            subtitles = ("A  Eingefahren / Scherenwinkel 18°", "B  Ausgefahren / Scherenwinkel 78°")
        for panel, x in enumerate((55, 1245)):
            draw.rounded_rectangle((x-5, 180, x+1105, 1120), radius=24, fill="white")
            draw.text((x+20, 198), subtitles[panel], font=font(28, True), fill=TEAL)
            raw = Image.open(WORK / f"{frame['slug']}-{panel}.png").convert("RGBA")
            validate_render(raw)
            image.paste(raw, (x, 255), raw)
        draw = ImageDraw.Draw(image)
        # A numbered key avoids tiny text placed over the geometry.
        badges = []
        for number, name in enumerate(frame["labels"], 1):
            anchor = evidence[frame["slug"]]["panels"][0][name]
            x, y = anchor[0] + 55, anchor[1] + 255
            dx = -90 if number % 2 else 90
            dy = -50 if number < 3 else 50
            for candidate in ((dx, dy), (dx, -dy), (-dx, dy), (-dx, -dy),
                              (dx, -140), (-dx, 140)):
                cx, cy = x + candidate[0], y + candidate[1]
                if (85 < cx < 1125 and 290 < cy < 1070
                        and all((cx-bx)**2 + (cy-by)**2 > 65**2
                                for bx, by in badges)):
                    dx, dy = candidate
                    break
            else:
                raise ValueError(f"No readable label position: {frame['slug']} / {name}")
            badges.append((x+dx, y+dy))
            draw.line((x, y, x+dx, y+dy), fill=TEAL, width=3)
            draw.ellipse((x+dx-22, y+dy-22, x+dx+22, y+dy+22), fill=TEAL)
            draw.text((x+dx, y+dy), str(number), font=font(25, True), fill="white", anchor="mm")
        legend = "    /    ".join(f"{i}  {LABELS[name]}" for i, name in enumerate(frame["labels"], 1))
        draw.text((65, 1136), legend, font=font(28, True), fill=TEAL)
        draw.text((65, 1195), frame["action"], font=font(30, True), fill=INK)
        draw.text((65, 1250), frame["check"], font=font(28), fill=INK)
        note = "Originalteile; Versätze in A zur Übersicht vergrößert, keine maßstäblichen Einführpfade."
        if "chest" not in evidence[frame["slug"]]["parts"]:
            note += " Truhe ausgeblendet."
        if mode == "lid":
            note += " Blick auf Deckelunterseite."
        draw.text((65, 1325), note, font=font(24), fill="#536570")
        draw.text((65, 1365), "Grau: bereits zugeordnete Teile. Filamentstifte nicht dargestellt.",
                  font=font(23), fill="#536570")
        path = OUT / f"ghouls-grip-montage-{frame['slug']}.png"
        image.save(path, dpi=(220, 220))
        outputs.append(path)
    sheet = Image.new("RGB", (1800, 4 * 385), "#E3EAEE")
    for index, path in enumerate(outputs):
        thumb = Image.open(path).convert("RGB")
        thumb.thumbnail((590, 370))
        sheet.paste(thumb, ((index % 3) * 600 + 5, (index // 3) * 385 + 5))
    sheet.save(OUT / "ghouls-grip-montage-bildfolge.png")
    print(f"Rendered {len(outputs)} step images and contact sheet; all panels nonempty.")


def main():
    if "--blender-stage" in sys.argv:
        render_all()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", type=Path)
    args = parser.parse_args()
    executable = args.blender or shutil.which("blender")
    if executable is None:
        installs = sorted(Path("C:\\Program Files\\Blender Foundation").glob("Blender *\\blender.exe"))
        executable = installs[-1] if installs else None
    if executable is None or not Path(executable).is_file():
        raise FileNotFoundError("Blender not found; pass --blender <executable>")
    hashes = {p: digest(p) for p in (ROOT / "models").glob("ghouls-grip*")}
    subprocess.run([str(executable), "--background", "--factory-startup",
                    "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
                    "--", "--blender-stage"], check=True)
    compose_all()
    if any(digest(p) != value for p, value in hashes.items()):
        raise RuntimeError("Source model changed during illustration render")
    print(f"Unchanged source models: {len(hashes)}; 42 source bodies in each of 3 poses.")


if __name__ == "__main__":
    main()
