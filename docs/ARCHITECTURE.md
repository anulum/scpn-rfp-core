<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — Architecture
-->

# Architecture

## Purpose and evidence state

`SCPN-RFP-CORE` is the device-family owner for reversed-field pinch systems
in the SCPN Reactor Systems Research Group portfolio. The
repository owns two implemented capabilities at
`computational_prototype` in `src/scpn_rfp_core/`: the device
configuration model (design record ADR 0002, evidence record
`VALIDATION.md#device-configuration-model`) and the diagnostic and
clock semantics model (design record ADR 0003, evidence record
`VALIDATION.md#diagnostic-and-clock-semantics`). Every other
section below describes boundaries and contracts. The claim inventory is
empty; capability and claim inventories are generated and drift-checked.

## The five-surface boundary

1. **Governing confinement physics** — toroidal confinement by a relaxed,
   current-dominated state (`reversed_field_pinch`, relaxed-current torus):
   the plasma current supplies most of the poloidal and much of the
   toroidal field, the safety factor stays below unity and falls through
   zero towards the edge, where the toroidal field is reversed. The
   configuration sits near a minimum-energy relaxed state and is sustained
   against resistive decay by MHD dynamo activity; the operational spectrum
   spans multiple-helicity turbulence and quasi-single-helicity states.
   Tokamaks (externally dominated toroidal field, safety factor above
   unity), stellarator-family devices (externally generated transform),
   spheromaks (simply connected, no toroidal-field circuit), and linear
   self-magnetic pinches fail this sharing test and are excluded.
2. **Primary driver and energy delivery** — inductive (ohmic) drive with
   programmed poloidal- and toroidal-field circuit waveforms; the pinch is
   formed and sustained by circuit programming rather than by auxiliary
   heating, which remains an optional configuration facet.
3. **Plant and shot lifecycle** — pulsed discharge lifecycle: circuit
   charge, breakdown and pinch formation, current ramp, sustained flat-top
   with dynamo activity and discrete relaxation events, programmed
   termination. Device-level semantics of relaxation bursts and
   wall-locked-mode hazards belong here; their solver physics stays with
   the solver owner.
4. **Diagnostic, reference-frame, and clock model** — magnetics-dominated
   diagnostic declarations: edge coil arrays, mode-number decompositions,
   reversal and pinch parameters (F and Θ), regime identification between
   multiple-helicity and quasi-single-helicity states, laboratory-frame
   conventions and pulse-relative clock identities.
5. **Solver, evidence, and control-contract boundary** — versioned seams
   towards `SCPN-FUSION-CORE`, review-only semantics towards
   `SCPN-PHASE-ORCHESTRATOR`, and the device-owned CONTROL adapter
   specification towards `SCPN-CONTROL`.

## Position in the SCPN ecosystem

```text
SCPN-RFP-CORE (device truth: relaxed-state configuration policy, pulse
               lifecycle, magnetics semantics, safety envelope, adapter spec)
   │  optional versioned solver seams (none active)
   ├──────────────► SCPN-FUSION-CORE      (solver mathematics, evidence)
   │  typed review-only semantics
   ├──────────────► SCPN-PHASE-ORCHESTRATOR (semantics, comparability)
   │  device-owned adapter (specification only; no implementation)
   ├──────────────► SCPN-CONTROL          (admission; sole ControlAction author)
   │  derived portfolio descriptor (not_federated)
   └──────────────► SCPN-STUDIO           (catalogue, evidence UI, gating)

SCPN-CONTROL ──admitted ControlAction──► independent machine protection
                                          (final veto) ─► plant actuators
```

## Repository layout

| Path | Role |
|---|---|
| `reactor-domain.json` | portable source of project identity and contracts |
| `studio/portfolio-descriptor.json` | derived Studio descriptor, `not_federated` |
| `capability-inventory.json` | generated, truthfully empty inventory |
| `docs/CONTROL_ADAPTER_SPECIFICATION.md` | device-owned adapter contract |
| `docs/THREAT_MODEL.md` | assets, trust boundaries, misuse paths |
| `docs/adr/0001-repository-boundary.md` | boundary decision record |
| `tools/` | validators, derivation tools, preflight orchestrator |
| `tests/` | statement- and branch-complete tests for `tools/` |
| `.github/workflows/` | read-only CI definitions (no publication) |

## Contract surfaces and versioning

- `reactor-domain.json` follows schema `scpn.reactor-domain.v1`; schema
  changes are versioned and unknown schemas are rejected by consumers.
- The Studio descriptor is derived deterministically from the manifest and
  embeds the manifest's SHA-256; manual edits are detected as drift.
- The CONTROL adapter contract is specification-only at version
  `0.1.0-spec`.
- SPO binding is fixed to reactor registry `1.0.0`, digest
  `786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090`.

## What would change this architecture

Acceptance of a FUSION solver seam through the family migration gate,
ratification of an SPO `ControlIntent`-class contract, or Studio federation
after a real capability passes producer and consumer gates — each recorded
as a versioned contract change in a new ADR.
