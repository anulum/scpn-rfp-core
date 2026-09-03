<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — VALIDATION
-->

# Validation

Every gate currently active in this repository, with its exact scope,
followed by the evidence record of each implemented capability.

## Local gates

| Gate | Command | Scope |
|---|---|---|
| Lint | `ruff check .` | all Python under `src/`, `tools/`, and `tests/` |
| Format | `ruff format --check .` | same scope |
| Typing | `mypy --strict src tools tests benchmarks` | zero errors, strict mode |
| Tests + coverage | `pytest -q --cov=src --cov=tools --cov-branch --cov-fail-under=100` | 100 % statement and branch coverage of `src/` and `tools/` |
| Domain manifest | `python3 tools/validate_reactor_domain.py reactor-domain.json` | schema, registry version/digest, exact configuration set, capability inventory shape and ceiling rule, safety boundary, the optional shared-kernel-library pin |
| Studio descriptor | `python3 tools/derive_studio_descriptor.py --check` | committed descriptor byte-identical to a fresh derivation |
| Capability inventory | `python3 tools/generate_capability_inventory.py --check` | committed inventory byte-identical to a fresh generation |
| Licensing | `reuse lint` | REUSE 3.x compliance of the full tree |
| Workflow lint | `actionlint` | all files under `.github/workflows/` |
| Workflow modularity | `python3 tools/audit_workflows.py` | distributed workflow inventory: single ownership per job, coordinator/gate contract, action pinning, size ceilings |
| Native crate | `make rust` | format, lint and unit tests of the optional native kernels (fetches the pinned kernel crate) |
| Documentation | `python3 tools/preflight.py --only docs` | UTF-8 readability and relative-link integrity of every Markdown file |
| Orchestrated | `python3 tools/preflight.py` | fail-closed run of all gates above |

## Workflow gates

Definitions are present in-repository; they run on the hosted platform
only once a remote exists under separate owner authority.

The hosted surface is modular: `ci.yml` is a coordinator that carries
only trigger policy, two reusable-workflow calls, and one stable
fail-closed `gate` job aggregating every category (failure,
cancellation, and unexpected skips all fail the gate). Every job is
declared and owned exactly once in the versioned inventory
`.github/workflow-inventory.json`, which the workflow-modularity guard
verifies locally and in hosted CI.

| Workflow | Purpose |
|---|---|
| `ci.yml` | coordinator and stable required gate |
| `reusable-static-policy.yml` | lint, format, typing, domain policy, workflow guard |
| `reusable-tests.yml` | tests with complete statement and branch coverage; native crate gates, bit-exact parity and a benchmark smoke |
| `pre-commit.yml` | exact pre-commit parity |
| `codeql.yml` | Python code scanning |
| `security-audit.yml` | secrets, dependency, licence, and workflow policy |
| `docs.yml` | strict documentation and link validation, no deployment |
| `sbom.yml` | reproducible dependency inventory, no release |
| `scorecard.yml` | read-only supply-chain analysis |

## Shared ecosystem gate

From the monorepo root:

```bash
python3 agentic-shared/scripts/repository_tier0_scaffold_audit.py \
  03_CODE/SCPN-RFP-CORE --json
```

proves the Tier-0 local-scaffold machine profile (required and forbidden
paths, Git/remote boundary, workflow pins and permissions, badge non-claims,
JSON integrity, defensive ignore rules).

## Device configuration model

Evidence record of the `device_configuration_model` capability
(`computational_prototype`; design record: `docs/adr/0002-device-configuration-model.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- Validated frozen parameter objects (`PinchGeometry`, `FieldProgramme`,
  `OperationalLimits`, `DeviceConfiguration`) rejecting non-finite
  values, bound violations, torus inversions, and a positive edge
  toroidal field (the hard reversal invariant F ≤ 0) — every rejection
  branch is tested.
- Advisory consistency findings with documented bounds, reported and
  never clamped: the declared pinch parameter is cross-checked against
  the current-derived value via `B_theta(a) = mu0 I_p / (2 pi a)`
  (> 20 % relative mismatch is flagged), and a declared Θ below the
  Taylor-relaxation reversal threshold ~1.2 is flagged (Taylor, Phys.
  Rev. Lett. 33 (1974) 1139).
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.
- A data-only pin equality check binding the model to the SPO reactor
  registry version and digest declared in `reactor-domain.json`.

Bounded claims — what is NOT claimed:

- No parameter set describes, approximates, or validates any real
  machine; every exercised parameter set is a synthetic test fixture.
- The estimates are advisory regime checks, not equilibrium, transport,
  or stability results; no benchmark, dataset, solver, controller, or
  experimental correlation exists in this repository.

## Level-0 device physics

Evidence record of the `level0_device_physics` capability
(`computational_prototype`; design records:
`docs/adr/0005-level0-device-physics.md` and
`docs/adr/0006-shared-numerics-kernels.md`). Source: R. Paccagnella,
"Relaxation models for single helical reversed field pinch plasmas",
arXiv:1509.07307v2 (2015), eqs. 4–5 and the definitions of ``F`` and
``Theta`` (open access), taken in its single-region limit as the
Bessel-function model of the Taylor state; the Bessel functions and their
zeros through the pinned shared kernel library (NIST DLMF 10.2.2, 10.21;
OEIS A115368, A115369).

What is exercised, all under the 100 % statement-and-branch coverage gate
(`src/scpn_rfp_core/physics/`):

- **Numerics substrate** (`numerics.py`): ``J0`` and ``J1`` and their
  first zeros are the pinned shared kernel library's
  (`scpn-reactor-kernels`, kernel `numerics_bessel`; commit and inventory
  digest in `reactor-domain.json`, `kernel_library`); tests prove each
  wrapper returns the library value bit for bit, that the zeros are the
  library's constants with ``|J0(j_{0,1})|`` and ``|J1(j_{1,1})|`` at or
  below `1e-14`, and that a library refusal (argument outside ``|x| <= 8``
  or non-finite) is re-raised as `NumericsError` (a configuration error).
  The manifest block is validated field by field and a contract test
  proves the manifest, the `pyproject.toml` dependency, the installed
  library version, `rust/Cargo.toml`, `rust/Cargo.lock` and the CI install
  steps name one commit.
- **Relaxed state** (`relaxation.py`; eqs. 4–5): the reversal threshold
  ``Theta_rev = j_{0,1} / 2 = 1.2024...`` is the model's own identity and
  the configuration's advisory ``1.2`` is proven to be its rounding;
  ``F_bfm(Theta_rev) = 0`` exactly in double arithmetic; ``F_bfm -> 1`` as
  ``Theta -> 0`` with a deviation bounded by ``Theta^2`` at four decades;
  ``F_bfm`` is positive below the threshold, negative above it and
  decreasing towards the pole; the reversal radius exists exactly when
  ``Theta > Theta_rev`` and tends to ``a`` at the threshold; the product
  identity ``B0 J1(2 Theta) = <B_phi> Theta`` holds to `1e-15` relative;
  the model refuses ``Theta <= 0`` and ``Theta >= j_{1,1} / 2`` with the
  stated reason; the edge-field advisory reproduces the configuration's
  current cross-check.
- **Radial profile** (`profiles.py`): on the axis ``B_theta = 0``,
  ``B_phi = B0`` and ``q(0) = a / (Theta R0)`` without forming a quotient,
  reproduced by the series at ``r / a = 1e-7`` to `1e-12` relative; at the
  wall ``B_phi(a) / <B_phi> = F_bfm``, ``B_theta(a) = <B_phi> Theta`` and
  ``q(a) = F_bfm a / (Theta R0)`` to `1e-14`; ``q(a)`` and ``B_phi(a)``
  vanish at the threshold; the profile is monotone in ``B_phi`` and ``q``;
  a station outside ``[0, 1]`` is refused.
- A composed `Level0PhysicsRecord` (`scpn.rfp-level0-physics.v1` `1.0.0`)
  with canonical bytes, SHA-256 digest, fixed non-claims and two pinned
  reference digests (reversed and unreversed), built from the validated
  configuration and explicit `ModelInputs` (the radial stations); the
  record proves that every station beyond the reversal radius carries a
  reversed toroidal field and none does below the threshold.
- **Native parity**: the Rust crate in `rust/` mirrors every kernel with
  identical operation order on the library's Rust crate at the pinned
  commit; `tests/test_physics_native_parity.py` compares float64 bit
  patterns over a 112-point grid of the relaxed state (including the
  ``None`` reversal radius) and five stations each, plus the refusal
  paths of the bindings.
- **Benchmark**: `benchmarks/level0_physics.py` per the ecosystem
  benchmark standard; results in `docs/benchmarks.md` and the committed
  local artefact `benchmarks/results/level0_physics.local.json`.

Bounded claims — what is NOT claimed:

- Every number is a closed-form evaluation of the cylindrical
  Bessel-function relaxed state on a synthetic configuration; no
  equilibrium, transport, dynamo or stability equation is solved, and no
  eigenvalue problem exists here.
- The Bessel-function model is the fully relaxed single-region state; the
  source itself records that real reversed-field pinches depart from it
  (its ``F``–``Theta`` curve is steeper than the operational range), so the
  model's reversal parameter is reported against the declared one as an
  advisory, never as a prediction.
- The anchors are identities of the model and the printed zeros of the
  Bessel functions; they are not correlations with experimental data.
- No confinement, fusion power, gain or breakeven statement is made.
- No value describes, approximates or validates any real machine; the
  benchmark measures per-point evaluation cost of two implementations of
  the same closed forms, not physics.
- Maturity stays `computational_prototype`.

## Diagnostic and clock semantics

Evidence record of the `diagnostic_clock_semantics` capability
(`computational_prototype`; design record: `docs/adr/0003-diagnostic-clock-semantics.md`).

What is exercised, all under the 100 % statement-and-branch coverage gate:

- The nullable `timing_uncertainty_s` member, declared `null` on every
  channel because no event-relative candidate is applicable here; a
  non-null value is refused. This keeps the channel shape identical across
  the portfolio under envelope 1.1.0.
- Validated frozen declaration objects (`ClockModel`,
  `DiagnosticChannelPlan`, `DeferredCandidate`, `DiagnosticPlan`)
  rejecting catalogue misalignment: inapplicable candidates,
  inadmissible carriers, evidence-vocabulary mismatches, incompatible
  clock kinds, Nyquist violations, and incomplete candidate coverage —
  every rejection branch is tested.
- A data-only pin (`ObservabilityBinding`) to the SPO
  observability-profile catalogue release `1.0.0`
  (`d70c0de696534e5a77066ef8420cf7ca17bc4d7321984b0ac83523dbc1dce609`),
  bound in turn to reactor registry `1.0.0`; a plan pinned to any other
  release is rejected.
- A reference plan mirroring canonical practice with synthetic
  declarations: flux loops, Rogowski coil, toroidal probe array, synthetic oscillator, each bound to its clock domain.
- A documented advisory band check with its source stated in the code:
  RFP tearing and relaxation fluctuations in the 1–500 kHz scale (Ortolani and Schnack 1993); findings are reported, never clamped.
- Canonical serialisation (sorted keys, NaN/infinity rejected on both
  emit and parse), SHA-256 digest identity, and a strict round-trip
  parser that refuses unknown fields.

Bounded claims — what is NOT claimed:

- No channel describes a real diagnostic, measurement, or facility;
  every plan is a synthetic declaration of HOW evidence slots would be
  bound, marked `synthetic=True` by hard invariant.
- No SPO semantic-profile ingress is declared; the profile registry
  `ingress_state` for this device family remains `not_declared`, and
  no adapter, producer, or handoff exists in this repository.

### Portable plan envelope

The `diagnostic_clock_semantics` capability additionally exercises a
producer-owned portable envelope
(`src/scpn_rfp_core/plan_envelope.py`,
`scpn.reactor-diagnostic-plan-envelope.v1` version `1.0.0`): one
canonically serialised object carrying the exact project identity and
owned configurations, the capability and its maturity, the
synthetic/review-only/non-actuating statements, both SPO registry pins,
the SHA-256 digest of the inner canonical plan, the producer revision,
and fixed no-observation/no-control non-claims. The committed immutable
fixture (`tests/data/plan_envelope_fixture.json`, byte hash pinned in
the tests) is verified together with positive, tamper, wrong-project,
wrong-configuration, registry-drift, duplicate-member, and non-finite
rejection paths, all under the 100 % coverage gate. The envelope claims
nothing beyond the enveloped synthetic declaration.

### Typed frames, clock relations, and acquisition geometry

The deepened model adds typed reference frames (per-repository allowed
`FrameKind` subset; every noncyclic `coordinate_frame` binding must
reference a declared frame), clock synchronisation relations
(synthetic offset/uncertainty BOUNDS between declared non-simulation
clocks with an explicit method statement — no correlation evidence is
claimed and no clock is mapped to physical wall time), and per-channel
acquisition windows and element counts with device-cited advisory
scales. Both decoders are hardened per the SPO intake architecture:
recursive exact-key refusal in every nested entry, duplicate-member
refusal, and byte-canonical refusal (a document that is not exactly
canonical bytes is rejected). The envelope is `1.1.0`, adding
`manifest_sha256` — the SHA-256 of the committed canonical
`reactor-domain.json` — verified in tests against the committed file.
All declarations remain synthetic; nothing here observes or controls
anything.

### Signal inventories, frame transformations, and clock topology

The depth slice (envelope `1.2.0`; a `1.1.0` document is refused by the
`1.2.0` codec and vice versa — no defaults, no cross-version coercion;
`1.1.0` remains historical custody at the consumer) adds three typed
declaration surfaces, every branch under the 100 % statement-and-branch
gate:

- A per-channel **signal inventory** (`SignalDeclaration`: identifier,
  quantity, unit, role, description). Hard rules: non-empty, unique and
  sorted; exactly one `carrier`; no `timing_marker` (no
  event-relative candidate is applicable); numerical-only
  channels declare a single `phase`/`rad` carrier. Quantity and unit are
  declared tokens — no SI or UCUM validation is performed or claimed —
  and no declaration creates or overrides a candidate, carrier,
  observation, or phase: the candidate profile stays authoritative. An
  advisory flags a multi-element cyclic array without an amplitude
  signal.
- **Frame transformations** (`FrameTransformation`) between declared
  frames: kind admissibility fixed by frame-kind pair (`flux_mapping`
  for machine↔flux, flux↔Boozer, field-line↔machine; `projection` for
  blanket↔machine; `rigid` for chamber↔beamline), `equilibrium_dependent`
  exactly for flux mappings, at most one transformation per frame pair,
  sorted by source then target, and — with two or more frames — a
  connected transformation graph. Methods are declarations;
  `evidence_claimed` is always `False`.
- A **clock topology** (`ClockDomain`, `ClockTopology`): every physical
  clock in exactly one domain, the simulation clock in none; a domain
  holding a facility clock is rooted there, otherwise at its shot-event
  epoch; every non-root member declares a relation to its root; every
  non-reference root declares a relation to the reference root (star);
  relations must not form a cycle. The reference plan declares one
  domain (`clk_facility` root, `clk_shot` member); multi-domain rules
  are exercised by test-constructed plans. Scopes are declarations;
  `mapping_state` stays `unmapped`.

## Device 3D model

Evidence record of the `device_3d_model` capability
(`computational_prototype`; design record: `docs/adr/0007-device-3d-and-cad-models.md`;
consumer contract: `docs/DEVICE_3D_MODEL_CONTRACT.md`).

The unit circle, the tessellation primitives, the closed-mesh contract and
the STL/GLB serialisers are consumed from the shared kernel library
`scpn-reactor-kernels`, pinned in the manifest (`kernel_library`: commit
object and kernel-inventory digest) and in `pyproject.toml`; their evidence
is the library's, at its `VALIDATION.md#geometry-kernels`. What this
repository exercises, all under the 100 % statement-and-branch coverage
gate (`src/scpn_rfp_core/geometry/`):

- **Device geometry** (`DeviceGeometry`): four SI parameters of the
  envelope of the cylindrical periodic equivalent (vessel wall, conducting
  shell, winding gap and thickness) with fail-closed positivity, canonical
  bytes, SHA-256 digest and a strict parser refusing unknown fields and
  non-finite literals; every rejection branch is tested. The layout
  follows the relaxation literature's geometry (Paccagnella 2015, on
  file: the ideal conducting shell surrounding the plasma, bounded at the
  wall radius). No dimension of any device is used.
- **Anchor**: the geometry tier carries a second fixture pair built from
  the values that source prints — the aspect ratio `R/a = 5` of its single
  helical eigenstates (Fig. 1, 3 and 8) and the reversal parameter
  `F = -0.05` it calls the shallow reversed case. That source works
  throughout in units normalised to the plasma minor radius and prints no
  length in metres, so the anchored quantities are dimensionless; the
  absolute radii that realise the ratio, the pinch parameter, the field
  amplitude, the operational limits and every envelope thickness are
  declared and said to be declared. Both tiers are checked against it: the
  tessellated plasma column and the B-rep solid each return the printed
  ratio from their own bounding box, the tessellated one exactly.
  Reproducing a printed value is an anchor, never a claim about a machine.
- **Device model** (`DeviceModel3D`, `scpn.rfp-3d-model.v1` `1.0.0`):
  four bodies in the fixed order (plasma column, vacuum vessel,
  conducting shell, toroidal-field winding) nested radially over the
  periodic length `2 pi R0`; convergence of every body volume to its
  analytic cylinder or tube; the fixed body inventory; determinism (two
  builds equal, digests equal); canonical bytes and one pinned reference
  digest (segments = 8) as an immutability fixture.
- **Exports**: the device-side provenance record (`glb_extras`) is exactly
  what the library's GLB carries as document `extras`; the bytes are
  proven identical to the library serialisers called directly; the binary
  STL and glTF 2.0 binary layouts are read back with minimal
  specification-level readers; determinism of the bytes; the file writers.
- **Native parity**: `tests/test_geometry_native_parity.py` builds the
  four device bodies on the library's Python floor and compares float64
  bit patterns of every vertex coordinate, the face index streams, the
  signed volume and the surface area against the library's native module
  (`scpn_reactor_kernels_native`); the consumer inherits the library's
  parity rather than re-proving the kernels. The crate in `rust/` carries
  physics only.
- **Benchmark**: `benchmarks/device_model_3d.py` per the ecosystem
  benchmark standard, measuring the library's Python floor (through the
  validated device build) against the library's native kernels; results in
  `docs/benchmarks.md` and the committed local artefact
  `benchmarks/results/device_model_3d.local.json`.

Bounded claims — what is NOT claimed:

- The cylindrical periodic equivalent of the toroidal device is the
  modelled object: the end caps of the cylinder primitives are an
  artefact, and the toroidal curvature, the poloidal coil rings and the
  shell penetrations are not modelled at this tier.
- The plasma body is the Bessel-function-model domain of the level-0
  physics, not an equilibrium boundary of the torus.
- No material property, load, field or neutronic quantity is carried or
  implied by any body, role or material token.
- No value describes, approximates or validates any real machine; the
  benchmark measures tessellation cost, not physics.
- Exporting STL and GLB files does not federate, present or gate this
  repository anywhere; the portfolio layer keeps that authority.
- Maturity stays `computational_prototype`.

## Device CAD model

Evidence record of the `device_cad_model` capability
(`computational_prototype`; design record: `docs/adr/0007-device-3d-and-cad-models.md`;
the STEP surface of the consumer contract `docs/DEVICE_3D_MODEL_CONTRACT.md`).

The B-rep, STEP, faceting and evidence kernels are the shared library's
`cad` group (the same `kernel_library` pin; the dependency's optional
`cad` extra); their evidence is the library's, at its
`VALIDATION.md#cad-kernels`. What this repository exercises, all under the
100 % statement-and-branch coverage gate (`src/scpn_rfp_core/geometry/cad.py`,
`tests/test_geometry_cad.py`):

- **Same design, same bodies**: the four B-rep bodies are built at the
  names, roles, material tokens and extents of the tier-G1 model, proven
  by an inventory comparison against `build_device_model`.
- **B-rep measures against the analytic closed forms**: every body's
  OpenCASCADE volume and surface area agree with the analytic cylinder or
  tube forms within the library's measure tolerance `1e-9` relative,
  fail-closed by construction of the record.
- **Faceting evidence**: every body faceted at the declared deflections
  (linear `1e-4 m`, angular `0.1 rad`) validates as a closed,
  outward-oriented mesh of the G1 contract; the faceted volume deficit
  against the analytic form stays within the declared bound `2 d / r`, and
  the faceted volume agrees with the G1 reference mesh at the declared
  eight segments within the exact polygon-deficit bound.
- **Placement identities**: the four bodies nest radially (plasma edge,
  vessel, shell, winding) and every body spans the full periodic length,
  read from the B-rep bounding boxes.
- **STEP export**: the written file is exactly the byte string whose
  SHA-256 the record carries as `step_sha256`; two builds of the same
  design are byte-identical in the pinned back-end environment; a
  re-import in a separate reader process reproduces every body volume
  within `1e-9`.
- **Record**: `scpn.rfp-cad-model.v1` `1.0.0` with canonical bytes,
  SHA-256 digest and fixed non-claims; one pinned reference digest in the
  reference back-end environment (cadquery 2.8.0, OCP 7.9.3.1) as an
  immutability fixture; invalid segments, invalid deflections, a foreign
  body inventory, a foreign manifest schema and a malformed STEP digest
  are refused.
- **Benchmark**: `benchmarks/device_model_cad.py` per the ecosystem
  benchmark standard (build, export, facet and full record build);
  results in `docs/benchmarks.md` and the committed local artefact
  `benchmarks/results/device_model_cad.local.json`.

Bounded claims — what is NOT claimed:

- The bodies are exact analytic solids of a synthetic design built by a
  pinned third-party kernel: not an engineering model, no equilibrium
  boundary, no manufacturing drawing; the cylindrical periodic equivalent
  is the modelled object (see the tier-G1 non-claims).
- Determinism of the STEP bytes is claimed within the pinned back-end
  environment only; identity across OpenCASCADE or gmsh versions is not
  claimed, and a back-end bump re-pins the record digest as a governed
  data change.
- No value describes, approximates or validates any real machine; the
  benchmark measures build, export and faceting cost, not physics.
- Maturity stays `computational_prototype`.
