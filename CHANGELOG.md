# Changelog

## 0.1.0 (Unreleased)

- Initial release
- Core `helio_api` Python package with `HelioClient` class
- Modules: auth, catalog, upload, simulate, optimize, download
- 14 GraphQL queries extracted from BambuStudio integration
- Interactive CLI (`examples/interactive_cli.py`)
- Workflow scripts: simulate_from_gcode, optimize_with_bounds
- pytest test suite with mocked HTTP
- CI via GitHub Actions (Python 3.10-3.12)
- Fix: simulation/optimization names from `generate_timestamped_name()` now carry milliseconds and a random suffix, so parallel runs no longer fail with "Optimization name already exists"
