<!--
SPDX-License-Identifier: AGPL-3.0-or-later
Commercial license available
© Concepts 1996–2026 Miroslav Šotek. All rights reserved.
© Code 2020–2026 Miroslav Šotek. All rights reserved.
ORCID: 0009-0009-3560-0851
Contact: www.anulum.li | protoscience@anulum.li
SCPN RFP Core — ADR 0006
-->

# ADR 0006 — Consume the shared numerics kernels: the library pin

Status: accepted (2026-09-02). Companion of ADR 0005.

## Context

The level-0 models need the Bessel functions ``J0`` and ``J1`` and their
first positive zeros. The family's bit-exact rule admits only ``+ - * /``
and ``sqrt`` on the Python floor plus vendored deterministic
implementations of anything else, mirrored operation for operation in the
native crate; platform special functions are outside the rule. The shared
kernel library of the research group, `scpn-reactor-kernels`, carries
exactly those kernels (its ADR 0005, kernel `numerics_bessel`: the NIST
DLMF 10.2.2 ascending series in Horner form on ``|x| <= 8``, with the
zeros as the correctly rounded doubles of OEIS A115368 and A115369) with a
Rust crate proven bit-exact against its Python floor. Carrying a copy here
would create the drift the library exists to prevent.

## Decision

1. The repository declares `scpn-reactor-kernels` as its one runtime
   dependency, pinned to a commit object of the library's public
   repository (`pyproject.toml`, `dependencies`); no release of the
   library exists yet, so the commit is the exact identity.
2. The manifest carries the pin as the optional `kernel_library` block
   (distribution, version, `source_commit`, `inventory_sha256` of the
   library's generated `kernel-inventory.json` at that commit, and the
   sorted identifiers of the kernels consumed: `numerics_bessel`). The
   validator enforces every field; a contract test proves that the
   manifest, the `pyproject.toml` dependency, the installed package
   version, the native crate's `Cargo.toml` and `Cargo.lock` and the CI
   install steps name one commit.
3. `src/scpn_rfp_core/physics/numerics.py` is the only import site of the
   library: it re-raises the library's domain refusal as the device
   `NumericsError` (a `DeviceConfigurationError`) with the library's
   message, so the consumer's error contract stays device-typed, and it
   re-exports the library's zero constants unchanged.
4. The native crate `scpn-rfp-rs` depends on the library's Rust crate
   `scpn-reactor-kernels-rs` as a git dependency at the same commit (no
   default features); `Cargo.lock` records the source, and the hosted
   `rust` job fetches it. Parity is proven between this repository's
   Python floor and its own native module; the library's own parity
   covers the kernels themselves.
5. The manifest adds the excluded domain
   `shared_physics_geometry_and_numerics_kernels` owned by
   `SCPN-REACTOR-KERNELS`, mirroring the library's exclusion of device
   truth.

## Consequences

A change of the library pin is a governed data change of this repository
(manifest, descriptor and inventory regeneration, envelope fixture re-pin,
Cargo re-lock, SPO re-intake). The library's consumer table gains this
repository as its fourth consumer and the first of the Bessel kernel;
because that entry changes the library's inventory, the digest pinned
here names the inventory at the pinned commit, never the one that lists
this consumer (the library's ADR 0004 fixes the same rule).
