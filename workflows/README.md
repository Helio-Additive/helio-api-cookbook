# Workflows

Cookbook of workflow recipes for the Helio Additive API, organized by domain.

## Domains

| Domain | Status | Description |
|--------|--------|-------------|
| [fdm_slicers/](fdm_slicers/) | Active | FDM print simulation and optimization (Bambu Studio, OrcaSlicer, Creality Print) |
| [large_format_pellet/](large_format_pellet/) | Planned | Large-format pellet printer workflows |
| [webapp_dashboard/](webapp_dashboard/) | Planned | Web application and dashboard integrations |
| [integrations/](integrations/) | Planned | Third-party tool integrations (AdaOne/Adaxis) |

## Portability

These recipes are patterns. The Helio API accepts standard G-code from any
FDM slicer, so workflows tested with one slicer generally work with others.
Slicer-specific steps (like temperature defaults or G-code flavor) may vary —
see each workflow's portability notes.

## Creating a New Workflow

1. Copy the [`_template/`](_template/) directory into the appropriate domain folder
2. Rename and edit `run.py` with your workflow logic
3. Fill in all sections of `README.md` (see template for required sections)
4. Optionally update `sample_config.yaml` with workflow-specific metadata

```bash
cp -r workflows/_template workflows/fdm_slicers/bambu_studio/my_workflow
```

## Prerequisites

```bash
pip install -e .        # install the helio_api package
export HELIO_PAT="..."  # set your Personal Access Token
```
