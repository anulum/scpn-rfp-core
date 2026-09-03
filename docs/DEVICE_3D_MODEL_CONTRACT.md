<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — Device 3D model contract
-->

# Device 3D model contract

Producer-owned contract of the `device_3d_model` and `device_cad_model`
capabilities (`computational_prototype`; design record ADR 0007). It states
exactly what the exported files contain so that a consumer — the portfolio
presentation layer, an engineering tool, a reviewer — can read them without
importing this package. Nothing in the files or in this contract creates a
federation, a claim, or an engineering statement.

## What is modelled, and what a toroidal device loses in it

A reversed field pinch is a torus. What this tier builds is its **cylindrical
periodic equivalent**: the torus cut at one poloidal plane and straightened,
so the axial extent is the periodic length `2 pi R0` and the bodies are
concentric cylinders and tubes of the minor cross-section. The end caps of
those cylinders are an artefact of the primitive, not a wall; the toroidal
curvature, the poloidal coil rings and the shell penetrations are not
modelled here. This is stated in the record's own `non_claims` and repeated
below, because it is the single most consequential thing a reader of these
files has to know.

## Records

| Record | Schema | Identity |
|---|---|---|
| Device configuration | package `DeviceConfiguration` record | `configuration_digest_sha256` |
| Device geometry | package `DeviceGeometry` record (four SI fields) | `geometry_digest_sha256` |
| Device model | `scpn.rfp-3d-model.v1` version `1.0.0` | `model_sha256` = SHA-256 of the canonical model record |
| CAD model | `scpn.rfp-cad-model.v1` version `1.0.0` | `step_sha256` of the exported STEP bytes |
| Body mesh | little-endian `uint32 vertex_count, uint32 face_count, float64 x y z per vertex, uint32 i j k per face` | `mesh_sha256` |

The model record carries: `schema`, `schema_version`, `units`, `non_claims`,
`configuration_digest_sha256`, `geometry_digest_sha256`, `segments`, and
`bodies` (one summary per body: `name`, `role`, `material_identifier`,
`vertex_count`, `face_count`, `volume_m3`, `surface_area_m2`,
`bounding_box_min_m`, `bounding_box_max_m`, `mesh_sha256`). Canonical bytes
are UTF-8 JSON with sorted keys, minimal separators and a trailing newline;
NaN and infinity are never emitted.

The four geometry fields are the envelope only: `vessel_wall_thickness_m`,
`shell_thickness_m`, `winding_gap_m`, `winding_thickness_m`. The plasma
minor radius `a` and major radius `R0` live in the configuration's
`PinchGeometry` and are read from there — one number, one home.

## Units and axes

- Length unit: metre, in every record and in both export formats.
- Right-handed Cartesian frame; `z` runs along the axis of the cylindrical
  periodic equivalent, and the origin is `z = 0` at one end of the periodic
  length `2 pi R0`. Every body spans that full length.
- Float64 in the records and the canonical mesh bytes; float32 in STL and
  GLB because both containers require it (the canonical digests are taken on
  the float64 bytes, never on the exports).

## Bodies (fixed order, fixed names)

| Node name | Role | Material token | Analytic body |
|---|---|---|---|
| `plasma_column` | `plasma` | `plasma` | solid cylinder of radius `a` |
| `vacuum_vessel` | `vacuum_boundary` | `vessel_wall` | annular tube, `a` to `a + t_vessel` |
| `conducting_shell` | `vacuum_boundary` | `shell_conductor` | annular tube, `a + t_vessel` to `a + t_vessel + t_shell` |
| `toroidal_field_winding` | `coil` | `coil_conductor` | annular tube, inner radius `a + t_vessel + t_shell + gap`, thickness `t_winding` |

Material tokens are declarations only; no density, composition,
conductivity or nuclear property is carried anywhere. The plasma body is the
cylindrical domain of the relaxed state the level-0 models describe, not a
computed equilibrium boundary.

Every body is a closed triangle surface with outward orientation
(counter-clockwise vertex order seen from outside), no degenerate face, every
directed edge appearing exactly once together with its reverse. Segment
counts are multiples of eight (at least eight).

## Files

- **Binary STL** (`stl_bytes`, `write_stl`): 80-byte header starting with the
  shared library kernel's literal, `uint32` triangle count, then per triangle
  a float32 unit normal, three float32 vertices and a zero `uint16` attribute.
  All bodies are concatenated in the fixed order; STL carries no names, so the
  GLB is the file for body identity.
- **glTF 2.0 binary** (`glb_bytes`, `write_glb`): header (magic `glTF`,
  version 2, total length), one JSON chunk (space-padded to four bytes), one
  binary chunk (zero-padded). One `mesh` and one `node` per body, the node
  named as in the table above, with `node.extras` = `{role,
  material_identifier, mesh_sha256}`. Each primitive has a float32 `VEC3`
  `POSITION` accessor with `min`/`max` and a `uint32` `SCALAR` index accessor,
  mode `TRIANGLES`; buffer views are four-byte aligned. The document `extras`
  carry `schema`, `schema_version`, `configuration_digest_sha256`,
  `geometry_digest_sha256`, `model_sha256`, `segments`, `units` and
  `non_claims`. No materials, textures, animations or extensions are used.
- **STEP** (`write_step`, capability `device_cad_model`): an ISO 10303-21
  (AP214) export of the B-rep assembly of the SAME four bodies, built by the
  pinned OpenCASCADE kernel through the shared library's `cad` group. The
  header is normalised by the library so the bytes are reproducible. The file
  written is exactly the byte string whose SHA-256 the CAD model record
  carries as `step_sha256`, next to the back-end versions; the bytes are
  deterministic within one pinned back-end environment and no identity across
  OpenCASCADE or gmsh versions is claimed. The CAD record additionally
  carries, per body, the B-rep volume and area against the analytic closed
  form, and the faceted volume against the tessellated model at the declared
  reference segment count (`8`, linear deflection `1e-4 m`, angular deflection
  `0.1 rad`).

## Determinism

The same configuration, geometry and segment count always yield the same
records, the same mesh bytes and the same export bytes, on every backend: the
vertex coordinates are computed by the polynomial unit circle of the shared
kernel library `scpn-reactor-kernels` (pinned by commit object and
kernel-inventory digest in `reactor-domain.json`, `kernel_library`) with fixed
operation order, proven bit-exact between that library's Python floor and its
native kernels, and the device model is proven bit-exact against the library's
native module body by body. The serialisers are the library's kernel
`geometry_exports`: the binary STL header and the glTF `asset.generator` name
that kernel, while the document `extras` carry this repository's provenance. A
change of the library pin is a governed data change of this repository.

## Anchoring

The geometry tier carries two fixture pairs. The *reference* pair is
synthetic. The *anchor* pair reproduces the values printed by Paccagnella,
"Relaxation models for single helical reversed field pinch plasmas",
arXiv:1509.07307 (2015), on file: the aspect ratio `R/a = 5` of its single
helical eigenstates and the reversal parameter `F = -0.05` it calls the
shallow reversed case. That source works throughout in units normalised to
the plasma minor radius and prints no length in metres, so what is anchored
is dimensionless — which is what this family has to anchor on. Both tiers are
checked against it: the tessellated plasma column returns the printed ratio
from its bounding box exactly, and the B-rep solid returns it within the
kernel's measurement tolerance. The absolute radii that realise the ratio,
the pinch parameter, the field amplitude, the operational limits and every
envelope thickness are declared and said to be declared.

## Non-claims

- The bodies are analytic surfaces of a declared design: no equilibrium
  boundary, no engineering model.
- The cylindrical periodic equivalent of a toroidal device is modelled; the
  cylinder end caps are an artefact of the primitive, and the toroidal
  curvature, poloidal coil rings and shell penetrations are absent.
- A value reproduced from a published source (the anchor fixture) is an
  anchor, not a claim about any machine.
- No material property, load, field or neutronic quantity is carried.
- No value describes or validates any real machine.
- Providing these files does not federate the repository, present it, or gate
  its execution anywhere; those remain the portfolio layer's domain.
