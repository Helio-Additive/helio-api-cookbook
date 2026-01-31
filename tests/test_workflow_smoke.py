"""Smoke tests for module imports and pure functions."""


def test_import_helio_api():
    """Top-level package imports successfully."""
    import helio_api

    assert hasattr(helio_api, "HelioClient")
    assert hasattr(helio_api, "load_pat_token")
    assert hasattr(helio_api, "run_simulation")
    assert hasattr(helio_api, "run_optimization")


def test_import_all_modules():
    """All submodules are importable."""
    from helio_api import (  # noqa: F401
        auth,
        catalog,
        client,
        download,
        optimize,
        queries,
        simulate,
        upload,
    )


def test_compute_simulation_settings_with_temps():
    """compute_simulation_settings converts temperatures correctly."""
    from helio_api.simulate import compute_simulation_settings

    settings = compute_simulation_settings(chamber_temp=40, bed_temp=80)
    assert "stabilizedAirTemperature" in settings
    # 40 + 273.15 = 313.15
    assert abs(settings["stabilizedAirTemperature"] - 313.15) < 0.01
    # (40 + 80) / 2 + 273.15 = 333.15
    assert abs(settings["airTemperatureAboveBuildPlate"] - 333.15) < 0.01


def test_compute_simulation_settings_no_temps():
    """compute_simulation_settings with no temps returns minimal settings."""
    from helio_api.simulate import compute_simulation_settings

    settings = compute_simulation_settings()
    assert "temperatureStabilizationHeight" in settings
    assert "stabilizedAirTemperature" not in settings


def test_build_optimization_settings_basic():
    """build_optimization_settings sets HYBRID optimizer and converts units."""
    from helio_api.optimize import build_optimization_settings

    settings = build_optimization_settings(
        min_velocity_mm=20,
        max_velocity_mm=300,
        from_layer=2,
        to_layer=100,
    )
    assert settings["optimizer"] == "HYBRID"
    assert settings["residualStrategySettings"] == {"strategy": "LINEAR"}
    assert settings["minVelocity"] == 0.02
    assert settings["maxVelocity"] == 0.3
    assert settings["layersToOptimize"] == [{"fromLayer": 2, "toLayer": 100}]


def test_build_optimization_settings_clamps_from_layer():
    """fromLayer is clamped to minimum 2."""
    from helio_api.optimize import build_optimization_settings

    settings = build_optimization_settings(from_layer=1, to_layer=-1)
    assert settings["layersToOptimize"] == [{"fromLayer": 2, "toLayer": -1}]


def test_build_optimization_settings_with_priority():
    """Print priority is included in settings."""
    from helio_api.optimize import build_optimization_settings

    settings = build_optimization_settings(print_priority="QUALITY")
    assert settings["printPriority"] == "QUALITY"
    assert settings["optimizer"] == "HYBRID"


def test_convert_units():
    """Unit conversion functions produce correct results."""
    from helio_api.optimize import convert_speed_mm_to_m, convert_volumetric_mm3_to_m3

    assert convert_speed_mm_to_m(1000) == 1.0
    assert convert_speed_mm_to_m(5) == 0.005
    assert convert_volumetric_mm3_to_m3(1e9) == 1.0


def test_queries_are_strings():
    """GraphQL query constants are non-empty strings."""
    from helio_api import queries

    assert isinstance(queries.QUERY_PRESIGNED_URL, str)
    assert "getPresignedUrl" in queries.QUERY_PRESIGNED_URL
    assert isinstance(queries.MUTATION_CREATE_SIMULATION, str)
    assert "CreateSimulation" in queries.MUTATION_CREATE_SIMULATION
    assert isinstance(queries.MUTATION_CREATE_OPTIMIZATION, str)
    assert "CreateOptimization" in queries.MUTATION_CREATE_OPTIMIZATION
    assert isinstance(queries.QUERY_THERMAL_HISTORIES, str)


def test_api_url_constants():
    """API URL constants point to correct endpoints."""
    from helio_api.client import API_URL_CHINA, API_URL_GLOBAL

    assert "api.helioadditive.com" in API_URL_GLOBAL
    assert "api.helioam.cn" in API_URL_CHINA
