# Snakemake Project Runner

`run_workflow.py` is a thin launcher for project-oriented Snakemake runs.

It expects each project directory to contain a YAML config with:

- `workflow`: registered workflow name, currently `cloops2` or `rnaseq`
- workflow-specific Snakemake config keys
- optional `cores`
- optional `snakemake_cmd`, for example `conda run -n snakemake snakemake`

Example usage from a project directory:

```bash
python /home/yangzichen/workflow/snakemake-project-runner/run_workflow.py project.yaml
```

Or simply:

```bash
python /home/yangzichen/workflow/snakemake-project-runner/run_workflow.py .
```

The launcher will:

1. read `workflow` from the project config
2. resolve the matching Snakefile from the internal registry
3. run `snakemake -s <snakefile> --configfile <project_yaml> --directory <project_dir>`

This keeps workflow code under `workflow/` and project-specific configs under `projects/`.

Registered workflows:

- `cloops2` -> `/home/yangzichen/workflow/cloops2/snakemake_core/Snakefile`
- `rnaseq` -> `/home/yangzichen/workflow/rnaseq-downstream/Snakefile`
