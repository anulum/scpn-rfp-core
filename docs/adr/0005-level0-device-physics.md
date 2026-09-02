<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ADR 0005
-->

# ADR 0005 — Level-0 device physics: the Bessel-function relaxed state with native parity

Status: accepted (2026-09-02). Adds the third implemented capability,
`level0_device_physics`, at `computational_prototype`.

## Context

Until this record the repository carried no physics beyond the
current-derived pinch parameter and the Taylor-relaxation advisory of the
configuration model. Every device manifest excludes
`solver_mathematics_and_validation_evidence` (owner SCPN-FUSION-CORE), and
no FUSION seam covers the reversed-field-pinch family. The device owner
therefore needs its own bounded, exercised, published physics: closed
forms from the family's own literature, evaluated on the validated
configuration, without solving any equation. The force-free relaxed state
of the reversed-field pinch in its cylindrical Bessel-function form is
stated in an open-access source (R. Paccagnella, "Relaxation models for
single helical reversed field pinch plasmas", arXiv:1509.07307v2 (2015),
eqs. 4–5, after J. B. Taylor), which also defines the reversal and pinch
parameters ``F`` and ``Theta`` as the wall fields over the cross-section
average of the toroidal field. Taylor's original papers (Phys. Rev. Lett.
33 (1974) 1139; Rev. Mod. Phys. 58 (1986) 741) are not freely available
and are cited through the filed source, which reproduces the model.

## Decision

1. A new owned domain `analytic_device_physics_models` is declared in
   `reactor-domain.json`: device-owned closed-form and 0-D models from the
   device literature. It is disjoint from solver mathematics: no solver
   code is copied, no equilibrium, transport, dynamo or stability equation
   is solved, and no FUSION seam is implied or consumed.
2. Two models, each with its published form cited in the module
   docstring, live one per module under `src/scpn_rfp_core/physics/`:
   the relaxed state (`relaxation.py`: the force-free parameter
   ``mu = 2 Theta / a``, the axis field ``B0 = <B_phi> Theta / J1(2 Theta)``,
   the model reversal parameter ``F_bfm = Theta J0(2 Theta) / J1(2 Theta)``
   against the declared ``F``, the reversal threshold
   ``Theta_rev = j_{0,1} / 2`` and radius ``r_rev = j_{0,1} / mu``, and
   the edge poloidal field against the declared current) and the radial
   profile (`profiles.py`: ``B_phi = B0 J0(mu r)``, ``B_theta = B0 J1(mu r)``
   and ``q = (r / R0) J0 / J1`` with the series limit ``a / (Theta R0)``
   on the axis, at declared stations). A composed `Level0PhysicsRecord`
   serialises canonically with a SHA-256 digest and carries fixed
   non-claims.
3. The model's domain is stated and enforced, never clamped: the
   Bessel-function model is defined for ``0 < Theta < j_{1,1} / 2``
   because ``J1(2 Theta)`` vanishes at the bound (the relaxed state's
   average toroidal field is zero there and ``F_bfm`` has its pole);
   a declared pinch parameter at or beyond it is refused with that reason.
   This bound lies below the kernel's series domain, so the library is
   never asked for an argument it would refuse in normal use.
4. Declared modelling choices are stated: the model is the single-region
   (fully relaxed) limit of the source's two-region construction; the
   argument ``mu r`` is evaluated as ``2 Theta (r / a)``; the on-axis
   safety factor is reported from the series limit rather than from a
   quotient of two zeros; the edge-field comparison restates the
   configuration's own current cross-check in field units.
5. Inputs the configuration does not carry are declared explicitly in
   `ModelInputs` (the radial stations, non-empty, within ``[0, 1]``,
   strictly increasing); nothing is defaulted silently. The absence of a
   reversal surface below the threshold is reported as ``None``.
6. The Bessel functions are the pinned shared kernel library's (ADR 0006);
   the Python floor uses only ``+ - * /`` and those kernels. Native
   kernels (`rust/`, crate `scpn-rfp-rs`, optional distribution
   `scpn-rfp-native` via maturin) mirror every evaluation with identical
   operation order on the library's Rust crate; parity tests compare
   float64 bit patterns, never tolerances. The pure-Python floor remains
   the public API and the default.
7. Performance numbers follow the ecosystem benchmark standard; the local
   artefact is committed and labelled non-isolated.

## Consequences

Evidence maturity stays `computational_prototype`; the claims inventory
stays empty. VALIDATION states per model what is exercised and what is
not claimed; the anchors are identities of the model (``F_bfm = 0`` at
``j_{0,1} / 2``, ``F_bfm -> 1`` as ``Theta -> 0``, the axis limit of
``q``, ``q(a) = 0`` at the threshold, ``B_theta(a) = <B_phi> Theta``) and
the printed zeros of the Bessel functions, which is not a correlation with
data; the source itself records that real relaxed states depart from the
fully relaxed model. The manifest change alters `manifest_sha256` inside
the plan envelope, so the envelope fixture is regenerated from the public
surface and re-pinned; the plan bytes and `plan_sha256` are unchanged.
The configuration model's advisory threshold ``1.2`` is now traceable to
``j_{0,1} / 2`` by a test; its value is unchanged.
