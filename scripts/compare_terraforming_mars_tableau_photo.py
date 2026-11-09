"""Compare exported Tableau section contours with the printed-board photo."""

import argparse
import json
import zipfile
from pathlib import Path

import cv2
import numpy as np

import revise_terraforming_mars_tableau as revision


ROOT = revision.ROOT
OUTPUT = revision.OUTPUT
IMAGE_DIR = ROOT / "docs" / "images"
GRID_ORIGIN_PX = (264.0, 30.0)
GRID_PITCH_PX = 52.0
GRID_PITCH_MM = 10.0
OBSERVED_ANCHORS = (
    ("lower-left zero", (368.0, 527.0)),
    ("lower-middle zero", (734.0, 527.0)),
    ("lower-right zero", (1082.0, 527.0)),
    ("upper-left -5", (508.0, 350.0)),
    ("upper-middle zero", (798.0, 350.0)),
    ("upper-right zero", (1103.0, 350.0)),
)


def model_point(datum):
    return [
        revision.OLD_LEFT + datum["offset_x"],
        revision.TOP_EDGE - datum["top_distance"],
    ]


def classify(size, center):
    if max(size) > 200:
        return (0, 255, 255), 3
    if 100 < size[0] < 120 and 6.5 < size[1] < 7.1:
        return (255, 255, 0), 2
    if 24.0 < size[0] < 24.5 and 15.3 < size[1] < 15.9 and center[0] < -80:
        return (0, 150, 255), 2
    if 17.5 < size.max() < 18.2 and 8.5 < size.min() < 8.8:
        return (255, 0, 255), 2
    if np.all((size > 8.5) & (size < 8.8)):
        return (255, 0, 255), 2
    if size.max() > 35:
        return (0, 255, 0), 2
    return None


def project_points(points, transform):
    points = np.asarray(points, dtype=np.float32).reshape((-1, 1, 2))
    return cv2.perspectiveTransform(points, transform).reshape((-1, 2))


def draw_contours(photo, mesh, transform, section_z):
    overlay = photo.copy()
    section = mesh.section(
        plane_normal=[0, 0, 1], plane_origin=[0, 0, section_z]
    )
    revision.require(section is not None, "Missing exported 3MF section")
    contour_count = 0
    for loop in section.discrete:
        if len(loop) < 4 or np.linalg.norm(loop[0] - loop[-1]) > revision.TOL:
            continue
        low = loop[:, :2].min(axis=0)
        high = loop[:, :2].max(axis=0)
        center = (low + high) / 2
        size = high - low
        style = classify(size, center)
        if style is None:
            continue
        color, thickness = style
        pixels = project_points(loop[:, :2], transform).round().astype(np.int32)
        cv2.polylines(
            overlay, [pixels], isClosed=True, color=color,
            thickness=thickness, lineType=cv2.LINE_AA,
        )
        contour_count += 1
    return overlay, contour_count


def annotate_anchors(image, transform):
    predicted = project_points(
        [model_point(datum) for datum in revision.ROW_ANCHORS], transform
    )
    observations = np.asarray([point for _, point in OBSERVED_ANCHORS])
    residuals = np.linalg.norm(predicted - observations, axis=1)
    for expected, observed in zip(predicted, observations):
        cv2.circle(image, tuple(expected.round().astype(int)), 7,
                   (255, 255, 0), 2, cv2.LINE_AA)
        cv2.drawMarker(
            image, tuple(observed.round().astype(int)), (0, 255, 255),
            cv2.MARKER_CROSS, 15, 2, cv2.LINE_AA,
        )
        cv2.line(
            image, tuple(expected.round().astype(int)),
            tuple(observed.round().astype(int)), (0, 0, 255), 1, cv2.LINE_AA,
        )
    return predicted, residuals


def title_bar(image, title, subtitle=None):
    bar_height = 70 if subtitle else 48
    banner = np.full((bar_height, image.shape[1], 3), (22, 38, 48),
                     dtype=np.uint8)
    cv2.putText(banner, title, (18, 30), cv2.FONT_HERSHEY_SIMPLEX,
                0.75, (255, 255, 255), 2, cv2.LINE_AA)
    if subtitle:
        cv2.putText(banner, subtitle, (18, 57), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, (220, 230, 235), 1, cv2.LINE_AA)
    return np.vstack((banner, image))


def fit_image(image, width, height):
    scale = min(width / image.shape[1], height / image.shape[0])
    resized = cv2.resize(
        image, (round(image.shape[1] * scale), round(image.shape[0] * scale)),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((height, width, 3), 245, dtype=np.uint8)
    x = (width - resized.shape[1]) // 2
    y = (height - resized.shape[0]) // 2
    canvas[y:y + resized.shape[0], x:x + resized.shape[1]] = resized
    return canvas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--photo", required=True, type=Path)
    args = parser.parse_args()
    photo = cv2.imread(str(args.photo))
    revision.require(photo is not None, f"Could not read photo: {args.photo}")
    height, width = photo.shape[:2]
    revision.require((width, height) == (1687, 949),
                     f"Unexpected photo dimensions: {width}x{height}")

    scale = GRID_PITCH_PX / GRID_PITCH_MM
    origin_x, origin_y = GRID_ORIGIN_PX
    transform = np.asarray([
        [scale, 0.0, origin_x - scale * revision.OLD_LEFT],
        [0.0, -scale, origin_y + scale * revision.TOP_EDGE],
        [0.0, 0.0, 1.0],
    ], dtype=np.float32)
    with zipfile.ZipFile(OUTPUT) as archive:
        _, _, mesh = revision.as_mesh(
            archive.read(revision.FRONT_PATHS[0]),
            revision.MESH_IDS[revision.FRONT_PATHS[0]],
        )
    section_z = float(mesh.bounds[0, 2] + mesh.extents[2] / 2)
    overlay, contour_count = draw_contours(photo, mesh, transform, section_z)
    predicted, residuals = annotate_anchors(overlay, transform)

    labels = [
        f"{name}: {error / scale:.1f} mm"
        for (name, _), error in zip(OBSERVED_ANCHORS, residuals)
    ]
    for index, label in enumerate(labels):
        cv2.putText(overlay, label, (20, 100 + index * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255),
                    2, cv2.LINE_AA)
        cv2.putText(overlay, label, (20, 100 + index * 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 0, 0),
                    1, cv2.LINE_AA)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    full_path = IMAGE_DIR / f"{OUTPUT.stem}-grid-photo-validation.png"
    cv2.imwrite(str(full_path), title_bar(
        overlay,
        "Exported 3MF number rows over centimeter grid",
        "Magenta: pockets; green: unchanged windows; yellow: model envelope, not paper edge",
    ))

    closeups = []
    for name, bounds in (
        ("upper", (300, 285, 1420, 500)),
        ("lower", (300, 460, 1420, 655)),
    ):
        x1, y1, x2, y2 = bounds
        crop = overlay[y1:y2, x1:x2]
        crop = cv2.resize(crop, None, fx=1.5, fy=1.5,
                          interpolation=cv2.INTER_CUBIC)
        close_path = IMAGE_DIR / f"{OUTPUT.stem}-grid-{name}-row-closeup.png"
        cv2.imwrite(str(close_path), title_bar(
            crop, f"Grid-calibrated exported 3MF contours - {name} rows"
        ))
        closeups.append(str(close_path.relative_to(ROOT)).replace("\\", "/"))

    report = {
        "photo_path": args.photo.name,
        "photo_dimensions_px": [width, height],
        "output_3mf": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "output_3mf_sha256": revision.sha256(OUTPUT),
        "section_z_mm": section_z,
        "exported_section_contours": contour_count,
        "calibration": {
            "method": "single scale/translation from estimated centimeter-paper grid",
            "grid_pitch_px": GRID_PITCH_PX,
            "grid_pitch_mm": GRID_PITCH_MM,
            "pixel_per_mm": scale,
            "model_left_top_reference_px": list(GRID_ORIGIN_PX),
            "grid_evidence": (
                "Autocorrelation of exposed strips finds about 52-53 px between "
                "major grid lines and about 26 px between subdivisions. The "
                "approximate ruler-photo scale is about 47 px/cm, while the grid "
                "photo estimate is about 52 px/cm. Approximate visible board "
                "extents suggest roughly 4% cross-photo scale uncertainty; camera "
                "perspective and ambiguous laminate edges prevent a tighter claim."
            ),
            "basis": (
                "estimated left/top edge of the laminated paper tableau; this "
                "photo does not show the printed frame's mating cavity edge"
            ),
            "transform_model_xy_to_photo": transform.tolist(),
        },
        "fit_scope": {
            "photo_subject": "laminated paper tableau, not the printed frame",
            "rear_panel_inner_receiving_cavity": "none; rear mesh is a full panel with mounting pins",
            "panel_envelope_mm": [revision.NEW_LENGTH, revision.SHORT_SIDE],
            "panel_envelope_policy": (
                "Retained from the explicit model dimensions; not inferred from "
                "the paper outline."
            ),
            "visual_validation_scope": (
                "Number-row/pocket registration only. The paper photo cannot "
                "validate the printed frame's outer fit or an inner cavity."
            ),
        },
        "anchor_residuals_px": [
            {
                "name": name,
                "predicted_pixel": point.tolist(),
                "observed_pixel_estimate": list(observed),
                "residual_px": float(error),
                "residual_mm": float(error / scale),
            }
            for (name, observed), point, error in zip(
                OBSERVED_ANCHORS, predicted, residuals
            )
        ],
        "photo_limitations": (
            "Field-edge pixels and the laminated left/top origin are manually "
            "estimated; anchor residuals are calibration checks, not independent "
            "measurements, and carry about 1-2 mm photo-reading uncertainty. The "
            "grid overlay supports visual row registration but does not prove "
            "frame-to-paper fit, full-assembly physical fit, or slicer printability. "
            "Camera perspective and raised laminate can introduce parallax."
        ),
        "closeups": closeups,
    }
    report_path = ROOT / "docs" / f"{OUTPUT.stem}-grid-photo-validation.json"
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "full_overlay": str(full_path),
        "closeups": closeups,
        "report": str(report_path),
        "anchor_residuals_px": [round(float(value), 1) for value in residuals],
        "contours": contour_count,
    }, indent=2))


if __name__ == "__main__":
    main()
