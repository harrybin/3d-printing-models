# Ghoul's Grip – Sources and Licenses

## Skull Accent

### Search Scope

Before the revision, the following search terms were used on October 10, 2026:

- `human skull anatomical scan CC BY STL`
- `NIH 3D Print Exchange human skull CC BY`
- `Smithsonian Open Access human skull 3D scan CC0`
- `human skull CT scan Printables license`

The initial search focused on an anatomical scan with a license permitting
modification and redistribution of derivative repository content.

### Candidates

| Candidate | Creator / primary source | License and rights | Files / quality | Assessment |
| --- | --- | --- | --- | --- |
| **Skull_Human Skeleton**, `3DPX-016801` | My Segmenter, [NIH 3D](https://3d.nih.gov/entries/3DPX-016801/3), metadata: [NIH API](https://3d.nih.gov/api/entries/16801) | **CC BY 4.0**. Modification, commercial use, and redistribution are permitted with attribution, a license link, and a notice of changes: [license text](https://creativecommons.org/licenses/by/4.0/). | CT segmentation; STL, OBJ, GLB, X3D, WRL, and BLEND. The published STL has 613.916 triangles and 306.736 vertices; according to NIH metadata, it is watertight and has no non-manifold edges. Direct NIH API download of the reviewed STL version: `https://3d.nih.gov/api/files/1058705`. | **Very good anatomical reference**, but not a practical mesh component for this 48,5-mm knob. |
| **Human skull CT scan**, model `731166` | Andrzejerzy, [Printables](https://www.printables.com/model/731166-human-skull-ct-scan) | The model page could not be retrieved automatically during review; the specific model license and redistribution requirements could therefore not be verified from the primary source. | STL, approximately 70 MB; according to the search index, CT-based and includes cervical vertebrae. Topology and scale were not downloaded or checked. | **Rejected**: unconfirmed license; the cervical vertebrae and complete scan geometry are also unsuitable for the accent. |
| **Open3DModel – Skull** | Open3DModel / AnatomyTOOL, [project page](https://anatomytool.org/content/open3dmodel-skull-english-labels) | Search index lists CC BY-SA; the specific primary page was unavailable during review, so the version, creator chain, and Share-Alike text could not be sufficiently verified. | Educational model, including in GLB format. No verified printable single body or reproducible direct download was found. | **Rejected**: provenance and specific download license not sufficiently verified. |

### Decision: `reference-only`

The NIH scan is license-compatible but was **not incorporated into the
repository**. A local hybrid test showed why:

- The scan STL contains 613.916 triangles and eleven additional tiny
  eight-triangle fragments beside the main body.
- The full scan has many genuine anatomical openings and internal cavities
  (`Euler number -222`). After scaling, relief cutting, and joining it to the
  back of the knob, the test remained a single body but still had 556.272
  triangles and `Euler number -246`.
- At only about 48,5 × 55,1 mm, the thin ethmoid, dental, and orbital structures
  would fall below useful printable detail sizes. The extensive voxel repair
  required would alter the scan surface so much that it offers no reliable
  advantage over a controlled parametric reconstruction.

For this reason, `scripts/skull.py` uses the scan only as an anatomical shape
reference. The revised original design adds, in particular, supraorbital
ridges, zygomatic pillars, a maxillary arch, ascending mandibular rami, oval
eye sockets, a piriform nasal aperture, and finer gaps between the teeth. The
flange, rib, shaft, and blind Ø8-mm socket remain fully parametric and
unchanged as fit-critical features.

The shipped model has no attribution requirement for the NIH scan because no
scan geometry is distributed. If it is later used as a mesh base, at least the
following attribution must be retained:

> “Skull_Human Skeleton” (`3DPX-016801`) by My Segmenter, NIH 3D,
> licensed under CC BY 4.0; modified for Ghoul's Grip.

## Gothic Chest Ornaments

### Search Scope and Candidates

Before revising the reliefs, searches were made for `Gothic tracery public
domain vector`, `Gothic horror ornament CC0`, `bat wing ornament vector`, and
`acanthus thorn scroll public domain`.

| Candidate | Source | License and rights | Assessment |
| --- | --- | --- | --- |
| **Gothic tracery design elements** | CraftsmanSpace, based on Mabel Sykes, *A Source Book of Problems for Geometry* (1912), [project page](https://www.craftsmanspace.com/free-patterns/gothic-tracery-design-elements.html) | According to the project page, the offered SVG/EPS/DWG files are under **CC BY-SA**; modification and redistribution are permitted with attribution and Share-Alike. | **Reference-only**. The historic pointed-arch and quatrefoil proportions were studied, but no file or contour was incorporated. |
| **Free Gothic vector art** | PublicDomainVectors, [collection](https://publicdomainvectors.org/en/free-gothic-vector-art) | The collection identifies its contents as Public Domain/CC0; individual contributions would need to be checked on their detail pages before direct use. | **Reference-only**. No third-party geometry was imported because of mixed creators and lack of need. |
| **Wikimedia Commons 3D resources** | Wikimedia Commons, [3D resources](https://commons.wikimedia.org/wiki/Commons:Free_media_resources/3D_models) | File-specific free licenses; rights and attribution must be checked for each object. | **Rejected as a component**: no suitable, simple, clearly licensed set of chest reliefs was needed. |

### Decision: `rebuild`

The reliefs in `scripts/gothic_chest.py` are a new parametric original design.
They use:

- rounded thorn and acanthus scrolls from cubically sampled curves;
- leaf finials and quatrefoil rosettes;
- trefoil-like inserts in the rear pointed-arch panels;
- open bat wings with printable ribs on the lid;
- a continuous front cartouche around the rotating skull socket.

No third-party vector or mesh geometry was incorporated. The historical
sources serve only as style and proportion references, so the shipped reliefs
incur no additional attribution or Share-Alike obligations.

## Additional Existing Anatomy Source and Candy-Hand Extension

The hand geometry continues to be based on **“Wrist Bones Full Hand – Human
Skeleton”**, NIH 3D Print Exchange, model `3DPX-016815`, uploaded by My
Segmenter, **CC BY 4.0** ([NIH 3D Entry](https://3d.nih.gov/entries/3DPX-016815)).
Before the candy-hand extension on October 19, 2026, a search was also made for
reusable templates (`3D printable cupped skeleton hand candy holder bowl removable dish STL license Creative Commons`).
Two Printables candidates (`model/1436550-skeleton-hand-bowl`,
`model/590777-halloween-skeleton-candy-bowl`) returned HTTP 403 when their
primary pages were accessed; their licenses could
not be verified from the primary source, and no geometry was downloaded.

Decision: **Hybrid reuse** of the already licensed NIH hand scan
(`3DPX-016815`, CC BY 4.0), rigidly repositioned (opposed thumb, curved
fingers, solid closed knuckle transitions without V-notches) in
`scripts/skeleton_hand.py`, together with a technically redesigned,
removable elliptical candy dish (`candy-dish`) with three asymmetric locating
pins in `scripts/candy_hand.py`.
