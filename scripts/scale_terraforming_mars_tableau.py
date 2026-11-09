import hashlib
import json
import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "terraforming-mars-tableau-print.3mf"
OUTPUT = ROOT / "models" / "terraforming-mars-tableau-179mm.3mf"
REPORT = ROOT / "docs" / "terraforming-mars-tableau-179mm-validation.json"
EXPECTED_SOURCE_SHA256 = (
    "179e1cb51043f6b4dd99c27d6f166f95c03a223e313050b709b1c9c1aa0cfc84"
)
SCALE = 179 / 172
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
NS = {"m": CORE, "p": PROD}
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("BambuStudio", "http://schemas.bambulab.com/package/2021")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def transform_vertices(vertices, transform):
    matrix = np.asarray(transform[:9], dtype=float).reshape((3, 3))
    translation = np.asarray(transform[9:12], dtype=float)
    return vertices @ matrix + translation


def as_mesh(model_bytes, object_id):
    root = ET.fromstring(model_bytes)
    obj = root.find(f"./m:resources/m:object[@id='{object_id}']", NS)
    require(obj is not None, f"Missing mesh object {object_id}")
    mesh_node = obj.find("m:mesh", NS)
    require(mesh_node is not None, f"Object {object_id} has no mesh")
    vertices = np.asarray(
        [
            [float(vertex.get(axis)) for axis in ("x", "y", "z")]
            for vertex in mesh_node.findall("./m:vertices/m:vertex", NS)
        ],
        dtype=float,
    )
    faces = np.asarray(
        [
            [int(face.get(axis)) for axis in ("v1", "v2", "v3")]
            for face in mesh_node.findall("./m:triangles/m:triangle", NS)
        ],
        dtype=np.int64,
    )
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=True)
    require(mesh.is_watertight, f"Object {object_id} is not watertight")
    require(mesh.is_winding_consistent, f"Object {object_id} winding is inconsistent")
    return root, mesh_node, mesh


def scale_external_model(model_bytes):
    root = ET.fromstring(model_bytes)
    objects = root.findall("./m:resources/m:object", NS)
    require(len(objects) == 1, "Expected one mesh object per external model")
    mesh = objects[0].find("m:mesh", NS)
    require(mesh is not None, "External model has no mesh")
    vertices = mesh.findall("./m:vertices/m:vertex", NS)
    require(bool(vertices), "External model has no vertices")
    for vertex in vertices:
        for axis in ("x", "y", "z"):
            vertex.set(axis, f"{float(vertex.get(axis)) * SCALE:.9g}")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def bounds(vertices):
    return np.min(vertices, axis=0), np.max(vertices, axis=0)


def main():
    source_bytes = SOURCE.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    require(source_hash == EXPECTED_SOURCE_SHA256, "Unexpected source project hash")
    with zipfile.ZipFile(SOURCE) as source:
        entries = {item.filename: (item, source.read(item.filename)) for item in source.infolist()}

    model_root = ET.fromstring(entries["3D/3dmodel.model"][1])
    model_objects = {
        obj.get("id"): obj for obj in model_root.findall("./m:resources/m:object", NS)
    }
    build_items = model_root.findall("./m:build/m:item", NS)
    require(len(build_items) == 3, "Expected exactly three source build objects")

    # Each source build item references an external mesh. Scale the front copy,
    # rear, and duplicate front independently while retaining their object IDs.
    plate_offsets = {
        "2": np.array([0.0, 0.0]),
        "4": np.array([314.4, 0.0]),
        "6": np.array([0.0, -314.4]),
    }
    object_results = []
    changed_entries = set()
    front_meshes = []
    for item in build_items:
        object_id = item.get("objectid")
        wrapper = model_objects[object_id]
        component = wrapper.find("./m:components/m:component", NS)
        require(component is not None, f"Build object {object_id} has no mesh component")
        path = component.get(f"{{{PROD}}}path", "").lstrip("/")
        component_id = component.get("objectid")
        require(path in entries, f"Missing external mesh {path}")
        if path not in changed_entries:
            entries[path] = (entries[path][0], scale_external_model(entries[path][1]))
            changed_entries.add(path)

        external_root, mesh_node, mesh = as_mesh(entries[path][1], component_id)
        if "Body1_2" not in path:
            front_meshes.append(mesh)

        component_transform = [
            float(value) for value in component.get("transform").split()
        ]
        build_transform = [float(value) for value in item.get("transform").split()]
        require(len(component_transform) == 12 and len(build_transform) == 12,
                "Unexpected 3MF transform shape")
        transformed = transform_vertices(mesh.vertices, component_transform)
        world_before_z_drop = transform_vertices(transformed, build_transform)
        old_min_z = float(world_before_z_drop[:, 2].min())
        build_transform[11] -= old_min_z
        item.set("transform", " ".join(f"{value:.12g}" for value in build_transform))
        world = transform_vertices(transformed, build_transform)
        low, high = bounds(world)
        plate_offset = plate_offsets[object_id]
        local_low = low[:2] - plate_offset
        local_high = high[:2] - plate_offset
        center = (local_low + local_high) / 2
        extents = high - low
        require(abs(center[0] - 125) < 0.01 and abs(center[1] - 125) < 0.01,
                f"Object {object_id} is not centered on its plate")
        require(np.all(local_low >= -1e-6) and np.all(local_high <= 250 + 1e-6),
                f"Object {object_id} is outside the 250 mm bed")
        require(abs(low[2]) < 1e-6, f"Object {object_id} does not rest on Z=0")
        object_results.append(
            {
                "build_object_id": object_id,
                "mesh_path": path,
                "mesh_object_id": component_id,
                "bounds_mm": [low.tolist(), high.tolist()],
                "plate_local_xy_bounds_mm": [
                    local_low.tolist(),
                    local_high.tolist(),
                ],
                "extents_mm": extents.tolist(),
                "plate_center_mm": center.tolist(),
            }
        )

    require(len(changed_entries) == 3, "Expected two front meshes and one rear mesh")
    require(len(front_meshes) == 2, "Expected original and duplicate front meshes")
    front_bounds = [mesh.bounds for mesh in front_meshes]
    require(
        np.allclose(front_bounds[0], front_bounds[1], atol=1e-7),
        "Front copies do not have matching scaled geometry",
    )

    # The source has eight small mounting bores. Keep all eight; each must
    # remain open at the bore and have solid material in its existing blind floor.
    centers = [
        (0.0, -83.07),
        (0.0, 83.07),
        (-112.6, -83.07),
        (-112.6, 0.0),
        (-112.6, 83.07),
        (112.6, -83.07),
        (112.6, 0.0),
        (112.6, 83.07),
    ]
    front_mesh = front_meshes[0]
    floor_z = 1.3 * SCALE
    bore_z = 0.5 * SCALE
    floor_volume = 0.4 * 0.4 * 0.1
    for x, y in centers:
        probe_xy = np.array([x, y]) * SCALE
        floor_probe = trimesh.creation.box(extents=[0.4, 0.4, 0.1])
        floor_probe.apply_translation([*probe_xy, floor_z])
        floor_intersection = trimesh.boolean.intersection(
            [front_mesh, floor_probe], engine="manifold"
        )
        require(
            abs(float(floor_intersection.volume) - floor_volume) < 1e-6,
            f"Mounting hole at {probe_xy.tolist()} lost its blind floor",
        )
        bore_probe = trimesh.creation.box(extents=[0.5, 0.5, 0.5])
        bore_probe.apply_translation([*probe_xy, bore_z])
        bore_intersection = trimesh.boolean.intersection(
            [front_mesh, bore_probe], engine="manifold"
        )
        bore_volume = (
            0.0 if bore_intersection.is_empty else float(bore_intersection.volume)
        )
        require(
            bore_volume < 1e-7,
            f"Mounting hole at {probe_xy.tolist()} is no longer open",
        )

    entries["3D/3dmodel.model"] = (
        entries["3D/3dmodel.model"][0],
        ET.tostring(model_root, encoding="utf-8", xml_declaration=True),
    )
    with zipfile.ZipFile(OUTPUT, "w") as archive:
        for name, (info, content) in entries.items():
            archive.writestr(info, content)

    with zipfile.ZipFile(SOURCE) as source, zipfile.ZipFile(OUTPUT) as output:
        require(output.testzip() is None, "Output 3MF CRC check failed")
        source_names = set(source.namelist())
        require(set(output.namelist()) == source_names, "3MF package members changed")
        for name in source_names - changed_entries - {"3D/3dmodel.model"}:
            require(source.read(name) == output.read(name), f"Unchanged entry differs: {name}")
        require(
            source.read("Metadata/project_settings.config")
            == output.read("Metadata/project_settings.config"),
            "Print settings changed",
        )
        require(
            source.read("Metadata/model_settings.config")
            == output.read("Metadata/model_settings.config"),
            "Per-object and plate settings changed",
        )

    report = {
        "source": "models/terraforming-mars-tableau-print.3mf",
        "source_sha256": source_hash,
        "output": "models/terraforming-mars-tableau-179mm.3mf",
        "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        "scale_factor": SCALE,
        "short_side_before_mm": 172.0,
        "short_side_after_mm": 172.0 * SCALE,
        "long_side_before_mm": 231.0,
        "long_side_after_mm": 231.0 * SCALE,
        "hole_result": "All eight original front mounting bores retain their blind floors; geometry uniformly scaled.",
        "print_settings_preserved": True,
        "objects": object_results,
        "verification": [
            "Source SHA-256 matches the approved user-saved baseline",
            "All three referenced meshes scaled uniformly by 179/172",
            "Both front mesh copies match after scaling",
            "Eight mounting-bore cavity and blind-floor volume probes pass",
            "All parts remain centered within their 250x250 mm plate and rest at Z=0",
            "All non-geometry 3MF entries, print settings and model settings are unchanged",
            "No slicer toolpath or physical fit test was performed",
        ],
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
