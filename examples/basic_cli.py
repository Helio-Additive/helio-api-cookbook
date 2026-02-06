#!/usr/bin/env python3
"""
Basic CLI for the Helio Additive API.

This is the simplified CLI for typical users who want to simulate or optimize
G-code from BambuStudio (or other FDM slicers). It covers the core workflow:
upload G-code, run simulation/optimization, download results.

For advanced features (thermal history, mesh visualization), see:
  - examples/advanced/README.md
  - examples/interactive_cli.py (full menu)

Usage:
    pip install -e .
    python examples/basic_cli.py
"""

import os
import sys

# Allow running directly without pip install by adding src/ to path
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_repo_root, "src", "helio_api")):
    sys.path.insert(0, os.path.join(_repo_root, "src"))

from helio_api import (  # noqa: E402
    HelioClient,
    build_optimization_settings,
    check_user_quota,
    compute_simulation_settings,
    download_file,
    get_default_optimization_settings,
    get_print_priority_options,
    get_recent_runs,
    list_materials,
    list_printers,
    load_pat_token,
    poll_optimization,
    poll_simulation,
    run_optimization,
    run_simulation,
    upload_and_register_gcode,
)

# =============================================================================
# Interactive Helpers
# =============================================================================


def select_printer(client):
    """Interactive printer selection: browse list or enter ID directly."""
    print("\n  How would you like to select a printer?")
    print("    1. Browse the list of supported printers")
    print("    2. Enter a printer ID directly")
    choice = input("  Choice [1/2]: ").strip()

    if choice == "2":
        pid = input("  Enter printer ID: ").strip()
        return pid

    print("  Fetching printers...")
    printers = list_printers(client)
    if not printers:
        print("  No printers found. Enter ID manually.")
        return input("  Enter printer ID: ").strip()

    for i, p in enumerate(printers):
        bbs = f" (BambuStudio: {p['bambustudio_name']})" if p["bambustudio_name"] else ""
        print(f"    {i + 1:3d}. {p['name']}{bbs}  [{p['id']}]")

    idx = input(f"  Select printer [1-{len(printers)}]: ").strip()
    try:
        idx = int(idx) - 1
        return printers[idx]["id"]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return input("  Enter printer ID: ").strip()


def select_material(client):
    """Interactive material selection: browse list or enter ID directly."""
    print("\n  How would you like to select a material?")
    print("    1. Browse the list of supported materials")
    print("    2. Enter a material ID directly")
    choice = input("  Choice [1/2]: ").strip()

    if choice == "2":
        mid = input("  Enter material ID: ").strip()
        return mid

    print("  Fetching materials...")
    materials = list_materials(client)
    if not materials:
        print("  No materials found. Enter ID manually.")
        return input("  Enter material ID: ").strip()

    for i, m in enumerate(materials):
        bbs = f" (BambuStudio: {m['bambustudio_name']})" if m["bambustudio_name"] else ""
        print(f"    {i + 1:3d}. {m['name']}{bbs}  [{m['id']}]")

    idx = input(f"  Select material [1-{len(materials)}]: ").strip()
    try:
        idx = int(idx) - 1
        return materials[idx]["id"]
    except (ValueError, IndexError):
        print("  Invalid selection.")
        return input("  Enter material ID: ").strip()


def input_optional_float(prompt, default=None):
    """Prompt for an optional numeric value."""
    if default is not None:
        suffix = f" [{default}]"
    else:
        suffix = " (Enter to skip)"
    val = input(f"  {prompt}{suffix}: ").strip()
    if not val:
        return default
    try:
        return float(val)
    except ValueError:
        print("  Invalid number, skipping.")
        return default


def format_temp_display(value):
    """Format a temperature value for display."""
    if value is not None:
        return f"{value} C"
    return "auto-calculated by Helio"


# =============================================================================
# Prompt Helpers
# =============================================================================


def _prompt_temperatures():
    """Prompt for optional chamber and bed temperature overrides."""
    print("\n  Temperature overrides (optional):")
    print("  If skipped, Helio will auto-calculate from the G-code.\n")
    chamber_temp = input_optional_float(
        "Chamber temp override in C, auto-calculated if skipped"
    )
    bed_temp = input_optional_float(
        "Bed temp override in C, auto-calculated if skipped"
    )
    return chamber_temp, bed_temp


def _prompt_print_priority(client, material_id):
    """Prompt for print priority selection."""
    print("\n  Fetching print priority options...")
    priority_options = get_print_priority_options(client, material_id)
    print_priority = None
    optimize_outerwall = None

    if priority_options:
        available = [o for o in priority_options if o["isAvailable"]]
        if available:
            print("  Print priority options:")
            for i, opt in enumerate(available):
                desc = f" - {opt['description']}" if opt["description"] else ""
                print(f"    {i + 1}. {opt['label']}{desc}")
            idx = input(f"  Select priority [1-{len(available)}]: ").strip()
            try:
                idx = int(idx) - 1
                print_priority = available[idx]["value"]
                print(f"  Using priority: {print_priority}")
            except (ValueError, IndexError):
                print("  Invalid selection, using first available option.")
                print_priority = available[0]["value"]
        else:
            print("  No available print priority options for this material.")
    else:
        print("  No print priority options returned. Using legacy method.")
        outerwall = input("  Optimize outer wall? [Y/n]: ").strip().lower()
        optimize_outerwall = outerwall != "n"

    return print_priority, optimize_outerwall


def _prompt_optimization_settings(client, gcode_id):
    """Prompt for optimization settings: server defaults or custom."""
    print("\n  Optimization velocity/layer settings:")
    print("    1. Use server defaults (Recommended)")
    print("    2. Enter custom settings")
    settings_choice = input("  Choice [1/2]: ").strip()

    min_vel = None
    max_vel = None
    min_vol = None
    max_vol = None
    from_layer = 2
    to_layer = -1

    if settings_choice == "2":
        print("\n  Enter values (press Enter to use server default for that field):\n")

        val = input("    Min velocity in mm/s (Enter to skip = server default): ").strip()
        if val:
            min_vel = float(val)

        val = input("    Max velocity in mm/s (Enter to skip = server default): ").strip()
        if val:
            max_vel = float(val)

        val = input(
            "    Min volumetric flow rate in mm^3/s (Enter to skip = server default): "
        ).strip()
        if val:
            min_vol = float(val)

        val = input(
            "    Max volumetric flow rate in mm^3/s (Enter to skip = server default): "
        ).strip()
        if val:
            max_vol = float(val)

        val = input("    From layer [2]: ").strip()
        if val:
            from_layer = max(int(val), 2)

        val = input("    To layer [-1 = last layer]: ").strip()
        if val:
            to_layer = int(val)
    else:
        print("  Fetching server defaults...")
        defaults = get_default_optimization_settings(client, gcode_id)
        if defaults:
            print(
                f"    Server velocity range: minVelocity={defaults.get('minVelocity')}, "
                f"maxVelocity={defaults.get('maxVelocity')}"
            )
            print("    Optimizer: HYBRID (always used by this script)")
            layers = defaults.get("layersToOptimize", [])
            if layers:
                from_layer = max(layers[0].get("fromLayer", 2), 2)
                to_layer = layers[0].get("toLayer", -1)
                print(f"    Default layer range: {from_layer} to {to_layer}")
        else:
            print("    Could not fetch defaults; using from_layer=2, to_layer=-1.")

    return min_vel, max_vel, min_vol, max_vol, from_layer, to_layer


# =============================================================================
# Execution Helpers
# =============================================================================


def _execute_simulation(client, gcode_id, file_path):
    """Run a single simulation cycle."""
    chamber_temp, bed_temp = _prompt_temperatures()

    print("\n  Summary:")
    print(f"    File:     {os.path.basename(file_path)}")
    print(f"    GCode ID: {gcode_id}")
    print(f"    Chamber:  {format_temp_display(chamber_temp)}")
    print(f"    Bed:      {format_temp_display(bed_temp)}")
    confirm = input("\n  Proceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("  Cancelled.")
        return False

    try:
        print("\n  --- Running Simulation ---")
        sim_id, result, thermal_url = run_simulation(client, gcode_id, chamber_temp, bed_temp)

        if thermal_url:
            dl = input("\n  Download thermal index G-code? [Y/n]: ").strip().lower()
            if dl != "n":
                out_path = os.path.splitext(file_path)[0] + "_thermal_index.gcode"
                download_file(thermal_url, out_path)

        return True
    except Exception as e:
        print(f"\n  Simulation error: {e}")
        return False


def _execute_optimization(client, gcode_id, material_id, file_path):
    """Run a single optimization cycle."""
    print_priority, optimize_outerwall = _prompt_print_priority(client, material_id)

    min_vel, max_vel, min_vol, max_vol, from_layer, to_layer = _prompt_optimization_settings(
        client, gcode_id
    )

    chamber_temp, bed_temp = _prompt_temperatures()

    sim_settings = compute_simulation_settings(chamber_temp, bed_temp)
    opt_settings = build_optimization_settings(
        print_priority=print_priority,
        optimize_outerwall=optimize_outerwall,
        min_velocity_mm=min_vel,
        max_velocity_mm=max_vel,
        min_volumetric_mm3=min_vol,
        max_volumetric_mm3=max_vol,
        from_layer=from_layer,
        to_layer=to_layer,
    )

    priority_display = print_priority or f"outerwall={optimize_outerwall}"
    to_layer_display = to_layer if to_layer != -1 else "last layer"
    print("\n  Summary:")
    print(f"    File:      {os.path.basename(file_path)}")
    print(f"    GCode ID:  {gcode_id}")
    print(f"    Priority:  {priority_display}")
    print(f"    Layers:    {from_layer} to {to_layer_display}")
    print(f"    Chamber:   {format_temp_display(chamber_temp)}")
    print(f"    Bed:       {format_temp_display(bed_temp)}")
    confirm = input("\n  Proceed? [Y/n]: ").strip().lower()
    if confirm == "n":
        print("  Cancelled.")
        return False

    try:
        print("\n  --- Running Optimization ---")
        opt_id, result, optimized_url = run_optimization(
            client, gcode_id, sim_settings, opt_settings
        )

        if optimized_url:
            dl = input("\n  Download optimized G-code? [Y/n]: ").strip().lower()
            if dl != "n":
                out_path = os.path.splitext(file_path)[0] + "_optimized.gcode"
                download_file(optimized_url, out_path)

        return True
    except Exception as e:
        print(f"\n  Optimization error: {e}")
        return False


def _post_run_menu(primary_action):
    """Display the post-run menu."""
    if primary_action == "simulate":
        label_1 = "Re-run SIMULATION (same G-code, no re-upload)"
        label_2 = "Run OPTIMIZATION instead (same G-code, no re-upload)"
    else:
        label_1 = "Re-run OPTIMIZATION (same G-code, no re-upload)"
        label_2 = "Run SIMULATION instead (same G-code, no re-upload)"

    print("\n  What next?")
    print(f"    1. {label_1}")
    print(f"    2. {label_2}")
    print("    3. Return to main menu")
    choice = input("  Choice [1/2/3]: ").strip()

    if choice == "1":
        return "rerun"
    elif choice == "2":
        return "switch"
    else:
        return "menu"


# =============================================================================
# Workflows
# =============================================================================


def workflow_simulate(client):
    """Interactive simulation workflow with upload and rerun loop."""
    print("\n=== Simulation Workflow ===\n")

    file_path = input("  G-code file path: ").strip().strip("'\"")
    if not os.path.isfile(file_path):
        print(f"  Error: File not found: {file_path}")
        return

    printer_id = select_printer(client)
    print(f"  Using printer: {printer_id}")

    material_id = select_material(client)
    print(f"  Using material: {material_id}")

    try:
        print("\n  --- Uploading G-code ---")
        gcode_id = upload_and_register_gcode(client, file_path, printer_id, material_id)
    except Exception as e:
        print(f"\n  Upload error: {e}")
        return

    _execute_simulation(client, gcode_id, file_path)

    while True:
        action = _post_run_menu("simulate")
        if action == "rerun":
            _execute_simulation(client, gcode_id, file_path)
        elif action == "switch":
            _execute_optimization(client, gcode_id, material_id, file_path)
        else:
            break


def workflow_optimize(client):
    """Interactive optimization workflow with upload and rerun loop."""
    print("\n=== Optimization Workflow ===\n")

    file_path = input("  G-code file path: ").strip().strip("'\"")
    if not os.path.isfile(file_path):
        print(f"  Error: File not found: {file_path}")
        return

    printer_id = select_printer(client)
    print(f"  Using printer: {printer_id}")

    material_id = select_material(client)
    print(f"  Using material: {material_id}")

    try:
        print("\n  --- Uploading G-code ---")
        gcode_id = upload_and_register_gcode(client, file_path, printer_id, material_id)
    except Exception as e:
        print(f"\n  Upload error: {e}")
        return

    _execute_optimization(client, gcode_id, material_id, file_path)

    while True:
        action = _post_run_menu("optimize")
        if action == "rerun":
            _execute_optimization(client, gcode_id, material_id, file_path)
        elif action == "switch":
            _execute_simulation(client, gcode_id, file_path)
        else:
            break


def workflow_check_simulation(client):
    """Check the status of an existing simulation by ID."""
    sim_id = input("  Enter simulation ID: ").strip()
    if not sim_id:
        return

    print("  Polling...")
    try:
        result = poll_simulation(client, sim_id)
        print("\n  Status: FINISHED")
        print(f"  Thermal Index URL: {result.get('thermalIndexGcodeUrl', 'N/A')}")
        pi = result.get("printInfo")
        if pi:
            print(f"  Print Outcome: {pi.get('printOutcome', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")


def workflow_check_optimization(client):
    """Check the status of an existing optimization by ID."""
    opt_id = input("  Enter optimization ID: ").strip()
    if not opt_id:
        return

    print("  Polling...")
    try:
        result = poll_optimization(client, opt_id)
        print("\n  Status: FINISHED")
        print(f"  Quality Mean: {result.get('qualityMeanImprovement', 'N/A')}")
        print(f"  Quality Std:  {result.get('qualityStdImprovement', 'N/A')}")
        print(f"  Download URL: {result.get('optimizedGcodeWithThermalIndexesUrl', 'N/A')}")
    except Exception as e:
        print(f"  Error: {e}")


def workflow_recent_runs(client):
    """Fetch and display recent simulation and optimization runs."""
    print("\n  Fetching recent runs...")
    try:
        opts, sims = get_recent_runs(client)
    except RuntimeError as e:
        print(f"  Error: {e}")
        return

    print(f"\n  === Recent Optimizations ({len(opts)}) ===")
    for opt in opts[:20]:
        status = opt.get("status", "?")
        name = opt.get("name", "?")
        qm = opt.get("qualityMeanImprovement", "")
        qs = opt.get("qualityStdImprovement", "")
        quality_str = f" | Quality: mean={qm}, std={qs}" if qm else ""
        gcode = opt.get("gcode") or {}
        printer = (gcode.get("printer") or {}).get("name", "?")
        material = (gcode.get("material") or {}).get("name", "?")
        print(f"    [{status:10s}] {name}")
        print(f"               ID: {opt.get('id', '?')} | {printer} / {material}{quality_str}")

    print(f"\n  === Recent Simulations ({len(sims)}) ===")
    for sim in sims[:20]:
        status = sim.get("status", "?")
        name = sim.get("name", "?")
        pi = sim.get("printInfo") or {}
        outcome = pi.get("printOutcome", "")
        outcome_str = f" | Outcome: {outcome}" if outcome else ""
        gcode = sim.get("gcode") or {}
        printer = (gcode.get("printer") or {}).get("name", "?")
        material = (gcode.get("material") or {}).get("name", "?")
        print(f"    [{status:10s}] {name}")
        print(f"               ID: {sim.get('id', '?')} | {printer} / {material}{outcome_str}")


# =============================================================================
# Main Menu
# =============================================================================


def display_menu():
    """Display the main menu."""
    print("\n=== Helio Additive API Tool ===\n")
    print("  1. List supported printers")
    print("  2. List supported materials")
    print("  3. Check account quota")
    print("  4. Upload G-code and run SIMULATION")
    print("  5. Upload G-code and run OPTIMIZATION")
    print("  6. Check status of simulation (by ID)")
    print("  7. Check status of optimization (by ID)")
    print("  8. View recent runs (history)")
    print("  0. Exit")
    print()
    print("  For advanced features (thermal history, mesh visualization):")
    print("    These require enterprise access - contact Helio Additive.")
    print("    Run: python examples/interactive_cli.py")
    print("    Or see: examples/advanced/README.md")
    print()


def main():
    """Entry point: load PAT, verify connectivity, run menu loop."""
    print("=== Helio Additive API Tool (Basic) ===\n")

    pat_token = load_pat_token()
    client = HelioClient(pat_token)

    # Verify API connectivity
    print("Verifying API connectivity...")
    quota = check_user_quota(client)
    if "error" in quota:
        print(f"Warning: Could not verify connectivity: {quota['error']}")
        print("Continuing anyway. Some operations may fail.\n")
    else:
        sub = quota.get("subscription_name") or "None"
        remaining = quota.get("remaining_opts_this_month", 0)
        addons = quota.get("add_on_optimizations", 0)
        print(f"  Connected! Subscription: {sub}")
        print(f"  Remaining optimizations this month: {remaining} (+{addons} add-ons)")
        if quota.get("is_free_trial_active"):
            print("  Free trial is active.")
        elif quota.get("free_trial_eligible"):
            print("  You are eligible for a free trial.")
        print()

    # Main menu loop
    while True:
        display_menu()
        choice = input("  Select option: ").strip()

        if choice == "0":
            print("Goodbye!")
            break
        elif choice == "1":
            print("\n  Fetching printers...")
            printers = list_printers(client)
            print(f"\n  Found {len(printers)} printers:\n")
            for p in printers:
                bbs = (
                    f" (BambuStudio: {p['bambustudio_name']})" if p["bambustudio_name"] else ""
                )
                print(f"    {p['name']}{bbs}  [{p['id']}]")
        elif choice == "2":
            print("\n  Fetching materials...")
            materials = list_materials(client)
            print(f"\n  Found {len(materials)} materials (FILAMENT only):\n")
            for m in materials:
                bbs = (
                    f" (BambuStudio: {m['bambustudio_name']})" if m["bambustudio_name"] else ""
                )
                print(f"    {m['name']}{bbs}  [{m['id']}]")
        elif choice == "3":
            quota = check_user_quota(client)
            if "error" in quota:
                print(f"  Error: {quota['error']}")
            else:
                print(f"\n  Subscription: {quota.get('subscription_name') or 'None'}")
                print(f"  Remaining this month: {quota.get('remaining_opts_this_month', 0)}")
                print(f"  Add-on optimizations: {quota.get('add_on_optimizations', 0)}")
                print(f"  Free trial active: {quota.get('is_free_trial_active', False)}")
                print(f"  Free trial claimed: {quota.get('is_free_trial_claimed', False)}")
                print(f"  Free trial eligible: {quota.get('free_trial_eligible', False)}")
        elif choice == "4":
            workflow_simulate(client)
        elif choice == "5":
            workflow_optimize(client)
        elif choice == "6":
            workflow_check_simulation(client)
        elif choice == "7":
            workflow_check_optimization(client)
        elif choice == "8":
            workflow_recent_runs(client)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
