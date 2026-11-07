"""Compare exported Tableau meshes with the measured laminated-board photo."""

import argparse
import json
import zipfile
from pathlib import Path

import cv2
import numpy as np

import revise_terraforming_mars_tableau as revision


ROOT = revision.ROOT
BEFORE = revision.PREVIOUS_OUTPUT
IMAGE_DIR = ROOT / "docs" / "images"
PHOTO_REPORT = (
    ROOT / "docs"
    / f"{revision.OUTPUT.stem}-photo-validation.json"
)
RAW_LAMINATE_BOUNDS_PX = (272.0, 32.0, 1446.0, 900.0)
RAW_CENTER_PX = (
    (RAW_LAMINATE_BOUNDS_PX[0] + RAW_LAMINATE_BOUNDS_PX[2]) / 2,
    (RAW_LAMINATE_BOUNDS_PX[1] + RAW_LAMINATE_BOUNDS_PX[3]) / 2,
)
RAW_SCALE_PX_PER_MM = np.mean([
    (RAW_LAMINATE_BOUNDS_PX[2] - RAW_LAMINATE_BOUNDS_PX[0])
    / revision.LAMINATE_LENGTH,
    (RAW_LAMINATE_BOUNDS_PX[3] - RAW_LAMINATE_BOUNDS_PX[1])
    / revision.LAMINATE_WIDTH,
])

COLORS = {
    "before": {
        "panel": (0, 190, 255),
        "paper": (255, 255, 255),
        "window": (0, 80, 255),
        "row": (180, 90, 180),
        "slot": (255, 180, 0),
        "mount": (30, 30, 240),
        "transition": (0, 140, 255),
    },
    "after": {
        "panel": (0, 255, 255),
        "paper": (255, 255, 255),
        "window": (0, 255, 80),
        "row": (255, 0, 255),
        "slot": (255, 0, 0),
        "mount": (0, 0, 255),
        "transition": (0, 140, 255),
    },
}


def load_front(path):
    with zipfile.ZipFile(path) as archive:
        _, _, mesh = revision.as_mesh(
            archive.read(revision.FRONT_PATHS[0]),
            revision.MESH_IDS[revision.FRONT_PATHS[0]],
        )
    return mesh


def model_to_pixel(points, center_px, scale):
    points = np.asarray(points, dtype=float)
    return np.column_stack((
        center_px[0] + points[:, 0] * scale,
        center_px[1] - points[:, 1] * scale,
    ))


def marked_block_target(name):
    x1, y1, x2, y2 = revision.BLOCK_MARKUP_TARGET_BOUNDS_PX[name]
    panel_x1, panel_y1, panel_x2, panel_y2 = (
        revision.BLOCK_MARKUP_PANEL_BOUNDS_PX
    )
    scale_x = (panel_x2 - panel_x1) / revision.NEW_LENGTH
    scale_y = (panel_y2 - panel_y1) / revision.SHORT_SIDE
    origin_x = (panel_x1 + panel_x2) / 2
    origin_y = (panel_y1 + panel_y2) / 2
    center = np.asarray([
        ((x1 + x2) / 2 - origin_x) / scale_x,
        (origin_y - (y1 + y2) / 2) / scale_y,
    ])
    size = np.asarray([
        (x2 - x1) / scale_x,
        (y2 - y1) / scale_y,
    ])
    return center, size


def rectangle_points(center, size):
    x, y = center
    half_x, half_y = np.asarray(size) / 2
    return np.asarray([
        [x - half_x, y - half_y],
        [x + half_x, y - half_y],
        [x + half_x, y + half_y],
        [x - half_x, y + half_y],
    ])


def draw_rectangle(image, center, size, transform, color, thickness=2,
                   dashed=False):
    points = model_to_pixel(rectangle_points(center, size), *transform)
    points = points.round().astype(np.int32)
    if not dashed:
        cv2.polylines(image, [points], True, color, thickness, cv2.LINE_AA)
        return
    for start, end in zip(points, np.roll(points, -1, axis=0)):
        delta = end - start
        length = float(np.linalg.norm(delta))
        if length == 0:
            continue
        direction = delta / length
        for offset in np.arange(0, length, 18):
            segment_end = min(offset + 10, length)
            a = (start + direction * offset).round().astype(int)
            b = (start + direction * segment_end).round().astype(int)
            cv2.line(image, tuple(a), tuple(b), color, thickness, cv2.LINE_AA)


def resource_window_contours(mesh, z):
    section = mesh.section(
        plane_normal=[0, 0, 1],
        plane_origin=[0, 0, z],
    )
    revision.require(section is not None, "Missing resource-window section")
    contours = []
    for loop in section.discrete:
        if len(loop) < 4 or np.linalg.norm(loop[0] - loop[-1]) > revision.TOL:
            continue
        low = loop[:, :2].min(axis=0)
        high = loop[:, :2].max(axis=0)
        center = (low + high) / 2
        size = high - low
        if (
            35.0 < size[0] < 160.0
            and 20.0 < size[1] < 60.0
            and (center[1] > 30 or center[1] < -30)
        ):
            contours.append(loop[:, :2])
    return contours


def draw_model(
    image, mesh, transform, palette, annotate_mounts=True, slot_height=None,
    draw_transition=False,
):
    if slot_height is None:
        slot_height = revision.LONG_SLOT_HEIGHT
    x0, y0 = mesh.bounds[0, :2]
    x1, y1 = mesh.bounds[1, :2]
    draw_rectangle(
        image, [(x0 + x1) / 2, (y0 + y1) / 2], [x1 - x0, y1 - y0],
        transform, palette["panel"], 3,
    )
    draw_rectangle(
        image, [0, 0],
        [revision.LAMINATE_LENGTH, revision.LAMINATE_WIDTH],
        transform, palette["paper"], 2,
    )
    window_z = float(mesh.bounds[1, 2]) - 0.01
    for contour in resource_window_contours(mesh, window_z):
        points = model_to_pixel(contour, *transform).round().astype(np.int32)
        cv2.polylines(
            image, [points], True, palette["window"], 3, cv2.LINE_AA
        )
    for index, target in enumerate(revision.TARGET_WINDOWS, start=1):
        center = np.asarray(target["center_mm"])
        pixel = model_to_pixel([center], *transform)[0].round().astype(int)
        label = "5/6" if draw_transition and index == 5 else str(index)
        cv2.putText(image, label, tuple(pixel),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, palette["window"], 2,
                    cv2.LINE_AA)
    holes = revision.square_holes(mesh, 0.0)
    for center in holes:
        draw_rectangle(
            image, center, [revision.OPENING_WIDTH] * 2, transform,
            palette["row"], 1,
        )
    for center, size in zip(
        *revision.double_width_slots(mesh, 0.2)
    ):
        draw_rectangle(image, center, size, transform, palette["row"], 1)
    slot_center, slot_size = revision.long_horizontal_slot(
        mesh, 0.0, slot_height
    )
    draw_rectangle(image, slot_center, slot_size, transform, palette["slot"], 3)
    draw_rectangle(
        image, revision.FOLLOWUP_SLIDER_MARK_CENTER_MM,
        revision.FOLLOWUP_SLIDER_SIZE_MM, transform, palette["slot"], 2,
        dashed=True,
    )
    if draw_transition:
        ramp = revision.REPORT.read_text(encoding="utf-8")
        ramp_spec = json.loads(ramp)["followup_adjustments"][
            "window5_to6_transition"
        ]
        ramp_center = np.asarray([
            (ramp_spec["window5_inner_edge_x_mm"]
             + ramp_spec["top_face_transfer_end_x_mm"]) / 2,
            sum(ramp_spec["y_span_mm"]) / 2,
        ])
        ramp_size = np.asarray([
            ramp_spec["top_face_transfer_end_x_mm"]
            - ramp_spec["window5_inner_edge_x_mm"],
            ramp_spec["y_span_mm"][1] - ramp_spec["y_span_mm"][0],
        ])
        draw_rectangle(
            image, ramp_center, ramp_size, transform,
            palette["transition"], 3
        )

    mount_centers = revision.SOURCE_MOUNTS.copy()
    outer = np.abs(mount_centers[:, 0]) >= 1
    mount_centers[outer, 0] -= np.sign(mount_centers[outer, 0])
    pixels = model_to_pixel(mount_centers, *transform).round().astype(int)
    radius = max(3, round(revision.SOCKET_DIAMETER * transform[1] / 2))
    for index, center in enumerate(pixels, start=1):
        cv2.circle(image, tuple(center), radius, palette["mount"], 2,
                   cv2.LINE_AA)
        if annotate_mounts:
            cv2.drawMarker(image, tuple(center), palette["mount"],
                           cv2.MARKER_CROSS, 10, 2, cv2.LINE_AA)


def draw_target_marks(image, transform):
    target_color = (0, 140, 255)
    for target in revision.TARGET_WINDOWS:
        draw_rectangle(
            image, target["center_mm"], target["size_mm"], transform,
            target_color, 2, dashed=True,
        )
    draw_rectangle(
        image, revision.FOLLOWUP_SLIDER_MARK_CENTER_MM,
        revision.FOLLOWUP_SLIDER_SIZE_MM, transform, target_color, 2,
        dashed=True,
    )
    for name in revision.NUMBER_BLOCK_SHIFTS_X_MM:
        center, size = marked_block_target(name)
        draw_rectangle(
            image, center, size, transform, (0, 0, 255), 2, dashed=True
        )


def title_bar(image, title, subtitle):
    height = 72
    banner = np.full((height, image.shape[1], 3), (25, 38, 48), np.uint8)
    cv2.putText(banner, title, (18, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.72, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(banner, subtitle, (18, 56), cv2.FONT_HERSHEY_SIMPLEX,
                0.5, (220, 230, 235), 1, cv2.LINE_AA)
    return np.vstack([banner, image])


def full_comparison(photo, before_mesh, after_mesh):
    transform = (RAW_CENTER_PX, RAW_SCALE_PX_PER_MM)
    before = photo.copy()
    after = photo.copy()
    draw_model(
        before, before_mesh, transform, COLORS["before"],
        slot_height=revision.PREVIOUS_LONG_SLOT_HEIGHT,
    )
    draw_model(
        after, after_mesh, transform, COLORS["after"],
        slot_height=revision.LONG_SLOT_HEIGHT,
        draw_transition=True,
    )
    draw_target_marks(after, transform)
    draw_target_marks(before, transform)
    before = title_bar(
        before, "BEFORE - prior exported 3MF",
        "Red-orange: old windows | magenta: old pockets | blue: old slot",
    )
    after = title_bar(
        after, "AFTER - cube-sized slider, window 5/6 ramp and top skin",
        "One global photo map (~1 mm uncertainty) | green: front-face contours | orange: 5->6 ramp | magenta: pockets | blue: slider",
    )
    return np.hstack([before, after])


def row_closeup(image, bounds, title):
    x1, y1, x2, y2 = bounds
    crop = image[y1:y2, x1:x2].copy()
    banner = np.full((42, crop.shape[1], 3), (25, 38, 48), np.uint8)
    cv2.putText(banner, title, (12, 28), cv2.FONT_HERSHEY_SIMPLEX,
                0.65, (255, 255, 255), 2, cv2.LINE_AA)
    return np.vstack([banner, crop])


def centered_closeup(image, center_px, size_px, title):
    width, height = size_px
    center_x, center_y = center_px
    bounds = (
        max(0, round(center_x - width / 2)),
        max(0, round(center_y - height / 2)),
        min(image.shape[1], round(center_x + width / 2)),
        min(image.shape[0], round(center_y + height / 2)),
    )
    return row_closeup(image, bounds, title)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True, type=Path)
    args = parser.parse_args()
    photo = cv2.imread(str(args.photo))
    revision.require(photo is not None, f"Could not read photo: {args.photo}")
    revision.require(
        tuple(photo.shape[1::-1]) == (1687, 949),
        f"Unexpected photo dimensions: {photo.shape[1]}x{photo.shape[0]}",
    )
    before_mesh = load_front(BEFORE)
    after_mesh = load_front(revision.OUTPUT)
    before_slot_center, _ = revision.long_horizontal_slot(
        before_mesh, 0.0, revision.PREVIOUS_LONG_SLOT_HEIGHT
    )
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    comparison_path = IMAGE_DIR / (
        f"{revision.OUTPUT.stem}-photo-before-after.png"
    )
    after_overlay = photo.copy()
    draw_model(
        after_overlay, after_mesh,
        (RAW_CENTER_PX, RAW_SCALE_PX_PER_MM), COLORS["after"],
        slot_height=revision.LONG_SLOT_HEIGHT,
        draw_transition=True,
    )
    draw_target_marks(after_overlay, (RAW_CENTER_PX, RAW_SCALE_PX_PER_MM))
    cv2.imwrite(
        str(comparison_path),
        full_comparison(photo, before_mesh, after_mesh),
    )
    outputs = [str(comparison_path.relative_to(ROOT)).replace("\\", "/")]
    row_ranges = (
        ("upper", (275, 315, 1450, 462), "UPPER PRODUCTION ROWS"),
        ("lower", (275, 488, 1450, 650), "LOWER PRODUCTION ROWS"),
    )
    for name, bounds, title in row_ranges:
        closeup_path = IMAGE_DIR / (
            f"{revision.OUTPUT.stem}-photo-{name}-rows.png"
        )
        cv2.imwrite(
            str(closeup_path),
            row_closeup(after_overlay, bounds, title),
        )
        outputs.append(str(closeup_path.relative_to(ROOT)).replace("\\", "/"))

    block_closeups = []
    for name, title in (
        ("upper-left -5", "UPPER-LEFT NUMBER BLOCK"),
        ("lower-left zero", "LOWER-LEFT NUMBER BLOCK"),
        ("upper-right zero", "UPPER-RIGHT NUMBER BLOCK"),
    ):
        center_mm, _ = marked_block_target(name)
        center_px = model_to_pixel(
            [center_mm], RAW_CENTER_PX, RAW_SCALE_PX_PER_MM
        )[0]
        filename_key = name.replace(" -", "-").replace(" ", "-").replace("/", "-")
        closeup_path = IMAGE_DIR / (
            f"{revision.OUTPUT.stem}-photo-{filename_key}-closeup.png"
        )
        cv2.imwrite(
            str(closeup_path),
            centered_closeup(
                after_overlay, center_px, (480, 260), title
            ),
        )
        block_closeups.append(
            str(closeup_path.relative_to(ROOT)).replace("\\", "/")
        )
        outputs.append(block_closeups[-1])
    slider_pixel = model_to_pixel(
        [revision.FOLLOWUP_SLIDER_CENTER_MM],
        RAW_CENTER_PX,
        RAW_SCALE_PX_PER_MM,
    )[0]
    slider_closeup = IMAGE_DIR / (
        f"{revision.OUTPUT.stem}-photo-slider-closeup.png"
    )
    cv2.imwrite(
        str(slider_closeup),
        centered_closeup(
            after_overlay, slider_pixel, (620, 220),
            "MIDDLE SLIDER - RED-MARK CENTER TARGET",
        ),
    )
    outputs.append(str(slider_closeup.relative_to(ROOT)).replace("\\", "/"))

    ramp = revision.REPORT.read_text(encoding="utf-8")
    ramp_spec = json.loads(ramp)["followup_adjustments"][
        "window5_to6_transition"
    ]
    ramp_center = np.asarray([
        (ramp_spec["window5_inner_edge_x_mm"]
         + ramp_spec["top_face_transfer_end_x_mm"]) / 2,
        sum(ramp_spec["y_span_mm"]) / 2,
    ])
    ramp_pixel = model_to_pixel(
        [ramp_center], RAW_CENTER_PX, RAW_SCALE_PX_PER_MM
    )[0]
    ramp_closeup = IMAGE_DIR / (
        f"{revision.OUTPUT.stem}-photo-window5-to6-ramp-closeup.png"
    )
    cv2.imwrite(
        str(ramp_closeup),
        centered_closeup(
            after_overlay, ramp_pixel, (500, 300),
            "WINDOW 5->6: RAMPED 8.64 mm FRONT-FACE TRANSFER",
        ),
    )
    outputs.append(str(ramp_closeup.relative_to(ROOT)).replace("\\", "/"))

    lower_right_center_mm = np.asarray([
        revision.PAPER_LEFT + 155.0 + revision.CUBE_EDGE / 2
        + revision.LOWER_RIGHT_TRACK_SHIFT_X_MM + 6.5 * revision.CUBE_EDGE,
        revision.PAPER_TOP - 96.0 - revision.CUBE_EDGE,
    ])
    lower_right_pixel = model_to_pixel(
        [lower_right_center_mm], RAW_CENTER_PX, RAW_SCALE_PX_PER_MM
    )[0]
    lower_right_closeup = IMAGE_DIR / (
        f"{revision.OUTPUT.stem}-photo-lower-right-closeup.png"
    )
    cv2.imwrite(
        str(lower_right_closeup),
        centered_closeup(
            after_overlay, lower_right_pixel, (520, 250),
            "LOWER-RIGHT CUBE FIELDS 3-5 AND 8-10",
        ),
    )
    outputs.append(
        str(lower_right_closeup.relative_to(ROOT)).replace("\\", "/")
    )

    photo_report = {
        "version": 1,
        "reference_photo": "User-provided unobscured centimeter-grid photo",
        "photo_size_px": [int(photo.shape[1]), int(photo.shape[0])],
        "user_measured_laminate_outer_size_mm": [
            revision.LAMINATE_LENGTH, revision.LAMINATE_WIDTH
        ],
        "estimated_laminate_outer_bounds_px": list(RAW_LAMINATE_BOUNDS_PX),
        "registration": {
            "method": "One uniform scale and translation for the whole image; no local warping",
            "model_origin_pixel": list(RAW_CENTER_PX),
            "uniform_scale_px_per_mm": float(RAW_SCALE_PX_PER_MM),
            "estimated_photo_alignment_uncertainty_mm": 1.0,
            "independent_landmark_residual_mm": None,
            "residual_note": "No independent pixel-level landmark residual is claimed; visible contour agreement is qualitative.",
        },
        "target_mark_source": "Unchanged user-marked resource windows and the user red-marked slider target; all transformed by the same photo-to-model map",
        "same_global_transform_used_for_model_and_target_marks": True,
        "exported_3mf": str(revision.OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "exported_3mf_sha256": revision.sha256(revision.OUTPUT),
        "compared_to_3mf": str(BEFORE.relative_to(ROOT)).replace("\\", "/"),
        "followup_translations_mm": {
            "slider": (
                revision.FOLLOWUP_SLIDER_CENTER_MM
                - before_slot_center
            ).tolist(),
            "lower_right_cube_rows": [
                revision.LOWER_RIGHT_TRACK_SHIFT_X_MM, 0.0
            ],
            "number_blocks": revision.NUMBER_BLOCK_SHIFTS_X_MM,
        },
        "new_geometry_and_surface_settings": {
            "slider_height_before_mm": revision.PREVIOUS_LONG_SLOT_HEIGHT,
            "slider_height_after_mm": revision.LONG_SLOT_HEIGHT,
            "slider_extension_down_mm": revision.SLIDER_EXTENSION_DOWN_MM,
            "slider_top_edge_preserved": True,
            "window5_to6_front_face_transfer_aperture_mm": (
                ramp_spec["target_front_face_transfer_aperture_mm"]
            ),
            "window5_to6_ramp_depth_mm": ramp_spec["ramp_depth_z_mm"],
            "transparent_front_top_shell_layers": 1,
            "transparent_front_ironing_type": "top",
            "physical_cube_transfer_tested": False,
            "surface_smoothness_and_optical_clarity_tested": False,
        },
        "number_block_targets": {
            "source": "User-marked red rectangles",
            "panel_outline_bounds_px": list(
                revision.BLOCK_MARKUP_PANEL_BOUNDS_PX
            ),
            "screen_pixels_per_mm_x": (
                revision.BLOCK_MARKUP_PX_PER_MM_X
            ),
            "estimated_alignment_uncertainty_mm": 1.0,
            "targets_model_mm": {
                name: {
                    "center_mm": marked_block_target(name)[0].tolist(),
                    "size_mm": marked_block_target(name)[1].tolist(),
                }
                for name in revision.NUMBER_BLOCK_SHIFTS_X_MM
            },
            "closeups": block_closeups,
        },
        "overlay_images": outputs,
        "physical_fit_test_performed": False,
        "successful_slicer_validation": False,
        "limitations": [
            "The transparent laminate edge is low contrast and the photo has perspective.",
            "The overlay validates visual placement only; it does not prove physical fit or laminate compression clearance.",
        ],
    }
    PHOTO_REPORT.write_text(
        json.dumps(photo_report, indent=2) + "\n", encoding="utf-8"
    )
    outputs.append(str(PHOTO_REPORT.relative_to(ROOT)).replace("\\", "/"))

    print({
        "outputs": outputs,
        "output_3mf_sha256": revision.sha256(revision.OUTPUT),
        "photo_to_model": {
            "laminate_bounds_px": RAW_LAMINATE_BOUNDS_PX,
            "laminate_size_mm": [
                revision.LAMINATE_LENGTH, revision.LAMINATE_WIDTH
            ],
            "center_px": RAW_CENTER_PX,
            "single_scale_px_per_mm": float(RAW_SCALE_PX_PER_MM),
            "photo_alignment_uncertainty_mm": 1.0,
        },
    })


if __name__ == "__main__":
    main()
