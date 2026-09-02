# SPDX-License-Identifier: AGPL-3.0-or-later
# Commercial license available
# © Concepts 1996–2026 Miroslav Šotek. All rights reserved.
# © Code 2020–2026 Miroslav Šotek. All rights reserved.
# ORCID: 0009-0009-3560-0851
# Contact: www.anulum.li | protoscience@anulum.li
# SCPN RFP Core — level-0 physics benchmark

"""Benchmark the level-0 physics kernels: Python floor versus native.

Follows the ecosystem benchmark standard: warm-up, repeated samples,
percentiles, one row per (operation, backend), unavailable backends marked
explicitly, full provenance in the artefact. The operation is the
Bessel-function relaxed state (force-free parameter, axis field, model
reversal parameter, reversal radius, edge-field comparison) and the
profile at five radial stations over a grid of synthetic parameter
points; each sample times one full grid pass. Both backends evaluate the
Bessel functions through the pinned shared kernel library. Nothing
measured here is a physics claim.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scpn_rfp_core.physics import (  # noqa: E402
    LEVEL0_RADIAL_STATIONS,
    axis_field,
    bfm_reversal_parameter,
    force_free_parameter,
    radial_station,
    reversal_radius,
)
from scpn_rfp_core.physics.numerics import bessel_j1  # noqa: E402

SCHEMA: Final = "scpn-rfp-core.level0-physics-benchmark.v1"
Point = tuple[float, float, float, float, float]


def grid(points: int) -> list[Point]:
    """Build a deterministic synthetic parameter grid.

    Parameters
    ----------
    points
        Number of grid points.

    Returns
    -------
    list of (float, float, float, float, float)
        (pinch parameter, minor radius, major radius, average toroidal
        field, plasma current) tuples inside the model's domain.
    """
    return [
        (
            0.3 + 1.55 * (index % 97) / 96.0,
            0.3 + 0.3 * (index % 89) / 88.0,
            1.5 + 2.0 * (index % 83) / 82.0,
            0.1 + 0.4 * (index % 79) / 78.0,
            0.3 + 1.2 * (index % 73) / 72.0,
        )
        for index in range(points)
    ]


def floor_pass(sample_grid: list[Point]) -> float:
    """Run one grid pass on the Python floor.

    Parameters
    ----------
    sample_grid
        Parameter grid.

    Returns
    -------
    float
        Checksum of the results, so the work cannot be optimised away.
    """
    total = 0.0
    for theta, minor, major, average, current in sample_grid:
        total += force_free_parameter(theta, minor)
        b0 = axis_field(average, theta)
        total += bfm_reversal_parameter(theta)
        radius = reversal_radius(theta, minor)
        total += 0.0 if radius is None else radius
        edge = b0 * bessel_j1(2.0 * theta)
        total += (0.2 * current / minor - edge) / edge
        for fraction in LEVEL0_RADIAL_STATIONS:
            total += radial_station(fraction, minor, major, theta, b0).safety_factor
    return total


def native_pass_factory() -> Callable[[list[Point]], float] | None:
    """Return the native grid pass when the native module is importable.

    Returns
    -------
    callable or None
        The pass function, or None when scpn_rfp_native is absent.
    """
    try:
        native = importlib.import_module("scpn_rfp_native")
    except ImportError:
        return None

    def native_pass(sample_grid: list[Point]) -> float:
        total = 0.0
        for theta, minor, major, average, current in sample_grid:
            state = native.relaxed_state(minor, theta, average, -0.2, current)
            total += state[1] + state[3]
            total += 0.0 if state[7] is None else state[7]
            total += state[10]
            for fraction in LEVEL0_RADIAL_STATIONS:
                total += native.radial_station(fraction, minor, major, theta, state[2])[
                    4
                ]
        return total

    return native_pass


def measure(
    run: Callable[[list[Point]], float],
    sample_grid: list[Point],
    warmup: int,
    repeats: int,
) -> dict[str, float]:
    """Time repeated grid passes and summarise them.

    Parameters
    ----------
    run
        Grid pass to time.
    sample_grid
        Parameter grid.
    warmup
        Discarded leading passes.
    repeats
        Timed passes.

    Returns
    -------
    dict[str, float]
        Percentiles, mean, min, max in microseconds per grid point and the
        throughput in points per second (P50-based).
    """
    for _ in range(warmup):
        run(sample_grid)
    samples: list[float] = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        run(sample_grid)
        samples.append((time.perf_counter_ns() - start) / 1e3 / len(sample_grid))
    ordered = sorted(samples)

    def percentile(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, round(fraction * (len(ordered) - 1)))]

    p50 = percentile(0.5)
    return {
        "p50_us_per_point": p50,
        "p95_us_per_point": percentile(0.95),
        "p99_us_per_point": percentile(0.99),
        "mean_us_per_point": statistics.fmean(samples),
        "min_us_per_point": ordered[0],
        "max_us_per_point": ordered[-1],
        "throughput_points_per_s": 1e6 / p50,
    }


def provenance() -> dict[str, Any]:
    """Collect the environment provenance of a run.

    Returns
    -------
    dict[str, Any]
        Interpreter, platform, CPU model, commit and host-load context.
    """
    cpu_model = "unknown"
    with contextlib.suppress(OSError):
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
    load = "unavailable"
    with contextlib.suppress(OSError):
        load = Path("/proc/loadavg").read_text(encoding="utf-8").split()[0]
    commit = "unknown"
    git = shutil.which("git")
    if git is not None:
        with contextlib.suppress(OSError):
            commit = subprocess.run(
                [git, "rev-parse", "HEAD"],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_model": cpu_model,
        "load_average_1min_at_start": load,
        "commit": commit,
        "isolated_cores": False,
    }


def main(argv: list[str] | None = None) -> int:
    """Run the benchmark command-line interface.

    Parameters
    ----------
    argv
        Argument vector; None reads sys.argv.

    Returns
    -------
    int
        0 on completion.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--points", type=int, default=100_000)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=20)
    parser.add_argument("--label", default="local")
    parser.add_argument("--output", type=Path, default=ROOT / "benchmarks" / "results")
    args = parser.parse_args(argv)
    sample_grid = grid(args.points)
    results: list[dict[str, Any]] = [
        {
            "name": "level0_grid_pass",
            "backend": "python_floor",
            "stats": measure(floor_pass, sample_grid, args.warmup, args.repeats),
            "status": "measured",
        }
    ]
    native_pass = native_pass_factory()
    if native_pass is None:
        results.append(
            {
                "name": "level0_grid_pass",
                "backend": "rust_native",
                "stats": None,
                "status": "unavailable: scpn_rfp_native not installed",
            }
        )
    else:
        stats = measure(native_pass, sample_grid, args.warmup, args.repeats)
        results.append(
            {
                "name": "level0_grid_pass",
                "backend": "rust_native",
                "stats": stats,
                "status": "measured",
                "requires": "optional native build (rust/, maturin)",
            }
        )
        floor_p50 = results[0]["stats"]["p50_us_per_point"]
        results[1]["speedup_p50_vs_python_floor"] = (
            floor_p50 / stats["p50_us_per_point"]
        )
    artefact = {
        "schema": SCHEMA,
        "generated_at": datetime.now(UTC).isoformat(),
        "label": args.label,
        "platform": provenance(),
        "parameters": {
            "points": args.points,
            "warmup": args.warmup,
            "repeats": args.repeats,
        },
        "results": results,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output / f"level0_physics.{args.label}.json"
    target.write_text(
        json.dumps(artefact, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(f"benchmark: wrote {target}")
    for row in results:
        print(f"  {row['backend']}: {row['status']} {row['stats']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
