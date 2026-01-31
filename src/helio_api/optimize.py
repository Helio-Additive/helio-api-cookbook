"""
Optimization functions for the Helio Additive API.

Provides unit conversions, optimization settings building, optimization
creation, polling, and a convenience ``run_optimization()`` that combines
all steps.
"""

from __future__ import annotations

import time

from helio_api.client import (
    MAX_CONSECUTIVE_HTTP_FAILURES,
    SIM_OPT_POLL_INTERVAL_S,
    HelioClient,
    generate_timestamped_name,
    print_progress_bar,
)
from helio_api.queries import MUTATION_CREATE_OPTIMIZATION, QUERY_POLL_OPTIMIZATION


def convert_speed_mm_to_m(mm_per_s: float) -> float:
    """Convert mm/s to m/s."""
    return round(mm_per_s / 1000.0, 9)


def convert_volumetric_mm3_to_m3(mm3_per_s: float) -> float:
    """Convert mm^3/s to m^3/s."""
    return round(mm3_per_s / 1e9, 20)


def build_optimization_settings(
    print_priority: str | None = None,
    optimize_outerwall: bool | None = None,
    min_velocity_mm: float | None = None,
    max_velocity_mm: float | None = None,
    min_volumetric_mm3: float | None = None,
    max_volumetric_mm3: float | None = None,
    from_layer: int | None = None,
    to_layer: int | None = None,
) -> dict:
    """Build the optimizationSettings dict for the CreateOptimization mutation.

    Velocity inputs are in mm/s, volumetric in mm^3/s (converted to SI internally).
    The optimizer is always set to HYBRID with LINEAR residual strategy.

    Args:
        print_priority: Print priority value (e.g. "QUALITY", "SPEED").
        optimize_outerwall: Legacy outer wall flag (used if print_priority is None).
        min_velocity_mm: Minimum velocity in mm/s.
        max_velocity_mm: Maximum velocity in mm/s.
        min_volumetric_mm3: Minimum volumetric flow rate in mm^3/s.
        max_volumetric_mm3: Maximum volumetric flow rate in mm^3/s.
        from_layer: Starting layer (clamped to min 2 per BambuStudio).
        to_layer: Ending layer (-1 = last layer).

    Returns:
        Dict suitable for the ``optimizationSettings`` API field.
    """
    settings: dict = {}

    # Print priority (new method) vs optimizeOuterwall (old method)
    if print_priority:
        settings["printPriority"] = print_priority
    elif optimize_outerwall is not None:
        settings["optimizeOuterwall"] = optimize_outerwall

    if min_velocity_mm is not None and min_velocity_mm > 0:
        settings["minVelocity"] = convert_speed_mm_to_m(min_velocity_mm)
    if max_velocity_mm is not None and max_velocity_mm > 0:
        settings["maxVelocity"] = convert_speed_mm_to_m(max_velocity_mm)
    if min_volumetric_mm3 is not None and min_volumetric_mm3 > 0:
        settings["minExtruderFlowRate"] = convert_volumetric_mm3_to_m3(min_volumetric_mm3)
    if max_volumetric_mm3 is not None and max_volumetric_mm3 > 0:
        settings["maxExtruderFlowRate"] = convert_volumetric_mm3_to_m3(max_volumetric_mm3)

    # Residual strategy and optimizer (HYBRID is always used -- this is
    # intentional and should not be changed to another optimizer type).
    settings["residualStrategySettings"] = {"strategy": "LINEAR"}
    settings["optimizer"] = "HYBRID"

    # Layer range
    if from_layer is not None and to_layer is not None:
        # Clamp fromLayer minimum to 2 (per BambuStudio behavior)
        actual_from = max(from_layer, 2)
        settings["layersToOptimize"] = [{"fromLayer": actual_from, "toLayer": to_layer}]

    return settings


def create_optimization(
    client: HelioClient,
    gcode_id: str,
    sim_settings: dict | None = None,
    opt_settings: dict | None = None,
) -> str:
    """Create an optimization via the API.

    Args:
        client: Helio API client.
        gcode_id: Registered G-code ID.
        sim_settings: Optional simulation settings dict.
        opt_settings: Optional optimization settings dict.

    Returns:
        The optimization ID.

    Raises:
        RuntimeError: On API error.
    """
    name = generate_timestamped_name()

    input_data: dict = {
        "name": name,
        "gcodeId": gcode_id,
        "simulationSettings": sim_settings or {},
        "optimizationSettings": opt_settings or {},
    }

    data, errors, trace_id = client.query(MUTATION_CREATE_OPTIMIZATION, {"input": input_data})
    if errors:
        raise RuntimeError(f"CreateOptimization error: {'; '.join(errors)} (trace: {trace_id})")

    opt = data["createOptimization"]
    opt_id = opt["id"]
    print(f"  Optimization created: id={opt_id}, name={opt['name']}")
    return opt_id


def poll_optimization(client: HelioClient, optimization_id: str) -> dict:
    """Poll optimization progress until finished.

    Args:
        client: Helio API client.
        optimization_id: The optimization ID to poll.

    Returns:
        Full optimization result dict.

    Raises:
        RuntimeError: On server failure or too many consecutive poll errors.
    """
    consecutive_failures = 0

    while True:
        data, errors, trace_id = client.query(
            QUERY_POLL_OPTIMIZATION, {"id": optimization_id}
        )
        if errors:
            consecutive_failures += 1
            print(
                f"\n  Poll error ({consecutive_failures}/{MAX_CONSECUTIVE_HTTP_FAILURES}): "
                f"{errors}"
            )
            if consecutive_failures >= MAX_CONSECUTIVE_HTTP_FAILURES:
                raise RuntimeError("Too many consecutive poll failures.")
            time.sleep(SIM_OPT_POLL_INTERVAL_S)
            continue

        consecutive_failures = 0
        opt = data["optimization"]
        status = opt.get("status", "")
        progress = opt.get("progress", 0)

        print_progress_bar(progress)

        if status == "FAILED":
            print()
            raise RuntimeError("Optimization failed on the server.")

        if status == "FINISHED":
            print()
            return opt

        time.sleep(SIM_OPT_POLL_INTERVAL_S)


def run_optimization(
    client: HelioClient,
    gcode_id: str,
    sim_settings: dict | None = None,
    opt_settings: dict | None = None,
) -> tuple[str, dict, str | None]:
    """Create and poll an optimization, then display results.

    Args:
        client: Helio API client.
        gcode_id: Registered G-code ID.
        sim_settings: Optional simulation settings dict.
        opt_settings: Optional optimization settings dict.

    Returns:
        ``(opt_id, result_dict, optimized_url)`` tuple.
    """
    opt_id = create_optimization(client, gcode_id, sim_settings, opt_settings)

    print("  Polling optimization progress...")
    result = poll_optimization(client, opt_id)

    # Display results
    print("\n  === Optimization Results ===")
    print(f"  ID: {result.get('id')}")
    print(f"  Name: {result.get('name')}")
    print(f"  Quality Mean Improvement: {result.get('qualityMeanImprovement', 'N/A')}")
    print(f"  Quality Std Improvement: {result.get('qualityStdImprovement', 'N/A')}")

    optimized_url = result.get("optimizedGcodeWithThermalIndexesUrl")
    return opt_id, result, optimized_url
