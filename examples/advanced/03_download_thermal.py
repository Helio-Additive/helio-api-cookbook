#!/usr/bin/env python3
"""
STEP 3: Download Thermal History
================================

This script downloads the thermal history data for a specific layer.
Thermal history shows how each element's temperature changed over time
after deposition - this is the core data for thermal analysis.

ENTERPRISE FEATURE: Thermal history downloads require Helio to enable this
for your account. This is a paid feature primarily used by materials scientists.
Contact Helio Additive to discuss access: https://helioadditive.com

What you'll learn:
    - Thermal history is per-layer (one file per layer)
    - Each element has 100 temperature/time measurements
    - Element indices link thermal data to mesh data

Prerequisites:
    - HELIO_PAT environment variable set
    - pip install helio-api-cookbook[thermal]  (includes pyarrow)
    - Know the LAYER number from the visualization (step 2)

Usage:
    python examples/advanced/03_download_thermal.py
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
    HelioClient,
    download_thermal_history_as_csv,
    load_pat_token,
)

# ============================================================================
# MAIN WORKFLOW
# ============================================================================


def main():
    """
    Main workflow: Connect to API, get layer number, download thermal history.
    """
    print("\n" + "=" * 60)
    print("STEP 3: Download Thermal History")
    print("=" * 60)
    print()
    print("This downloads temperature-over-time data for a specific layer.")
    print()
    print("IMPORTANT:")
    print("  - Thermal history files are PER LAYER")
    print("  - You need to know the layer number from the visualization")
    print("  - Not all layers may have thermal data available")
    print()
    print("NOTE: This is an enterprise feature. If you receive 404 errors,")
    print("contact Helio Additive to enable thermal history for your account.")
    print()

    # -------------------------------------------------------------------------
    # Step 3.1: Load API credentials
    # -------------------------------------------------------------------------

    print("Loading API credentials...")
    pat_token = load_pat_token()
    client = HelioClient(pat_token)
    print("  Connected to Helio API.\n")

    # -------------------------------------------------------------------------
    # Step 3.2: Get the simulation or optimization ID
    # -------------------------------------------------------------------------
    # Use the same ID from step 1

    sim_or_opt_id = input("Enter simulation or optimization ID: ").strip()
    if not sim_or_opt_id:
        print("Error: No ID provided.")
        return

    # -------------------------------------------------------------------------
    # Step 3.3: Determine if this is an optimization with optimized data
    # -------------------------------------------------------------------------

    is_opt = input("Is this an optimization? [y/N]: ").strip().lower() == "y"

    use_optimized = True
    if is_opt:
        use_opt = input("Use optimized data (vs original)? [Y/n]: ").strip().lower()
        use_optimized = use_opt != "n"

    # The API parameter combines these:
    # is_optimized = True only if it's an optimization AND we want optimized data
    is_optimized = is_opt and use_optimized

    # -------------------------------------------------------------------------
    # Step 3.4: Get the layer number
    # -------------------------------------------------------------------------
    # This is the layer you identified in the visualization (step 2)
    # Layers are 0-indexed

    print()
    print("Enter the LAYER number from the visualization.")
    print("(Layers are 0-indexed, e.g., layer 0, 1, 2, ...)")
    layer_str = input("Layer number: ").strip()
    try:
        layer = int(layer_str)
    except ValueError:
        print("Error: Invalid layer number.")
        return

    # -------------------------------------------------------------------------
    # Step 3.5: Choose output directory
    # -------------------------------------------------------------------------

    output_dir = input("Output directory [.]: ").strip() or "."
    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # Step 3.6: Download the thermal history
    # -------------------------------------------------------------------------
    # This function:
    # 1. Queries the API for the presigned download URL
    # 2. Downloads the Parquet file
    # 3. Converts it to CSV using pyarrow

    print(f"\nDownloading thermal history for layer {layer}...")
    try:
        download_thermal_history_as_csv(
            client,
            layer,
            is_optimized,
            sim_or_opt_id,
            output_dir,
        )

        csv_path = os.path.join(output_dir, f"thermal_history_layer{layer}.csv")
        if os.path.isfile(csv_path):
            print(f"\nSuccess! Thermal history saved to: {csv_path}")
            print()
            print("The CSV contains:")
            print("  - element_index: Links to the mesh data")
            print("  - datapoint 000-099: 100 temperature readings (Kelvin)")
            print("  - timestamp 000-099: Time of each reading (seconds)")
            print()
            print("Next step: Run 04_plot_thermal.py with this CSV and the")
            print("element INDEX you noted from the visualization.")
        else:
            print("\nNote: Download may have failed or file format changed.")
            print("Check the output directory for any downloaded files.")

    except Exception as e:
        print(f"\nError: {e}")
        print()
        print("Common issues:")
        print("  - 404 error: Thermal history not available for this layer")
        print("    Try a different layer number, or contact Helio to enable")
        print("    thermal history for your account.")
        print("  - Invalid ID: Check that the simulation/optimization exists")
        print("  - pyarrow not installed: pip install pyarrow")


if __name__ == "__main__":
    main()
