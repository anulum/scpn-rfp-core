# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — numerics wrapper tests

"""The library Bessel kernels are the only special-function path; refusals re-raised."""

from __future__ import annotations

import pytest
from scpn_reactor_kernels import numerics as library

from scpn_rfp_core.errors import DeviceConfigurationError, NumericsError
from scpn_rfp_core.physics import (
    BESSEL_DOMAIN,
    BESSEL_J0_FIRST_ZERO,
    BESSEL_J1_FIRST_ZERO,
    bessel_j0,
    bessel_j1,
)


def test_wrappers_return_the_library_values_bit_for_bit() -> None:
    """Every wrapper is the library kernel; the zeros are the library's constants."""
    assert bessel_j0(2.0) == library.bessel_j0(2.0)
    assert bessel_j1(2.0) == library.bessel_j1(2.0)
    assert bessel_j0(0.0) == 1.0
    assert bessel_j1(0.0) == 0.0
    assert BESSEL_J0_FIRST_ZERO == library.BESSEL_J0_FIRST_ZERO
    assert BESSEL_J1_FIRST_ZERO == library.BESSEL_J1_FIRST_ZERO
    assert BESSEL_DOMAIN == library.BESSEL_DOMAIN
    assert abs(bessel_j0(BESSEL_J0_FIRST_ZERO)) <= 1.0e-14
    assert abs(bessel_j1(BESSEL_J1_FIRST_ZERO)) <= 1.0e-14


@pytest.mark.parametrize(
    ("call", "fragment"),
    [
        (lambda: bessel_j0(9.0), "x"),
        (lambda: bessel_j1(-8.5), "x"),
        (lambda: bessel_j0(float("nan")), "finite"),
    ],
)
def test_refusals_are_re_raised_under_the_device_error(
    call: object, fragment: str
) -> None:
    """A library refusal becomes a NumericsError that is a configuration error."""
    assert callable(call)
    with pytest.raises(NumericsError, match=fragment) as info:
        call()
    assert isinstance(info.value, DeviceConfigurationError)
    assert info.value.__cause__ is not None
