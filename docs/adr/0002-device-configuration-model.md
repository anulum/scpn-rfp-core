<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ADR 0002: device configuration model
-->

# ADR 0002 — Device configuration model and evidence-maturity semantics

**Status:** accepted (2026-08-31)

**Deciders:** project owner; SCPN Reactor Systems Research Group standard

## Context

The repository was established architecture-only (ADR 0001). The first
capability lane is the device configuration model for the single
registry configuration this repository owns (`reversed_field_pinch`).
The same two decisions the family pilot ratified apply: the claim
boundary, and the repository-level `evidence_maturity` semantics.

## Decision

1. The package `scpn_rfp_core` implements the device configuration
   model as frozen, strictly typed value objects: toroidal pinch
   geometry, the F/Θ field programme, and operational limits.
2. Claim boundary — identical to the family pilot: internal-consistency
   validation, cited textbook estimates with documented bounds,
   canonical serialisation with SHA-256 digest, and the data-only SPO
   registry pin. No claim about any real machine; every exercised
   parameter set is a synthetic test fixture.
3. Edge-reversal invariant (hard): the reversal parameter
   ``F = B_phi(a) / <B_phi>`` must be non-positive — a reversed edge
   toroidal field is the defining property of the configuration class.
   ``F`` is bounded to ``[-2, 0]`` and the pinch parameter
   ``Theta = B_theta(a) / <B_phi>`` to ``(0, 5]`` as model bounds.
4. Cross-field consistency (advisory, never clamped): the declared
   pinch parameter is compared against the value derived from the
   declared plasma current and geometry via
   ``B_theta(a) = mu0 I_p / (2 pi a)``; a relative mismatch above 20 %
   is reported. A declared ``Theta`` below ~1.2 is flagged because
   field reversal is not expected below the Taylor-relaxation threshold
   (J. B. Taylor, Phys. Rev. Lett. 33 (1974) 1139).
5. Repository-level `evidence_maturity` = the highest state claimed by
   any capability entry; per-capability states are the authoritative
   claim surface (family ADR 0002 semantics).
6. Everything else is unchanged: review-only/non-actionable SPO
   profile, no adapter implementation, empty solver seams,
   `not_federated` Studio state, independent machine-protection veto,
   all non-claims.

## Consequences

- The Studio descriptor's `capabilities` array carries its first item
  (schema 1.1.0 data change only).
- The reactor-domain validator gains the populated-capabilities branch
  with the ceiling rule.
- Later lanes (magnetics/mode diagnostic semantics, safety envelope)
  build on these types; maturity advances per capability only with the
  evidence the family standard requires.
