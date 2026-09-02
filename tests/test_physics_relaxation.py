# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — relaxed-state tests

"""The Bessel-function model: threshold identity, limits, signs, refusals."""

from __future__ import annotations

import math

import pytest

from physics_fixtures import configuration
from scpn_rfp_core.configuration import TAYLOR_RELAXATION_MIN_THETA
from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.physics import (
    BESSEL_J0_FIRST_ZERO,
    BESSEL_J1_FIRST_ZERO,
    BFM_MAX_PINCH_PARAMETER,
    BFM_REVERSAL_PINCH_PARAMETER,
    axis_field,
    bessel_j1,
    bfm_reversal_parameter,
    force_free_parameter,
    relaxed_state,
    require_bfm_pinch_parameter,
    reversal_radius,
)


def test_reversal_threshold_is_half_the_first_zero_of_j0() -> None:
    """Theta_rev = j_{0,1} / 2; the configuration's 1.2 is its rounding; F = 0 there."""
    assert BFM_REVERSAL_PINCH_PARAMETER == BESSEL_J0_FIRST_ZERO / 2.0
    assert round(BFM_REVERSAL_PINCH_PARAMETER, 1) == TAYLOR_RELAXATION_MIN_THETA
    assert 1.20 < BFM_REVERSAL_PINCH_PARAMETER < 1.21
    assert abs(bfm_reversal_parameter(BFM_REVERSAL_PINCH_PARAMETER)) <= 1.0e-14
    assert BFM_MAX_PINCH_PARAMETER == BESSEL_J1_FIRST_ZERO / 2.0
    assert BFM_REVERSAL_PINCH_PARAMETER < BFM_MAX_PINCH_PARAMETER < 4.0


@pytest.mark.parametrize("theta", [1.0e-3, 1.0e-4, 1.0e-5, 1.0e-6])
def test_reversal_parameter_tends_to_one_at_small_theta(theta: float) -> None:
    """F_bfm -> 1 as Theta -> 0 (the deviation is of order Theta^2 / 2)."""
    deviation = abs(bfm_reversal_parameter(theta) - 1.0)
    assert deviation <= theta * theta
    assert deviation > 0.0 or theta < 1.0e-5


def test_reversal_parameter_sign_follows_the_threshold() -> None:
    """F_bfm > 0 below Theta_rev, < 0 above it, decreasing towards the pole."""
    below = bfm_reversal_parameter(1.0)
    above = bfm_reversal_parameter(1.4)
    deeper = bfm_reversal_parameter(1.6)
    near_pole = bfm_reversal_parameter(1.9)
    assert 0.0 < below < 1.0
    assert deeper < above < 0.0
    assert near_pole < deeper
    assert bfm_reversal_parameter(1.2) > 0.0
    assert (
        bfm_reversal_parameter(math.nextafter(BFM_REVERSAL_PINCH_PARAMETER, 2.0)) < 0.0
    )


def test_reversal_radius_exists_only_beyond_the_threshold() -> None:
    """r_rev = j_{0,1} / mu inside the plasma exactly when Theta > Theta_rev."""
    assert reversal_radius(1.0, 0.5) is None
    assert reversal_radius(BFM_REVERSAL_PINCH_PARAMETER, 0.5) is None
    radius = reversal_radius(1.6, 0.5)
    assert radius is not None
    assert radius == BESSEL_J0_FIRST_ZERO / force_free_parameter(1.6, 0.5)
    assert 0.0 < radius < 0.5
    just_above = reversal_radius(math.nextafter(BFM_REVERSAL_PINCH_PARAMETER, 2.0), 0.5)
    assert just_above is not None
    assert math.isclose(just_above, 0.5, rel_tol=1.0e-15)


def test_force_free_parameter_and_axis_field() -> None:
    """The force-free parameter, the axis field and their product identity."""
    assert force_free_parameter(1.6, 0.5) == 6.4
    b0 = axis_field(0.25, 1.6)
    assert b0 > 0.25
    assert math.isclose(b0 * bessel_j1(3.2), 0.25 * 1.6, rel_tol=1.0e-15)


@pytest.mark.parametrize(
    ("theta", "fragment"),
    [
        (0.0, "strictly positive"),
        (-1.0, "strictly positive"),
        (math.nan, "finite"),
        (BFM_MAX_PINCH_PARAMETER, "j_1,1 / 2"),
        (2.0, "j_1,1 / 2"),
    ],
)
def test_pinch_parameter_outside_the_model_is_refused(
    theta: float, fragment: str
) -> None:
    """The model refuses Theta <= 0 and Theta >= j_{1,1} / 2, never clamps."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        require_bfm_pinch_parameter(theta)
    with pytest.raises(DeviceConfigurationError, match=fragment):
        bfm_reversal_parameter(theta)
    assert require_bfm_pinch_parameter(1.6) == 1.6


def test_relaxed_state_of_a_configuration() -> None:
    """The state carries the model quantities and the advisory comparisons."""
    state = relaxed_state(configuration())
    assert state.pinch_parameter == 1.6
    assert state.force_free_parameter_per_m == 6.4
    assert state.axis_field_t == axis_field(0.25, 1.6)
    assert state.bfm_reversal_parameter == bfm_reversal_parameter(1.6)
    assert state.declared_reversal_parameter == -0.2
    assert state.reversal_mismatch == -0.2 - state.bfm_reversal_parameter
    assert state.reversed is True
    assert state.reversal_radius_m == reversal_radius(1.6, 0.5)
    assert math.isclose(state.edge_poloidal_field_bfm_t, 0.4, rel_tol=1.0e-15)
    assert state.edge_poloidal_field_current_t == 0.4
    assert abs(state.edge_field_relative_mismatch) < 1.0e-15
    assert set(state.to_record()) == {
        "pinch_parameter",
        "force_free_parameter_per_m",
        "axis_field_t",
        "bfm_reversal_parameter",
        "declared_reversal_parameter",
        "reversal_mismatch",
        "reversed",
        "reversal_radius_m",
        "edge_poloidal_field_bfm_t",
        "edge_poloidal_field_current_t",
        "edge_field_relative_mismatch",
    }


def test_relaxed_state_below_the_threshold_and_with_a_current_mismatch() -> None:
    """No reversal surface below Theta_rev; the edge advisory tracks the current."""
    state = relaxed_state(configuration(pinch_parameter=1.0, plasma_current_ma=0.5))
    assert state.reversed is False
    assert state.reversal_radius_m is None
    assert state.to_record()["reversal_radius_m"] is None
    assert state.bfm_reversal_parameter > 0.0
    assert math.isclose(state.edge_poloidal_field_bfm_t, 0.25, rel_tol=1.0e-15)
    assert state.edge_poloidal_field_current_t == 0.2
    assert math.isclose(state.edge_field_relative_mismatch, -0.2, rel_tol=1.0e-14)
    derived = configuration(pinch_parameter=1.0, plasma_current_ma=0.5)
    assert math.isclose(
        1.0 + state.edge_field_relative_mismatch,
        derived.derived_pinch_parameter() / 1.0,
        rel_tol=1.0e-14,
    )


def test_relaxed_state_refuses_a_configuration_beyond_the_pole() -> None:
    """A declared Theta at or beyond j_{1,1} / 2 is refused with the reason."""
    with pytest.raises(DeviceConfigurationError, match="average toroidal field"):
        relaxed_state(configuration(pinch_parameter=2.5))
