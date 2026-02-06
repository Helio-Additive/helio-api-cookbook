"""
File download and thermal history functions for the Helio Additive API.

Handles downloading result files (optimized G-code, thermal index G-code)
and the enterprise thermal history Parquet-to-CSV workflow.
"""

from __future__ import annotations

import os

import requests

from helio_api.client import HelioClient, print_progress_bar
from helio_api.queries import (
    QUERY_THERMAL_HISTORIES,
    QUERY_SIMULATION_MESH,
    QUERY_OPTIMIZATION_MESH,
)

# Optional: pyarrow for Parquet-to-CSV conversion
try:
    import pyarrow.csv as pa_csv
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False


def download_file(url: str, output_path: str) -> None:
    """Download a file from a URL and save to disk.

    Args:
        url: The URL to download from.
        output_path: Local path to save the file.

    Raises:
        RuntimeError: If the server returns a 404 (file not found).
        requests.HTTPError: On other HTTP errors.
    """
    print(f"  Downloading to {output_path}...")
    resp = requests.get(url, stream=True, timeout=300)
    if resp.status_code == 404:
        raise RuntimeError(
            "File not found (404). The requested data may not be available "
            "for this simulation/optimization or layer number."
        )
    resp.raise_for_status()

    total = int(resp.headers.get("content-length", 0))
    downloaded = 0

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
            downloaded += len(chunk)
            if total > 0:
                print_progress_bar(downloaded / total * 100)

    if total > 0:
        print()
    print(f"  Downloaded: {output_path} ({downloaded:,} bytes)")


def get_thermal_histories_url(
    client: HelioClient, layer: int, is_optimized: bool, sim_or_opt_id: str
) -> str | None:
    """Fetch the thermal history Parquet file URL.

    The ``optimizationId`` parameter accepts both simulation and optimization IDs.
    Use ``is_optimized=False`` for simulation results, ``True`` for optimization results.

    Args:
        client: Helio API client.
        layer: Layer number to fetch thermal history for.
        is_optimized: Whether this is an optimized result.
        sim_or_opt_id: The simulation or optimization ID.

    Returns:
        The presigned download URL, or ``None`` if unavailable.

    Raises:
        RuntimeError: On API error.
    """
    variables = {
        "isOptimized": is_optimized,
        "layer": layer,
        "optimizationId": sim_or_opt_id,
    }
    data, errors, trace_id = client.query(QUERY_THERMAL_HISTORIES, variables)
    if errors:
        raise RuntimeError(f"ThermalHistories error: {'; '.join(errors)} (trace: {trace_id})")
    th = data.get("thermalHistories")
    if not th:
        raise RuntimeError("No thermal histories data returned.")
    return th.get("url")


def convert_parquet_to_csv(parquet_path: str, csv_path: str) -> bool:
    """Convert a Parquet file to CSV using pyarrow (no pandas needed).

    Args:
        parquet_path: Path to the input Parquet file.
        csv_path: Path to write the output CSV file.

    Returns:
        ``True`` if conversion succeeded, ``False`` if pyarrow is not installed.
    """
    if not HAS_PYARROW:
        print("  Warning: pyarrow not installed. Cannot convert Parquet to CSV.")
        print("  Install with: pip install pyarrow")
        return False

    table = pq.read_table(parquet_path)
    pa_csv.write_csv(table, csv_path)
    print(f"  Converted to CSV: {csv_path}")
    return True


def download_thermal_history_as_csv(
    client: HelioClient,
    layer: int,
    is_optimized: bool,
    sim_or_opt_id: str,
    output_dir: str = ".",
) -> None:
    """Full workflow: fetch URL -> download Parquet -> convert to CSV.

    This is an enterprise feature that requires Helio to enable thermal
    histories for your account. Contact Helio Additive if downloads
    return 404 errors.

    Args:
        client: Helio API client.
        layer: Layer number.
        is_optimized: Whether this is an optimized result.
        sim_or_opt_id: The simulation or optimization ID.
        output_dir: Directory to save output files.
    """
    print(f"  Fetching thermal history URL (layer={layer}, optimized={is_optimized})...")
    url = get_thermal_histories_url(client, layer, is_optimized, sim_or_opt_id)
    if not url:
        print("  No thermal history URL available.")
        return
    # Debug: print full URL path (before query params)
    url_path = url.split("?")[0] if "?" in url else url
    print(f"  URL path: {url_path}")

    parquet_path = os.path.join(output_dir, f"thermal_history_layer{layer}.parquet")
    csv_path = os.path.join(output_dir, f"thermal_history_layer{layer}.csv")

    try:
        download_file(url, parquet_path)
    except RuntimeError as e:
        if "404" in str(e):
            print(f"  Thermal history data not found for layer {layer}.")
            print("  Possible causes:")
            print("    - Layer number may not have thermal history data")
            print("    - Try a different layer number (layers are 0-indexed)")
            print("    - Enterprise feature may not be enabled for this account")
            print(f"  URL attempted: {url[:100]}...")
            return
        raise

    if HAS_PYARROW:
        convert_parquet_to_csv(parquet_path, csv_path)
    else:
        print("  Parquet file saved. Install pyarrow to convert to CSV.")


def get_simulation_mesh_url(client: HelioClient, sim_id: str) -> str | None:
    """Fetch the mesh Parquet file URL from a simulation.

    Args:
        client: Helio API client.
        sim_id: The simulation ID.

    Returns:
        The presigned download URL, or ``None`` if unavailable.

    Raises:
        RuntimeError: On API error.
    """
    data, errors, trace_id = client.query(QUERY_SIMULATION_MESH, {"id": sim_id})
    if errors:
        raise RuntimeError(f"SimulationMesh error: {'; '.join(errors)} (trace: {trace_id})")
    simulation = data.get("simulation")
    if not simulation:
        raise RuntimeError(f"Simulation not found: {sim_id}")
    mesh_url = simulation.get("meshUrl")
    if not mesh_url:
        return None
    return mesh_url.get("url")


def get_optimization_mesh_url(
    client: HelioClient, opt_id: str, use_optimized: bool = True
) -> str | None:
    """Fetch the mesh Parquet file URL from an optimization.

    Args:
        client: Helio API client.
        opt_id: The optimization ID.
        use_optimized: If True, return the optimized mesh URL.
            If False, return the original (pre-optimization) mesh URL.

    Returns:
        The presigned download URL, or ``None`` if unavailable.

    Raises:
        RuntimeError: On API error.
    """
    data, errors, trace_id = client.query(QUERY_OPTIMIZATION_MESH, {"id": opt_id})
    if errors:
        raise RuntimeError(f"OptimizationMesh error: {'; '.join(errors)} (trace: {trace_id})")
    optimization = data.get("optimization")
    if not optimization:
        raise RuntimeError(f"Optimization not found: {opt_id}")

    if use_optimized:
        mesh_asset = optimization.get("optimizedMeshAsset")
    else:
        mesh_asset = optimization.get("originalMeshAsset")

    if not mesh_asset:
        return None
    return mesh_asset.get("url")


def download_mesh_as_csv(
    client: HelioClient,
    sim_or_opt_id: str,
    output_dir: str = ".",
    is_optimization: bool = False,
    use_optimized: bool = True,
) -> str | None:
    """Full workflow: fetch mesh URL -> download Parquet -> convert to CSV.

    This is an enterprise feature that requires Helio to enable mesh downloads
    for your account. Contact Helio Additive if downloads return 404 errors.

    Args:
        client: Helio API client.
        sim_or_opt_id: The simulation or optimization ID.
        output_dir: Directory to save output files.
        is_optimization: If True, fetch mesh from optimization.
            If False, fetch mesh from simulation.
        use_optimized: For optimizations only - if True, download the optimized mesh.
            If False, download the original (pre-optimization) mesh.

    Returns:
        Path to the CSV file on success, or ``None`` on failure.
    """
    mesh_type = "optimized" if (is_optimization and use_optimized) else "original"
    print(f"  Fetching mesh URL ({mesh_type})...")

    if is_optimization:
        url = get_optimization_mesh_url(client, sim_or_opt_id, use_optimized)
    else:
        url = get_simulation_mesh_url(client, sim_or_opt_id)

    if not url:
        print("  No mesh URL available.")
        return None

    parquet_path = os.path.join(output_dir, f"mesh_{mesh_type}.parquet")
    csv_path = os.path.join(output_dir, f"mesh_{mesh_type}.csv")

    try:
        download_file(url, parquet_path)
    except RuntimeError as e:
        if "404" in str(e):
            print("  Mesh data is not available.")
            print("  This feature requires Helio to enable mesh downloads for")
            print("  your account. Contact Helio Additive to enable this feature.")
            return None
        raise

    if HAS_PYARROW:
        convert_parquet_to_csv(parquet_path, csv_path)
        return csv_path
    else:
        print("  Parquet file saved. Install pyarrow to convert to CSV.")
        return parquet_path
