# Ghoul's Grip - Mechanism Verification

Result of the wall and floor-bearing correction: **PASS**

The floor bearings were rebuilt as open double cheeks around the unchanged arm envelopes. Largest current arm/chest intersection volume: 0.000082 mm³. Each individual arm is checked in all 61 states; any intersection greater than 0.001 mm³ fails the verification. This proves geometry, not load capacity or PLA fit.

Baseline comparison: the chest from `f396e7a:models/ghouls-grip-view.3mf`, with only the view-plate offset reversed, was checked against the same unchanged scissor arms. Greatest improvement with the corrected enclosure: 462.644683 mm³.

The verification covers the rigid, manually reversible power train: rotating skull -> drive pinion -> slider rack -> double scissors, and drive pinion -> lid rack -> captured lid-crank pin. A moving five-gear train with three idler gears transfers scissor-arm rotation to the forearm. There are no cables, rubber bands, springs, or winding spools.

| Check | Result |
| --- | ---: |
| Max. Pivot-Schließfehler | 0.000000 mm |
| Kleinster Scherenkulissenrand | 1.000 mm |
| Ritzel/Zahnstangen-Schließfehler | 0.000000 mm |
| Deckelkurbel-Schließfehler | 0.000000 mm |
| Kleinster Deckelzapfen-Kulissenrand | 1.000 mm |
| Max. Zahnrad-Mittenfehler | 0.000000 mm |
| Max. Zahnrad-Teilungsfehler | 0.162 mm |
| Zwischenrad-Pinspiel | 0.400 mm |
| Unterarm-Einsetzsweep | 0.000 mm³ |
| D-Wellen-Einsetzsweep | 0.000 mm³ |
| Hinterwand am ehemaligen Mechanikfenster | 100.000% massiv |
| Totenkopf-Drehweg | 113.54° |
| Einzelkörper je Druckteil | {'scissor-arm': 1, 'slider': 1, 'lid-follower-rack': 1, 'platform': 1, 'drive-pinion': 1, 'lid-crank': 1, 'crank-spacer': 1, 'lid-transfer-gear': 1, 'scissor-drive-gear': 1, 'idler-gear': 1, 'forearm-output-gear': 1, 'forearm': 1, 'chest': 1, 'lid': 1} |
| Laufzeit | 323.2 s |
| Sweep hand_chest | 0.000 mm³ |
| Sweep hand_lid | 0.000 mm³ |
| Sweep hand_platform | 0.000 mm³ |
| Sweep hand_scissor | 0.000 mm³ |
| Sweep forearm_platform | 0.000 mm³ |
| Sweep input_gear_platform | 0.000 mm³ |
| Sweep idler_gear_0_platform | 0.000 mm³ |
| Sweep idler_gear_1_platform | 0.000 mm³ |
| Sweep idler_gear_2_platform | 0.000 mm³ |
| Sweep output_gear_platform | 0.000 mm³ |
| Sweep output_gear_forearm | 0.000 mm³ |
| Sweep gear_mesh_0_1 | 0.000 mm³ |
| Sweep gear_mesh_1_2 | 0.000 mm³ |
| Sweep gear_mesh_2_3 | 0.000 mm³ |
| Sweep gear_mesh_3_4 | 0.000 mm³ |
| Sweep slider_chest | 0.000 mm³ |
| Sweep lid_chest | 0.000 mm³ |
| Sweep lid_rack_lid | 0.000 mm³ |
| Sweep lid_rack_chest | 0.000 mm³ |
| Sweep lid_yoke_lid | 0.000 mm³ |
| Sweep lid_yoke_chest | 0.000 mm³ |
| Sweep lid_crank_lid | 0.000 mm³ |
| Sweep lid_crank_chest | 0.000 mm³ |
| Sweep platform_chest | 0.000 mm³ |
| Sweep scissors_repaired_region | 0.000 mm³ |
| Sweep lid_transfer_input_chest | 0.000 mm³ |
| Sweep lid_transfer_idler_chest | 0.000 mm³ |
| Sweep lid_transfer_input_lid | 0.000 mm³ |
| Sweep lid_transfer_idler_lid | 0.000 mm³ |
| Sweep lid_transfer_mesh_0_1 | 0.000 mm³ |
| Sweep lid_transfer_mesh_1_2 | 0.000 mm³ |
| Sweep lid_transfer_input_rack | 0.000 mm³ |
| Sweep arm-0-False_chest | 0.000 mm³ |
| Sweep arm-0-True_chest | 0.000 mm³ |
| Sweep arm-1-False_chest | 0.000 mm³ |
| Sweep arm-1-True_chest | 0.000 mm³ |

## Resolved Existing Collision (Baseline for Comparison Only)

| Scissor angle / pose | Pair | Baseline f396e7a | Current |
| --- | --- | ---: | ---: |
| 18 Grad | scissors_chest (Bodenlager) | 424.376 mm³ | 0.000 mm³ |
| 48 Grad | scissors_chest (Bodenlager) | 421.088 mm³ | 0.000 mm³ |
| 78 Grad | scissors_chest (Bodenlager) | 462.645 mm³ | 0.000 mm³ |

| Pose | Individual pair | Baseline f396e7a | Current |
| --- | --- | ---: | ---: |
| 18 Grad | arm-0-False / chest (Bodenlager) | 212.188 mm³ | 0.000 mm³ |
| 18 Grad | arm-1-False / chest (Bodenlager) | 212.188 mm³ | 0.000 mm³ |
| 48 Grad | arm-0-False / chest (Bodenlager) | 210.544 mm³ | 0.000 mm³ |
| 48 Grad | arm-1-False / chest (Bodenlager) | 210.544 mm³ | 0.000 mm³ |
| 78 Grad | arm-0-False / chest (Bodenlager) | 231.322 mm³ | 0.000 mm³ |
| 78 Grad | arm-1-False / chest (Bodenlager) | 231.322 mm³ | 0.000 mm³ |

The rear rack runs 14,854 mm farther inward. Two identical transfer gears transmit motion with two direction reversals and a 1:1 ratio to the unchanged lid sector. The chest wall is now continuous across the former opening; all 61 scissor positions from 18 to 78 degrees, including 48 degrees, are checked against the actual wall.

## Coupled Motion

| Scissor angle | Skull/pinion | Lid | Forearm |
| ---: | ---: | ---: | ---: |
| 18° | 0.0° | -0.0° | -105.0° |
| 19° | 0.8° | -7.2° | -104.0° |
| 20° | 1.7° | -14.7° | -103.0° |
| 21° | 2.7° | -22.6° | -102.0° |
| 22° | 3.6° | -30.9° | -101.0° |
| 23° | 4.7° | -39.6° | -100.0° |
| 24° | 5.7° | -48.6° | -99.0° |
| 25° | 6.8° | -58.0° | -98.0° |
| 26° | 8.0° | -67.7° | -97.0° |
| 27° | 9.2° | -77.8° | -96.0° |
| 28° | 10.4° | -88.3° | -95.0° |
| 29° | 11.7° | -99.1° | -94.0° |
| 30° | 13.0° | -108.0° | -93.0° |
| 31° | 14.3° | -108.0° | -92.0° |
| 32° | 15.7° | -108.0° | -91.0° |
| 33° | 17.2° | -108.0° | -90.0° |
| 34° | 18.6° | -108.0° | -89.0° |
| 35° | 20.2° | -108.0° | -88.0° |
| 36° | 21.7° | -108.0° | -87.0° |
| 37° | 23.3° | -108.0° | -86.0° |
| 38° | 24.9° | -108.0° | -85.0° |
| 39° | 26.6° | -108.0° | -84.0° |
| 40° | 28.3° | -108.0° | -83.0° |
| 41° | 30.0° | -108.0° | -82.0° |
| 42° | 31.8° | -108.0° | -81.0° |
| 43° | 33.6° | -108.0° | -80.0° |
| 44° | 35.4° | -108.0° | -79.0° |
| 45° | 37.3° | -108.0° | -78.0° |
| 46° | 39.2° | -108.0° | -77.0° |
| 47° | 41.1° | -108.0° | -76.0° |
| 48° | 43.1° | -108.0° | -75.0° |
| 49° | 45.1° | -108.0° | -74.0° |
| 50° | 47.1° | -108.0° | -73.0° |
| 51° | 49.2° | -108.0° | -72.0° |
| 52° | 51.2° | -108.0° | -71.0° |
| 53° | 53.4° | -108.0° | -70.0° |
| 54° | 55.5° | -108.0° | -69.0° |
| 55° | 57.7° | -108.0° | -68.0° |
| 56° | 59.9° | -108.0° | -67.0° |
| 57° | 62.1° | -108.0° | -66.0° |
| 58° | 64.3° | -108.0° | -65.0° |
| 59° | 66.6° | -108.0° | -64.0° |
| 60° | 68.9° | -108.0° | -63.0° |
| 61° | 71.2° | -108.0° | -62.0° |
| 62° | 73.6° | -108.0° | -61.0° |
| 63° | 75.9° | -108.0° | -60.0° |
| 64° | 78.3° | -108.0° | -59.0° |
| 65° | 80.7° | -108.0° | -58.0° |
| 66° | 83.2° | -108.0° | -57.0° |
| 67° | 85.6° | -108.0° | -56.0° |
| 68° | 88.1° | -108.0° | -55.0° |
| 69° | 90.6° | -108.0° | -54.0° |
| 70° | 93.1° | -108.0° | -53.0° |
| 71° | 95.6° | -108.0° | -52.0° |
| 72° | 98.1° | -108.0° | -51.0° |
| 73° | 100.6° | -108.0° | -50.0° |
| 74° | 103.2° | -108.0° | -49.0° |
| 75° | 105.8° | -108.0° | -48.0° |
| 76° | 108.3° | -108.0° | -47.0° |
| 77° | 110.9° | -108.0° | -46.0° |
| 78° | 113.5° | -108.0° | -45.0° |

Insert the bone-colored forearm from above between the two bearing ears, without the gear attached. Then slide the natural-white output gear and its D-shaft axially from the gear side through both round bearings and the matching D-hub in the forearm. A 1.75-mm filament pin in the outer cross-hole secures the shaft against slipping out; install the idler gears only afterward.

The fingers remain printable, pre-curved PLA flexures in the compact gripping pose. The new rigid power train actuates the lid, scissor lift, and forearm; it deliberately does not simulate tendon actuation.
