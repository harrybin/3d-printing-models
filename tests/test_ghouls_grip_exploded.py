"""Presentation transforms must cover every source part without editing meshes."""

import importlib.util
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "exploded", ROOT / "scripts" / "render_ghouls_grip_exploded.py")
exploded = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(exploded)


class ExplodedDrawingTests(unittest.TestCase):
    def test_empty_camera_render_cannot_be_delivered(self):
        from PIL import Image
        with self.assertRaisesRegex(ValueError, "Empty Blender render"):
            exploded.validate_render(Image.new("RGBA", (20, 20)))

    def test_every_delivered_part_has_one_presentation_group(self):
        with ZipFile(exploded.SOURCE) as archive:
            root = ET.fromstring(archive.read("3D/3dmodel.model"))
        names = [
            node.get("name").removeprefix("deployed-")
            for node in root.findall(".//{*}resources/{*}object")
            if node.get("name", "").startswith("deployed-")
        ]
        self.assertEqual(len(names), 42)
        self.assertEqual({exploded.layout(name)[0] for name in names},
                         set(range(1, 9)))
        for name in names:
            self.assertEqual(len(exploded.layout(name)[1]), 3)

    def test_unknown_part_is_not_silently_omitted(self):
        with self.assertRaisesRegex(ValueError, "Unmapped"):
            exploded.layout("new-unclassified-part")

    def test_explosion_keeps_base_fixed_and_separates_hand_parts(self):
        self.assertEqual(exploded.layout("chest"), (1, (0, 0, 0)))
        offsets = {
            exploded.layout("hand-finger-" + name)[1]
            for name in ("thumb", "index", "middle", "ring", "little")
        }
        self.assertEqual(len(offsets), 5)
        self.assertGreater(exploded.layout("lid")[1][0], 100)
        self.assertGreater(exploded.layout("platform")[1][2],
                           exploded.layout("slider")[1][2])


if __name__ == "__main__":
    unittest.main()
