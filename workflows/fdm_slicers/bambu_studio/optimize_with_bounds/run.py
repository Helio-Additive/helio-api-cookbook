#!/usr/bin/env python3
"""Optimize a G-code file with custom velocity bounds.

Uploads a G-code file, runs an optimization with explicit velocity and layer
range settings, and downloads the optimized G-code.

Usage:
    export HELIO_PAT="your-token"
    python workflows/fdm_slicers/bambu_studio/optimize_with_bounds/run.py <gcode_file> <printer_id> <material_id>

Example:
    python workflows/fdm_slicers/bambu_studio/optimize_with_bounds/run.py model.gcode abc123 def456
"""

import os
import sys

# Walk up to find repo root (directory containing src/helio_api/)
_d = os.path.dirname(os.path.abspath(__file__))
while _d != os.path.dirname(_d):
    if os.path.isdir(os.path.join(_d, "src", "helio_api")):
        sys.path.insert(0, os.path.join(_d, "src"))
        break
    _d = os.path.dirname(_d)

from helio_api import (
    HelioClient,
    build_optimization_settings,
    compute_simulation_settings,
    download_file,
    load_pat_token,
    run_optimization,
    upload_and_register_gcode,
)


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <gcode_file> <printer_id> <material_id>")
        sys.exit(1)

    file_path, printer_id, material_id = sys.argv[1], sys.argv[2], sys.argv[3]
    client = HelioClient(load_pat_token())

    print("Uploading G-code...")
    gcode_id = upload_and_register_gcode(client, file_path, printer_id, material_id)

    # Customize these settings for your use case
    sim_settings = compute_simulation_settings(chamber_temp=35, bed_temp=60)
    opt_settings = build_optimization_settings(
        print_priority="QUALITY",
        min_velocity_mm=20,
        max_velocity_mm=300,
        from_layer=2,
        to_layer=-1,  # -1 = last layer
    )

    print("Running optimization...")
    opt_id, result, optimized_url = run_optimization(
        client, gcode_id, sim_settings, opt_settings
    )

    if optimized_url:
        out_path = os.path.splitext(file_path)[0] + "_optimized.gcode"
        download_file(optimized_url, out_path)
        print(f"Optimized G-code saved to {out_path}")


if __name__ == "__main__":
    main()
