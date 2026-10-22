"""Read-only exploded assembly illustration from the delivered view 3MF.

Run with the catalog venv; Blender renders exact source meshes, Pillow adds
German typography. Only presentation translations are applied. Intermediate
render/projection evidence is kept in build/ghouls-grip-exploded/.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "ghouls-grip-view.3mf"
WORK = ROOT / "build" / "ghouls-grip-exploded"
OUTPUT = ROOT / "docs" / "images" / "ghouls-grip-explosionszeichnung.png"
INK = "#243447"
TEAL = "#007F82"
CARDS = (
    ("Truhe", "Schritt 1",
     "Öffnung nach oben. Bodenlager und\nSchienen bleiben Teil der Truhe."),
    ("Schlitten", "Schritt 2",
     "Senkrecht auf die Schienen drücken;\nbeide Schnappfinger einrasten lassen."),
    ("Hauptantrieb & Totenkopf", "Schritte 3–4",
     "Ritzel von innen durch die Vorderwand.\nKnauf außen auf die D-Welle stecken;\nmit 14-mm-Filamentstift quer sichern."),
    ("Deckel-Folger & Transfer", "Schritte 5–6",
     "Folger absenken, Pressstift einsetzen.\nZwei Transferzahnräder in −X einschieben;\naußen mit je 5-mm-Filamentstift sichern."),
    ("Doppelschere", "Schritte 7–8",
     "Vier Arme, zwei Scherenebenen.\nBodenstifte von der Mitte nach außen.\nEingangszahnrad vor dem Hubjoch setzen."),
    ("Hubjoch & Fünf-Zahnrad-Getriebe", "Schritt 9",
     "Unterarm und Abtriebswelle vormontieren.\nJoch 3 mm versetzt absenken, dann entlang\nder Achsverbindung in Eingriff schieben."),
    ("Unterarm, Hand & optionale Schale", "Schritt 10 / Vormontage 9",
     "Handgelenk: 16-mm-Querstift. Finger:\nZeige-, Mittel-, Ring-, kleiner, Daumen.\nAuf MCP-Zapfen schieben; Schale zuletzt."),
    ("Deckel, Kurbel & Distanzhülse", "Schritte 11–12",
     "Kurbel + Hülse außerhalb vormontieren.\nDeckel 108° offen, 3 mm nach hinten;\nabsenken, vorziehen, 198-mm-Achse einführen."),
)


def layout(name: str) -> tuple[int, tuple[float, float, float]]:
    """Map all 42 delivered bodies to drawing groups and rigid offsets."""
    if name == "chest":
        return 1, (0, 0, 0)
    if name == "slider":
        return 2, (0, 0, 150)
    if name in ("drive-pinion", "drive-skull-knob"):
        return 3, (-100, -100 if name.endswith("knob") else -45, 85)
    if name in ("lid-follower-rack", "pivot-pin-follower"):
        return 4, (-140, 0 if name.endswith("rack") else 35, 150)
    if name.startswith("lid-transfer-"):
        return 4, (-160 if name.endswith("input") else -125, 25, 210)
    if name.startswith("arm-"):
        return 5, (35 if name.endswith("True") else 0,
                   -32 if name.startswith("arm-0") else 32, 205)
    if name.startswith("pivot-pin-") and "idler" not in name:
        return 5, (0, -65 if name.endswith("-0") else 65, 205)
    if name == "scissor-drive-gear":
        return 5, (0, 105, 220)
    if name == "platform":
        return 6, (0, 0, 305)
    if name.startswith(("idler-gear-", "pivot-pin-idler-")):
        return 6, (0, 65 if name.startswith("idler-") else 100, 305)
    if name == "forearm-output-gear":
        return 6, (0, 55, 340)
    if name == "forearm":
        return 7, (0, 0, 385)
    if name == "hand-palm":
        return 7, (-20, 0, 420)
    if name.startswith("hand-finger-"):
        index = ("thumb", "index", "middle", "ring", "little").index(
            name.removeprefix("hand-finger-"))
        return 7, (-65, (index - 2) * 21, 470 + (index % 2) * 12)
    if name == "candy-dish":
        return 7, (85, 0, 535)
    if name in ("lid", "lid-crank", "crank-spacer"):
        return 8, (240 if name == "lid" else 200,
                   35 if name == "lid" else -5, 260)
    raise ValueError(f"Unmapped source part: {name}")


def digest(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def validate_render(image) -> None:
    if image.getchannel("A").getbbox() is None:
        raise ValueError("Empty Blender render: no visible source geometry")


def blender_render() -> None:
    import bpy
    from bpy_extras.object_utils import world_to_camera_view
    from mathutils import Vector

    sys.path.insert(0, str(ROOT / "scripts"))
    from build_ghouls_grip_blender_scene import _import_master, _reset_scene

    _reset_scene()
    objects = _import_master()
    if len(objects) != 42:
        raise ValueError(f"Expected 42 source objects, found {len(objects)}")
    groups = {}
    for obj in objects:
        name = obj["source_name"]
        group, offset = layout(name)
        obj.location += Vector(offset)
        groups.setdefault(group, []).append(obj)
        obj.hide_select = True
        obj.color = obj.data.materials[0].diffuse_color
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.001
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.studiolight_rotate_z = math.radians(25)
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.display.shading.cavity_type = "BOTH"
    scene.display.shading.curvature_ridge_factor = 1.5
    scene.display.shading.curvature_valley_factor = 1.2
    scene.display.shading.show_specular_highlight = True
    scene.display.shading.background_type = "WORLD"
    scene.world.color = (0.92, 0.94, 0.95)
    scene.render.film_transparent = True
    scene.display.render_aa = "32"
    scene.render.resolution_x = 2100
    scene.render.resolution_y = 2100
    scene.render.resolution_percentage = 100
    camera_data = bpy.data.cameras.new("exploded_camera")
    camera = bpy.data.objects.new("exploded_camera", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    bpy.context.view_layer.update()
    corners = [obj.matrix_world @ Vector(corner)
               for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(p[i] for p in corners) for i in range(3)))
    high = Vector(tuple(max(p[i] for p in corners) for i in range(3)))
    center = (low + high) / 2
    camera.location = center + Vector((950, -1550, 1000))
    camera.rotation_euler = (center - camera.location).to_track_quat(
        "-Z", "Y").to_euler()
    camera_data.type = "ORTHO"
    camera_data.clip_end = 10000
    bpy.context.view_layer.update()
    inverse = camera.matrix_world.inverted()
    projected = [inverse @ p for p in corners]
    width = max(p.x for p in projected) - min(p.x for p in projected)
    height = max(p.y for p in projected) - min(p.y for p in projected)
    camera_data.ortho_scale = max(width, height) * 1.18
    # Centre the projected bounds, not the 3D bounds (the lid is off-axis).
    camera.location += camera.rotation_euler.to_matrix() @ Vector((
        (max(p.x for p in projected) + min(p.x for p in projected)) / 2,
        (max(p.y for p in projected) + min(p.y for p in projected)) / 2, 0))
    bpy.context.view_layer.update()

    def pixel(point):
        p = world_to_camera_view(scene, camera, point)
        return [round(p.x * 2100, 2), round((1 - p.y) * 2100, 2)]

    anchors = {}
    representatives = {
        1: "chest", 2: "slider", 3: "drive-skull-knob",
        4: "lid-follower-rack", 5: "arm-0-False", 6: "platform",
        7: "hand-palm", 8: "lid",
    }
    evidence = []
    for obj in objects:
        name = obj["source_name"]
        corners = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
        center = sum(corners, Vector()) / 8
        group, offset = layout(name)
        if name == representatives[group]:
            anchors[group] = pixel(center)
        evidence.append({
            "name": name, "group": group, "translation": offset,
            "vertices": len(obj.data.vertices), "triangles": len(obj.data.polygons),
            "screen_bounds": [pixel(c) for c in corners],
        })
    if any(not 0 <= coordinate <= 2100
           for item in evidence for point in item["screen_bounds"]
           for coordinate in point):
        raise ValueError("Source part falls outside the drawing camera")
    WORK.mkdir(parents=True, exist_ok=True)
    (WORK / "projection.json").write_text(
        json.dumps({"anchors": anchors, "objects": evidence}, indent=2),
        encoding="utf-8")
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(WORK / "parts.png")
    bpy.ops.render.render(write_still=True)


def compose() -> None:
    from PIL import Image, ImageDraw, ImageFont

    def font(size, bold=False):
        filename = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        windows = Path("C:\\Windows\\Fonts") / (
            "segoeuib.ttf" if bold else "segoeui.ttf")
        return ImageFont.truetype(str(windows) if windows.exists() else filename,
                                  size)

    image = Image.new("RGB", (3200, 2600), "#F3F6F7")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 3200, 18), fill=TEAL)
    draw.text((80, 58), "THE GHOUL’S GRIP", font=font(30, True), fill=TEAL)
    draw.text((75, 101), "Explosionszeichnung", font=font(82, True), fill=INK)
    draw.text((82, 210), "Montageübersicht  /  Originalbauteile aus dem Ansichtsprojekt",
              font=font(30), fill=INK)
    draw.rounded_rectangle((65, 290, 2185, 2390), radius=30, fill="white")
    metadata = json.loads((WORK / "projection.json").read_text(encoding="utf-8"))
    anchors = metadata["anchors"]
    for start, end in ((1, 2), (2, 5), (5, 6), (6, 7)):
        a = [anchors[str(start)][i] + (75, 290)[i] for i in range(2)]
        b = [anchors[str(end)][i] + (75, 290)[i] for i in range(2)]
        distance = math.dist(a, b)
        for step in range(0, int(distance), 22):
            t0, t1 = step / distance, min(step + 11, distance) / distance
            draw.line(tuple(tuple(a[i] + (b[i] - a[i]) * t for i in range(2))
                            for t in (t0, t1)), fill="#92BFC0", width=3)
        t = 0.53
        tip = tuple(a[i] + (b[i] - a[i]) * t for i in range(2))
        angle = math.atan2(b[1]-a[1], b[0]-a[0])
        draw.polygon([tip] + [
            (tip[0] - 19 * math.cos(angle + delta),
             tip[1] - 19 * math.sin(angle + delta))
            for delta in (-0.45, 0.45)], fill="#92BFC0")
    parts = Image.open(WORK / "parts.png").convert("RGBA")
    validate_render(parts)
    image.paste(parts, (75, 290), parts)
    draw = ImageDraw.Draw(image)
    # Badge offsets keep the leaders outside the silhouettes.
    badge_offsets = {
        1: (-300, 110), 2: (270, -10), 3: (-160, 100), 4: (-180, -60),
        5: (-270, 0), 6: (210, 20), 7: (-220, 25), 8: (310, -50),
    }
    for key, anchor in metadata["anchors"].items():
        group = int(key)
        point = (anchor[0] + 75, anchor[1] + 290)
        off = badge_offsets[group]
        badge = (point[0] + off[0], point[1] + off[1])
        draw.line((badge, point), fill=TEAL, width=3)
        draw.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5),
                     fill=TEAL)
        draw.ellipse((badge[0]-30, badge[1]-30, badge[0]+30, badge[1]+30),
                     fill=TEAL)
        draw.text(badge, str(group), font=font(30, True), fill="white",
                  anchor="mm")

    draw.text((2250, 295), "BAUGRUPPEN & REIHENFOLGE",
              font=font(29, True), fill=TEAL)
    for index, (title, steps, text) in enumerate(CARDS):
        y = 365 + index * 240
        draw.line((2250, y - 18, 3105, y - 18), fill="#CFDADF", width=2)
        draw.ellipse((2250, y, 2306, y+56), fill=TEAL)
        draw.text((2278, y+28), str(index+1), anchor="mm",
                  font=font(28, True), fill="white")
        draw.text((2324, y-4), title, font=font(30, True), fill=INK)
        draw.text((2324, y+40), steps, font=font(25, True), fill=TEAL)
        draw.multiline_text((2324, y+87), text, font=font(27), fill=INK,
                            spacing=9)

    draw.text((110, 2240), "↑  EXPLOSION: nach oben / seitlich auseinandergezogen",
              font=font(29, True), fill=TEAL)
    draw.multiline_text(
        (110, 2290),
        "Gestrichelt: Explosionsachsen zur Übersicht, keine Einführpfade.\n"
        "Schnappstifte sind seitlich gelöst; Zahnradgruppen bleiben ihrer Baugruppe zugeordnet.",
        font=font(26), fill=INK, spacing=10)
    draw.line((80, 2430, 3120, 2430), fill="#B6C9D0", width=2)
    draw.multiline_text(
        (82, 2460),
        "42 Druckteile  •  Schwarz: Gehäuse  /  Naturweiß: Mechanik  /  Knochenbeige: Hand  /  Gold: Knauf + Schale\n"
        "Filamentstifte nicht dargestellt. Detail-Steckrichtungen, Sicherungen und Trockenlauf: Bauanleitung, Schritte 1–13.",
        font=font(28), fill=INK, spacing=14)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    image.save(OUTPUT, dpi=(240, 240))


def main() -> None:
    if "--blender-stage" in sys.argv:
        blender_render()
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--blender", type=Path)
    args = parser.parse_args()
    executable = args.blender or shutil.which("blender")
    if executable is None:
        installs = sorted(Path("C:\\Program Files\\Blender Foundation").glob(
            "Blender *\\blender.exe"))
        executable = installs[-1] if installs else None
    if executable is None or not Path(executable).is_file():
        raise FileNotFoundError("Blender not found; pass --blender <executable>")
    originals = {p: digest(p) for p in (ROOT / "models").glob("ghouls-grip*")}
    WORK.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        str(executable), "--background", "--factory-startup",
        "--python-exit-code", "1", "--python", str(Path(__file__).resolve()),
        "--", "--blender-stage",
    ], check=True)
    compose()
    for path, before in originals.items():
        if digest(path) != before:
            raise RuntimeError(f"Model unexpectedly changed: {path}")
    print(json.dumps({"output": str(OUTPUT), "size": [3200, 2600],
                      "source_sha256": originals[SOURCE],
                      "unchanged_model_files": len(originals)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
