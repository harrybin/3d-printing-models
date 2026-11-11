import copy
import hashlib
import json
import math
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.parsers import expat

import numpy as np
import trimesh
from shapely.geometry import box

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "models" / "terraforming-mars-tableau-print.3mf"
OUTPUT = ROOT / "models" / "terraforming-mars-tableau-fit-samples.3mf"
CORE = "http://schemas.microsoft.com/3dmanufacturing/core/2015/02"
PROD = "http://schemas.microsoft.com/3dmanufacturing/production/2015/06"
BAMBU = "http://schemas.bambulab.com/package/2021"
NS = {"m": CORE}
IDENTITY = "1 0 0 0 1 0 0 0 1"
RELATIONSHIP_TYPE = "http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"
ET.register_namespace("", CORE)
ET.register_namespace("p", PROD)
ET.register_namespace("BambuStudio", BAMBU)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def mesh_check(mesh):
    require(mesh.is_watertight, "Mesh is not watertight")
    require(mesh.is_winding_consistent, "Inconsistent winding")
    require(mesh.volume > 0, "Nonpositive volume")
    require(len(mesh.split(only_watertight=False)) == 1, "Disconnected coupon")
    require(np.min(mesh.area_faces) > 1e-10, "Degenerate triangles")


def outer_polygon(marks):
    outline = box(-15, -2.9, 15, 2.9)
    for i in range(marks):
        x = (i - (marks - 1) / 2) * 1.8
        outline = outline.difference(box(x - 0.4, 2.4, x + 0.4, 3.2))
    return outline


def lathe(profile, center):
    mesh = trimesh.creation.revolve(np.asarray(profile), sections=128)
    mesh.apply_translation([center, 0, 0])
    return mesh


def make_back(diameter, marks):
    radius = diameter / 2
    fillet = 0.5
    profile = [[0, 1.9], [radius + fillet, 1.9]]
    for angle in np.linspace(0, math.pi / 2, 25):
        profile.append(
            [
                radius + fillet - fillet * math.sin(angle),
                2 + fillet - fillet * math.cos(angle),
            ]
        )
    profile.extend([[radius, 3.8], [radius - 0.3, 4.1], [0, 4.1], [0, 1.9]])
    base = trimesh.creation.extrude_polygon(
        outer_polygon(marks), 2, engine="earcut"
    )
    result = trimesh.boolean.union(
        [base, lathe(profile, -10), lathe(profile, 10)], engine="manifold"
    )
    mesh_check(result)
    return result


def make_front(marks):
    # Socket entrance is printed against the bed, matching the source front.
    cutter_profile = [
        [0, -0.1],
        [2, -0.1],
        [2, 0],
        [1.5, 0.5],
        [1.5, 2.5],
        [0, 2.5],
        [0, -0.1],
    ]
    base = trimesh.creation.extrude_polygon(
        outer_polygon(marks), 3, engine="earcut"
    )
    result = trimesh.boolean.difference(
        [base, lathe(cutter_profile, -10), lathe(cutter_profile, 10)],
        engine="manifold",
    )
    mesh_check(result)
    return result


def metadata(parent, key, value):
    element = parent.find(f"./metadata[@key='{key}']")
    if element is None:
        element = ET.SubElement(parent, "metadata", {"key": key})
    element.set("value", str(value))


def serialize(root):
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def mesh_xml(mesh, object_id, sequence):
    root = ET.Element(
        f"{{{CORE}}}model",
        {
            "unit": "millimeter",
            "{http://www.w3.org/XML/1998/namespace}lang": "en-US",
            "requiredextensions": "p",
            "xmlns:BambuStudio": BAMBU,
        },
    )
    ET.SubElement(root, f"{{{CORE}}}metadata", {"name": "BambuStudio:3mfVersion"}).text = "1"
    resources = ET.SubElement(root, f"{{{CORE}}}resources")
    obj = ET.SubElement(
        resources,
        f"{{{CORE}}}object",
        {
            "id": str(object_id),
            "type": "model",
            f"{{{PROD}}}UUID": f"{sequence:08x}-61cb-4c03-9d28-80fed5dfa1dc",
        },
    )
    mesh_node = ET.SubElement(obj, f"{{{CORE}}}mesh")
    vertices = ET.SubElement(mesh_node, f"{{{CORE}}}vertices")
    for vertex in mesh.vertices:
        ET.SubElement(
            vertices,
            f"{{{CORE}}}vertex",
            {key: f"{value:.9g}" for key, value in zip(("x", "y", "z"), vertex)},
        )
    triangles = ET.SubElement(mesh_node, f"{{{CORE}}}triangles")
    for face in mesh.faces:
        ET.SubElement(
            triangles,
            f"{{{CORE}}}triangle",
            {key: str(value) for key, value in zip(("v1", "v2", "v3"), face)},
        )
    return serialize(root)


source_bytes = SOURCE.read_bytes()
with zipfile.ZipFile(SOURCE) as archive:
    original = {name: archive.read(name) for name in archive.namelist()}
data = dict(original)
model = ET.fromstring(data["3D/3dmodel.model"])
config = ET.fromstring(data["Metadata/model_settings.config"])
settings = json.loads(data["Metadata/project_settings.config"])
original_config = ET.fromstring(original["Metadata/model_settings.config"])
front_template = config.find("./object[@id='6']")
back_template = config.find("./object[@id='4']")
front_slot = int(front_template.find("./metadata[@key='extruder']").get("value"))
back_slot = int(back_template.find("./metadata[@key='extruder']").get("value"))
require(front_slot == 1 and back_slot == 3, "Unexpected material mapping")
resources = model.find("m:resources", NS)
build = model.find("m:build", NS)
old_resource_text = data["3D/3dmodel.model"].decode("utf-8")
require(len(config.findall("plate")) == 3, "Expected three source plates")
plate = ET.Element("plate")
for key, value in (
    ("plater_id", "4"),
    ("plater_name", "Fit samples 2.4 - 2.5 - 2.6 mm"),
    ("locked", "false"),
    ("filament_map_mode", "Auto For Flush"),
    ("filament_maps", "1 1 1 1"),
    ("print_sequence", "by object"),
):
    metadata(plate, key, value)
config.insert(list(config).index(config.find("assemble")), plate)
assembly = config.find("assemble")
relationship_text = data["3D/_rels/3dmodel.model.rels"].decode("utf-8")
report = []

for row, diameter in enumerate((2.4, 2.5, 2.6), start=1):
    back = make_back(diameter, row)
    front = make_front(row)
    moved_front = front.copy()
    moved_front.apply_translation([0, 0, 2])
    collision = trimesh.boolean.intersection([back, moved_front], engine="manifold")
    # Coplanar mating faces may remain in an intersection of touching solids.
    triangles = collision.triangles
    intersection_volume = abs(
        np.einsum(
            "ij,ij->i",
            triangles[:, 0],
            np.cross(triangles[:, 1], triangles[:, 2]),
        ).sum() / 6
    )
    require(intersection_volume < 1e-7, "Assembled pin/socket collision")
    for center in (-10, 10):
        shaft_section = back.section(
            plane_normal=[0, 0, 1], plane_origin=[0, 0, 3]
        )
        shaft_loops = [
            loop
            for loop in shaft_section.discrete
            if abs(np.mean(loop[:, 0]) - center) < 0.1
        ]
        require(len(shaft_loops) == 1, "Missing pin shaft")
        require(
            abs(np.ptp(shaft_loops[0], axis=0)[0] - diameter) < 1e-5,
            "Wrong shaft diameter",
        )
    require(abs(front.bounds[1, 2] - 3) < 1e-6, "Wrong front height")
    require(abs(back.bounds[1, 2] - 4.1) < 1e-6, "Wrong pin height")
    require(abs((3 - 0.5) - (4.1 - 2) - 0.4) < 1e-6, "Wrong depth reserve")
    front.apply_transform(np.array([
        [1, 0, 0, 0],
        [0, -1, 0, 0],
        [0, 0, -1, 3],
        [0, 0, 0, 1],
    ]))
    mesh_check(front)
    for role, mesh, template, x in (
        ("Back", back, back_template, 175),
        ("Front", front, front_template, 65),
    ):
        mesh_id = 7 + len(report) * 2
        object_id = mesh_id + 1
        sequence = 4 + len(report)
        notch_label = "notch" if row == 1 else "notches"
        name = f"Fit sample {diameter:.1f} mm - {role} - {row} {notch_label}"
        target = f"3D/Objects/FitSample_{mesh_id}.model"
        data[target] = mesh_xml(mesh, mesh_id, sequence)
        obj = ET.SubElement(
            resources,
            f"{{{CORE}}}object",
            {
                "id": str(object_id),
                "type": "model",
                f"{{{PROD}}}UUID": f"{sequence:08x}-61cb-4c03-9d28-80fed5dfa1dc",
            },
        )
        components = ET.SubElement(obj, f"{{{CORE}}}components")
        ET.SubElement(
            components,
            f"{{{CORE}}}component",
            {
                f"{{{PROD}}}path": "/" + target,
                "objectid": str(mesh_id),
                f"{{{PROD}}}UUID": f"{sequence:04x}0000-b206-40ff-9872-83e8017abed1",
                "transform": IDENTITY + " 0 0 0",
            },
        )
        # Four plates retain a two-column layout; plate 4 is bottom-right.
        local_y = 50 + (row - 1) * 70
        transform = f"{IDENTITY} {x + 314.4:.9g} {local_y - 314.4:.9g} 0"
        ET.SubElement(
            build,
            f"{{{CORE}}}item",
            {
                "objectid": str(object_id),
                f"{{{PROD}}}UUID": f"{object_id:08x}-b1ec-4553-aec9-835e5b724bb4",
                "transform": transform,
                "printable": "1",
            },
        )
        object_settings = ET.Element("object", {"id": str(object_id)})
        for item in template.findall("metadata"):
            object_settings.append(copy.deepcopy(item))
        metadata(object_settings, "name", name)
        metadata(object_settings, "layer_height", "0.2")
        part = ET.SubElement(
            object_settings, "part", {"id": str(mesh_id), "subtype": "normal_part"}
        )
        metadata(part, "name", name)
        metadata(part, "matrix", "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1")
        metadata(part, "source_file", OUTPUT.name)
        metadata(part, "source_object_id", len(report))
        metadata(part, "source_volume_id", "0")
        ET.SubElement(
            part,
            "mesh_stat",
            {key: "0" for key in (
                "edges_fixed", "degenerate_facets", "facets_removed",
                "facets_reversed", "backwards_edges"
            )},
        )
        config.insert(list(config).index(config.find("plate")), object_settings)
        instance = ET.SubElement(plate, "model_instance")
        metadata(instance, "object_id", object_id)
        metadata(instance, "instance_id", "0")
        metadata(instance, "identify_id", 201 + len(report))
        ET.SubElement(
            assembly,
            "assemble_item",
            {
                "object_id": str(object_id),
                "instance_id": "0",
                "transform": transform,
                "offset": "0 0 0",
            },
        )
        relationship_text = relationship_text.replace(
            "</Relationships>",
            f' <Relationship Target="/{target}" Id="rel-{sequence}" '
            f'Type="{RELATIONSHIP_TYPE}"/>\n</Relationships>',
        )
        report.append({
            "name": name,
            "object_id": object_id,
            "mesh": target,
            "vertices": len(mesh.vertices),
            "triangles": len(mesh.faces),
            "volume_mm3": float(mesh.volume),
            "filament_slot": int(
                object_settings.find("./metadata[@key='extruder']").get("value")
            ),
        })

# Print clear fronts first, then all backs, to avoid dark residue in clear PLA.
sample_ids = [
    str(sample["object_id"])
    for sample in sorted(report, key=lambda sample: (
        sample["filament_slot"], sample["object_id"]
    ))
]
for parent, tag, attr in (
    (resources, f"{{{CORE}}}object", "id"),
    (build, f"{{{CORE}}}item", "objectid"),
    (config, "object", "id"),
    (assembly, "assemble_item", "object_id"),
):
    ordered = [
        next(node for node in parent.findall(tag) if node.get(attr) == object_id)
        for object_id in sample_ids
    ]
    for node in ordered:
        parent.remove(node)
    insertion = (
        list(parent).index(parent.find("plate")) if parent is config else len(parent)
    )
    for offset, node in enumerate(ordered):
        parent.insert(insertion + offset, node)
instances = list(plate.findall("model_instance"))
for node in instances:
    plate.remove(node)
for object_id in sample_ids:
    plate.append(next(
        node for node in instances
        if node.find("./metadata[@key='object_id']").get("value") == object_id
    ))

# The slicer forbids a prime tower with sequential multi-material printing.
# Every original plate contains just one single-material object.
settings["enable_prime_tower"] = "0"

# Preserve original XML byte formatting and namespace declarations. Only append
# new resources/items; do not reserialize the original known-good model document.
new_objects = list(resources)[3:]
new_build_items = list(build)[3:]
new_resources_xml = "".join(ET.tostring(o, encoding="unicode") for o in new_objects)
new_items_xml = "".join(ET.tostring(o, encoding="unicode") for o in new_build_items)
data["3D/3dmodel.model"] = old_resource_text.replace(
    "</resources>", new_resources_xml + "</resources>"
).replace("</build>", new_items_xml + "</build>").encode("utf-8")
data["3D/_rels/3dmodel.model.rels"] = relationship_text.encode("utf-8")
data["Metadata/model_settings.config"] = serialize(config)
for key in ("wipe_tower_x", "wipe_tower_y"):
    require(len(settings[key]) == 3, "Expected three wipe-tower entries")
    settings[key].append(settings[key][-1])
data["Metadata/project_settings.config"] = json.dumps(
    settings, ensure_ascii=False, indent=2
).encode("utf-8")

with zipfile.ZipFile(OUTPUT, "w", zipfile.ZIP_DEFLATED) as archive:
    for name, value in data.items():
        archive.writestr(name, value)
with zipfile.ZipFile(OUTPUT) as archive:
    require(archive.testzip() is None, "ZIP CRC failed")
    for name in original:
        if name not in (
            "3D/3dmodel.model",
            "3D/_rels/3dmodel.model.rels",
            "Metadata/model_settings.config",
            "Metadata/project_settings.config",
        ):
            require(archive.read(name) == original[name], f"Original changed: {name}")
    new_config = ET.fromstring(archive.read("Metadata/model_settings.config"))
    new_model = ET.fromstring(archive.read("3D/3dmodel.model"))
    require(len(new_config.findall("plate")) == 4, "Expected four plates")
    require(len(new_model.findall("m:build/m:item", NS)) == 9, "Expected nine objects")
    require(
        new_config.findall("plate")[3].find(
            "./metadata[@key='print_sequence']"
        ).get("value") == "by object",
        "Plate 4 must use sequential printing",
    )
    ordered_samples = [
        next(sample for sample in report if str(sample["object_id"]) == item.get("objectid"))
        for item in new_model.findall("m:build/m:item", NS)[3:]
    ]
    materials = [sample["filament_slot"] for sample in ordered_samples]
    require(materials == [1, 1, 1, 3, 3, 3], "Material sequence must have one change")
    sample_settings = [
        new_config.find(f"./object[@id='{sample['object_id']}']")
        for sample in report
    ]
    require(
        all(
            obj.find("./metadata[@key='layer_height']").get("value") == "0.2"
            for obj in sample_settings
        ),
        "Prime tower requires matching layer heights on plate 4",
    )
    for old in original_config.findall("object"):
        new = new_config.find(f"./object[@id='{old.get('id')}']")
        require(ET.tostring(old) == ET.tostring(new), "Original object settings changed")
    for i, old in enumerate(original_config.findall("plate")):
        require(
            ET.tostring(old) == ET.tostring(new_config.findall("plate")[i]),
            "Original plate configuration changed",
        )
    previous_settings = json.loads(original["Metadata/project_settings.config"])
    new_settings = json.loads(archive.read("Metadata/project_settings.config"))
    for key, value in previous_settings.items():
        actual = new_settings[key]
        if key == "enable_prime_tower":
            require(actual == "0", "Prime tower must be disabled")
            continue
        if key in ("wipe_tower_x", "wipe_tower_y"):
            actual = actual[:3]
        require(actual == value, f"User print setting changed: {key}")
    targets = []
    parser = expat.ParserCreate()
    parser.StartElementHandler = lambda name, attrs: (
        targets.append(attrs["Target"].lstrip("/"))
        if name == "Relationship" and attrs.get("Type") == RELATIONSHIP_TYPE
        else None
    )
    parser.Parse(archive.read("3D/_rels/3dmodel.model.rels"), True)
    require(len(targets) == 9, "Slicer cannot discover all nine meshes")
    sample_bounds = []
    for target in targets:
        root = ET.fromstring(archive.read(target))
        vertices = np.array([
            [float(v.get(axis)) for axis in ("x", "y", "z")]
            for v in root.findall(".//m:vertex", NS)
        ])
        triangles = np.array([
            [int(t.get(axis)) for axis in ("v1", "v2", "v3")]
            for t in root.findall(".//m:triangle", NS)
        ])
        require(len(vertices) > 0 and len(triangles) > 0, "Missing mesh")
        mesh = trimesh.Trimesh(vertices, triangles, process=True)
        mesh_check(mesh)
        if target.startswith("3D/Objects/FitSample_"):
            sample = next(item for item in report if item["mesh"] == target)
            item = new_model.find(
                f"m:build/m:item[@objectid='{sample['object_id']}']", NS
            )
            transform = np.array([float(v) for v in item.get("transform").split()])
            world = vertices @ transform[:9].reshape(3, 3) + transform[9:]
            local = world - np.array([314.4, -314.4, 0])
            require(
                np.all(local.min(axis=0) >= -1e-5)
                and np.all(local.max(axis=0)[:2] <= 250),
                "Sample outside plate",
            )
            require(
                local.max(axis=0)[2] < float(settings["extruder_clearance_height_to_rod"]),
                "Sample exceeds gantry height clearance",
            )
            sample_bounds.append((local.min(axis=0)[:2], local.max(axis=0)[:2]))
            if "Front" in sample["name"]:
                for z, diameter in ((2.999, 3.998), (2.75, 3.5), (2.0, 3.0), (0.501, 3.0)):
                    section = mesh.section(
                        plane_normal=[0, 0, 1], plane_origin=[0, 0, z]
                    )
                    holes = [
                        loop for loop in section.discrete
                        if np.ptp(loop[:, 0]) < 5
                    ]
                    require(len(holes) == 2, "Expected two upward-facing sockets")
                    require(
                        all(abs(np.ptp(loop[:, 0]) - diameter) < 2e-5 for loop in holes),
                        "Socket cross-section differs from specification",
                    )
                require(
                    len(mesh.section(
                        plane_normal=[0, 0, 1], plane_origin=[0, 0, 0.499]
                    ).discrete) == 1,
                    "Blind socket must retain a 0.5-mm closed bottom",
                )
    for index, (lower, upper) in enumerate(sample_bounds):
        for other_lower, other_upper in sample_bounds[index + 1:]:
            delta = np.maximum(0, np.maximum(lower - other_upper, other_lower - upper))
            require(
                np.linalg.norm(delta) > float(settings["extruder_clearance_radius"]),
                "Insufficient horizontal clearance between sequential objects",
            )
    for item in new_model.findall("m:build/m:item", NS)[:3]:
        old_model = ET.fromstring(original["3D/3dmodel.model"])
        old = old_model.find(
            f"m:build/m:item[@objectid='{item.get('objectid')}']", NS
        )
        require(item.attrib == old.attrib, "Original build transform changed")
require(SOURCE.read_bytes() == source_bytes, "User source file changed")
manifest = {
    "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
    "output_sha256": hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
    "new_plate": 4,
    "samples": report,
    "dimensions_mm": {
        "coupon_length": 30,
        "coupon_width": 5.8,
        "back_base_thickness": 2,
        "front_thickness": 3,
        "pin_spacing": 20,
        "pin_projection": 2.1,
        "tip_chamfer_axial_and_radial": 0.3,
        "root_fillet_radius": 0.5,
        "socket_diameter": 3,
        "socket_depth": 2.5,
        "socket_entrance_diameter": 4,
        "socket_entrance_depth": 0.5,
        "axial_clearance": 0.4,
    },
    "checks": [
        "All six coupons watertight, consistently wound and single-component",
        "All six samples use 0.2-mm layers for prime-tower compatibility",
        "Front coupons rotated 180 degrees, openings facing up; exported hole cross-sections checked",
        "Shaft diameters measured from generated mesh cross-sections",
        "Each assembled pair has zero interference volume",
        "All nine mesh references discovered by slicer-style Expat callback",
        "Reparsed exported meshes pass watertight/volume checks",
        "Original meshes, three plates, object overrides and material presets unchanged",
        "User settings preserved except extending plate arrays and disabling prime tower (incompatible with sequential multi-material printing)",
        "Plate 4 uses by-object printing, clear fronts first, then backs: one material transition",
        "Horizontal gaps exceed configured 60-mm clearance; all objects below 40-mm gantry clearance",
        "No physical fit test or slicer toolpath validation performed",
    ],
}
(
    ROOT / "docs" / "terraforming-mars-tableau-fit-validation.json"
).write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(OUTPUT)
print(json.dumps(manifest, ensure_ascii=False, indent=2))
