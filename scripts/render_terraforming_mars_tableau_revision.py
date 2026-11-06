"""Render the final three-plate Tableau revision."""

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import vedo

from fit_terraforming_mars_tableau import (
    NS, PROD, ROOT, as_mesh, transform_vertices,
)

OUTPUT = (
    ROOT / "models"
    / "terraforming-mars-tableau-179mm-laminate-centered-blocks.3mf"
)
PREVIEW = ROOT / "docs" / "images" / f"{OUTPUT.stem}-preview.png"


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
    print(PREVIEW)


if __name__ == "__main__":
    main()
