# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — radial profiles of the Bessel-function model

"""Field and safety-factor profiles of the Bessel-function relaxed state.

At the radius ``r = (r/a) a`` of the cylinder the relaxed state of
R. Paccagnella, arXiv:1509.07307v2 (2015), eq. 5 (core region, taken
over the whole minor radius) has ``B_phi(r) = B0 J0(mu r)`` and
``B_theta(r) = B0 J1(mu r)`` with ``mu = 2 Theta / a``, so the argument
``mu r`` equals ``2 Theta (r/a)`` and is evaluated in that form. The
safety factor of the cylinder, ``q(r) = r B_phi / (R0 B_theta)``, is then
``q(r) = (r / R0) J0(mu r) / J1(mu r)``; on the axis the series limit
``J0 / J1 -> 2 / (mu r)`` gives ``q(0) = 2 / (mu R0) = a / (Theta R0)``,
which is the value reported at ``r = 0`` (the quotient is not formed
there). At the wall ``q(a) = F_bfm a / (Theta R0)``, zero exactly where
the toroidal field reverses at the wall. Inside the model's domain
``2 Theta (r/a) < j_{1,1}`` so ``J1`` is strictly positive at every
station off the axis. Nothing here describes a real machine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scpn_rfp_core.configuration import DeviceConfiguration
from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.parameters import require_finite
from scpn_rfp_core.physics.numerics import bessel_j0, bessel_j1


def require_station(name: str, fraction: float) -> float:
    """Return ``fraction`` when it lies in ``[0, 1]``.

    Parameters
    ----------
    name
        Field name reported in the rejection message.
    fraction
        Normalised radius ``r / a``.

    Returns
    -------
    float
        The validated fraction.

    Raises
    ------
    DeviceConfigurationError
        If ``fraction`` is non-finite or outside ``[0, 1]``.
    """
    require_finite(name, fraction)
    if not 0.0 <= fraction <= 1.0:
        raise DeviceConfigurationError(
            f"{name}: a radial station is r / a within [0, 1], got {fraction!r}"
        )
    return fraction


@dataclass(frozen=True, slots=True)
class RadialStation:
    """The relaxed-state fields at one normalised radius.

    Parameters
    ----------
    fraction
        ``r / a``.
    radius_m
        ``r``.
    toroidal_field_t
        ``B_phi(r) = B0 J0(mu r)``.
    poloidal_field_t
        ``B_theta(r) = B0 J1(mu r)``.
    safety_factor
        ``q(r)``; the series limit on the axis.
    """

    fraction: float
    radius_m: float
    toroidal_field_t: float
    poloidal_field_t: float
    safety_factor: float

    def to_record(self) -> dict[str, Any]:
        """Project the station to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "fraction": self.fraction,
            "radius_m": self.radius_m,
            "toroidal_field_t": self.toroidal_field_t,
            "poloidal_field_t": self.poloidal_field_t,
            "safety_factor": self.safety_factor,
        }


def axis_safety_factor(
    minor_radius_m: float, major_radius_m: float, theta: float
) -> float:
    """Return ``q(0) = a / (Theta R0)``.

    Parameters
    ----------
    minor_radius_m
        Minor radius ``a``.
    major_radius_m
        Major radius ``R0``.
    theta
        Pinch parameter.

    Returns
    -------
    float
        The on-axis safety factor of the Bessel-function model.
    """
    return minor_radius_m / (theta * major_radius_m)


def radial_station(
    fraction: float,
    minor_radius_m: float,
    major_radius_m: float,
    theta: float,
    axis_field_t: float,
) -> RadialStation:
    """Evaluate the relaxed-state fields and ``q`` at one station.

    Parameters
    ----------
    fraction
        ``r / a`` in ``[0, 1]``.
    minor_radius_m
        Minor radius ``a``.
    major_radius_m
        Major radius ``R0``.
    theta
        Pinch parameter inside the model's domain.
    axis_field_t
        ``B0`` of the relaxed state.

    Returns
    -------
    RadialStation
        The fields and the safety factor at the station.

    Raises
    ------
    DeviceConfigurationError
        If the station is outside ``[0, 1]``.
    """
    require_station("fraction", fraction)
    radius = fraction * minor_radius_m
    x = 2.0 * theta * fraction
    j0 = bessel_j0(x)
    j1 = bessel_j1(x)
    if fraction == 0.0:
        q = axis_safety_factor(minor_radius_m, major_radius_m, theta)
    else:
        q = (radius / major_radius_m) * j0 / j1
    return RadialStation(
        fraction=fraction,
        radius_m=radius,
        toroidal_field_t=axis_field_t * j0,
        poloidal_field_t=axis_field_t * j1,
        safety_factor=q,
    )


def radial_profile(
    configuration: DeviceConfiguration,
    axis_field_t: float,
    stations: tuple[float, ...],
) -> tuple[RadialStation, ...]:
    """Evaluate the relaxed-state profile at the declared stations.

    Parameters
    ----------
    configuration
        Validated reversed-field-pinch configuration.
    axis_field_t
        ``B0`` of its relaxed state.
    stations
        Normalised radii ``r / a``.

    Returns
    -------
    tuple of RadialStation
        One station per declared radius, in the declared order.
    """
    return tuple(
        radial_station(
            fraction,
            configuration.geometry.minor_radius_m,
            configuration.geometry.major_radius_m,
            configuration.fields.pinch_parameter,
            axis_field_t,
        )
        for fraction in stations
    )
