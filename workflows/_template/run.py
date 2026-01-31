#!/usr/bin/env python3
"""[Workflow Name] - Brief description.

Copy this template into the appropriate domain folder and customize.

Usage:
    export HELIO_PAT="your-token"
    python workflows/<domain>/<tool>/<workflow>/run.py <gcode_file> <printer_id> <material_id>
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

from helio_api import (  # noqa: E402
    HelioClient,
    load_pat_token,
    upload_and_register_gcode,
    # Add imports for your workflow:
    # run_simulation, run_optimization, download_file,
    # compute_simulation_settings, build_optimization_settings,
)


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <gcode_file> <printer_id> <material_id>")
        sys.exit(1)

    file_path, printer_id, material_id = sys.argv[1], sys.argv[2], sys.argv[3]
    client = HelioClient(load_pat_token())

    # Step 1: Upload G-code
    print("Uploading G-code...")
    gcode_id = upload_and_register_gcode(client, file_path, printer_id, material_id)

    # Step 2: Add your workflow logic here
    # Example: run_simulation(client, gcode_id)
    # Example: run_optimization(client, gcode_id, sim_settings, opt_settings)
    print(f"G-code registered: {gcode_id}")
    print("TODO: Add workflow logic")


if __name__ == "__main__":
    main()
