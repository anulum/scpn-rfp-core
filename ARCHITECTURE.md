<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — Architecture summary
-->

# Architecture summary

`SCPN-RFP-CORE` is the device-family owner for reversed-field pinch systems
inside the SCPN Reactor Systems Research Group. The repository holds two implemented capabilities at
`computational_prototype` — the device configuration model (ADR 0002)
and the diagnostic and clock semantics model (ADR 0003), both in
`src/scpn_rfp_core/` — alongside the device boundary, its
ecosystem contracts, and the validation tooling that enforces both.

The authoritative architecture record is
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). The ownership decision and
its consequences are fixed in
[`docs/adr/0001-repository-boundary.md`](docs/adr/0001-repository-boundary.md).

Boundary in one paragraph: this repository owns reversed-field pinch plant
and experiment truth — configuration policy for relaxed, current-dominated
toroidal states with edge toroidal-field reversal and dynamo sustainment,
pulsed circuit-programmed lifecycle semantics with relaxation-event and
helicity-regime records, magnetics-dominated diagnostic and clock
declarations, actuator-response boundaries, safety-envelope declarations,
and the device-owned CONTROL adapter specification. Solver mathematics
stays in `SCPN-FUSION-CORE`; typed semantics stay in
`SCPN-PHASE-ORCHESTRATOR` (review-only); admitted control actions are
formed only by `SCPN-CONTROL`; independent machine protection keeps the
final veto; portfolio presentation belongs to `SCPN-STUDIO`, towards which
this project is `not_federated`.
