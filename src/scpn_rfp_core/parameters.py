# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — reversed-field-pinch parameter model

"""Validated parameter objects of a reversed-field-pinch configuration.

The model bounds documented here are modelling-domain bounds of this
repository, not claims about any real machine: the reversal parameter is
accepted in ``[-2, 0]`` (a non-positive edge toroidal field is the
defining property of the class) and the pinch parameter in ``(0, 5]``,
which covers the published reversed-field-pinch operating space while
rejecting unphysical inputs.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Final

from scpn_rfp_core.errors import DeviceConfigurationError

REVERSAL_PARAMETER_BOUNDS: Final = (-2.0, 0.0)
PINCH_PARAMETER_BOUNDS: Final = (0.0, 5.0)


def require_finite(name: str, value: float) -> float:
    """Return ``value`` when finite, otherwise fail closed.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is NaN or infinite; non-finite input is rejected,
        never clamped.
    """
    if not math.isfinite(value):
        raise DeviceConfigurationError(f"{name}: must be finite, got {value!r}")
    return value


def require_positive(name: str, value: float) -> float:
    """Return ``value`` when finite and strictly positive.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    value
        Value under validation.

    Returns
    -------
    float
        The validated value.

    Raises
    ------
    DeviceConfigurationError
        If ``value`` is non-finite or not strictly positive.
    """
    require_finite(name, value)
    if value <= 0.0:
        raise DeviceConfigurationError(
            f"{name}: must be strictly positive, got {value!r}"
        )
    return value


@dataclass(frozen=True, slots=True)
class PinchGeometry:
    """Toroidal pinch geometry parameters.

    Parameters
    ----------
    major_radius_m
        Plasma major radius ``R0`` in metres; strictly positive.
    minor_radius_m
        Plasma minor radius ``a`` in metres; strictly positive and
        strictly smaller than ``major_radius_m``.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or outside its model bound.
    """

    major_radius_m: float
    minor_radius_m: float

    def __post_init__(self) -> None:
        """Validate every geometric invariant of the torus.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or outside its model bound.
        """
        require_positive("major_radius_m", self.major_radius_m)
        require_positive("minor_radius_m", self.minor_radius_m)
        if self.minor_radius_m >= self.major_radius_m:
            raise DeviceConfigurationError(
                "minor_radius_m: must be strictly smaller than major_radius_m "
                f"({self.minor_radius_m!r} >= {self.major_radius_m!r})"
            )

    @property
    def aspect_ratio(self) -> float:
        """Aspect ratio ``A = R0 / a`` of the validated torus.

        Returns
        -------
        float
            Ratio of major to minor radius; always greater than one.
        """
        return self.major_radius_m / self.minor_radius_m


@dataclass(frozen=True, slots=True)
class FieldProgramme:
    """Declared F/Θ field programme of a reversed-field pinch.

    Parameters
    ----------
    reversal_parameter
        ``F = B_phi(a) / <B_phi>``; accepted in ``[-2, 0]`` — the edge
        toroidal field must not be positive in this configuration class.
    pinch_parameter
        ``Theta = B_theta(a) / <B_phi>``; accepted in ``(0, 5]``.
    average_toroidal_field_t
        Volume-averaged toroidal field ``<B_phi>`` in tesla; strictly
        positive.

    Raises
    ------
    DeviceConfigurationError
        If any parameter is non-finite or outside its model bound.
    """

    reversal_parameter: float
    pinch_parameter: float
    average_toroidal_field_t: float

    def __post_init__(self) -> None:
        """Validate the field-programme invariants.

        Raises
        ------
        DeviceConfigurationError
            If any parameter is non-finite or outside its model bound.
        """
        low, high = REVERSAL_PARAMETER_BOUNDS
        require_finite("reversal_parameter", self.reversal_parameter)
        if not low <= self.reversal_parameter <= high:
            raise DeviceConfigurationError(
                f"reversal_parameter: must be within [{low}, {high}], "
                f"got {self.reversal_parameter!r}"
            )
        low, high = PINCH_PARAMETER_BOUNDS
        require_finite("pinch_parameter", self.pinch_parameter)
        if not low < self.pinch_parameter <= high:
            raise DeviceConfigurationError(
                f"pinch_parameter: must be within ({low}, {high}], "
                f"got {self.pinch_parameter!r}"
            )
        require_positive("average_toroidal_field_t", self.average_toroidal_field_t)


@dataclass(frozen=True, slots=True)
class OperationalLimits:
    """Declared operating-point limits of a reversed-field pinch.

    Parameters
    ----------
    plasma_current_ma
        Flat-top plasma current ``I_p`` in mega-amperes; strictly
        positive.
    flat_top_duration_s
        Declared flat-top duration in seconds; non-negative.

    Raises
    ------
    DeviceConfigurationError
        If any limit is non-finite or outside its model bound.
    """

    plasma_current_ma: float
    flat_top_duration_s: float

    def __post_init__(self) -> None:
        """Validate every declared limit.

        Raises
        ------
        DeviceConfigurationError
            If any limit is non-finite or outside its model bound.
        """
        require_positive("plasma_current_ma", self.plasma_current_ma)
        require_finite("flat_top_duration_s", self.flat_top_duration_s)
        if self.flat_top_duration_s < 0.0:
            raise DeviceConfigurationError(
                "flat_top_duration_s: must be non-negative, "
                f"got {self.flat_top_duration_s!r}"
            )

    def edge_poloidal_field_t(self, geometry: PinchGeometry) -> float:
        """Edge poloidal field of this current in the given geometry.

        Parameters
        ----------
        geometry
            Validated pinch geometry supplying the minor radius.

        Returns
        -------
        float
            ``B_theta(a) = mu0 I_p / (2 pi a)`` in tesla, evaluated as
            ``0.2 I_p[MA] / a[m]`` (exact in SI with
            ``mu0 = 4 pi x 10^-7``).
        """
        return 0.2 * self.plasma_current_ma / geometry.minor_radius_m
