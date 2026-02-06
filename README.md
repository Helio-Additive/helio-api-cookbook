# Helio API Cookbook

Workflow recipes and a Python library for the [Helio Additive](https://helioadditive.com) 3D print simulation and optimization API.

This is a community cookbook of portable workflow patterns — not an official SDK. Current recipes focus on FDM slicer workflows (tested with Bambu Studio) that carry over to other FDM slicers like OrcaSlicer and Creality Print.

## Quick Start

```bash
# Install
pip install -e .

# Set your Personal Access Token
export HELIO_PAT="your-token-here"

# Run a workflow
python workflows/fdm_slicers/bambu_studio/simulate_from_gcode/run.py model.gcode <printer_id> <material_id>
```

## Getting Started

### Most Users: Simulate or Optimize G-code

For typical BambuStudio users who want to simulate or optimize G-code:

```bash
# Simple interactive menu (options 1-8)
python examples/basic_cli.py
```

Or use the workflow scripts directly:

```bash
python workflows/fdm_slicers/bambu_studio/simulate_from_gcode/run.py model.gcode <printer_id> <material_id>
```

### Advanced Users: Thermal Analysis (Enterprise)

> **Note**: Thermal history and mesh downloads are enterprise features.
> Contact Helio Additive to discuss access: https://helioadditive.com
>
> These features are primarily used for R&D by materials scientists.

For thermal history exploration and analysis:

```bash
# Step-by-step educational scripts
python examples/advanced/01_download_mesh.py
python examples/advanced/02_visualize_mesh.py
python examples/advanced/03_download_thermal.py
python examples/advanced/04_plot_thermal.py
```

Or use the full interactive CLI with all options:

```bash
python examples/interactive_cli.py
```

See the [Advanced Guide](examples/advanced/README.md) for detailed instructions.

## Where to Start

- **Basic CLI**: `python examples/basic_cli.py` - Simple menu for simulation and optimization
- **Full CLI**: `python examples/interactive_cli.py` - All features including advanced thermal analysis
- **FDM slicer workflows**: [`workflows/fdm_slicers/bambu_studio/`](workflows/fdm_slicers/bambu_studio/)
- **Create your own**: Copy [`workflows/_template/`](workflows/_template/) into the appropriate domain folder

## Domains

This cookbook is organized into workflow domains:

| Domain | Status | Description |
|--------|--------|-------------|
| [FDM Slicers](workflows/fdm_slicers/) | Active | Simulation and optimization for FDM prints (Bambu Studio, OrcaSlicer, Creality Print) |
| [Large-Format Pellet](workflows/large_format_pellet/) | Planned | Pellet printer and large-format workflows |
| [Webapp Dashboard](workflows/webapp_dashboard/) | Planned | Dashboard and web application integrations |
| [Integrations](workflows/integrations/) | Planned | Third-party integrations (AdaOne/Adaxis) |

Current workflows are tested with Bambu Studio but the patterns are portable to other FDM slicers.

## Repository Structure

```
helio-api-cookbook/
├── src/helio_api/              # Python library for the Helio API
│   ├── client.py               # HelioClient class (GraphQL client)
│   ├── auth.py                 # PAT token loading
│   ├── queries.py              # GraphQL query/mutation constants
│   ├── catalog.py              # Printers, materials, quota
│   ├── upload.py               # G-code upload workflow
│   ├── simulate.py             # Simulation create/poll/results
│   ├── optimize.py             # Optimization create/poll/results
│   ├── download.py             # File downloads, thermal histories
│   ├── element.py              # Element lookup and thermal plotting
│   └── visualize.py            # 3D mesh visualization generator
├── examples/
│   ├── basic_cli.py            # Simple CLI (simulation/optimization)
│   ├── interactive_cli.py      # Full CLI (all features)
│   └── advanced/               # Step-by-step thermal analysis scripts
│       ├── README.md           # Guide for advanced features
│       ├── 01_download_mesh.py
│       ├── 02_visualize_mesh.py
│       ├── 03_download_thermal.py
│       └── 04_plot_thermal.py
├── workflows/                  # Portable workflow recipes by domain
│   ├── _template/              # Starter template for new workflows
│   ├── fdm_slicers/            # FDM slicer workflows
│   │   ├── bambu_studio/       # Tested with Bambu Studio
│   │   ├── orcaslicer/         # Patterns apply (stub)
│   │   └── creality_print/     # Patterns apply (stub)
│   ├── large_format_pellet/    # Planned
│   ├── webapp_dashboard/       # Planned
│   └── integrations/           # Third-party integrations
└── tests/                      # pytest test suite
```

## Workflows

| Workflow | Domain | Description |
|----------|--------|-------------|
| [simulate_from_gcode](workflows/fdm_slicers/bambu_studio/simulate_from_gcode/) | FDM Slicers | Upload G-code and run a thermal simulation |
| [optimize_with_bounds](workflows/fdm_slicers/bambu_studio/optimize_with_bounds/) | FDM Slicers | Optimize with custom velocity and layer bounds |

## Library Usage

```python
from helio_api import HelioClient, load_pat_token, run_simulation

client = HelioClient(load_pat_token())

# Upload and simulate
from helio_api import upload_and_register_gcode
gcode_id = upload_and_register_gcode(client, "model.gcode", printer_id, material_id)
sim_id, result, thermal_url = run_simulation(client, gcode_id)

# Optimize with custom settings
from helio_api import build_optimization_settings, compute_simulation_settings, run_optimization

sim_settings = compute_simulation_settings(chamber_temp=35, bed_temp=60)
opt_settings = build_optimization_settings(
    print_priority="QUALITY",
    min_velocity_mm=20,
    max_velocity_mm=300,
    from_layer=2,
    to_layer=-1,
)
opt_id, result, url = run_optimization(client, gcode_id, sim_settings, opt_settings)
```

## Interactive CLI

A full-featured interactive tool with printer/material browsing, upload, simulation, optimization, history, and thermal history downloads:

```bash
python examples/interactive_cli.py
```

## API Endpoints

| Region | Endpoint |
|--------|----------|
| Global | `https://api.helioadditive.com/graphql` |
| China  | `https://api.helioam.cn/graphql` |

Override the endpoint:

```bash
export HELIO_API_URL="https://api.helioam.cn/graphql"
```

Or pass it directly:

```python
client = HelioClient(pat_token, api_url="https://api.helioam.cn/graphql")
```

## Configuration

Set your PAT token using one of these methods:

1. **Environment variable** (recommended): `export HELIO_PAT="your-token"`
2. **Config file**: `echo "your-token" > ~/.helio_config`
3. **Interactive prompt**: The CLI will ask on startup

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/ examples/
```

## License

MIT
