<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ADR 0001: repository boundary
-->

# ADR 0001 — Repository boundary and ownership

**Status:** accepted (2026-08-30)  
**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The SCPN reactor portfolio assigns every built-in configuration of the SCPN
Phase Orchestrator reactor registry (version `1.0.0`, 32 configurations) to
exactly one device-family repository. The reversed-field pinch is a
toroidal device superficially adjacent to the tokamak, but its confinement
principle (relaxed, current-dominated state with edge field reversal and
dynamo sustainment) and lifecycle differ fundamentally. A boundary decision
was needed on its ownership and its relations to the solver, semantic,
control, presentation, and machine-protection layers.

## Decision

1. `SCPN-RFP-CORE` owns exactly one registry configuration:
   `reversed_field_pinch` (relaxed-current torus).
2. The repository owns device-level truth only: relaxed-state configuration
   policy, pulsed circuit-programmed lifecycle semantics, magnetics-heavy
   diagnostic declarations (reversal and pinch parameters, helicity-regime
   identification), actuator-response model boundaries, the safety-envelope
   declaration, and the device-owned CONTROL adapter specification.
3. Solver mathematics remains in `SCPN-FUSION-CORE` until an exact surface
   passes the family migration gate. No solver code is copied here.
4. Typed semantics remain in `SCPN-PHASE-ORCHESTRATOR` (review-only).
   Admission and `ControlAction` formation remain exclusively in
   `SCPN-CONTROL`. Machine protection remains independent with the final
   veto. Presentation remains in `SCPN-STUDIO`; this project is
   `not_federated`.
5. The repository starts, and remains until evidenced otherwise, at
   `architecture_only` with empty capability and claim inventories.

## Alternatives considered

- **Folding the RFP into the tokamak repository** (both are axisymmetric
  tori with inductive drive): rejected — the governing physics (relaxed
  state, sub-unity falling safety factor, dynamo sustainment), the
  diagnostic model (reversal/pinch parameters, helicity regimes), and the
  hazard structure (relaxation events rather than the tokamak disruption
  chain) differ on surfaces 1, 4, and 3.
- **Grouping all pinch-class devices** (RFP + Z-pinch + theta pinch):
  rejected — the RFP is a quasi-steady toroidal confinement device with an
  external toroidal-field circuit; linear pinches are single-shot
  compression devices with a different lifecycle and driver.
- **Absorbing solver code at scaffold time**: rejected — violates the
  migration gate.

## Consequences

- Downstream consumers get one stable identity for the RFP configuration
  and a manifest to bind against.
- The validator fails on any capability or claim entry while maturity is
  `architecture_only`.
- Boundary changes require a portfolio-level map change first; a future ADR
  records any such change here.
