import json
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import revise_terraforming_mars_tableau as revision


class TableauRevisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(revision.SOURCE) as archive:
            cls.source = {
                name: archive.read(name) for name in archive.namelist()
            }
        with zipfile.ZipFile(revision.OUTPUT) as archive:
            cls.output = {
                name: archive.read(name) for name in archive.namelist()
            }
            cls.crc_error = archive.testzip()
        with zipfile.ZipFile(revision.PREVIOUS_OUTPUT) as archive:
            cls.previous = {
                name: archive.read(name) for name in archive.namelist()
            }
            cls.previous_crc_error = archive.testzip()
        cls.report = json.loads(revision.REPORT.read_text(encoding="utf-8"))

    def test_archive_changes_only_the_three_panel_meshes(self):
        self.assertIsNone(self.crc_error)
        self.assertEqual(
            list(self.output),
            list(self.source) + [revision.PRINT_METADATA_ENTRY],
        )
        changed = {
            name for name in self.output
            if name not in self.source
            or self.source.get(name) != self.output[name]
        }
        self.assertEqual(
            changed,
            set(revision.MESH_IDS) | {
                "Metadata/project_settings.config",
                "Metadata/model_settings.config",
                revision.PRINT_METADATA_ENTRY,
            },
        )
        self.assertIsNone(self.previous_crc_error)
        self.assertTrue(
            self.report["filament_scope_checks_passed"]
        )

    def test_transparent_filament_settings_are_isolated_to_slot_four(self):
        source_settings = json.loads(
            self.source["Metadata/project_settings.config"]
        )
        settings = json.loads(self.output["Metadata/project_settings.config"])
        slot = revision.TRANSPARENT_FILAMENT_SLOT - 1
        self.assertEqual(revision.TRANSPARENT_FILAMENT_SLOT, 4)
        self.assertEqual(len(settings["filament_settings_id"]), 4)
        for key, value in source_settings.items():
            if (
                key != "printable_area"
                and isinstance(value, list)
                and len(value) == 4
            ):
                self.assertEqual(settings[key][:3], value[:3], key)
            elif key == "different_settings_to_system":
                self.assertEqual(settings[key][:5], value[:5])
            else:
                self.assertEqual(settings[key], value, key)
        self.assertEqual(
            settings["filament_settings_id"][slot],
            revision.TRANSPARENT_FILAMENT_PROFILE,
        )
        self.assertEqual(settings["nozzle_temperature"][slot], "220")
        self.assertEqual(
            settings["nozzle_temperature_initial_layer"][slot], "220"
        )
        self.assertLessEqual(
            float(settings["nozzle_temperature_range_low"][slot]), 220
        )
        self.assertGreaterEqual(
            float(settings["nozzle_temperature_range_high"][slot]), 220
        )
        self.assertEqual(settings["fan_min_speed"][slot], "20")
        self.assertEqual(settings["fan_max_speed"][slot], "20")
        self.assertEqual(
            settings["additional_cooling_fan_speed"][slot], "0"
        )
        self.assertEqual(settings["filament_flow_ratio"][slot], "0.98")

        model = ET.fromstring(self.output["Metadata/model_settings.config"])
        objects = {
            item.get("id"): item for item in model.findall("object")
        }
        self.assertEqual(
            {
                item.get("key"): item.get("value")
                for item in objects["6"].findall("metadata")
            }["extruder"],
            "4",
        )
        transparent = {
            item.get("key"): item.get("value")
            for item in objects["6"].findall("metadata")
        }
        for key in (
            "layer_height", "outer_wall_speed", "inner_wall_speed",
            "solid_infill_speed", "internal_solid_infill_speed",
            "sparse_infill_speed", "gap_infill_speed", "top_surface_speed",
        ):
            self.assertEqual(transparent[key], "0.1" if key == "layer_height" else "20")
        self.assertEqual(transparent["wall_loops"], "2")
        self.assertEqual(transparent["top_shell_layers"], "0")
        self.assertEqual(transparent["bottom_shell_layers"], "0")
        self.assertEqual(transparent["sparse_infill_density"], "100%")
        for key in (
            "sparse_infill_pattern", "internal_solid_infill_pattern",
            "top_surface_pattern", "bottom_surface_pattern",
        ):
            self.assertEqual(transparent[key], "alignedrectilinear")
        self.assertEqual(transparent["infill_direction"], "0")
        self.assertEqual(transparent["solid_infill_direction"], "0")
        self.assertEqual(transparent["sparse_infill_rotate_template"], "0")
        self.assertEqual(transparent["solid_infill_rotate_template"], "0")

    def test_print_metadata_marks_unsliced_totals_unknown(self):
        root = ET.fromstring(self.output[revision.PRINT_METADATA_ENTRY])
        values = {
            item.get("name"): item.get("value")
            for item in root.findall("metadata")
        }
        self.assertEqual(values["status"], "not-verified")
        self.assertEqual(values["plateCount"], "3")
        for key in (
            "estimatedPrintTimeSeconds",
            "filamentUsageGrams",
            "filamentUsageMillimeters",
            "filamentUsageCubicMillimeters",
            "supportFilamentGrams",
            "supportFilamentMillimeters",
            "supportFilamentCubicMillimeters",
        ):
            self.assertEqual(values[key], "unknown")
        self.assertIn("enable_support=0", values["supportPolicy"])
        self.assertEqual(values["seamPosition"], "random")
        self.assertEqual(values["ironingType"], "top")

    def test_exported_envelope_mounts_and_cube_registration(self):
        self.assertAlmostEqual(
            self.report["requested_revision"]["long_dimension_after_mm"],
            revision.NEW_LENGTH,
            places=6,
        )
        self.assertEqual(
            self.report["requested_revision"]["short_dimension_mm"],
            revision.SHORT_SIDE,
        )
        self.assertEqual(
            self.report["requested_revision"]["front_thickness_mm"],
            revision.FRONT_THICKNESS,
        )
        for path, object_id in revision.MESH_IDS.items():
            with self.subTest(path=path):
                _, _, mesh = revision.as_mesh(self.output[path], object_id)
                self.assertTrue(mesh.is_watertight)
                self.assertAlmostEqual(
                    mesh.extents[0], revision.NEW_LENGTH, delta=1e-5
                )
                self.assertAlmostEqual(mesh.extents[1], revision.SHORT_SIDE,
                                       places=5)
                if path in revision.FRONT_PATHS:
                    self.assertAlmostEqual(mesh.extents[2],
                                           revision.FRONT_THICKNESS, places=6)

        sockets = self.report["fit"]["sockets"]
        pins = self.report["fit"]["pins"]
        self.assertEqual(len(sockets), 8)
        self.assertEqual(len(pins), 8)
        for mount in sockets:
            np.testing.assert_allclose(
                mount["socket_diameter_mm"], revision.SOCKET_DIAMETER,
                atol=revision.TOL, rtol=0,
            )
            self.assertEqual(mount["blind_floor_mm"], revision.SOCKET_FLOOR)
        for pin in pins:
            np.testing.assert_allclose(
                pin["shaft_diameter_mm"], revision.PIN_DIAMETER,
                atol=revision.TOL, rtol=0,
            )

        grid = self.report["cube_grid"]
        laminate = self.report["laminate_registration"]
        self.assertEqual(laminate["outer_size_mm"], [227.0, 168.0])
        self.assertEqual(
            laminate["frame_margin_each_side_mm"],
            [revision.FRAME_MARGIN_X, revision.FRAME_MARGIN_Y],
        )
        self.assertGreater(
            laminate["socket_clearances_to_laminate_edges_mm"]["short_side_mm"],
            0.9,
        )
        self.assertGreater(
            laminate["socket_clearances_to_laminate_edges_mm"]["long_side_mm"],
            1.1,
        )
        self.assertEqual(grid["pitch_and_web"]["opening_count"], 65)
        self.assertEqual(
            grid["pitch_and_web"]["opening_probe_checks"]["openings"], 65
        )
        self.assertEqual(
            grid["unrelated_cutouts"]["unrelated_cutout_count"], 0
        )
        windows = grid["resource_windows"]
        self.assertEqual(len(windows["targets"]), 6)
        self.assertEqual(len(windows["exported_section_checks"]), 12)
        self.assertEqual(
            windows["photo_calibration"]["pixels_per_mm"],
            revision.PHOTO_PX_PER_MM,
        )
        self.assertGreaterEqual(
            grid["layout_clearances"]["minimum_window_to_window_web_mm"],
            0.8,
        )
        self.assertGreaterEqual(
            grid["layout_clearances"]["minimum_window_to_cube_clearance_mm"],
            0.8,
        )
        slider = grid["pitch_and_web"]["horizontal_slot"]
        np.testing.assert_allclose(
            slider["target_center_mm"], revision.FOLLOWUP_SLIDER_CENTER_MM,
            atol=revision.TOL, rtol=0,
        )
        self.assertGreaterEqual(
            grid["pitch_and_web"]["slider_clearance"]["minimum_clearance_mm"],
            revision.MIN_SLOT_CLEARANCE,
        )
        self.assertAlmostEqual(
            grid["adjacent_cutout"]["translation_mm"][0], -3.95
        )
        row_registration = grid["pitch_and_web"]["row_registration"]
        self.assertEqual(len(row_registration), 13)
        self.assertLessEqual(
            grid["pitch_and_web"]["max_cell_center_error_mm"], 1.646
        )
        self.assertTrue(all(
            abs(row["max_abs_actual_center_error_mm"]
                - row["max_abs_center_error_mm"]) < revision.TOL
            for row in row_registration
        ))
        self.assertLessEqual(
            max(abs(row["vertical_center_error_mm"])
                for row in row_registration), 0.661
        )
        anchors = grid["anchors"]
        self.assertEqual(len(anchors), len(revision.ROW_ANCHORS))
        for anchor, datum in zip(anchors, revision.ROW_ANCHORS):
            self.assertAlmostEqual(
                anchor["target_center_x_mm"],
                revision.PAPER_LEFT + datum["offset_x"]
                + revision.CUBE_EDGE / 2
                + (revision.LOWER_RIGHT_TRACK_SHIFT_X_MM
                   if datum["name"] == "lower-right zero" else 0.0)
                + revision.NUMBER_BLOCK_SHIFTS_X_MM.get(
                    datum["name"], 0.0
                ),
            )
            self.assertAlmostEqual(
                anchor["target_center_y_mm"],
                anchor["top_row_center_y_mm"],
                delta=revision.TOL,
            )
            self.assertLessEqual(abs(anchor["y_error_mm"]), revision.TOL)
            row = next(
                item for item in row_registration
                if item["track"] == datum["name"]
                and item["row_index_from_anchor"] == 0
            )
            expected_print_center_y = (
                revision.PAPER_TOP - datum["top_distance"]
                - revision.CUBE_EDGE / 2
            )
            self.assertAlmostEqual(
                row["print_field_center_y_mm"],
                expected_print_center_y,
                places=6,
            )
            self.assertAlmostEqual(
                row["target_y_mm"],
                expected_print_center_y + row["vertical_center_error_mm"],
                places=6,
            )

    def test_only_requested_number_blocks_move_from_previous(self):
        _, _, before = revision.as_mesh(
            self.previous[revision.FRONT_PATHS[0]],
            revision.MESH_IDS[revision.FRONT_PATHS[0]],
        )
        _, _, after = revision.as_mesh(
            self.output[revision.FRONT_PATHS[0]],
            revision.MESH_IDS[revision.FRONT_PATHS[0]],
        )
        before_tracks = revision.track_groups(revision.square_holes(before, 0.2))
        after_tracks = revision.track_groups(revision.square_holes(after, 0.2))
        self.assertEqual(len(before_tracks), 6)
        self.assertEqual(len(after_tracks), 6)
        expected_translations = {
            0: -1.0,
            1: 0.0,
            2: 0.0,
            3: -1.5,
            4: 0.0,
            5: 0.5,
        }
        for track_index, (before_track, after_track) in enumerate(
            zip(before_tracks, after_tracks)
        ):
            before_rows = sorted(np.unique(np.round(before_track[:, 1], 6)))
            after_rows = sorted(np.unique(np.round(after_track[:, 1], 6)))
            np.testing.assert_allclose(before_rows, after_rows, atol=1e-6)
            expected_dx = expected_translations[track_index]
            for y in before_rows:
                before_row = before_track[
                    np.abs(before_track[:, 1] - y) < 0.02
                ]
                after_row = after_track[
                    np.abs(after_track[:, 1] - y) < 0.02
                ]
                before_row = before_row[np.argsort(before_row[:, 0])]
                after_row = after_row[np.argsort(after_row[:, 0])]
                self.assertEqual(len(before_row), len(after_row))
                np.testing.assert_allclose(
                    after_row - before_row,
                    np.tile([expected_dx, 0.0], (len(before_row), 1)),
                    atol=revision.TOL,
                    rtol=0,
                )

        self.assertEqual(
            self.output[revision.REAR_PATH],
            self.previous[revision.REAR_PATH],
        )
        self.assertEqual(
            self.output["Metadata/project_settings.config"],
            self.previous["Metadata/project_settings.config"],
        )
        self.assertEqual(
            self.output["Metadata/model_settings.config"],
            self.previous["Metadata/model_settings.config"],
        )

        before_windows = revision.resource_window_loops(before, 0.0)
        after_windows = revision.resource_window_loops(after, 0.0)
        for old_window, new_window in zip(before_windows, after_windows):
            np.testing.assert_allclose(old_window[0], new_window[0],
                                       atol=revision.TOL, rtol=0)
            np.testing.assert_allclose(old_window[1], new_window[1],
                                       atol=revision.TOL, rtol=0)

        before_slider = revision.long_horizontal_slot(before, 0.0, 6.8)
        after_slider = revision.long_horizontal_slot(after, 0.0, 6.8)
        np.testing.assert_allclose(
            after_slider[0], revision.FOLLOWUP_SLIDER_CENTER_MM,
            atol=revision.TOL, rtol=0,
        )
        np.testing.assert_allclose(after_slider[1], before_slider[1],
                                   atol=revision.TOL, rtol=0)
        self.assertGreaterEqual(
            self.report["cube_grid"]["layout_clearances"][
                "minimum_slider_to_cube_clearance_mm"
            ],
            revision.MIN_SLOT_CLEARANCE,
        )
        block_checks = self.report["followup_adjustments"][
            "number_block_centering"
        ]["blocks"]
        self.assertEqual(len(block_checks), 3)
        self.assertEqual(
            [item["translation_x_mm"] for item in block_checks],
            [-1.5, -1.0, 0.5],
        )
        self.assertFalse(
            self.report["transparent_guide_review"][
                "effective_gcode_speeds_verified"
            ]
        )
        for item in block_checks:
            self.assertLessEqual(
                abs(item["after_centroid_error_mm"]), 1.0
            )
            self.assertLessEqual(
                item["max_abs_field_error_to_unshifted_anchor_mm"], 3.2
            )
        all_tracks = self.report["cube_grid"][
            "all_six_track_alignment"
        ]["tracks"]
        self.assertEqual(len(all_tracks), 6)
        self.assertEqual(
            [
                item["number_block_translation_from_previous_mm"]
                for item in all_tracks
            ],
            [-1.0, 0.0, 0.0, -1.5, 0.0, 0.5],
        )
        self.assertTrue(all(item["field_count"] > 0 for item in all_tracks))


if __name__ == "__main__":
    unittest.main()
