# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — shared numerics kernels

"""The Bessel kernels of the shared library and their first zeros.

The level-0 models use only ``+ - * /`` plus the deterministic Bessel
functions ``J0`` and ``J1`` of the pinned shared kernel library
(``scpn_reactor_kernels.numerics``, kernel ``numerics_bessel``: the NIST
DLMF 10.2.2 ascending series on ``|x| <= 8``), never a platform special
function, so the Python floor and the native crate (which depends on the
same library's Rust crate) agree bit for bit. The first positive zeros
``j_{0,1}`` and ``j_{1,1}`` are the library's correctly rounded constants
(OEIS A115368, A115369). A domain refusal of the library is re-raised as
:class:`~scpn_rfp_core.errors.NumericsError` with the library's message.
"""

from __future__ import annotations

from scpn_reactor_kernels.errors import NumericsError as LibraryNumericsError
from scpn_reactor_kernels.numerics import (
    BESSEL_DOMAIN,
    BESSEL_J0_FIRST_ZERO,
    BESSEL_J1_FIRST_ZERO,
)
from scpn_reactor_kernels.numerics import bessel_j0 as _bessel_j0
from scpn_reactor_kernels.numerics import bessel_j1 as _bessel_j1

from scpn_rfp_core.errors import NumericsError

__all__ = [
    "BESSEL_DOMAIN",
    "BESSEL_J0_FIRST_ZERO",
    "BESSEL_J1_FIRST_ZERO",
    "bessel_j0",
    "bessel_j1",
]


def bessel_j0(x: float) -> float:
    """Return ``J0(x)`` by the library kernel.

    Parameters
    ----------
    x
        Argument with ``|x| <= 8``.

    Returns
    -------
    float
        The Bessel function of the first kind, order zero.

    Raises
    ------
    NumericsError
        If the library refuses the argument.
    """
    try:
        return _bessel_j0(x)
    except LibraryNumericsError as exc:
        raise NumericsError(str(exc)) from exc


def bessel_j1(x: float) -> float:
    """Return ``J1(x)`` by the library kernel.

    Parameters
    ----------
    x
        Argument with ``|x| <= 8``.

    Returns
    -------
    float
        The Bessel function of the first kind, order one.

    Raises
    ------
    NumericsError
        If the library refuses the argument.
    """
    try:
        return _bessel_j1(x)
    except LibraryNumericsError as exc:
        raise NumericsError(str(exc)) from exc
