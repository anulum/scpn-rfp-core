# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — device capability package

"""Device capability models of the SCPN reversed-field-pinch family.

Public surface of the ``device_configuration_model``,
``diagnostic_clock_semantics`` and ``level0_device_physics`` capabilities
at ``computational_prototype`` maturity: validated parameter objects,
synthetic diagnostic and clock declarations aligned with the pinned SPO
observability catalogue, documented consistency estimates, the
Bessel-function relaxed state and its profile evaluated on the validated
configuration through the pinned shared Bessel kernels, canonical
serialisation with SHA-256 digests, and data-only pins to the SPO
registries. No claim about any real machine or diagnostic is made
anywhere in this package.
"""

from __future__ import annotations

from typing import Final

from scpn_rfp_core.configuration import (
    OWNED_CONFIGURATIONS,
    TAYLOR_RELAXATION_MIN_THETA,
    THETA_MISMATCH_TOLERANCE,
    ConsistencyFinding,
    DeviceConfiguration,
    RegistryBinding,
    configuration_from_bytes,
    configuration_from_record,
)
from scpn_rfp_core.errors import (
    DeviceConfigurationError,
    DiagnosticPlanError,
    NumericsError,
)
from scpn_rfp_core.observability import (
    APPLICABLE_CANDIDATES,
    CATALOGUE_BINDING,
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
from scpn_rfp_core.parameters import (
    PINCH_PARAMETER_BOUNDS,
    REVERSAL_PARAMETER_BOUNDS,
    FieldProgramme,
    OperationalLimits,
    PinchGeometry,
)
from scpn_rfp_core.physics import (
    BFM_MAX_PINCH_PARAMETER,
    BFM_REVERSAL_PINCH_PARAMETER,
    LEVEL0_NON_CLAIMS,
    LEVEL0_RADIAL_STATIONS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    RadialStation,
    RelaxedState,
    bfm_reversal_parameter,
    level0_physics,
    radial_profile,
    relaxed_state,
    reversal_radius,
)
from scpn_rfp_core.plan_envelope import (
    PlanEnvelope,
    envelope_for_plan,
    envelope_from_bytes,
    envelope_from_record,
    verify_envelope,
)

__version__: Final = "0.1.0.dev0"

__all__ = [
    "APPLICABLE_CANDIDATES",
    "BFM_MAX_PINCH_PARAMETER",
    "BFM_REVERSAL_PINCH_PARAMETER",
    "CATALOGUE_BINDING",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_RADIAL_STATIONS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "OWNED_CONFIGURATIONS",
    "PINCH_PARAMETER_BOUNDS",
    "REVERSAL_PARAMETER_BOUNDS",
    "TAYLOR_RELAXATION_MIN_THETA",
    "THETA_MISMATCH_TOLERANCE",
    "CandidateProfile",
    "ClockKind",
    "ClockModel",
    "ClockRelation",
    "ConsistencyFinding",
    "DeferredCandidate",
    "DeviceConfiguration",
    "DeviceConfigurationError",
    "DiagnosticChannelPlan",
    "DiagnosticPlan",
    "DiagnosticPlanError",
    "FieldProgramme",
    "FrameKind",
    "Level0PhysicsRecord",
    "ModelInputs",
    "NumericsError",
    "ObservabilityBinding",
    "ObservabilityClass",
    "OperationalLimits",
    "PinchGeometry",
    "PlanEnvelope",
    "RadialStation",
    "ReferenceFrame",
    "RegistryBinding",
    "RelaxedState",
    "SemanticCarrier",
    "__version__",
    "bfm_reversal_parameter",
    "configuration_from_bytes",
    "configuration_from_record",
    "envelope_for_plan",
    "envelope_from_bytes",
    "envelope_from_record",
    "level0_physics",
    "plan_from_bytes",
    "plan_from_record",
    "radial_profile",
    "relaxed_state",
    "reversal_radius",
    "verify_envelope",
]
