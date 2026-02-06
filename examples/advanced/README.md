# Advanced: Thermal History Analysis

> **Enterprise Feature**: Access to mesh and thermal history data requires
> Helio to enable this for your account. This is a paid enterprise feature
> primarily used for R&D by materials scientists.
>
> Contact Helio Additive to discuss access: https://helioadditive.com

This folder contains step-by-step scripts for thermal history analysis.
Run them in order to understand the data flow.

## Prerequisites

```bash
# Install with advanced dependencies
pip install -e ".[full]"
```

This installs:
- `pyarrow` - For converting Parquet files to CSV
- `matplotlib` - For plotting thermal curves

## The Workflow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  01: Download   │ ──> │  02: Visualize  │ ──> │  03: Download   │ ──> │  04: Plot       │
│      Mesh       │     │      Mesh       │     │  Thermal History│     │  Thermal Curve  │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
       │                        │                        │                        │
       v                        v                        v                        v
  mesh_optimized.csv    visualization.html   thermal_history_layer5.csv    plot.png
```

1. **Download Mesh** - Get element data (positions, quality scores) from your simulation
2. **Visualize** - See the 3D model in your browser, click elements to find their index and layer
3. **Download Thermal** - Get temperature-over-time data for a specific layer
4. **Plot** - Create temperature vs time graphs for specific elements

## Quick Reference

| Script | Input | Output |
|--------|-------|--------|
| `01_download_mesh.py` | simulation/optimization ID | `mesh_optimized.csv` |
| `02_visualize_mesh.py` | mesh CSV file | `mesh_optimized_visualization.html` |
| `03_download_thermal.py` | ID + layer number | `thermal_history_layer{N}.csv` |
| `04_plot_thermal.py` | thermal CSV + element index | plot (display or save) |

## Running the Scripts

```bash
# Step 1: Download mesh data
python examples/advanced/01_download_mesh.py

# Step 2: Generate visualization and open in browser
python examples/advanced/02_visualize_mesh.py

# Step 3: Download thermal history for a layer
python examples/advanced/03_download_thermal.py

# Step 4: Plot thermal curve for an element
python examples/advanced/04_plot_thermal.py
```

## Understanding the Data

### Mesh CSV Columns

| Column | Description |
|--------|-------------|
| `element_index` | Unique ID for each mesh element (use this to look up thermal data) |
| `layer` | Print layer number (0-indexed) |
| `partition` | Segment within the layer |
| `quality` | Thermal quality score: -1 (too cold) to +1 (too hot), 0 is ideal |
| `temperature` | Temperature at deposition (Kelvin) |
| `x1, y1, z1` | Position in meters |
| `t1` | Time when this element was printed (seconds) |

### Thermal History CSV Columns

| Column | Description |
|--------|-------------|
| `element_index` | Links to mesh data |
| `partition` | Segment within the layer |
| `datapoint 000-099` | 100 temperature readings (Kelvin) |
| `timestamp 000-099` | Time of each reading (seconds) |

### Thermal Quality Colors

In the visualization:
- **Blue** (-1): Element cooled too quickly (quality issues)
- **Green** (0): Ideal thermal conditions
- **Red** (+1): Element stayed too hot (quality issues)

## Tips

1. **Start with a completed simulation/optimization** - The mesh and thermal data are only available after processing completes.

2. **Note the layer number** - Thermal history files are per-layer. When you click an element in the visualization, it shows the layer number in the info panel.

3. **Element index is the key** - This unique number connects the mesh data to the thermal history. It's shown when you click an element in the visualization.

4. **Not all layers have data** - Thermal history may not be available for every layer. If you get a 404, try a different layer.

## Alternative: Unified Workflow

For a more streamlined experience, use option 13 in the full interactive CLI:

```bash
python examples/interactive_cli.py
# Select option 13: Thermal history exploration (unified)
```

This automates the mesh download, visualization, and thermal history workflow in one session.
