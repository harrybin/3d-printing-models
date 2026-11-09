import json
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import cv2
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
        required_changes = set(revision.MESH_IDS) | {
            "3D/3dmodel.model",
            "Metadata/project_settings.config",
            "Metadata/model_settings.config",
            revision.PRINT_METADATA_ENTRY,
        }
        expected_changes = required_changes | {
            path for path in revision.FRONT_PLATE_PREVIEWS
            if self.source[path] != self.output[path]
        }
        self.assertEqual(changed, expected_changes)
        for path in revision.FRONT_PLATE_PREVIEWS:
            source_image = cv2.imdecode(
                np.frombuffer(self.source[path], dtype=np.uint8),
                cv2.IMREAD_UNCHANGED,
            )
            output_image = cv2.imdecode(
                np.frombuffer(self.output[path], dtype=np.uint8),
                cv2.IMREAD_UNCHANGED,
            )
            np.testing.assert_array_equal(
                output_image, cv2.rotate(source_image, cv2.ROTATE_180)
            )
        self.assertIsNone(self.previous_crc_error)
        self.assertTrue(
            self.report["filament_scope_checks_passed"]
        )

    def test_only_front_panels_receive_an_in_place_z_rotation(self):
        source_scene = ET.fromstring(self.source["3D/3dmodel.model"])
        output_scene = ET.fromstring(self.output["3D/3dmodel.model"])

        def items_by_id(scene):
            return {
                item.get("objectid"): item
                for item in scene.findall("./m:build/m:item", revision.NS)
            }

        def item_mesh_path(scene, item):
            assembly = scene.find(
                f"./m:resources/m:object[@id='{item.get('objectid')}']",
                revision.NS,
            )
            component = assembly.find(
                "./m:components/m:component", revision.NS
            )
            return component.get(f"{{{revision.PROD}}}path").lstrip("/")

        source_items = items_by_id(source_scene)
        output_items = items_by_id(output_scene)
        self.assertEqual(list(source_items), list(output_items))
        target_ids = []
        expected_delta = np.diag([-1.0, -1.0, 1.0])
        for object_id, source_item in source_items.items():
            output_item = output_items[object_id]
            path = item_mesh_path(source_scene, source_item)
            if path in revision.FRONT_PATHS:
                target_ids.append(object_id)
                source_rotation, source_translation = (
                    revision.parse_3mf_transform(source_item.get("transform"))
                )
                output_rotation, output_translation = (
                    revision.parse_3mf_transform(output_item.get("transform"))
                )
                np.testing.assert_allclose(
                    output_rotation, expected_delta @ source_rotation,
                    atol=1e-10, rtol=0,
                )
                np.testing.assert_allclose(
                    output_translation, source_translation,
                    atol=revision.TOL, rtol=0,
                )
                self.assertAlmostEqual(
                    output_rotation[2, 2], 1.0, places=10
                )
            else:
                self.assertEqual(
                    output_item.get("transform"),
                    source_item.get("transform"),
                )
        self.assertEqual(target_ids, ["2", "6"])
        report = self.report["plate_layout"]
        self.assertTrue(report["build_item_ids_and_plate_order_preserved"])
        self.assertTrue(report["rear_part_transform_unchanged"])
        self.assertTrue(report["in_plane_rotation_preserves_bed_contact"])
        self.assertEqual(
            report["front_plate_preview_images_rotated"],
            list(revision.FRONT_PLATE_PREVIEWS),
        )
        self.assertEqual(
            [item["plate_index"] for item in report["front_part_rotations"]],
            [1, 3],
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
                if key in (
                    "cool_plate_temp",
                    "cool_plate_temp_initial_layer",
                ):
                    self.assertEqual(settings[key][slot], "55", key)
            elif key == "curr_bed_type":
                self.assertEqual(settings[key], value)
            elif key == "different_settings_to_system":
                expected = value[:]
                process_overrides = expected[0].split(";")
                for setting in (
                    "top_shell_layers",
                    "top_shell_thickness",
                    "infill_direction",
                    "solid_infill_direction",
                    "initial_layer_speed",
                ):
                    if setting not in process_overrides:
                        process_overrides.append(setting)
                expected[0] = ";".join(process_overrides)
                machine_overrides = list(
                    filter(None, expected[1].split(";"))
                )
                expected[1] = ";".join(machine_overrides)
                expected[revision.TRANSPARENT_FILAMENT_SLOT + 1] = (
                    "filament_settings_id;cool_plate_temp;"
                    "cool_plate_temp_initial_layer;nozzle_temperature;"
                    "nozzle_temperature_BRASS;"
                    "nozzle_temperature_initial_layer;"
                    "nozzle_temperature_initial_layer_BRASS;fan_min_speed;"
                    "fan_min_speed_BRASS;fan_min_speed_HS;fan_max_speed;"
                    "fan_max_speed_BRASS;fan_max_speed_HS;"
                    "fan_speed_after_x_layers;"
                    "additional_cooling_fan_speed"
                )
                self.assertEqual(settings[key], expected)
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
        self.assertEqual(settings["cool_plate_temp"][slot], "55")
        self.assertEqual(
            settings["cool_plate_temp_initial_layer"][slot], "55"
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
            "initial_layer_speed",
        ):
            self.assertEqual(transparent[key], "0.1" if key == "layer_height" else "20")
        self.assertEqual(transparent["wall_loops"], "2")
        self.assertEqual(transparent["top_shell_layers"], "2")
        self.assertEqual(transparent["top_shell_thickness"], "0.2")
        self.assertEqual(transparent["bottom_shell_layers"], "0")
        self.assertEqual(transparent["ironing_type"], "top")
        self.assertEqual(transparent["sparse_infill_density"], "100%")
        for key in (
            "sparse_infill_pattern", "internal_solid_infill_pattern",
            "top_surface_pattern", "bottom_surface_pattern",
        ):
            self.assertEqual(transparent[key], "alignedrectilinear")
        self.assertEqual(transparent["infill_direction"], "90")
        self.assertEqual(transparent["solid_infill_direction"], "90")
        self.assertEqual(transparent["sparse_infill_rotate_template"], "0")
        self.assertEqual(transparent["solid_infill_rotate_template"], "0")
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "bed_type"
            ],
            "Cool Plate",
        )
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "global_bed_type"
            ],
            source_settings["curr_bed_type"],
        )
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "cool_plate_temperature_c"
            ],
            "55",
        )
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "cool_plate_first_layer_temperature_c"
            ],
            "55",
        )
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "first_layer_speed_mm_s"
            ],
            "20",
        )
        self.assertEqual(
            self.report["requested_revision"]["transparent_filament_settings"][
                "first_layer_solid_infill_speed_mm_s"
            ],
            "60",
        )
        self.assertFalse(
            self.report["requested_revision"]["transparent_filament_settings"][
                "first_layer_solid_infill_applies"
            ]
        )

    def test_print_metadata_marks_unsliced_totals_unknown(self):
        root = ET.fromstring(self.output[revision.PRINT_METADATA_ENTRY])
        values = {
            item.get("name"): item.get("value")
            for item in root.findall("metadata")
        }
        self.assertEqual(values["status"], "not-verified")
        self.assertEqual(values["plateCount"], "3")
        self.assertEqual(
            values["bedType"],
            "Global: Textured PEI Plate; Plate 3: Cool Plate",
        )
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
        reliefs = grid["local_reliefs"]
        window = reliefs["small_window"]
        np.testing.assert_allclose(
            window["bounds_mm"],
            [[-100.176, 3.425], [-81.928, 17.035]],
            atol=0.001,
            rtol=0,
        )
        np.testing.assert_allclose(
            window["size_mm"], [18.248, 13.61],
            atol=0.001, rtol=0,
        )
        self.assertTrue(window["inner_area_solid"])
        web = reliefs["small_window_web"]
        self.assertAlmostEqual(
            web["rear_layer_thickness_mm"],
            revision.SMALL_WEB_THICKNESS_MM,
        )
        self.assertAlmostEqual(web["height_mm"], revision.OPENING_WIDTH)
        self.assertGreater(web["width_mm"], 1.0)
        self.assertLess(web["recessed_front_probe_volume_mm3"], 1e-7)
        arrows = reliefs["end_slots"]
        self.assertEqual(len(arrows), 6)
        self.assertTrue(reliefs["rear_face_flush_and_front_recess_passed"])
        self.assertTrue(reliefs["cube_fit_and_overrun_support_passed"])
        for arrow in arrows:
            self.assertAlmostEqual(
                arrow["back_layer_thickness_mm"], 1.0, places=6
            )
            self.assertAlmostEqual(
                arrow["front_recess_depth_mm"], 1.5, places=6
            )
            self.assertLess(arrow["cube_interference_volume_mm3"], 1e-6)
            self.assertGreater(arrow["overrun_cube_contact_area_mm2"], 0.0)
        windows = grid["resource_windows"]
        self.assertEqual(len(windows["targets"]), 6)
        self.assertEqual(len(windows["exported_section_checks"]), 12)
        targets = windows["targets"]
        self.assertAlmostEqual(
            targets[0]["size_mm"][0], revision.UPPER_LEFT_WINDOW_WIDTH_MM,
            places=5,
        )
        self.assertGreaterEqual(targets[3]["size_mm"][0], 69.0)
        self.assertGreaterEqual(
            targets[5]["size_mm"][0],
            revision.LOWER_RIGHT_WINDOW_MIN_WIDTH_MM,
        )
        for target in targets:
            self.assertAlmostEqual(
                target["size_mm"][1],
                revision.RESOURCE_WINDOW_HEIGHT_MM,
                places=5,
            )
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
        self.assertGreaterEqual(
            grid["layout_clearances"]["minimum_window_to_window_web_mm"],
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
        self.assertEqual(
            grid["adjacent_cutout"]["translation_after_prior_alignment_mm"],
            [2.0, 0.0],
        )
        self.assertEqual(grid["adjacent_cutout"]["left_trim_mm"], 6.0)
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
        after_back_z = float(after.bounds[0, 2]) + 0.05
        after_centers = np.asarray([
            center for center, size in revision.section_loops(
                after, after_back_z
            )
            if np.all((size > 8.5) & (size < 8.8))
        ])
        self.assertEqual(len(before_tracks), 6)
        self.assertEqual(len(after_centers), 65)
        expected_translations = {
            0: -1.0,
            1: 0.0,
            2: 0.0,
            3: -1.5,
            4: 0.0,
            5: 0.5,
        }
        for track_index, before_track in enumerate(before_tracks):
            before_rows = sorted(np.unique(np.round(before_track[:, 1], 6)))
            expected_dx = expected_translations[track_index]
            for y in before_rows:
                before_row = before_track[
                    np.abs(before_track[:, 1] - y) < 0.02
                ]
                before_row = before_row[np.argsort(before_row[:, 0])]
                expected_row = before_row + [expected_dx, 0.0]
                after_row = []
                for expected_center in expected_row:
                    distances = np.linalg.norm(
                        after_centers - expected_center, axis=1
                    )
                    match = int(np.argmin(distances))
                    self.assertLess(distances[match], revision.TOL)
                    after_row.append(after_centers[match])
                after_row = np.asarray(after_row)
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
        prior_project = json.loads(
            self.previous["Metadata/project_settings.config"]
        )
        output_project = json.loads(
            self.output["Metadata/project_settings.config"]
        )
        expected_overrides = prior_project["different_settings_to_system"][:]
        process_overrides = expected_overrides[0].split(";")
        for setting in (
            "top_shell_layers",
            "top_shell_thickness",
            "infill_direction",
            "solid_infill_direction",
            "initial_layer_speed",
        ):
            if setting not in process_overrides:
                process_overrides.append(setting)
        expected_overrides[0] = ";".join(process_overrides)
        expected_overrides[revision.TRANSPARENT_FILAMENT_SLOT + 1] = (
            "filament_settings_id;cool_plate_temp;"
            "cool_plate_temp_initial_layer;nozzle_temperature;"
            "nozzle_temperature_BRASS;nozzle_temperature_initial_layer;"
            "nozzle_temperature_initial_layer_BRASS;fan_min_speed;"
            "fan_min_speed_BRASS;fan_min_speed_HS;fan_max_speed;"
            "fan_max_speed_BRASS;fan_max_speed_HS;fan_speed_after_x_layers;"
            "additional_cooling_fan_speed"
        )
        self.assertEqual(
            output_project["different_settings_to_system"],
            expected_overrides,
        )
        for key in prior_project.keys() - {"different_settings_to_system"}:
            if key == "curr_bed_type":
                self.assertEqual(output_project[key], prior_project[key])
            elif key in ("cool_plate_temp", "cool_plate_temp_initial_layer"):
                expected_temperatures = prior_project[key][:]
                expected_temperatures[
                    revision.TRANSPARENT_FILAMENT_SLOT - 1
                ] = "55"
                self.assertEqual(output_project[key], expected_temperatures)
            else:
                self.assertEqual(output_project[key], prior_project[key], key)

        prior_model = ET.fromstring(
            self.previous["Metadata/model_settings.config"]
        )
        output_model = ET.fromstring(
            self.output["Metadata/model_settings.config"]
        )
        transparent_plate = next(
            plate for plate in output_model.findall("plate")
            if any(
                item.get("key") == "plater_id"
                and item.get("value") == str(revision.TRANSPARENT_PLATE_ID)
                for item in plate.findall("metadata")
            )
        )
        plate_settings = {
            item.get("key"): item.get("value")
            for item in transparent_plate.findall("metadata")
        }
        self.assertEqual(
            plate_settings["bed_type"],
            "Cool Plate",
        )
        self.assertNotIn("curr_bed_type", plate_settings)
        prior_transparent_plate = next(
            plate for plate in prior_model.findall("plate")
            if any(
                item.get("key") == "plater_id"
                and item.get("value") == str(revision.TRANSPARENT_PLATE_ID)
                for item in plate.findall("metadata")
            )
        )
        self.assertNotIn(
            "bed_type",
            {
                item.get("key"): item.get("value")
                for item in prior_transparent_plate.findall("metadata")
            },
        )
        prior_objects = {
            item.get("id"): item for item in prior_model.findall("object")
        }
        output_objects = {
            item.get("id"): item for item in output_model.findall("object")
        }
        self.assertEqual(prior_objects.keys(), output_objects.keys())
        for object_id in prior_objects.keys() - {"6"}:
            self.assertEqual(
                ET.tostring(output_objects[object_id]),
                ET.tostring(prior_objects[object_id]),
            )
        front_before = ET.fromstring(ET.tostring(prior_objects["6"]))
        front_after = ET.fromstring(ET.tostring(output_objects["6"]))
        approved_surface_keys = {
            "top_shell_layers",
            "top_shell_thickness",
            "ironing_type",
            "infill_direction",
            "solid_infill_direction",
            "initial_layer_speed",
        }
        for root in (front_before, front_after):
            for metadata in list(root.findall("metadata")):
                if metadata.get("key") in approved_surface_keys:
                    root.remove(metadata)
        self.assertEqual(ET.tostring(front_after), ET.tostring(front_before))

        before_windows = revision.resource_window_loops(before, 0.0)
        after_window_z = float(after.bounds[0, 2]) + 0.05
        after_windows = revision.resource_window_loops(after, after_window_z)
        self.assertEqual(len(before_windows), 6)
        self.assertEqual(len(after_windows), 6)
        for actual, expected in zip(
            after_windows, revision.target_window_specs()
        ):
            np.testing.assert_allclose(
                actual[0], expected["center_mm"],
                atol=revision.TOL, rtol=0,
            )
            np.testing.assert_allclose(
                actual[1], expected["size_mm"],
                atol=revision.TOL, rtol=0,
            )
        ramp = self.report["followup_adjustments"]["window5_to6_transition"]
        ramp_checks = ramp["exported_cube_probe_checks"]
        self.assertTrue(ramp_checks["geometry_passed"])
        self.assertEqual(
            ramp["ramp_y_bounds_mm"], ramp["overlap_y_bounds_mm"]
        )
        self.assertAlmostEqual(
            ramp["ramp_span_y_mm"],
            ramp["overlap_y_bounds_mm"][1] - ramp["overlap_y_bounds_mm"][0],
        )
        self.assertAlmostEqual(
            ramp["ramp_cross_slope_width_mm"],
            revision.TRANSITION_RAMP_RUN_MM,
        )
        self.assertAlmostEqual(ramp["slope_run_x_mm"], 8.64, places=3)
        self.assertAlmostEqual(ramp["ramp_depth_z_mm"], 2.5, places=3)
        self.assertGreater(
            ramp["window5_opening_after_ramp_mm"],
            revision.OPENING_WIDTH,
        )
        self.assertEqual(ramp["window6_opening_width_preserved_mm"], 69.0)
        self.assertGreater(
            ramp["slope_run_x_mm"], ramp["reference_web_4_to5_mm"]
        )
        self.assertAlmostEqual(
            ramp["ramp_angle_from_front_face_deg"], 16.14, places=1
        )
        self.assertTrue(ramp["slope_rises_with_increasing_model_x"])
        self.assertFalse(ramp["physical_view_x_reversed_from_model"])
        self.assertTrue(ramp_checks["ramp_direction_matches_printed_left_to_right"])
        self.assertTrue(ramp_checks["cube_sweep_is_continuous"])
        self.assertTrue(ramp_checks["cube_sweep_clearance_passed"])
        self.assertEqual(
            ramp_checks["continuous_cube_sweep_max_intersection_mm3"], 0.0
        )
        self.assertTrue(all(
            abs(actual - ramp_checks["ramp_material_probe_volume_mm3"]) < 1e-5
            for actual in
            ramp_checks["ramp_material_probe_below_intersection_mm3"]
        ))
        self.assertEqual(len(ramp_checks["ramp_material_probe_x_fractions"]), 11)
        self.assertEqual(len(ramp_checks["solid_material_probe_y_levels_mm"]), 3)
        self.assertEqual(
            len(ramp_checks["ramp_material_probe_below_intersection_mm3"]), 33
        )
        self.assertEqual(
            len(ramp_checks["ramp_material_probe_above_intersection_mm3"]), 33
        )
        self.assertTrue(ramp_checks["solid_material_confirmed_along_slope"])
        self.assertTrue(ramp_checks["empty_space_confirmed_above_slope"])
        self.assertEqual(len(ramp_checks["cube_sweep_y_positions"]), 3)
        self.assertEqual(len(ramp_checks["cube_sweep_normal_clearances"]), 3)
        self.assertFalse(ramp_checks["physical_cube_transfer_tested"])

        before_slider = revision.long_horizontal_slot(
            before, 0.0, revision.PREVIOUS_LONG_SLOT_HEIGHT
        )
        after_slider = revision.long_horizontal_slot(
            after, 0.0, revision.LONG_SLOT_HEIGHT
        )
        np.testing.assert_allclose(
            after_slider[0], revision.FOLLOWUP_SLIDER_CENTER_MM,
            atol=revision.TOL, rtol=0,
        )
        self.assertAlmostEqual(after_slider[1][0], before_slider[1][0], places=5)
        self.assertAlmostEqual(
            after_slider[0][1] + after_slider[1][1] / 2,
            before_slider[0][1] + before_slider[1][1] / 2,
            places=5,
        )
        self.assertAlmostEqual(
            before_slider[1][1], revision.PREVIOUS_LONG_SLOT_HEIGHT, places=5
        )
        self.assertAlmostEqual(
            after_slider[1][1], revision.OPENING_WIDTH, places=5
        )
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
