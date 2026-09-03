# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device model parity against the library's native kernels

"""Bit-exact parity of the device model against the pinned library's native kernels.

The device model is composed on the Python floor of the shared kernel
library; this file proves that every body it builds agrees bit for bit
with the library's native tessellation and mesh measures, so the consumer
inherits the library's parity rather than re-proving the kernels. Skipped
hermetically when the library's optional native module is absent; when
present, every vertex coordinate, face index and measure is compared by
float64 bit pattern, never by tolerance. All inputs are synthetic.
"""

from __future__ import annotations

import pytest

from geometry_fixtures import (
    bits,
    reference_configuration,
    reference_geometry,
    stream_bits,
)
from scpn_rfp_core.geometry import build_device_model

native = pytest.importorskip("scpn_reactor_kernels_native")


def native_bodies(segments: int) -> list[tuple[list[float], list[int]]]:
    """Tessellate the four device bodies through the library's native kernels."""
    import math

    configuration = reference_configuration()
    geometry = reference_geometry()
    minor = configuration.geometry.minor_radius_m
    length = 2.0 * math.pi * configuration.geometry.major_radius_m
    vessel_outer = minor + geometry.vessel_wall_thickness_m
    shell_outer = vessel_outer + geometry.shell_thickness_m
    winding_inner = shell_outer + geometry.winding_gap_m
    streams = (
        native.tessellate_cylinder(minor, 0.0, length, segments),
        native.tessellate_annular_tube(minor, vessel_outer, 0.0, length, segments),
        native.tessellate_annular_tube(
            vessel_outer, shell_outer, 0.0, length, segments
        ),
        native.tessellate_annular_tube(
            winding_inner,
            winding_inner + geometry.winding_thickness_m,
            0.0,
            length,
            segments,
        ),
    )
    return [(list(vertices), list(faces)) for vertices, faces in streams]


@pytest.mark.parametrize("segments", [8, 32, 64])
def test_every_body_is_bit_exact_with_the_library_native_kernels(
    segments: int,
) -> None:
    """Vertices, faces, volume and area of all four bodies agree bit for bit."""
    model = build_device_model(
        reference_configuration(), reference_geometry(), segments
    )
    bodies = native_bodies(segments)
    for mesh, (vertices, faces) in zip(model.meshes, bodies, strict=True):
        floor = [c for v in mesh.vertices for c in v]
        assert stream_bits(floor) == stream_bits(vertices)
        assert [i for f in mesh.faces for i in f] == faces
        volume = native.mesh_volume(vertices, faces)
        assert bits(volume) == bits(mesh.signed_volume_m3())
        assert bits(native.mesh_area(vertices, faces)) == bits(mesh.surface_area_m2())
