# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — shared fixtures of the level-0 physics tests

"""Synthetic configurations and inputs shared by the level-0 physics tests.

Every value is a test fixture; none describes a real machine. The orders
of magnitude (aspect ratio 4, a quarter-tesla average toroidal field, a
mega-ampere of current, pinch parameters between one and two) exist only
so that the identities of the Bessel-function model can serve as anchors.
"""

from __future__ import annotations

import struct

from scpn_rfp_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_rfp_core.parameters import FieldProgramme, OperationalLimits, PinchGeometry
from scpn_rfp_core.physics import LEVEL0_RADIAL_STATIONS, ModelInputs

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"


def configuration(
    pinch_parameter: float = 1.6,
    reversal_parameter: float = -0.2,
    plasma_current_ma: float = 1.0,
    minor_radius_m: float = 0.5,
    major_radius_m: float = 2.0,
    average_toroidal_field_t: float = 0.25,
) -> DeviceConfiguration:
    """Return a synthetic configuration with optional overrides."""
    return DeviceConfiguration(
        identifier="reversed_field_pinch",
        geometry=PinchGeometry(
            major_radius_m=major_radius_m, minor_radius_m=minor_radius_m
        ),
        fields=FieldProgramme(
            reversal_parameter=reversal_parameter,
            pinch_parameter=pinch_parameter,
            average_toroidal_field_t=average_toroidal_field_t,
        ),
        limits=OperationalLimits(
            plasma_current_ma=plasma_current_ma, flat_top_duration_s=0.1
        ),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def inputs(stations: tuple[float, ...] = LEVEL0_RADIAL_STATIONS) -> ModelInputs:
    """Return synthetic model inputs (the plan's stations by default)."""
    return ModelInputs(radial_stations=stations)


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)
