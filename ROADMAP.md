<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ROADMAP
-->

# Roadmap

Planned work and implemented capability are kept strictly separate. Anything
listed under "Planned" carries no implementation, no code, and no claim in
this repository until it appears in the capability inventory with evidence.

## Implemented (repository infrastructure, not reactor capability)

- Domain manifest (`reactor-domain.json`) with validator.
- Derived Studio portfolio descriptor (`not_federated`) with drift check.
- Generated capability inventory (truthfully empty) with drift check.
- CONTROL adapter specification (contract only, no implementation).
- Local and workflow gate definitions (lint, typing, tests, coverage,
  REUSE, security audit, SBOM, documentation checks).

- **Device configuration model** (landed 2026-08-31) — validated geometry,
  field-programme (F/Θ), and operational-limit objects for
  `reversed_field_pinch` with the hard edge-reversal invariant (F ≤ 0),
  a declared-vs-derived pinch-parameter cross-check, documented Taylor
  relaxation advisory, canonical digests, and the SPO registry data pin;
  `computational_prototype` (ADR 0002,
  `VALIDATION.md#device-configuration-model`). Shell and mode-control
  coil inventory remains future work under the same capability.
- **Diagnostic and clock semantics** (landed 2026-08-31) — synthetic
  diagnostic-channel and clock declarations aligned fail-closed with the
  pinned SPO observability-profile catalogue (release `1.0.0`): candidate
  applicability, carrier admissibility, exact evidence vocabularies,
  clock-kind compatibility, Nyquist bounds, canonical digests; the
  reference plan mirrors canonical practice (flux loops, Rogowski coil, toroidal probe array, synthetic oscillator);
  `computational_prototype` (ADR 0003,
  `VALIDATION.md#diagnostic-and-clock-semantics`). No ingress is
  declared; the SPO semantic-profile state remains `not_declared`.

## Planned (no implementation exists; ordering is not a commitment)
1. **Safety-envelope declaration** — machine-readable operational envelope
   (current, circuit energy, relaxation and locked-mode margins) consumed
   by the CONTROL adapter contract.
2. **CONTROL adapter implementation** — device-owned adapter against the
   published specification, with replay fixtures and HIL evidence,
   targeting `control_research_ready` only after replay and HIL
   acceptance.
3. **Solver seam consumption** — versioned consumption of exact
   `SCPN-FUSION-CORE` seams for relaxed-state equilibrium and transport
   surfaces, strictly after the family migration gate proves exact
   replacement; no solver code is copied.
4. **Facility-data correlation** — preregistered acceptance contracts
   against identified facility or published experimental data, targeting
   `experiment_correlated` per capability.

## Not planned in this repository

Tokamak systems, stellarator-family systems, spheromaks, FRC physics,
linear pinches, inertial and magneto-inertial systems, mirrors,
electrostatic devices, generic controller mathematics, machine-protection
logic, and any direct actuation path.
