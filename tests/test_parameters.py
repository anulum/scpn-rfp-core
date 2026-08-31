# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — parameter model tests

"""Every validation branch of the reversed-field-pinch parameter model.

All parameter sets in this module are synthetic fixtures; none describes
any real machine.
"""

from __future__ import annotations

import math

import pytest

from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.parameters import (
    FieldProgramme,
    OperationalLimits,
    PinchGeometry,
    require_finite,
    require_positive,
)


def synthetic_geometry(**overrides: float) -> PinchGeometry:
    """Build a valid synthetic geometry with optional field overrides."""
    values: dict[str, float] = {
        "major_radius_m": 2.0,
        "minor_radius_m": 0.5,
    }
    values.update(overrides)
    return PinchGeometry(**values)


def synthetic_fields(**overrides: float) -> FieldProgramme:
    """Build a valid synthetic field programme with optional overrides."""
    values: dict[str, float] = {
        "reversal_parameter": -0.2,
        "pinch_parameter": 1.6,
        "average_toroidal_field_t": 0.25,
    }
    values.update(overrides)
    return FieldProgramme(**values)


def synthetic_limits(**overrides: float) -> OperationalLimits:
    """Build valid synthetic limits with optional field overrides."""
    values: dict[str, float] = {
        "plasma_current_ma": 1.0,
        "flat_top_duration_s": 0.1,
    }
    values.update(overrides)
    return OperationalLimits(**values)


def test_valid_geometry_and_aspect_ratio() -> None:
    """A valid pinch torus constructs and derives its aspect ratio."""
    assert synthetic_geometry().aspect_ratio == pytest.approx(4.0)


def test_require_finite_accepts_and_rejects() -> None:
    """The finite guard returns the value and rejects NaN and infinity."""
    assert require_finite("x", 1.5) == 1.5
    for bad in (math.nan, math.inf, -math.inf):
        with pytest.raises(DeviceConfigurationError, match="x: must be finite"):
            require_finite("x", bad)


def test_require_positive_accepts_and_rejects() -> None:
    """The positive guard returns the value and rejects zero and below."""
    assert require_positive("x", 0.1) == 0.1
    for bad in (0.0, -2.0):
        with pytest.raises(DeviceConfigurationError, match="strictly positive"):
            require_positive("x", bad)
    with pytest.raises(DeviceConfigurationError, match="must be finite"):
        require_positive("x", math.nan)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"major_radius_m": 0.0}, "major_radius_m"),
        ({"minor_radius_m": -1.0}, "minor_radius_m"),
        ({"minor_radius_m": 2.0}, "strictly smaller than"),
        ({"minor_radius_m": 3.0}, "strictly smaller than"),
    ],
)
def test_invalid_geometry_is_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each geometric invariant violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_geometry(**overrides)


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"reversal_parameter": 0.1}, "reversal_parameter"),
        ({"reversal_parameter": -2.1}, "reversal_parameter"),
        ({"reversal_parameter": math.nan}, "reversal_parameter"),
        ({"pinch_parameter": 0.0}, "pinch_parameter"),
        ({"pinch_parameter": 5.1}, "pinch_parameter"),
        ({"pinch_parameter": math.nan}, "pinch_parameter"),
        ({"average_toroidal_field_t": 0.0}, "average_toroidal_field_t"),
    ],
)
def test_invalid_field_programme_is_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each field-programme violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_fields(**overrides)


def test_reversal_bounds_are_inclusive() -> None:
    """Both reversal-parameter model bounds are inclusive."""
    assert synthetic_fields(reversal_parameter=0.0).reversal_parameter == 0.0
    assert synthetic_fields(reversal_parameter=-2.0).reversal_parameter == -2.0


def test_pinch_bound_is_inclusive_at_five() -> None:
    """The pinch-parameter upper model bound is inclusive."""
    assert synthetic_fields(pinch_parameter=5.0).pinch_parameter == 5.0


def test_valid_limits_and_edge_poloidal_field() -> None:
    """Limits construct and the edge poloidal field follows the formula."""
    limits = synthetic_limits()
    assert limits.flat_top_duration_s == 0.1
    field = limits.edge_poloidal_field_t(synthetic_geometry())
    assert field == pytest.approx(0.2 * 1.0 / 0.5)


def test_zero_flat_top_is_valid() -> None:
    """A zero flat-top duration is representable."""
    assert synthetic_limits(flat_top_duration_s=0.0).flat_top_duration_s == 0.0


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"plasma_current_ma": 0.0}, "plasma_current_ma"),
        ({"flat_top_duration_s": -1.0}, "flat_top_duration_s"),
        ({"flat_top_duration_s": math.inf}, "flat_top_duration_s"),
    ],
)
def test_invalid_limits_are_rejected(
    overrides: dict[str, float], fragment: str
) -> None:
    """Each limit violation is rejected with its field name."""
    with pytest.raises(DeviceConfigurationError, match=fragment):
        synthetic_limits(**overrides)
