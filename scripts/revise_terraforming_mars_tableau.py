"""Build a laminate-registered tableau revision from the approved fitted 3MF."""

import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh

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
FOLLOWUP_SLIDER_CENTER_MM = np.asarray([
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
TRANSPARENT_FILAMENT_SLOT = 4
TRANSPARENT_FILAMENT_PROFILE = (
    "Transparent PLA slow test @Anycubic Kobra S1 0.4 nozzle"
)
SOCKET_DIAMETER = 3.0
PIN_DIAMETER = 2.6
SOCKET_FLOOR = 0.5
SOCKET_DEPTH = FRONT_THICKNESS - SOCKET_FLOOR
PIN_PROJECTION = SOCKET_DEPTH - 0.4
AXIAL_CLEARANCE = 0.4
CUBE_EDGE = 8.5
OPENING_WIDTH = 8.64
OPENING_PITCH = 9.16
LONG_SLOT_HEIGHT = 6.8
MIN_SLOT_CLEARANCE = 0.5
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


TARGET_WINDOWS = tuple(photo_box_to_model(box) for box in PHOTO_WINDOW_BOXES_PX)
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


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    different[TRANSPARENT_FILAMENT_SLOT + 1] = (
        "filament_settings_id;nozzle_temperature;"
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
        "infill_direction": "0",
        "solid_infill_direction": "0",
        "sparse_infill_rotate_template": "0",
        "solid_infill_rotate_template": "0",
        "top_shell_layers": "0",
        "bottom_shell_layers": "0",
        "wall_loops": "2",
    }
    for key, value in object_settings.items():
        existing = metadata.get(key)
        if existing is None:
            existing = ET.SubElement(transparent, "metadata", key=key)
            metadata[key] = existing
        existing.set("value", value)
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
            require(new_value[:5] == old_value[:5],
                    "Process, machine, or original filament override flags changed")
            expected_filament_flags = {
                "filament_settings_id",
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

    profile = revised["filament_settings_id"][TRANSPARENT_FILAMENT_SLOT - 1]
    require(profile == TRANSPARENT_FILAMENT_PROFILE,
            "Transparent filament profile name was not persisted")
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
    plate_details = [
        {"name": f"Plate {index} - {profile}", **unknown_stats}
        for index, profile in enumerate(active_profiles, start=1)
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
        "bedType": settings.get("curr_bed_type", "unknown"),
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
        if 24.0 < size[0] < 24.5
        and 15.3 < size[1] < 15.9
        and center[0] < -80.0
    ]
    require(len(cutouts) == 1,
            f"Expected one adjacent cube-zone cutout, found {len(cutouts)}")
    return cutouts[0]


def resource_window_loops(mesh, z):
    windows = [
        (center, size) for center, size in section_loops(mesh, z)
        if 35.0 < size[0] < 100.0 and 20.0 < size[1] < 60.0
    ]
    require(len(windows) == 6,
            f"Expected six resource windows, found {len(windows)}")
    return sorted(windows, key=lambda item: (-int(item[0][1] > 0), item[0][0]))


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
    moved_slots = []
    for center, size in zip(slot_centers, slot_sizes):
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
    source_adjacent_center, source_adjacent_size = adjacent_cutout(mesh, 0.2)
    target_adjacent_center = source_adjacent_center + np.asarray([
        ADJACENT_CUTOUT_SHIFT_X, 0.0
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
        extents=[source_adjacent_size[0], source_adjacent_size[1],
                 old_thickness + 0.04]
    )
    adjacent_cutter.apply_translation([
        target_adjacent_center[0], target_adjacent_center[1], 0
    ])
    cut_boxes.append(adjacent_cutter)
    adjacent_cutout_revision = {
        "source_center_mm": source_adjacent_center.tolist(),
        "target_center_mm": target_adjacent_center.tolist(),
        "translation_mm": [ADJACENT_CUTOUT_SHIFT_X, 0.0],
        "size_mm": source_adjacent_size.tolist(),
    }
    source_slot_center, source_slot_size = long_horizontal_slot(mesh, 0.2, 8.64)
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
        "target_center_mm": target_slot_center.tolist(),
        "target_size_mm": [float(source_slot_size[0]), LONG_SLOT_HEIGHT],
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
    require(np.allclose(actual_adjacent_size, source_adjacent_size,
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
        relocated, np.asarray(moved), moved_slots, long_slot_revision,
        adjacent_cutout_revision, target_windows,
    )


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
    adjacent_center = np.asarray(expected_adjacent_cutout["target_center_mm"])
    adjacent_size = np.asarray(expected_adjacent_cutout["size_mm"])
    nearest = None
    for center in holes:
        gap_x = (
            abs(center[0] - adjacent_center[0])
            - (OPENING_WIDTH + adjacent_size[0]) / 2
        )
        gap_y = (
            abs(center[1] - adjacent_center[1])
            - (OPENING_WIDTH + adjacent_size[1]) / 2
        )
        if gap_x >= 0 and gap_y <= 0:
            if nearest is None or gap_x < nearest[0]:
                edge_x = (
                    adjacent_center[0] + adjacent_size[0] / 2
                    if center[0] > adjacent_center[0]
                    else adjacent_center[0] - adjacent_size[0] / 2
                )
                hole_edge_x = center[0] - np.sign(
                    center[0] - adjacent_center[0]
                ) * OPENING_WIDTH / 2
                y = np.clip(
                    adjacent_center[1],
                    center[1] - OPENING_WIDTH / 2,
                    center[1] + OPENING_WIDTH / 2,
                )
                nearest = (
                    float(gap_x), [(edge_x + hole_edge_x) / 2, y]
                )
    require(nearest is not None, "Adjacent cutout has no measured cube web")
    web_centers.append(nearest[1])
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
        "inset_probe_mm": 4.2,
        "edge_probe_offset_mm": 4.34,
        "separating_web_probe_count": len(web_centers),
        "separating_web_probe_volume_mm3": web_volumes,
    }


def verify_cube_grid(mesh, expected_slots, expected_rows, expected_long_slot,
                     expected_adjacent_cutout):
    holes, opening_sizes = square_opening_data(
        mesh, float(mesh.bounds[:, 2].mean())
    )
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
    adjacent_center, adjacent_size = adjacent_cutout(mesh, 0.2)
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
                24.0 < size[0] < 24.5
                and 15.3 < size[1] < 15.9
                and center[0] < -80.0
            )
            is_resource_window = (
                35.0 < size[0] < 100.0 and 20.0 < size[1] < 60.0
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
    source_z = (
        float(source.bounds[0, 2])
        + (0.2 - float(revised.bounds[0, 2]))
        / float(revised.extents[2]) * float(source.extents[2])
    )
    before = np.asarray(descriptors(source, SOURCE_MOUNTS, source_z))
    after = np.asarray(descriptors(revised, revised_mounts, 0.2))
    require(before.shape == after.shape, "Unrelated cutout count changed")
    require(np.allclose(before, after, atol=TOL, rtol=0),
            "An unrelated cutout moved or changed size")
    return {
        "unchanged": True,
        "unrelated_cutout_count": len(before),
    }


def verify_export(entries, original_entries, expected_slots, expected_rows,
                  expected_long_slot, expected_adjacent_cutout,
                  expected_windows):
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
    for z in (0.0, 0.2):
        actual_windows = resource_window_loops(front, z)
        for actual, expected in zip(actual_windows, expected_windows):
            require(
                np.allclose(actual[0], expected["center_mm"],
                            atol=TOL, rtol=0)
                and np.allclose(actual[1], expected["size_mm"],
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
    _, _, source_front = as_mesh(
        original_entries[FRONT_PATHS[0]], MESH_IDS[FRONT_PATHS[0]]
    )
    unrelated_cutouts = verify_unrelated_cutouts_unchanged(
        source_front, front
    )
    return (
        checks, mount_results, pin_results, insertion, clearance,
        cube_measurements, pitch_report, unrelated_cutouts, window_checks,
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
            (mesh, moved_holes, moved_slots, revised_long_slot,
             revised_adjacent_cutout, revised_windows) = relocate_cube_openings(
                mesh, tracks, row_plans
            )
            if not cube_slots:
                cube_slots = moved_slots
            else:
                require(moved_slots == cube_slots,
                        "Front copies have different cube end slots")
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
            transformations[path] = {
                "cube_tracks": anchors,
                "cube_row_registration": row_plans,
                "cube_track_end_slots": moved_slots,
                "horizontal_slot": revised_long_slot,
                "adjacent_cutout": revised_adjacent_cutout,
                "resource_windows": revised_windows,
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
        "Metadata/project_settings.config",
        "Metadata/model_settings.config",
        PRINT_METADATA_ENTRY,
    }
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
     window_checks) = verify_export(
        revised, original, cube_slots, cube_rows, long_slot_revision,
        adjacent_cutout_revision, window_revision,
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
        previous_front, 0.0, LONG_SLOT_HEIGHT
    )
    require(
        np.allclose(
            previous_slot_size,
            long_slot_revision["target_size_mm"],
            atol=TOL,
            rtol=0,
        ),
        "Follow-up unexpectedly changed the slider slot length",
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
        revised["3D/3dmodel.model"] == original["3D/3dmodel.model"],
        "3MF plate/build transforms changed",
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
            "Machine and global process settings",
            "Bed temperatures and calibrated flow",
            "Native filament start/end/change routines",
            "Bridge/overhang cooling behavior",
        ],
    }
    transparent_guide_review = {
        "reference": (
            "https://www.printables.com/model/15310-how-to-print-glass?lang=de"
        ),
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
        },
        "settings_changed_after_review": [],
        "not_adopted": [
            "Simplify3D-specific outline/solid underspeed percentages; no successful slice to verify effective speed",
            "PETG temperature, 0.50 mm width, 1.01 extrusion multiplier, and drying recipe not validated for this PLA profile",
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
                "source": (
                    "Six orange marked regions, mapped with a single "
                    "paper-centered transform"
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
                "red_outline_bounds_px": list(
                    FOLLOWUP_SLIDER_MARK_BOUNDS_PX
                ),
                "red_outline_center_px": list(
                    FOLLOWUP_SLIDER_MARK_CENTER_PX
                ),
                "red_outline_size_mm": FOLLOWUP_SLIDER_SIZE_MM.tolist(),
                "target_center_mm": FOLLOWUP_SLIDER_CENTER_MM.tolist(),
                "translation_mm": (
                    FOLLOWUP_SLIDER_CENTER_MM
                    - previous_slot_center
                ).tolist(),
                "slot_size_mm": long_slot_revision["target_size_mm"],
                "collision_clearance_mm": (
                    layout_clearances["minimum_slider_to_cube_clearance_mm"]
                ),
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
                "Six resource windows",
                "The middle two cube tracks and their rows",
                "Panel envelope, laminate registration, mounts and Z stack",
                "All unrelated filament slots and printer/process settings",
            ],
        },
        "mesh_checks": mesh_checks,
        "plate_layout": {
            "source_build_item_count": len(source_build_items),
            "output_build_item_count": len(revised_build_items),
            "build_items_and_transforms_unchanged": True,
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
            "status": "not-run-for-centered-blocks-artifact",
            "gcode_files_produced": 0,
            "support_enabled": project_settings.get("enable_support") == "1",
            "prior_attempts_artifact": str(
                PREVIOUS_OUTPUT.relative_to(ROOT)
            ).replace("\\", "/"),
            "prior_attempts_status": "failed; no G-code produced",
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
