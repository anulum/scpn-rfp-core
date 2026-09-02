# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — native parity tests

"""Bit-exact parity between the Python floor and the native kernels.

The native module is an optional build (rust/, distribution
scpn-rfp-native) whose Bessel functions are the shared kernel library's
Rust crate at the pinned commit; these tests are skipped hermetically
when it is absent and compare float64 bit patterns, never tolerances,
when present. All parameter sets are synthetic fixtures.
"""

from __future__ import annotations

import pytest

from physics_fixtures import bits, configuration
from scpn_rfp_core.physics import (
    BFM_MAX_PINCH_PARAMETER,
    BFM_REVERSAL_PINCH_PARAMETER,
    axis_field,
    bfm_reversal_parameter,
    radial_station,
    relaxed_state,
)

native = pytest.importorskip("scpn_rfp_native")

THETAS = [0.3, 1.0, 1.2, BFM_REVERSAL_PINCH_PARAMETER, 1.4, 1.6, 1.85]
GRID = [
    (theta, minor, major, average, current)
    for theta in THETAS
    for minor in (0.3, 0.5)
    for major in (1.2, 2.0)
    for average in (0.1, 0.25)
    for current in (0.4, 1.0)
]


def _bits(values: tuple[float, ...]) -> list[bytes]:
    return [bits(value) for value in values]


@pytest.mark.parametrize("theta", THETAS)
def test_reversal_parameter_is_bit_exact(theta: float) -> None:
    """F_bfm agrees bit for bit at every grid pinch parameter."""
    assert bits(native.bfm_reversal_parameter(theta)) == bits(
        bfm_reversal_parameter(theta)
    )


@pytest.mark.parametrize(("theta", "minor", "major", "average", "current"), GRID)
def test_relaxed_state_and_profile_are_bit_exact(
    theta: float, minor: float, major: float, average: float, current: float
) -> None:
    """Every scalar of the state and of five stations agrees bit for bit."""
    config = configuration(
        pinch_parameter=theta,
        plasma_current_ma=current,
        minor_radius_m=minor,
        major_radius_m=major,
        average_toroidal_field_t=average,
    )
    floor = relaxed_state(config)
    got = native.relaxed_state(minor, theta, average, -0.2, current)
    assert _bits(got[:6]) == _bits(
        (
            floor.pinch_parameter,
            floor.force_free_parameter_per_m,
            floor.axis_field_t,
            floor.bfm_reversal_parameter,
            floor.declared_reversal_parameter,
            floor.reversal_mismatch,
        )
    )
    assert got[6] is floor.reversed
    if floor.reversal_radius_m is None:
        assert got[7] is None
    else:
        assert got[7] is not None
        assert bits(got[7]) == bits(floor.reversal_radius_m)
    assert _bits(got[8:]) == _bits(
        (
            floor.edge_poloidal_field_bfm_t,
            floor.edge_poloidal_field_current_t,
            floor.edge_field_relative_mismatch,
        )
    )
    b0 = axis_field(average, theta)
    for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
        station = radial_station(fraction, minor, major, theta, b0)
        native_station = native.radial_station(fraction, minor, major, theta, b0)
        assert _bits(native_station) == _bits(
            (
                station.fraction,
                station.radius_m,
                station.toroidal_field_t,
                station.poloidal_field_t,
                station.safety_factor,
            )
        )


def test_native_refusals_mirror_the_floor() -> None:
    """The model's domain refusals and the library's are ValueErrors."""
    with pytest.raises(ValueError, match="j_1,1 / 2"):
        native.bfm_reversal_parameter(BFM_MAX_PINCH_PARAMETER)
    with pytest.raises(ValueError, match="strictly positive"):
        native.relaxed_state(0.5, 0.0, 0.25, -0.2, 1.0)
    with pytest.raises(ValueError, match="finite"):
        native.relaxed_state(0.5, float("nan"), 0.25, -0.2, 1.0)
    with pytest.raises(ValueError, match="fraction"):
        native.radial_station(1.5, 0.5, 2.0, 1.6, 1.0)
    with pytest.raises(ValueError, match="finite"):
        native.radial_station(float("inf"), 0.5, 2.0, 1.6, 1.0)
