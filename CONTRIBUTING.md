# Contributing

Contributions are welcome! Here's how to get started.

## Setup

```bash
git clone https://github.com/Helio-Additive/helio-api-cookbook.git
cd helio-api-cookbook
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Development Workflow

1. Create a branch: `git checkout -b my-feature`
2. Make your changes
3. Run tests: `pytest`
4. Run linter: `ruff check src/ tests/ examples/`
5. Submit a pull request

## Code Style

- We use [ruff](https://docs.astral.sh/ruff/) for linting
- Line length: 100 characters
- Target: Python 3.10+

## Adding a Workflow

1. Copy the [`workflows/_template/`](workflows/_template/) directory into the
   appropriate **domain folder** (e.g. `workflows/fdm_slicers/bambu_studio/`)
2. Rename the directory and edit `run.py` with your workflow logic
3. Fill in **all** required sections of `README.md` (see template)
4. Optionally update `sample_config.yaml` with workflow-specific metadata
5. Import from the `helio_api` package — never from other workflows

```bash
cp -r workflows/_template workflows/fdm_slicers/bambu_studio/my_workflow
```

### Workflow Placement

Place workflows inside the correct domain folder:

| Domain | Path | When to use |
|--------|------|-------------|
| FDM Slicers | `workflows/fdm_slicers/<slicer>/` | Desktop FDM slicer workflows (Bambu Studio, OrcaSlicer, Creality Print) |
| Large-Format Pellet | `workflows/large_format_pellet/` | Pellet printer and large-format workflows |
| Webapp Dashboard | `workflows/webapp_dashboard/` | Web application and dashboard integrations |
| Integrations | `workflows/integrations/<tool>/` | Third-party tool integrations (AdaOne/Adaxis, etc.) |

### Required README Sections

Every workflow README must include:

- **Purpose** — What the workflow does
- **Applies to** — Domain and tool (e.g. "FDM Slicers / Bambu Studio")
- **Portability notes** — What changes when using a different slicer or tool
- **Inputs / Config** — Arguments, environment variables, config files
- **Side effects / cost notes** — API quota usage, file downloads, rate limits
- **How to run** — Exact command to run the workflow
- **Troubleshooting** — Common issues and solutions

### Creating a New Domain

To add an entirely new workflow domain:

1. Create a directory under `workflows/` (e.g. `workflows/my_domain/`)
2. Add a `README.md` with a brief description, status, and scope
3. Update `workflows/README.md` to list the new domain
4. Update the root `README.md` domains table

## Tests

- All tests use mocked HTTP responses — no API credentials needed
- **Tests must not hit the network.** Use the `responses` library to mock HTTP.
- Run with: `pytest -v`

## Security

- **No secrets in code or configs.** Never commit PAT tokens, API keys, or credentials.
- Sanitize log output in examples — redact tokens before printing.
- Provide `sample_config.yaml` files with empty placeholder values, not real data.
