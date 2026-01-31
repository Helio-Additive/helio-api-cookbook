# AI Agent Instructions

Instructions for AI agents working with this repository.

## Repository Overview

This is `helio-api-cookbook` — a **community cookbook** of portable workflow
patterns and a Python library for the Helio Additive 3D print simulation and
optimization GraphQL API. This is **not** an official SDK; it's a collection of
recipes that demonstrate how to use the Helio API from Python.

## Structure

- `src/helio_api/` — Core Python package (installable via pip)
- `examples/interactive_cli.py` — Full interactive menu-driven CLI
- `workflows/` — Portable workflow recipes organized by **domain**
  - `_template/` — Starter template for new workflows
  - `fdm_slicers/` — FDM slicer workflows (Bambu Studio, OrcaSlicer, Creality Print)
  - `large_format_pellet/` — Large-format pellet printer workflows (planned)
  - `webapp_dashboard/` — Web application integrations (planned)
  - `integrations/` — Third-party tool integrations (planned)
- `tests/` — pytest test suite

## Key Patterns

### HelioClient

All API calls go through `HelioClient`, which wraps authentication and GraphQL
request handling:

```python
from helio_api import HelioClient, load_pat_token
client = HelioClient(load_pat_token())
data, errors, trace_id = client.query(SOME_QUERY, {"var": "value"})
```

### Module Dependencies

```
queries.py  auth.py  client.py    (leaf nodes, no intra-package imports)
catalog.py  upload.py  simulate.py  optimize.py  download.py  (depend on client + queries)
__init__.py  (re-exports from all modules)
```

No circular dependencies. Domain modules never import from each other.

### API URLs

- Global: `https://api.helioadditive.com/graphql`
- China: `https://api.helioam.cn/graphql`
- URL selection: explicit arg > `HELIO_API_URL` env var > global default

### Important Constraints

- The optimizer is always `HYBRID` — never change this
- `fromLayer` is always clamped to min 2 (per BambuStudio behavior)
- `fileName` for presigned URLs is always `"test.gcode"`
- `isSingleShell` is always `True` in createGcodeV2
- Residual strategy is always `LINEAR`

## Portability-First Design

Slicer-specific logic belongs in **workflow scripts**, not in the core library.
The `src/helio_api/` package handles API communication and is slicer-agnostic.
Workflow scripts under `workflows/` contain slicer-specific defaults, G-code
conventions, and parameter choices.

When adding or modifying workflows:
- Keep API calls in `src/helio_api/` modules
- Keep slicer-specific logic in the workflow `run.py`
- Document portability in the workflow README
- If a pattern works across slicers, note it; if it's slicer-specific, explain why

## Development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src/ tests/ examples/
```

## Testing

- `tests/test_client.py` — Mocked HTTP tests for HelioClient (uses `responses` library)
- `tests/test_workflow_smoke.py` — Import checks and pure function tests
- No tests require API credentials; all HTTP is mocked
- **Tests must never hit the network.** Always mock with `responses`.

## Adding a New Workflow

1. Copy `workflows/_template/` into the correct **domain folder**
   (e.g. `workflows/fdm_slicers/bambu_studio/my_workflow/`)
2. Edit `run.py` with your workflow logic — import from `helio_api`, not other workflows
3. Fill in all required README sections (see template)
4. The `run.py` uses a robust `sys.path` setup that walks up to find `src/helio_api/`

## Adding a New Domain

1. Create a directory under `workflows/` (e.g. `workflows/my_domain/`)
2. Add a `README.md` with description, status, and scope
3. Update `workflows/README.md` and root `README.md` domain tables
4. Keep documentation consistent across domains

## Adding a New API Function

1. Add the GraphQL query to `src/helio_api/queries.py`
2. Create the function in the appropriate domain module
3. Re-export from `src/helio_api/__init__.py`
4. Add tests to `tests/`
