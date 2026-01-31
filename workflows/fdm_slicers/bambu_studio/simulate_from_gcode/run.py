#!/usr/bin/env python3
"""Simulate a G-code file with the Helio API.

Uploads a G-code file, runs a thermal simulation, and optionally downloads
the thermal index G-code.

Usage:
    export HELIO_PAT="your-token"
    python workflows/fdm_slicers/bambu_studio/simulate_from_gcode/run.py <gcode_file> <printer_id> <material_id>

Example:
    python workflows/fdm_slicers/bambu_studio/simulate_from_gcode/run.py model.gcode abc123 def456
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
    download_file,
    load_pat_token,
    run_simulation,
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

    print("Running simulation...")
    sim_id, result, thermal_url = run_simulation(client, gcode_id)

    if thermal_url:
        out_path = os.path.splitext(file_path)[0] + "_thermal_index.gcode"
        download_file(thermal_url, out_path)
        print(f"Thermal index G-code saved to {out_path}")


if __name__ == "__main__":
    main()
