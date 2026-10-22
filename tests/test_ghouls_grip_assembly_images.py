"""Assembly illustrations must match the documented build order and source BOM."""

import importlib.util
import json
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
SPEC = importlib.util.spec_from_file_location(
    "assembly_images", ROOT / "scripts" / "render_ghouls_grip_assembly.py")
images = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(images)


class AssemblyImagesTests(unittest.TestCase):
    def test_every_printed_body_has_a_documented_introduction(self):
        with ZipFile(images.SOURCE) as archive:
            root = ET.fromstring(archive.read("3D/3dmodel.model"))
        names = {
            obj.get("name").removeprefix("deployed-")
            for obj in root.findall(".//{*}resources/{*}object")
            if obj.get("name", "").startswith("deployed-")
        }
        self.assertEqual(len(names), 42)
        self.assertEqual(set(images.PART_STEP), names)
        self.assertEqual(sum(step == 9 for step in images.PART_STEP.values()), 7)

    def test_upper_pins_are_not_seated_before_platform(self):
        for name, step in images.PART_STEP.items():
            if name.startswith(("pivot-pin-fixed-", "pivot-pin-slot-")):
                self.assertEqual(step, 8)
        self.assertLess(images.PART_STEP["scissor-drive-gear"], 8)

    def test_every_instruction_section_has_its_own_image(self):
        self.assertEqual({frame["step"] for frame in images.FRAMES},
                         set(range(2, 13)))
        self.assertEqual(len({frame["slug"] for frame in images.FRAMES}),
                         len(images.FRAMES))

    def test_frame_pose_matches_audited_insertion_state(self):
        poses = {frame["step"]: frame["pose"] for frame in images.FRAMES}
        self.assertEqual(poses[5], "retracted")
        self.assertEqual(poses[6], "intermediate")
        self.assertEqual(poses[8], "deployed")
        self.assertEqual(poses[11], "intermediate")

    def test_join_illustration_separates_whole_platform_not_only_pins(self):
        frame = next(f for f in images.FRAMES if f["step"] == 8)
        selected, focus = images.selection(frame)
        self.assertIn("platform", focus)
        self.assertIn("forearm", focus)
        self.assertIn("arm-0-False", selected)
        self.assertNotEqual(images.offset("platform", frame), (0, 0, 0))

    def test_lid_remains_fixed_while_crank_is_presented_separately(self):
        frame = next(f for f in images.FRAMES if f["step"] == 10)
        self.assertEqual(images.offset("lid", frame), (0, 0, 0))
        self.assertNotEqual(images.offset("lid-crank", frame), (0, 0, 0))

    def test_each_frame_is_embedded_in_guide_and_catalogued(self):
        guide = (ROOT / "docs" / "ghouls-grip-bauanleitung.md").read_text(encoding="utf-8")
        catalog = json.loads((ROOT / "catalog.json").read_text(encoding="utf-8"))
        docs = next(model["docs"] for model in catalog["models"]
                    if model["slug"] == "ghouls-grip")
        for frame in images.FRAMES:
            filename = f"ghouls-grip-montage-{frame['slug']}.png"
            self.assertIn(f"images/{filename}", guide)
            self.assertIn(f"docs/images/{filename}", docs)

    def test_all_focus_labels_point_to_a_rendered_body(self):
        for frame in images.FRAMES:
            selected, focus = images.selection(frame)
            self.assertTrue(focus <= selected)
            self.assertTrue(set(frame["labels"]) <= selected)
            self.assertTrue(set(frame["labels"]) <= set(images.LABELS))


if __name__ == "__main__":
    unittest.main()
