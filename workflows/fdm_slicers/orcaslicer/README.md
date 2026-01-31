# OrcaSlicer Workflows

Placeholder for workflow recipes using [OrcaSlicer](https://github.com/SoftFever/OrcaSlicer) G-code.

## Status

No OrcaSlicer-specific workflows yet. The patterns in
[bambu_studio/](../bambu_studio/) apply directly since the Helio API works
with standard G-code from any FDM slicer.

## Getting Started

1. Slice your model in OrcaSlicer and export the `.gcode` file
2. Use any workflow from `../bambu_studio/` — they accept standard G-code
3. Find your printer and material IDs via `python examples/interactive_cli.py`

## Differences from Bambu Studio

- OrcaSlicer may produce slightly different G-code comments/metadata, but the
  Helio API parses standard G-code commands regardless of slicer.
- Temperature defaults may vary; use the optional chamber/bed temp overrides
  if auto-detection produces unexpected results.
