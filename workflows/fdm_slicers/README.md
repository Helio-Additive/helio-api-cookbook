# FDM Slicers

Workflow recipes for FDM (Fused Deposition Modeling) 3D print simulation and optimization.

## Slicer-Specific Folders

| Slicer | Status | Description |
|--------|--------|-------------|
| [bambu_studio](bambu_studio/) | Active | Workflows tested with Bambu Studio G-code |
| [orcaslicer](orcaslicer/) | Planned | Patterns apply; see notes on differences |
| [creality_print](creality_print/) | Planned | Patterns apply; see notes on differences |

## Portability

The Helio API works with standard G-code from any FDM slicer. The workflow
patterns in `bambu_studio/` are generally portable:

- **Printer and material IDs** are Helio catalog entries, not slicer-specific.
  Use `python examples/interactive_cli.py` (options 1 and 2) to browse available IDs.
- **G-code upload** works with any standard `.gcode` file.
- **Temperature settings** may differ between slicers; adjust chamber/bed temp
  overrides as needed.

Slicer-specific behavior (like default temperature extraction) is handled by
the Helio API server, not by these workflow scripts.
