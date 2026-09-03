# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — repository header artwork generator

"""Generate the three README header images (1280x640) for this repository.

Every image is original generated artwork derived from this repository's
own domain surface — the reversed-field-pinch F/Θ field programme, the
Taylor-relaxation threshold it validates, and the edge field reversal
that defines the owned registry identifier. The right-hand text panel
states only facts backed by the repository itself.

Outputs (written next to this script):

- ``repo_header.png`` — circular pinch section with the toroidal field
  out of plane in the core and reversed into the plane at the edge
  (used by ``README.md``).
- ``repo_header_field_profiles.png`` — relaxed-state B_phi/B_theta
  radial profiles with the reversal surface marked.
- ``repo_header_f_theta.png`` — the F-Theta programme curve with the
  Taylor threshold and the F = 0 edge-reversal crossing.

Generation-time tooling only: requires ``numpy`` and ``matplotlib``,
which are deliberately not part of the pinned development lock. Run as
``python3 docs/assets/generate_header.py`` from the repository root.
The output is deterministic (fixed geometry, no random input).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing aid only
    from numpy.typing import NDArray

OUT_DIR = Path(__file__).resolve().parent

BG = "#00050a"
CYAN = "#00ccff"
MAGENTA = "#ff00ff"
STEEL = "#334466"
PROBE = "#66aaff"
RED = "#ff3366"

WIDTH_IN, HEIGHT_IN, DPI = 12.8, 6.4, 100

TITLE_METRICS: list[tuple[str, str]] = [
    ("Device Configuration", "reversed_field_pinch · relaxed torus"),
    ("Field Programme", "F/Θ · Θ cross-checked vs μ0·Ip/2πa"),
    ("Taylor Relaxation", "Θ below ~1.2 flagged (PRL 33, 1974)"),
    ("Diagnostics & Clocks", "fail-closed vs pinned SPO catalogue"),
    ("Plan Envelope", "v1.1.0 · synthetic · review-only"),
    ("Quality Gates", "100% branch cov · mypy --strict"),
]


def _pyplot() -> Any:
    """Return pyplot configured for headless Agg rendering."""
    import matplotlib as mpl

    mpl.use("Agg")
    import matplotlib.pyplot as plt

    return plt


def _glow_cmap() -> Any:
    """Build the family glow colormap (deep navy to cyan)."""
    from matplotlib.colors import LinearSegmentedColormap

    return LinearSegmentedColormap.from_list(
        "scpn_glow",
        ["#00050a", "#001428", "#002d55", "#005588", "#0088bb", "#00ccff"],
    )


def bessel_j0_j1(
    argument: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Return series approximations of J0 and J1 on a bounded argument."""
    j0 = np.ones_like(argument)
    term = np.ones_like(argument)
    for order in range(1, 14):
        term = term * (-((argument / 2.0) ** 2)) / (order * order)
        j0 = j0 + term
    half = argument / 2.0
    term = half.copy()
    j1 = term.copy()
    for order in range(1, 14):
        term = term * (-(half**2)) / (order * (order + 1))
        j1 = j1 + term
    return j0, j1


def _text_panel(fig: Any, subtitle: str) -> None:
    """Draw the family right-hand text panel onto ``fig``."""
    ax = fig.add_axes([0.62, 0.0, 0.38, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.08,
        0.84,
        "SCPN",
        color="white",
        fontsize=36,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.74,
        "RFP CORE",
        color="white",
        fontsize=34,
        fontweight="bold",
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        0.08,
        0.66,
        subtitle,
        color=CYAN,
        fontsize=11,
        fontfamily="monospace",
        alpha=0.85,
    )
    ax.plot([0.08, 0.85], [0.615, 0.615], color=STEEL, lw=0.8, alpha=0.5)
    y = 0.55
    for label, value in TITLE_METRICS:
        ax.text(
            0.08,
            y,
            f"▸ {label}",
            color="#6688aa",
            fontsize=9,
            fontfamily="monospace",
            alpha=0.9,
        )
        ax.text(
            0.10,
            y - 0.030,
            value,
            color="#99bbdd",
            fontsize=8,
            fontfamily="monospace",
            alpha=0.7,
        )
        y -= 0.072
    ax.text(
        0.08,
        0.06,
        "© 1996–2026 Miroslav Šotek",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.6,
    )
    ax.text(
        0.08,
        0.03,
        "anulum.li | AGPL-3.0",
        color="#445566",
        fontsize=7,
        fontfamily="monospace",
        alpha=0.5,
    )


def _art_axes(fig: Any) -> Any:
    """Return the borderless left-hand art axes of ``fig``."""
    ax = fig.add_axes([0.0, 0.0, 0.68, 1.0], facecolor=BG)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    return ax


def _save(fig: Any, plt: Any, name: str) -> None:
    """Save ``fig`` to ``name`` inside the assets directory and close it."""
    target = OUT_DIR / name
    fig.savefig(target, dpi=DPI, facecolor=BG, bbox_inches="tight", pad_inches=0)
    plt.close(fig)
    print(f"generated {target}")


def generate_reversal_section() -> None:
    """Generate ``repo_header.png``: the spatial field-reversal section."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(-2.6, 2.6)
    ax.set_ylim(-1.3, 1.3)
    ax.set_aspect("equal")

    grid_x = np.linspace(-1.3, 1.3, 200)
    grid_z = np.linspace(-1.25, 1.25, 200)
    mesh_x, mesh_z = np.meshgrid(grid_x, grid_z)
    rho = np.sqrt(mesh_x**2 + mesh_z**2)
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 2.6),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.85,
    )

    theta = np.linspace(0.0, 2.0 * np.pi, 300)
    surfaces = [(1.0, 2.2, 0.95), (0.78, 0.7, 0.4), (0.56, 0.7, 0.4), (0.34, 0.7, 0.4)]
    for radius, lw, alpha in surfaces:
        ax.plot(
            radius * np.cos(theta),
            radius * np.sin(theta),
            color=CYAN,
            lw=lw,
            alpha=alpha,
        )

    for radius in (0.0, 0.22, 0.45):
        count = 1 if radius == 0.0 else 6
        for index in range(count):
            angle = 2.0 * np.pi * index / max(count, 1)
            ax.plot(
                radius * np.cos(angle),
                radius * np.sin(angle),
                "o",
                color="white",
                ms=4,
                alpha=0.85,
                mfc="white",
            )
    for index in range(10):
        angle = 2.0 * np.pi * index / 10
        ax.plot(
            0.9 * np.cos(angle),
            0.9 * np.sin(angle),
            "x",
            color=RED,
            ms=7,
            mew=1.6,
            alpha=0.9,
        )
    for index in range(12):
        angle = 2.0 * np.pi * index / 12
        base_x, base_z = 1.12 * np.cos(angle), 1.12 * np.sin(angle)
        delta_x, delta_z = -np.sin(angle) * 0.14, np.cos(angle) * 0.14
        ax.annotate(
            "",
            xy=(base_x + delta_x, base_z + delta_z),
            xytext=(base_x - delta_x, base_z - delta_z),
            arrowprops={"arrowstyle": "->", "color": PROBE, "lw": 1.2, "alpha": 0.8},
        )

    ax.text(
        0,
        -1.22,
        "B_φ out of plane (core) · reversed into plane (edge) · B_θ around",
        color="#445566",
        fontsize=7.5,
        fontfamily="monospace",
        ha="center",
    )
    ax.text(
        1.38,
        0.95,
        "⊙ core",
        color="white",
        fontsize=9,
        fontfamily="monospace",
        alpha=0.8,
    )
    ax.text(
        1.38,
        0.72,
        "⊗ edge",
        color=RED,
        fontsize=9,
        fontfamily="monospace",
        alpha=0.9,
    )
    _text_panel(fig, "Relaxed-Current Torus, One Identifier")
    _save(fig, plt, "repo_header.png")


def generate_field_profiles() -> None:
    """Generate ``repo_header_field_profiles.png``: B_phi/B_theta(r)."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.0, 3.4)

    glow_x = np.linspace(0.4, 9.6, 240)
    glow_z = np.linspace(-2.9, 3.3, 140)
    mesh_x, mesh_z = np.meshgrid(glow_x, glow_z)
    rho = np.abs(mesh_z - 0.2) / 2.4
    ax.contourf(
        mesh_x,
        mesh_z,
        np.exp(-rho * 2.0) * (0.35 + 0.65 * np.exp(-(((mesh_x - 5.0) / 4.2) ** 2))),
        levels=30,
        cmap=_glow_cmap(),
        alpha=0.5,
    )

    minor_radius = np.linspace(0.0, 1.0, 400)
    j0, j1 = bessel_j0_j1(2.9 * minor_radius)
    xs = 0.7 + 8.6 * minor_radius

    ax.plot([0.7, 9.3], [0.2, 0.2], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([0.7, 0.7], [-2.4, 3.1], color=STEEL, lw=1.0, alpha=0.7)

    ax.plot(xs, 0.2 + 2.4 * j1, color=PROBE, lw=2.0, alpha=0.9)
    ax.text(6.6, 2.05, "B_θ(r)", color=PROBE, fontsize=10, fontfamily="monospace")

    ax.plot(xs, 0.2 + 2.6 * j0, color=CYAN, lw=2.4, alpha=0.95)
    ax.text(1.25, 2.95, "B_φ(r)", color=CYAN, fontsize=10, fontfamily="monospace")

    reversal_radius = 2.405 / 2.9
    x_rev = 0.7 + 8.6 * reversal_radius
    ax.plot([x_rev, x_rev], [-2.1, 2.8], color=RED, lw=1.4, alpha=0.8, ls=(0, (5, 3)))
    ax.text(
        x_rev - 0.12,
        -1.7,
        "reversal surface",
        ha="right",
        color=RED,
        fontsize=8.5,
        fontfamily="monospace",
        alpha=0.9,
    )
    ax.annotate(
        "",
        xy=(8.85, -0.75),
        xytext=(x_rev + 0.25, -0.75),
        arrowprops={"arrowstyle": "->", "color": RED, "lw": 1.2, "alpha": 0.7},
    )
    ax.text(
        7.85,
        -1.12,
        "B_φ < 0",
        color=RED,
        fontsize=8.5,
        fontfamily="monospace",
        ha="center",
        alpha=0.9,
    )

    ax.text(
        9.0,
        -0.12,
        "r/a",
        color="#445566",
        fontsize=8.5,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(
        5.0,
        -2.72,
        "relaxed-state field programme · declared, then cross-checked",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "The Field That Reverses At The Edge")
    _save(fig, plt, "repo_header_field_profiles.png")


def generate_f_theta() -> None:
    """Generate ``repo_header_f_theta.png``: the F-Theta programme."""
    plt = _pyplot()
    fig = plt.figure(figsize=(WIDTH_IN, HEIGHT_IN), dpi=DPI, facecolor=BG)
    ax = _art_axes(fig)
    ax.set_xlim(0, 10)
    ax.set_ylim(-3.2, 3.2)

    ax.plot([0.9, 9.4], [0.6, 0.6], color=STEEL, lw=1.0, alpha=0.7)
    ax.plot([0.9, 0.9], [-2.6, 2.9], color=STEEL, lw=1.0, alpha=0.7)
    ax.text(
        9.35,
        0.28,
        "Θ",
        color="#8899bb",
        fontsize=11,
        fontfamily="monospace",
        ha="right",
    )
    ax.text(1.05, 2.75, "F", color="#8899bb", fontsize=11, fontfamily="monospace")

    pinch = np.linspace(0.05, 1.70, 500)
    j0, j1 = bessel_j0_j1(2.0 * pinch)
    with np.errstate(divide="ignore", invalid="ignore"):
        f_curve = np.where(np.abs(j1) > 1e-9, pinch * j0 / j1, np.nan)
    f_curve = np.clip(f_curve, -4.0, 3.0)
    xs = 0.9 + (8.3 / 2.2) * pinch
    ys = np.clip(0.6 + 0.85 * f_curve, -2.5, 2.85)
    ax.plot(xs, ys, color=CYAN, lw=2.4, alpha=0.95)
    ax.fill_between(xs, ys, 0.6, where=np.isfinite(ys), color=CYAN, alpha=0.06)

    x_threshold = 0.9 + (8.3 / 2.2) * 1.2
    ax.plot(
        [x_threshold, x_threshold],
        [-2.5, 2.85],
        color=MAGENTA,
        lw=1.4,
        alpha=0.85,
        ls=(0, (5, 3)),
    )
    ax.text(
        x_threshold + 0.12,
        2.45,
        "Θ ≈ 1.2 · Taylor relaxation",
        color=MAGENTA,
        fontsize=8.5,
        fontfamily="monospace",
        alpha=0.95,
    )
    ax.text(
        x_threshold + 0.12,
        2.12,
        "below: declared reversal flagged",
        color="#bb77cc",
        fontsize=8,
        fontfamily="monospace",
        alpha=0.85,
    )

    beyond = xs > x_threshold
    crossing = np.nanargmin(np.abs(ys[beyond] - 0.6))
    ax.plot(xs[beyond][crossing], 0.6, "o", color=RED, ms=6, alpha=0.95)
    ax.text(
        xs[beyond][crossing] + 0.15,
        0.82,
        "F = 0 · edge reversal",
        color=RED,
        fontsize=8.5,
        fontfamily="monospace",
        alpha=0.95,
    )

    ax.text(
        5.0,
        -2.95,
        "F–Θ programme · Taylor, Phys. Rev. Lett. 33 (1974) 1139",
        color="#445566",
        fontsize=8,
        fontfamily="monospace",
        ha="center",
    )
    _text_panel(fig, "F–Θ Programme, Validated Threshold")
    _save(fig, plt, "repo_header_f_theta.png")


if __name__ == "__main__":
    generate_reversal_section()
    generate_field_profiles()
    generate_f_theta()
