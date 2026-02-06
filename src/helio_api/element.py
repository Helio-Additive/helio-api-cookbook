"""
Element lookup and thermal history analysis functions for the Helio Additive API.

Provides utilities for loading mesh data, finding specific elements,
loading thermal history data, and plotting temperature vs time curves.
"""

from __future__ import annotations

import csv
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any

# Optional: matplotlib for plotting
try:
    import matplotlib.pyplot as plt

    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


def load_mesh_csv(csv_path: str) -> list[dict[str, Any]]:
    """Load mesh CSV into a list of element dictionaries.

    Expected CSV columns: index, partition, layer, event, temperature,
    fan_speed, height, width, environment_temperature, y1, t1, z1, x1, quality

    Args:
        csv_path: Path to the mesh CSV file.

    Returns:
        List of element dictionaries, each containing all mesh properties.
        Returns empty list if file not found or on error.
    """
    if not os.path.isfile(csv_path):
        print(f"  Error: File not found: {csv_path}")
        return []

    elements = []
    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Handle both 'index' and 'element_index' column names
                idx_val = row.get("index") or row.get("element_index")

                # Skip rows with missing index (header rows or empty rows)
                if not idx_val or idx_val == "":
                    continue

                element = {
                    "index": int(idx_val) if idx_val else None,
                    "partition": int(row["partition"]) if row.get("partition") else None,
                    "layer": int(row["layer"]) if row.get("layer") else None,
                    "event": int(row["event"]) if row.get("event") else None,
                    "temperature": float(row["temperature"]) if row.get("temperature") else None,
                    "fan_speed": float(row["fan_speed"]) if row.get("fan_speed") else None,
                    "height": float(row["height"]) if row.get("height") else None,
                    "width": float(row["width"]) if row.get("width") else None,
                    "environment_temperature": (
                        float(row["environment_temperature"])
                        if row.get("environment_temperature")
                        else None
                    ),
                    "x1": float(row["x1"]) if row.get("x1") else None,
                    "y1": float(row["y1"]) if row.get("y1") else None,
                    "z1": float(row["z1"]) if row.get("z1") else None,
                    "t1": float(row["t1"]) if row.get("t1") else None,
                    "quality": float(row["quality"]) if row.get("quality") else None,
                }
                if element["index"] is not None:
                    elements.append(element)
    except Exception as e:
        print(f"  Error loading mesh CSV: {e}")
        return []

    return elements


def get_element_by_index(mesh_data: list[dict], element_index: int) -> dict | None:
    """Find an element by its index in the mesh data.

    Args:
        mesh_data: List of element dictionaries from load_mesh_csv().
        element_index: The element index to find.

    Returns:
        The element dictionary, or None if not found.
    """
    for element in mesh_data:
        if element.get("index") == element_index:
            return element
    return None


def get_elements_by_layer(mesh_data: list[dict], layer: int) -> list[dict]:
    """Filter mesh data to elements in a specific layer.

    Args:
        mesh_data: List of element dictionaries from load_mesh_csv().
        layer: The layer number to filter by.

    Returns:
        List of element dictionaries in the specified layer.
    """
    return [e for e in mesh_data if e.get("layer") == layer]


def get_layer_count(mesh_data: list[dict]) -> int:
    """Get the maximum layer number in the mesh data.

    Args:
        mesh_data: List of element dictionaries from load_mesh_csv().

    Returns:
        Maximum layer number (0-indexed), or -1 if no data.
    """
    if not mesh_data:
        return -1
    layers = [e.get("layer", 0) for e in mesh_data if e.get("layer") is not None]
    return max(layers) if layers else -1


def load_thermal_history_csv(csv_path: str) -> list[dict[str, Any]]:
    """Load thermal history CSV into a list of element thermal histories.

    Expected CSV structure:
    - Columns: datapoint 000-099, element_index, partition, timestamp 000-099

    Args:
        csv_path: Path to the thermal history CSV file.

    Returns:
        List of dictionaries, each containing:
        - element_index: int
        - partition: int
        - temperatures: list of 100 temperature values
        - timestamps: list of 100 timestamp values
        Returns empty list if file not found or on error.
    """
    if not os.path.isfile(csv_path):
        print(f"  Error: File not found: {csv_path}")
        return []

    histories = []
    try:
        with open(csv_path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Skip rows with missing element_index
                if not row.get("element_index") or row.get("element_index") == "":
                    continue

                # Parse temperatures (datapoint 000 through datapoint 099)
                temperatures = []
                for i in range(100):
                    col_name = f"datapoint {i:03d}"
                    val = row.get(col_name)
                    if val and val != "":
                        temperatures.append(float(val))
                    else:
                        temperatures.append(None)

                # Parse timestamps (timestamp 000 through timestamp 099)
                timestamps = []
                for i in range(100):
                    col_name = f"timestamp {i:03d}"
                    val = row.get(col_name)
                    if val and val != "":
                        timestamps.append(float(val))
                    else:
                        timestamps.append(None)

                history = {
                    "element_index": int(row["element_index"]),
                    "partition": int(row["partition"]) if row.get("partition") else None,
                    "temperatures": temperatures,
                    "timestamps": timestamps,
                }
                histories.append(history)
    except Exception as e:
        print(f"  Error loading thermal history CSV: {e}")
        return []

    return histories


def get_element_thermal_history(
    thermal_data: list[dict], element_index: int
) -> dict | None:
    """Find thermal history for a specific element index.

    Args:
        thermal_data: List of thermal history dictionaries from load_thermal_history_csv().
        element_index: The element index to find.

    Returns:
        The thermal history dictionary, or None if not found.
    """
    for history in thermal_data:
        if history.get("element_index") == element_index:
            return history
    return None


def extract_thermal_data(
    thermal_history: dict,
) -> tuple[list[float], list[float]]:
    """Extract plottable timestamps and temperatures from thermal history.

    Filters out None values and ensures both lists have matching lengths.

    Args:
        thermal_history: Thermal history dictionary from get_element_thermal_history().

    Returns:
        Tuple of (timestamps, temperatures) lists ready for plotting.
    """
    timestamps = thermal_history.get("timestamps", [])
    temperatures = thermal_history.get("temperatures", [])

    # Filter out None values, keeping only valid pairs
    valid_data = [
        (t, temp)
        for t, temp in zip(timestamps, temperatures)
        if t is not None and temp is not None
    ]

    if not valid_data:
        return [], []

    filtered_timestamps, filtered_temps = zip(*valid_data)
    return list(filtered_timestamps), list(filtered_temps)


def plot_element_thermal_history(
    elements_data: list[tuple[int, list[float], list[float]]],
    output_path: str | None = None,
    title: str | None = None,
) -> bool:
    """Plot temperature vs time for one or multiple elements.

    Args:
        elements_data: List of tuples, each containing:
            (element_index, timestamps, temperatures)
        output_path: If provided, save plot to this path (PNG, PDF, etc.).
            If None, display interactive plot.
        title: Optional custom title for the plot.

    Returns:
        True on success, False if matplotlib is not available.
    """
    if not HAS_MATPLOTLIB:
        print("  Error: matplotlib is not installed.")
        print("  Install with: pip install matplotlib")
        return False

    if not elements_data:
        print("  Error: No data to plot.")
        return False

    fig, ax = plt.subplots(figsize=(10, 6))

    for element_index, timestamps, temperatures in elements_data:
        label = f"Element {element_index}"
        ax.plot(timestamps, temperatures, label=label, linewidth=1.5)

    ax.set_xlabel("Time (s)", fontsize=11)
    ax.set_ylabel("Temperature (K)", fontsize=11)

    if title:
        ax.set_title(title, fontsize=12)
    elif len(elements_data) == 1:
        ax.set_title(f"Thermal History - Element {elements_data[0][0]}", fontsize=12)
    else:
        ax.set_title("Thermal History Comparison", fontsize=12)

    ax.grid(True, alpha=0.3)
    ax.legend(loc="best")

    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=150)
        print(f"  Plot saved to: {output_path}")
        plt.close(fig)
    else:
        plt.show()

    return True


def print_element_info(element: dict) -> None:
    """Print formatted element information.

    Args:
        element: Element dictionary from get_element_by_index().
    """
    print(f"\n  Element {element.get('index')}:")
    print(f"    Layer:       {element.get('layer')}")
    print(f"    Partition:   {element.get('partition')}")
    print(f"    Event:       {element.get('event')}")
    print(f"    Temperature: {element.get('temperature')} K")
    print(f"    Env Temp:    {element.get('environment_temperature')} K")
    print(f"    Fan Speed:   {element.get('fan_speed')}")
    print(f"    Height:      {element.get('height')} m")
    print(f"    Width:       {element.get('width')} m")
    print(f"    Position:    ({element.get('x1')}, {element.get('y1')}, {element.get('z1')}) m")
    print(f"    Time:        {element.get('t1')} s")
    print(f"    Quality:     {element.get('quality')}")


def export_thermal_data_csv(
    elements_data: list[tuple[int, list[float], list[float]]],
    output_path: str,
) -> bool:
    """Export thermal history data to CSV.

    Creates a CSV with one row per data point, suitable for further analysis
    in spreadsheet software or data analysis tools.

    Args:
        elements_data: List of tuples, each containing:
            (element_index, timestamps, temperatures)
        output_path: Path for the output CSV file.

    Returns:
        True on success, False on error.

    Output CSV format:
        element_index, timestamp_s, temperature_K
        5119, 0.0, 485.2
        5119, 0.1, 480.1
        ...
    """
    try:
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["element_index", "timestamp_s", "temperature_K"])
            for elem_idx, timestamps, temps in elements_data:
                for t, temp in zip(timestamps, temps):
                    writer.writerow([elem_idx, t, temp])
        print(f"  Exported thermal data to: {output_path}")
        return True
    except Exception as e:
        print(f"  Error exporting CSV: {e}")
        return False
