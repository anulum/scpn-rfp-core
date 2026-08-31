# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device configuration container

"""Device configuration container bound to the SPO reactor registry.

A :class:`DeviceConfiguration` composes validated pinch geometry, the
F/Θ field programme, and operational limits under the single registry
identifier this repository owns. The declared pinch parameter is
cross-checked against the value derived from the declared plasma current
via ``B_theta(a) = mu0 I_p / (2 pi a)``, and a declared ``Theta`` below
the Taylor-relaxation threshold ~1.2 is flagged because field reversal
is not expected there (J. B. Taylor, Phys. Rev. Lett. 33 (1974) 1139).
Serialisation is canonical (sorted keys, no NaN or infinity accepted
anywhere) and the SHA-256 digest of those bytes identifies the exact
parameter set. The registry binding is a data pin only — this package
never imports SCPN Phase Orchestrator code.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Final

from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.parameters import (
    FieldProgramme,
    OperationalLimits,
    PinchGeometry,
)

OWNED_CONFIGURATIONS: Final = ("reversed_field_pinch",)
TAYLOR_RELAXATION_MIN_THETA: Final = 1.2
THETA_MISMATCH_TOLERANCE: Final = 0.2
HEX_DIGEST: Final = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True, slots=True)
class RegistryBinding:
    """Pin to one SPO reactor registry release.

    Parameters
    ----------
    version
        Registry release version; non-empty.
    digest_sha256
        Registry digest as 64 lowercase hexadecimal characters.

    Raises
    ------
    DeviceConfigurationError
        If either pin component is malformed.
    """

    version: str
    digest_sha256: str

    def __post_init__(self) -> None:
        """Validate the registry pin.

        Raises
        ------
        DeviceConfigurationError
            If either pin component is malformed.
        """
        if not self.version:
            raise DeviceConfigurationError("registry.version: must be non-empty")
        if HEX_DIGEST.fullmatch(self.digest_sha256) is None:
            raise DeviceConfigurationError(
                "registry.digest_sha256: must be 64 lowercase hexadecimal "
                f"characters, got {self.digest_sha256!r}"
            )


@dataclass(frozen=True, slots=True)
class ConsistencyFinding:
    """One internal-consistency finding on a device configuration.

    Parameters
    ----------
    field
        Dotted field path the finding refers to.
    message
        Human-readable statement of the inconsistency.
    """

    field: str
    message: str


@dataclass(frozen=True, slots=True)
class DeviceConfiguration:
    """Validated reversed-field-pinch device configuration.

    Parameters
    ----------
    identifier
        SPO registry configuration identifier; must be
        ``reversed_field_pinch``.
    geometry
        Validated pinch geometry.
    fields
        Validated F/Θ field programme.
    limits
        Validated operational limits.
    registry
        Pin to the SPO reactor registry release the identifier belongs
        to.

    Raises
    ------
    DeviceConfigurationError
        If the identifier is not owned by this repository.
    """

    identifier: str
    geometry: PinchGeometry
    fields: FieldProgramme
    limits: OperationalLimits
    registry: RegistryBinding

    def __post_init__(self) -> None:
        """Validate identifier ownership.

        Raises
        ------
        DeviceConfigurationError
            If the identifier is not owned by this repository.
        """
        if self.identifier not in OWNED_CONFIGURATIONS:
            raise DeviceConfigurationError(
                f"identifier: {self.identifier!r} is not owned by "
                f"SCPN-RFP-CORE; owned: {OWNED_CONFIGURATIONS!r}"
            )

    def derived_pinch_parameter(self) -> float:
        """Pinch parameter derived from the declared current.

        Returns
        -------
        float
            ``Theta = B_theta(a) / <B_phi>`` with
            ``B_theta(a) = mu0 I_p / (2 pi a)``.
        """
        return (
            self.limits.edge_poloidal_field_t(self.geometry)
            / self.fields.average_toroidal_field_t
        )

    def consistency_report(self) -> tuple[ConsistencyFinding, ...]:
        """Report physics-consistency findings without failing.

        Returns
        -------
        tuple of ConsistencyFinding
            Advisory findings from the documented estimates; empty when
            the declared programme is internally consistent. Findings
            are advisory instruments, not machine claims.
        """
        findings: list[ConsistencyFinding] = []
        declared = self.fields.pinch_parameter
        derived = self.derived_pinch_parameter()
        if abs(declared - derived) / derived > THETA_MISMATCH_TOLERANCE:
            findings.append(
                ConsistencyFinding(
                    field="fields.pinch_parameter",
                    message=(
                        f"declared pinch parameter {declared:.3f} deviates "
                        f"more than {THETA_MISMATCH_TOLERANCE:.0%} from the "
                        f"current-derived value {derived:.3f}"
                    ),
                )
            )
        if declared < TAYLOR_RELAXATION_MIN_THETA:
            findings.append(
                ConsistencyFinding(
                    field="fields.pinch_parameter",
                    message=(
                        f"pinch parameter {declared:.3f} is below the "
                        "Taylor-relaxation reversal threshold "
                        f"{TAYLOR_RELAXATION_MIN_THETA:.1f}"
                    ),
                )
            )
        return tuple(findings)

    def to_record(self) -> dict[str, Any]:
        """Project the configuration to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Nested record with every declared parameter.
        """
        return {
            "identifier": self.identifier,
            "geometry": {
                "major_radius_m": self.geometry.major_radius_m,
                "minor_radius_m": self.geometry.minor_radius_m,
            },
            "fields": {
                "reversal_parameter": self.fields.reversal_parameter,
                "pinch_parameter": self.fields.pinch_parameter,
                "average_toroidal_field_t": self.fields.average_toroidal_field_t,
            },
            "limits": {
                "plasma_current_ma": self.limits.plasma_current_ma,
                "flat_top_duration_s": self.limits.flat_top_duration_s,
            },
            "registry": {
                "version": self.registry.version,
                "digest_sha256": self.registry.digest_sha256,
            },
        }

    def canonical_bytes(self) -> bytes:
        """Serialise the configuration canonically.

        Returns
        -------
        bytes
            UTF-8 JSON with sorted keys, minimal separators, and a
            trailing newline; NaN and infinity are never emitted.
        """
        text = json.dumps(
            self.to_record(),
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        return (text + "\n").encode("utf-8")

    def digest_sha256(self) -> str:
        """Identify the exact parameter set.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def _require_mapping(record: dict[str, Any], field: str) -> dict[str, Any]:
    """Return one required mapping field of a record.

    Parameters
    ----------
    record
        Parent mapping under inspection.
    field
        Key that must hold a mapping.

    Returns
    -------
    dict[str, Any]
        The nested mapping.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a mapping.
    """
    value = record.get(field)
    if not isinstance(value, dict):
        raise DeviceConfigurationError(f"{field}: must be an object")
    return value


def _number(record: dict[str, Any], field: str) -> float:
    """Return one required real-number field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a real number.

    Returns
    -------
    float
        The numeric value; booleans are rejected.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a real number.
    """
    value = record.get(field)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise DeviceConfigurationError(f"{field}: must be a number, got {value!r}")
    return float(value)


def _string(record: dict[str, Any], field: str) -> str:
    """Return one required string field of a record.

    Parameters
    ----------
    record
        Mapping under inspection.
    field
        Key that must hold a string.

    Returns
    -------
    str
        The string value.

    Raises
    ------
    DeviceConfigurationError
        If the field is missing or not a string.
    """
    value = record.get(field)
    if not isinstance(value, str):
        raise DeviceConfigurationError(f"{field}: must be a string, got {value!r}")
    return value


def configuration_from_record(record: Any) -> DeviceConfiguration:
    """Build a validated configuration from a decoded record.

    Parameters
    ----------
    record
        Decoded JSON object in the shape produced by
        :meth:`DeviceConfiguration.to_record`.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the record shape or any value violates the model.
    """
    if not isinstance(record, dict):
        raise DeviceConfigurationError("record: must be an object")
    known = {"identifier", "geometry", "fields", "limits", "registry"}
    unknown = sorted(set(record) - known)
    if unknown:
        raise DeviceConfigurationError(f"record: unknown fields {unknown!r}")
    geometry = _require_mapping(record, "geometry")
    fields = _require_mapping(record, "fields")
    limits = _require_mapping(record, "limits")
    registry = _require_mapping(record, "registry")
    return DeviceConfiguration(
        identifier=_string(record, "identifier"),
        geometry=PinchGeometry(
            major_radius_m=_number(geometry, "major_radius_m"),
            minor_radius_m=_number(geometry, "minor_radius_m"),
        ),
        fields=FieldProgramme(
            reversal_parameter=_number(fields, "reversal_parameter"),
            pinch_parameter=_number(fields, "pinch_parameter"),
            average_toroidal_field_t=_number(fields, "average_toroidal_field_t"),
        ),
        limits=OperationalLimits(
            plasma_current_ma=_number(limits, "plasma_current_ma"),
            flat_top_duration_s=_number(limits, "flat_top_duration_s"),
        ),
        registry=RegistryBinding(
            version=_string(registry, "version"),
            digest_sha256=_string(registry, "digest_sha256"),
        ),
    )


def configuration_from_bytes(data: bytes) -> DeviceConfiguration:
    """Build a validated configuration from canonical JSON bytes.

    Parameters
    ----------
    data
        UTF-8 JSON document; NaN and infinity literals are rejected.

    Returns
    -------
    DeviceConfiguration
        The fully validated configuration.

    Raises
    ------
    DeviceConfigurationError
        If the document is not valid strict JSON or violates the model.
    """

    def _reject_constant(literal: str) -> float:
        raise DeviceConfigurationError(
            f"record: non-finite JSON literal {literal!r} is rejected"
        )

    try:
        record = json.loads(data.decode("utf-8"), parse_constant=_reject_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DeviceConfigurationError(f"record: invalid JSON document: {exc}") from exc
    return configuration_from_record(record)
