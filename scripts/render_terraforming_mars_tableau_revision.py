"""Render the final three-plate Tableau revision."""

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import vedo

import revise_terraforming_mars_tableau as revision

from fit_terraforming_mars_tableau import (
    NS, PROD, ROOT, as_mesh, transform_vertices,
)

OUTPUT = (
    ROOT / "models"
    / "terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf"
)
PREVIEW = ROOT / "docs" / "images" / f"{OUTPUT.stem}-preview.png"
RAMP_SECTION = (
    ROOT / "docs" / "images" / f"{OUTPUT.stem}-ramp-section.png"
)
RAMP_WEB_CLOSEUP = (
    ROOT / "docs" / "images"
    / f"{OUTPUT.stem}-window5-to6-web-closeup.png"
)
LOCAL_RELIEFS = (
    ROOT / "docs" / "images" / f"{OUTPUT.stem}-local-reliefs.png"
)


def render_ramp_section(ramp, mesh):
    image = np.full((620, 1080, 3), 248, dtype=np.uint8)
    ramp_low_x = ramp["low_edge_x_mm"]
    ramp_high_x = ramp["high_edge_x_mm"]
    physical_x_min = ramp_low_x - 3.0
    physical_x_max = ramp_high_x + 3.0
    z_min = ramp["rear_face_z_mm"]
    z_max = ramp["front_face_z_mm"]
    plot_left, plot_right = 145, 905
    plot_top, plot_bottom = 115, 430
    z_display_min = z_min - 0.65
    z_display_max = z_max + 0.55
    scale = min(
        (plot_right - plot_left) / (physical_x_max - physical_x_min),
        (plot_bottom - plot_top) / (z_display_max - z_display_min),
    )

    def point(model_x, z):
        return (
            round(plot_left + (model_x - physical_x_min) * scale),
            round(plot_bottom - (z - z_display_min) * scale),
        )

    section_y = (ramp["ramp_y_bounds_mm"][0]
                 + ramp["ramp_y_bounds_mm"][1]) / 2
    section = mesh.section(
        plane_normal=[0, 1, 0], plane_origin=[0, section_y, 0]
    )
    revision.require(section is not None, "Missing exported ramp XZ section")
    for curve in section.discrete:
        points = np.asarray([point(x, z) for x, z in curve[:, [0, 2]]],
                            dtype=np.int32)
        cv2.polylines(image, [points], False, (135, 145, 153), 2, cv2.LINE_AA)

    profile_points = []
    ramp_slope = (z_max - z_min) / (ramp_high_x - ramp_low_x)
    for curve in section.discrete:
        points = curve[:, [0, 2]]
        on_profile = (
            (points[:, 0] >= ramp_low_x - 1e-4)
            & (points[:, 0] <= ramp_high_x + 1e-4)
            & (np.abs(
                points[:, 1]
                - (z_min + (points[:, 0] - ramp_low_x) * ramp_slope)
            ) < 1e-4)
        )
        profile_points.extend(points[on_profile].tolist())
    profile_points = np.asarray(profile_points, dtype=float)
    revision.require(
        len(profile_points) >= 2,
        "Exported mesh does not expose a continuous ramp profile",
    )
    profile_points = profile_points[
        np.argsort(profile_points[:, 0])
    ]
    profile = np.asarray(
        [point(x, z) for x, z in profile_points], dtype=np.int32
    )
    cv2.polylines(image, [profile], False, (35, 105, 190), 5, cv2.LINE_AA)

    baseline = point(ramp_low_x, z_display_min + 0.20)[1]
    cv2.line(image, (plot_left, baseline), (plot_right, baseline),
             (60, 70, 80), 2, cv2.LINE_AA)
    cv2.putText(image, "WINDOW 5", (plot_left + 12, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (70, 80, 90), 2, cv2.LINE_AA)
    cv2.putText(image, "WINDOW 6", (plot_right - 145, 210),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (70, 80, 90), 2, cv2.LINE_AA)
    cv2.putText(image, "MESH SECTION: PRINTED FRONT ORIENTATION",
                (32, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.82,
                (25, 45, 60), 2, cv2.LINE_AA)
    cv2.putText(
        image, "+X maps left-to-right in the photo registration",
        (32, 76), cv2.FONT_HERSHEY_SIMPLEX, 0.58,
        (25, 45, 60), 2, cv2.LINE_AA,
    )
    cv2.arrowedLine(
        image, (plot_left + 70, 470), (plot_right - 70, 470),
        (32, 80, 185), 4, cv2.LINE_AA, tipLength=0.035,
    )

    dimension_y = 500
    cv2.arrowedLine(image, (point(ramp_low_x, z_min)[0], dimension_y),
                    (point(ramp_high_x, z_max)[0], dimension_y), (25, 120, 45), 2,
                    cv2.LINE_AA, tipLength=0.04)
    cv2.arrowedLine(image, (point(ramp_high_x, z_max)[0], dimension_y),
                    (point(ramp_low_x, z_min)[0], dimension_y), (25, 120, 45), 2,
                    cv2.LINE_AA, tipLength=0.04)
    cv2.putText(
        image, f"run {ramp['slope_run_x_mm']:.3f} mm",
        (plot_left, 540), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (25, 105, 40), 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image, "5 -> 6: rises monotonically to the window-6 front face",
        (plot_left, 575), cv2.FONT_HERSHEY_SIMPLEX, 0.54, (45, 65, 80), 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image,
        f"rise {ramp['ramp_depth_z_mm']:.3f} mm | "
        f"{ramp['ramp_angle_from_front_face_deg']:.2f} deg | "
        f"top shelf {max(ramp['exported_cube_probe_checks']['ramp_top_edge_widths_mm']):.3f} mm",
        (plot_left, 605), cv2.FONT_HERSHEY_SIMPLEX, 0.50, (45, 65, 80), 2,
        cv2.LINE_AA,
    )
    if not cv2.imwrite(str(RAMP_SECTION), image):
        raise RuntimeError(f"Could not write ramp section: {RAMP_SECTION}")


def render_ramp_web_closeup(ramp, mesh):
    image = np.full((620, 1480, 3), 248, dtype=np.uint8)
    dark = (35, 54, 68)
    low_x, high_x = ramp["low_edge_x_mm"], ramp["high_edge_x_mm"]
    slice_x = (low_x + high_x) / 2
    y_min, y_max = ramp["ramp_y_bounds_mm"]
    z_min, z_max = ramp["rear_face_z_mm"], ramp["front_face_z_mm"]
    section_z = z_min + (slice_x - low_x) / (high_x - low_x) * (z_max - z_min)
    section = mesh.section(
        plane_normal=[1, 0, 0], plane_origin=[slice_x, 0, 0]
    )
    revision.require(section is not None, "Missing exported ramp YZ section")
    section_points = np.concatenate([
        curve[:, [1, 2]] for curve in section.discrete
    ])
    mesh_slope_points = section_points[
        (section_points[:, 0] >= y_min - 0.01)
        & (section_points[:, 0] <= y_max + 0.01)
        & (np.abs(section_points[:, 1] - section_z) < 1e-3)
    ]
    revision.require(
        len(mesh_slope_points) >= 2
        and abs(float(mesh_slope_points[:, 0].min()) - y_min) < 0.02
        and abs(float(mesh_slope_points[:, 0].max()) - y_max) < 0.02,
        "The exported ramp does not span the full divider at the mid-run section",
    )
    z_display_min = z_min - 0.55
    z_display_max = z_max + 0.55
    plot_left, plot_right = 180, 1300
    plot_top, plot_bottom = 150, 440
    scale = min(
        (plot_right - plot_left) / (y_max - y_min),
        (plot_bottom - plot_top) / (z_display_max - z_display_min),
    )
    horizontal_pad = ((plot_right - plot_left) - (y_max - y_min) * scale) / 2
    vertical_pad = ((plot_bottom - plot_top)
                    - (z_display_max - z_display_min) * scale) / 2

    def point(y, z):
        return (
            round(plot_left + horizontal_pad + (y - y_min) * scale),
            round(plot_top + vertical_pad
                  + (z_display_max - z) * scale),
        )

    # This section is derived from the exported mesh at a fixed X in the ramp.
    section_bounds = np.asarray([
        point(y_min, z_min), point(y_max, z_min),
        point(y_max, section_z), point(y_min, section_z),
    ], dtype=np.int32)
    cv2.fillPoly(image, [section_bounds], (219, 231, 240), cv2.LINE_AA)
    cv2.polylines(image, [section_bounds], True, (135, 145, 153), 2,
                  cv2.LINE_AA)
    slope_y = np.asarray([
        point(float(mesh_slope_points[:, 0].min()), section_z),
        point(float(mesh_slope_points[:, 0].max()), section_z),
    ], dtype=np.int32)
    cv2.line(image, tuple(slope_y[0]), tuple(slope_y[1]),
             (35, 105, 190), 5, cv2.LINE_AA)
    cv2.line(image, (plot_left, point(0, z_min)[1]),
             (plot_right, point(0, z_min)[1]), (60, 70, 80), 2,
             cv2.LINE_AA)
    cv2.putText(image, f"Y {y_min:.3f}", (plot_left, 480),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, dark, 2, cv2.LINE_AA)
    cv2.putText(image, f"Y {y_max:.3f}", (plot_right - 145, 480),
                cv2.FONT_HERSHEY_SIMPLEX, 0.52, dark, 2, cv2.LINE_AA)
    cv2.putText(image, "rear face", (72, point(0, z_min)[1] + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, dark, 2, cv2.LINE_AA)
    cv2.putText(image, "ramp surface", (72, point(0, section_z)[1] + 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.48, (35, 105, 190), 2,
                cv2.LINE_AA)
    cv2.putText(image, "EXPORTED MESH: RAMP SECTION ALONG DIVIDER",
                (42, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, dark, 2, cv2.LINE_AA)
    cv2.putText(
        image, f"Fixed X = {slice_x:.3f} mm | rise profile spans full length = "
        f"{y_max-y_min:.3f} mm",
        (42, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.62, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, "Blue line is the exported-mesh ramp surface; shaded area is solid ramp material",
        (42, 545), cv2.FONT_HERSHEY_SIMPLEX, 0.55, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, "Section coordinates follow model Y; 5 -> 6 direction is shown in the XZ profile.",
        (42, 580), cv2.FONT_HERSHEY_SIMPLEX, 0.52, dark, 2, cv2.LINE_AA,
    )
    if not cv2.imwrite(str(RAMP_WEB_CLOSEUP), image):
        raise RuntimeError(f"Could not write ramp web close-up: {RAMP_WEB_CLOSEUP}")


def render_local_reliefs(report):
    image = np.full((720, 1440, 3), 248, dtype=np.uint8)
    dark = (35, 54, 68)
    blue = (180, 218, 237)
    gold = (176, 208, 235)

    cv2.putText(
        image, "LOCAL CAD DETAILS FROM EXPORTED 3MF",
        (42, 48), cv2.FONT_HERSHEY_SIMPLEX, 0.9, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, "Victory-point window and adjacent zero-cube field",
        (42, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.68, dark, 2, cv2.LINE_AA,
    )
    window = report["small_siegpunkte_window"]["exported_geometry"]
    web = report["small_siegpunkte_window"]["web_to_zero_cube_field"]
    cube = np.asarray(web["zero_field_center_mm"], dtype=float)
    cube_half = 8.64 / 2
    bounds = np.asarray(window["bounds_mm"], dtype=float)
    scale = 16.0
    left = min(bounds[0, 0], cube[0] - cube_half)
    bottom = min(bounds[0, 1], cube[1] - cube_half)
    top = max(bounds[1, 1], cube[1] + cube_half)
    plan_x = 64
    plan_y = 150

    def plan_point(x, y):
        return (
            round(plan_x + (x - left) * scale),
            round(plan_y + (top - y) * scale),
        )

    window_rect = np.asarray([
        plan_point(bounds[0, 0], bounds[1, 1]),
        plan_point(bounds[1, 0], bounds[0, 1]),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(window_rect[0]), tuple(window_rect[1]),
                  blue, -1, cv2.LINE_AA)
    cv2.rectangle(image, tuple(window_rect[0]), tuple(window_rect[1]),
                  (56, 106, 142), 3, cv2.LINE_AA)
    cube_rect = np.asarray([
        plan_point(cube[0] - cube_half, cube[1] + cube_half),
        plan_point(cube[0] + cube_half, cube[1] - cube_half),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(cube_rect[0]), tuple(cube_rect[1]),
                  (227, 232, 212), -1, cv2.LINE_AA)
    cv2.rectangle(image, tuple(cube_rect[0]), tuple(cube_rect[1]),
                  (65, 110, 75), 3, cv2.LINE_AA)
    web_rect = np.asarray([
        plan_point(web["bounds_mm"][0][0], web["bounds_mm"][1][1]),
        plan_point(web["bounds_mm"][1][0], web["bounds_mm"][0][1]),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(web_rect[0]), tuple(web_rect[1]),
                  gold, -1, cv2.LINE_AA)
    cv2.rectangle(image, tuple(web_rect[0]), tuple(web_rect[1]),
                  (162, 108, 38), 2, cv2.LINE_AA)
    cv2.putText(
        image, f"Window {window['size_mm'][0]:.3f} x "
        f"{window['size_mm'][1]:.3f} mm",
        (82, 458), cv2.FONT_HERSHEY_SIMPLEX, 0.56, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, f"Web {web['width_mm']:.3f} x "
        f"{web['height_mm']:.3f} mm",
        (82, 492), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (130, 82, 24), 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image, "Zero-cube aperture 8.640 x 8.640 mm",
        (82, 526), cv2.FONT_HERSHEY_SIMPLEX, 0.56, (48, 96, 59), 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image, "Rear view: web remains 1.000 mm thick; front is relieved 1.500 mm",
        (42, 570), cv2.FONT_HERSHEY_SIMPLEX, 0.48, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, "At the front recess the window opens into the zero-cube field.",
        (42, 600), cv2.FONT_HERSHEY_SIMPLEX, 0.48, dark, 2, cv2.LINE_AA,
    )

    cv2.line(image, (720, 82), (720, 652), (196, 204, 209), 2,
             cv2.LINE_AA)
    cv2.putText(
        image, "10-cube end slot - XZ section at centerline",
        (764, 96), cv2.FONT_HERSHEY_SIMPLEX, 0.68, dark, 2, cv2.LINE_AA,
    )
    arrow = report["ten_cube_arrow_ledges"]["fields"][1]
    slot_width = arrow["front_slot_size_mm"][0]
    arrow_width = arrow["rear_arrow_opening_size_mm"][0]
    floor = arrow["back_layer_thickness_mm"]
    x_scale = 28.0
    z_scale = 56.0
    origin_x = 798
    floor_y = 540

    def section_point(x, z):
        return (
            round(origin_x + x * x_scale),
            round(floor_y - z * z_scale),
        )

    back_floor = np.asarray([
        section_point(arrow_width, 0.0),
        section_point(slot_width, floor),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(back_floor[0]), tuple(back_floor[1]),
                  (189, 202, 211), -1, cv2.LINE_AA)
    cv2.rectangle(image, tuple(back_floor[0]), tuple(back_floor[1]),
                  (68, 87, 100), 2, cv2.LINE_AA)
    opening_left = section_point(0.0, 0.0)
    opening_right = section_point(slot_width, 0.0)
    front_left = section_point(0.0, 2.5)
    front_right = section_point(slot_width, 2.5)
    cv2.line(image, opening_left, opening_right, (46, 99, 132), 2,
             cv2.LINE_AA)
    cv2.line(image, front_left, front_right, (46, 99, 132), 3,
             cv2.LINE_AA)
    cv2.line(image, opening_left, front_left, (46, 99, 132), 2,
             cv2.LINE_AA)
    cv2.line(image, opening_right, front_right, (46, 99, 132), 2,
             cv2.LINE_AA)
    cube_width = 8.5
    cube_outline = np.asarray([
        section_point(0.07, 0.0),
        section_point(0.07 + cube_width, 8.5),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(cube_outline[0]), tuple(cube_outline[1]),
                  (203, 224, 238), 2, cv2.LINE_AA)
    overrun_start = 8.64
    overrun_end = overrun_start + cube_width
    overrun_outline = np.asarray([
        section_point(overrun_start, floor),
        section_point(overrun_end, floor + cube_width),
    ], dtype=np.int32)
    cv2.rectangle(image, tuple(overrun_outline[0]), tuple(overrun_outline[1]),
                  (232, 218, 184), 2, cv2.LINE_AA)
    cv2.putText(
        image, "10-field cube: 8.500 mm",
        (origin_x, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (45, 99, 132), 2,
        cv2.LINE_AA,
    )
    cv2.putText(
        image, "Overrun cube rests on the raised ledge",
        (origin_x + 210, 216), cv2.FONT_HERSHEY_SIMPLEX, 0.48,
        (130, 91, 28), 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, f"Rear arrow opening: {arrow_width:.3f} mm",
        (origin_x, 590), cv2.FONT_HERSHEY_SIMPLEX, 0.5, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, f"Slot: {slot_width:.3f} mm | back ledge: {floor:.3f} mm | "
        f"front recess: {arrow['front_recess_depth_mm']:.3f} mm",
        (origin_x, 622), cv2.FONT_HERSHEY_SIMPLEX, 0.43, dark, 2, cv2.LINE_AA,
    )
    cv2.putText(
        image, f"Measured CAD contact area for overrun cube: "
        f"{arrow['overrun_cube_contact_area_mm2']:.1f} mm2",
        (origin_x, 654), cv2.FONT_HERSHEY_SIMPLEX, 0.43, dark, 2,
        cv2.LINE_AA,
    )
    if not cv2.imwrite(str(LOCAL_RELIEFS), image):
        raise RuntimeError(f"Could not write local relief preview: {LOCAL_RELIEFS}")


def main():
    with zipfile.ZipFile(OUTPUT) as archive:
        model = ET.fromstring(archive.read("3D/3dmodel.model"))
        config = ET.fromstring(archive.read("Metadata/model_settings.config"))
        settings = json.loads(archive.read("Metadata/project_settings.config"))
        objects = {
            item.get("id"): item
            for item in model.findall("./m:resources/m:object", NS)
        }
        metadata = {item.get("id"): item for item in config.findall("object")}
        plotter = vedo.Plotter(shape=(1, 3), size=(1800, 720), offscreen=True,
                               bg="#e8eef2")
        for index, item in enumerate(model.findall("./m:build/m:item", NS)):
            object_id = item.get("objectid")
            component = objects[object_id].find("./m:components/m:component", NS)
            path = component.get(f"{{{PROD}}}path").lstrip("/")
            _, _, mesh = as_mesh(archive.read(path), component.get("objectid"))
            vertices = transform_vertices(
                mesh.vertices, list(map(float, component.get("transform").split()))
            )
            vertices = transform_vertices(
                vertices, list(map(float, item.get("transform").split()))
            )
            vertices -= (vertices.max(axis=0) + vertices.min(axis=0)) / 2
            slot = int(
                metadata[object_id]
                .find("./metadata[@key='extruder']")
                .get("value")
            )
            color = settings["filament_colour"][slot - 1][:7]
            actor = vedo.Mesh([vertices, mesh.faces]).c(color).lighting("plastic")
            actor.compute_normals()
            if slot == 1:
                actor.alpha(0.75)
            title = (
                "Plate 1 - front / white",
                "Plate 2 - rear / dark",
                "Plate 3 - front / clear",
            )[index]
            subtitle = (
                "8 sockets: Ø3.000 mm" if index != 1
                else "8 pins: Ø2.600 mm"
            )
            if slot == 4:
                subtitle = "Transparent PLA: 0.10 mm | 20 mm/s | 220 C"
            plotter.show(
                actor,
                vedo.Text2D(title, pos="top-center", c="#183040", s=0.85),
                vedo.Text2D(subtitle, pos="bottom-center", c="#183040", s=0.8),
                at=index,
                camera={
                    "pos": (0, -180, 600),
                    "focal_point": (0, 0, 0),
                    "viewup": (0, 1, 0),
                    "parallel_scale": 160,
                },
                resetcam=False,
                interactive=False,
            )
            plotter.camera.ParallelProjectionOn()
        plotter.screenshot(str(PREVIEW))
        plotter.close()
        _, _, ramp_mesh = revision.as_mesh(
            archive.read(revision.FRONT_PATHS[0]),
            revision.MESH_IDS[revision.FRONT_PATHS[0]],
        )
    report = json.loads(
        (ROOT / "docs" /
         "terraforming-mars-tableau-179mm-laminate-centered-blocks-validation.json")
        .read_text(encoding="utf-8")
    )
    ramp_report = report["followup_adjustments"]["window5_to6_transition"]
    render_ramp_section(ramp_report, ramp_mesh)
    render_ramp_web_closeup(ramp_report, ramp_mesh)
    render_local_reliefs(report["followup_adjustments"])
    print(PREVIEW)
    print(RAMP_SECTION)
    print(RAMP_WEB_CLOSEUP)
    print(LOCAL_RELIEFS)


if __name__ == "__main__":
    main()
