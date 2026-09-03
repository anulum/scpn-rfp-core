<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ADR 0007
-->

# ADR 0007 — Device 3D model and device CAD model of the cylindrical periodic equivalent on the shared kernels

Status: accepted (2026-09-03). Adds the fourth and fifth implemented
capabilities, `device_3d_model` and `device_cad_model`, at
`computational_prototype`.

## Context

The repository owns device truth for the reversed-field pinch family: the
validated configuration carries the pinch geometry (plasma major and
minor radii), the field programme and the operational limits (ADR 0002),
and the level-0 models evaluate the Bessel-function relaxed state of the
cylinder (ADR 0005, ADR 0006). There was no mechanical envelope and no
way to present, measure or hand a design to downstream tooling. The
research group's G1/G2 pattern (the Z-PINCH pilot, the theta-pinch and
spheromak landings) fixes how a family gains it.

The RFP is toroidal; the library's torus-segment primitive has not landed.
What the cylinder primitives CAN carry honestly is the cylindrical
periodic equivalent — which is the geometry of the level-0
Bessel-function model itself: plasma column at r ≤ a, the wall at r = a,
the close-fitting ideal conducting shell the relaxation literature
requires (R. Paccagnella, arXiv:1509.07307v2 (2015): "the presence of an
ideal shell surrounding the plasma is crucial to preserve global
invariants"), and the toroidal-field winding as a solenoid outside it,
over the periodic length 2πR0. The toroidal curvature, the poloidal coil
rings and the shell penetrations are NOT modelled at this tier; the end
caps of the cylinder primitives are an artefact, declared in the
non-claims.

## Decision

1. `DeviceGeometry` carries only what the configuration does not: the
   vessel wall thickness, the shell thickness, and the winding gap and
   thickness. The plasma radii are the configuration's
   `geometry.minor_radius_m` / `geometry.major_radius_m`, used directly —
   never duplicated. The periodic length is `2 pi R0` computed in one
   fixed operation order.
2. Four bodies in a fixed order: `plasma_column`, `vacuum_vessel`,
   `conducting_shell`, `toroidal_field_winding`, nested radially, each
   spanning the full periodic length.
3. Tier G1: `DeviceModel3D` (`scpn.rfp-3d-model.v1` 1.0.0) on the
   library's tessellation primitives with the closed-mesh contract; the
   exports are the library's serialisers with the device provenance as
   the GLB document extras. Tier G2: `DeviceModelCAD`
   (`scpn.rfp-cad-model.v1` 1.0.0) on the library's `cad` group
   (`cad_brep_solids`, `cad_step_export`, `cad_faceting`) with the
   library's `cad_evidence` kernel checking every body fail-closed
   (B-rep against the analytic closed forms within 1e-9, faceted volume
   within the declared deflection deficit bound and the exact
   polygon-deficit bound of the G1 reference mesh); the STEP export is
   the library's normalised deterministic writer and `write_step` writes
   exactly the digested bytes.
4. The kernel-library pin moves to the commit carrying the CAD group, the
   evidence kernel and the placement kernels (0f76b8ca); the manifest's
   `kernel_library` block records it with the inventory digest at that
   commit and the consumed kernel identifiers (the four geometry kernels,
   the three CAD kernels, the evidence kernel, and `numerics_bessel`,
   which the level-0 physics continues to consume). The dependency gains
   the optional `cad` extra; the CI gains a `cad` job that installs the
   system library the mesher's wheel links against before the extra; the
   crate re-locks its `scpn-reactor-kernels-rs` dependency at the same
   commit and gains the group's documentation lints with `cargo doc` in
   the rust gate.
5. No anchor fixture at this tier: no filed source prints the dimensions
   of a published arrangement for this family; every fixture is
   synthetic. (The Z-PINCH pilot precedent: a qualitative layout source
   with synthetic dimensions.)

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty; the excluded domain
`shared_physics_geometry_and_numerics_kernels` already names the library.
The STEP file is an export of the record, never its source; determinism
of the STEP bytes is claimed within the pinned back-end environment only
(the record carries the back-end versions), and a back-end bump re-pins
the record digest as a governed data change. A change of the library pin
is a governed data change of this repository (manifest, descriptor and
inventory regeneration, envelope fixture re-pin, SPO re-intake). When the
library lands the torus-segment primitive, the toroidal device model is a
later tier with its own ADR; the cylindrical equivalent stays as the
level-0 model's own geometry.
