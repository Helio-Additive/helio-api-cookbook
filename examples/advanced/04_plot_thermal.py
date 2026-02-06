#!/usr/bin/env python3
"""
STEP 4: Plot Thermal Curve
==========================

This script creates a temperature vs time plot for specific elements.
This shows how the element cooled after deposition - the core output
for thermal analysis in materials science research.

ENTERPRISE FEATURE: You need thermal history data from step 3, which
requires enterprise access. Contact Helio Additive: https://helioadditive.com

What you'll learn:
    - Loading thermal history CSV data
    - Finding an element by its index
    - Creating matplotlib plots
    - Interpreting thermal cooling curves

Prerequisites:
    - pip install matplotlib
    - Thermal history CSV from step 3 (03_download_thermal.py)
    - Element INDEX from the visualization (step 2)

Usage:
    python examples/advanced/04_plot_thermal.py
"""

import os
import sys

# ============================================================================
# PATH SETUP
# ============================================================================

_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isdir(os.path.join(_repo_root, "src", "helio_api")):
    sys.path.insert(0, os.path.join(_repo_root, "src"))

# ============================================================================
# IMPORTS
# ============================================================================

from helio_api import (  # noqa: E402
    HAS_MATPLOTLIB,  # Check if matplotlib is installed
    export_thermal_data_csv,  # Export data to CSV
    extract_thermal_data,  # Extract timestamps and temperatures
    get_element_thermal_history,  # Find a specific element's data
    load_thermal_history_csv,  # Load the thermal history CSV
    plot_element_thermal_history,  # Create the plot
)

# ============================================================================
# MAIN WORKFLOW
# ============================================================================


def main():
    """
    Main workflow: Load thermal data, get element index, create plot.
    """
    print("\n" + "=" * 60)
    print("STEP 4: Plot Thermal Curve")
    print("=" * 60)
    print()
    print("This creates a temperature vs time plot showing how an element")
    print("cooled after deposition.")
    print()

    # -------------------------------------------------------------------------
    # Step 4.0: Check matplotlib is installed
    # -------------------------------------------------------------------------

    if not HAS_MATPLOTLIB:
        print("ERROR: matplotlib is not installed.")
        print()
        print("Install with:")
        print("  pip install matplotlib")
        print()
        print("Or install all optional dependencies:")
        print("  pip install helio-api-cookbook[full]")
        return

    # -------------------------------------------------------------------------
    # Step 4.1: Get the thermal history CSV file
    # -------------------------------------------------------------------------
    # This should be the file created by step 3 (03_download_thermal.py)

    thermal_csv = input("Path to thermal history CSV file: ").strip().strip("'\"")
    if not thermal_csv:
        print("Error: No file path provided.")
        return
    if not os.path.isfile(thermal_csv):
        print(f"Error: File not found: {thermal_csv}")
        return

    # -------------------------------------------------------------------------
    # Step 4.2: Load the thermal history data
    # -------------------------------------------------------------------------
    # The CSV contains one row per element, with 100 temperature readings
    # and 100 timestamps for each element.

    print("\nLoading thermal history data...")
    thermal_data = load_thermal_history_csv(thermal_csv)

    if not thermal_data:
        print("Error: Could not load thermal history data.")
        print("Make sure the CSV file is in the correct format.")
        return

    print(f"  Loaded {len(thermal_data)} elements from thermal history.")
    print()

    # -------------------------------------------------------------------------
    # Step 4.3: Collect elements to plot
    # -------------------------------------------------------------------------
    # You can plot multiple elements on the same graph for comparison.
    # Enter the element INDEX from the visualization (step 2).

    print("Enter element indices to plot. You can plot multiple elements")
    print("on the same graph for comparison.")
    print()
    print("Type the element index and press Enter. When done, type 'done'.")
    print()

    elements_to_plot = []

    while True:
        idx_str = input("  Element index (or 'done'): ").strip()

        if idx_str.lower() == "done":
            break

        try:
            element_index = int(idx_str)
        except ValueError:
            print("  Invalid number. Enter a valid element index or 'done'.")
            continue

        # Find this element in the thermal data
        history = get_element_thermal_history(thermal_data, element_index)

        if not history:
            print(f"  Element {element_index} not found in this thermal history file.")
            print("  Make sure the element is in the same layer as this file.")
            continue

        # Extract the timestamps and temperatures
        timestamps, temperatures = extract_thermal_data(history)

        if not timestamps or not temperatures:
            print(f"  No valid thermal data for element {element_index}.")
            continue

        elements_to_plot.append((element_index, timestamps, temperatures))
        print(f"  Added element {element_index} ({len(timestamps)} data points)")

    if not elements_to_plot:
        print("\nNo elements selected. Nothing to plot.")
        return

    # -------------------------------------------------------------------------
    # Step 4.4: Choose whether to save the plot
    # -------------------------------------------------------------------------

    print()
    save_choice = input("Save plot to file? [y/N]: ").strip().lower()
    output_path = None

    if save_choice == "y":
        indices_str = "_".join(str(e[0]) for e in elements_to_plot[:3])
        default_name = f"thermal_curve_{indices_str}.png"
        output_path = input(f"  Output path [{default_name}]: ").strip() or default_name

    # -------------------------------------------------------------------------
    # Step 4.5: Create the plot
    # -------------------------------------------------------------------------
    # The plot shows temperature (Kelvin) on the Y-axis and time (seconds)
    # on the X-axis. Each element gets a different colored line.

    print("\nCreating plot...")

    # Set a title
    if len(elements_to_plot) == 1:
        title = f"Thermal History - Element {elements_to_plot[0][0]}"
    else:
        title = "Thermal History Comparison"

    success = plot_element_thermal_history(
        elements_to_plot,
        output_path=output_path,
        title=title,
    )

    if success:
        if output_path:
            print(f"\nPlot saved to: {output_path}")
        else:
            print("\nPlot displayed. Close the plot window to continue.")

        # -------------------------------------------------------------------------
        # Step 4.6: Offer CSV export
        # -------------------------------------------------------------------------
        # Export the raw data for further analysis in spreadsheets or other tools.

        print()
        export_choice = input("Export data to CSV? [y/N]: ").strip().lower()
        if export_choice == "y":
            indices_str = "_".join(str(e[0]) for e in elements_to_plot[:3])
            default_csv = f"thermal_data_{indices_str}.csv"
            csv_path = input(f"  Output path [{default_csv}]: ").strip() or default_csv
            export_thermal_data_csv(elements_to_plot, csv_path)
            print()
            print("CSV format:")
            print("  - element_index: Which element this row is for")
            print("  - timestamp_s: Time in seconds")
            print("  - temperature_K: Temperature in Kelvin")

        print()
        print("=" * 60)
        print("INTERPRETING THE PLOT")
        print("=" * 60)
        print()
        print("The plot shows how temperature changes over time after deposition:")
        print()
        print("  - Y-axis: Temperature in Kelvin")
        print("  - X-axis: Time in seconds")
        print()
        print("A typical cooling curve shows:")
        print("  1. Initial high temperature (deposition)")
        print("  2. Rapid cooling phase")
        print("  3. Gradual approach to ambient temperature")
        print()
        print("For quality analysis, compare elements with different quality scores:")
        print("  - Elements with quality near 0 (green in viz) have ideal cooling")
        print("  - Elements with quality < 0 (blue) cooled too quickly")
        print("  - Elements with quality > 0 (red) stayed hot too long")
    else:
        print("\nError creating plot.")


if __name__ == "__main__":
    main()
