"""Render the English step-by-step guide from unchanged delivered 3MF bodies.

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
    dict(step=2, slug="02", title="Prepare and sort the parts",
         pose="deployed", mode="inventory",
         labels=("chest", "hand-palm", "candy-dish"),
         action="Sort the 42 printed parts by color and function. The dish is optional.",
         check="Also prepare four Ø1.75 mm filament pieces, 198 / 14 / 10 / 16 mm long (Ø2.30 mm holes)."),
    dict(step=3, slug="03a", title="Fit the slider onto the floor guides",
         pose="retracted", mode="slider", labels=("slider",),
         action="Offset about 5.5 mm toward +X and press down until both snap fingers engage.",
         check="The closed box frame with crossbars slides without twisting or bowing."),
    dict(step=3, slug="03b", title="Install the pinion and skull knob",
         pose="retracted", mode="drive",
         labels=("drive-pinion", "drive-skull-knob"),
         action="Insert the pinion through the front wall from inside; fit the knob onto the D-shaft from outside.",
         check="Secure with a 14 mm filament cross-pin. Turn the knob; do not press it."),
    dict(step=4, slug="04", title="Install the follower and lid transfer gears",
         pose="retracted", mode="follower",
         labels=("lid-follower-rack", "pivot-pin-follower",
                 "lid-transfer-input", "lid-transfer-idler"),
         action="Lower the follower; press the unslotted 13.1 mm follower pin almost to the wall.",
         check="Slide both transfer gears axially in −X until each slotted clip engages behind its bearing block."),
    dict(step=5, slug="05", title="Assemble both scissor pairs",
         pose="retracted", mode="scissors",
         labels=("arm-0-False", "arm-1-True", "pivot-pin-floor-0",
                 "pivot-pin-slider-0", "pivot-pin-centre-0"),
         action="Insert the two extra-long 21.6 mm floor pins from inside outward; fit the two 14.4 mm slider pins at the lower joints.",
         check="Fit the two short 11.6 mm pins at the arm crossings. Leave the upper joints open."),
    dict(step=6, slug="06", title="Fit the input gear before the lift yoke",
         pose="intermediate", mode="input",
         labels=("scissor-drive-gear",),
         action="Slide the gear from +Y onto the upper arm eye and seat its locating pin in the arm hole.",
         check="Set the scissors to 48°. Install the lift yoke afterward; secure the upper pin later."),
    dict(step=7, slug="07", title="Preassemble the lift yoke and forearm",
         pose="deployed", mode="platform",
         labels=("platform", "forearm", "forearm-output-gear",
                 "idler-gear-1", "pivot-pin-idler-1"),
         action="Place the forearm between the bearing ears, slide the D-shaft through, and fit the 10 mm cross-pin.",
         check="Three 14.6 mm long pins, matching the slider-pin style, secure the three idler gears."),
    dict(step=8, slug="08", title="Offset the lift yoke into the scissors",
         pose="deployed", mode="join",
         labels=("platform", "scissor-drive-gear", "pivot-pin-fixed-1",
                 "pivot-pin-fixed-0", "pivot-pin-slot-0", "pivot-pin-slot-1"),
         action="At 78°, lower with a 3 mm offset, then engage along the 64° shaft axis.",
         check="Secure the top: one 19.6 mm extra-long gear pin at +Y and three 10.0 mm short pins in the remaining eyes."),
    dict(step=9, slug="09", title="Fit the palm, fingers, and dish",
         pose="deployed", mode="hand",
         labels=("hand-palm", "hand-finger-index", "hand-finger-thumb", "candy-dish"),
         action="Fit the 16 mm wrist cross-pin. Install the fingers in this order: index → middle → ring → little → thumb.",
         check="Fit the dish last. The fingers and dish are removable, not locked in place."),
    dict(step=10, slug="10", title="Fit the crank and spacer to the detached lid",
         pose="intermediate", mode="lid",
         labels=("lid-crank", "crank-spacer"),
         action="Place the crank in the 25 mm hood, then slide it 5.6 mm toward +X into the pocket.",
         check="This creates room behind it for the 15.8 mm spacer (26.8 mm combined)."),
    dict(step=11, slug="11", title="Position the lid and secure the hinge",
         pose="intermediate", mode="hinge", labels=("lid",),
         action="With the lid open 108°, lower it 3 mm rearward (+Y), then slide it forward.",
         check="Set the scissors to 48°. Insert the 198 mm filament hinge pin from the end through all eyes."),
    dict(step=12, slug="12", title="Run a slow, unloaded test",
         pose="deployed", mode="test", labels=(),
         action="Extend the mechanism with the skull knob and retract it in reverse. Do not turn past either end stop.",
         check="Stop if you hear a crack, feel resistance, or notice a skipped tooth. Keep fingers clear of the mechanism."),
)
LABELS = {
    "chest": "Chest", "slider": "Slider",
    "drive-pinion": "Pinion / D-shaft", "drive-skull-knob": "Skull knob",
    "lid-follower-rack": "Follower",
    "pivot-pin-follower": "Follower press pin (unslotted)",
    "lid-transfer-input": "Transfer gear 1",
    "lid-transfer-idler": "Transfer gear 2", "arm-0-False": "Front scissor pair",
    "arm-1-True": "Rear scissor pair",
    "pivot-pin-floor-0": "Extra-long pin (2× floor)",
    "pivot-pin-slider-0": "Long pin (2× slider)",
    "pivot-pin-centre-0": "Short pin (2× scissor center)",
    "scissor-drive-gear": "Input gear", "platform": "Lift yoke",
    "forearm": "Forearm", "forearm-output-gear": "Output gear / D-shaft",
    "idler-gear-1": "Idler gears",
    "pivot-pin-idler-1": "Long pin (3× idler gear)",
    "hand-palm": "Palm",
    "hand-finger-index": "Index finger", "hand-finger-thumb": "Thumb",
    "candy-dish": "Dish (optional)", "lid-crank": "Lid crank (11.0 mm)",
    "crank-spacer": "Spacer (15.8 mm)", "lid": "Lid assembly",
    "pivot-pin-fixed-1": "Extra-long pin (1× gear)",
    "pivot-pin-fixed-0": "Extra-short pin (fixed −Y)",
    "pivot-pin-slot-0": "Extra-short pin (slot −Y)",
    "pivot-pin-slot-1": "Extra-short pin (slot +Y)",
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
        draw.text((55, 35), f"THE GHOUL’S GRIP  /  ASSEMBLY GUIDE  /  STEP {frame['step']}",
                  font=font(26, True), fill=TEAL)
        draw.text((52, 85), frame["title"], font=font(48, True), fill=INK)
        mode = frame["mode"]
        subtitles = ("A  Parts separated / before assembly",
                     "B  Assembled / parts in installed positions")
        if mode == "inventory":
            subtitles = ("A  Printed parts and subassemblies",
                         "B  How the assembly fits together")
        if mode == "test":
            subtitles = ("A  Retracted / 18° scissor angle",
                         "B  Deployed / 78° scissor angle")
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
        note = "Original parts; offsets in panel A are enlarged for clarity and are not to scale for insertion."
        if "chest" not in evidence[frame["slug"]]["parts"]:
            note += " Chest hidden."
        if mode == "lid":
            note += " View of the underside of the lid."
        draw.text((65, 1325), note, font=font(24), fill="#536570")
        draw.text((65, 1365), "Gray: parts already assigned to the assembly. Filament pins are not shown.",
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
