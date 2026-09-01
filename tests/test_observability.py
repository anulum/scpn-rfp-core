# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — diagnostic and clock semantics tests

"""Every branch of the diagnostic plan model and its parsers.

All plans in this module are synthetic fixtures; none describes any real
diagnostic, measurement, or facility.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

import pytest

from scpn_rfp_core.errors import DiagnosticPlanError
from scpn_rfp_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
    OBSERVABILITY_CATALOGUE_DIGEST,
    OBSERVABILITY_CATALOGUE_VERSION,
    CandidateProfile,
    ClockKind,
    ClockModel,
    ClockRelation,
    DeferredCandidate,
    DiagnosticChannelPlan,
    DiagnosticPlan,
    FrameKind,
    ObservabilityBinding,
    ObservabilityClass,
    ReferenceFrame,
    SemanticCarrier,
    plan_from_bytes,
    plan_from_record,
)

DERIVED_BINDINGS = {
    "calibration": "synthetic coil transfer functions",
    "clock_epoch": "clk_facility",
    "mode_identity": "declared instability mode labels",
    "observability_threshold": "declared amplitude floor",
    "observation_operator": "synthetic coil-array projection operator",
    "operator_validation": "operator exercised on synthetic fields",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "reference_signal": "synthetic reference oscillator",
    "uncertainty": "declared amplitude and phase bounds",
    "validity": "synthetic validity window",
}
NONCYCLIC_BINDINGS = {
    "calibration": "synthetic calibration set",
    "clock_epoch": "clk_shot",
    "coordinate_frame": "frm_flux",
    "provenance": "synthetic fixture",
    "quality": "synthetic quality flags",
    "uncertainty": "declared bounds",
    "units": "SI units declared per field",
    "validity": "synthetic validity window",
}
NUMERICAL_BINDINGS = {
    "initial_condition": "synthetic initial state",
    "model_revision": "model revision identifier",
    "provenance": "synthetic fixture",
    "simulation_clock": "clk_sim",
    "solver_validity": "declared solver validity envelope",
}


REFERENCE_FRAMES = (
    ReferenceFrame(
        identifier="frm_flux",
        kind=FrameKind.FLUX_SURFACE,
        description="flux-surface label frame from the equilibrium set",
    ),
    ReferenceFrame(
        identifier="frm_machine",
        kind=FrameKind.MACHINE_CYLINDRICAL,
        description="machine cylindrical R-phi-Z frame",
    ),
)
CLOCK_RELATIONS = (
    ClockRelation(
        child_identifier="clk_shot",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method=(
            "synthetic declaration: trigger timestamped against the "
            "facility oscillator; no correlation evidence claimed"
        ),
        mapping_state="unmapped",
        evidence_claimed=False,
    ),
)


def clock_facility() -> ClockModel:
    """Build the synthetic facility master clock."""
    return ClockModel(
        identifier="clk_facility",
        kind=ClockKind.FACILITY_MONOTONIC,
        epoch="facility master oscillator zero",
        resolution_s=1.0e-8,
        uncertainty_s=5.0e-9,
    )


def clock_shot() -> ClockModel:
    """Build the synthetic shot-epoch clock."""
    return ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="discharge initiation trigger t0",
        resolution_s=1.0e-6,
        uncertainty_s=1.0e-6,
    )


def clock_simulation() -> ClockModel:
    """Build the synthetic simulation clock."""
    return ClockModel(
        identifier="clk_sim",
        kind=ClockKind.SIMULATION,
        epoch="solver step zero",
        resolution_s=1.0e-9,
        uncertainty_s=0.0,
    )


def channel_noncyclic_one() -> DiagnosticChannelPlan:
    """Build the synthetic flux-loop equilibrium channel."""
    return DiagnosticChannelPlan(
        identifier="ch_flux_loop_set",
        candidate_id="closed.equilibrium_profiles",
        carrier=SemanticCarrier.BOUNDED_FEATURE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e04,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.5,
        element_count=8,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        synthetic=True,
    )


def channel_noncyclic_two() -> DiagnosticChannelPlan:
    """Build the synthetic Rogowski plasma-current channel."""
    return DiagnosticChannelPlan(
        identifier="ch_rogowski_coil",
        candidate_id="closed.equilibrium_profiles",
        carrier=SemanticCarrier.BOUNDED_FEATURE,
        clock_identifier="clk_shot",
        sample_rate_hz=1.0e06,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.5,
        element_count=1,
        evidence_bindings=dict(NONCYCLIC_BINDINGS),
        synthetic=True,
    )


def channel_derived() -> DiagnosticChannelPlan:
    """Build the synthetic toroidal magnetic-probe array channel."""
    return DiagnosticChannelPlan(
        identifier="ch_toroidal_probe_array",
        candidate_id="closed.resolved_mhd_mode",
        carrier=SemanticCarrier.COMPLEX_MODE,
        clock_identifier="clk_facility",
        sample_rate_hz=2.0e06,
        max_signal_frequency_hz=1.0e05,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.5,
        element_count=32,
        evidence_bindings=dict(DERIVED_BINDINGS),
        synthetic=True,
    )


def channel_oscillator() -> DiagnosticChannelPlan:
    """Build the synthetic model-oscillator channel."""
    return DiagnosticChannelPlan(
        identifier="ch_synthetic_oscillator",
        candidate_id="model.synthetic_oscillator_coordinate",
        carrier=SemanticCarrier.NUMERICAL_PHASE,
        clock_identifier="clk_sim",
        sample_rate_hz=1.0e4,
        max_signal_frequency_hz=0.0,
        timing_uncertainty_s=None,
        acquisition_start_s=0.0,
        acquisition_duration_s=0.1,
        element_count=1,
        evidence_bindings=dict(NUMERICAL_BINDINGS),
        synthetic=True,
    )


def synthetic_plan() -> DiagnosticPlan:
    """Build a fully valid synthetic diagnostic plan."""
    return DiagnosticPlan(
        identifier="rfp_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        channels=(
            channel_noncyclic_one(),
            channel_noncyclic_two(),
            channel_oscillator(),
            channel_derived(),
        ),
        deferrals=(),
    )


def test_embedded_catalogue_subset_is_exact() -> None:
    """The embedded subset lists exactly the applicable candidates."""
    identifiers = [candidate.candidate_id for candidate in APPLICABLE_CANDIDATES]
    assert identifiers == [
        "closed.equilibrium_profiles",
        "closed.resolved_mhd_mode",
        "model.synthetic_oscillator_coordinate",
    ]
    assert CATALOGUE_BINDING.catalogue_version == OBSERVABILITY_CATALOGUE_VERSION
    assert CATALOGUE_BINDING.catalogue_digest_sha256 == OBSERVABILITY_CATALOGUE_DIGEST


def test_candidate_properties_follow_class_tables() -> None:
    """Carriers and evidence vocabularies are fixed by the class."""
    by_id = {candidate.candidate_id: candidate for candidate in APPLICABLE_CANDIDATES}
    mhd = by_id["closed.resolved_mhd_mode"]
    assert SemanticCarrier.COMPLEX_MODE in mhd.admissible_carriers
    assert "observation_operator" in mhd.required_evidence
    numerical = by_id["model.synthetic_oscillator_coordinate"]
    assert numerical.admissible_carriers == {SemanticCarrier.NUMERICAL_PHASE}
    assert "simulation_clock" in numerical.required_evidence


def test_binding_rejects_empty_catalogue_version() -> None:
    """An empty catalogue version is rejected."""
    with pytest.raises(DiagnosticPlanError, match="catalogue_version"):
        ObservabilityBinding(
            catalogue_version="",
            catalogue_digest_sha256="0" * 64,
            reactor_registry_version="1.0.0",
            reactor_registry_digest_sha256="0" * 64,
        )


def test_binding_rejects_empty_registry_version() -> None:
    """An empty reactor registry version is rejected."""
    with pytest.raises(DiagnosticPlanError, match="reactor_registry_version"):
        ObservabilityBinding(
            catalogue_version="1.0.0",
            catalogue_digest_sha256="0" * 64,
            reactor_registry_version="",
            reactor_registry_digest_sha256="0" * 64,
        )


@pytest.mark.parametrize(
    ("catalogue_digest", "registry_digest"),
    [("XYZ", "0" * 64), ("0" * 64, "abc")],
)
def test_binding_rejects_malformed_digests(
    catalogue_digest: str, registry_digest: str
) -> None:
    """Digests must be 64 lowercase hexadecimal characters."""
    with pytest.raises(DiagnosticPlanError, match="digest_sha256"):
        ObservabilityBinding(
            catalogue_version="1.0.0",
            catalogue_digest_sha256=catalogue_digest,
            reactor_registry_version="1.0.0",
            reactor_registry_digest_sha256=registry_digest,
        )


def test_candidate_rejects_malformed_identifier() -> None:
    """A malformed candidate identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match="candidate_id"):
        CandidateProfile(
            candidate_id="Bad-Id",
            phenomenon="x",
            configurations=("reversed_field_pinch",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_empty_phenomenon() -> None:
    """An empty phenomenon statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="phenomenon"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="",
            configurations=("reversed_field_pinch",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_empty_configurations() -> None:
    """A candidate without configurations is rejected."""
    with pytest.raises(DiagnosticPlanError, match="configurations"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=(),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_unsorted_configurations() -> None:
    """Duplicated configurations are rejected."""
    with pytest.raises(DiagnosticPlanError, match="unique and sorted"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=("reversed_field_pinch", "reversed_field_pinch"),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_candidate_rejects_foreign_configuration() -> None:
    """A configuration owned by another repository is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not owned"):
        CandidateProfile(
            candidate_id="a.b",
            phenomenon="x",
            configurations=("conventional_tokamak",),
            observability_class=ObservabilityClass.NONCYCLIC_FEATURE,
        )


def test_clock_rejects_malformed_identifier() -> None:
    """A malformed clock identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"clock\.identifier"):
        ClockModel(
            identifier="Clock!",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


def test_clock_rejects_empty_epoch() -> None:
    """An empty epoch statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="epoch"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="",
            resolution_s=1.0e-9,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("resolution", [0.0, -1.0, float("nan"), float("inf")])
def test_clock_rejects_bad_resolution(resolution: float) -> None:
    """Non-positive or non-finite resolutions are rejected."""
    with pytest.raises(DiagnosticPlanError, match="resolution_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=resolution,
            uncertainty_s=0.0,
        )


@pytest.mark.parametrize("uncertainty", [-1.0e-9, float("nan")])
def test_clock_rejects_bad_uncertainty(uncertainty: float) -> None:
    """Negative or non-finite uncertainties are rejected."""
    with pytest.raises(DiagnosticPlanError, match="uncertainty_s"):
        ClockModel(
            identifier="clk",
            kind=ClockKind.SIMULATION,
            epoch="x",
            resolution_s=1.0e-9,
            uncertainty_s=uncertainty,
        )


def _derived(**overrides: Any) -> DiagnosticChannelPlan:
    """Build the Mirnov channel with keyword overrides applied."""
    values: dict[str, Any] = {
        "identifier": "ch_toroidal_probe_array",
        "candidate_id": "closed.resolved_mhd_mode",
        "carrier": SemanticCarrier.COMPLEX_MODE,
        "clock_identifier": "clk_facility",
        "sample_rate_hz": 2.0e06,
        "max_signal_frequency_hz": 1.0e05,
        "timing_uncertainty_s": None,
        "acquisition_start_s": 0.0,
        "acquisition_duration_s": 0.5,
        "element_count": 32,
        "evidence_bindings": dict(DERIVED_BINDINGS),
        "synthetic": True,
    }
    values.update(overrides)
    return DiagnosticChannelPlan(**values)


def test_channel_rejects_timing_uncertainty() -> None:
    """No applicable candidate is event-relative, so the member must be None."""
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        _derived(timing_uncertainty_s=1.0e-5)


def test_record_carries_null_timing_uncertainty_on_every_channel() -> None:
    """The portable record declares the member as null on every channel."""
    record = synthetic_plan().to_record()
    assert all(entry["timing_uncertainty_s"] is None for entry in record["channels"])
    assert plan_from_record(record) == synthetic_plan()


@pytest.mark.parametrize(
    "value", [True, "1e-5", [1.0e-5], float("nan"), float("inf"), float("-inf")]
)
def test_parser_rejects_non_numeric_timing_uncertainty(value: Any) -> None:
    """Only a finite number or null is accepted for the nullable member."""
    record = synthetic_plan().to_record()
    record["channels"][0]["timing_uncertainty_s"] = value
    with pytest.raises(DiagnosticPlanError, match="number or null"):
        plan_from_record(record)


def test_parser_rejects_numeric_timing_uncertainty() -> None:
    """A numeric value parses but the channel model refuses it."""
    record = synthetic_plan().to_record()
    record["channels"][0]["timing_uncertainty_s"] = 1.0e-5
    with pytest.raises(DiagnosticPlanError, match="only event-relative"):
        plan_from_record(record)


def test_channel_rejects_malformed_identifier() -> None:
    """A malformed channel identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"channel\.identifier"):
        _derived(identifier="Channel!")


def test_channel_rejects_unknown_candidate() -> None:
    """A candidate outside the embedded subset is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not applicable"):
        _derived(candidate_id="closed.recurrent_transient")


def test_channel_rejects_inadmissible_carrier() -> None:
    """A carrier outside the class table is rejected."""
    with pytest.raises(DiagnosticPlanError, match="not admissible"):
        _derived(carrier=SemanticCarrier.BOUNDED_FEATURE)


def test_channel_rejects_malformed_clock_identifier() -> None:
    """A malformed clock reference is rejected."""
    with pytest.raises(DiagnosticPlanError, match="clock_identifier"):
        _derived(clock_identifier="Clock!")


@pytest.mark.parametrize("rate", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_sample_rate(rate: float) -> None:
    """Non-positive or non-finite sampling rates are rejected."""
    with pytest.raises(DiagnosticPlanError, match="sample_rate_hz"):
        _derived(sample_rate_hz=rate)


@pytest.mark.parametrize("frequency", [-1.0, float("inf")])
def test_channel_rejects_bad_signal_frequency(frequency: float) -> None:
    """Negative or non-finite signal frequencies are rejected."""
    with pytest.raises(DiagnosticPlanError, match="max_signal_frequency_hz"):
        _derived(max_signal_frequency_hz=frequency)


def test_channel_rejects_cyclic_zero_band() -> None:
    """A cyclic channel must declare a positive signal band."""
    with pytest.raises(DiagnosticPlanError, match="positive signal band"):
        _derived(max_signal_frequency_hz=0.0)


def test_channel_rejects_nyquist_violation() -> None:
    """Sampling below twice the signal band is rejected."""
    with pytest.raises(DiagnosticPlanError, match="Nyquist"):
        _derived(sample_rate_hz=5.0e04)


def test_channel_rejects_evidence_key_mismatch() -> None:
    """Missing and extra evidence slots are both rejected."""
    bindings = dict(DERIVED_BINDINGS)
    del bindings["mode_identity"]
    bindings["surprise"] = "x"
    with pytest.raises(DiagnosticPlanError, match=r"missing=.*extra="):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_empty_evidence_statement() -> None:
    """An empty evidence statement is rejected."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["quality"] = ""
    with pytest.raises(DiagnosticPlanError, match="quality"):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_clock_binding_mismatch() -> None:
    """The clock evidence slot must reference the bound clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_other"
    with pytest.raises(DiagnosticPlanError, match="must reference the bound clock"):
        _derived(evidence_bindings=bindings)


def test_channel_rejects_non_synthetic() -> None:
    """No channel in this repository may claim to be real."""
    with pytest.raises(DiagnosticPlanError, match="synthetic"):
        _derived(synthetic=False)


def test_channel_exposes_observability_class() -> None:
    """The class property resolves through the embedded catalogue."""
    assert channel_derived().observability_class is ObservabilityClass.DERIVED_CYCLIC


def test_deferral_rejects_unknown_candidate() -> None:
    """A deferral must name an applicable candidate."""
    with pytest.raises(DiagnosticPlanError, match=r"not.*applicable"):
        DeferredCandidate(candidate_id="closed.recurrent_transient", reason="x")


def test_deferral_rejects_empty_reason() -> None:
    """A deferral must carry a reason."""
    with pytest.raises(DiagnosticPlanError, match="reason"):
        DeferredCandidate(
            candidate_id="model.synthetic_oscillator_coordinate", reason=""
        )


def test_plan_accepts_reference_fixture() -> None:
    """The reference plan validates and reports no findings."""
    plan = synthetic_plan()
    assert plan.consistency_report() == ()


def test_plan_accepts_explicit_deferral() -> None:
    """A deferred candidate satisfies the coverage rule."""
    plan = DiagnosticPlan(
        identifier="rfp_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        channels=(
            channel_noncyclic_one(),
            channel_noncyclic_two(),
            channel_derived(),
        ),
        deferrals=(
            DeferredCandidate(
                candidate_id="model.synthetic_oscillator_coordinate",
                reason="synthetic oscillator adds no exercised content here",
            ),
        ),
    )
    assert plan.deferrals[0].candidate_id == ("model.synthetic_oscillator_coordinate")


def test_plan_rejects_malformed_identifier() -> None:
    """A malformed plan identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.identifier"):
        DiagnosticPlan(
            identifier="Plan!",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_plan_rejects_foreign_binding() -> None:
    """A binding to any other catalogue release is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.binding"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=ObservabilityBinding(
                catalogue_version="9.9.9",
                catalogue_digest_sha256="0" * 64,
                reactor_registry_version="1.0.0",
                reactor_registry_digest_sha256="0" * 64,
            ),
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_plan_rejects_unsorted_clocks() -> None:
    """Clocks must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.clocks"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_shot(), clock_facility(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_plan_rejects_unsorted_channels() -> None:
    """Channels must be unique and sorted by identifier."""
    with pytest.raises(DiagnosticPlanError, match=r"plan\.channels"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_two(),
                channel_noncyclic_one(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_plan_rejects_duplicate_deferrals() -> None:
    """Deferrals must be unique and sorted by candidate identifier."""
    deferral = DeferredCandidate(
        candidate_id="model.synthetic_oscillator_coordinate",
        reason="synthetic oscillator adds no exercised content here",
    )
    with pytest.raises(DiagnosticPlanError, match=r"plan\.deferrals"):
        DiagnosticPlan(
            identifier="rfp_partial_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_derived(),
            ),
            deferrals=(deferral, deferral),
        )


def test_plan_rejects_undeclared_clock() -> None:
    """A channel bound to an undeclared clock is rejected."""
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_plan_rejects_incompatible_clock_kind() -> None:
    """A cyclic channel cannot bind to a shot-epoch clock."""
    bindings = dict(DERIVED_BINDINGS)
    bindings["clock_epoch"] = "clk_shot"
    channel = _derived(clock_identifier="clk_shot", evidence_bindings=bindings)
    with pytest.raises(DiagnosticPlanError, match="incompatible with class"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel,
            ),
            deferrals=(),
        )


def test_plan_rejects_planned_and_deferred_overlap() -> None:
    """A candidate cannot be both planned and deferred."""
    with pytest.raises(DiagnosticPlanError, match="both planned and deferred"):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_oscillator(),
                channel_derived(),
            ),
            deferrals=(
                DeferredCandidate(
                    candidate_id="model.synthetic_oscillator_coordinate",
                    reason="x",
                ),
            ),
        )


def test_plan_rejects_incomplete_coverage() -> None:
    """Every applicable candidate must be planned or deferred."""
    with pytest.raises(DiagnosticPlanError, match="missing="):
        DiagnosticPlan(
            identifier="rfp_reference_plan",
            binding=CATALOGUE_BINDING,
            clocks=(clock_facility(), clock_shot(), clock_simulation()),
            frames=REFERENCE_FRAMES,
            clock_relations=CLOCK_RELATIONS,
            channels=(
                channel_noncyclic_one(),
                channel_noncyclic_two(),
                channel_derived(),
            ),
            deferrals=(),
        )


def test_report_flags_band_outside_typical_range() -> None:
    """A band outside the device-typical scale draws the advisory."""
    channel = _derived(sample_rate_hz=1.0e07, max_signal_frequency_hz=5.0e06)
    plan = DiagnosticPlan(
        identifier="rfp_reference_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot(), clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        channels=(
            channel_noncyclic_one(),
            channel_noncyclic_two(),
            channel_oscillator(),
            channel,
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "Ortolani" in findings[0].message


def test_report_flags_clock_coarser_than_sampling() -> None:
    """A clock that cannot separate samples draws the advisory."""
    clock = ClockModel(
        identifier="clk_shot",
        kind=ClockKind.SHOT_EVENT_EPOCH,
        epoch="discharge initiation trigger t0",
        resolution_s=1.0e-2,
        uncertainty_s=1.0e-6,
    )
    plan = DiagnosticPlan(
        identifier="rfp_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock, clock_simulation()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        channels=(
            channel_noncyclic_one(),
            channel_oscillator(),
            channel_derived(),
        ),
        deferrals=(),
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "cannot distinguish" in findings[0].message


def test_round_trip_preserves_deferrals() -> None:
    """A plan with an explicit deferral survives the record round-trip."""
    plan = DiagnosticPlan(
        identifier="rfp_partial_plan",
        binding=CATALOGUE_BINDING,
        clocks=(clock_facility(), clock_shot()),
        frames=REFERENCE_FRAMES,
        clock_relations=CLOCK_RELATIONS,
        channels=(
            channel_noncyclic_one(),
            channel_noncyclic_two(),
            channel_derived(),
        ),
        deferrals=(
            DeferredCandidate(
                candidate_id="model.synthetic_oscillator_coordinate",
                reason="synthetic oscillator adds no exercised content here",
            ),
        ),
    )
    assert plan_from_record(plan.to_record()) == plan


def test_round_trip_preserves_digest() -> None:
    """Record and byte round-trips preserve the canonical digest."""
    plan = synthetic_plan()
    rebuilt = plan_from_record(plan.to_record())
    assert rebuilt == plan
    assert plan_from_bytes(plan.canonical_bytes()) == plan
    assert rebuilt.digest_sha256() == plan.digest_sha256()


def test_canonical_bytes_are_sorted_and_terminated() -> None:
    """Canonical bytes use sorted keys and end with a newline."""
    data = synthetic_plan().canonical_bytes()
    assert data.endswith(b"\n")
    decoded = json.loads(data.decode("utf-8"))
    assert list(decoded) == sorted(decoded)
    digest = hashlib.sha256(data).hexdigest()
    assert synthetic_plan().digest_sha256() == digest


def test_parser_rejects_non_object_record() -> None:
    """A non-object record is rejected."""
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record([1, 2])


def test_parser_rejects_unknown_fields() -> None:
    """Unknown top-level fields are rejected."""
    record = synthetic_plan().to_record()
    record["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown fields"):
        plan_from_record(record)


def test_parser_rejects_non_mapping_binding() -> None:
    """A non-object binding is rejected."""
    record = synthetic_plan().to_record()
    record["binding"] = 3
    with pytest.raises(DiagnosticPlanError, match="binding: must be an object"):
        plan_from_record(record)


@pytest.mark.parametrize(
    "field", ["clocks", "channels", "deferrals", "frames", "clock_relations"]
)
def test_parser_rejects_non_list_sections(field: str) -> None:
    """Every plan section must be an array."""
    record = synthetic_plan().to_record()
    record[field] = {}
    with pytest.raises(DiagnosticPlanError, match=f"{field}: must be an array"):
        plan_from_record(record)


@pytest.mark.parametrize(
    "field", ["clocks", "channels", "deferrals", "frames", "clock_relations"]
)
def test_parser_rejects_non_object_entries(field: str) -> None:
    """Every section entry must be an object."""
    record = synthetic_plan().to_record()
    record[field] = [1]
    with pytest.raises(DiagnosticPlanError, match="must be an object"):
        plan_from_record(record)


def test_parser_rejects_boolean_number() -> None:
    """Booleans are rejected where numbers are required."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["resolution_s"] = True
    with pytest.raises(DiagnosticPlanError, match="must be a number"):
        plan_from_record(record)


def test_parser_accepts_integer_numbers() -> None:
    """Plain integers satisfy numeric fields."""
    record = synthetic_plan().to_record()
    record["channels"][0]["sample_rate_hz"] = 1000
    assert plan_from_record(record).channels[0].sample_rate_hz == 1000.0


def test_parser_rejects_non_boolean_flag() -> None:
    """A non-boolean synthetic flag is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["synthetic"] = "yes"
    with pytest.raises(DiagnosticPlanError, match="must be a boolean"):
        plan_from_record(record)


def test_parser_rejects_non_string_field() -> None:
    """A non-string identifier is rejected."""
    record = synthetic_plan().to_record()
    record["identifier"] = 7
    with pytest.raises(DiagnosticPlanError, match="must be a string"):
        plan_from_record(record)


def test_parser_rejects_unknown_enum_value() -> None:
    """A value outside the enum vocabulary is rejected."""
    record = synthetic_plan().to_record()
    record["clocks"][0]["kind"] = "sundial"
    with pytest.raises(DiagnosticPlanError, match="is not one of"):
        plan_from_record(record)


def test_parser_rejects_non_string_evidence_value() -> None:
    """A non-string evidence statement is rejected."""
    record = synthetic_plan().to_record()
    record["channels"][0]["evidence_bindings"]["provenance"] = 5
    with pytest.raises(DiagnosticPlanError, match="evidence_bindings"):
        plan_from_record(record)


def test_bytes_parser_rejects_nan_literal() -> None:
    """A NaN literal in the document is rejected."""
    record = synthetic_plan().to_record()
    text = json.dumps(record).replace("10000.0", "NaN")
    with pytest.raises(DiagnosticPlanError, match="non-finite"):
        plan_from_bytes(text.encode("utf-8"))


def test_bytes_parser_rejects_invalid_json() -> None:
    """A malformed document is rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"{")


def test_bytes_parser_rejects_invalid_utf8() -> None:
    """Non-UTF-8 bytes are rejected."""
    with pytest.raises(DiagnosticPlanError, match="invalid JSON"):
        plan_from_bytes(b"\xff\xfe")


def test_frame_rejects_disallowed_kind() -> None:
    """A frame kind outside the repository's allowed set is rejected."""
    with pytest.raises(DiagnosticPlanError, match="allowed frame"):
        ReferenceFrame(
            identifier="frm_bad",
            kind=FrameKind.CHAMBER_CARTESIAN,
            description="x",
        )


def test_frame_rejects_malformed_identifier() -> None:
    """A malformed frame identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"frame\.identifier"):
        ReferenceFrame(
            identifier="Frame!",
            kind=FrameKind.FLUX_SURFACE,
            description="x",
        )


def test_frame_rejects_empty_description() -> None:
    """An empty frame description is rejected."""
    with pytest.raises(DiagnosticPlanError, match="description"):
        ReferenceFrame(
            identifier="frm_ok",
            kind=FrameKind.FLUX_SURFACE,
            description="",
        )


def test_relation_rejects_self_relation() -> None:
    """A clock cannot be related to itself."""
    with pytest.raises(DiagnosticPlanError, match="itself"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_shot",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


@pytest.mark.parametrize("value", [-1.0, float("nan"), float("inf")])
def test_relation_rejects_bad_bounds(value: float) -> None:
    """Non-finite or negative relation bounds are rejected."""
    with pytest.raises(DiagnosticPlanError, match="finite and non-negative"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=value,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_relation_rejects_empty_method() -> None:
    """A relation without a method statement is rejected."""
    with pytest.raises(DiagnosticPlanError, match="method"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_plan_rejects_undeclared_relation_clock() -> None:
    """A relation naming an undeclared clock is rejected."""
    relation = ClockRelation(
        child_identifier="clk_zz_unknown",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method="x",
        mapping_state="unmapped",
        evidence_claimed=False,
    )
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="is not declared"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, relation),
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_rejects_simulation_clock_relation() -> None:
    """The simulation clock cannot join a synchronisation relation."""
    relation = ClockRelation(
        child_identifier="clk_sim",
        parent_identifier="clk_facility",
        max_offset_s=1.0e-6,
        uncertainty_s=1.0e-7,
        method="x",
        mapping_state="unmapped",
        evidence_claimed=False,
    )
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="simulation clock"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, relation),
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_requires_epoch_to_facility_bound() -> None:
    """An epoch clock without a facility bound is rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match="must declare a bound"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(),
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_rejects_duplicate_frames() -> None:
    """Duplicate frame identifiers are rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match=r"plan\.frames"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=(*plan.frames, plan.frames[0]),
            clock_relations=plan.clock_relations,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_plan_rejects_unknown_frame_reference() -> None:
    """A coordinate_frame binding must name a declared frame."""
    plan = synthetic_plan()
    kept = tuple(frame for frame in plan.frames if frame.identifier != "frm_flux")
    with pytest.raises(DiagnosticPlanError, match="declared frame"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=kept,
            clock_relations=plan.clock_relations,
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


@pytest.mark.parametrize("start", [float("nan"), float("inf")])
def test_channel_rejects_bad_acquisition_start(start: float) -> None:
    """A non-finite acquisition start is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_start_s"):
        _derived(acquisition_start_s=start)


@pytest.mark.parametrize("duration", [0.0, -1.0, float("nan")])
def test_channel_rejects_bad_acquisition_duration(duration: float) -> None:
    """A non-positive acquisition duration is rejected."""
    with pytest.raises(DiagnosticPlanError, match="acquisition_duration_s"):
        _derived(acquisition_duration_s=duration)


@pytest.mark.parametrize("count", [0, -3, True])
def test_channel_rejects_bad_element_count(count: object) -> None:
    """A non-integer or sub-unit element count is rejected."""
    with pytest.raises(DiagnosticPlanError, match="element_count"):
        _derived(element_count=count)


def test_report_flags_window_beyond_device_ceiling() -> None:
    """An acquisition window beyond the device scale draws the advisory."""
    channel = _derived(acquisition_duration_s=10.0)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "acquisition window" in findings[0].message


def test_report_flags_array_size_outside_common_range() -> None:
    """A two-element array below the common range draws the advisory."""
    channel = _derived(element_count=2)
    plan = synthetic_plan()
    plan = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=plan.clocks,
        frames=plan.frames,
        clock_relations=plan.clock_relations,
        channels=tuple(
            channel if entry.identifier == channel.identifier else entry
            for entry in plan.channels
        ),
        deferrals=plan.deferrals,
    )
    findings = plan.consistency_report()
    assert len(findings) == 1
    assert "array size" in findings[0].message


@pytest.mark.parametrize("section", ["clocks", "channels", "frames", "clock_relations"])
def test_parser_rejects_unknown_entry_members(section: str) -> None:
    """Unknown members inside nested entries are rejected."""
    record = synthetic_plan().to_record()
    record[section][0]["surprise"] = 1
    with pytest.raises(DiagnosticPlanError, match="unknown members"):
        plan_from_record(record)


def test_parser_rejects_unknown_deferral_members() -> None:
    """Unknown members inside a deferral entry are rejected."""
    record = synthetic_plan().to_record()
    record["deferrals"] = [{"candidate_id": "x", "reason": "y", "z": 1}]
    with pytest.raises(DiagnosticPlanError, match="unknown members"):
        plan_from_record(record)


def test_bytes_parser_rejects_duplicate_members() -> None:
    """A duplicate JSON member is rejected."""
    data = synthetic_plan().canonical_bytes()
    text = data.decode("utf-8").rstrip("\n")
    tampered = text[:-1] + ',"identifier":"x"}\n'
    with pytest.raises(DiagnosticPlanError, match="duplicate member"):
        plan_from_bytes(tampered.encode("utf-8"))


def test_bytes_parser_rejects_non_canonical_document() -> None:
    """A valid but non-canonical byte form is rejected."""
    record = synthetic_plan().to_record()
    pretty = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode()
    with pytest.raises(DiagnosticPlanError, match="non-canonical"):
        plan_from_bytes(pretty)


def test_relation_rejects_malformed_identifier() -> None:
    """A malformed relation clock identifier is rejected."""
    with pytest.raises(DiagnosticPlanError, match=r"relation\.child_identifier"):
        ClockRelation(
            child_identifier="Clock!",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=False,
        )


def test_plan_without_facility_clock_needs_no_relation() -> None:
    """Without a facility clock, epoch clocks need no declared bound."""
    plan = synthetic_plan()
    facility_ids = {
        clock.identifier
        for clock in plan.clocks
        if clock.kind is ClockKind.FACILITY_MONOTONIC
    }
    clocks = tuple(
        clock for clock in plan.clocks if clock.identifier not in facility_ids
    )
    channels = tuple(
        channel
        for channel in plan.channels
        if channel.clock_identifier not in facility_ids
    )
    kept = {channel.candidate_id for channel in channels}
    deferrals = tuple(
        DeferredCandidate(
            candidate_id=candidate.candidate_id,
            reason="no facility clock in this variant",
        )
        for candidate in APPLICABLE_CANDIDATES
        if candidate.candidate_id not in kept
    )
    variant = DiagnosticPlan(
        identifier=plan.identifier,
        binding=plan.binding,
        clocks=clocks,
        frames=plan.frames,
        clock_relations=(),
        channels=channels,
        deferrals=deferrals,
    )
    assert variant.clock_relations == ()


def test_parser_rejects_non_integer_element_count() -> None:
    """A non-integer element count is rejected by the parser."""
    record = synthetic_plan().to_record()
    record["channels"][0]["element_count"] = "many"
    with pytest.raises(DiagnosticPlanError, match="must be an integer"):
        plan_from_record(record)


def test_relation_rejects_mapped_state() -> None:
    """Any mapping state other than unmapped is rejected."""
    with pytest.raises(DiagnosticPlanError, match="mapping_state"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="mapped",
            evidence_claimed=False,
        )


def test_relation_rejects_claimed_evidence() -> None:
    """A relation may never claim correlation evidence."""
    with pytest.raises(DiagnosticPlanError, match="evidence_claimed"):
        ClockRelation(
            child_identifier="clk_shot",
            parent_identifier="clk_facility",
            max_offset_s=1.0e-6,
            uncertainty_s=1.0e-7,
            method="x",
            mapping_state="unmapped",
            evidence_claimed=True,
        )


def test_plan_rejects_duplicate_relations() -> None:
    """Duplicate clock relations are rejected."""
    plan = synthetic_plan()
    with pytest.raises(DiagnosticPlanError, match=r"plan\.clock_relations"):
        DiagnosticPlan(
            identifier=plan.identifier,
            binding=plan.binding,
            clocks=plan.clocks,
            frames=plan.frames,
            clock_relations=(*plan.clock_relations, plan.clock_relations[0]),
            channels=plan.channels,
            deferrals=plan.deferrals,
        )


def test_parser_rejects_pre_deepening_record_shape() -> None:
    """A record without the deepened sections is refused, fail closed."""
    record = synthetic_plan().to_record()
    del record["frames"]
    del record["clock_relations"]
    with pytest.raises(DiagnosticPlanError, match="must be an array"):
        plan_from_record(record)
