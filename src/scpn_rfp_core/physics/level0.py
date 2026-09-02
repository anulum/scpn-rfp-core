# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — level-0 physics record

"""Level-0 physics record of one validated reversed-field-pinch configuration.

The record composes the Bessel-function relaxed state (R. Paccagnella,
arXiv:1509.07307v2 (2015), eqs. 4-5, taken as the single-region Taylor
state) and its radial profile at the declared stations on the validated
:class:`~scpn_rfp_core.configuration.DeviceConfiguration`. It serialises
canonically with a SHA-256 digest and states its own non-claims: every
number is a closed-form evaluation on a synthetic configuration, at
``computational_prototype`` maturity; no equation is solved.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Final

from scpn_rfp_core.configuration import DeviceConfiguration
from scpn_rfp_core.errors import DeviceConfigurationError
from scpn_rfp_core.physics.profiles import (
    RadialStation,
    radial_profile,
    require_station,
)
from scpn_rfp_core.physics.relaxation import RelaxedState, relaxed_state

LEVEL0_SCHEMA: Final = "scpn.rfp-level0-physics.v1"
LEVEL0_SCHEMA_VERSION: Final = "1.0.0"
#: The plan's radial stations ``r / a``.
LEVEL0_RADIAL_STATIONS: Final = (0.0, 0.25, 0.5, 0.75, 1.0)
LEVEL0_NON_CLAIMS: Final = (
    "closed-form evaluation of the cylindrical Bessel-function relaxed state "
    "on a synthetic configuration",
    "the Bessel-function model is the fully relaxed single-region state; real "
    "reversed-field pinches depart from it and no equation is solved: no "
    "equilibrium, transport, dynamo or stability calculation",
    "no confinement, fusion power, gain or breakeven statement",
    "no value describes or validates any real machine; the anchors reproduce "
    "identities of the model and the printed zeros of the Bessel functions",
)


@dataclass(frozen=True, slots=True)
class ModelInputs:
    """Declared inputs of the level-0 models beyond the configuration.

    Parameters
    ----------
    radial_stations
        Normalised radii ``r / a`` at which the profile is evaluated;
        non-empty, each within ``[0, 1]``, strictly increasing.

    Raises
    ------
    DeviceConfigurationError
        If the stations are empty, out of range or not strictly increasing.
    """

    radial_stations: tuple[float, ...]

    def __post_init__(self) -> None:
        """Validate the declared stations.

        Raises
        ------
        DeviceConfigurationError
            If the stations are empty, out of range or not strictly
            increasing.
        """
        if not self.radial_stations:
            raise DeviceConfigurationError(
                "radial_stations: at least one station is required"
            )
        for index, fraction in enumerate(self.radial_stations):
            require_station(f"radial_stations[{index}]", fraction)
        if any(
            later <= earlier
            for earlier, later in zip(
                self.radial_stations, self.radial_stations[1:], strict=False
            )
        ):
            raise DeviceConfigurationError(
                "radial_stations: must be strictly increasing, got "
                f"{self.radial_stations!r}"
            )

    def to_record(self) -> dict[str, Any]:
        """Project the inputs to a JSON-serialisable record.

        Returns
        -------
        dict[str, Any]
            Every field under its name.
        """
        return {"radial_stations": list(self.radial_stations)}


@dataclass(frozen=True, slots=True)
class Level0PhysicsRecord:
    """The level-0 models evaluated on one configuration.

    Parameters
    ----------
    configuration_digest_sha256
        Digest of the validated configuration the record was built from.
    inputs
        Declared model inputs.
    relaxed
        The Bessel-function relaxed state.
    profile
        The relaxed-state profile at the declared stations.
    """

    configuration_digest_sha256: str
    inputs: ModelInputs
    relaxed: RelaxedState
    profile: tuple[RadialStation, ...]

    def to_record(self) -> dict[str, Any]:
        """Project the record to a JSON-serialisable object.

        Returns
        -------
        dict[str, Any]
            Schema identity, non-claims, and every model record.
        """
        return {
            "schema": LEVEL0_SCHEMA,
            "schema_version": LEVEL0_SCHEMA_VERSION,
            "non_claims": list(LEVEL0_NON_CLAIMS),
            "configuration_digest_sha256": self.configuration_digest_sha256,
            "inputs": self.inputs.to_record(),
            "relaxed": self.relaxed.to_record(),
            "profile": [station.to_record() for station in self.profile],
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
        """Identify the exact record.

        Returns
        -------
        str
            SHA-256 digest of :meth:`canonical_bytes` as lowercase hex.
        """
        return hashlib.sha256(self.canonical_bytes()).hexdigest()


def level0_physics(
    configuration: DeviceConfiguration, inputs: ModelInputs
) -> Level0PhysicsRecord:
    """Evaluate every level-0 model on a validated configuration.

    Parameters
    ----------
    configuration
        Validated reversed-field-pinch configuration.
    inputs
        Declared model inputs.

    Returns
    -------
    Level0PhysicsRecord
        The composed record.

    Raises
    ------
    DeviceConfigurationError
        If the declared pinch parameter is outside the model's domain.
    """
    relaxed = relaxed_state(configuration)
    profile = radial_profile(
        configuration, relaxed.axis_field_t, inputs.radial_stations
    )
    return Level0PhysicsRecord(
        configuration_digest_sha256=configuration.digest_sha256(),
        inputs=inputs,
        relaxed=relaxed,
        profile=profile,
    )
