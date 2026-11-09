"""Build a laminate-registered tableau revision from the approved fitted 3MF."""

import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
import numpy as np
import trimesh
from build123d import Plane, Polygon, extrude

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "terraforming-mars-tableau-179mm-loch1-zapfen3.3mf"
PREVIOUS_OUTPUT = (
    ROOT / "model-sources" / "terraforming-mars-tableau"
    / "terraforming-mars-tableau-179mm-laminate-slider-cubes.3mf"
)
OUTPUT = (
    ROOT / "models"
    / "terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf"
)
REPORT = (
    ROOT / "docs"
    / "terraforming-mars-tableau-179mm-laminate-centered-blocks-validation.json"
)
EXPECTED_SOURCE_SHA256 = (
    "bbe777436d9af56f55875cf00df18dbfee49e5a0531c94c98a5895ab76892f37"
)
EXPECTED_PREVIOUS_SHA256 = (
    "713571a0d9b614d4bd900dc8f501f84246de4cee3cda14080bddcf42440f57ad"
)

CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"m": CORE, "p": PROD}
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("BambuStudio", "http://schemas.bambulab.com/package/2021")

FRONT_PATHS = (
    "3D/Objects/Body1_1.model",
    "3D/Objects/Vorderseite - PLA Transparent (Startprofil)_3.model",
)
FRONT_PLATE_PREVIEWS = tuple(
    f"Metadata/{prefix}_{plate}{suffix}.png"
    for plate in (1, 3)
    for prefix, suffix in (
        ("plate", ""),
        ("plate", "_small"),
        ("plate_no_light", ""),
    )
)
REAR_PATH = "3D/Objects/Body1_2.model"
PRINT_METADATA_ENTRY = "Metadata/ghouls_grip_print_metadata.xml"
MESH_IDS = {
    FRONT_PATHS[0]: "1",
    REAR_PATH: "3",
    FRONT_PATHS[1]: "5",
}

OLD_LENGTH = 240.401162
NEW_LENGTH = OLD_LENGTH - 2.0
NEW_EDGE = NEW_LENGTH / 2
NEW_LEFT = -NEW_EDGE
SHORT_SIDE = 179.0
LAMINATE_LENGTH = 227.0
LAMINATE_WIDTH = 168.0
PAPER_LEFT = -LAMINATE_LENGTH / 2
PAPER_TOP = LAMINATE_WIDTH / 2
FRAME_MARGIN_X = (NEW_LENGTH - LAMINATE_LENGTH) / 2
FRAME_MARGIN_Y = (SHORT_SIDE - LAMINATE_WIDTH) / 2
FOLLOWUP_REFERENCE_BOUNDS_PX = (117.0, 45.0, 704.0, 487.0)
FOLLOWUP_SLIDER_MARK_BOUNDS_PX = (390.0, 258.0, 672.0, 283.0)
FOLLOWUP_SLIDER_MARK_CENTER_PX = (
    (FOLLOWUP_SLIDER_MARK_BOUNDS_PX[0] + FOLLOWUP_SLIDER_MARK_BOUNDS_PX[2]) / 2,
    (FOLLOWUP_SLIDER_MARK_BOUNDS_PX[1] + FOLLOWUP_SLIDER_MARK_BOUNDS_PX[3]) / 2,
)
FOLLOWUP_SLIDER_MARK_SIZE_PX = (
    FOLLOWUP_SLIDER_MARK_BOUNDS_PX[2] - FOLLOWUP_SLIDER_MARK_BOUNDS_PX[0],
    FOLLOWUP_SLIDER_MARK_BOUNDS_PX[3] - FOLLOWUP_SLIDER_MARK_BOUNDS_PX[1],
)
FOLLOWUP_SCREEN_PX_PER_MM_X = (
    FOLLOWUP_REFERENCE_BOUNDS_PX[2] - FOLLOWUP_REFERENCE_BOUNDS_PX[0]
) / NEW_LENGTH
FOLLOWUP_SCREEN_PX_PER_MM_Y = (
    FOLLOWUP_REFERENCE_BOUNDS_PX[3] - FOLLOWUP_REFERENCE_BOUNDS_PX[1]
) / SHORT_SIDE
FOLLOWUP_SLIDER_MARK_CENTER_MM = np.asarray([
    (FOLLOWUP_SLIDER_MARK_CENTER_PX[0]
     - (FOLLOWUP_REFERENCE_BOUNDS_PX[0] + FOLLOWUP_REFERENCE_BOUNDS_PX[2]) / 2)
    / FOLLOWUP_SCREEN_PX_PER_MM_X,
    ((FOLLOWUP_REFERENCE_BOUNDS_PX[1] + FOLLOWUP_REFERENCE_BOUNDS_PX[3]) / 2
     - FOLLOWUP_SLIDER_MARK_CENTER_PX[1])
    / FOLLOWUP_SCREEN_PX_PER_MM_Y,
])
FOLLOWUP_SLIDER_SIZE_MM = np.asarray([
    FOLLOWUP_SLIDER_MARK_SIZE_PX[0] / FOLLOWUP_SCREEN_PX_PER_MM_X,
    FOLLOWUP_SLIDER_MARK_SIZE_PX[1] / FOLLOWUP_SCREEN_PX_PER_MM_Y,
])
LOWER_RIGHT_TRACK_SHIFT_X_MM = 2.0
NUMBER_BLOCK_SHIFTS_X_MM = {
    "upper-left -5": -1.5,
    "lower-left zero": -1.0,
    "upper-right zero": 0.5,
}
BLOCK_MARKUP_PANEL_BOUNDS_PX = (117.0, 48.0, 703.0, 490.0)
BLOCK_MARKUP_TARGET_BOUNDS_PX = {
    "upper-left -5": (220.0, 206.0, 363.0, 285.0),
    "lower-left zero": (170.0, 288.0, 321.0, 349.0),
    "upper-right zero": (518.0, 202.0, 663.0, 261.0),
}
BLOCK_MARKUP_ORIGIN_X_PX = (
    BLOCK_MARKUP_PANEL_BOUNDS_PX[0] + BLOCK_MARKUP_PANEL_BOUNDS_PX[2]
) / 2
BLOCK_MARKUP_PX_PER_MM_X = (
    BLOCK_MARKUP_PANEL_BOUNDS_PX[2] - BLOCK_MARKUP_PANEL_BOUNDS_PX[0]
) / NEW_LENGTH
BLOCK_MARKED_TARGET_CENTERS_X_MM = {
    name: (
        (bounds[0] + bounds[2]) / 2 - BLOCK_MARKUP_ORIGIN_X_PX
    ) / BLOCK_MARKUP_PX_PER_MM_X
    for name, bounds in BLOCK_MARKUP_TARGET_BOUNDS_PX.items()
}
FOLLOWUP_SELECTED_FIELD_LABELS = {
    "upper": [3, 4, 5],
    "lower": [8, 9, 10],
}
FRONT_THICKNESS = 2.5
SMALL_WINDOW_TRANSLATION_X_MM = 2.0
SMALL_WINDOW_LEFT_TRIM_MM = 6.0
SMALL_WINDOW_TOP_TRIM_MM = 1.0
SMALL_WINDOW_BOTTOM_TRIM_MM = 1.0
SMALL_WEB_THICKNESS_MM = 1.0
END_ARROW_LEDGE_THICKNESS_MM = 1.0
LOCAL_RELIEF_EPS_MM = 0.02
TRANSPARENT_FILAMENT_SLOT = 4
TRANSPARENT_FILAMENT_PROFILE = (
    "Transparent PLA slow test @Anycubic Kobra S1 0.4 nozzle"
)
TRANSPARENT_BED_TYPE = "Cool Plate"
TRANSPARENT_BED_TEMPERATURE_C = 35
TRANSPARENT_FIRST_LAYER_SPEED_MM_S = 20
TRANSPARENT_PLATE_ID = 3
SOCKET_DIAMETER = 3.0
PIN_DIAMETER = 2.6
SOCKET_FLOOR = 0.5
SOCKET_DEPTH = FRONT_THICKNESS - SOCKET_FLOOR
PIN_PROJECTION = SOCKET_DEPTH - 0.4
AXIAL_CLEARANCE = 0.4
CUBE_EDGE = 8.5
OPENING_WIDTH = 8.64
OPENING_PITCH = 9.16
PREVIOUS_LONG_SLOT_HEIGHT = 6.8
LONG_SLOT_HEIGHT = OPENING_WIDTH
SLIDER_EXTENSION_DOWN_MM = LONG_SLOT_HEIGHT - PREVIOUS_LONG_SLOT_HEIGHT
FOLLOWUP_SLIDER_CENTER_MM = FOLLOWUP_SLIDER_MARK_CENTER_MM - np.asarray([
    0.0, SLIDER_EXTENSION_DOWN_MM / 2
])
MIN_SLOT_CLEARANCE = 0.5
TRANSITION_RAMP_BOOLEAN_EPS_MM = 0.02
TRANSITION_RAMP_RUN_MM = OPENING_WIDTH
ADJACENT_CUTOUT_SHIFT_X = -3.95
PHOTO_PX_PER_MM = 4.07
PHOTO_REFERENCE_CENTER_PX = (673.5, 411.5)
PHOTO_WINDOW_INSET_PX = 2.0
PHOTO_WINDOW_BOXES_PX = (
    (255.0, 118.0, 599.0, 299.0),
    (607.0, 112.0, 840.0, 301.0),
    (854.0, 113.0, 1085.0, 299.0),
    (253.0, 553.0, 541.0, 710.0),
    (554.0, 552.0, 808.0, 709.0),
    (811.0, 548.0, 1091.0, 711.0),
)
RESOURCE_WINDOW_HEIGHT_MM = 43.0
UPPER_LEFT_WINDOW_WIDTH_MM = 86.0
LOWER_RIGHT_WINDOW_MIN_WIDTH_MM = 69.0
PHOTO_SLIDER_BOX_PX = (629.0, 403.0, 1096.0, 460.0)
ROW_ANCHORS = (
    {"name": "lower-left zero", "offset_x": 20.0, "row_y": -17.33,
     "top_distance": 96.0, "side": "left"},
    {"name": "lower-middle zero", "offset_x": 89.0, "row_y": -17.33,
     "top_distance": 96.0, "side": "middle"},
    {"name": "lower-right zero", "offset_x": 155.0, "row_y": -17.33,
     "top_distance": 96.0, "side": "right"},
    {"name": "upper-left -5", "offset_x": 47.0, "row_y": 18.99,
     "top_distance": 61.0, "side": "left"},
    {"name": "upper-middle zero", "offset_x": 99.6, "row_y": 18.26,
     "top_distance": 61.0, "side": "middle"},
    {"name": "upper-right zero", "offset_x": 159.5, "row_y": 18.26,
     "top_distance": 61.0, "side": "right"},
)
TOL = 3e-4

SOURCE_MOUNTS = np.asarray([
    (0.0, -86.4819752), (0.0, 86.4819752),
    (-117.1825565, -86.4819752), (-117.1825565, 0.0),
    (-117.1825565, 86.4819752), (117.1825565, -86.4819752),
    (117.1825565, 0.0), (117.1825565, 86.4819752),
])
SOCKET_BOTTOM = -1.56104651
OLD_SOCKET_FLOOR = 1.0406976744186047
PIN_BASE = -0.20813953488372094
PIN_SHOULDER = 0.9366279069767442
OLD_PIN_TIP = 2.2895348837209303
EXPECTED_TRACK_COUNTS = (10, 10, 10, 15, 10, 10)


def photo_box_to_model(box, inset_px=PHOTO_WINDOW_INSET_PX):
    x1, y1, x2, y2 = box
    x1 += inset_px
    y1 += inset_px
    x2 -= inset_px
    y2 -= inset_px
    center_x, center_y = PHOTO_REFERENCE_CENTER_PX
    low = np.asarray([
        (x1 - center_x) / PHOTO_PX_PER_MM,
        (center_y - y2) / PHOTO_PX_PER_MM,
    ])
    high = np.asarray([
        (x2 - center_x) / PHOTO_PX_PER_MM,
        (center_y - y1) / PHOTO_PX_PER_MM,
    ])
    return {
        "center_mm": ((low + high) / 2).tolist(),
        "size_mm": (high - low).tolist(),
        "bounds_mm": [*low.tolist(), *high.tolist()],
    }


def requested_window_specs(boxes):
    windows = []
    for index, box in enumerate(boxes):
        item = photo_box_to_model(box)
        center = np.asarray(item["center_mm"], dtype=float)
        size = np.asarray(item["size_mm"], dtype=float)
        size[1] = RESOURCE_WINDOW_HEIGHT_MM
        if index == 0:
            right_edge = center[0] + size[0] / 2
            size[0] = UPPER_LEFT_WINDOW_WIDTH_MM
            center[0] = right_edge - size[0] / 2
        elif index == 5:
            left_edge = center[0] - size[0] / 2
            size[0] = max(size[0], LOWER_RIGHT_WINDOW_MIN_WIDTH_MM)
            center[0] = left_edge + size[0] / 2
        low = center - size / 2
        high = center + size / 2
        windows.append({
            "center_mm": center.tolist(),
            "size_mm": size.tolist(),
            "bounds_mm": [*low.tolist(), *high.tolist()],
        })
    return tuple(windows)


TARGET_WINDOWS = requested_window_specs(PHOTO_WINDOW_BOXES_PX)
SLIDER_AREA = photo_box_to_model(PHOTO_SLIDER_BOX_PX)
TRACK_ROW_LABELS = (
    ((0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
    ((0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
    ((0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
    ((-5, -4, -3, -2, -1), (0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
    ((0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
    ((0, 1, 2, 3, 4, 5), (6, 7, 8, 9, 10)),
)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def parse_3mf_transform(value):
    values = np.asarray([float(item) for item in value.split()], dtype=float)
    require(len(values) == 12, "Invalid 3MF transform")
    rotation = values[:9].reshape((3, 3)).T
    translation = values[9:12]
    return rotation, translation


def serialize_3mf_transform(rotation, translation):
    values = np.concatenate((rotation.T.reshape(-1), translation))
    values[np.abs(values) < 1e-12] = 0.0
    for index, value in enumerate(values):
        rounded = round(float(value))
        if abs(float(value) - rounded) < 1e-12:
            values[index] = rounded
    return " ".join(f"{value:.12g}" for value in values)


def rotate_front_build_items(entries):
    scene = ET.fromstring(entries["3D/3dmodel.model"])
    resources = {
        obj.get("id"): obj
        for obj in scene.findall("./m:resources/m:object", NS)
    }
    rotate_z_180 = np.diag([-1.0, -1.0, 1.0])
    results = []
    for item_index, item in enumerate(
        scene.findall("./m:build/m:item", NS), start=1
    ):
        assembly = resources.get(item.get("objectid"))
        component = (
            assembly.find("./m:components/m:component", NS)
            if assembly is not None else None
        )
        if component is None:
            continue
        mesh_path = component.get(f"{{{PROD}}}path", "").lstrip("/")
        if mesh_path not in FRONT_PATHS:
            continue

        mesh_root = ET.fromstring(entries[mesh_path])
        vertex_nodes = mesh_root.findall(
            "./m:resources/m:object/m:mesh/m:vertices/m:vertex", NS
        )
        require(vertex_nodes, f"No mesh vertices found in {mesh_path}")
        local_vertices = np.asarray([
            [float(vertex.get(axis)) for axis in ("x", "y", "z")]
            for vertex in vertex_nodes
        ])
        component_rotation, component_translation = parse_3mf_transform(
            component.get("transform")
        )
        local_vertices = (
            component_rotation @ local_vertices.T
        ).T + component_translation
        local_center = (
            local_vertices.min(axis=0) + local_vertices.max(axis=0)
        ) / 2

        current_rotation, current_translation = parse_3mf_transform(
            item.get("transform")
        )
        rotated = rotate_z_180 @ current_rotation
        rotated_translation = (
            current_translation + (current_rotation - rotated) @ local_center
        )
        before_vertices = (
            current_rotation @ local_vertices.T
        ).T + current_translation
        after_vertices = (
            rotated @ local_vertices.T
        ).T + rotated_translation
        before_bounds = np.stack(
            (before_vertices.min(axis=0), before_vertices.max(axis=0))
        )
        after_bounds = np.stack(
            (after_vertices.min(axis=0), after_vertices.max(axis=0))
        )
        require(
            np.allclose(before_bounds, after_bounds, atol=TOL, rtol=0),
            f"In-place rotation changed plate bounds for {mesh_path}",
        )
        require(
            np.allclose(
                before_vertices[:, 2], after_vertices[:, 2],
                atol=TOL, rtol=0,
            ),
            f"In-place rotation changed bed contact for {mesh_path}",
        )
        item.set(
            "transform",
            serialize_3mf_transform(rotated, rotated_translation),
        )
        results.append({
            "plate_index": item_index,
            "build_object_id": item.get("objectid"),
            "mesh_path": mesh_path,
            "rotation_axis": "build Z",
            "rotation_degrees": 180,
            "before_rotation_matrix": current_rotation.tolist(),
            "after_rotation_matrix": rotated.tolist(),
            "translation_mm": rotated_translation.tolist(),
            "world_bounds_mm": after_bounds.tolist(),
            "bed_z_bounds_mm": [
                float(after_bounds[0, 2]), float(after_bounds[1, 2])
            ],
        })
    require(
        {record["mesh_path"] for record in results} == set(FRONT_PATHS),
        "Expected exactly one build item for each front panel",
    )
    for path in FRONT_PLATE_PREVIEWS:
        encoded = np.frombuffer(entries[path], dtype=np.uint8)
        image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
        require(image is not None, f"Could not decode 3MF preview {path}")
        success, rotated_preview = cv2.imencode(
            ".png", cv2.rotate(image, cv2.ROTATE_180)
        )
        require(success, f"Could not rotate 3MF preview {path}")
        entries[path] = rotated_preview.tobytes()
    entries["3D/3dmodel.model"] = ET.tostring(
        scene, encoding="utf-8", xml_declaration=True
    )
    return results


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plate_bed_type(model_settings_bytes, plater_id):
    config = ET.fromstring(model_settings_bytes)
    for plate in config.findall("plate"):
        metadata = {
            item.get("key"): item.get("value")
            for item in plate.findall("metadata")
        }
        if metadata.get("plater_id") == str(plater_id):
            return metadata.get("bed_type")
    return None


def apply_transparent_filament_settings(project_bytes, model_settings_bytes):
    settings = json.loads(project_bytes)
    original_slot_count = len(settings["filament_settings_id"])
    require(original_slot_count == 4,
            f"Expected four source filament slots, got {original_slot_count}")
    for key, value in list(settings.items()):
        if (
            key != "printable_area"
            and isinstance(value, list)
            and len(value) == original_slot_count
        ):
            settings[key] = value[:]
            settings[key][-1] = value[0]

    def set_filament_value(key, value):
        values = settings.get(key)
        require(
            isinstance(values, list)
            and len(values) == original_slot_count,
            f"Cannot set slot {TRANSPARENT_FILAMENT_SLOT} setting {key}",
        )
        values[TRANSPARENT_FILAMENT_SLOT - 1] = str(value)

    set_filament_value("filament_settings_id", TRANSPARENT_FILAMENT_PROFILE)
    set_filament_value("nozzle_temperature", 220)
    set_filament_value("nozzle_temperature_BRASS", 220)
    set_filament_value("nozzle_temperature_initial_layer", 220)
    set_filament_value("nozzle_temperature_initial_layer_BRASS", 220)
    set_filament_value("cool_plate_temp", TRANSPARENT_BED_TEMPERATURE_C)
    set_filament_value(
        "cool_plate_temp_initial_layer", TRANSPARENT_BED_TEMPERATURE_C
    )
    for key in (
        "fan_min_speed",
        "fan_min_speed_BRASS",
        "fan_min_speed_HS",
        "fan_max_speed",
        "fan_max_speed_BRASS",
        "fan_max_speed_HS",
        "fan_speed_after_x_layers",
    ):
        set_filament_value(key, 20)
    set_filament_value("additional_cooling_fan_speed", 0)
    different = settings["different_settings_to_system"]
    require(len(different) == original_slot_count + 2,
            "Unexpected different_settings_to_system slot count")
    process_overrides = different[0].split(";")
    for key in (
        "top_shell_layers",
        "top_shell_thickness",
        "infill_direction",
        "solid_infill_direction",
        "initial_layer_speed",
    ):
        if key not in process_overrides:
            process_overrides.append(key)
    different[0] = ";".join(process_overrides)
    different[TRANSPARENT_FILAMENT_SLOT + 1] = (
        "filament_settings_id;cool_plate_temp;"
        "cool_plate_temp_initial_layer;nozzle_temperature;"
        "nozzle_temperature_BRASS;nozzle_temperature_initial_layer;"
        "nozzle_temperature_initial_layer_BRASS;fan_min_speed;"
        "fan_min_speed_BRASS;fan_min_speed_HS;fan_max_speed;"
        "fan_max_speed_BRASS;fan_max_speed_HS;fan_speed_after_x_layers;"
        "additional_cooling_fan_speed"
    )

    config = ET.fromstring(model_settings_bytes)
    objects = {
        item.get("id"): item for item in config.findall("object")
    }
    transparent = objects.get("6")
    require(transparent is not None, "Transparent front object 6 is missing")
    metadata = {
        item.get("key"): item for item in transparent.findall("metadata")
    }
    require(metadata.get("name").get("value")
            == "Vorderseite - PLA Transparent (Startprofil)",
            "Object 6 is not the transparent front")
    metadata["extruder"].set("value", str(TRANSPARENT_FILAMENT_SLOT))
    object_settings = {
        "layer_height": "0.1",
        "initial_layer_speed": str(TRANSPARENT_FIRST_LAYER_SPEED_MM_S),
        "outer_wall_speed": "20",
        "inner_wall_speed": "20",
        "solid_infill_speed": "20",
        "internal_solid_infill_speed": "20",
        "sparse_infill_speed": "20",
        "gap_infill_speed": "20",
        "top_surface_speed": "20",
        "sparse_infill_pattern": "alignedrectilinear",
        "internal_solid_infill_pattern": "alignedrectilinear",
        "top_surface_pattern": "alignedrectilinear",
        "bottom_surface_pattern": "alignedrectilinear",
        "infill_direction": "90",
        "solid_infill_direction": "90",
        "sparse_infill_rotate_template": "0",
        "solid_infill_rotate_template": "0",
        "ironing_type": "top",
        "top_shell_layers": "2",
        "top_shell_thickness": "0.2",
        "bottom_shell_layers": "0",
        "wall_loops": "2",
    }
    for key, value in object_settings.items():
        existing = metadata.get(key)
        if existing is None:
            existing = ET.SubElement(transparent, "metadata", key=key)
            metadata[key] = existing
        existing.set("value", value)

    transparent_plate = None
    for plate in config.findall("plate"):
        plate_metadata = {
            item.get("key"): item for item in plate.findall("metadata")
        }
        if plate_metadata.get("plater_id", {}).get("value") == str(
            TRANSPARENT_PLATE_ID
        ):
            transparent_plate = plate
            break
    require(
        transparent_plate is not None,
        f"Transparent front plate {TRANSPARENT_PLATE_ID} is missing",
    )
    plate_metadata = {
        item.get("key"): item
        for item in transparent_plate.findall("metadata")
    }
    bed_type_metadata = plate_metadata.get("bed_type")
    if bed_type_metadata is None:
        bed_type_metadata = ET.SubElement(
            transparent_plate, "metadata", key="bed_type"
        )
    bed_type_metadata.set("value", TRANSPARENT_BED_TYPE)
    return (
        (json.dumps(settings, indent=2) + "\n").encode("utf-8"),
        ET.tostring(config, encoding="utf-8", xml_declaration=True),
        object_settings,
    )


def load_previous_front():
    with zipfile.ZipFile(PREVIOUS_OUTPUT) as archive:
        _, _, mesh = as_mesh(
            archive.read(FRONT_PATHS[0]),
            MESH_IDS[FRONT_PATHS[0]],
        )
    return mesh


def verify_filament_scope(
    original, revised, original_model_bytes, revised_model_bytes,
    transparent_object_settings,
):
    for key, old_value in original.items():
        new_value = revised.get(key)
        if key == "different_settings_to_system":
            expected_process_flags = old_value[0].split(";")
            for setting in (
                "top_shell_layers",
                "top_shell_thickness",
                "infill_direction",
                "solid_infill_direction",
                "initial_layer_speed",
            ):
                if setting not in expected_process_flags:
                    expected_process_flags.append(setting)
            expected_machine_flags = list(
                filter(None, old_value[1].split(";"))
            )
            require(
                new_value[0] == ";".join(expected_process_flags)
                and new_value[1] == ";".join(expected_machine_flags)
                and new_value[2:5] == old_value[2:5],
                "Only the selected bed type and transparent-front surface/raster flags may change",
            )
            expected_filament_flags = {
                "filament_settings_id",
                "cool_plate_temp",
                "cool_plate_temp_initial_layer",
                "nozzle_temperature",
                "nozzle_temperature_BRASS",
                "nozzle_temperature_initial_layer",
                "nozzle_temperature_initial_layer_BRASS",
                "fan_min_speed",
                "fan_min_speed_BRASS",
                "fan_min_speed_HS",
                "fan_max_speed",
                "fan_max_speed_BRASS",
                "fan_max_speed_HS",
                "fan_speed_after_x_layers",
                "additional_cooling_fan_speed",
            }
            require(
                set(filter(None, new_value[5].split(";")))
                == expected_filament_flags,
                "Transparent filament override flags are incomplete",
            )
        elif (
            key != "printable_area"
            and isinstance(old_value, list)
            and len(old_value) == 4
        ):
            require(
                isinstance(new_value, list)
                and len(new_value) == 4
                and new_value[:3] == old_value[:3],
                f"Original filament slots changed for {key}",
            )
        else:
            require(new_value == old_value,
                    f"Unrelated project setting changed: {key}")

    require(
        revised.get("curr_bed_type") == original.get("curr_bed_type"),
        "The global bed type must remain unchanged",
    )
    require(
        plate_bed_type(revised_model_bytes, TRANSPARENT_PLATE_ID)
        == TRANSPARENT_BED_TYPE,
        "Cool Plate was not selected for the transparent-front plate",
    )
    require(
        plate_bed_type(original_model_bytes, TRANSPARENT_PLATE_ID) is None,
        "Expected the source transparent-front plate to inherit the global bed type",
    )

    profile = revised["filament_settings_id"][TRANSPARENT_FILAMENT_SLOT - 1]
    require(profile == TRANSPARENT_FILAMENT_PROFILE,
            "Transparent filament profile name was not persisted")
    for key in ("cool_plate_temp", "cool_plate_temp_initial_layer"):
        require(
            revised[key][TRANSPARENT_FILAMENT_SLOT - 1]
            == str(TRANSPARENT_BED_TEMPERATURE_C),
            f"Transparent filament {key} must be {TRANSPARENT_BED_TEMPERATURE_C} C",
        )
    require(
        revised["filament_flow_ratio"][TRANSPARENT_FILAMENT_SLOT - 1] == "0.98",
        "Transparent filament flow ratio changed from the calibrated value",
    )
    require(
        revised["additional_cooling_fan_speed"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ] == "0",
        "Auxiliary/side fan is not disabled for the transparent filament",
    )
    for key in ("filament_start_gcode", "filament_end_gcode"):
        if key in original:
            require(
                revised[key][TRANSPARENT_FILAMENT_SLOT - 1]
                == original[key][0],
                f"Transparent filament native {key} was not preserved",
            )

    old_config = ET.fromstring(original_model_bytes)
    new_config = ET.fromstring(revised_model_bytes)
    old_objects = {
        item.get("id"): item for item in old_config.findall("object")
    }
    new_objects = {
        item.get("id"): item for item in new_config.findall("object")
    }
    require(old_objects.keys() == new_objects.keys(),
            "Object inventory changed")
    for object_id, old_object in old_objects.items():
        new_object = new_objects[object_id]
        if object_id != "6":
            require(
                ET.tostring(old_object) == ET.tostring(new_object),
                f"Non-transparent object settings changed for {object_id}",
            )
            continue
        old_metadata = {
            item.get("key"): item.get("value")
            for item in old_object.findall("metadata")
        }
        old_parts = [ET.tostring(item) for item in old_object.findall("part")]
        new_parts = [ET.tostring(item) for item in new_object.findall("part")]
        require(old_parts == new_parts,
                "Transparent-front part metadata or geometry mapping changed")
        new_metadata = {
            item.get("key"): item.get("value")
            for item in new_object.findall("metadata")
        }
        for key, value in old_metadata.items():
            if key not in transparent_object_settings and key != "extruder":
                require(new_metadata.get(key) == value,
                        f"Unrelated transparent-front setting changed: {key}")
        require(
            new_metadata.get("extruder") == str(TRANSPARENT_FILAMENT_SLOT),
            "Transparent front is not assigned to its dedicated filament slot",
        )
        for key, value in transparent_object_settings.items():
            require(new_metadata.get(key) == value,
                    f"Transparent-front override missing: {key}")
    return True


def unverified_print_metadata(settings, model_settings_bytes):
    model_settings = ET.fromstring(model_settings_bytes)
    active_slots = sorted({
        int(item.get("value"))
        for obj in model_settings.findall("object")
        for item in obj.findall("metadata")
        if item.get("key") == "extruder"
    })
    profiles = settings.get("filament_settings_id", [])
    colors = settings.get("filament_colour", [])
    materials = settings.get("filament_type", [])
    active_profiles = [
        profiles[index - 1]
        for index in active_slots
        if 0 < index <= len(profiles)
    ]
    active_colors = [
        colors[index - 1]
        for index in active_slots
        if 0 < index <= len(colors)
    ]
    unknown_stats = {
        "status": "not-verified",
        "estimatedPrintTimeSeconds": "unknown",
        "filamentUsageGrams": "unknown",
        "filamentUsageMillimeters": "unknown",
        "filamentUsageCubicMillimeters": "unknown",
        "supportFilamentGrams": "unknown",
        "supportFilamentMillimeters": "unknown",
        "supportFilamentCubicMillimeters": "unknown",
    }
    plate_details = []
    for index, profile in enumerate(active_profiles, start=1):
        bed_type = (
            plate_bed_type(model_settings_bytes, index)
            or settings.get("curr_bed_type", "unknown")
        )
        plate_details.append({
            "name": f"Plate {index} - {profile}",
            "bedType": bed_type,
            **unknown_stats,
        })
    bed_type_details = [
        f"Plate {index}: {details['bedType']}"
        for index, details in enumerate(plate_details, start=1)
        if details["bedType"] != settings.get("curr_bed_type", "unknown")
    ]
    values = {
        **unknown_stats,
        "plateCount": str(len(plate_details)),
        "plateDetails": json.dumps(
            plate_details, separators=(",", ":"), sort_keys=True
        ),
        "filamentUsageByColor": "{}",
        "printerProfile": settings.get("printer_settings_id", "unknown"),
        "nozzleDiameterMm": "0.4",
        "processProfile": settings.get(
            "process_settings_id"
        ) or "Embedded project settings",
        "layerHeightMm": (
            f"{settings.get('layer_height', 'unknown')} global; "
            "0.10 transparent front object"
        ),
        "filamentProfile": ", ".join(dict.fromkeys(active_profiles)),
        "materialType": ", ".join(dict.fromkeys(materials)),
        "materialColorHex": ", ".join(active_colors),
        "bedType": "; ".join([
            f"Global: {settings.get('curr_bed_type', 'unknown')}",
            *bed_type_details,
        ]),
        "wallLoops": "Per-object overrides; transparent front=2",
        "infillDensity": (
            "Per-object overrides; transparent front=100% aligned rectilinear"
        ),
        "supportPolicy": (
            f"Global enable_support={settings.get('enable_support', 'unknown')}; "
            f"{settings.get('support_type', 'unknown')}; "
            "inherited disabled setting, not a support-free validation"
        ),
        "seamPosition": settings.get("seam_position", "unknown"),
        "ironingType": settings.get("ironing_type", "unknown"),
        "objectCount": str(len(active_slots)),
        "validationNotes": (
            "This centered-block artifact was not sliced. Prior attempts on "
            "the preceding slider/cube layout yielded no G-code: OrcaSlicer "
            "2.0.0.0 exited -18 because "
            "retraction_distances_when_cut=0 is outside [10,18]; "
            "AnycubicSlicerNext 2.0.0.3 crashed before producing G-code. "
            "Support is inherited disabled (enable_support=0)."
        ),
    }
    root = ET.Element("ghouls-grip-print-metadata", version="1")
    for key, value in values.items():
        ET.SubElement(root, "metadata", name=key, value=str(value))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def as_mesh(model_bytes, object_id):
    root = ET.fromstring(model_bytes)
    obj = root.find(f"./m:resources/m:object[@id='{object_id}']", NS)
    require(obj is not None, f"Missing mesh object {object_id}")
    node = obj.find("m:mesh", NS)
    require(node is not None, f"Object {object_id} has no mesh")
    vertices = np.asarray([
        [float(vertex.get(axis)) for axis in ("x", "y", "z")]
        for vertex in node.findall("./m:vertices/m:vertex", NS)
    ], dtype=float)
    faces = np.asarray([
        [int(face.get(axis)) for axis in ("v1", "v2", "v3")]
        for face in node.findall("./m:triangles/m:triangle", NS)
    ], dtype=np.int64)
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    check_mesh(mesh)
    return root, node, mesh


def check_mesh(mesh):
    require(mesh.is_watertight, "Mesh is not watertight")
    require(mesh.is_winding_consistent, "Inconsistent winding")
    require(mesh.volume > 0, "Nonpositive mesh volume")
    require(np.min(mesh.area_faces) > 1e-10, "Degenerate triangles")
    require(len(mesh.split(only_watertight=False)) == 1, "Disconnected panel")


def mesh_xml(root, mesh_node, mesh):
    for child in list(mesh_node):
        mesh_node.remove(child)
    vertices = ET.SubElement(mesh_node, f"{{{CORE}}}vertices")
    for vertex in mesh.vertices:
        ET.SubElement(
            vertices, f"{{{CORE}}}vertex",
            dict(zip(("x", "y", "z"), (f"{value:.12g}" for value in vertex))),
        )
    triangles = ET.SubElement(mesh_node, f"{{{CORE}}}triangles")
    for face in mesh.faces:
        ET.SubElement(
            triangles, f"{{{CORE}}}triangle",
            dict(zip(("v1", "v2", "v3"), map(str, face))),
        )
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def section_loops(mesh, z):
    section = mesh.section(
        plane_normal=[0, 0, 1],
        plane_origin=[0, 0, z],
    )
    require(section is not None, "Missing cube-opening section")
    records = []
    for loop in section.discrete:
        if len(loop) < 4 or np.linalg.norm(loop[0] - loop[-1]) > TOL:
            continue
        low = loop[:, :2].min(axis=0)
        high = loop[:, :2].max(axis=0)
        records.append(((low + high) / 2, high - low))
    return records


def square_opening_data(mesh, z):
    holes = []
    sizes_found = []
    for center, size in section_loops(mesh, z):
        if np.all((size > 8.5) & (size < 8.8)):
            holes.append(center)
            sizes_found.append(size)
    require(len(holes) == 65, f"Expected 65 cube openings, found {len(holes)}")
    return np.asarray(holes), np.asarray(sizes_found)


def square_holes(mesh, z):
    return square_opening_data(mesh, z)[0]


def double_width_slots(mesh, z):
    slots = [
        (center, size) for center, size in section_loops(mesh, z)
        if 17.5 < size.max() < 18.2
        and 8.5 < size.min() < 8.8
    ]
    require(len(slots) == 6, f"Expected six cube-track end slots, found {len(slots)}")
    centers = np.asarray([center for center, _ in slots])
    sizes = np.asarray([size for _, size in slots])
    return centers, sizes


def end_slot_back_profiles(mesh, slot_centers):
    back_z = float(mesh.bounds[0, 2]) + LOCAL_RELIEF_EPS_MM
    section = mesh.section(
        plane_normal=[0, 0, 1],
        plane_origin=[0, 0, back_z],
    )
    require(section is not None, "Missing end-slot back profile section")
    loops = []
    for points in section.discrete:
        if len(points) < 4 or np.linalg.norm(points[0] - points[-1]) > TOL:
            continue
        low = points[:, :2].min(axis=0)
        high = points[:, :2].max(axis=0)
        center = (low + high) / 2
        size = high - low
        if 10.5 < size[0] < 12.0 and 8.3 < size[1] < 8.9:
            loops.append((points[:, :2].copy(), center, size))

    profiles = []
    for slot_center in slot_centers:
        candidates = [
            item for item in loops
            if np.linalg.norm(item[1] - slot_center) < 6.0
        ]
        require(
            len(candidates) == 1,
            f"Expected one source arrow profile near {slot_center.tolist()}, "
            f"found {len(candidates)}",
        )
        points, center, size = candidates[0]
        local_points = points - slot_center
        if np.linalg.norm(local_points[0] - local_points[-1]) < TOL:
            local_points = local_points[:-1]
        keep = np.ones(len(local_points), dtype=bool)
        keep[1:] = (
            np.linalg.norm(np.diff(local_points, axis=0), axis=1) > 1e-5
        )
        local_points = local_points[keep]
        require(len(local_points) >= 6,
                "Source arrow profile has too few unique points")
        profiles.append({
            "size_mm": size.tolist(),
            "center_offset_mm": (center - slot_center).tolist(),
            "points_local_mm": local_points.tolist(),
        })
    return profiles


def long_horizontal_slot(mesh, z, expected_height):
    slots = [
        (center, size) for center, size in section_loops(mesh, z)
        if 100 < size[0] < 120
        and abs(size[1] - expected_height) < 0.2
    ]
    require(len(slots) == 1,
            f"Expected one horizontal slot at {expected_height} mm height")
    return slots[0]


def adjacent_cutout(mesh, z):
    cutouts = [
        (center, size) for center, size in section_loops(mesh, z)
        if 17.5 < size[0] < 25.5
        and 12.5 < size[1] < 17.0
        and center[0] < -80.0
    ]
    require(len(cutouts) == 1,
            f"Expected one adjacent cube-zone cutout, found {len(cutouts)}")
    return cutouts[0]


def resource_window_loops(mesh, z, allow_transition_merge=False):
    max_width = 160.0 if allow_transition_merge else 100.0
    windows = [
        (center, size) for center, size in section_loops(mesh, z)
        if 35.0 < size[0] < max_width and 20.0 < size[1] < 60.0
    ]
    expected_counts = (5, 6) if allow_transition_merge else (6,)
    require(len(windows) in expected_counts,
            f"Unexpected resource-window section count: {len(windows)}")
    return sorted(windows, key=lambda item: (-int(item[0][1] > 0), item[0][0]))


def measure_window_web(mesh, first_index, second_index, z):
    windows = resource_window_loops(mesh, z)
    first_center, first_size = windows[first_index - 1]
    second_center, second_size = windows[second_index - 1]
    return float(
        second_center[0] - second_size[0] / 2
        - first_center[0] - first_size[0] / 2
    )


def add_window_transition_ramp(mesh):
    windows = resource_window_loops(mesh, 0.0)
    window5_center, window5_size = windows[4]
    window6_center, window6_size = windows[5]
    window5_left_x = float(window5_center[0] - window5_size[0] / 2)
    window5_right_x = float(window5_center[0] + window5_size[0] / 2)
    window6_left_x = float(window6_center[0] - window6_size[0] / 2)
    existing_gap = window6_left_x - window5_right_x
    require(existing_gap > 0.8,
            f"Window 5/6 divider is unexpectedly narrow: {existing_gap:.3f} mm")

    overlap_y_min = max(
        window5_center[1] - window5_size[1] / 2,
        window6_center[1] - window6_size[1] / 2,
    )
    overlap_y_max = min(
        window5_center[1] + window5_size[1] / 2,
        window6_center[1] + window6_size[1] / 2,
    )
    ramp_length_y = overlap_y_max - overlap_y_min
    require(ramp_length_y > CUBE_EDGE,
            "The shared window divider is too short for a cube transfer")
    y_min, y_max = overlap_y_min, overlap_y_max

    z_min = float(mesh.bounds[0, 2])
    z_max = float(mesh.bounds[1, 2])
    # Keep the high endpoint on window 6's left edge so its specified 69 mm
    # opening is not narrowed; gain ramp run by extending only into window 5.
    ramp_high_x = window6_left_x
    ramp_low_x = ramp_high_x - TRANSITION_RAMP_RUN_MM
    window5_opening_after_ramp_mm = ramp_low_x - window5_left_x
    require(window5_opening_after_ramp_mm >= OPENING_WIDTH,
            "The widened ramp would reduce window 5 below the cube aperture")
    require(window6_size[0] >= LOWER_RIGHT_WINDOW_MIN_WIDTH_MM - TOL,
            "Window 6 is already below its user-requested minimum width")
    ramp_run_x = ramp_high_x - ramp_low_x
    require(abs(ramp_run_x - TRANSITION_RAMP_RUN_MM) < TOL,
            "The widened ramp run does not match the selected cube aperture")

    epsilon = TRANSITION_RAMP_BOOLEAN_EPS_MM
    ramp_profile = Plane.XZ * Polygon(
        (ramp_low_x, z_min),
        (ramp_high_x, z_min),
        (ramp_high_x, z_max),
        align=None,
    )
    cut_profile = Plane.XZ * Polygon(
        (ramp_low_x, z_min - epsilon),
        (ramp_high_x, z_max - epsilon),
        (ramp_high_x, z_max + epsilon),
        (ramp_low_x, z_max + epsilon),
        align=None,
    )
    ramp_shape = extrude(ramp_profile, amount=ramp_length_y)
    cut_shape = extrude(cut_profile, amount=ramp_length_y)
    ramp_shape = ramp_shape.translate((0, y_max, 0))
    cut_shape = cut_shape.translate((0, y_max, 0))

    def to_mesh(shape):
        vertices, faces = shape.tessellate(0.01)
        result = trimesh.Trimesh(
            vertices=[tuple(vertex) for vertex in vertices],
            faces=faces,
            process=True,
        )
        check_mesh(result)
        return result

    cut_mesh = trimesh.boolean.difference(
        [mesh, to_mesh(cut_shape)], engine="manifold"
    )
    check_mesh(cut_mesh)
    volume_before = float(mesh.volume)
    ramped = trimesh.boolean.union(
        [cut_mesh, to_mesh(ramp_shape)], engine="manifold"
    )
    check_mesh(ramped)
    volume_added = float(ramped.volume) - volume_before
    require(volume_added > 1.0,
            "The solid window 5/6 ramp did not add the intended material")
    reference_web = measure_window_web(
        mesh, 4, 5, float(mesh.bounds[0, 2]) + 0.05
    )
    return ramped, {
        "windows": ["lower-middle (5)", "lower-right (6)"],
        "feature_type": "solid_additive_ramp",
        "original_divider_width_mm": existing_gap,
        "target_ramp_run_mm": TRANSITION_RAMP_RUN_MM,
        "window5_opening_after_ramp_mm": window5_opening_after_ramp_mm,
        "window6_opening_width_preserved_mm": float(window6_size[0]),
        "overlap_y_bounds_mm": [overlap_y_min, overlap_y_max],
        "ramp_y_bounds_mm": [y_min, y_max],
        "ramp_span_y_mm": ramp_length_y,
        "reference_web_4_to5_mm": reference_web,
        "ramp_cross_slope_width_mm": ramp_run_x,
        "low_edge_x_mm": ramp_low_x,
        "high_edge_x_mm": ramp_high_x,
        "slope_rises_with_increasing_model_x": True,
        "physical_view_x_reversed_from_model": False,
        "movement_direction_in_printed_front_view": "window 5 -> window 6, left to right",
        "window6_left_edge_x_mm": window6_left_x,
        "window5_inner_edge_x_mm": window5_right_x,
        "slope_run_x_mm": ramp_run_x,
        "ramp_depth_z_mm": z_max - z_min,
        "ramp_angle_from_front_face_deg": float(np.degrees(np.arctan2(
            z_max - z_min, ramp_run_x
        ))),
        "y_span_mm": [float(y_min), float(y_max)],
        "rear_face_z_mm": z_min,
        "front_face_z_mm": z_max,
        "added_volume_mm3": volume_added,
        "cube_edge_mm": CUBE_EDGE,
        "physical_cube_transfer_tested": False,
    }


def verify_window_transition_ramp(mesh, expected):
    z_min = float(mesh.bounds[0, 2])
    z_max = float(mesh.bounds[1, 2])
    y_min, y_max = expected["y_span_mm"]
    y_center = (y_min + y_max) / 2
    ramp_low_x = expected["low_edge_x_mm"]
    ramp_high_x = expected["high_edge_x_mm"]
    ramp_run_x = ramp_high_x - ramp_low_x
    z_depth = z_max - z_min
    slope = z_depth / ramp_run_x
    profile_y_levels = np.linspace(y_min + 0.02, y_max - 0.02, 3)
    line_checks = []
    top_edge_widths = []
    for profile_y in profile_y_levels:
        section = mesh.section(
            plane_normal=[0, 1, 0],
            plane_origin=[0, profile_y, 0],
        )
        require(section is not None, "Missing exported ramp cross-section")
        line_points = []
        section_points = []
        for curve in section.discrete:
            points = curve[:, [0, 2]]
            section_points.extend(points.tolist())
            on_profile = (
                (points[:, 0] >= ramp_low_x - TOL)
                & (points[:, 0] <= ramp_high_x + TOL)
                & (np.abs(
                    points[:, 1]
                    - (z_min + (points[:, 0] - ramp_low_x) * slope)
                ) <= 1e-4)
            )
            line_points.extend(points[on_profile].tolist())
        line_points = np.asarray(line_points, dtype=float)
        require(
            len(line_points) >= 2
            and abs(float(line_points[:, 0].min()) - ramp_low_x) < TOL
            and abs(float(line_points[:, 0].max()) - ramp_high_x) < TOL,
            "The exported ramp does not have one continuous low-to-high profile",
        )
        ordered = line_points[np.argsort(line_points[:, 0])]
        require(
            abs(float(ordered[0, 1]) - z_min) < TOL
            and abs(float(ordered[-1, 1]) - z_max) < TOL,
            "The ramp endpoints do not span the complete panel thickness",
        )
        require(
            bool(np.all(np.diff(ordered[:, 1]) >= -TOL)),
            "The exported ramp reverses or steps downward toward window 6",
        )
        top_points = np.asarray(section_points, dtype=float)
        top_points = top_points[
            (top_points[:, 0] >= ramp_low_x - TOL)
            & (top_points[:, 0] <= ramp_high_x + TOL)
            & (np.abs(top_points[:, 1] - z_max) < TOL)
        ]
        top_width = (
            float(top_points[:, 0].max() - top_points[:, 0].min())
            if len(top_points) else float("inf")
        )
        require(
            top_width < TOL,
            "The exported ramp has a horizontal upper shelf or lip",
        )
        top_edge_widths.append(top_width)
        line_checks.append({
            "y_mm": float(profile_y),
            "low_endpoint_x_mm": float(ordered[0, 0]),
            "low_endpoint_z_mm": float(ordered[0, 1]),
            "high_endpoint_x_mm": float(ordered[-1, 0]),
            "high_endpoint_z_mm": float(ordered[-1, 1]),
            "sampled_profile_points": len(ordered),
            "rises_with_increasing_model_x": True,
        })

    ramp_material_probe_size = [0.02, 0.02, 0.02]
    ramp_below_probe_volumes = []
    ramp_above_probe_volumes = []
    x_fractions = np.linspace(0.05, 0.95, 11)
    probe_y_levels = np.linspace(y_min + 0.02, y_max - 0.02, 3)
    for fraction in x_fractions:
        x = ramp_low_x + fraction * ramp_run_x
        z = z_min + fraction * z_depth
        for probe_y in probe_y_levels:
            ramp_below_probe_volumes.append(
                probe_intersection(mesh, probe_at(
                    [x, probe_y], z - 0.04, ramp_material_probe_size
                ))
            )
            ramp_above_probe_volumes.append(
                probe_intersection(mesh, probe_at(
                    [x, probe_y], z + 0.04, ramp_material_probe_size
                ))
            )
    expected_material_volume = float(np.prod(ramp_material_probe_size))
    require(
        all(abs(volume - expected_material_volume) < 1e-5
            for volume in ramp_below_probe_volumes),
        "The exported ramp is missing material below its sloped face",
    )
    require(
        all(volume < 1e-8 for volume in ramp_above_probe_volumes),
        "The exported ramp contains an unexpected shoulder above its face",
    )

    reference_web = expected["reference_web_4_to5_mm"]
    require(
        abs(expected["target_ramp_run_mm"] - TRANSITION_RAMP_RUN_MM) < TOL,
        "The ramp run does not match the user-approved wider cube aperture",
    )
    require(
        abs(ramp_run_x - expected["target_ramp_run_mm"]) < TOL,
        "The exported ramp does not preserve its selected run",
    )
    require(
        abs((y_max - y_min) - expected["ramp_span_y_mm"]) < TOL,
        "The exported ramp does not span the complete window divider",
    )
    require(
        abs((y_max - y_min) - (
            expected["overlap_y_bounds_mm"][1]
            - expected["overlap_y_bounds_mm"][0]
        )) < TOL,
        "The exported ramp does not cover the full shared divider length",
    )
    require(
        abs(ramp_high_x - expected["window6_left_edge_x_mm"]) < TOL,
        "The ramp intrusion would reduce window 6's specified width",
    )

    ramp_angle = float(np.arctan2(z_depth, ramp_run_x))
    cosine, sine = float(np.cos(ramp_angle)), float(np.sin(ramp_angle))
    rotation = np.asarray([
        [cosine, 0, -sine, 0],
        [0, 1, 0, 0],
        [sine, 0, cosine, 0],
        [0, 0, 0, 1],
    ])
    tangent = np.asarray([cosine, 0.0, sine])
    normal = np.asarray([-sine, 0.0, cosine])
    ramp_midpoint = np.asarray([
        (ramp_low_x + ramp_high_x) / 2,
        y_center,
        (z_min + z_max) / 2,
    ])
    cube_path_length = ramp_run_x / cosine + CUBE_EDGE
    swept_cube_length = cube_path_length + CUBE_EDGE
    cube_y_centers = (
        y_min + CUBE_EDGE / 2 + 0.05,
        y_center,
        y_max - CUBE_EDGE / 2 - 0.05,
    )
    normal_clearances = (0.02, 0.05, 0.1)
    sweep_results = []
    for clearance in normal_clearances:
        intersections = []
        for cube_y in cube_y_centers:
            swept_cube = trimesh.creation.box(extents=[
                swept_cube_length, CUBE_EDGE, CUBE_EDGE
            ])
            swept_cube.apply_transform(rotation)
            swept_cube.apply_translation(
                ramp_midpoint
                + normal * (CUBE_EDGE / 2 + clearance)
                + [0.0, cube_y - y_center, 0.0]
            )
            intersections.append(
                0.0 if swept_cube.is_empty else
                probe_intersection(mesh, swept_cube)
            )
        sweep_results.append({
            "normal_clearance_mm": clearance,
            "sample_count": len(intersections),
            "maximum_intersection_mm3": max(intersections),
            "collision_free": max(intersections) < 1e-5,
        })
    max_transfer_intersection = max(
        item["maximum_intersection_mm3"] for item in sweep_results
    )
    return {
        "ramp_material_probe_volume_mm3": expected_material_volume,
        "ramp_profile_checks": line_checks,
        "ramp_top_edge_widths_mm": top_edge_widths,
        "ramp_material_probe_x_fractions": x_fractions.tolist(),
        "ramp_material_probe_below_intersection_mm3": ramp_below_probe_volumes,
        "ramp_material_probe_above_intersection_mm3": ramp_above_probe_volumes,
        "solid_material_confirmed_along_slope": True,
        "empty_space_confirmed_above_slope": True,
        "solid_material_probe_y_levels_mm": probe_y_levels.tolist(),
        "cube_probe_edge_mm": CUBE_EDGE,
        "ramp_length_y_mm": y_max - y_min,
        "ramp_cross_slope_width_mm": ramp_run_x,
        "cube_transfer_path": (
            "Continuous swept volume of an 8.5 mm cube aligned to the ramp, "
            "from fully before its low endpoint to fully beyond its high endpoint"
        ),
        "cube_sweep_is_continuous": True,
        "cube_swept_volume_length_mm": swept_cube_length,
        "cube_sweep_y_positions": list(cube_y_centers),
        "cube_sweep_normal_clearances": sweep_results,
        "continuous_cube_sweep_max_intersection_mm3": max_transfer_intersection,
        "cube_sweep_clearance_passed": all(
            item["collision_free"] for item in sweep_results
        ),
        "physical_cube_transfer_tested": False,
        "ramp_run_mm": expected["target_ramp_run_mm"],
        "ramp_lane_width_mm": y_max - y_min,
        "low_edge_x_mm": ramp_low_x,
        "high_edge_x_mm": ramp_high_x,
        "slope_run_x_mm": ramp_run_x,
        "ramp_depth_z_mm": z_depth,
        "rear_face_z_mm": z_min,
        "front_face_z_mm": z_max,
        "reference_web_4_to5_mm": reference_web,
        "window5_remaining_width_at_rear_face_mm": (
            expected["window5_opening_after_ramp_mm"]
        ),
        "window6_width_preserved_mm": (
            expected["window6_opening_width_preserved_mm"]
        ),
        "ramp_direction_matches_printed_left_to_right": (
            expected["slope_rises_with_increasing_model_x"]
        ),
        "ramp_meets_window6_front_face_at_single_point": (
            max(top_edge_widths) < TOL
        ),
        "geometry_passed": True,
    }


def source_window_fill_specs(mesh):
    source = resource_window_loops(mesh, 0.2)
    levels = (-1.4, -1.0, -0.5, 0.0, 0.2, 0.5, 1.0, 1.3)
    records = []
    for source_center, source_size in source:
        extents = source_size.copy()
        for z in levels:
            for center, size in section_loops(mesh, z):
                if (
                    35.0 < size[0] < 100.0
                    and 20.0 < size[1] < 60.0
                    and np.linalg.norm(center - source_center) < 5.0
                ):
                    extents = np.maximum(extents, size)
        records.append({
            "center_mm": source_center.tolist(),
            "fill_size_mm": (extents + 0.2).tolist(),
        })
    return records


def target_window_specs():
    return [
        {
            "name": f"{row}-{column}",
            **target,
        }
        for row, start in (("upper", 0), ("lower", 3))
        for column, target in zip(
            ("left", "middle", "right"), TARGET_WINDOWS[start:start + 3]
        )
    ]


def rectangle_clearance(center_a, size_a, center_b, size_b):
    gaps = np.abs(np.asarray(center_a) - np.asarray(center_b)) - (
        np.asarray(size_a) + np.asarray(size_b)
    ) / 2
    if np.all(gaps < 0):
        return -float(np.min(-gaps))
    return float(np.max(gaps))


def slider_cube_clearance(row_plans, center, size):
    slot_center = np.asarray(center)
    slot_size = np.asarray(size)
    minimum = float("inf")
    nearest = None
    for plan in row_plans:
        cell_x = plan["target_cell_centers_x_mm"]
        for index, x in enumerate(cell_x):
            opening_size = (
                [17.8, OPENING_WIDTH]
                if plan["end_slot_cell"] and index == len(cell_x) - 1
                else [OPENING_WIDTH, OPENING_WIDTH]
            )
            clearance = rectangle_clearance(
                [x, plan["target_y_mm"]],
                opening_size,
                slot_center,
                slot_size,
            )
            if clearance < minimum:
                minimum = clearance
                nearest = {
                    "track": plan["track"],
                    "field_labels": plan["field_labels"],
                    "cube_center_mm": [float(x), plan["target_y_mm"]],
                }
    require(minimum >= MIN_SLOT_CLEARANCE - TOL,
            f"Slider intersects a cube opening or leaves only {minimum:.3f} mm")
    return {"minimum_clearance_mm": minimum, "nearest_opening": nearest}


def verify_layout_clearances(row_plans, windows, slider_center, slider_size):
    minimum_window_web = float("inf")
    window_pair = None
    for index, first in enumerate(windows):
        for second in windows[index + 1:]:
            clearance = rectangle_clearance(
                first["center_mm"], first["size_mm"],
                second["center_mm"], second["size_mm"],
            )
            if clearance < minimum_window_web:
                minimum_window_web = clearance
                window_pair = [first["name"], second["name"]]
    require(minimum_window_web >= 0.8 - TOL,
            f"Resource windows leave only {minimum_window_web:.3f} mm web")

    minimum_window_cube = float("inf")
    nearest_window_cube = None
    for window in windows:
        for plan in row_plans:
            cell_x = plan["target_cell_centers_x_mm"]
            for index, x in enumerate(cell_x):
                cell_size = (
                    [17.8, OPENING_WIDTH]
                    if plan["end_slot_cell"] and index == len(cell_x) - 1
                    else [OPENING_WIDTH, OPENING_WIDTH]
                )
                clearance = rectangle_clearance(
                    window["center_mm"], window["size_mm"],
                    [x, plan["target_y_mm"]], cell_size,
                )
                if clearance < minimum_window_cube:
                    minimum_window_cube = clearance
                    nearest_window_cube = {
                        "window": window["name"],
                        "track": plan["track"],
                        "field_labels": plan["field_labels"],
                    }
    require(minimum_window_cube >= 0.8 - TOL,
            f"Resource window approaches a cube opening by "
            f"{minimum_window_cube:.3f} mm")

    slider = {
        "center_mm": list(map(float, slider_center)),
        "size_mm": list(map(float, slider_size)),
    }
    slider_window_clearance = min(
        rectangle_clearance(
            slider["center_mm"], slider["size_mm"],
            window["center_mm"], window["size_mm"],
        )
        for window in windows
    )
    require(slider_window_clearance >= 0.8 - TOL,
            "Slider area approaches a resource window")
    return {
        "minimum_window_to_window_web_mm": minimum_window_web,
        "closest_window_pair": window_pair,
        "minimum_window_to_cube_clearance_mm": minimum_window_cube,
        "nearest_window_cube_pair": nearest_window_cube,
        "minimum_slider_to_cube_clearance_mm": slider_cube_clearance(
            row_plans, slider["center_mm"], slider["size_mm"]
        )["minimum_clearance_mm"],
        "minimum_slider_to_window_clearance_mm": slider_window_clearance,
    }


def track_groups(holes):
    parents = list(range(len(holes)))

    def find(index):
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i, center in enumerate(holes):
        for j in range(i):
            if np.max(np.abs(center - holes[j])) < 10.0:
                parents[find(i)] = find(j)
    groups = {}
    for index, center in enumerate(holes):
        groups.setdefault(find(index), []).append(center)
    tracks = [np.asarray(group) for group in groups.values()]
    lower = [track for track in tracks if track[:, 1].max() < 0]
    upper = [track for track in tracks if track[:, 1].min() >= 0]
    require(len(lower) == 3 and len(upper) == 3,
            f"Expected three lower and three upper tracks, got {len(lower)} and {len(upper)}")
    lower.sort(key=lambda track: float(track[:, 0].mean()))
    upper.sort(key=lambda track: float(track[:, 0].mean()))
    ordered = lower + upper
    require(tuple(map(len, ordered)) == EXPECTED_TRACK_COUNTS,
            f"Unexpected cube-track counts: {tuple(map(len, ordered))}")
    return ordered


def track_deltas(tracks, slot_centers, slot_sizes):
    row_plans = []
    anchors = []
    row_counts = (6, 6, 6, 5, 6, 6)
    slot_by_track_row = {}
    for center, size in zip(slot_centers, slot_sizes):
        track_distances = [
            float(np.min(np.linalg.norm(track - center, axis=1)))
            for track in tracks
        ]
        track_index = int(np.argmin(track_distances))
        require(track_distances[track_index] < 15,
                f"Unassigned cube end slot at {center.tolist()}")
        source_row_y = float(
            tracks[track_index][
                np.argmin(np.abs(tracks[track_index][:, 1] - center[1])), 1
            ]
        )
        slot_by_track_row[(track_index, round(source_row_y, 6))] = (
            center, size
        )

    for track_index, (track, datum, expected_count) in enumerate(
        zip(tracks, ROW_ANCHORS, row_counts)
    ):
        row = track[np.abs(track[:, 1] - datum["row_y"]) < 0.02]
        require(len(row) == expected_count,
                f"Unexpected anchor row count for {datum['name']}: {len(row)}")
        anchor_x = float(row[:, 0].min())
        photo_mark_shift_x = (
            LOWER_RIGHT_TRACK_SHIFT_X_MM if track_index == 2 else 0.0
        )
        target_x = (
            PAPER_LEFT + datum["offset_x"] + CUBE_EDGE / 2
            + photo_mark_shift_x
        )
        side_mean = float(track[:, 0].mean())
        if datum["side"] == "left":
            require(side_mean < -35, f"Wrong track for {datum['name']}")
        elif datum["side"] == "middle":
            require(-35 <= side_mean < 40, f"Wrong track for {datum['name']}")
        else:
            require(side_mean >= 40, f"Wrong track for {datum['name']}")
        target_y = PAPER_TOP - datum["top_distance"] - CUBE_EDGE / 2
        rows = []
        for row_index, source_y in enumerate(
            sorted(np.unique(np.round(track[:, 1], 6)), reverse=True)
        ):
            squares = track[np.abs(track[:, 1] - source_y) < 0.02]
            squares = squares[np.argsort(squares[:, 0])]
            first_x = float(squares[0, 0])
            index_offset = int(round((first_x - anchor_x) / OPENING_PITCH))
            block_shift_x = NUMBER_BLOCK_SHIFTS_X_MM.get(
                datum["name"], 0.0
            )
            target_first_x = (
                target_x + index_offset * CUBE_EDGE + block_shift_x
            )
            print_field_center_y = target_y - row_index * CUBE_EDGE
            opening_row_center_y = float(np.mean([
                target_y - step * CUBE_EDGE + step * OPENING_PITCH
                for step in range(len(TRACK_ROW_LABELS[track_index]))
            ])) - row_index * OPENING_PITCH
            source_cells_x = squares[:, 0].tolist()
            slot = slot_by_track_row.get((track_index, round(float(source_y), 6)))
            slot_cell_center_x = None
            if slot is not None:
                slot_center, slot_size = slot
                slot_cell_center_x = float(
                    slot_center[0] - slot_size[0] / 2 + OPENING_WIDTH / 2
                )
                source_cells_x.append(slot_cell_center_x)
            source_cells_x = np.asarray(source_cells_x)
            target_cells_x = (
                target_first_x
                + np.arange(len(source_cells_x), dtype=float) * CUBE_EDGE
            )
            dx = float(np.mean(target_cells_x - source_cells_x))
            moved_cell_x = source_cells_x + dx
            errors = moved_cell_x - target_cells_x
            row_plan = {
                "track_index": track_index,
                "track": datum["name"],
                "field_labels": list(TRACK_ROW_LABELS[track_index][row_index]),
                "source_y_mm": float(source_y),
                "print_field_center_y_mm": print_field_center_y,
                "target_y_mm": opening_row_center_y,
                "vertical_center_error_mm": (
                    opening_row_center_y - print_field_center_y
                ),
                "row_index_from_anchor": row_index,
                "source_first_cell_center_x_mm": first_x,
                "target_first_cell_center_x_mm": target_first_x,
                "source_cell_centers_x_mm": source_cells_x.tolist(),
                "target_cell_centers_x_mm": target_cells_x.tolist(),
                "target_square_centers_x_mm": target_cells_x[:len(squares)].tolist(),
                "opening_count": len(squares),
                "end_slot_cell": slot is not None,
                "end_slot_cell_center_x_mm": slot_cell_center_x,
                "dx_mm": dx,
                "dy_mm": opening_row_center_y - float(source_y),
                "cell_center_errors_mm": errors.tolist(),
                "max_abs_center_error_mm": float(np.max(np.abs(errors))),
                "min_web_mm": OPENING_PITCH - OPENING_WIDTH,
            }
            rows.append(row_plan)
            row_plans.append(row_plan)
        anchors.append({
            "track": datum["name"],
            "photo_mark_shift_x_mm": photo_mark_shift_x,
            "whole_block_shift_x_mm": NUMBER_BLOCK_SHIFTS_X_MM.get(
                datum["name"], 0.0
            ),
            "source_anchor_row_y_mm": datum["row_y"],
            "left_edge_offset_from_board_mm": datum["offset_x"],
            "top_edge_offset_from_board_mm": datum["top_distance"],
            "current_first_opening_center_x_mm": anchor_x,
            "target_first_printed_cell_center_x_mm": (
                target_x + NUMBER_BLOCK_SHIFTS_X_MM.get(
                    datum["name"], 0.0
                )
            ),
            "current_top_row_center_y_mm": float(track[:, 1].max()),
            "target_top_print_field_center_y_mm": target_y,
            "target_top_opening_center_y_mm": rows[0]["target_y_mm"],
            "opening_count": len(track),
            "anchored_row_opening_count": len(row),
            "row_layouts": rows,
        })
    return row_plans, anchors


def row_plan_for_center(row_plans, track_index, center_y):
    plans = [
        plan for plan in row_plans
        if plan["track_index"] == track_index
    ]
    require(plans, f"Missing row plan for cube track {track_index}")
    return min(plans, key=lambda plan: abs(plan["source_y_mm"] - center_y))


def relocate_cube_openings(mesh, tracks, row_plans):
    old_thickness = float(mesh.extents[2])
    fill_boxes = []
    cut_boxes = []
    moved = []
    source_windows = source_window_fill_specs(mesh)
    target_windows = target_window_specs()
    for window in source_windows:
        fill = trimesh.creation.box(
            extents=[
                *window["fill_size_mm"],
                old_thickness + 0.02,
            ]
        )
        fill.apply_translation([*window["center_mm"], 0])
        fill_boxes.append(fill)
    for window in target_windows:
        cutter = trimesh.creation.box(
            extents=[*window["size_mm"], old_thickness + 0.04]
        )
        cutter.apply_translation([*window["center_mm"], 0])
        cut_boxes.append(cutter)

    for track_index, track in enumerate(tracks):
        for center in track:
            plan = row_plan_for_center(
                row_plans, track_index, float(center[1])
            )
            fill = trimesh.creation.box(
                extents=[OPENING_WIDTH + 0.02, OPENING_WIDTH + 0.02,
                         old_thickness + 0.02]
            )
            fill.apply_translation([center[0], center[1], 0])
            fill_boxes.append(fill)
            cutter = trimesh.creation.box(
                extents=[OPENING_WIDTH, OPENING_WIDTH, old_thickness + 0.04]
            )
            new_center = center + np.asarray([plan["dx_mm"], plan["dy_mm"]])
            cutter.apply_translation([new_center[0], new_center[1], 0])
            cut_boxes.append(cutter)
            moved.append(new_center)
    slot_centers, slot_sizes = double_width_slots(mesh, 0.2)
    source_arrow_profiles = end_slot_back_profiles(mesh, slot_centers)
    moved_slots = []
    target_arrow_profiles = []
    for slot_index, (center, size) in enumerate(
        zip(slot_centers, slot_sizes)
    ):
        track_distances = [
            float(np.min(np.linalg.norm(track - center, axis=1)))
            for track in tracks
        ]
        track_index = int(np.argmin(track_distances))
        plan = row_plan_for_center(
            row_plans, track_index, float(center[1])
        )
        ordered = sorted(track_distances)
        require(ordered[0] < 15 and ordered[1] > ordered[0] + 1,
                f"Ambiguous cube-slot track at {center.tolist()}")
        fill = trimesh.creation.box(
            extents=[size[0] + 0.02, size[1] + 0.02, old_thickness + 0.02]
        )
        fill.apply_translation([center[0], center[1], 0])
        fill_boxes.append(fill)
        new_center = center + np.asarray([plan["dx_mm"], plan["dy_mm"]])
        cutter = trimesh.creation.box(
            extents=[size[0], size[1], old_thickness + 0.04]
        )
        cutter.apply_translation([new_center[0], new_center[1], 0])
        cut_boxes.append(cutter)
        moved_slots.append({
            "center_mm": new_center.tolist(),
            "size_mm": size.tolist(),
            "track": ROW_ANCHORS[track_index]["name"],
            "source_row_y_mm": float(center[1]),
        })
        target_arrow_profiles.append({
            "center_mm": new_center.tolist(),
            **source_arrow_profiles[slot_index],
        })
    source_adjacent_center, source_adjacent_size = adjacent_cutout(mesh, 0.2)
    target_left_x = (
        source_adjacent_center[0] - source_adjacent_size[0] / 2
        + ADJACENT_CUTOUT_SHIFT_X + SMALL_WINDOW_TRANSLATION_X_MM
        + SMALL_WINDOW_LEFT_TRIM_MM
    )
    target_right_x = (
        source_adjacent_center[0] + source_adjacent_size[0] / 2
        + ADJACENT_CUTOUT_SHIFT_X + SMALL_WINDOW_TRANSLATION_X_MM
    )
    target_adjacent_size = np.asarray([
        target_right_x - target_left_x,
        source_adjacent_size[1]
        - SMALL_WINDOW_TOP_TRIM_MM - SMALL_WINDOW_BOTTOM_TRIM_MM,
    ])
    target_adjacent_center = np.asarray([
        (target_left_x + target_right_x) / 2,
        source_adjacent_center[1]
        + (SMALL_WINDOW_TOP_TRIM_MM - SMALL_WINDOW_BOTTOM_TRIM_MM) / 2,
    ])
    adjacent_fill = trimesh.creation.box(
        extents=[source_adjacent_size[0] + 0.02,
                 source_adjacent_size[1] + 0.02, old_thickness + 0.02]
    )
    adjacent_fill.apply_translation([
        source_adjacent_center[0], source_adjacent_center[1], 0
    ])
    fill_boxes.append(adjacent_fill)
    adjacent_cutter = trimesh.creation.box(
        extents=[*target_adjacent_size,
                 old_thickness + 0.04]
    )
    adjacent_cutter.apply_translation([
        target_adjacent_center[0], target_adjacent_center[1], 0
    ])
    cut_boxes.append(adjacent_cutter)
    adjacent_cutout_revision = {
        "source_center_mm": source_adjacent_center.tolist(),
        "target_center_mm": target_adjacent_center.tolist(),
        "target_bounds_mm": [
            [target_left_x, target_adjacent_center[1]
             - target_adjacent_size[1] / 2],
            [target_right_x, target_adjacent_center[1]
             + target_adjacent_size[1] / 2],
        ],
        "translation_from_source_mm": [
            ADJACENT_CUTOUT_SHIFT_X + SMALL_WINDOW_TRANSLATION_X_MM,
            0.0,
        ],
        "translation_after_prior_alignment_mm": [
            SMALL_WINDOW_TRANSLATION_X_MM, 0.0
        ],
        "left_trim_mm": SMALL_WINDOW_LEFT_TRIM_MM,
        "top_trim_mm": SMALL_WINDOW_TOP_TRIM_MM,
        "bottom_trim_mm": SMALL_WINDOW_BOTTOM_TRIM_MM,
        "source_size_mm": source_adjacent_size.tolist(),
        "size_mm": target_adjacent_size.tolist(),
        "solid_inner_area_preserved": True,
    }
    source_slot_center, source_slot_size = long_horizontal_slot(
        mesh, 0.2, 8.64
    )
    target_slot_center = FOLLOWUP_SLIDER_CENTER_MM.copy()
    slider_clearance = slider_cube_clearance(
        row_plans, target_slot_center,
        [source_slot_size[0], LONG_SLOT_HEIGHT],
    )
    require(
        np.all(FOLLOWUP_SLIDER_SIZE_MM
               >= np.asarray([source_slot_size[0], LONG_SLOT_HEIGHT])),
        "The measured slider target is smaller than the preserved slot",
    )
    fill = trimesh.creation.box(
        extents=[source_slot_size[0] + 2.0,
                 source_slot_size[1] + 2.0, old_thickness + 0.02]
    )
    fill.apply_translation([source_slot_center[0], source_slot_center[1], 0])
    fill_boxes.append(fill)
    cutter = trimesh.creation.box(
        extents=[source_slot_size[0], LONG_SLOT_HEIGHT, old_thickness + 0.04]
    )
    cutter.apply_translation([target_slot_center[0], target_slot_center[1], 0])
    cut_boxes.append(cutter)
    long_slot_revision = {
        "source_center_mm": source_slot_center.tolist(),
        "source_size_mm": source_slot_size.tolist(),
        "previous_center_mm": FOLLOWUP_SLIDER_MARK_CENTER_MM.tolist(),
        "previous_size_mm": [
            float(source_slot_size[0]), PREVIOUS_LONG_SLOT_HEIGHT
        ],
        "target_center_mm": target_slot_center.tolist(),
        "target_size_mm": [float(source_slot_size[0]), LONG_SLOT_HEIGHT],
        "extension_down_mm": SLIDER_EXTENSION_DOWN_MM,
        "top_edge_preserved": True,
        "target_area_center_mm": FOLLOWUP_SLIDER_CENTER_MM.tolist(),
        "target_area_size_mm": FOLLOWUP_SLIDER_SIZE_MM.tolist(),
        "minimum_cube_clearance_mm": slider_clearance["minimum_clearance_mm"],
        "nearest_cube_opening": slider_clearance["nearest_opening"],
    }
    fill_mesh = trimesh.boolean.union(fill_boxes, engine="manifold")
    cutter_mesh = trimesh.boolean.union(cut_boxes, engine="manifold")
    patched = trimesh.boolean.union([mesh, fill_mesh], engine="manifold")
    bounded = trimesh.creation.box(
        extents=[250.0, 190.0, old_thickness]
    )
    bounded.apply_translation([0, 0, float(mesh.bounds[:, 2].mean())])
    patched = trimesh.boolean.intersection([patched, bounded], engine="manifold")
    relocated = trimesh.boolean.difference(
        [patched, cutter_mesh], engine="manifold"
    )
    relocated = trimesh.boolean.intersection(
        [relocated, bounded], engine="manifold"
    )
    check_mesh(relocated)
    result_holes = square_holes(relocated, 0.0)
    require(len(result_holes) == 65, "Cube opening count changed")
    for track_index, track in enumerate(tracks):
        for center in track:
            plan = row_plan_for_center(
                row_plans, track_index, float(center[1])
            )
            new_center = center + np.asarray([plan["dx_mm"], plan["dy_mm"]])
            require(np.min(np.linalg.norm(result_holes - new_center, axis=1)) < TOL,
                    f"Relocated cube opening missing at {new_center.tolist()}")
    result_slots, result_sizes = double_width_slots(relocated, 0.0)
    require(len(result_slots) == len(moved_slots), "Cube end-slot count changed")
    for expected in moved_slots:
        distances = np.linalg.norm(
            result_slots - np.asarray(expected["center_mm"]), axis=1
        )
        index = int(np.argmin(distances))
        require(distances[index] < TOL, "Relocated cube end-slot missing")
        require(np.allclose(result_sizes[index], expected["size_mm"],
                            atol=TOL, rtol=0),
                "Cube end-slot dimensions changed")
    actual_center, actual_size = long_horizontal_slot(
        relocated, 0.0, LONG_SLOT_HEIGHT
    )
    require(np.allclose(actual_center, target_slot_center, atol=TOL, rtol=0),
            "Horizontal slot center changed")
    require(np.allclose(actual_size, long_slot_revision["target_size_mm"],
                        atol=TOL, rtol=0),
            "Horizontal slot dimensions changed")
    actual_adjacent_center, actual_adjacent_size = adjacent_cutout(
        relocated, 0.0
    )
    require(np.allclose(actual_adjacent_center, target_adjacent_center,
                        atol=TOL, rtol=0),
            "Adjacent cutout position changed")
    require(np.allclose(actual_adjacent_size, target_adjacent_size,
                        atol=TOL, rtol=0),
            "Adjacent cutout dimensions changed")
    actual_windows = resource_window_loops(relocated, 0.0)
    for actual, expected in zip(actual_windows, target_windows):
        require(
            np.allclose(actual[0], expected["center_mm"], atol=TOL, rtol=0)
            and np.allclose(actual[1], expected["size_mm"], atol=TOL, rtol=0),
            f"Resource window changed: expected {expected['name']} "
            f"{expected['center_mm']}/{expected['size_mm']}, got "
            f"{actual[0].tolist()}/{actual[1].tolist()}",
        )
    return (
        relocated, np.asarray(moved), moved_slots, target_arrow_profiles,
        long_slot_revision, adjacent_cutout_revision, target_windows,
    )


def add_local_support_features(mesh, moved_slots, arrow_profiles,
                               small_window):
    require(len(moved_slots) == 6 and len(arrow_profiles) == 6,
            "Expected six end-slot arrow profiles")
    bottom, top = map(float, mesh.bounds[:, 2])
    thickness = top - bottom
    floor_boxes = []
    cutters = []
    cube_proxies = []
    slot_results = []
    epsilon = LOCAL_RELIEF_EPS_MM

    for slot, arrow in zip(moved_slots, arrow_profiles):
        center = np.asarray(slot["center_mm"], dtype=float)
        size = np.asarray(slot["size_mm"], dtype=float)
        profile_center = center + np.asarray(
            arrow["center_offset_mm"], dtype=float
        )
        profile_size = np.asarray(arrow["size_mm"], dtype=float)
        shelf = trimesh.creation.box(
            extents=[size[0], size[1], END_ARROW_LEDGE_THICKNESS_MM]
        )
        shelf.apply_translation([
            center[0], center[1],
            bottom + END_ARROW_LEDGE_THICKNESS_MM / 2,
        ])
        check_mesh(shelf)
        floor_boxes.append(shelf)

        cube_center = np.asarray([
            center[0] - size[0] / 2 + OPENING_WIDTH / 2,
            center[1],
        ])
        cube_opening_size = np.asarray([
            OPENING_WIDTH, min(OPENING_WIDTH, float(size[1]))
        ])
        cube_hole = trimesh.creation.box(
            extents=[
                *cube_opening_size, thickness + 2 * epsilon
            ]
        )
        cube_hole.apply_translation([
            cube_center[0], cube_center[1], (bottom + top) / 2
        ])
        cutters.append(cube_hole)
        cube_proxy = trimesh.creation.box(
            extents=[CUBE_EDGE, CUBE_EDGE, thickness]
        )
        cube_proxy.apply_translation([
            cube_center[0], cube_center[1], (bottom + top) / 2
        ])
        cube_proxies.append((cube_center, cube_proxy))

        points = np.asarray(arrow["points_local_mm"], dtype=float) + center
        signed_area = 0.5 * np.sum(
            points[:, 0] * np.roll(points[:, 1], -1)
            - points[:, 1] * np.roll(points[:, 0], -1)
        )
        if signed_area < 0:
            points = points[::-1]
        profile = Polygon(
            *(tuple(point) for point in points),
            align=None,
        )
        arrow_shape = extrude(
            profile,
            amount=END_ARROW_LEDGE_THICKNESS_MM + 2 * epsilon,
        ).translate((0, 0, bottom - epsilon))
        arrow_vertices, arrow_faces = arrow_shape.tessellate(0.01)
        arrow_cutter = trimesh.Trimesh(
            vertices=[tuple(vertex) for vertex in arrow_vertices],
            faces=arrow_faces,
            process=True,
        )
        check_mesh(arrow_cutter)
        cutters.append(arrow_cutter)
        slot_results.append({
            "center_mm": center.tolist(),
            "slot_size_mm": size.tolist(),
            "source_arrow_opening_size_mm": profile_size.tolist(),
            "source_arrow_center_mm": profile_center.tolist(),
            "opening_width_at_rear_mm": float(profile_size[0]),
            "shelf_width_after_arrow_tip_mm": float(
                size[0] - profile_size[0]
            ),
        })

    shelf_mesh = trimesh.boolean.union(floor_boxes, engine="manifold")
    patched = trimesh.boolean.union(
        [mesh, shelf_mesh], engine="manifold"
    )
    check_mesh(patched)
    cutter_mesh = trimesh.boolean.union(cutters, engine="manifold")
    require(cutter_mesh.is_watertight and cutter_mesh.volume > 0,
            "Local relief cutters are not a valid watertight set")
    result = trimesh.boolean.difference(
        [patched, cutter_mesh], engine="manifold"
    )
    check_mesh(result)

    window_center = np.asarray(
        small_window["target_center_mm"], dtype=float
    )
    window_size = np.asarray(small_window["size_mm"], dtype=float)
    window_right = window_center[0] + window_size[0] / 2
    window_top = window_center[1] + window_size[1] / 2
    window_bottom = window_center[1] - window_size[1] / 2
    holes = square_holes(
        result, bottom + END_ARROW_LEDGE_THICKNESS_MM + 0.05
    )
    candidates = [
        center for center in holes
        if center[0] - OPENING_WIDTH / 2 > window_right
        and abs(center[1] - window_center[1]) < OPENING_WIDTH / 2
    ]
    require(candidates,
            "Could not identify the zero-cube field beside the small window")
    zero_center = min(candidates, key=lambda center: center[0])
    web_right = float(zero_center[0] - OPENING_WIDTH / 2)
    web_left = float(window_right)
    web_low = max(window_bottom, float(zero_center[1] - OPENING_WIDTH / 2))
    web_high = min(window_top, float(zero_center[1] + OPENING_WIDTH / 2))
    web_width = web_right - web_left
    web_height = web_high - web_low
    require(web_width > 1.0 and abs(web_height - OPENING_WIDTH) < TOL,
            f"Small-window web bounds invalid: {web_width:.4f} x "
            f"{web_height:.4f} mm")
    recess_bottom = bottom + SMALL_WEB_THICKNESS_MM
    web_cutter = trimesh.creation.box(
        extents=[
            web_width + 2 * epsilon,
            web_height + 2 * epsilon,
            top + epsilon - recess_bottom,
        ]
    )
    web_cutter.apply_translation([
        (web_left + web_right) / 2,
        (web_low + web_high) / 2,
        (recess_bottom + top + epsilon) / 2,
    ])
    result = trimesh.boolean.difference(
        [result, web_cutter], engine="manifold"
    )
    check_mesh(result)

    web_probe_center = [(web_left + web_right) / 2,
                        (web_low + web_high) / 2]
    web_probe_size = [0.4, 0.4, 0.1]
    web_rear_probe = probe_intersection(
        result,
        probe_at(web_probe_center, bottom + 0.5, web_probe_size),
    )
    web_front_probe = probe_intersection(
        result,
        probe_at(web_probe_center, bottom + 1.1, web_probe_size),
    )
    require(abs(web_rear_probe - 0.016) < 1e-6,
            "The small-window web is not solid through its 1 mm back layer")
    require(web_front_probe < 1e-7,
            "The small-window web was not recessed from the front")

    for slot_result, (cube_center, cube_proxy) in zip(
        slot_results, cube_proxies
    ):
        interference = probe_intersection(result, cube_proxy)
        require(interference < 1e-6,
                f"8.5 mm cube interferes in 10-cube field: {interference}")
        slot_center = np.asarray(slot_result["center_mm"])
        slot_size = np.asarray(slot_result["slot_size_mm"])
        support_x = float(slot_center[0] + slot_size[0] / 2 - 0.5)
        support_center = [support_x, float(slot_center[1])]
        support_samples = []
        for offset in (0.25, 0.75, 0.99):
            sample = probe_intersection(
                result,
                probe_at(support_center, bottom + offset, [0.1, 0.1, 0.01]),
            )
            require(abs(sample - 0.0001) < 1e-7,
                    "An arrow ledge does not span the full 1 mm back layer")
            support_samples.append({
                "z_from_back_face_mm": offset,
                "solid_probe_volume_mm3": sample,
            })
        beyond_floor = probe_intersection(
            result,
            probe_at(
                support_center, bottom + 1.01, [0.1, 0.1, 0.01]
            ),
        )
        require(beyond_floor < 1e-7,
                "Arrow ledge protrudes beyond its 1 mm back layer")
        overrun_center = [
            float(cube_center[0] + OPENING_WIDTH), float(slot_center[1])
        ]
        contact_probe = probe_at(
            overrun_center, bottom + 0.95,
            [CUBE_EDGE, CUBE_EDGE, 0.05],
        )
        contact_volume = probe_intersection(result, contact_probe)
        contact_area = contact_volume / 0.05
        require(contact_area > 0.0,
                "Overrun cube has no shelf contact on the arrow ledge")
        slot_result.update({
            "cube_center_mm": cube_center.tolist(),
            "cube_interference_volume_mm3": interference,
            "ledge_rear_face_flush": True,
            "ledge_thickness_mm": END_ARROW_LEDGE_THICKNESS_MM,
            "front_recess_depth_mm": thickness - END_ARROW_LEDGE_THICKNESS_MM,
            "ledge_thickness_probe_checks": support_samples,
            "probe_above_ledge_mm3": beyond_floor,
            "overrun_cube_contact_area_mm2": contact_area,
        })

    require(abs(result.bounds[0, 2] - bottom) < TOL
            and abs(result.bounds[1, 2] - top) < TOL,
            "Local supports changed the panel Z envelope")
    return result, {
        "end_slot_count": len(slot_results),
        "end_slots": slot_results,
        "small_window": {
            "center_mm": small_window["target_center_mm"],
            "size_mm": small_window["size_mm"],
            "bounds_mm": small_window["target_bounds_mm"],
        },
        "rear_face_z_mm": bottom,
        "panel_front_z_mm": top,
        "ledge_thickness_mm": END_ARROW_LEDGE_THICKNESS_MM,
        "front_recess_depth_mm": thickness - END_ARROW_LEDGE_THICKNESS_MM,
        "small_window_web": {
            "target_center_mm": web_probe_center,
            "bounds_mm": [
                [web_left, web_low], [web_right, web_high]
            ],
            "width_mm": web_width,
            "height_mm": web_height,
            "rear_layer_thickness_mm": SMALL_WEB_THICKNESS_MM,
            "front_recess_depth_mm": thickness - SMALL_WEB_THICKNESS_MM,
            "solid_back_probe_volume_mm3": web_rear_probe,
            "recessed_front_probe_volume_mm3": web_front_probe,
            "zero_field_center_mm": zero_center.tolist(),
        },
    }


def verify_local_relief_export(mesh, expected):
    bottom, top = map(float, mesh.bounds[:, 2])
    require(abs(bottom - expected["rear_face_z_mm"]) < TOL
            and abs(top - expected["panel_front_z_mm"]) < TOL,
            "Exported local relief changed the front panel Z envelope")
    actual_window_center, actual_window_size = adjacent_cutout(
        mesh, bottom + 0.05
    )
    target_window = expected["small_window"]
    require(
        np.allclose(
            actual_window_center, target_window["center_mm"],
            atol=TOL, rtol=0,
        )
        and np.allclose(
            actual_window_size, target_window["size_mm"],
            atol=TOL, rtol=0,
        ),
        "Exported small-window bounds differ from the requested revision",
    )

    slots = expected["end_slots"]
    require(len(slots) == 6, "Exported arrow ledge count changed")
    rear_profiles = section_loops(mesh, bottom + 0.05)
    front_slots, front_sizes = double_width_slots(
        mesh, bottom + END_ARROW_LEDGE_THICKNESS_MM + 0.05
    )
    require(len(front_slots) == 6,
            "Expected six full-width front-recessed end slots")
    checks = []
    for item in slots:
        slot_center = np.asarray(item["center_mm"], dtype=float)
        slot_size = np.asarray(item["slot_size_mm"], dtype=float)
        profile_center = np.asarray(
            item["source_arrow_center_mm"], dtype=float
        )
        profile_size = np.asarray(
            item["source_arrow_opening_size_mm"], dtype=float
        )
        profile_matches = [
            (center, size) for center, size in rear_profiles
            if 10.5 < size[0] < 12.0
            and 8.3 < size[1] < 8.9
            and np.linalg.norm(center - profile_center) < TOL
        ]
        require(len(profile_matches) == 1,
                f"Rear arrow opening missing at {profile_center.tolist()}")
        actual_profile_center, actual_profile_size = profile_matches[0]
        require(
            np.allclose(actual_profile_size, profile_size, atol=TOL, rtol=0),
            "Exported rear arrow opening dimensions changed",
        )
        front_match = int(np.argmin(np.linalg.norm(
            front_slots - slot_center, axis=1
        )))
        require(
            np.linalg.norm(front_slots[front_match] - slot_center) < TOL
            and np.allclose(
                front_sizes[front_match], slot_size, atol=TOL, rtol=0
            ),
            "Front end-slot dimensions changed above the arrow ledge",
        )

        cube_center = np.asarray(item["cube_center_mm"], dtype=float)
        cube_probe = probe_at(
            cube_center, (bottom + top) / 2,
            [CUBE_EDGE, CUBE_EDGE, top - bottom],
        )
        cube_interference = probe_intersection(mesh, cube_probe)
        require(cube_interference < 1e-6,
                f"Exported 8.5 mm cube clearance failed: {cube_interference}")
        support_center = [
            float(slot_center[0] + slot_size[0] / 2 - 0.5),
            float(slot_center[1]),
        ]
        samples = []
        for offset in (0.25, 0.75, 0.99):
            volume = probe_intersection(
                mesh,
                probe_at(support_center, bottom + offset,
                         [0.1, 0.1, 0.01]),
            )
            require(abs(volume - 0.0001) < 1e-7,
                    "Exported arrow ledge is not a continuous 1 mm floor")
            samples.append(volume)
        above_floor = probe_intersection(
            mesh,
            probe_at(support_center, bottom + 1.01, [0.1, 0.1, 0.01]),
        )
        require(above_floor < 1e-7,
                "Exported arrow ledge is not recessed from the front")
        overrun_center = [
            float(cube_center[0] + OPENING_WIDTH),
            float(slot_center[1]),
        ]
        contact_area = probe_intersection(
            mesh,
            probe_at(overrun_center, bottom + 0.95,
                     [CUBE_EDGE, CUBE_EDGE, 0.05]),
        ) / 0.05
        require(contact_area > 0.0,
                "Exported ledge has no overrun-cube contact area")
        checks.append({
            "center_mm": slot_center.tolist(),
            "front_slot_size_mm": front_sizes[front_match].tolist(),
            "rear_arrow_center_mm": actual_profile_center.tolist(),
            "rear_arrow_opening_size_mm": actual_profile_size.tolist(),
            "cube_center_mm": cube_center.tolist(),
            "cube_interference_volume_mm3": cube_interference,
            "back_layer_thickness_mm": END_ARROW_LEDGE_THICKNESS_MM,
            "front_recess_depth_mm": top - bottom
            - END_ARROW_LEDGE_THICKNESS_MM,
            "back_layer_sample_volumes_mm3": samples,
            "probe_above_floor_mm3": above_floor,
            "overrun_cube_contact_area_mm2": contact_area,
        })

    web = expected["small_window_web"]
    web_center = np.asarray(web["target_center_mm"], dtype=float)
    web_size = [0.4, 0.4, 0.1]
    solid_volume = probe_intersection(
        mesh, probe_at(web_center, bottom + 0.5, web_size)
    )
    recessed_volume = probe_intersection(
        mesh, probe_at(web_center, bottom + 1.1, web_size)
    )
    require(abs(solid_volume - 0.016) < 1e-6,
            "Exported small-window web is not solid through its back layer")
    require(recessed_volume < 1e-7,
            "Exported small-window web is not front-recessed")
    return {
        "small_window": {
            "center_mm": actual_window_center.tolist(),
            "size_mm": actual_window_size.tolist(),
            "bounds_mm": [
                (actual_window_center - actual_window_size / 2).tolist(),
                (actual_window_center + actual_window_size / 2).tolist(),
            ],
            "inner_area_solid": True,
        },
        "small_window_web": {
            **web,
            "solid_back_probe_volume_mm3": solid_volume,
            "recessed_front_probe_volume_mm3": recessed_volume,
        },
        "end_slot_count": len(checks),
        "end_slots": checks,
        "rear_face_flush_and_front_recess_passed": True,
        "cube_fit_and_overrun_support_passed": True,
    }


def move_mount_vertices(mesh, centers):
    vertices = mesh.vertices.copy()
    moved_centers = centers.copy()
    for index, center in enumerate(centers):
        if abs(center[0]) < 1:
            continue
        dx = -np.sign(center[0])
        radial = np.linalg.norm(vertices[:, :2] - center, axis=1)
        weight = np.ones(len(vertices))
        weight[radial >= 4.2] = 0
        transition = (radial > 2.2) & (radial < 4.2)
        weight[transition] = (4.2 - radial[transition]) / 2.0
        vertices[:, 0] += dx * weight
        moved_centers[index, 0] += dx
    result = trimesh.Trimesh(vertices=vertices, faces=mesh.faces, process=False)
    check_mesh(result)
    return result, moved_centers


def scale_front_z(mesh, centers):
    vertices = mesh.vertices.copy()
    bottom = float(mesh.bounds[0, 2])
    factor = FRONT_THICKNESS / float(mesh.extents[2])
    vertices[:, 2] = bottom + (vertices[:, 2] - bottom) * factor
    floor_after_scale = bottom + (OLD_SOCKET_FLOOR - bottom) * factor
    new_top = bottom + FRONT_THICKNESS
    target_floor = new_top - SOCKET_FLOOR
    floor_vertices = 0
    for center in centers:
        radial = np.linalg.norm(vertices[:, :2] - center, axis=1)
        mask = (
            (np.abs(vertices[:, 2] - floor_after_scale) < TOL)
            & (radial < 1.6)
        )
        require(mask.sum() >= 24, f"Socket floor missing at {center.tolist()}")
        vertices[mask, 2] = target_floor
        floor_vertices += int(mask.sum())
    result = trimesh.Trimesh(vertices=vertices, faces=mesh.faces, process=False)
    check_mesh(result)
    require(abs(result.extents[2] - FRONT_THICKNESS) < TOL,
            "Front thickness differs from target")
    return result, {
        "bottom_z_mm": bottom,
        "top_z_mm": float(result.bounds[1, 2]),
        "floor_z_mm": target_floor,
        "floor_vertices_adjusted": floor_vertices,
    }


def shorten_pins(mesh, centers):
    vertices = mesh.vertices.copy()
    target_tip = PIN_BASE + PIN_PROJECTION
    factor = (target_tip - PIN_SHOULDER) / (OLD_PIN_TIP - PIN_SHOULDER)
    for center in centers:
        radial = np.linalg.norm(vertices[:, :2] - center, axis=1)
        mask = (radial < 1.6) & (vertices[:, 2] > PIN_SHOULDER + TOL)
        require(mask.sum() >= 24, f"Pin taper missing at {center.tolist()}")
        vertices[mask, 2] = (
            PIN_SHOULDER
            + (vertices[mask, 2] - PIN_SHOULDER) * factor
        )
    result = trimesh.Trimesh(vertices=vertices, faces=mesh.faces, process=False)
    check_mesh(result)
    return result


def trim_long_edges(mesh):
    slab = trimesh.creation.box(
        extents=[NEW_LENGTH, 250.0, 20.0]
    )
    slab.apply_translation([0, 0, float(mesh.bounds[:, 2].mean())])
    result = trimesh.boolean.intersection([mesh, slab], engine="manifold")
    check_mesh(result)
    require(abs(result.extents[0] - NEW_LENGTH) < TOL,
            f"Long dimension is {result.extents[0]}, expected {NEW_LENGTH}")
    require(abs(result.extents[1] - SHORT_SIDE) < TOL,
            f"Short dimension changed: {result.extents[1]}")
    return result


def ring_diameters(mesh, center, z, section_offset=1e-6):
    section = mesh.section(
        plane_normal=[0, 0, 1],
        plane_origin=[0, 0, z + section_offset],
    )
    require(section is not None, "Missing mounting feature section")
    loops = [
        loop for loop in section.discrete
        if np.linalg.norm(
            (loop[:, :2].max(axis=0) + loop[:, :2].min(axis=0)) / 2 - center
        ) < TOL and np.ptp(loop[:, :2], axis=0).max() < 4.0
    ]
    require(len(loops) == 1,
            f"Ambiguous mount ring at {center.tolist()}, Z={z}")
    return np.ptp(loops[0][:, :2], axis=0)


def probe_intersection(mesh, probe):
    result = trimesh.boolean.intersection([mesh, probe], engine="manifold")
    return 0.0 if result.is_empty else abs(float(result.volume))


def probe_at(center, z, size):
    probe = trimesh.creation.box(extents=size)
    probe.apply_translation([center[0], center[1], z])
    return probe


def combined_probes(centers, z, size):
    probes = []
    for center in centers:
        probe = trimesh.creation.box(extents=size)
        probe.apply_translation([center[0], center[1], z])
        probes.append(probe)
    return trimesh.util.concatenate(probes)


def verify_cube_openings(
    mesh, holes, expected_long_slot, expected_adjacent_cutout
):
    bottom, top = map(float, mesh.bounds[:, 2])
    z_levels = (bottom + 0.1, (bottom + top) / 2, top - 0.1)
    inside_offsets = np.asarray([
        [0.0, 0.0], [-4.2, -4.2], [-4.2, 4.2],
        [4.2, -4.2], [4.2, 4.2],
    ])
    inside_centers = np.concatenate([
        holes + offset for offset in inside_offsets
    ])
    outside_offsets = np.asarray([
        [-4.34, 0.0], [4.34, 0.0],
        [0.0, -4.34], [0.0, 4.34],
    ])
    outside_centers = np.concatenate([
        holes + offset for offset in outside_offsets
    ])
    for z in z_levels:
        inside_volume = probe_intersection(
            mesh, combined_probes(inside_centers, z, [0.1, 0.1, 0.1])
        )
        require(inside_volume < 1e-7,
                f"Cube aperture obstructed at Z={z}")
    rear_web_z = bottom + SMALL_WEB_THICKNESS_MM / 2
    for z in (rear_web_z,):
        outside_volume = probe_intersection(
            mesh, combined_probes(outside_centers, z, [0.02, 0.02, 0.1])
        )
        expected_outside_volume = len(outside_centers) * 0.02 * 0.02 * 0.1
        require(abs(outside_volume - expected_outside_volume) < 1e-5,
                f"Cube aperture boundary changed at Z={z}")

    web_centers = []
    for index, center in enumerate(holes):
        distances = np.linalg.norm(holes - center, axis=1)
        for other_index in np.flatnonzero(
            (distances > 9.0) & (distances < 9.4)
        ):
            other = holes[other_index]
            midpoint = (center + other) / 2
            web_centers.append(midpoint)
    require(web_centers, "No cube separating webs were measured")
    expected_web_volume = len(web_centers) * 0.2 * 0.2 * 0.1
    web_volumes = []
    for z in z_levels:
        volume = probe_intersection(
            mesh,
            combined_probes(web_centers, z, [0.2, 0.2, 0.1]),
        )
        require(abs(volume - expected_web_volume) < 1e-5,
                f"Cube openings or adjacent cutout merge at Z={z}")
        web_volumes.append(volume)
    return {
        "openings": len(holes),
        "tested_z_levels_mm": list(z_levels),
        "cube_boundary_probe_z_mm": rear_web_z,
        "inset_probe_mm": 4.2,
        "edge_probe_offset_mm": 4.34,
        "separating_web_probe_count": len(web_centers),
        "separating_web_probe_volume_mm3": web_volumes,
    }


def verify_cube_grid(mesh, expected_slots, expected_rows, expected_long_slot,
                     expected_adjacent_cutout):
    expected_centers = np.asarray([
        [x + plan["dx_mm"], plan["target_y_mm"]]
        for plan in expected_rows
        for x in plan["source_cell_centers_x_mm"][:plan["opening_count"]]
    ])
    require(len(expected_centers) == 65,
            "Expected cube field registration no longer contains 65 fields")
    back_z = float(mesh.bounds[0, 2]) + LOCAL_RELIEF_EPS_MM + 0.03
    back_openings = [
        (center, size) for center, size in section_loops(mesh, back_z)
        if np.all((size > 8.5) & (size < 8.8))
    ]
    measured_sizes = []
    for center in expected_centers:
        matches = [
            size for actual, size in back_openings
            if np.linalg.norm(actual - center) < TOL
        ]
        require(len(matches) == 1,
                f"Back-layer cube aperture missing at {center.tolist()}")
        measured_sizes.append(matches[0])
    holes = expected_centers
    opening_sizes = np.asarray(measured_sizes)
    require(np.allclose(opening_sizes, OPENING_WIDTH, atol=TOL, rtol=0),
            "Cube aperture width changed")
    slot_centers, slot_sizes = double_width_slots(mesh, 0.2)
    require(len(slot_centers) == len(expected_slots),
            "Cube end-slot count changed")
    for expected in expected_slots:
        expected_center = np.asarray(expected["center_mm"])
        distances = np.linalg.norm(slot_centers - expected_center, axis=1)
        index = int(np.argmin(distances))
        require(distances[index] < TOL, "Cube end-slot anchor changed")
        require(np.allclose(slot_sizes[index], expected["size_mm"],
                            atol=TOL, rtol=0),
                "Cube end-slot dimensions changed")
    slot_center, slot_size = long_horizontal_slot(
        mesh, 0.0, LONG_SLOT_HEIGHT
    )
    require(np.allclose(slot_center, expected_long_slot["target_center_mm"],
                        atol=TOL, rtol=0),
            "Horizontal slot position changed")
    require(np.allclose(slot_size, expected_long_slot["target_size_mm"],
                        atol=TOL, rtol=0),
            "Horizontal slot size changed")
    slider_clearance = slider_cube_clearance(
        expected_rows, slot_center, slot_size
    )
    adjacent_center, adjacent_size = adjacent_cutout(mesh, back_z)
    require(np.allclose(
        adjacent_center, expected_adjacent_cutout["target_center_mm"],
        atol=TOL, rtol=0,
    ), "Adjacent cutout position changed")
    require(np.allclose(adjacent_size, expected_adjacent_cutout["size_mm"],
                        atol=TOL, rtol=0),
            "Adjacent cutout size changed")
    tracks = track_groups(holes)
    measurements = []
    row_checks = []
    for plan in expected_rows:
        track = tracks[plan["track_index"]]
        row = track[np.abs(track[:, 1] - plan["target_y_mm"]) < 0.02]
        row = row[np.argsort(row[:, 0])]
        expected_x = np.asarray(plan["target_square_centers_x_mm"])
        require(len(row) == len(expected_x),
                f"Row opening count changed for {plan['track']}")
        actual_square_errors = row[:, 0] - expected_x
        planned_square_errors = np.asarray(
            plan["cell_center_errors_mm"][:len(expected_x)]
        )
        require(np.all(np.abs(actual_square_errors - planned_square_errors) < TOL),
                f"Cube row registration mismatch for {plan['track']} "
                f"at Y={plan['target_y_mm']}")
        actual_cell_x = row[:, 0].tolist()
        if plan["end_slot_cell"]:
            expected_slot = next(
                item for item in expected_slots
                if item["track"] == plan["track"]
                and abs(item["source_row_y_mm"] - plan["source_y_mm"]) < TOL
            )
            distances = np.linalg.norm(
                slot_centers - np.asarray(expected_slot["center_mm"]), axis=1
            )
            slot_index = int(np.argmin(distances))
            require(distances[slot_index] < TOL,
                    "Could not measure exported end-slot center")
            slot_center = slot_centers[slot_index]
            slot_size = slot_sizes[slot_index]
            actual_cell_x.append(float(
                slot_center[0] - slot_size[0] / 2 + OPENING_WIDTH / 2
            ))
        actual_cell_errors = (
            np.asarray(actual_cell_x)
            - np.asarray(plan["target_cell_centers_x_mm"])
        )
        require(np.all(np.abs(
            actual_cell_errors - np.asarray(plan["cell_center_errors_mm"])
        ) < TOL), f"Cube field errors changed for {plan['track']}")
        require(abs(float(row[:, 1].mean()) - plan["target_y_mm"]) < TOL,
                f"Cube row vertical registration mismatch for {plan['track']}")
        row_checks.append({
            **plan,
            "actual_square_centers_x_mm": row[:, 0].tolist(),
            "actual_cell_center_errors_mm": actual_cell_errors.tolist(),
            "actual_row_center_y_mm": float(row[:, 1].mean()),
            "max_abs_actual_center_error_mm": float(
                np.max(np.abs(actual_cell_errors))
            ),
        })

    for track_index, (track, datum) in enumerate(zip(tracks, ROW_ANCHORS)):
        anchor_plan = next(
            plan for plan in expected_rows
            if plan["track_index"] == track_index
            and plan["row_index_from_anchor"] == 0
        )
        row = track[np.abs(track[:, 1] - anchor_plan["target_y_mm"]) < 0.02]
        center_x = float(row[:, 0].min())
        target_x = anchor_plan["target_first_cell_center_x_mm"]
        top_row_y = float(track[:, 1].max())
        target_y = anchor_plan["target_y_mm"]
        measurements.append({
            **datum,
            "opening_count": len(track),
            "first_opening_center_x_mm": center_x,
            "target_center_x_mm": target_x,
            "x_error_mm": center_x - target_x,
            "top_row_center_y_mm": top_row_y,
            "target_center_y_mm": target_y,
            "y_error_mm": top_row_y - target_y,
            "aperture_width_mm": OPENING_WIDTH,
            "cube_edge_mm": CUBE_EDGE,
            "diametral_clearance_mm": OPENING_WIDTH - CUBE_EDGE,
        })
    rows = {}
    for x, y in holes:
        rows.setdefault(round(float(y), 2), []).append(float(x))
    pitches = []
    for xs in rows.values():
        xs.sort()
        pitches.extend(
            right - left for left, right in zip(xs, xs[1:])
            if 9.0 < right - left < 9.3
        )
    require(len(pitches) >= 40, "Insufficient adjacent-cell pitch measurements")
    require(np.allclose(pitches, OPENING_PITCH, atol=0.02, rtol=0),
            "Cube opening pitch changed")
    opening_checks = verify_cube_openings(
        mesh, holes, expected_long_slot, expected_adjacent_cutout
    )
    return measurements, {
        "opening_count": len(holes),
        "opening_probe_checks": opening_checks,
        "cube_track_end_slots": expected_slots,
        "row_registration": row_checks,
        "max_cell_center_error_mm": max(
            item["max_abs_actual_center_error_mm"] for item in row_checks
        ),
        "horizontal_slot": expected_long_slot,
        "slider_clearance": slider_clearance,
        "pitch_min_mm": float(min(pitches)),
        "pitch_max_mm": float(max(pitches)),
        "pitch_mean_mm": float(np.mean(pitches)),
        "separating_web_mm": OPENING_PITCH - OPENING_WIDTH,
    }


def verify_unrelated_cutouts_unchanged(source, revised):
    def descriptors(mesh, mount_centers, z):
        result = []
        for center, size in section_loops(mesh, z):
            is_square = np.all((size > 8.5) & (size < 8.8))
            is_end_slot = (
                17.5 < size.max() < 18.2 and 8.5 < size.min() < 8.8
            )
            is_horizontal_slot = 100 < size[0] < 120 and size[1] > 6.5
            is_adjacent_cutout = (
                17.5 < size[0] < 25.5
                and 12.5 < size[1] < 17.0
                and center[0] < -80.0
            )
            is_resource_window = (
                35.0 < size[0] < 160.0 and 20.0 < size[1] < 60.0
            )
            is_mount = (
                np.all((size > 2.8) & (size < 3.2))
                and np.min(np.linalg.norm(mount_centers - center, axis=1))
                < 0.1
            )
            if (
                not is_square and not is_end_slot
                and not is_horizontal_slot and not is_adjacent_cutout
                and not is_resource_window and not is_mount
                and 35.0 < size.max() < 200
            ):
                result.append([*center.tolist(), *size.tolist()])
        return sorted(result, key=lambda item: (item[1], item[0], item[2], item[3]))

    revised_mounts = SOURCE_MOUNTS.copy()
    for index, center in enumerate(SOURCE_MOUNTS):
        if abs(center[0]) >= 1:
            revised_mounts[index, 0] -= np.sign(center[0])
    revised_z = float(revised.bounds[0, 2]) + LOCAL_RELIEF_EPS_MM + 0.03
    source_z = (
        float(source.bounds[0, 2])
        + (revised_z - float(revised.bounds[0, 2]))
        / float(revised.extents[2]) * float(source.extents[2])
    )
    before = np.asarray(descriptors(source, SOURCE_MOUNTS, source_z))
    after = np.asarray(descriptors(revised, revised_mounts, revised_z))
    require(before.shape == after.shape, "Unrelated cutout count changed")
    require(np.allclose(before, after, atol=TOL, rtol=0),
            "An unrelated cutout moved or changed size")
    return {
        "unchanged": True,
        "unrelated_cutout_count": len(before),
    }


def verify_export(entries, original_entries, expected_slots, expected_rows,
                  expected_long_slot, expected_adjacent_cutout,
                  expected_windows, expected_transition_ramp,
                  expected_local_reliefs):
    meshes = {}
    checks = []
    centers = SOURCE_MOUNTS.copy()
    for path, object_id in MESH_IDS.items():
        _, _, mesh = as_mesh(entries[path], object_id)
        meshes[path] = mesh
        checks.append({
            "path": path,
            "bounds_mm": mesh.bounds.tolist(),
            "extents_mm": mesh.extents.tolist(),
            "euler_number": int(mesh.euler_number),
            "vertices": len(mesh.vertices),
            "triangles": len(mesh.faces),
        })
    front = meshes[FRONT_PATHS[0]]
    duplicate = meshes[FRONT_PATHS[1]]
    rear = meshes[REAR_PATH]
    require(np.array_equal(front.vertices, duplicate.vertices)
            and np.array_equal(front.faces, duplicate.faces),
            "Front mesh copies differ")

    updated_centers = centers.copy()
    for i, center in enumerate(centers):
        if abs(center[0]) >= 1:
            updated_centers[i, 0] -= np.sign(center[0])
    socket_centers = updated_centers
    socket_floor_z = SOCKET_BOTTOM + SOCKET_DEPTH
    socket_top_z = SOCKET_BOTTOM + FRONT_THICKNESS
    mount_results = []
    for center in socket_centers:
        diameter = ring_diameters(
            front, center, socket_floor_z, section_offset=-1e-6
        )
        require(np.allclose(diameter, SOCKET_DIAMETER, atol=TOL, rtol=0),
                f"Socket diameter mismatch at {center.tolist()}: {diameter}")
        floor_probe = probe_at(center, socket_top_z - SOCKET_FLOOR / 2,
                               [0.8, 0.8, 0.1])
        require(abs(probe_intersection(front, floor_probe) - 0.064) < 1e-5,
                f"Blind floor missing at {center.tolist()}")
        bore_probe = probe_at(center, SOCKET_BOTTOM + SOCKET_DEPTH / 2,
                              [0.5, 0.5, SOCKET_DEPTH - 0.02])
        require(probe_intersection(front, bore_probe) < 1e-7,
                f"Socket cavity obstructed at {center.tolist()}")
        mount_results.append({
            "center_mm": center.tolist(),
            "socket_diameter_mm": diameter.tolist(),
            "socket_depth_mm": SOCKET_DEPTH,
            "blind_floor_mm": SOCKET_FLOOR,
        })

    pin_results = []
    for center in socket_centers:
        diameter = ring_diameters(rear, center, PIN_BASE)
        require(np.allclose(diameter, PIN_DIAMETER, atol=TOL, rtol=0),
                f"Pin diameter mismatch at {center.tolist()}: {diameter}")
        pin_results.append({
            "center_mm": center.tolist(),
            "shaft_diameter_mm": diameter.tolist(),
            "projection_mm": PIN_PROJECTION,
        })

    clearance = (
        socket_floor_z + (PIN_BASE - SOCKET_BOTTOM)
        - (PIN_BASE + PIN_PROJECTION)
    )
    require(abs(clearance - AXIAL_CLEARANCE) < TOL,
            f"Unexpected axial clearance: {clearance}")
    insertion = []
    final_translation = PIN_BASE - SOCKET_BOTTOM
    for separation in np.linspace(PIN_PROJECTION + 0.1, 0, 9):
        moved_front = front.copy()
        moved_front.apply_translation([0, 0, final_translation + separation])
        volume = probe_intersection(rear, moved_front)
        require(volume < 0.001, f"Insertion collision: {volume} mm3")
        insertion.append({
            "separation_mm": float(separation),
            "intersection_mm3": volume,
        })
    cube_measurements, pitch_report = verify_cube_grid(
        front, expected_slots, expected_rows, expected_long_slot,
        expected_adjacent_cutout
    )
    window_checks = []
    window_test_levels = (
        float(front.bounds[0, 2]) + 0.05,
        float(front.bounds[0, 2]) + 0.15,
    )
    for z in window_test_levels:
        actual_windows = resource_window_loops(front, z)
        require(len(actual_windows) == 6,
                "The solid transition must retain six separate windows")
        for index, expected in enumerate(expected_windows):
            actual = actual_windows[index]
            expected_center = np.asarray(expected["center_mm"], dtype=float)
            expected_size = np.asarray(expected["size_mm"], dtype=float)
            require(
                np.allclose(actual[0], expected_center,
                            atol=TOL, rtol=0)
                and np.allclose(actual[1], expected_size,
                                atol=TOL, rtol=0),
                f"Exported resource window changed at Z={z}: "
                f"{expected['name']}",
            )
            window_checks.append({
                "name": expected["name"],
                "center_mm": actual[0].tolist(),
                "size_mm": actual[1].tolist(),
                "z_mm": z,
            })
    ramp_checks = verify_window_transition_ramp(
        front, expected_transition_ramp
    )
    local_relief_checks = verify_local_relief_export(
        front, expected_local_reliefs
    )
    _, _, source_front = as_mesh(
        original_entries[FRONT_PATHS[0]], MESH_IDS[FRONT_PATHS[0]]
    )
    unrelated_cutouts = verify_unrelated_cutouts_unchanged(
        source_front, front
    )
    return (
        checks, mount_results, pin_results, insertion, clearance,
        cube_measurements, pitch_report, unrelated_cutouts, window_checks,
        ramp_checks, local_relief_checks,
    )


def block_center_checks(row_registration):
    results = []
    for track_name, translation in NUMBER_BLOCK_SHIFTS_X_MM.items():
        rows = [
            row for row in row_registration if row["track"] == track_name
        ]
        require(rows, f"Missing exported rows for {track_name}")
        centers = []
        field_errors = []
        for row in rows:
            actual = (
                np.asarray(row["target_cell_centers_x_mm"])
                + np.asarray(row["actual_cell_center_errors_mm"])
            )
            centers.extend(actual.tolist())
            field_errors.extend(
                (
                    np.asarray(row["actual_cell_center_errors_mm"])
                    + translation
                ).tolist()
            )
        target = BLOCK_MARKED_TARGET_CENTERS_X_MM[track_name]
        after = float(np.mean(centers))
        before = after - translation
        results.append({
            "track": track_name,
            "field_count": len(centers),
            "marked_target_bounds_px": list(
                BLOCK_MARKUP_TARGET_BOUNDS_PX[track_name]
            ),
            "marked_target_center_x_mm": target,
            "before_cell_centroid_x_mm": before,
            "after_cell_centroid_x_mm": after,
            "before_centroid_error_mm": before - target,
            "after_centroid_error_mm": after - target,
            "translation_x_mm": translation,
            "max_abs_field_error_to_unshifted_anchor_mm": max(
                abs(error) for error in field_errors
            ),
            "field_errors_to_unshifted_anchor_by_row_mm": [
                {
                    "field_labels": row["field_labels"],
                    "errors_mm": (
                        np.asarray(row["actual_cell_center_errors_mm"])
                        + translation
                    ).tolist(),
                }
                for row in rows
            ],
            "max_field_distance_from_block_centroid_mm": max(
                abs(center - after) for center in centers
            ),
            "field_labels_by_row": [
                row["field_labels"] for row in rows
            ],
        })
    return results


def all_track_alignment_checks(row_registration):
    results = []
    for track_index, datum in enumerate(ROW_ANCHORS):
        rows = [
            row for row in row_registration
            if row["track_index"] == track_index
        ]
        net_translation = NUMBER_BLOCK_SHIFTS_X_MM.get(
            datum["name"], 0.0
        )
        row_results = []
        all_errors = []
        for row in rows:
            errors = (
                np.asarray(row["actual_cell_center_errors_mm"])
                + net_translation
            )
            all_errors.extend(errors.tolist())
            row_results.append({
                "field_labels": row["field_labels"],
                "mean_error_mm": float(np.mean(errors)),
                "max_abs_error_mm": float(np.max(np.abs(errors))),
                "errors_mm": errors.tolist(),
            })
        results.append({
            "track": datum["name"],
            "number_block_translation_from_previous_mm": net_translation,
            "field_count": len(all_errors),
            "mean_center_error_mm": float(np.mean(all_errors)),
            "max_abs_center_error_mm": float(
                np.max(np.abs(all_errors))
            ),
            "rows": row_results,
        })
    return results


def main():
    require(sha256(SOURCE) == EXPECTED_SOURCE_SHA256,
            "Unexpected fitted 179 mm source archive")
    require(sha256(PREVIOUS_OUTPUT) == EXPECTED_PREVIOUS_SHA256,
            "The slider/cube baseline source archive changed unexpectedly")
    with zipfile.ZipFile(SOURCE) as archive:
        infos = archive.infolist()
        original = {item.filename: archive.read(item.filename) for item in infos}
    revised = dict(original)
    cube_anchors = []
    cube_rows = []
    cube_slots = []
    long_slot_revision = None
    adjacent_cutout_revision = None
    window_revision = None
    transition_ramp_revision = None
    local_relief_revision = None
    arrow_profiles = None
    transformations = {}
    for path, object_id in MESH_IDS.items():
        root, mesh_node, mesh = as_mesh(original[path], object_id)
        if path in FRONT_PATHS:
            holes = square_holes(mesh, 0.2)
            tracks = track_groups(holes)
            source_slots, source_slot_sizes = double_width_slots(mesh, 0.2)
            row_plans, anchors = track_deltas(
                tracks, source_slots, source_slot_sizes
            )
            if not cube_anchors:
                cube_anchors = anchors
                cube_rows = row_plans
            else:
                require(anchors == cube_anchors,
                        "Front copies have different cube-track datums")
            (mesh, moved_holes, moved_slots, revised_arrow_profiles,
             revised_long_slot, revised_adjacent_cutout,
             revised_windows) = relocate_cube_openings(
                mesh, tracks, row_plans
            )
            if not cube_slots:
                cube_slots = moved_slots
            else:
                require(moved_slots == cube_slots,
                        "Front copies have different cube end slots")
            if arrow_profiles is None:
                arrow_profiles = revised_arrow_profiles
            else:
                require(revised_arrow_profiles == arrow_profiles,
                        "Front copies have different arrow ledge profiles")
            if long_slot_revision is None:
                long_slot_revision = revised_long_slot
            else:
                require(revised_long_slot == long_slot_revision,
                        "Front copies have different horizontal slots")
            if adjacent_cutout_revision is None:
                adjacent_cutout_revision = revised_adjacent_cutout
            else:
                require(revised_adjacent_cutout == adjacent_cutout_revision,
                        "Front copies have different adjacent cutouts")
            if window_revision is None:
                window_revision = revised_windows
            else:
                require(revised_windows == window_revision,
                        "Front copies have different resource windows")
        else:
            deltas = None
            anchors = None
            moved_slots = None
            revised_long_slot = None
            revised_adjacent_cutout = None
            revised_windows = None
        mesh, moved_mount_centers = move_mount_vertices(mesh, SOURCE_MOUNTS)
        if path in FRONT_PATHS:
            mesh, z_result = scale_front_z(mesh, moved_mount_centers)
            mesh, revised_transition_ramp = add_window_transition_ramp(mesh)
            if transition_ramp_revision is None:
                transition_ramp_revision = revised_transition_ramp
            else:
                require(revised_transition_ramp == transition_ramp_revision,
                        "Front copies have different window transition ramps")
            mesh, revised_local_reliefs = add_local_support_features(
                mesh, moved_slots, revised_arrow_profiles,
                revised_adjacent_cutout,
            )
            if local_relief_revision is None:
                local_relief_revision = revised_local_reliefs
            else:
                require(revised_local_reliefs == local_relief_revision,
                        "Front copies have different local relief features")
            transformations[path] = {
                "cube_tracks": anchors,
                "cube_row_registration": row_plans,
                "cube_track_end_slots": moved_slots,
                "horizontal_slot": revised_long_slot,
                "adjacent_cutout": revised_adjacent_cutout,
                "resource_windows": revised_windows,
                "window5_to6_ramp": revised_transition_ramp,
                "local_reliefs": revised_local_reliefs,
                "mount_centers_mm": moved_mount_centers.tolist(),
                "front_z": z_result,
            }
        else:
            mesh = shorten_pins(mesh, moved_mount_centers)
            transformations[path] = {
                "mount_centers_mm": moved_mount_centers.tolist(),
                "pin_projection_mm": PIN_PROJECTION,
                "tip_z_mm": PIN_BASE + PIN_PROJECTION,
            }
        mesh = trim_long_edges(mesh)
        revised[path] = mesh_xml(root, mesh_node, mesh)

    (revised["Metadata/project_settings.config"],
     revised["Metadata/model_settings.config"],
     transparent_object_settings) = apply_transparent_filament_settings(
        original["Metadata/project_settings.config"],
        original["Metadata/model_settings.config"],
    )
    revised[PRINT_METADATA_ENTRY] = unverified_print_metadata(
        json.loads(revised["Metadata/project_settings.config"]),
        revised["Metadata/model_settings.config"],
    )
    front_build_rotations = rotate_front_build_items(revised)
    with zipfile.ZipFile(OUTPUT, "w") as archive:
        for info in infos:
            archive.writestr(info, revised[info.filename])
        if PRINT_METADATA_ENTRY not in original:
            archive.writestr(
                PRINT_METADATA_ENTRY, revised[PRINT_METADATA_ENTRY]
            )
    with zipfile.ZipFile(OUTPUT) as archive:
        require(archive.testzip() is None, "Output 3MF CRC check failed")
        expected_names = list(original)
        if PRINT_METADATA_ENTRY not in original:
            expected_names.append(PRINT_METADATA_ENTRY)
        require(archive.namelist() == expected_names,
                "3MF archive member list changed")
        revised = {name: archive.read(name) for name in archive.namelist()}
    changed_entries = set(MESH_IDS) | {
        "3D/3dmodel.model",
        "Metadata/project_settings.config",
        "Metadata/model_settings.config",
        PRINT_METADATA_ENTRY,
    } | set(FRONT_PLATE_PREVIEWS)
    for name in original.keys() - changed_entries:
        require(original[name] == revised[name],
                f"Unrelated archive member changed: {name}")
    for name, content in revised.items():
        if name.endswith((".model", ".config", ".xml", ".rels")):
            if content.lstrip().startswith(b"{"):
                json.loads(content)
            else:
                ET.fromstring(content)

    (mesh_checks, sockets, pins, insertion, clearance,
     cube_checks, pitch_report, unrelated_cutouts,
     window_checks, transition_ramp_checks,
     local_relief_checks) = verify_export(
        revised, original, cube_slots, cube_rows, long_slot_revision,
        adjacent_cutout_revision, window_revision,
        transition_ramp_revision, local_relief_revision,
    )
    layout_clearances = verify_layout_clearances(
        cube_rows, window_revision, long_slot_revision["target_center_mm"],
        long_slot_revision["target_size_mm"],
    )
    block_checks = block_center_checks(
        pitch_report["row_registration"]
    )
    all_track_checks = all_track_alignment_checks(
        pitch_report["row_registration"]
    )
    previous_front = load_previous_front()
    previous_slot_center, previous_slot_size = long_horizontal_slot(
        previous_front, 0.0, PREVIOUS_LONG_SLOT_HEIGHT
    )
    require(
        abs(previous_slot_size[0] - long_slot_revision["target_size_mm"][0])
        < TOL
        and abs(previous_slot_size[1] - PREVIOUS_LONG_SLOT_HEIGHT) < TOL,
        "Unexpected previous slider dimensions",
    )
    require(
        abs(
            previous_slot_center[1] + previous_slot_size[1] / 2
            - long_slot_revision["target_center_mm"][1]
            - LONG_SLOT_HEIGHT / 2
        ) < TOL,
        "Slider top edge moved instead of extending downward",
    )
    project_settings = json.loads(revised["Metadata/project_settings.config"])
    original_project_settings = json.loads(
        original["Metadata/project_settings.config"]
    )
    settings_preserved = verify_filament_scope(
        original_project_settings,
        project_settings,
        original["Metadata/model_settings.config"],
        revised["Metadata/model_settings.config"],
        transparent_object_settings,
    )
    source_nozzle_range = (
        float(project_settings["nozzle_temperature_range_low"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ]),
        float(project_settings["nozzle_temperature_range_high"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ]),
    )
    require(
        source_nozzle_range[0] <= 220 <= source_nozzle_range[1],
        "Requested 220 C exceeds the selected filament's declared range",
    )
    source_scene = ET.fromstring(original["3D/3dmodel.model"])
    revised_scene = ET.fromstring(revised["3D/3dmodel.model"])
    source_build_items = source_scene.findall("./m:build/m:item", NS)
    revised_build_items = revised_scene.findall("./m:build/m:item", NS)
    require(
        len(revised_build_items) == len(source_build_items)
        and [
            item.get("objectid") for item in revised_build_items
        ] == [item.get("objectid") for item in source_build_items],
        "3MF plate count or build-item identities changed",
    )
    for source_item, revised_item in zip(
        source_build_items, revised_build_items
    ):
        if source_item.get("objectid") not in {
            record["build_object_id"] for record in front_build_rotations
        }:
            require(
                source_item.get("transform") == revised_item.get("transform"),
                "A non-front build-item transform changed",
            )
    selected_row_residuals = []
    for row in pitch_report["row_registration"]:
        if row["track"] != "lower-right zero":
            continue
        selected_labels = (
            FOLLOWUP_SELECTED_FIELD_LABELS["upper"]
            if row["row_index_from_anchor"] == 0
            else FOLLOWUP_SELECTED_FIELD_LABELS["lower"]
        )
        for label, after_error in zip(
            row["field_labels"], row["actual_cell_center_errors_mm"]
        ):
            if label in selected_labels:
                selected_row_residuals.append({
                    "row": row["row_index_from_anchor"],
                    "field": label,
                    "before_error_vs_red_target_mm": (
                        after_error - LOWER_RIGHT_TRACK_SHIFT_X_MM
                    ),
                    "after_error_vs_red_target_mm": after_error,
                })
    require(len(selected_row_residuals) == 6,
            "Could not report residuals for all six selected cube fields")
    transparent_settings = {
        "filament_profile": TRANSPARENT_FILAMENT_PROFILE,
        "filament_slot": TRANSPARENT_FILAMENT_SLOT,
        "bed_type": plate_bed_type(
            revised["Metadata/model_settings.config"],
            TRANSPARENT_PLATE_ID,
        ),
        "global_bed_type": project_settings.get("curr_bed_type", "unknown"),
        "cool_plate_temperature_c": project_settings["cool_plate_temp"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ],
        "cool_plate_first_layer_temperature_c": project_settings[
            "cool_plate_temp_initial_layer"
        ][TRANSPARENT_FILAMENT_SLOT - 1],
        "normal_nozzle_temperature_c": project_settings[
            "nozzle_temperature"
        ][TRANSPARENT_FILAMENT_SLOT - 1],
        "first_layer_nozzle_temperature_c": project_settings[
            "nozzle_temperature_initial_layer"
        ][TRANSPARENT_FILAMENT_SLOT - 1],
        "declared_nozzle_range_c": list(source_nozzle_range),
        "flow_ratio_preserved": project_settings["filament_flow_ratio"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ],
        "first_layer_flow_ratio": project_settings["first_layer_flow_ratio"],
        "first_layer_line_width_mm": project_settings[
            "initial_layer_line_width"
        ],
        "first_layer_print_sequence": project_settings[
            "first_layer_print_sequence"
        ],
        "first_layer_speed_mm_s": transparent_object_settings[
            "initial_layer_speed"
        ],
        "first_layer_solid_infill_speed_mm_s": project_settings[
            "initial_layer_infill_speed"
        ],
        "first_layer_solid_infill_applies": (
            int(transparent_object_settings["bottom_shell_layers"]) > 0
        ),
        "part_fan_normal_percent": project_settings["fan_min_speed"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ],
        "part_fan_max_percent": project_settings["fan_max_speed"][
            TRANSPARENT_FILAMENT_SLOT - 1
        ],
        "auxiliary_fan_percent": project_settings[
            "additional_cooling_fan_speed"
        ][TRANSPARENT_FILAMENT_SLOT - 1],
        "object_overrides": transparent_object_settings,
        "preserved": [
            "Original filament slots 1-3",
            "Global process settings and non-transparent filament temperatures",
            "Calibrated nozzle temperature and flow",
            "First-layer flow ratio, line width and print sequence",
            "Native filament start/end/change routines",
            "Bridge/overhang cooling behavior",
        ],
    }
    transparent_guide_review = {
        "references": [
            "https://doi.org/10.3390/polym16202862",
            "https://blog.snapmaker.com/blog/how-to-3d-print-clear-filament/",
            "https://us.qidi3d.com/blogs/guides/tips-for-3d-printing-with-transparent-filaments",
            "https://www.youtube.com/watch?v=MKyC1qbvAyI",
            "https://www.orcaslicer.com/wiki/print_settings/strength/strength_settings_top_bottom_shells",
        ],
        "core_recipe_match": {
            "layer_height_mm": "0.10 object override",
            "speed_mm_s": "20 object overrides for walls, infill, gap and top",
            "wall_loops": transparent_object_settings["wall_loops"],
            "top_bottom_shell_layers": [
                transparent_object_settings["top_shell_layers"],
                transparent_object_settings["bottom_shell_layers"],
            ],
            "infill_density_percent": (
                "100% transparent-front object override"
            ),
            "same_direction_infill": True,
            "all_solid_surface_patterns_aligned": True,
            "top_surface_followup": {
                "top_shell_layers": transparent_object_settings[
                    "top_shell_layers"
                ],
                "top_shell_thickness_mm": transparent_object_settings[
                    "top_shell_thickness"
                ],
                "ironing_type": transparent_object_settings["ironing_type"],
                "infill_direction_degrees": transparent_object_settings[
                    "infill_direction"
                ],
                "solid_infill_direction_degrees": transparent_object_settings[
                    "solid_infill_direction"
                ],
                "short_axis_track_length_mm": SHORT_SIDE,
                "long_axis_track_length_mm": NEW_LENGTH,
                "intent": (
                    "Two 0.10 mm top-skin layers and top ironing provide a "
                    "smoother surface candidate. Rotating aligned raster lines "
                    "to the shorter panel axis reduces continuous line length; "
                    "physical surface and clarity remain unverified."
                ),
            },
        },
        "settings_changed_after_review": [
            "Increase transparent-front top skin from one to two 0.10 mm layers while retaining top ironing.",
            "Rotate the 100% aligned single-direction infill and solid-surface raster to 90 degrees, along the panel's shorter axis.",
            "Keep global Textured PEI; select Cool Plate only for transparent-front plate 3 and retain only transparent PLA slot 4 Cool Plate first/normal bed temperatures at 35 C, within the manufacturer-stated 30-50 C range.",
            "Reduce transparent-front object initial-layer wall/sparse speed from 40 to 20 mm/s; with zero bottom-shell layers, first-layer fill follows this sparse-infill speed, so the separate 60 mm/s solid-infill setting is unchanged and inapplicable. Retain first-layer flow, line width and print sequence.",
        ],
        "not_adopted": [
            "Simplify3D-specific outline/solid underspeed percentages; no successful slice to verify effective speed",
            "A 0.30 mm layer / 240 C / 100% fan / 0.75 flow optimum reported for a different PLA on Prusa MK4 1 mm coupons; not transferred to this Kobra S1 fit-critical 2.5 mm panel.",
            "PETG temperatures, wider lines, 1.01 flow, and PETG drying schedules are not transferable to the unidentified transparent PLA spool",
        ],
        "effective_gcode_speeds_verified": False,
    }
    socket_clearances = {
        "long_side_mm": min(
            abs(mount["center_mm"][0]) - SOCKET_DIAMETER / 2
            - LAMINATE_LENGTH / 2
            for mount in sockets if abs(mount["center_mm"][0]) > 1
        ),
        "short_side_mm": min(
            abs(mount["center_mm"][1]) - SOCKET_DIAMETER / 2
            - LAMINATE_WIDTH / 2
            for mount in sockets if abs(mount["center_mm"][1]) > 1
        ),
    }
    pin_clearances = {
        "long_side_mm": min(
            abs(pin["center_mm"][0]) - PIN_DIAMETER / 2
            - LAMINATE_LENGTH / 2
            for pin in pins if abs(pin["center_mm"][0]) > 1
        ),
        "short_side_mm": min(
            abs(pin["center_mm"][1]) - PIN_DIAMETER / 2
            - LAMINATE_WIDTH / 2
            for pin in pins if abs(pin["center_mm"][1]) > 1
        ),
    }
    report = {
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": EXPECTED_SOURCE_SHA256,
        "output": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "output_sha256": sha256(OUTPUT),
        "requested_revision": {
            "long_dimension_before_mm": OLD_LENGTH,
            "long_dimension_after_mm": NEW_LENGTH,
            "short_dimension_mm": SHORT_SIDE,
            "front_thickness_mm": FRONT_THICKNESS,
            "cube_edge_mm": 8.5,
            "laminate_left_edge_model_x_mm": PAPER_LEFT,
            "cube_anchor_edge_offsets_x_mm": [a["offset_x"] for a in ROW_ANCHORS],
            "cube_anchor_edge_offsets_y_mm": [a["top_distance"] for a in ROW_ANCHORS],
            "lower_right_user_mark_translation_mm": [
                LOWER_RIGHT_TRACK_SHIFT_X_MM, 0.0
            ],
            "number_block_translations_x_mm": NUMBER_BLOCK_SHIFTS_X_MM,
            "transparent_filament_settings": transparent_settings,
            "laminated_insert_outer_size_mm": [
                LAMINATE_LENGTH, LAMINATE_WIDTH
            ],
            "frame_margin_each_side_mm": [FRAME_MARGIN_X, FRAME_MARGIN_Y],
        },
        "laminate_registration": {
            "outer_size_mm": [LAMINATE_LENGTH, LAMINATE_WIDTH],
            "source": "User measurement including transparent sealed edge",
            "paper_edge_model_coordinates_mm": {
                "left_x": PAPER_LEFT,
                "top_y": PAPER_TOP,
            },
            "frame_margin_each_side_mm": [
                FRAME_MARGIN_X, FRAME_MARGIN_Y
            ],
            "socket_clearances_to_laminate_edges_mm": socket_clearances,
            "pin_clearances_to_laminate_edges_mm": pin_clearances,
            "z_stack_policy": (
                "Kept identical to the current model per user direction; "
                "the physical laminate thickness and assembled compression "
                "were not independently measured or tested."
            ),
        },
        "fit": {
            "socket_diameter_mm": SOCKET_DIAMETER,
            "pin_diameter_mm": PIN_DIAMETER,
            "socket_depth_mm": SOCKET_DEPTH,
            "blind_floor_mm": SOCKET_FLOOR,
            "pin_projection_mm": PIN_PROJECTION,
            "axial_clearance_mm": clearance,
            "sockets": sockets,
            "pins": pins,
            "insertion_sweep": insertion,
        },
        "cube_grid": {
            "anchors": cube_checks,
            "unrelated_cutouts": unrelated_cutouts,
            "adjacent_cutout": adjacent_cutout_revision,
            "local_reliefs": local_relief_checks,
            "pitch_and_web": pitch_report,
            "cube_fit": {
                "cube_edge_mm": CUBE_EDGE,
                "measured_clear_aperture_minimum_mm": OPENING_WIDTH,
                "measured_clear_aperture_maximum_mm": OPENING_WIDTH,
                "diametral_clearance_mm": OPENING_WIDTH - CUBE_EDGE,
                "nominal_clearance_per_side_mm": (
                    OPENING_WIDTH - CUBE_EDGE
                ) / 2,
                "through_thickness_probe_z_levels_mm": (
                    pitch_report["opening_probe_checks"]["tested_z_levels_mm"]
                ),
                "inset_and_boundary_probes_passed": True,
                "physical_cube_fit_tested": False,
                "note": (
                    "CAD clearance only. FDM dimensional variation, "
                    "elephant foot, and slicer extrusion effects can change "
                    "the printed opening; no successful slice or physical "
                    "cube insertion test is available."
                ),
            },
            "all_six_track_alignment": {
                "tracks": all_track_checks,
                "global_mirror_symmetry_forced": False,
                "symmetry_note": (
                    "The printed board artwork and row anchors are not "
                    "globally symmetric. Preserve per-block alignment to "
                    "the printed artwork rather than impose a mirror layout."
                ),
            },
            "layout_clearances": layout_clearances,
            "resource_windows": {
                "user_constraints": {
                    "all_six_height_mm": RESOURCE_WINDOW_HEIGHT_MM,
                    "upper_left_width_mm": UPPER_LEFT_WINDOW_WIDTH_MM,
                    "upper_left_expansion_direction": "left; right edge fixed",
                    "window_4_minimum_width_mm": 69.0,
                    "window_6_minimum_width_mm": (
                        LOWER_RIGHT_WINDOW_MIN_WIDTH_MM
                    ),
                    "window_6_expansion_direction": "right; left edge fixed",
                },
                "source": (
                    "Six orange marked regions, mapped with a single "
                    "paper-centered transform and resized to user constraints"
                ),
                "photo_calibration": {
                    "pixels_per_mm": PHOTO_PX_PER_MM,
                    "reference_center_px": list(PHOTO_REFERENCE_CENTER_PX),
                    "window_inset_px": PHOTO_WINDOW_INSET_PX,
                    "reference_photo_size_px": [1321, 796],
                    "estimated_photo_boundary_uncertainty_mm": 1.0,
                },
                "targets": window_revision,
                "exported_section_checks": window_checks,
                "window5_to6_ramp": {
                    **transition_ramp_revision,
                    "exported_cube_probe_checks": transition_ramp_checks,
                    "note": (
                        "A solid ramp spans the complete 42.754 mm shared "
                        "window height. Its 8.640 mm horizontal run rises "
                        "2.500 mm at 16.14 degrees from window 5 on the left "
                        "to window 6 on the right. The photo registration maps "
                        "increasing model X to the right; the earlier reversed "
                        "profile was incorrect. The high endpoint is on "
                        "window 6's left edge, preserving its 69 mm width; "
                        "the ramp removes the old divider shoulder above the "
                        "incline. Mesh cross-sections and material/void probes "
                        "check the monotone face at three positions along its "
                        "length. The 8.5 mm cube sweep is CAD-only."
                    ),
                },
            },
            "policy": (
                "Retain six separate cube tracks, openings and webs. Convert "
                "the user-measured lower/upper row offsets from the laminated "
                "outer edge into model coordinates using the measured "
                "227 x 168 mm insert and centered 238.401 x 179 mm frame. "
                "Translate each printed row independently and balance residuals "
                "over every cell in that row. Preserve the "
                "9.16 mm opening pitch and 8.64 mm openings, so 8.5 mm printed "
                "cells cannot all be centered without overlap."
            ),
        },
        "followup_adjustments": {
            "reference": "User red-marked overlay of the previous exported laminate-aligned model",
            "scope": [
                "Center the middle slider cutout on the red rounded outline",
                "Translate only the lower-right cube-track subrows to the right",
            ],
            "screen_calibration": {
                "panel_outline_bounds_px": list(FOLLOWUP_REFERENCE_BOUNDS_PX),
                "panel_size_mm": [NEW_LENGTH, SHORT_SIDE],
                "pixels_per_mm_xy": [
                    FOLLOWUP_SCREEN_PX_PER_MM_X,
                    FOLLOWUP_SCREEN_PX_PER_MM_Y,
                ],
                "estimated_annotation_reading_uncertainty_mm": 0.8,
            },
            "slider": {
                "previous_center_mm": previous_slot_center.tolist(),
                "previous_size_mm": previous_slot_size.tolist(),
                "red_outline_bounds_px": list(
                    FOLLOWUP_SLIDER_MARK_BOUNDS_PX
                ),
                "red_outline_center_px": list(FOLLOWUP_SLIDER_MARK_CENTER_PX),
                "red_outline_size_mm": FOLLOWUP_SLIDER_SIZE_MM.tolist(),
                "target_center_mm": FOLLOWUP_SLIDER_CENTER_MM.tolist(),
                "translation_mm": (
                    FOLLOWUP_SLIDER_CENTER_MM
                    - previous_slot_center
                ).tolist(),
                "slot_size_mm": long_slot_revision["target_size_mm"],
                "extension_down_mm": SLIDER_EXTENSION_DOWN_MM,
                "top_edge_preserved": long_slot_revision[
                    "top_edge_preserved"
                ],
                "collision_clearance_mm": (
                    layout_clearances["minimum_slider_to_cube_clearance_mm"]
                ),
            },
            "window5_to6_transition": {
                **transition_ramp_revision,
                "exported_cube_probe_checks": transition_ramp_checks,
            },
            "small_siegpunkte_window": {
                **adjacent_cutout_revision,
                "exported_geometry": local_relief_checks["small_window"],
                "inner_area_solid": True,
                "web_to_zero_cube_field": (
                    local_relief_checks["small_window_web"]
                ),
            },
            "ten_cube_arrow_ledges": {
                "count": local_relief_checks["end_slot_count"],
                "back_layer_thickness_mm": END_ARROW_LEDGE_THICKNESS_MM,
                "front_recess_depth_mm": (
                    FRONT_THICKNESS - END_ARROW_LEDGE_THICKNESS_MM
                ),
                "rear_face_flush": True,
                "fields": local_relief_checks["end_slots"],
                "cube_fit_and_overrun_support_passed": (
                    local_relief_checks["cube_fit_and_overrun_support_passed"]
                ),
                "physical_stability_tested": False,
            },
            "transparent_front_surface": {
                "top_shell_layers": transparent_object_settings[
                    "top_shell_layers"
                ],
                "top_shell_thickness_mm": float(
                    transparent_object_settings["top_shell_thickness"]
                ),
                "ironing_type": transparent_object_settings["ironing_type"],
                "object_id": "6",
                "bed_type": TRANSPARENT_BED_TYPE,
                "global_bed_type": project_settings["curr_bed_type"],
                "cool_plate_temperature_c": TRANSPARENT_BED_TEMPERATURE_C,
                "cool_plate_first_layer_temperature_c": (
                    TRANSPARENT_BED_TEMPERATURE_C
                ),
                "bed_temperature_scope": (
                    "Cool Plate is stored as the bed_type override only on "
                    "transparent-front plate "
                    "3; the global bed type and other plates remain unchanged. "
                    "Only transparent filament slot 4 Cool Plate temperatures "
                    "are changed."
                ),
                "bed_plate_source": (
                    "User-selected UniTak3D Energy-Saving Kobra S1/Kobra X/"
                    "Kobra 4 double-sided glossy/matte plate; seller lists "
                    "30-50 C for the smooth side with PLA. 35 C matches the "
                    "existing Cool Plate PLA profile and is not physically "
                    "validated."
                ),
                "other_material_profiles_changed": False,
                "optical_result_physically_tested": False,
            },
            "lower_right_cube_rows": {
                "track": "lower-right zero",
                "selected_fields": FOLLOWUP_SELECTED_FIELD_LABELS,
                "translation_mm": [
                    LOWER_RIGHT_TRACK_SHIFT_X_MM, 0.0
                ],
                "opening_width_mm": OPENING_WIDTH,
                "pitch_mm": OPENING_PITCH,
                "web_mm": OPENING_PITCH - OPENING_WIDTH,
                "selected_field_center_residuals_vs_red_targets_mm":
                    selected_row_residuals,
                "note": (
                    "Residuals are computed from exported opening centers and "
                    "the requested +2.0 mm screenshot-derived target shift. "
                    "The target interpretation is approximate; the openings, "
                    "pitch and separating webs are unchanged."
                ),
            },
            "number_block_centering": {
                "reference": (
                    "User-marked screenshot red rectangles; block centroids "
                    "measured from the exported cube fields"
                ),
                "panel_outline_bounds_px": list(
                    BLOCK_MARKUP_PANEL_BOUNDS_PX
                ),
                "panel_size_mm": [NEW_LENGTH, SHORT_SIDE],
                "pixels_per_mm_x": BLOCK_MARKUP_PX_PER_MM_X,
                "estimated_alignment_uncertainty_mm": 1.0,
                "translations_x_mm": NUMBER_BLOCK_SHIFTS_X_MM,
                "blocks": block_checks,
                "note": (
                    "Whole-block translations preserve row spacing and "
                    "pocket geometry. Remaining per-field offsets include "
                    "the intentional mismatch between 9.16 mm pocket pitch "
                    "and 8.5 mm printed-field pitch; the photo-derived mark "
                    "centers are approximate."
                ),
            },
            "frozen_geometry": [
                "Resource window layout except the requested local 5-to-6 transition",
                "The middle two cube tracks and their rows",
                "Panel envelope, laminate registration, mounts and Z stack",
                "All unrelated filament slots and printer/process settings",
            ],
        },
        "mesh_checks": mesh_checks,
        "plate_layout": {
            "source_build_item_count": len(source_build_items),
            "output_build_item_count": len(revised_build_items),
            "build_item_ids_and_plate_order_preserved": True,
            "front_part_rotations": front_build_rotations,
            "front_plate_preview_images_rotated": list(
                FRONT_PLATE_PREVIEWS
            ),
            "rear_part_transform_unchanged": True,
            "in_plane_rotation_preserves_bed_contact": True,
            "printer_profile": project_settings.get(
                "printer_settings_id", "unknown"
            ),
            "printable_area": project_settings.get("printable_area"),
            "bed_placement_status": (
                "Preserved exactly from the preceding project; independent "
                "slicer confirmation unavailable because slicing failed."
            ),
        },
        "transformations": transformations,
        "filament_scope_checks_passed": settings_preserved,
        "transparent_guide_review": transparent_guide_review,
        "physical_fit": (
            "The 3.0 mm sockets / 2.6 mm pins are inherited from the previously "
            "coupon-tested variant. The new 2.5 mm front, shortened pins, "
            "laminate-edge registration, resized windows and complete tableau "
            "fit have not been physically tested. The user asked to preserve "
            "the existing Z stack; laminate thickness/compression remains "
            "unverified. The transparent PLA profile has no physical test "
            "print on this 0.10 mm / 20 mm/s revision."
        ),
        "slicer_validation": {
            "status": "not-sliced-after-local-reliefs",
            "gcode_files_produced": 0,
            "support_enabled": project_settings.get("enable_support") == "1",
            "current_attempt_artifact": str(
                OUTPUT.relative_to(ROOT)
            ).replace("\\", "/"),
            "current_attempt_artifact_sha256": sha256(OUTPUT),
            "current_attempt_command": None,
            "current_attempt_exit_code": None,
            "current_attempt_diagnostic": (
                "No slice was run after adding the local window and arrow "
                "reliefs. The preceding integrated artifact failed before "
                "G-code generation with the saved retraction setting."
            ),
            "current_attempt_log": None,
            "current_attempt_gcode_files_produced": 0,
            "prior_attempts_artifact": str(
                OUTPUT.relative_to(ROOT)
            ).replace("\\", "/"),
            "prior_attempts_artifact_sha256": (
                "2a6297ed8d9cd30123396c4f61ac3af48a3b73c4ebe8c37abc72859b01982695"
            ),
            "prior_attempts_status": (
                "failed before local reliefs; no G-code produced"
            ),
            "prior_orca_slicer_command": (
                "orca-slicer.exe "
                "models/terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf "
                "--slice=0 --outputdir=build/tableau-final-sliced"
            ),
            "prior_orca_slicer_exit_code": -18,
            "prior_orca_slicer_exit_code_windows": 4294967278,
            "prior_orca_slicer_log": "build/tableau-final-slice.log",
            "prior_orca_slicer_cli_version": (
                "unreported; --version is not supported by this executable"
            ),
            "orca_slicer_version": "2.0.0.0",
            "orca_slicer_exit_code": -18,
            "orca_slicer_diagnostic": (
                "retraction_distances_when_cut=0 is outside [10,18]; "
                "the CLI also could not find the referenced BBL process preset."
            ),
            "anycubic_slicer_next_version": "2.0.0.3",
            "anycubic_slicer_next_exit_code": -1073741819,
            "anycubic_slicer_next_diagnostic": (
                "CLI crashed before producing G-code after "
                "calc_exclude_triangles reported it could not create exclude "
                "triangles; stderr also reports missing report.ini."
            ),
            "print_estimates": "unknown; no successful slice",
        },
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "output_sha256": report["output_sha256"],
        "panel_mm": [NEW_LENGTH, SHORT_SIDE],
        "laminate_mm": [LAMINATE_LENGTH, LAMINATE_WIDTH],
        "frame_margin_each_side_mm": [FRAME_MARGIN_X, FRAME_MARGIN_Y],
        "socket_clearance_to_laminate_mm": socket_clearances,
        "pin_clearance_to_laminate_mm": pin_clearances,
        "front_thickness_mm": FRONT_THICKNESS,
        "axial_clearance_mm": clearance,
        "cube_openings": pitch_report["opening_count"],
        "max_cube_center_error_mm": pitch_report["max_cell_center_error_mm"],
        "minimum_window_web_mm": (
            layout_clearances["minimum_window_to_window_web_mm"]
        ),
        "minimum_window_to_cube_clearance_mm": (
            layout_clearances["minimum_window_to_cube_clearance_mm"]
        ),
        "slider_center_mm": long_slot_revision["target_center_mm"],
        "slider_translation_mm": (
            FOLLOWUP_SLIDER_CENTER_MM - previous_slot_center
        ).tolist(),
        "slider_size_mm": long_slot_revision["target_size_mm"],
        "slider_extension_down_mm": SLIDER_EXTENSION_DOWN_MM,
        "window5_to6_ramp_run_mm": (
            transition_ramp_revision["target_ramp_run_mm"]
        ),
        "window5_to6_ramp_geometry_passed": (
            transition_ramp_checks["geometry_passed"]
        ),
        "lower_right_cube_translation_mm": [
            LOWER_RIGHT_TRACK_SHIFT_X_MM, 0.0
        ],
        "slider_clearance_mm": (
            layout_clearances["minimum_slider_to_cube_clearance_mm"]
        ),
        "transparent_filament_settings": transparent_settings,
        "filament_scope_checks_passed": settings_preserved,
    }, indent=2))


if __name__ == "__main__":
    main()
