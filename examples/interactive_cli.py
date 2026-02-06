#!/usr/bin/env python3
"""
Interactive CLI for the Helio Additive API.

Provides a menu-driven interface for uploading G-code, running simulations
and optimizations, browsing catalogs, and downloading results.

Usage:
    pip install -e .    # from repo root (or pip install helio-api-cookbook)
    python examples/interactive_cli.py
"""

import os
import sys

# Allow running directly without pip install by adding src/ to path
_repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.isdir(os.path.join(_repo_root, "src", "helio_api")):
    sys.path.insert(0, os.path.join(_repo_root, "src"))

from helio_api import (  # noqa: E402
    HAS_MATPLOTLIB,
    HelioClient,
    build_optimization_settings,
    check_user_quota,
    compute_simulation_settings,
    download_file,
    download_mesh_as_csv,
    download_thermal_history_as_csv,
    export_thermal_data_csv,
    extract_thermal_data,
    generate_mesh_visualization,
    get_default_optimization_settings,
    get_element_by_index,
    get_element_thermal_history,
    get_elements_by_layer,
    get_layer_count,
    get_print_priority_options,
    get_recent_runs,
    list_materials,
    list_printers,
    load_mesh_csv,
    load_pat_token,
    load_thermal_history_csv,
    plot_element_thermal_history,
    poll_optimization,
    poll_simulation,
    print_element_info,
    run_optimization,
    run_simulation,
    upload_and_register_gcode,
)
from helio_api.download import HAS_PYARROW  # noqa: E402

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

    # Browse
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

    # Browse
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
    """Prompt for an optional numeric value.

    Args:
        prompt: The prompt text to display.
        default: Value returned if the user presses Enter without typing.

    Returns:
        The float value entered, or default if skipped.
    """
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
    """Format a temperature value for summary display.

    Returns the numeric value as a string, or 'auto-calculated by Helio'
    if the value was not provided (None).
    """
    if value is not None:
        return f"{value} C"
    return "auto-calculated by Helio"


# =============================================================================
# Prompt Helpers
# =============================================================================


def _prompt_temperatures():
    """Prompt for optional chamber and bed temperature overrides.

    These are optional -- if skipped, Helio will auto-calculate temperature
    parameters from the G-code or use sensible defaults.

    Returns:
        (chamber_temp, bed_temp) tuple. Either may be None if skipped.
    """
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
    """Prompt for a print priority selection for the given material.

    Returns:
        (print_priority, optimize_outerwall) tuple. One will be set, the other None.
    """
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
    """Prompt for optimization settings: server defaults or custom.

    Returns:
        (min_vel, max_vel, min_vol, max_vol, from_layer, to_layer) tuple.
    """
    print("\n  Optimization velocity/layer settings:")
    print("    1. Use server defaults (Recommended)")
    print("    2. Enter custom settings")
    settings_choice = input("  Choice [1/2]: ").strip()

    min_vel = None
    max_vel = None
    min_vol = None
    max_vol = None
    from_layer = 2
    to_layer = -1  # -1 = last layer

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
        # Show server defaults for informational purposes
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
    """Run a single simulation cycle.

    Returns True on success, False otherwise.
    """
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
    """Run a single optimization cycle.

    Returns True on success, False otherwise.
    """
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
    """Display the post-run menu. Returns 'rerun', 'switch', or 'menu'."""
    if primary_action == "simulate":
        label_1 = "Re-run SIMULATION (same G-code, printer, material -- no re-upload)"
        label_2 = "Run OPTIMIZATION instead (same G-code, printer, material -- no re-upload)"
    else:
        label_1 = "Re-run OPTIMIZATION (same G-code, printer, material -- no re-upload)"
        label_2 = "Run SIMULATION instead (same G-code, printer, material -- no re-upload)"

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
# Full Workflows
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


def workflow_thermal_histories(client):
    """Download thermal history data as Parquet (optionally CSV)."""
    print(
        "\n  Note: Thermal histories require Helio to enable this feature for your"
    )
    print(
        "  account and is an exclusive enterprise feature mainly used for advanced "
        "R&D/material science.\n"
    )
    print("  Contact Helio Additive if you receive 404 errors when downloading.\n")
    if not HAS_PYARROW:
        print("  pyarrow is not installed. Parquet files will be downloaded")
        print("  but cannot be converted to CSV. Install with: pip install pyarrow\n")

    sim_or_opt_id = input("  Enter simulation or optimization ID: ").strip()
    if not sim_or_opt_id:
        return

    is_opt = input("  Is this an optimized result? [y/N]: ").strip().lower()
    is_optimized = is_opt == "y"

    layer_str = input("  Layer number: ").strip()
    try:
        layer = int(layer_str)
    except ValueError:
        print("  Invalid layer number.")
        return

    output_dir = input("  Output directory [.]: ").strip() or "."
    os.makedirs(output_dir, exist_ok=True)

    try:
        download_thermal_history_as_csv(client, layer, is_optimized, sim_or_opt_id, output_dir)
    except Exception as e:
        print(f"  Error: {e}")


def workflow_download_mesh(client):
    """Download mesh file as Parquet (optionally CSV)."""
    print("\n  Note: Mesh downloads require Helio to enable this feature for your")
    print("  account. Contact Helio Additive if you receive 404 errors.\n")
    if not HAS_PYARROW:
        print("  pyarrow is not installed. Parquet files will be downloaded")
        print("  but cannot be converted to CSV. Install with: pip install pyarrow\n")

    sim_or_opt_id = input("  Enter simulation or optimization ID: ").strip()
    if not sim_or_opt_id:
        return

    is_opt = input("  Is this an optimization? [y/N]: ").strip().lower()
    is_optimization = is_opt == "y"

    use_optimized = True
    if is_optimization:
        use_opt = input("  Download optimized mesh (vs original)? [Y/n]: ").strip().lower()
        use_optimized = use_opt != "n"

    output_dir = input("  Output directory [.]: ").strip() or "."
    os.makedirs(output_dir, exist_ok=True)

    try:
        result = download_mesh_as_csv(
            client, sim_or_opt_id, output_dir, is_optimization, use_optimized
        )
        if result:
            print(f"\n  Mesh file saved: {result}")
    except Exception as e:
        print(f"  Error: {e}")


def workflow_generate_visualization():
    """Generate interactive HTML visualization from mesh CSV."""
    print("\n  Generate interactive 3D visualization from mesh CSV.\n")

    mesh_csv_path = input("  Path to mesh CSV file: ").strip().strip("'\"")
    if not mesh_csv_path:
        return
    if not os.path.isfile(mesh_csv_path):
        print(f"  Error: File not found: {mesh_csv_path}")
        return

    default_output = os.path.splitext(mesh_csv_path)[0] + "_visualization.html"
    output_html = input(f"  Output HTML path [{default_output}]: ").strip() or default_output

    title = input("  Visualization title [Mesh Visualization]: ").strip() or "Mesh Visualization"

    try:
        success = generate_mesh_visualization(mesh_csv_path, output_html, title)
        if success:
            open_browser = input("\n  Open in browser? [Y/n]: ").strip().lower()
            if open_browser != "n":
                import webbrowser

                webbrowser.open(f"file://{os.path.abspath(output_html)}")
    except Exception as e:
        print(f"  Error: {e}")


def workflow_plot_element_thermal():
    """Plot thermal history for one or more elements."""
    print("\n  Plot thermal history for elements.\n")

    if not HAS_MATPLOTLIB:
        print("  Error: matplotlib is not installed.")
        print("  Install with: pip install matplotlib")
        return

    # Load mesh data
    mesh_csv_path = input("  Path to mesh CSV file: ").strip().strip("'\"")
    if not mesh_csv_path:
        return
    if not os.path.isfile(mesh_csv_path):
        print(f"  Error: File not found: {mesh_csv_path}")
        return

    print("  Loading mesh data...")
    mesh_data = load_mesh_csv(mesh_csv_path)
    if not mesh_data:
        print("  Error: Could not load mesh data.")
        return

    layer_count = get_layer_count(mesh_data)
    print(f"  Loaded {len(mesh_data)} elements across {layer_count + 1} layers.")

    # Collect element indices
    elements_to_plot = []

    while True:
        print("\n  Options:")
        print("    1. Enter element index directly")
        print("    2. Browse elements by layer")
        print("    3. Done selecting elements")
        choice = input("  Choice [1/2/3]: ").strip()

        if choice == "3":
            break
        elif choice == "2":
            # Browse by layer
            layer_str = input(f"  Enter layer number (0-{layer_count}): ").strip()
            try:
                layer = int(layer_str)
            except ValueError:
                print("  Invalid layer number.")
                continue

            layer_elements = get_elements_by_layer(mesh_data, layer)
            if not layer_elements:
                print(f"  No elements found in layer {layer}.")
                continue

            print(f"\n  Elements in layer {layer} ({len(layer_elements)} total):")
            # Show first 20 elements
            for i, elem in enumerate(layer_elements[:20]):
                print(
                    f"    Index: {elem['index']:6d}  |  "
                    f"Partition: {elem['partition']:3d}  |  "
                    f"Quality: {elem['quality']:.4f}"
                )
            if len(layer_elements) > 20:
                print(f"    ... and {len(layer_elements) - 20} more elements")

            idx_str = input("\n  Enter element index to add (or press Enter to skip): ").strip()
            if idx_str:
                try:
                    element_index = int(idx_str)
                    element = get_element_by_index(mesh_data, element_index)
                    if element:
                        elements_to_plot.append(element_index)
                        print_element_info(element)
                    else:
                        print(f"  Element {element_index} not found.")
                except ValueError:
                    print("  Invalid element index.")
        else:
            # Direct entry
            idx_str = input("  Enter element index: ").strip()
            try:
                element_index = int(idx_str)
                element = get_element_by_index(mesh_data, element_index)
                if element:
                    elements_to_plot.append(element_index)
                    print_element_info(element)
                else:
                    print(f"  Element {element_index} not found.")
            except ValueError:
                print("  Invalid element index.")

        if elements_to_plot:
            print(f"\n  Currently selected: {elements_to_plot}")

    if not elements_to_plot:
        print("  No elements selected.")
        return

    # Determine layer for thermal history
    # All elements should ideally be from the same layer for thermal history
    element_layers = set()
    for idx in elements_to_plot:
        elem = get_element_by_index(mesh_data, idx)
        if elem:
            element_layers.add(elem["layer"])

    if len(element_layers) > 1:
        print(f"\n  Warning: Selected elements span multiple layers: {element_layers}")
        print("  Thermal history files are per-layer. You may need multiple files.")

    # Load thermal history
    thermal_csv_path = input("\n  Path to thermal history CSV file: ").strip().strip("'\"")
    if not thermal_csv_path:
        return
    if not os.path.isfile(thermal_csv_path):
        print(f"  Error: File not found: {thermal_csv_path}")
        return

    print("  Loading thermal history data...")
    thermal_data = load_thermal_history_csv(thermal_csv_path)
    if not thermal_data:
        print("  Error: Could not load thermal history data.")
        return
    print(f"  Loaded thermal history for {len(thermal_data)} elements.")

    # Extract data for each element
    plot_data = []
    for element_index in elements_to_plot:
        history = get_element_thermal_history(thermal_data, element_index)
        if history:
            timestamps, temperatures = extract_thermal_data(history)
            if timestamps and temperatures:
                plot_data.append((element_index, timestamps, temperatures))
                print(f"  Found thermal history for element {element_index}:"
                      f" {len(timestamps)} datapoints")
            else:
                print(f"  Warning: No valid data for element {element_index}")
        else:
            print(f"  Warning: Element {element_index} not found in thermal history file.")

    if not plot_data:
        print("  Error: No thermal data found for selected elements.")
        return

    # Plot options
    save_choice = input("\n  Save plot to file? [y/N]: ").strip().lower()
    output_path = None
    if save_choice == "y":
        indices = "_".join(str(e) for e in elements_to_plot[:3])
        default_name = f"thermal_history_elements_{indices}.png"
        output_path = input(f"  Output path [{default_name}]: ").strip() or default_name

    title = None
    if len(plot_data) == 1:
        title = f"Thermal History - Element {plot_data[0][0]}"
    else:
        title = "Thermal History Comparison"

    plot_element_thermal_history(plot_data, output_path, title)


def workflow_thermal_exploration(client):
    """Unified workflow: visualize mesh → click elements → plot thermal history."""
    print("\n=== Thermal History Exploration ===\n")

    if not HAS_MATPLOTLIB:
        print("  Error: matplotlib is not installed.")
        print("  Install with: pip install matplotlib")
        return

    if not HAS_PYARROW:
        print("  Warning: pyarrow is not installed. Parquet → CSV conversion may fail.")
        print("  Install with: pip install pyarrow\n")

    # Step 1: Get simulation/optimization ID
    sim_or_opt_id = input("  Simulation or optimization ID: ").strip()
    if not sim_or_opt_id:
        return

    is_opt = input("  Is this an optimization? [y/N]: ").strip().lower() == "y"
    use_optimized = True
    if is_opt:
        use_optimized = input("  Use optimized data? [Y/n]: ").strip().lower() != "n"

    # Step 2: Download mesh and generate visualization
    print("\n  Downloading mesh...")
    output_dir = "."
    mesh_path = download_mesh_as_csv(client, sim_or_opt_id, output_dir, is_opt, use_optimized)
    if not mesh_path:
        print("  Failed to download mesh.")
        return

    print("\n  Generating visualization...")
    html_path = os.path.splitext(mesh_path)[0] + "_visualization.html"
    if not generate_mesh_visualization(mesh_path, html_path, "Thermal Exploration"):
        print("  Failed to generate visualization.")
        return

    print("  Opening in browser...")
    import webbrowser

    webbrowser.open(f"file://{os.path.abspath(html_path)}")

    # Track downloaded thermal histories to avoid re-downloading
    downloaded_layers = {}  # layer -> csv_path
    # Track loaded thermal data to avoid re-parsing
    loaded_thermal_data = {}  # layer -> thermal_data list

    # Step 3: Interactive element selection loop
    print("\n  Visualization opened in browser.")
    print("  Click on elements to see their index and layer in the info panel.")
    print()
    print("  " + "=" * 50)
    print("  PLOTTING THERMAL HISTORIES")
    print("  " + "=" * 50)
    print()
    print("  You can plot MULTIPLE elements on the same graph for comparison.")
    print()
    print("  How it works:")
    print("    1. Enter element index and layer (repeat to add more elements)")
    print("    2. Type 'plot' when ready to generate the graph")
    print("    3. After plotting, you can export the data as CSV")
    print()
    print("  Commands:")
    print("    <number>  - Add an element to plot (you'll be asked for the layer)")
    print("    plot      - Generate the plot with all selected elements")
    print("    export    - Export selected elements' data as CSV (without plotting)")
    print("    clear     - Clear current selection and start over")
    print("    quit      - Exit exploration")
    print()

    while True:
        # Collect elements to plot together
        elements_to_plot = []  # list of (element_index, layer, timestamps, temps)

        while True:
            if elements_to_plot:
                selected_str = ", ".join(
                    f"{e[0]}(L{e[1]})" for e in elements_to_plot
                )
                print(f"\n  Selected: [{selected_str}]")

            idx_str = input("  > Enter element index (or plot/export/clear/quit): ").strip()

            if idx_str.lower() == "quit":
                print("\n  Exploration complete.")
                return

            if idx_str.lower() == "clear":
                elements_to_plot = []
                print("  Selection cleared.")
                continue

            if idx_str.lower() == "plot":
                break

            if idx_str.lower() == "export":
                if not elements_to_plot:
                    print("  No elements selected yet. Add elements first.")
                    continue
                # Export without plotting
                plot_data = [(idx, ts, temps) for idx, layer, ts, temps in elements_to_plot]
                indices_str = "_".join(str(e[0]) for e in elements_to_plot[:3])
                if len(elements_to_plot) > 3:
                    indices_str += f"_and{len(elements_to_plot) - 3}more"
                default_csv = f"thermal_data_{indices_str}.csv"
                csv_path = input(f"  Output CSV path [{default_csv}]: ").strip() or default_csv
                export_thermal_data_csv(plot_data, csv_path)
                continue

            try:
                element_index = int(idx_str)
            except ValueError:
                print("  Invalid input. Enter element index or command"
                      " (plot/export/clear/quit).")
                continue

            layer_str = input("    Layer number: ").strip()
            try:
                layer = int(layer_str)
            except ValueError:
                print("  Invalid layer number.")
                continue

            # Download thermal history for this layer if not already downloaded
            if layer not in downloaded_layers:
                print(f"\n  Downloading thermal history for layer {layer}...")
                try:
                    download_thermal_history_as_csv(
                        client, layer, is_opt and use_optimized, sim_or_opt_id, output_dir
                    )
                    csv_path = os.path.join(output_dir, f"thermal_history_layer{layer}.csv")
                    # Only cache if file actually exists
                    if os.path.isfile(csv_path):
                        downloaded_layers[layer] = csv_path
                    else:
                        print("  Download failed or file not available for this layer.")
                        print("  Tip: Try a different layer - not all layers have"
                              " thermal history data.")
                        continue
                except Exception as e:
                    print(f"  Error downloading thermal history: {e}")
                    continue
            else:
                print(f"  Using cached thermal history for layer {layer}.")

            # Load thermal history if not already loaded
            if layer not in loaded_thermal_data:
                thermal_csv = downloaded_layers.get(layer)
                if not thermal_csv or not os.path.isfile(thermal_csv):
                    print(f"  Thermal history file not found for layer {layer}.")
                    continue
                thermal_data = load_thermal_history_csv(thermal_csv)
                if not thermal_data:
                    print("  Failed to load thermal history data.")
                    continue
                loaded_thermal_data[layer] = thermal_data
            else:
                thermal_data = loaded_thermal_data[layer]

            # Find element in thermal history
            history = get_element_thermal_history(thermal_data, element_index)
            if not history:
                print(f"  Element {element_index} not found in thermal history for layer {layer}.")
                print(f"  (Thermal history contains {len(thermal_data)} elements)")
                continue

            # Extract thermal data
            timestamps, temps = extract_thermal_data(history)
            if not timestamps or not temps:
                print(f"  No valid thermal data for element {element_index}.")
                continue

            elements_to_plot.append((element_index, layer, timestamps, temps))
            print(f"  + Added element {element_index} (layer {layer})")

        # Plot all collected elements
        if not elements_to_plot:
            print("  No elements selected to plot.")
            continue

        print(f"\n  Plotting {len(elements_to_plot)} element(s)...")
        plot_data = [(idx, ts, temps) for idx, layer, ts, temps in elements_to_plot]

        if len(elements_to_plot) == 1:
            title = f"Element {elements_to_plot[0][0]} (Layer {elements_to_plot[0][1]})"
        else:
            title = "Thermal History Comparison"

        plot_element_thermal_history(plot_data, title=title)

        # Offer CSV export after plotting
        export_choice = input("\n  Export plotted data to CSV? [y/N]: ").strip().lower()
        if export_choice == "y":
            indices_str = "_".join(str(e[0]) for e in elements_to_plot[:3])
            if len(elements_to_plot) > 3:
                indices_str += f"_and{len(elements_to_plot) - 3}more"
            default_csv = f"thermal_data_{indices_str}.csv"
            csv_path = input(f"  Output CSV path [{default_csv}]: ").strip() or default_csv
            export_thermal_data_csv(plot_data, csv_path)

        # Continue or quit
        another = input("\n  Plot more elements? [Y/n]: ").strip().lower()
        if another == "n":
            break

    print("\n  Exploration complete.")


# =============================================================================
# Main Menu
# =============================================================================


def display_menu():
    """Display the main interactive menu."""
    print("\n=== Helio Additive API Tool ===\n")
    print("  1. List supported printers")
    print("  2. List supported materials")
    print("  3. Check account quota")
    print("  4. Upload G-code and run SIMULATION")
    print("  5. Upload G-code and run OPTIMIZATION")
    print("  6. Check status of existing simulation (by ID)")
    print("  7. Check status of existing optimization (by ID)")
    print("  8. View recent runs (history)")
    print("  9. Download thermal histories (Parquet -> CSV)")
    print("  10. Download mesh file (Parquet -> CSV)")
    print("  11. Generate mesh visualization (HTML)")
    print("  12. Plot element thermal history")
    print("  13. Thermal history exploration (unified)")
    print("  0. Exit")
    print()


def main():
    """Entry point: load PAT, verify connectivity, run menu loop."""
    print("=== Helio Additive API Tool ===\n")

    pat_token = load_pat_token()
    client = HelioClient(pat_token)

    # Verify API connectivity
    print("\nVerifying API connectivity...")
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
        elif choice == "9":
            workflow_thermal_histories(client)
        elif choice == "10":
            workflow_download_mesh(client)
        elif choice == "11":
            workflow_generate_visualization()
        elif choice == "12":
            workflow_plot_element_thermal()
        elif choice == "13":
            workflow_thermal_exploration(client)
        else:
            print("  Invalid option.")


if __name__ == "__main__":
    main()
