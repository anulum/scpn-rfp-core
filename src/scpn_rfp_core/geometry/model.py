# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device 3D model record

"""Tier-G1 device 3D model: analytic bodies of one validated design.

The model composes the validated configuration (the pinch geometry:
plasma major and minor radii) and the validated device geometry (vessel
wall, conducting shell, winding) into four named, closed,
outward-oriented triangle meshes on the device axis of the cylindrical
periodic equivalent, regenerated deterministically from the two records.
Its canonical record carries the schema identity, the units and axis
convention, both source digests, the segment count, a summary of every
body (counts, volume, area, bounding box, mesh digest) and fixed
non-claims; the SHA-256 of that record identifies the exact model.

The meshes are analytic surfaces of the cylindrical periodic equivalent:
the plasma body is the Bessel-function-model domain of the level-0
physics, the periodic length is ``2 pi R0``, and the end caps of the
cylinders are an artefact of the primitive, not closures of the machine —
the toroidal curvature is not modelled at this tier. No body carries an
engineering property. The unit circle, the primitives and the mesh
contract are consumed from the pinned shared kernel library
(``scpn_reactor_kernels.geometry``); this module owns only the device
composition.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Final

from scpn_reactor_kernels.errors import GeometryError
from scpn_reactor_kernels.geometry import (
    TriangleMesh,
    annular_tube,
    cylinder_solid,
    require_segments,
)

from scpn_rfp_core.configuration import DeviceConfiguration
from scpn_rfp_core.errors import DeviceGeometryError
from scpn_rfp_core.geometry.device import DeviceGeometry

MODEL_SCHEMA: Final = "scpn.rfp-3d-model.v1"
MODEL_SCHEMA_VERSION: Final = "1.0.0"
MODEL_UNITS: Final = {
    "length": "metre",
    "handedness": "right",
    "axis": "z along the axis of the cylindrical periodic equivalent",
    "origin": "z = 0 at one end of the periodic length 2 pi R0",
}
MODEL_NON_CLAIMS: Final = (
    "analytic surfaces tessellated from a synthetic configuration and geometry",
    (
        "the cylindrical periodic equivalent of the toroidal device is "
        "modelled: the end caps of the cylinders are an artefact of the "
        "primitive, and the toroidal curvature, poloidal coil rings and shell "
        "penetrations are not modelled at this tier"
    ),
    "no body is an equilibrium boundary, a CAD solid or an engineering model",
    "no material property, load, field or neutronic quantity is carried",
    "no value describes or validates any real machine",
)

ROLE_VACUUM_BOUNDARY: Final = "vacuum_boundary"
ROLE_PLASMA: Final = "plasma"
ROLE_COIL: Final = "coil"
MATERIAL_VESSEL_WALL: Final = "vessel_wall"
MATERIAL_SHELL_CONDUCTOR: Final = "shell_conductor"
MATERIAL_COIL_CONDUCTOR: Final = "coil_conductor"
MATERIAL_PLASMA: Final = "plasma"

BODY_PLASMA_COLUMN: Final = "plasma_column"
BODY_VACUUM_VESSEL: Final = "vacuum_vessel"
BODY_CONDUCTING_SHELL: Final = "conducting_shell"
BODY_TOROIDAL_FIELD_WINDING: Final = "toroidal_field_winding"
BODY_NAMES: Final = (
    BODY_PLASMA_COLUMN,
    BODY_VACUUM_VESSEL,
    BODY_CONDUCTING_SHELL,
    BODY_TOROIDAL_FIELD_WINDING,
)


@dataclass(frozen=True, slots=True)
class DeviceModel3D:
    """The tessellated device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    segments
        Circumferential segment count used for every body.
    meshes
        The four bodies in the fixed order of :data:`BODY_NAMES`.

    Raises
    ------
    DeviceGeometryError
        If the body names or their order differ from :data:`BODY_NAMES`.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    segments: int
    meshes: tuple[TriangleMesh, ...]

    def __post_init__(self) -> None:
        """Validate the body inventory.

        Raises
        ------
        DeviceGeometryError
            If the body names or their order differ from :data:`BODY_NAMES`.
        """
        names = tuple(mesh.name for mesh in self.meshes)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"meshes: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, segment
            count and every body summary.
        """
        return {
            "schema": MODEL_SCHEMA,
            "schema_version": MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "segments": self.segments,
            "bodies": [mesh.summary_record() for mesh in self.meshes],
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the record canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(), sort_keys=True, separators=(",", ":"), allow_nan=False
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact model record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def build_device_model(
    configuration: DeviceConfiguration, geometry: DeviceGeometry, segments: int
) -> DeviceModel3D:
    """Tessellate the four bodies of a validated design.

    Parameters
    ----------
    configuration
        Validated RFP configuration; its pinch geometry fixes the plasma
        minor radius ``a`` and the periodic length ``2 pi R0``.
    geometry
        Validated device geometry (vessel wall, shell, winding gap and
        thickness).
    segments
        Circumferential segments for every body; at least 8, multiple of 8.

    Returns
    -------
    DeviceModel3D
        The composed model.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid (the library's refusal is
        re-raised under the device error type with its message).
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    minor = configuration.geometry.minor_radius_m
    length = 2.0 * math.pi * configuration.geometry.major_radius_m
    vessel_outer = minor + geometry.vessel_wall_thickness_m
    shell_outer = vessel_outer + geometry.shell_thickness_m
    winding_inner = shell_outer + geometry.winding_gap_m
    bodies = (
        (
            BODY_PLASMA_COLUMN,
            ROLE_PLASMA,
            MATERIAL_PLASMA,
            cylinder_solid(minor, 0.0, length, segments),
        ),
        (
            BODY_VACUUM_VESSEL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_VESSEL_WALL,
            annular_tube(minor, vessel_outer, 0.0, length, segments),
        ),
        (
            BODY_CONDUCTING_SHELL,
            ROLE_VACUUM_BOUNDARY,
            MATERIAL_SHELL_CONDUCTOR,
            annular_tube(vessel_outer, shell_outer, 0.0, length, segments),
        ),
        (
            BODY_TOROIDAL_FIELD_WINDING,
            ROLE_COIL,
            MATERIAL_COIL_CONDUCTOR,
            annular_tube(
                winding_inner,
                winding_inner + geometry.winding_thickness_m,
                0.0,
                length,
                segments,
            ),
        ),
    )
    meshes = tuple(
        TriangleMesh(
            name=name,
            role=role,
            material_identifier=material,
            vertices=vertices,
            faces=faces,
        )
        for name, role, material, (vertices, faces) in bodies
    )
    return DeviceModel3D(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        segments=segments,
        meshes=meshes,
    )
