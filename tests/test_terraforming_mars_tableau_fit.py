import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fit_terraforming_mars_tableau as fit


class TableauFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(fit.SOURCE) as archive:
            cls.source = {name: archive.read(name) for name in archive.namelist()}
        with zipfile.ZipFile(fit.OUTPUT) as archive:
            cls.output = {name: archive.read(name) for name in archive.namelist()}
            cls.crc_error = archive.testzip()

    def test_selected_physical_coupon_dimensions(self):
        measurements = fit.verify_coupons()
        self.assertEqual(len(measurements), 4)
        self.assertEqual(fit.HOLE_DIAMETER, 3.0)
        self.assertEqual(fit.PIN_DIAMETER, 2.6)

    def test_sources_preserved(self):
        self.assertEqual(fit.sha256(fit.SOURCE), fit.SOURCE_SHA256)
        self.assertEqual(fit.sha256(fit.COUPONS), fit.COUPONS_SHA256)

    def test_only_three_mesh_entries_changed_and_all_settings_are_preserved(self):
        self.assertIsNone(self.crc_error)
        self.assertEqual(list(self.source), list(self.output))
        changed = {name for name in self.source
                   if self.source[name] != self.output[name]}
        self.assertEqual(changed, set(fit.MESH_IDS))
        self.assertEqual(
            self.source["Metadata/project_settings.config"],
            self.output["Metadata/project_settings.config"],
        )
        self.assertEqual(
            self.source["Metadata/model_settings.config"],
            self.output["Metadata/model_settings.config"],
        )
        settings = ET.fromstring(self.output["Metadata/model_settings.config"])
        self.assertEqual(
            [
                node.get("value")
                for node in settings.findall(".//metadata[@key='layer_height']")
            ],
            ["0.2"],
        )
        root = ET.fromstring(self.output["3D/3dmodel.model"])
        self.assertEqual(len(root.findall("./m:build/m:item", fit.NS)), 3)

    def test_unrelated_geometry_and_all_axial_dimensions_unchanged(self):
        for path, object_id in fit.MESH_IDS.items():
            with self.subTest(path=path):
                _, _, before = fit.as_mesh(self.source[path], object_id)
                _, _, after = fit.as_mesh(self.output[path], object_id)
                np.testing.assert_array_equal(before.faces, after.faces)
                np.testing.assert_allclose(before.vertices[:, 2], after.vertices[:, 2],
                                           atol=1e-10, rtol=0)
                np.testing.assert_array_equal(before.bounds, after.bounds)
                self.assertAlmostEqual(after.extents[1], 179.0, places=7)
                self.assertEqual(before.euler_number, after.euler_number)
                frozen = np.ones(len(before.vertices), dtype=bool)
                for center in fit.CENTERS:
                    radial = np.linalg.norm(before.vertices[:, :2] - center, axis=1)
                    if path in fit.FRONT_PATHS:
                        editable = ((abs(radial - 1.5 * fit.SCALE) < fit.TOL)
                                    & (before.vertices[:, 2] <= fit.SOCKET_FLOOR + fit.TOL))
                    else:
                        editable = ((radial < 1.6 * fit.SCALE)
                                    & (before.vertices[:, 2] >= fit.PIN_BASE - fit.TOL))
                    frozen &= ~editable
                np.testing.assert_array_equal(before.vertices[frozen], after.vertices[frozen])

    def test_exported_dimensions_floors_and_full_panel_insertion(self):
        objects, insertion, clearance = fit.verify_export(self.source, self.output)
        self.assertEqual(sum(len(obj["features"]) for obj in objects), 24)
        self.assertEqual(len(insertion), 9)
        self.assertTrue(all(step["intersection_mm3"] < 0.001 for step in insertion))
        self.assertAlmostEqual(clearance, 0.1 * fit.SCALE, places=8)


if __name__ == "__main__":
    unittest.main()
