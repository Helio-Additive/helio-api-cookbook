# Bambu Studio Workflows

Workflow recipes tested with [Bambu Studio](https://bambulab.com/en/download/studio) G-code output.

## Available Workflows

| Workflow | Description |
|----------|-------------|
| [simulate_from_gcode](simulate_from_gcode/) | Upload G-code and run a thermal simulation |
| [optimize_with_bounds](optimize_with_bounds/) | Optimize with custom velocity bounds and layer range |

## Notes

- These workflows use G-code sliced by Bambu Studio but the Helio API accepts
  standard G-code from any FDM slicer.
- Printer/material IDs come from the Helio catalog. Use the interactive CLI
  (`python examples/interactive_cli.py`) to browse and find IDs for your setup.
- The GraphQL queries in `src/helio_api/queries.py` were originally extracted
  from Bambu Studio's Helio integration (`HelioDragon.cpp`).
