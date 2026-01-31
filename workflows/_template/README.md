# [Workflow Name]

> Copy this template into the appropriate domain folder to create a new workflow.

## Purpose

Describe what this workflow does in 1-2 sentences.

## Applies to

- **Domain**: (e.g., fdm_slicers, large_format_pellet, webapp_dashboard, integrations)
- **Tool/Slicer**: (e.g., Bambu Studio, OrcaSlicer, Creality Print, any)

## Tested with

- (Optional) Specific software version or environment, e.g., "Bambu Studio v1.9"

## Portability notes

Describe what would need to change to use this workflow with a different slicer
or environment. For example: "Printer and material IDs are slicer-specific;
use the interactive CLI to find IDs for your setup."

## Inputs / Config

| Input | Description | Required |
|-------|-------------|----------|
| `gcode_file` | Path to the G-code file | Yes |
| `printer_id` | Helio printer ID | Yes |
| `material_id` | Helio material ID | Yes |

See `sample_config.yaml` for optional metadata fields.

## Side effects / cost notes

- Each simulation or optimization consumes quota from your Helio subscription.
- Uploaded G-code files are stored temporarily in Helio's cloud.
- Be mindful of rate limits (HTTP 429) if running many workflows in sequence.

## How to run

```bash
export HELIO_PAT="your-token"
python workflows/<domain>/<tool>/<this_workflow>/run.py <gcode_file> <printer_id> <material_id>
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `HTTP 401 Unauthorized` | Check your PAT token is valid and not expired |
| `HTTP 429 Rate Limited` | You have exceeded your quota; check with option 3 in the CLI |
| `File not found` | Ensure the G-code file path is correct; strip quotes from paths |
| Import errors | Run `pip install -e .` from the repo root first |
