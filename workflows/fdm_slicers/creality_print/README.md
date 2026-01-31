# Creality Print Workflows

Placeholder for workflow recipes using [Creality Print](https://www.creality.com/pages/download-software) G-code.

## Status

No Creality Print-specific workflows yet. The patterns in
[bambu_studio/](../bambu_studio/) apply directly since the Helio API works
with standard G-code from any FDM slicer.

## Getting Started

1. Slice your model in Creality Print and export the `.gcode` file
2. Use any workflow from `../bambu_studio/` — they accept standard G-code
3. Find your printer and material IDs via `python examples/interactive_cli.py`

## Differences from Bambu Studio

- Creality Print may use different G-code flavor settings; the Helio API
  handles standard G-code commands regardless.
- Temperature defaults may vary; use the optional chamber/bed temp overrides
  if needed.
