# Simulate from G-code

Upload a G-code file and run a Helio thermal simulation.

## Usage

```bash
export HELIO_PAT="your-token"
python workflows/fdm_slicers/bambu_studio/simulate_from_gcode/run.py <gcode_file> <printer_id> <material_id>
```

## What it does

1. Uploads the G-code file to Helio via presigned S3 URL
2. Registers the G-code with the specified printer and material
3. Creates a simulation and polls until complete
4. Displays results (print outcome, temperature direction, suggested fixes)
5. Downloads the thermal index G-code if available

## Finding printer and material IDs

Use the interactive CLI to browse available printers and materials:

```bash
python examples/interactive_cli.py
# Select option 1 (printers) or 2 (materials) to see IDs
```
