# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device geometry model

"""Validated device geometry of a reversed-field pinch assembly.

The geometry complements the
:class:`~scpn_rfp_core.configuration.DeviceConfiguration` (which carries
the pinch geometry — plasma major and minor radii — the field programme
and the operational limits) with the device-owned mechanical envelope of
the cylindrical periodic equivalent of the toroidal device: the vacuum
vessel wall at the plasma edge, the close-fitting conducting shell the
relaxation physics requires, and the toroidal-field winding outside it.
The layout follows the relaxation literature's geometry (R. Paccagnella,
arXiv:1509.07307v2 (2015): an ideal shell surrounding the plasma,
bounded at the wall radius); no dimension of any device is used, and
every parameter set is synthetic. Validation is fail-closed,
serialisation is canonical, and the SHA-256 digest identifies the exact
geometry.

The plasma radii are not repeated here: they are the validated
configuration's ``geometry.minor_radius_m`` and ``geometry.major_radius_m``,
used directly when the model is built.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_rfp_core.errors import DeviceGeometryError
from scpn_rfp_core.parameters import require_positive

GEOMETRY_FIELDS: Final = (
    "vessel_wall_thickness_m",
    "shell_thickness_m",
    "winding_gap_m",
    "winding_thickness_m",
)


def _positive(name: str, value: float) -> float:
    """Apply the shared positivity rule with the geometry error type.

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
    DeviceGeometryError
        If the value is non-finite or not strictly positive.
    """
    try:
        return require_positive(name, value)
    except ValueError as exc:
        raise DeviceGeometryError(str(exc)) from exc


@dataclass(frozen=True, slots=True)
class DeviceGeometry:
    """Validated RFP envelope geometry (SI units in the field names).

    Parameters
    ----------
    vessel_wall_thickness_m
        Radial thickness of the vacuum vessel wall at the plasma edge;
        strictly positive.
    shell_thickness_m
        Radial thickness of the close-fitting conducting shell; strictly
        positive.
    winding_gap_m
        Radial gap between the conducting shell and the toroidal-field
        winding; strictly positive.
    winding_thickness_m
        Radial thickness of the toroidal-field winding; strictly
        positive.

    Raises
    ------
    DeviceGeometryError
        If any value is non-finite or not strictly positive.
    """

    vessel_wall_thickness_m: float
    shell_thickness_m: float
    winding_gap_m: float
    winding_thickness_m: float

    def __post_init__(self) -> None:
        """Validate every declared value.

        Raises
        ------
        DeviceGeometryError
            If any invariant fails.
        """
        for name in GEOMETRY_FIELDS:
            _positive(name, getattr(self, name))

    def to_record(self) -> dict[str, float]:
        """Project the geometry to a JSON-serialisable record.

        Returns
        -------
        dict[str, float]
            Every declared parameter under its name.
        """
        return {name: getattr(self, name) for name in GEOMETRY_FIELDS}

    def canonical_bytes(self) -> bytes:
        """Serialise the geometry canonically.

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
        """Identify the exact geometry.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Raises
    ------
    DeviceGeometryError
        If the field is missing or not a real number (booleans rejected).
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceGeometryError(f"{field}: must be a number, got {value!r}")
    return float(value)


def geometry_from_record(record: Any) -> DeviceGeometry:
    """Build a validated geometry from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceGeometry.to_record`.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the record shape or any value violates the model; unknown
        fields are refused.
    """
    if not isinstance(record, dict):
        raise DeviceGeometryError("record: must be an object")
    unknown = sorted(set(record) - set(GEOMETRY_FIELDS))
    if unknown:
        raise DeviceGeometryError(f"record: unknown fields {unknown!r}")
    return DeviceGeometry(**{name: _number(record, name) for name in GEOMETRY_FIELDS})


def geometry_from_bytes(data: bytes) -> DeviceGeometry:
    """Build a validated geometry from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceGeometry
        The fully validated geometry.

    Raises
    ------
    DeviceGeometryError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceGeometryError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceGeometryError(f"record: invalid JSON document: {exc}") from exc
    return geometry_from_record(record)
