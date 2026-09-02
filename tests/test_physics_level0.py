# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — level-0 record tests

"""Composition, identity, wiring, immutability pin and refusals of the record."""

from __future__ import annotations

import hashlib
import json
import math

import pytest

from physics_fixtures import configuration, inputs
from scpn_rfp_core import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_RADIAL_STATIONS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    level0_physics,
)
from scpn_rfp_core.errors import DeviceConfigurationError

REFERENCE_REVERSED_SHA256 = (
    "bfcb3b2244298c477def999e46e5345c0b86ca71a3253fb5af803e82b11ab9be"
)
REFERENCE_UNREVERSED_SHA256 = (
    "3dc88cf7c9bc261513c5993fddac33b04da2ada77cb4f9da8e1b9c4d51b5bd68"
)


def test_record_composes_every_model_and_is_canonical() -> None:
    """The record carries the configuration digest, the state and the profile."""
    config = configuration()
    record = level0_physics(config, inputs())
    assert isinstance(record, Level0PhysicsRecord)
    projected = record.to_record()
    assert projected["schema"] == LEVEL0_SCHEMA
    assert projected["schema_version"] == LEVEL0_SCHEMA_VERSION
    assert projected["non_claims"] == list(LEVEL0_NON_CLAIMS)
    assert projected["configuration_digest_sha256"] == config.digest_sha256()
    assert projected["inputs"] == {"radial_stations": list(LEVEL0_RADIAL_STATIONS)}
    assert len(projected["profile"]) == 5
    assert set(projected) == {
        "schema",
        "schema_version",
        "non_claims",
        "configuration_digest_sha256",
        "inputs",
        "relaxed",
        "profile",
    }
    data = record.canonical_bytes()
    assert data.endswith(b"\n")
    assert json.loads(data) == projected
    assert record.digest_sha256() == hashlib.sha256(data).hexdigest()
    assert level0_physics(config, inputs()).digest_sha256() == record.digest_sha256()


def test_reference_digests_are_pinned() -> None:
    """The reversed and unreversed reference records are immutability fixtures."""
    reversed_record = level0_physics(configuration(), inputs())
    assert reversed_record.digest_sha256() == REFERENCE_REVERSED_SHA256
    unreversed = level0_physics(
        configuration(pinch_parameter=1.0, plasma_current_ma=0.625), inputs()
    )
    assert unreversed.digest_sha256() == REFERENCE_UNREVERSED_SHA256


def test_models_are_wired_to_the_configuration_and_each_other() -> None:
    """The profile uses the state's axis field and the configuration's radii."""
    record = level0_physics(configuration(), inputs())
    assert record.relaxed.reversed is True
    assert record.profile[0].toroidal_field_t == record.relaxed.axis_field_t
    assert record.profile[-1].radius_m == 0.5
    assert math.isclose(
        record.profile[-1].toroidal_field_t / 0.25,
        record.relaxed.bfm_reversal_parameter,
        rel_tol=1.0e-14,
    )
    assert record.relaxed.reversal_radius_m is not None
    inside = [
        s for s in record.profile if s.radius_m > record.relaxed.reversal_radius_m
    ]
    assert inside
    assert all(s.toroidal_field_t < 0.0 for s in inside)
    outside = [
        s for s in record.profile if s.radius_m < record.relaxed.reversal_radius_m
    ]
    assert all(s.toroidal_field_t > 0.0 for s in outside)
    unreversed = level0_physics(configuration(pinch_parameter=1.0), inputs())
    assert unreversed.relaxed.reversal_radius_m is None
    assert all(s.toroidal_field_t > 0.0 for s in unreversed.profile)


def test_inputs_record_and_validation() -> None:
    """The stations are projected and validated: non-empty, in range, increasing."""
    model = inputs((0.0, 0.5, 1.0))
    assert model.to_record() == {"radial_stations": [0.0, 0.5, 1.0]}
    assert isinstance(model, ModelInputs)
    with pytest.raises(DeviceConfigurationError, match="at least one station"):
        ModelInputs(radial_stations=())
    with pytest.raises(DeviceConfigurationError, match=r"radial_stations\[1\]"):
        ModelInputs(radial_stations=(0.0, 1.5))
    with pytest.raises(DeviceConfigurationError, match=r"radial_stations\[0\]"):
        ModelInputs(radial_stations=(math.nan, 1.0))
    with pytest.raises(DeviceConfigurationError, match="strictly increasing"):
        ModelInputs(radial_stations=(0.5, 0.5))
    with pytest.raises(DeviceConfigurationError, match="strictly increasing"):
        ModelInputs(radial_stations=(1.0, 0.0))
    assert ModelInputs(radial_stations=(0.3,)).radial_stations == (0.3,)


def test_record_refuses_a_configuration_beyond_the_model() -> None:
    """A pinch parameter at or beyond j_{1,1} / 2 refuses the whole record."""
    with pytest.raises(DeviceConfigurationError, match="j_1,1 / 2"):
        level0_physics(configuration(pinch_parameter=2.0), inputs())
