"""Transfer the physically selected coupon diameters to the 179 mm project."""

import hashlib
import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / "model-sources" / "terraforming-mars-tableau"
SOURCE = INPUTS / "terraforming-mars-tableau-179mm.3mf"
COUPONS = INPUTS / "terraforming-mars-tableau-fit-samples.3mf"
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"m": CORE, "p": PROD}
SCALE = 179 / 172
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("BambuStudio", "http://schemas.bambulab.com/package/2021")
OUTPUT = ROOT / "models" / "terraforming-mars-tableau-179mm-loch1-zapfen3.3mf"
REPORT = ROOT / "docs" / "terraforming-mars-tableau-179mm-fit-validation.json"
SOURCE_SHA256 = "fb017fdd8bc1ef03faac8a431af10b39c6d1fc842391db4fb9cf50e121e43c3d"
COUPONS_SHA256 = "f2cd5082b5705df9b6b88963f716be752641be23a481abd9d7f663cfed2d23ef"
HOLE_DIAMETER = 3.0
PIN_DIAMETER = 2.6
CENTERS = np.asarray([
    (0, -83.1), (0, 83.1),
    (-112.6, -83.1), (-112.6, 0), (-112.6, 83.1),
    (112.6, -83.1), (112.6, 0), (112.6, 83.1),
]) * SCALE
FRONT_PATHS = (
    "3D/Objects/Body1_1.model",
    "3D/Objects/Vorderseite - PLA Transparent (Startprofil)_3.model",
)
REAR_PATH = "3D/Objects/Body1_2.model"
MESH_IDS = dict(zip((*FRONT_PATHS, REAR_PATH), ("1", "5", "3")))
SOCKET_BOTTOM = -1.5 * SCALE
SOCKET_FLOOR = 1.0 * SCALE
PIN_BASE = -0.2 * SCALE
PIN_SHOULDER = 0.9 * SCALE
PIN_TIP = 2.2 * SCALE
TOL = 2e-5


def require(condition, message):
    if not condition:
        raise ValueError(message)


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
    require(mesh.is_watertight, f"Object {object_id} is not watertight")
    require(mesh.is_winding_consistent, f"Object {object_id} winding is inconsistent")
    return root, node, mesh


def transform_vertices(vertices, transform):
    matrix = np.asarray(transform[:9], dtype=float).reshape((3, 3))
    translation = np.asarray(transform[9:12], dtype=float)
    return vertices @ matrix + translation


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ring_measure(mesh, center, z):
    vertices = mesh.vertices
    radius = np.linalg.norm(vertices[:, :2] - center, axis=1)
    points = vertices[(abs(vertices[:, 2] - z) < TOL) & (radius < 2 * SCALE)]
    require(len(points) >= 24, f"Missing circular ring at {center}, Z={z}")
    low, high = points[:, :2].min(axis=0), points[:, :2].max(axis=0)
    midpoint = (low + high) / 2
    return {
        "center_mm": midpoint.tolist(),
        "xy_diameters_mm": (high - low).tolist(),
        "z_mm": float(z),
    }


def check_mesh(mesh):
    require(mesh.is_watertight, "Mesh is not watertight")
    require(mesh.is_winding_consistent, "Inconsistent winding")
    require(mesh.volume > 0, "Nonpositive mesh volume")
    require(np.min(mesh.area_faces) > 1e-10, "Degenerate triangles")
    require(len(mesh.split(only_watertight=False)) == 1, "Disconnected panel")


def verify_coupons():
    require(sha256(COUPONS) == COUPONS_SHA256, "Unexpected coupon archive")
    with zipfile.ZipFile(COUPONS) as archive:
        _, _, hole = as_mesh(archive.read("3D/Objects/FitSample_9.model"), "9")
        _, _, pin = as_mesh(archive.read("3D/Objects/FitSample_15.model"), "15")
    measurements = []
    for role, mesh, diameter, z in (
        ("one-notch socket", hole, HOLE_DIAMETER, 1.5),
        ("three-notch pin", pin, PIN_DIAMETER, 3.0),
    ):
        section = mesh.section(plane_normal=[0, 0, 1], plane_origin=[0, 0, z])
        require(section is not None, f"Missing {role} section")
        for x in (-10, 10):
            loops = [
                loop for loop in section.discrete
                if abs((loop[:, 0].min() + loop[:, 0].max()) / 2 - x) < TOL
                and np.ptp(loop[:, :2], axis=0).max() < 5
            ]
            require(len(loops) == 1, f"Ambiguous {role} cross section")
            measured = np.ptp(loops[0][:, :2], axis=0)
            require(np.allclose(measured, diameter, atol=TOL, rtol=0),
                    f"Unexpected {role} diameter: {measured}")
            measurements.append({"role": role, "x_mm": x,
                                 "xy_diameters_mm": measured.tolist()})
    return measurements


def adjust_mesh(model_bytes, object_id, role):
    root, mesh_node, before = as_mesh(model_bytes, object_id)
    vertices = before.vertices.copy()
    touched = np.zeros(len(vertices), dtype=bool)
    changes = []
    for center in CENTERS:
        radial = np.linalg.norm(before.vertices[:, :2] - center, axis=1)
        if role == "socket":
            mask = (
                (abs(radial - 1.5 * SCALE) < TOL)
                & (before.vertices[:, 2] <= SOCKET_FLOOR + TOL)
            )
            diameter = HOLE_DIAMETER
            ring_z = SOCKET_FLOOR
        else:
            mask = (
                (radial < 1.6 * SCALE)
                & (before.vertices[:, 2] >= PIN_BASE - TOL)
            )
            diameter = PIN_DIAMETER
            ring_z = PIN_BASE
        require(mask.sum() >= 48, f"Incomplete {role} feature at {center}")
        require(not np.any(touched & mask), "Overlapping feature masks")
        measured = ring_measure(before, center, ring_z)
        old_diameter = float(np.mean(measured["xy_diameters_mm"]))
        expected = (3.0,) if role == "socket" else (2.6, 2.8)
        require(any(abs(old_diameter - value * SCALE) < TOL for value in expected),
                f"Unexpected source diameter {old_diameter}")
        # A radial-only feature transform preserves the original faces, axial
        # profile, blind floor, pin tip height and all unrelated vertices.
        vertices[mask, :2] = (
            center + (vertices[mask, :2] - center) * diameter / old_diameter
        )
        touched |= mask
        changes.append({"source": measured, "target_diameter_mm": diameter,
                        "changed_vertices": int(mask.sum())})

    after = trimesh.Trimesh(vertices=vertices, faces=before.faces, process=False)
    check_mesh(after)
    require(np.array_equal(before.faces, after.faces), "Mesh connectivity changed")
    require(np.array_equal(before.vertices[~touched], after.vertices[~touched]),
            "Unrelated vertices changed")
    require(np.array_equal(before.vertices[:, 2], after.vertices[:, 2]),
            "Axial dimensions changed")
    require(np.array_equal(before.bounds, after.bounds), "Panel envelope changed")
    require(before.euler_number == after.euler_number, "Topology changed")
    xml_vertices = mesh_node.findall("./m:vertices/m:vertex", NS)
    # as_mesh processes vertex indices; export its corresponding full mesh.
    require(len(xml_vertices) == len(after.vertices), "Unexpected merged vertices")
    for node in list(mesh_node):
        mesh_node.remove(node)
    core = NS["m"]
    v_parent = ET.SubElement(mesh_node, f"{{{core}}}vertices")
    for vertex in after.vertices:
        ET.SubElement(v_parent, f"{{{core}}}vertex",
                      dict(zip(("x", "y", "z"), (f"{v:.12g}" for v in vertex))))
    f_parent = ET.SubElement(mesh_node, f"{{{core}}}triangles")
    for face in after.faces:
        ET.SubElement(f_parent, f"{{{core}}}triangle",
                      dict(zip(("v1", "v2", "v3"), map(str, face))))
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), changes


def intersection_volume(mesh, probe):
    result = trimesh.boolean.intersection([mesh, probe], engine="manifold")
    return 0.0 if result.is_empty else abs(float(result.volume))


def probe_at(center, z, size):
    probe = trimesh.creation.box(extents=size)
    probe.apply_translation([*center, z])
    return probe


def verify_export(source_entries, output_entries):
    results = []
    exported = {}
    for path in MESH_IDS:
        _, _, before = as_mesh(source_entries[path], MESH_IDS[path])
        _, _, mesh = as_mesh(output_entries[path], MESH_IDS[path])
        check_mesh(mesh)
        require(np.allclose(mesh.bounds, before.bounds, atol=1e-9, rtol=0),
                "Exported bounds differ")
        require(mesh.euler_number == before.euler_number, "Exported topology differs")
        exported[path] = mesh
        socket = path in FRONT_PATHS
        feature_results = []
        for center in CENTERS:
            feature = {}
            for z in ((SOCKET_BOTTOM, 0.0, SOCKET_FLOOR) if socket
                      else (PIN_BASE, 0.0, PIN_SHOULDER)):
                section = mesh.section(plane_normal=[0, 0, 1],
                                       plane_origin=[0, 0, z + 1e-6])
                require(section is not None, "Missing exported section")
                loops = [
                    loop for loop in section.discrete
                    if np.linalg.norm(
                        (loop[:, :2].max(axis=0) + loop[:, :2].min(axis=0)) / 2
                        - center
                    ) < TOL and np.ptp(loop[:, :2], axis=0).max() < 4
                ]
                if socket and z == SOCKET_FLOOR:
                    ring = ring_measure(mesh, center, z)
                    measured = np.asarray(ring["xy_diameters_mm"])
                else:
                    require(len(loops) == 1, f"Missing fitting at {center}, Z={z}")
                    measured = np.ptp(loops[0][:, :2], axis=0)
                target = HOLE_DIAMETER if socket else PIN_DIAMETER
                require(np.allclose(measured, target, atol=TOL, rtol=0),
                        f"Incorrect exported diameter: {measured}")
                feature[f"diameters_at_z_{z:.6f}_mm"] = measured.tolist()
            ring = ring_measure(mesh, center, SOCKET_FLOOR if socket else PIN_BASE)
            require(np.allclose(ring["center_mm"], center, atol=TOL, rtol=0),
                    "Fitting center moved")
            feature["center_mm"] = ring["center_mm"]
            if socket:
                floor = probe_at(center, SOCKET_FLOOR + 0.1, [1.0, 1.0, 0.1])
                require(abs(intersection_volume(mesh, floor) - 0.1) < 1e-6,
                        "Blind floor missing")
                bore = probe_at(center, (SOCKET_BOTTOM + SOCKET_FLOOR) / 2,
                                [1.0, 1.0, SOCKET_FLOOR - SOCKET_BOTTOM - 0.01])
                require(intersection_volume(mesh, bore) < 1e-7, "Bore obstructed")
                feature["depth_mm"] = SOCKET_FLOOR - SOCKET_BOTTOM
                feature["floor_thickness_mm"] = 1.5 * SCALE - SOCKET_FLOOR
            feature_results.append(feature)
        results.append({"mesh_path": path, "features": feature_results,
                        "euler_number": int(mesh.euler_number),
                        "vertices": len(mesh.vertices), "triangles": len(mesh.faces),
                        "bounds_mm": mesh.bounds.tolist()})

    front, rear = exported[FRONT_PATHS[0]], exported[REAR_PATH]
    duplicate = exported[FRONT_PATHS[1]]
    require(np.array_equal(front.vertices, duplicate.vertices)
            and np.array_equal(front.faces, duplicate.faces),
            "Front copies differ")
    final_translation = PIN_BASE - SOCKET_BOTTOM
    clearance = SOCKET_FLOOR + final_translation - PIN_TIP
    require(clearance >= 0.1, f"Unsafe axial reserve: {clearance}")
    collision_results = []
    for separation in np.linspace(PIN_TIP - PIN_BASE + 0.1, 0, 9):
        moved = front.copy()
        moved.apply_translation([0, 0, final_translation + separation])
        volume = intersection_volume(rear, moved)
        require(volume < 0.001, f"Insertion collision: {volume} mm3")
        collision_results.append({"separation_mm": float(separation),
                                  "intersection_mm3": volume})
    return results, collision_results, clearance


def main():
    require(sha256(SOURCE) == SOURCE_SHA256, "Unexpected 179 mm source archive")
    coupons = verify_coupons()
    with zipfile.ZipFile(SOURCE) as archive:
        infos = archive.infolist()
        original = {info.filename: archive.read(info.filename) for info in infos}
    revised = dict(original)
    changes = {}
    for path, object_id in MESH_IDS.items():
        revised[path], changes[path] = adjust_mesh(
            original[path], object_id, "socket" if path in FRONT_PATHS else "pin"
        )
    with zipfile.ZipFile(OUTPUT, "w") as archive:
        for info in infos:
            archive.writestr(info, revised[info.filename])
    with zipfile.ZipFile(OUTPUT) as archive:
        require(archive.testzip() is None, "3MF CRC check failed")
        require(archive.namelist() == list(original), "3MF members changed")
        revised = {name: archive.read(name) for name in archive.namelist()}
    for name in original.keys() - MESH_IDS.keys():
        require(original[name] == revised[name], f"Unrelated entry changed: {name}")
    for name, data in revised.items():
        if name.endswith((".model", ".config", ".xml", ".rels")):
            if data.lstrip().startswith(b"{"):
                json.loads(data)
            else:
                ET.fromstring(data)
    objects, insertion, clearance = verify_export(original, revised)
    require(sha256(SOURCE) == SOURCE_SHA256, "Source archive was modified")
    require(sha256(COUPONS) == COUPONS_SHA256, "Coupon archive was modified")
    report = {
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "source_sha256": SOURCE_SHA256,
        "coupons_sha256": COUPONS_SHA256,
        "output": str(OUTPUT.relative_to(ROOT)).replace("\\", "/"),
        "output_sha256": sha256(OUTPUT),
        "selected_pair": {"hole_marks": 1, "pin_marks": 3,
                          "hole_diameter_mm": HOLE_DIAMETER,
                          "pin_diameter_mm": PIN_DIAMETER,
                          "diametral_clearance_mm": HOLE_DIAMETER - PIN_DIAMETER},
        "coupon_mesh_measurements": coupons,
        "scale_policy": "Panels remain scaled 179/172; selected physical fit diameters are NOT scaled again.",
        "short_side_mm": 179.0,
        "socket_depth_mm": SOCKET_FLOOR - SOCKET_BOTTOM,
        "socket_floor_mm": 0.5 * SCALE,
        "pin_projection_mm": PIN_TIP - PIN_BASE,
        "axial_clearance_mm": clearance,
        "changed_archive_members": list(MESH_IDS),
        "print_settings_preserved_byte_for_byte": True,
        "plate_component_build_and_assembly_transforms_preserved_byte_for_byte": True,
        "changes": changes,
        "exported_mesh_checks": objects,
        "insertion_sweep": insertion,
        "checks": [
            "All 16 sockets and eight pins measured on reparsed exported meshes",
            "All 16 blind floors and bore cavities verified with solid volume probes",
            "All three meshes watertight, consistently wound, single-component, no degenerate faces",
            "Mesh topology, all Z coordinates and all non-fitting vertices unchanged",
            "Both front copies identical; all eight pin/socket centers preserved",
            "Nine-step full-panel axial insertion sweep: no unintended interference",
            "Three plates, build/component transforms, materials and all settings byte-identical",
            "ZIP CRC, member list and all XML/JSON entries parse successfully",
            "Archived prior 179mm project and coupon archive preserved",
        ],
        "physical_fit": "Selected coupons physically tested by user; full tableau fit NOT verified. All three hole coupons have the same CAD diameter; reported hole-fit differences are not CAD size steps.",
        "slice_status": (
            "OrcaSlicer CLI attempted with unchanged saved settings; exit -18: "
            "retraction_distances_when_cut: 0 not in range [10.000000,18.000000]. "
            "No G-code produced. No successful slice, print-time, support or material claim."
        ),
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output_sha256": report["output_sha256"],
                      "hole_mm": HOLE_DIAMETER, "pin_mm": PIN_DIAMETER,
                      "axial_clearance_mm": clearance,
                      "checks": report["checks"]}, indent=2))


if __name__ == "__main__":
    main()
