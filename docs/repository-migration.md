# Repository migration

The model catalog was extracted with filtered Git history from
`harrybin/3d-printing` at commit `4243f0e`. `catalog.json` contains the full source
commit and SHA-256 hashes for 141 transferred assets/docs. All 29 STL/3MF outputs,
references, model-specific generators and tests retain their existing paths.
The source repository's history was not rewritten.

The engine is installed as `harrybin-printforge`, pinned in `requirements.txt`;
the Pages workflow selects the same engine release. Bootstrap materializes
ignored shared tools, skills, viewer and setup docs. These resources are not
catalog sources and must not be edited/committed here.

Visibility and license notices remain unchanged. Binary assets use ordinary Git,
as requested. No source asset was relicensed and no geometry was regenerated,
repaired, rotated, rendered or resliced during this migration.

## Existing model regression failure

Before extraction, the original 81-test suite had one error:
`test_ghouls_grip_bone_plate_layout.BonePlateLayoutTests.test_layout_is_centered_compact_and_idempotent`.
`arrange_ghouls_grip_bone_plate.arrange` rejects `hand-finger-ring`, whose
computed X bound reaches 271.07479884546865 mm on the test layout.
This is an existing model-layout defect, not a packaging/import failure.
The failing model test and delivered print project are preserved unchanged.
The catalog CI deliberately reports it instead of skipping it or changing
geometry during a repository migration.

## Checks

Run `printforge verify-catalog .` for the current inventory.
Use `printforge verify-catalog . --migration` for original asset hashes.
The migration check is historical evidence, not a restriction on intentional
future model edits. Run the model regression suite separately after bootstrap;
successful integrity verification does not certify print readiness.
