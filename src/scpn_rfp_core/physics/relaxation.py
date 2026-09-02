# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — relaxed state of the Bessel-function model

"""The cylindrical force-free relaxed state (Bessel-function model).

The relaxed state of a reversed-field pinch satisfies the force-free
condition ``curl B = alpha B`` with constant ``alpha`` (R. Paccagnella,
arXiv:1509.07307v2 (2015), eq. 4, after J. B. Taylor); in cylindrical
geometry and axisymmetry its regular solution is the Bessel pair
``B = (0, B0 J1(alpha r), B0 J0(alpha r))`` in ``(r, theta, phi)``
(eq. 5, core region). Taking that single region over the whole minor
radius ``a`` is the Bessel-function model (BFM). With the pinch parameter
``Theta = B_theta(a) / <B_phi>`` and the reversal parameter
``F = B_phi(a) / <B_phi>`` as the source defines them (the wall fields
over the cross-section average of the toroidal field), the cross-section
average ``<B_phi> = 2 B0 J1(alpha a) / (alpha a)`` gives

- ``alpha a = 2 Theta``, so the force-free parameter is ``mu = 2 Theta / a``;
- ``B0 = <B_phi> Theta / J1(2 Theta)``;
- ``F_bfm(Theta) = Theta J0(2 Theta) / J1(2 Theta)``, which tends to one
  as ``Theta`` tends to zero and crosses zero at
  ``Theta_rev = j_{0,1} / 2 = 1.2024...`` (the configuration's advisory
  threshold ``1.2`` is its rounding);
- the toroidal field reverses inside the plasma at ``r_rev = j_{0,1} / mu``
  when ``Theta > Theta_rev``, otherwise there is no reversal surface.

The model is defined for ``0 < Theta < j_{1,1} / 2 = 1.9158...``: at that
bound ``J1(2 Theta)`` vanishes, the relaxed state's average toroidal field
is zero and ``F_bfm`` has its pole; beyond it the axis field of the model
is antiparallel to the declared average. A pinch parameter at or beyond
the bound is refused, never clamped. The BFM edge poloidal field
``B0 J1(2 Theta)`` is compared with the field of the declared plasma
current, ``mu0 I_p / (2 pi a)`` (the configuration's own estimate), as an
advisory. Nothing here solves an equation and no value describes a real
machine: the source itself studies the departures of real relaxed states
from the fully relaxed Taylor state.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final

from scpn_rfp_core.configuration import DeviceConfiguration
from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.parameters import require_positive
from scpn_rfp_core.physics.numerics import (
    BESSEL_J0_FIRST_ZERO,
    BESSEL_J1_FIRST_ZERO,
    bessel_j0,
    bessel_j1,
)

#: ``j_{0,1} / 2``: the pinch parameter at which ``F_bfm = 0``.
BFM_REVERSAL_PINCH_PARAMETER: Final = BESSEL_J0_FIRST_ZERO / 2.0
#: ``j_{1,1} / 2``: the pole of ``F_bfm``; the model's exclusive upper bound.
BFM_MAX_PINCH_PARAMETER: Final = BESSEL_J1_FIRST_ZERO / 2.0


def require_bfm_pinch_parameter(theta: float) -> float:
    """Return ``theta`` when the Bessel-function model is defined there.

    Parameters
    ----------
    theta
        Pinch parameter.

    Returns
    -------
    float
        The validated pinch parameter.

    Raises
    ------
    DeviceConfigurationError
        If ``theta`` is not strictly positive or is at or beyond
        ``j_{1,1} / 2``.
    """
    require_positive("pinch_parameter", theta)
    if theta >= BFM_MAX_PINCH_PARAMETER:
        raise DeviceConfigurationError(
            "pinch_parameter: the Bessel-function model is defined for "
            f"Theta < j_1,1 / 2 = {BFM_MAX_PINCH_PARAMETER!r} (the average "
            "toroidal field of the relaxed state vanishes there), got "
            f"{theta!r}"
        )
    return theta


def force_free_parameter(theta: float, minor_radius_m: float) -> float:
    """Return ``mu = 2 Theta / a`` in inverse metres.

    Parameters
    ----------
    theta
        Pinch parameter.
    minor_radius_m
        Minor radius ``a``.

    Returns
    -------
    float
        The force-free parameter of the relaxed state.
    """
    return 2.0 * theta / minor_radius_m


def axis_field(average_toroidal_field_t: float, theta: float) -> float:
    """Return ``B0 = <B_phi> Theta / J1(2 Theta)`` in tesla.

    Parameters
    ----------
    average_toroidal_field_t
        Cross-section average of the toroidal field.
    theta
        Pinch parameter inside the model's domain.

    Returns
    -------
    float
        The on-axis field of the Bessel-function model.
    """
    return average_toroidal_field_t * theta / bessel_j1(2.0 * theta)


def bfm_reversal_parameter(theta: float) -> float:
    """Return ``F_bfm = Theta J0(2 Theta) / J1(2 Theta)``.

    Parameters
    ----------
    theta
        Pinch parameter.

    Returns
    -------
    float
        The reversal parameter of the Bessel-function model.

    Raises
    ------
    DeviceConfigurationError
        If ``theta`` is outside the model's domain.
    """
    require_bfm_pinch_parameter(theta)
    x = 2.0 * theta
    return theta * bessel_j0(x) / bessel_j1(x)


def reversal_radius(theta: float, minor_radius_m: float) -> float | None:
    """Return ``r_rev = j_{0,1} / mu`` when the field reverses inside ``a``.

    Parameters
    ----------
    theta
        Pinch parameter.
    minor_radius_m
        Minor radius ``a``.

    Returns
    -------
    float or None
        The reversal radius in metres, or ``None`` when
        ``Theta <= Theta_rev`` (no reversal surface inside the plasma).
    """
    if theta <= BFM_REVERSAL_PINCH_PARAMETER:
        return None
    return BESSEL_J0_FIRST_ZERO / force_free_parameter(theta, minor_radius_m)


@dataclass(frozen=True, slots=True)
class RelaxedState:
    """The Bessel-function relaxed state of one configuration.

    Parameters
    ----------
    pinch_parameter
        Declared ``Theta``.
    force_free_parameter_per_m
        ``mu = 2 Theta / a``.
    axis_field_t
        ``B0``.
    bfm_reversal_parameter
        ``F_bfm(Theta)``.
    declared_reversal_parameter
        The configuration's ``F``.
    reversal_mismatch
        ``F - F_bfm`` (advisory).
    reversed
        ``True`` when ``Theta > Theta_rev``.
    reversal_radius_m
        ``r_rev`` or ``None``.
    edge_poloidal_field_bfm_t
        ``B0 J1(2 Theta)``.
    edge_poloidal_field_current_t
        ``mu0 I_p / (2 pi a)`` from the declared current.
    edge_field_relative_mismatch
        ``(current-derived - BFM) / BFM`` (advisory).
    """

    pinch_parameter: float
    force_free_parameter_per_m: float
    axis_field_t: float
    bfm_reversal_parameter: float
    declared_reversal_parameter: float
    reversal_mismatch: float
    reversed: bool
    reversal_radius_m: float | None
    edge_poloidal_field_bfm_t: float
    edge_poloidal_field_current_t: float
    edge_field_relative_mismatch: float

    def to_record(self) -> dict[str, Any]:
        """Project the state to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {
            "pinch_parameter": self.pinch_parameter,
            "force_free_parameter_per_m": self.force_free_parameter_per_m,
            "axis_field_t": self.axis_field_t,
            "bfm_reversal_parameter": self.bfm_reversal_parameter,
            "declared_reversal_parameter": self.declared_reversal_parameter,
            "reversal_mismatch": self.reversal_mismatch,
            "reversed": self.reversed,
            "reversal_radius_m": self.reversal_radius_m,
            "edge_poloidal_field_bfm_t": self.edge_poloidal_field_bfm_t,
            "edge_poloidal_field_current_t": self.edge_poloidal_field_current_t,
            "edge_field_relative_mismatch": self.edge_field_relative_mismatch,
        }


def relaxed_state(configuration: DeviceConfiguration) -> RelaxedState:
    """Evaluate the Bessel-function relaxed state of a configuration.

    Parameters
    ----------
    configuration
        Validated reversed-field-pinch configuration.

    Returns
    -------
    RelaxedState
        The relaxed state and its advisory comparisons.

    Raises
    ------
    DeviceConfigurationError
        If the declared pinch parameter is outside the model's domain.
    """
    theta = require_bfm_pinch_parameter(configuration.fields.pinch_parameter)
    minor = configuration.geometry.minor_radius_m
    average = configuration.fields.average_toroidal_field_t
    declared = configuration.fields.reversal_parameter
    mu = force_free_parameter(theta, minor)
    b0 = axis_field(average, theta)
    f_bfm = bfm_reversal_parameter(theta)
    edge_bfm = b0 * bessel_j1(2.0 * theta)
    edge_current = configuration.limits.edge_poloidal_field_t(configuration.geometry)
    return RelaxedState(
        pinch_parameter=theta,
        force_free_parameter_per_m=mu,
        axis_field_t=b0,
        bfm_reversal_parameter=f_bfm,
        declared_reversal_parameter=declared,
        reversal_mismatch=declared - f_bfm,
        reversed=theta > BFM_REVERSAL_PINCH_PARAMETER,
        reversal_radius_m=reversal_radius(theta, minor),
        edge_poloidal_field_bfm_t=edge_bfm,
        edge_poloidal_field_current_t=edge_current,
        edge_field_relative_mismatch=(edge_current - edge_bfm) / edge_bfm,
    )
