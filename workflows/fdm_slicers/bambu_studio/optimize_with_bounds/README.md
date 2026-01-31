# Optimize with Custom Bounds

Upload a G-code file and run a Helio optimization with custom velocity bounds
and layer range.

## Usage

```bash
export HELIO_PAT="your-token"
python workflows/fdm_slicers/bambu_studio/optimize_with_bounds/run.py <gcode_file> <printer_id> <material_id>
```

## What it does

1. Uploads the G-code file to Helio via presigned S3 URL
2. Registers the G-code with the specified printer and material
3. Creates an optimization with custom settings:
   - Velocity range: 20-300 mm/s
   - Print priority: QUALITY
   - Layers: 2 to last
   - Temperature: 35C chamber, 60C bed
4. Polls until complete, displays quality improvement metrics
5. Downloads the optimized G-code

## Customizing

Edit `run.py` to change the velocity bounds, temperature settings, print
priority, or layer range. See `helio_api.build_optimization_settings()` for
all available parameters.
