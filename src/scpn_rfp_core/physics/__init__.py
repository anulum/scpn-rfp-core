# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — level-0 device physics

"""Level-0 device physics of the reversed-field-pinch family.

The cylindrical force-free relaxed state in its Bessel-function form
(R. Paccagnella, arXiv:1509.07307v2 (2015), eqs. 4-5, after J. B. Taylor)
evaluated on the validated device configuration: the force-free parameter
and on-axis field, the model's reversal parameter ``F_bfm(Theta)`` against
the declared ``F``, the reversal threshold and radius, the edge-field
comparison with the declared current, and the field and safety-factor
profile at declared radial stations. Every function is a closed-form
evaluation on the shared Bessel kernels; no equation is solved and no
value describes a real machine. Design records: ADR 0005, ADR 0006.
"""

from __future__ import annotations

from scpn_rfp_core.physics.level0 import (
    LEVEL0_NON_CLAIMS,
    LEVEL0_RADIAL_STATIONS,
    LEVEL0_SCHEMA,
    LEVEL0_SCHEMA_VERSION,
    Level0PhysicsRecord,
    ModelInputs,
    level0_physics,
)
from scpn_rfp_core.physics.numerics import (
    BESSEL_DOMAIN,
    BESSEL_J0_FIRST_ZERO,
    BESSEL_J1_FIRST_ZERO,
    bessel_j0,
    bessel_j1,
)
from scpn_rfp_core.physics.profiles import (
    RadialStation,
    axis_safety_factor,
    radial_profile,
    radial_station,
    require_station,
)
from scpn_rfp_core.physics.relaxation import (
    BFM_MAX_PINCH_PARAMETER,
    BFM_REVERSAL_PINCH_PARAMETER,
    RelaxedState,
    axis_field,
    bfm_reversal_parameter,
    force_free_parameter,
    relaxed_state,
    require_bfm_pinch_parameter,
    reversal_radius,
)

__all__ = [
    "BESSEL_DOMAIN",
    "BESSEL_J0_FIRST_ZERO",
    "BESSEL_J1_FIRST_ZERO",
    "BFM_MAX_PINCH_PARAMETER",
    "BFM_REVERSAL_PINCH_PARAMETER",
    "LEVEL0_NON_CLAIMS",
    "LEVEL0_RADIAL_STATIONS",
    "LEVEL0_SCHEMA",
    "LEVEL0_SCHEMA_VERSION",
    "Level0PhysicsRecord",
    "ModelInputs",
    "RadialStation",
    "RelaxedState",
    "axis_field",
    "axis_safety_factor",
    "bessel_j0",
    "bessel_j1",
    "bfm_reversal_parameter",
    "force_free_parameter",
    "level0_physics",
    "radial_profile",
    "radial_station",
    "relaxed_state",
    "require_bfm_pinch_parameter",
    "require_station",
    "reversal_radius",
]
