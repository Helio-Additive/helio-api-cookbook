"""
Helio API Cookbook - Python library for the Helio Additive GraphQL API.

Quick start::

    from helio_api import HelioClient, load_pat_token

    client = HelioClient(load_pat_token())
"""

from helio_api.auth import load_pat_token
from helio_api.catalog import (
    check_user_quota,
    get_default_optimization_settings,
    get_print_priority_options,
    get_recent_runs,
    list_materials,
    list_printers,
)
from helio_api.client import (
    API_URL_CHINA,
    API_URL_GLOBAL,
    HelioClient,
    generate_timestamped_name,
    print_progress_bar,
)
from helio_api.download import (
    HAS_PYARROW,
    convert_parquet_to_csv,
    download_file,
    download_mesh_as_csv,
    download_thermal_history_as_csv,
    get_optimization_mesh_url,
    get_simulation_mesh_url,
    get_thermal_histories_url,
)
from helio_api.element import (
    HAS_MATPLOTLIB,
    export_thermal_data_csv,
    extract_thermal_data,
    get_element_by_index,
    get_element_thermal_history,
    get_elements_by_layer,
    get_layer_count,
    load_mesh_csv,
    load_thermal_history_csv,
    plot_element_thermal_history,
    print_element_info,
)
from helio_api.optimize import (
    build_optimization_settings,
    convert_speed_mm_to_m,
    convert_volumetric_mm3_to_m3,
    create_optimization,
    poll_optimization,
    run_optimization,
)
from helio_api.simulate import (
    compute_simulation_settings,
    create_simulation,
    poll_simulation,
    run_simulation,
)
from helio_api.upload import (
    get_presigned_url,
    register_gcode,
    upload_and_register_gcode,
    upload_file,
)
from helio_api.visualize import generate_mesh_visualization

__all__ = [
    # Client
    "HelioClient",
    "API_URL_GLOBAL",
    "API_URL_CHINA",
    # Auth
    "load_pat_token",
    # Catalog
    "list_printers",
    "list_materials",
    "get_print_priority_options",
    "check_user_quota",
    "get_default_optimization_settings",
    "get_recent_runs",
    # Upload
    "get_presigned_url",
    "upload_file",
    "register_gcode",
    "upload_and_register_gcode",
    # Simulate
    "compute_simulation_settings",
    "create_simulation",
    "poll_simulation",
    "run_simulation",
    # Optimize
    "convert_speed_mm_to_m",
    "convert_volumetric_mm3_to_m3",
    "build_optimization_settings",
    "create_optimization",
    "poll_optimization",
    "run_optimization",
    # Download
    "download_file",
    "get_thermal_histories_url",
    "convert_parquet_to_csv",
    "download_thermal_history_as_csv",
    "get_simulation_mesh_url",
    "get_optimization_mesh_url",
    "download_mesh_as_csv",
    # Element lookup
    "load_mesh_csv",
    "get_element_by_index",
    "get_elements_by_layer",
    "get_layer_count",
    "load_thermal_history_csv",
    "get_element_thermal_history",
    "extract_thermal_data",
    "plot_element_thermal_history",
    "print_element_info",
    "export_thermal_data_csv",
    "HAS_MATPLOTLIB",
    "HAS_PYARROW",
    # Visualization
    "generate_mesh_visualization",
    # Utils
    "print_progress_bar",
    "generate_timestamped_name",
]
