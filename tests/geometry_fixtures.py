# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — shared synthetic fixtures of the geometry tests

"""Configurations and geometries shared by the geometry tests.

Two fixtures, and the difference between them is the point.

The *reference* pair is synthetic: round numbers chosen to exercise the
model, describing no machine.

The *anchor* pair carries the values printed by Paccagnella, "Relaxation
models for single helical reversed field pinch plasmas", arXiv:1509.07307
(2015), already on file: the aspect ratio ``R/a = 5`` of the eigenstates in
its Fig. 1, 3 and 8, and the reversal parameter ``F = -0.05`` that the same
figures call the shallow reversed case. That source works throughout in
units normalised to the plasma minor radius, so it prints no length in
metres; the anchored quantities are therefore dimensionless, which is what
this family has to anchor on. The absolute radii, the pinch parameter, the
field amplitude, the operational limits and every envelope thickness are
declared here and marked as declared. Reproducing a printed value is an
anchor, never a claim about any machine.
"""

from __future__ import annotations

import struct

from scpn_rfp_core.configuration import DeviceConfiguration, RegistryBinding
from scpn_rfp_core.geometry import DeviceGeometry
from scpn_rfp_core.parameters import FieldProgramme, OperationalLimits, PinchGeometry

REGISTRY_DIGEST = "786d9542ce76c56dd7748fa948b17efed6c073525e527ce90e6d5e29a2d00090"


def reference_configuration() -> DeviceConfiguration:
    """Return the synthetic RFP configuration of the geometry tests."""
    return DeviceConfiguration(
        identifier="reversed_field_pinch",
        geometry=PinchGeometry(major_radius_m=2.0, minor_radius_m=0.5),
        fields=FieldProgramme(
            reversal_parameter=-0.2,
            pinch_parameter=1.6,
            average_toroidal_field_t=0.25,
        ),
        limits=OperationalLimits(plasma_current_ma=1.0, flat_top_duration_s=0.1),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def reference_geometry() -> DeviceGeometry:
    """Return the synthetic RFP envelope geometry of the geometry tests."""
    return DeviceGeometry(
        vessel_wall_thickness_m=0.05,
        shell_thickness_m=0.02,
        winding_gap_m=0.1,
        winding_thickness_m=0.15,
    )


#: Values printed by Paccagnella (2015) for the single-helical eigenstates.
ANCHOR_ASPECT_RATIO = 5.0
ANCHOR_REVERSAL_PARAMETER = -0.05

#: Declared: the source is in normalised units and prints no length.
ANCHOR_MINOR_RADIUS_M = 0.5
ANCHOR_MAJOR_RADIUS_M = ANCHOR_MINOR_RADIUS_M * ANCHOR_ASPECT_RATIO


def anchor_configuration() -> DeviceConfiguration:
    """Return the configuration carrying the printed aspect ratio and reversal.

    The aspect ratio and the reversal parameter are the printed values. The
    absolute radii that realise the ratio, the pinch parameter, the field
    amplitude and the operational limits are declared; the source prints
    none of them.
    """
    return DeviceConfiguration(
        identifier="reversed_field_pinch",
        geometry=PinchGeometry(
            major_radius_m=ANCHOR_MAJOR_RADIUS_M,
            minor_radius_m=ANCHOR_MINOR_RADIUS_M,
        ),
        fields=FieldProgramme(
            reversal_parameter=ANCHOR_REVERSAL_PARAMETER,
            pinch_parameter=1.6,
            average_toroidal_field_t=0.25,
        ),
        limits=OperationalLimits(plasma_current_ma=1.0, flat_top_duration_s=0.1),
        registry=RegistryBinding(version="1.0.0", digest_sha256=REGISTRY_DIGEST),
    )


def anchor_geometry() -> DeviceGeometry:
    """Return the envelope geometry used with the anchor configuration.

    Every value is declared. The source prints the dimensionless state of
    the plasma, not the wall, shell or winding of any vessel around it.
    """
    return DeviceGeometry(
        vessel_wall_thickness_m=0.05,
        shell_thickness_m=0.02,
        winding_gap_m=0.1,
        winding_thickness_m=0.15,
    )


def bits(value: float) -> bytes:
    """Return the IEEE-754 double bit pattern of a value."""
    return struct.pack("<d", value)


def stream_bits(values: list[float]) -> bytes:
    """Return the concatenated bit patterns of a float stream."""
    return b"".join(bits(value) for value in values)
