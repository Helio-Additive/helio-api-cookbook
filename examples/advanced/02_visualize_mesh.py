#!/usr/bin/env python3
"""
STEP 2: Visualize the Mesh
==========================

This script generates an interactive 3D visualization of your mesh.
Open it in your browser to explore layers, see thermal quality colors,
and click on elements to find their index and layer number.

ENTERPRISE FEATURE: You need mesh data from step 1, which requires
enterprise access. Contact Helio Additive: https://helioadditive.com

What you'll learn:
    - Loading mesh CSV data
    - Generating HTML visualization with Three.js
    - Understanding thermal quality colors (blue=-1, green=0, red=+1)

Prerequisites:
    - Mesh CSV file from step 1 (01_download_mesh.py)

Usage:
    python examples/advanced/02_visualize_mesh.py
"""

import os
import sys
import webbrowser

# ============================================================================
# PATH SETUP
# ============================================================================

_repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.isdir(os.path.join(_repo_root, "src", "helio_api")):
    sys.path.insert(0, os.path.join(_repo_root, "src"))

# ============================================================================
# IMPORTS
# ============================================================================

from helio_api import generate_mesh_visualization  # noqa: E402

# ============================================================================
# MAIN WORKFLOW
# ============================================================================


def main():
    """
    Main workflow: Load mesh CSV, generate visualization, open in browser.
    """
    print("\n" + "=" * 60)
    print("STEP 2: Visualize the Mesh")
    print("=" * 60)
    print()
    print("This creates an interactive 3D visualization of your mesh.")
    print()
    print("In the visualization you can:")
    print("  - Drag to rotate the view")
    print("  - Scroll to zoom in/out")
    print("  - Shift+drag to pan")
    print("  - Use the layer slider to explore layer by layer")
    print("  - Click on elements to see their properties")
    print()
    print("IMPORTANT: Note the element INDEX and LAYER from the info panel")
    print("when you click an element. You'll need these for steps 3 and 4.")
    print()

    # -------------------------------------------------------------------------
    # Step 2.1: Get the mesh CSV file path
    # -------------------------------------------------------------------------
    # This should be the file created by step 1 (01_download_mesh.py)

    mesh_csv = input("Path to mesh CSV file: ").strip().strip("'\"")
    if not mesh_csv:
        print("Error: No file path provided.")
        return
    if not os.path.isfile(mesh_csv):
        print(f"Error: File not found: {mesh_csv}")
        return

    # -------------------------------------------------------------------------
    # Step 2.2: Set output path for the HTML file
    # -------------------------------------------------------------------------

    default_output = os.path.splitext(mesh_csv)[0] + "_visualization.html"
    output_html = input(f"Output HTML path [{default_output}]: ").strip() or default_output

    # -------------------------------------------------------------------------
    # Step 2.3: Optional title
    # -------------------------------------------------------------------------

    title = input("Visualization title [Mesh Visualization]: ").strip() or "Mesh Visualization"

    # -------------------------------------------------------------------------
    # Step 2.4: Generate the visualization
    # -------------------------------------------------------------------------
    # This function:
    # 1. Loads the mesh CSV
    # 2. Groups elements by layer and partition
    # 3. Generates HTML with embedded Three.js code
    # 4. Colors each element by its thermal quality score

    print("\nGenerating visualization...")
    try:
        success = generate_mesh_visualization(mesh_csv, output_html, title)

        if success:
            print(f"\nSuccess! Visualization saved to: {output_html}")
            print()

            # Offer to open in browser
            open_browser = input("Open in browser? [Y/n]: ").strip().lower()
            if open_browser != "n":
                webbrowser.open(f"file://{os.path.abspath(output_html)}")
                print("\nVisualization opened in browser.")

            print()
            print("=" * 60)
            print("WHAT TO DO IN THE VISUALIZATION")
            print("=" * 60)
            print()
            print("1. Use the LAYER SLIDER to explore different layers")
            print("2. Toggle between 'Cumulative' and 'Single' layer modes")
            print("3. CLICK on an element you're interested in")
            print("4. Note the INDEX and LAYER from the info panel")
            print()
            print("The colors represent thermal quality:")
            print("  - BLUE (-1): Too cold - cooled too quickly")
            print("  - GREEN (0): Ideal thermal conditions")
            print("  - RED (+1): Too hot - stayed hot too long")
            print()
            print("Next step: Run 03_download_thermal.py with the LAYER number")
            print("you noted, then 04_plot_thermal.py with the INDEX.")
        else:
            print("\nError: Could not generate visualization.")

    except Exception as e:
        print(f"\nError: {e}")


if __name__ == "__main__":
    main()
