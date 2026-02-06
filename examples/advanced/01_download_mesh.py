#!/usr/bin/env python3
"""
STEP 1: Download Mesh Data
==========================

This script downloads the mesh file from a completed simulation or optimization.
The mesh contains element-level data including positions, quality scores, and
thermal properties for every point in your print.

ENTERPRISE FEATURE: Mesh downloads require Helio to enable this for your
account. This is a paid feature primarily used by materials scientists for R&D.
Contact Helio Additive to discuss access: https://helioadditive.com

What you'll learn:
    - How to connect to the Helio API
    - How to download mesh data (Parquet -> CSV conversion)
    - Understanding the mesh data structure

Prerequisites:
    - HELIO_PAT environment variable set with your Personal Access Token
    - pip install helio-api-cookbook[thermal]  (includes pyarrow for Parquet)

Usage:
    python examples/advanced/01_download_mesh.py
"""

import os
import sys

# ============================================================================
# PATH SETUP
# This allows running the script directly without pip install
# ============================================================================

_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isdir(os.path.join(_repo_root, "src", "helio_api")):
    sys.path.insert(0, os.path.join(_repo_root, "src"))

# ============================================================================
# IMPORTS
# ============================================================================

from helio_api import (
    HelioClient,          # The API client - handles authentication and requests
    load_pat_token,       # Loads your Personal Access Token from env or config
    download_mesh_as_csv, # Downloads and converts mesh Parquet to CSV
)

# ============================================================================
# MAIN WORKFLOW
# ============================================================================


def main():
    """
    Main workflow: Connect to API, get user input, download mesh data.
    """
    print("\n" + "=" * 60)
    print("STEP 1: Download Mesh Data")
    print("=" * 60)
    print()
    print("This downloads the mesh file containing element-level data")
    print("from your simulation or optimization.")
    print()
    print("NOTE: This is an enterprise feature. If you receive 404 errors,")
    print("contact Helio Additive to enable mesh downloads for your account.")
    print()

    # -------------------------------------------------------------------------
    # Step 1.1: Load your API credentials
    # -------------------------------------------------------------------------
    # The PAT (Personal Access Token) authenticates you with the Helio API.
    # Set it via: export HELIO_PAT="your-token-here"
    # Or save it to: ~/.helio_config

    print("Loading API credentials...")
    pat_token = load_pat_token()
    client = HelioClient(pat_token)
    print("  Connected to Helio API.\n")

    # -------------------------------------------------------------------------
    # Step 1.2: Get the simulation or optimization ID
    # -------------------------------------------------------------------------
    # You can find this ID in:
    # - The Helio web dashboard after running a simulation/optimization
    # - The output from the basic_cli.py tool
    # - Option 8 (View recent runs) in basic_cli.py

    sim_or_opt_id = input("Enter simulation or optimization ID: ").strip()
    if not sim_or_opt_id:
        print("Error: No ID provided.")
        return

    # -------------------------------------------------------------------------
    # Step 1.3: Determine if this is an optimization (vs simulation)
    # -------------------------------------------------------------------------
    # Optimizations have two mesh versions:
    #   - Original: The mesh before optimization
    #   - Optimized: The mesh after optimization (usually what you want)

    is_opt = input("Is this an optimization? [y/N]: ").strip().lower() == "y"

    use_optimized = True
    if is_opt:
        use_opt = input("Download optimized mesh (vs original)? [Y/n]: ").strip().lower()
        use_optimized = use_opt != "n"

    # -------------------------------------------------------------------------
    # Step 1.4: Choose output directory
    # -------------------------------------------------------------------------

    output_dir = input("Output directory [.]: ").strip() or "."
    os.makedirs(output_dir, exist_ok=True)

    # -------------------------------------------------------------------------
    # Step 1.5: Download the mesh
    # -------------------------------------------------------------------------
    # This function:
    # 1. Queries the API for the presigned download URL
    # 2. Downloads the Parquet file
    # 3. Converts it to CSV using pyarrow

    print("\nDownloading mesh...")
    try:
        csv_path = download_mesh_as_csv(
            client,
            sim_or_opt_id,
            output_dir,
            is_optimization=is_opt,
            use_optimized=use_optimized,
        )

        if csv_path:
            print(f"\nSuccess! Mesh saved to: {csv_path}")
            print()
            print("Next step: Run 02_visualize_mesh.py to create an interactive")
            print("3D visualization of your mesh.")
        else:
            print("\nError: Could not download mesh.")
            print("If you received a 404 error, contact Helio Additive to enable")
            print("mesh downloads for your account.")

    except Exception as e:
        print(f"\nError: {e}")
        print()
        print("Common issues:")
        print("  - 404 error: Enterprise feature not enabled for your account")
        print("  - Invalid ID: Check that the simulation/optimization exists")
        print("  - pyarrow not installed: pip install pyarrow")


if __name__ == "__main__":
    main()
