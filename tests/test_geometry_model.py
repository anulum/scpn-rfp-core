# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device 3D model tests

"""Body inventory, placement, record identity and the pinned digest."""

from __future__ import annotations

import hashlib
import json
import math

import pytest

from geometry_fixtures import (
    ANCHOR_ASPECT_RATIO,
    ANCHOR_MINOR_RADIUS_M,
    ANCHOR_REVERSAL_PARAMETER,
    anchor_configuration,
    anchor_geometry,
    reference_configuration,
    reference_geometry,
)
from scpn_rfp_core.errors import DeviceGeometryError
from scpn_rfp_core.geometry import (
    BODY_NAMES,
    MODEL_NON_CLAIMS,
    MODEL_SCHEMA,
    MODEL_SCHEMA_VERSION,
    MODEL_UNITS,
    DeviceModel3D,
    build_device_model,
)

REFERENCE_MODEL_SHA256 = (
    "0bc637ea342a131004f393307a894251a8d3da76f5774e175b05f03c2a56a728"
)


def reference_model(segments: int = 16) -> DeviceModel3D:
    """Build the reference model of these tests at a segment count."""
    return build_device_model(reference_configuration(), reference_geometry(), segments)


def test_bodies_roles_materials_and_placement() -> None:
    """Four nested bodies in the fixed order with the declared placement."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = reference_model()
    assert tuple(mesh.name for mesh in model.meshes) == BODY_NAMES
    assert [mesh.role for mesh in model.meshes] == [
        "plasma",
        "vacuum_boundary",
        "vacuum_boundary",
        "coil",
    ]
    assert [mesh.material_identifier for mesh in model.meshes] == [
        "plasma",
        "vessel_wall",
        "shell_conductor",
        "coil_conductor",
    ]
    minor = configuration.geometry.minor_radius_m
    length = 2.0 * math.pi * configuration.geometry.major_radius_m
    plasma, vessel, shell, winding = model.meshes
    assert plasma.bounding_box() == ((-minor, -minor, 0.0), (minor, minor, length))
    vessel_outer = minor + geometry.vessel_wall_thickness_m
    shell_outer = vessel_outer + geometry.shell_thickness_m
    winding_inner = shell_outer + geometry.winding_gap_m
    assert vessel.bounding_box()[1][0] == pytest.approx(vessel_outer)
    assert shell.bounding_box()[1][0] == pytest.approx(shell_outer)
    assert winding.bounding_box()[1][0] == pytest.approx(
        winding_inner + geometry.winding_thickness_m
    )
    for mesh in model.meshes:
        assert mesh.signed_volume_m3() > 0.0


def test_volumes_follow_the_analytic_bodies() -> None:
    """Each body volume converges on the analytic cylinder or tube volume."""
    model = reference_model(1024)
    length = 2.0 * math.pi * 2.0
    analytic = [
        math.pi * 0.5**2 * length,
        math.pi * (0.55**2 - 0.5**2) * length,
        math.pi * (0.57**2 - 0.55**2) * length,
        math.pi * (0.82**2 - 0.67**2) * length,
    ]
    for mesh, exact in zip(model.meshes, analytic, strict=True):
        assert 0.0 < (exact - mesh.signed_volume_m3()) / exact < 1.0e-5


def test_record_identity_and_pinned_digest() -> None:
    """The canonical record is sorted JSON and the reference digest is pinned."""
    configuration = reference_configuration()
    geometry = reference_geometry()
    model = build_device_model(configuration, geometry, 8)
    record = model.to_record()
    assert record["schema"] == MODEL_SCHEMA
    assert record["schema_version"] == MODEL_SCHEMA_VERSION
    assert record["units"] == MODEL_UNITS
    assert record["non_claims"] == list(MODEL_NON_CLAIMS)
    assert record["configuration_digest_sha256"] == configuration.digest_sha256()
    assert record["geometry_digest_sha256"] == geometry.digest_sha256()
    assert record["segments"] == 8
    assert [body["name"] for body in record["bodies"]] == list(BODY_NAMES)
    data = model.canonical_bytes()
    assert json.loads(data) == record
    assert model.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert model.digest_sha256() == REFERENCE_MODEL_SHA256


def test_model_is_deterministic() -> None:
    """Two builds of the same inputs are equal and share every digest."""
    first = reference_model(32)
    second = reference_model(32)
    assert first == second
    assert first.digest_sha256() == second.digest_sha256()
    assert [m.digest_sha256() for m in first.meshes] == [
        m.digest_sha256() for m in second.meshes
    ]


def test_invalid_segments_are_refused_before_tessellation() -> None:
    """The segment rule is checked first."""
    with pytest.raises(DeviceGeometryError, match="multiple"):
        build_device_model(reference_configuration(), reference_geometry(), 20)


def test_body_inventory_is_enforced() -> None:
    """A model with the wrong bodies or order is refused."""
    model = reference_model(8)
    with pytest.raises(DeviceGeometryError, match="bodies must be exactly"):
        DeviceModel3D(
            configuration_digest_sha256=model.configuration_digest_sha256,
            geometry_digest_sha256=model.geometry_digest_sha256,
            segments=8,
            meshes=model.meshes[::-1],
        )


def test_anchor_bodies_reproduce_the_printed_aspect_ratio() -> None:
    """The printed ratio is recoverable from the built body, not only declared.

    Paccagnella (2015) prints the aspect ratio ``R/a = 5`` of its single
    helical eigenstates and the reversal parameter ``F = -0.05`` of the
    shallow reversed case, both in units normalised to the minor radius. The
    configuration carries both printed values, and the plasma column the
    model builds returns the same ratio when its periodic length is divided
    by the circumference of its own radius. The absolute radii that realise
    the ratio are declared, so it is the ratio that is checked and not them.
    """
    configuration = anchor_configuration()
    assert configuration.geometry.aspect_ratio == ANCHOR_ASPECT_RATIO
    assert configuration.fields.reversal_parameter == ANCHOR_REVERSAL_PARAMETER

    model = build_device_model(configuration, anchor_geometry(), 64)
    column = model.meshes[0]
    assert column.name == "plasma_column"
    (_, _, low_z), (high_x, _, high_z) = column.bounding_box()
    assert high_x == ANCHOR_MINOR_RADIUS_M
    assert low_z == 0.0
    assert high_z / (2.0 * math.pi * high_x) == ANCHOR_ASPECT_RATIO
