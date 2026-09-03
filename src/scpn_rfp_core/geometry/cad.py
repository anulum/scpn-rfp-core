# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device CAD model record (tier G2)

"""Tier-G2 device CAD model: B-rep solids of one validated design.

The model composes the validated configuration (the pinch geometry) and
the validated device geometry (vessel wall, conducting shell, winding)
into the same four named bodies as the tier-G1 model
(:func:`build_device_model`), built as exact B-rep solids of revolution by
the pinned third-party OpenCASCADE kernel through the shared kernel
library (``scpn_reactor_kernels.cad``, kernels ``cad_brep_solids``,
``cad_step_export``, ``cad_faceting``, ``cad_evidence``).

OpenCASCADE is not the bit-exact floor: every body is checked fail-closed
by the library's evidence kernel against its analytic closed form (volume
and surface area within the library's declared relative tolerance
``1e-9``), the faceted B-rep volume is checked against the declared
deflection deficit bound and against the tier-G1 mesh at the declared
reference segment count within the exact polygon-deficit bound, and the
STEP export is the library's normalised deterministic writer. This module
owns only what is device knowledge: the schema identity, the composition
of the four bodies, the build invariants of this family and its
non-claims. The canonical record carries the schema identity, the units
and axis convention, both source digests, the declared deflections and
reference segment count, the back-end versions, the assembly manifest,
the STEP digest and the per-body evidence; the SHA-256 of that record
identifies the exact model. No body carries an engineering property and
no value describes a real machine.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from typing import Any, Final

from scpn_reactor_kernels.cad import (
    MANIFEST_SCHEMA,
    BodyEvidence,
    BrepAssembly,
    annular_tube_brep,
    assembly_evidence,
    backend_versions,
    cylinder_solid_brep,
    facet_assembly,
)
from scpn_reactor_kernels.cad import (
    step_bytes as _normalised_step_bytes,
)
from scpn_reactor_kernels.cad import (
    step_sha256 as _step_bytes_sha256,
)
from scpn_reactor_kernels.errors import CadError, GeometryError
from scpn_reactor_kernels.geometry import TriangleMesh, require_segments

from scpn_rfp_core.configuration import DeviceConfiguration
from scpn_rfp_core.errors import DeviceGeometryError
from scpn_rfp_core.geometry.device import DeviceGeometry
from scpn_rfp_core.geometry.model import (
    BODY_CONDUCTING_SHELL,
    BODY_NAMES,
    BODY_PLASMA_COLUMN,
    BODY_TOROIDAL_FIELD_WINDING,
    BODY_VACUUM_VESSEL,
    MATERIAL_COIL_CONDUCTOR,
    MATERIAL_PLASMA,
    MATERIAL_SHELL_CONDUCTOR,
    MATERIAL_VESSEL_WALL,
    MODEL_UNITS,
    ROLE_COIL,
    ROLE_PLASMA,
    ROLE_VACUUM_BOUNDARY,
    build_device_model,
)

CAD_MODEL_SCHEMA: Final = "scpn.rfp-cad-model.v1"
CAD_MODEL_SCHEMA_VERSION: Final = "1.0.0"
CAD_MODEL_NON_CLAIMS: Final = (
    (
        "B-rep solids of the same declared design, built by the pinned "
        "third-party OpenCASCADE kernel and checked against the analytic closed "
        "forms; not an engineering model"
    ),
    (
        "the cylindrical periodic equivalent of the toroidal device is "
        "modelled: the end caps of the cylinders are an artefact of the "
        "primitive, and the toroidal curvature, poloidal coil rings and shell "
        "penetrations are not modelled at this tier"
    ),
    "no material property, load, field or neutronic quantity is carried",
    (
        "STEP bytes are deterministic only within one pinned back-end "
        "environment; identity across OpenCASCADE or gmsh versions is not "
        "claimed"
    ),
    "no value describes or validates any real machine",
)

#: Reference segment count of the tier-G1 mesh the faceted B-rep is
#: compared against.
DEFAULT_REFERENCE_MESH_SEGMENTS: Final = 8
#: Declared mesher deflections of the reference record.
DEFAULT_LINEAR_DEFLECTION_M: Final = 1.0e-4
DEFAULT_ANGULAR_DEFLECTION_RAD: Final = 0.1


@dataclass(frozen=True, slots=True)
class DeviceModelCAD:
    """The B-rep device model of one configuration and geometry.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the model was built from.
    geometry_digest_sha256
        Digest of the validated geometry the model was built from.
    reference_mesh_segments
        Segment count of the tier-G1 reference mesh of the comparison.
    linear_deflection_m, angular_deflection_rad
        Declared mesher deflections of the faceting evidence.
    backend_versions
        Versions of the pinned CAD back-ends (``cadquery``, ``ocp``,
        ``gmsh``) as reported by the library.
    assembly_manifest
        The library's B-rep assembly manifest record.
    step_sha256
        SHA-256 of the normalised STEP export of the assembly.
    bodies
        Per-body evidence in the fixed order of :data:`BODY_NAMES`, as
        checked by the library's evidence kernel.
    step_data
        The normalised STEP bytes (the digested export).
    faceted_meshes
        The faceted closed meshes, one per body, in the fixed order.

    Raises
    ------
    DeviceGeometryError
        If the body inventory differs from :data:`BODY_NAMES`, the segment
        rule or the deflection rule is violated, the manifest is foreign,
        or the STEP digest is not a 64-hex value.
    """

    configuration_digest_sha256: str
    geometry_digest_sha256: str
    reference_mesh_segments: int
    linear_deflection_m: float
    angular_deflection_rad: float
    backend_versions: dict[str, str]
    assembly_manifest: dict[str, Any]
    step_sha256: str
    bodies: tuple[BodyEvidence, ...]
    step_data: bytes = field(compare=False, repr=False)
    faceted_meshes: tuple[TriangleMesh, ...] = field(
        compare=False, repr=False, default=()
    )

    def __post_init__(self) -> None:
        """Validate the model inventory and declared parameters.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        names = tuple(body.name for body in self.bodies)
        if names != BODY_NAMES:
            raise DeviceGeometryError(
                f"bodies: bodies must be exactly {BODY_NAMES!r} in order, got {names!r}"
            )
        try:
            require_segments(self.reference_mesh_segments)
        except GeometryError as exc:
            raise DeviceGeometryError(str(exc)) from exc
        for name, value in (
            ("linear_deflection_m", self.linear_deflection_m),
            ("angular_deflection_rad", self.angular_deflection_rad),
        ):
            if not math.isfinite(value) or value <= 0.0:
                raise DeviceGeometryError(
                    f"{name}: must be finite and strictly positive, got {value!r}"
                )
        if self.assembly_manifest.get("schema") != MANIFEST_SCHEMA:
            raise DeviceGeometryError(
                f"assembly_manifest.schema: must be {MANIFEST_SCHEMA!r}"
            )
        if self.assembly_manifest.get("body_count") != len(BODY_NAMES):
            raise DeviceGeometryError(
                f"assembly_manifest.body_count: must be {len(BODY_NAMES)}, got "
                f"{self.assembly_manifest.get('body_count')!r}"
            )
        if len(self.step_sha256) != 64 or not all(
            character in "0123456789abcdef" for character in self.step_sha256
        ):
            raise DeviceGeometryError(
                "step_sha256: must be 64 lowercase hexadecimal characters"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the model to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Schema identity, units, non-claims, source digests, declared
            deflections and reference segment count, back-end versions, the
            assembly manifest, the STEP digest and every body evidence.
        """
        return {
            "schema": CAD_MODEL_SCHEMA,
            "schema_version": CAD_MODEL_SCHEMA_VERSION,
            "units": dict(MODEL_UNITS),
            "non_claims": list(CAD_MODEL_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "geometry_digest_sha256": self.geometry_digest_sha256,
            "reference_mesh_segments": self.reference_mesh_segments,
            "linear_deflection_m": self.linear_deflection_m,
            "angular_deflection_rad": self.angular_deflection_rad,
            "backend_versions": dict(self.backend_versions),
            "assembly_manifest": self.assembly_manifest,
            "step_sha256": self.step_sha256,
            "bodies": [body.to_record() for body in self.bodies],
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


def build_device_cad(
    configuration: DeviceConfiguration,
    geometry: DeviceGeometry,
    segments: int = DEFAULT_REFERENCE_MESH_SEGMENTS,
    linear_deflection_m: float = DEFAULT_LINEAR_DEFLECTION_M,
    angular_deflection_rad: float = DEFAULT_ANGULAR_DEFLECTION_RAD,
) -> DeviceModelCAD:
    """Build the B-rep device model of a validated design.

    Parameters
    ----------
    configuration
        Validated RFP configuration (pinch geometry).
    geometry
        Validated device geometry (vessel wall, shell, winding).
    segments
        Segment count of the tier-G1 reference mesh of the faceting
        comparison; at least 8, multiple of 8.
    linear_deflection_m
        Largest chord distance of the faceting to the true surface;
        strictly positive.
    angular_deflection_rad
        Largest angle between adjacent facet normals; strictly positive.

    Returns
    -------
    DeviceModelCAD
        The composed, fail-closed checked model with its STEP export.

    Raises
    ------
    DeviceGeometryError
        If the segment count is invalid, a deflection is invalid, or a
        body violates a declared evidence bound (the library's refusals
        are re-raised under the device error type with their messages);
        :class:`~scpn_reactor_kernels.errors.CadUnavailableError` if the
        optional CAD back-end is absent.
    """
    try:
        require_segments(segments)
    except GeometryError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    reference = build_device_model(configuration, geometry, segments)
    minor = configuration.geometry.minor_radius_m
    length = 2.0 * math.pi * configuration.geometry.major_radius_m
    vessel_outer = minor + geometry.vessel_wall_thickness_m
    shell_outer = vessel_outer + geometry.shell_thickness_m
    winding_inner = shell_outer + geometry.winding_gap_m
    try:
        assembly = BrepAssembly(
            (
                cylinder_solid_brep(
                    minor,
                    0.0,
                    length,
                    BODY_PLASMA_COLUMN,
                    ROLE_PLASMA,
                    MATERIAL_PLASMA,
                ),
                annular_tube_brep(
                    minor,
                    vessel_outer,
                    0.0,
                    length,
                    BODY_VACUUM_VESSEL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_VESSEL_WALL,
                ),
                annular_tube_brep(
                    vessel_outer,
                    shell_outer,
                    0.0,
                    length,
                    BODY_CONDUCTING_SHELL,
                    ROLE_VACUUM_BOUNDARY,
                    MATERIAL_SHELL_CONDUCTOR,
                ),
                annular_tube_brep(
                    winding_inner,
                    winding_inner + geometry.winding_thickness_m,
                    0.0,
                    length,
                    BODY_TOROIDAL_FIELD_WINDING,
                    ROLE_COIL,
                    MATERIAL_COIL_CONDUCTOR,
                ),
            )
        )
        faceted = facet_assembly(assembly, linear_deflection_m, angular_deflection_rad)
        bodies = assembly_evidence(
            assembly.bodies,
            (minor, minor, vessel_outer, winding_inner),
            faceted,
            reference.meshes,
            linear_deflection_m,
            segments,
        )
    except CadError as exc:
        raise DeviceGeometryError(str(exc)) from exc
    manifest = assembly.manifest()
    extras = {
        "schema": CAD_MODEL_SCHEMA,
        "schema_version": CAD_MODEL_SCHEMA_VERSION,
        "configuration_digest_sha256": configuration.digest_sha256(),
        "geometry_digest_sha256": geometry.digest_sha256(),
        "assembly_manifest_sha256": assembly.manifest_sha256(),
        "units": dict(MODEL_UNITS),
        "non_claims": list(CAD_MODEL_NON_CLAIMS),
        "backend_versions": backend_versions(),
    }
    step_data = _normalised_step_bytes(assembly, extras)
    return DeviceModelCAD(
        configuration_digest_sha256=configuration.digest_sha256(),
        geometry_digest_sha256=geometry.digest_sha256(),
        reference_mesh_segments=segments,
        linear_deflection_m=linear_deflection_m,
        angular_deflection_rad=angular_deflection_rad,
        backend_versions=backend_versions(),
        assembly_manifest=manifest,
        step_sha256=_step_bytes_sha256(step_data),
        bodies=bodies,
        step_data=step_data,
        faceted_meshes=faceted,
    )
