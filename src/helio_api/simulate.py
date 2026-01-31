"""
Simulation functions for the Helio Additive API.

Provides temperature settings computation, simulation creation, polling,
and a convenience ``run_simulation()`` that combines all steps.
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
from helio_api.queries import MUTATION_CREATE_SIMULATION, QUERY_POLL_SIMULATION


def compute_simulation_settings(
    chamber_temp: float | None = None, bed_temp: float | None = None
) -> dict:
    """Compute temperature simulation settings.

    Args:
        chamber_temp: Chamber temperature in Celsius (optional).
        bed_temp: Bed temperature in Celsius (optional).

    Returns:
        Dict with simulationSettings fields for the API.
    """
    settings: dict = {}

    # Default layer threshold: 20mm -> 0.020m
    settings["temperatureStabilizationHeight"] = 0.020

    if chamber_temp is not None and chamber_temp > 0:
        if bed_temp is not None and bed_temp > 0:
            initial_room_airtemp = (chamber_temp + bed_temp) / 2.0
            settings["airTemperatureAboveBuildPlate"] = initial_room_airtemp + 273.15

        settings["stabilizedAirTemperature"] = chamber_temp + 273.15

    return settings


def create_simulation(
    client: HelioClient, gcode_id: str, sim_settings: dict | None = None
) -> str:
    """Create a simulation via the API.

    Args:
        client: Helio API client.
        gcode_id: Registered G-code ID.
        sim_settings: Optional simulation settings dict.

    Returns:
        The simulation ID.

    Raises:
        RuntimeError: On API error.
    """
    name = generate_timestamped_name()

    input_data: dict = {
        "name": name,
        "gcodeId": gcode_id,
        "simulationSettings": sim_settings or {},
    }

    data, errors, trace_id = client.query(MUTATION_CREATE_SIMULATION, {"input": input_data})
    if errors:
        raise RuntimeError(f"CreateSimulation error: {'; '.join(errors)} (trace: {trace_id})")

    sim = data["createSimulation"]
    sim_id = sim["id"]
    print(f"  Simulation created: id={sim_id}, name={sim['name']}")
    return sim_id


def poll_simulation(client: HelioClient, simulation_id: str) -> dict:
    """Poll simulation progress until finished.

    Args:
        client: Helio API client.
        simulation_id: The simulation ID to poll.

    Returns:
        Full simulation result dict.

    Raises:
        RuntimeError: On server failure or too many consecutive poll errors.
    """
    consecutive_failures = 0

    while True:
        data, errors, trace_id = client.query(QUERY_POLL_SIMULATION, {"id": simulation_id})
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
        sim = data["simulation"]
        status = sim.get("status", "")
        progress = sim.get("progress", 0)

        print_progress_bar(progress)

        if status == "FAILED":
            print()
            raise RuntimeError("Simulation failed on the server.")

        if status == "FINISHED":
            print()
            return sim

        time.sleep(SIM_OPT_POLL_INTERVAL_S)


def run_simulation(
    client: HelioClient,
    gcode_id: str,
    chamber_temp: float | None = None,
    bed_temp: float | None = None,
) -> tuple[str, dict, str | None]:
    """Create and poll a simulation, then display results.

    Args:
        client: Helio API client.
        gcode_id: Registered G-code ID.
        chamber_temp: Optional chamber temperature in Celsius.
        bed_temp: Optional bed temperature in Celsius.

    Returns:
        ``(sim_id, result_dict, thermal_url)`` tuple.
    """
    sim_settings = compute_simulation_settings(chamber_temp, bed_temp)
    sim_id = create_simulation(client, gcode_id, sim_settings)

    print("  Polling simulation progress...")
    result = poll_simulation(client, sim_id)

    # Display results
    print("\n  === Simulation Results ===")
    print(f"  ID: {result.get('id')}")
    print(f"  Name: {result.get('name')}")

    print_info = result.get("printInfo")
    if print_info:
        print(f"  Print Outcome: {print_info.get('printOutcome', 'N/A')}")
        desc = print_info.get("printOutcomeDescription")
        if desc:
            print(f"    {desc}")
        print(f"  Temperature Direction: {print_info.get('temperatureDirection', 'N/A')}")
        temp_desc = print_info.get("temperatureDirectionDescription")
        if temp_desc:
            print(f"    {temp_desc}")
        caveats = print_info.get("caveats", [])
        if caveats:
            print("  Caveats:")
            for c in caveats:
                print(f"    - [{c.get('caveatType', '')}] {c.get('description', '')}")

    speed_factor = result.get("speedFactor")
    if speed_factor is not None:
        print(f"  Speed Factor: {speed_factor}")

    fixes = result.get("suggestedFixes", [])
    if fixes:
        print("  Suggested Fixes:")
        for fix in fixes:
            cat = fix.get("category", "")
            fix_text = fix.get("fix", "")
            print(f"    [{cat}] {fix_text}")
            for detail in fix.get("extraDetails", []):
                print(f"      - {detail}")

    thermal_url = result.get("thermalIndexGcodeUrl")
    return sim_id, result, thermal_url
