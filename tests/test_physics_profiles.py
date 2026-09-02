# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — radial profile tests

"""Field profile, safety factor, the axis limit and the wall identities."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import configuration
from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.physics import (
    BFM_REVERSAL_PINCH_PARAMETER,
    axis_field,
    axis_safety_factor,
    bfm_reversal_parameter,
    radial_profile,
    radial_station,
    require_station,
)


def test_axis_station_carries_the_series_limit() -> None:
    """At r = 0: B_phi = B0, B_theta = 0, q(0) = a / (Theta R0) without a quotient."""
    b0 = axis_field(0.25, 1.6)
    axis = radial_station(0.0, 0.5, 2.0, 1.6, b0)
    assert axis.radius_m == 0.0
    assert axis.toroidal_field_t == b0
    assert axis.poloidal_field_t == 0.0
    assert axis.safety_factor == axis_safety_factor(0.5, 2.0, 1.6) == 0.5 / 3.2
    near = radial_station(1.0e-7, 0.5, 2.0, 1.6, b0)
    assert math.isclose(near.safety_factor, axis.safety_factor, rel_tol=1.0e-12)
    assert set(axis.to_record()) == {
        "fraction",
        "radius_m",
        "toroidal_field_t",
        "poloidal_field_t",
        "safety_factor",
    }


def test_wall_station_reproduces_f_and_theta() -> None:
    """B_phi(a) / <B> = F_bfm, B_theta(a) = <B> Theta, q(a) = F_bfm a / (Theta R0)."""
    b0 = axis_field(0.25, 1.6)
    wall = radial_station(1.0, 0.5, 2.0, 1.6, b0)
    f_bfm = bfm_reversal_parameter(1.6)
    assert wall.radius_m == 0.5
    assert math.isclose(wall.toroidal_field_t / 0.25, f_bfm, rel_tol=1.0e-14)
    assert math.isclose(wall.poloidal_field_t, 0.25 * 1.6, rel_tol=1.0e-15)
    assert math.isclose(wall.safety_factor, f_bfm * 0.5 / (1.6 * 2.0), rel_tol=1.0e-14)
    assert wall.toroidal_field_t < 0.0
    assert wall.safety_factor < 0.0


def test_safety_factor_vanishes_at_the_wall_exactly_at_the_threshold() -> None:
    """q(a) = 0 where the toroidal field reverses at the wall."""
    theta = BFM_REVERSAL_PINCH_PARAMETER
    wall = radial_station(1.0, 0.5, 2.0, theta, axis_field(0.25, theta))
    assert abs(wall.safety_factor) <= 1.0e-14
    assert abs(wall.toroidal_field_t) <= 1.0e-14


def test_profile_is_monotone_in_the_expected_sense() -> None:
    """B_phi decreases from the axis to the wall; q decreases through zero."""
    config = configuration()
    profile = radial_profile(config, axis_field(0.25, 1.6), (0.0, 0.25, 0.5, 0.75, 1.0))
    assert [station.fraction for station in profile] == [0.0, 0.25, 0.5, 0.75, 1.0]
    toroidal = [station.toroidal_field_t for station in profile]
    assert toroidal == sorted(toroidal, reverse=True)
    safety = [station.safety_factor for station in profile]
    assert safety == sorted(safety, reverse=True)
    assert safety[0] > 0.0 > safety[-1]
    assert all(station.poloidal_field_t > 0.0 for station in profile[1:])
    assert radial_profile(config, axis_field(0.25, 1.6), ()) == ()


@pytest.mark.parametrize("fraction", [-0.1, 1.1, math.nan, math.inf])
def test_station_outside_the_plasma_is_refused(fraction: float) -> None:
    """A station is r / a within [0, 1]; anything else is refused."""
    with pytest.raises(DeviceConfigurationError, match="fraction"):
        radial_station(fraction, 0.5, 2.0, 1.6, 1.0)
    with pytest.raises(DeviceConfigurationError, match="station"):
        require_station("station", fraction)
    assert require_station("station", 0.5) == 0.5
