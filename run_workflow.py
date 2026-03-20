#!/usr/bin/env python3

import argparse
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


WORKFLOW_ROOT = Path("/home/yangzichen/workflow")
WORKFLOW_REGISTRY = {
    "cloops2": WORKFLOW_ROOT / "cloops2" / "snakemake_core" / "Snakefile",
    "rnaseq": WORKFLOW_ROOT / "rnaseq-downstream" / "Snakefile",
}


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run a registered Snakemake workflow from a project config file."
    )
    parser.add_argument(
        "project",
        nargs="?",
        default="config.yaml",
        help="Project config file path, or a project directory containing config.yaml/project.yaml.",
    )
    parser.add_argument(
        "--cores",
        type=int,
        default=None,
        help="Override cores from config.",
    )
    parser.add_argument(
        "--snakemake-cmd",
        default=None,
        help="Full Snakemake command to use, for example 'snakemake' or 'conda run -n snakemake snakemake'.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Add -n to the Snakemake command.",
    )
    parser.add_argument(
        "snakemake_args",
        nargs=argparse.REMAINDER,
        help="Extra arguments passed to Snakemake. Use -- before them.",
    )
    return parser.parse_args()


def resolve_project_file(project_arg: str) -> Path:
    candidate = Path(project_arg).expanduser().resolve()
    if candidate.is_dir():
        for name in ("project.yaml", "config.yaml"):
            config_path = candidate / name
            if config_path.exists():
                return config_path
        raise FileNotFoundError(
            f"No project config found in {candidate}. Expected project.yaml or config.yaml."
        )
    if candidate.exists():
        return candidate
    raise FileNotFoundError(f"Project path does not exist: {candidate}")


TOP_LEVEL_PATTERN = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*?)\s*$")


def parse_scalar(value: str):
    value = value.strip()
    if not value:
        return ""
    if value[0] in {'"', "'"} and value[-1] == value[0]:
        return value[1:-1]
    if re.fullmatch(r"[0-9]+", value):
        return int(value)
    return value


def load_launcher_fields(config_path: Path) -> dict:
    data = {}
    with config_path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.rstrip("\n")
            if not line or line.lstrip().startswith("#"):
                continue
            if line[:1].isspace():
                continue
            match = TOP_LEVEL_PATTERN.match(line)
            if not match:
                continue
            key, value = match.groups()
            if key in {"workflow", "cores", "snakemake_cmd"}:
                data[key] = parse_scalar(value.split(" #", 1)[0])
    return data


def normalize_extra_args(args):
    extra = list(args)
    if extra and extra[0] == "--":
        extra = extra[1:]
    return extra


def main():
    args = parse_args()
    config_path = resolve_project_file(args.project)
    config = load_launcher_fields(config_path)

    workflow_name = config.get("workflow")
    if not workflow_name:
        raise KeyError(
            f"Missing required 'workflow' field in {config_path}. "
            f"Available workflows: {', '.join(sorted(WORKFLOW_REGISTRY))}"
        )
    if workflow_name not in WORKFLOW_REGISTRY:
        raise KeyError(
            f"Unknown workflow '{workflow_name}' in {config_path}. "
            f"Available workflows: {', '.join(sorted(WORKFLOW_REGISTRY))}"
        )

    snakefile = WORKFLOW_REGISTRY[workflow_name]
    if not snakefile.exists():
        raise FileNotFoundError(f"Registered Snakefile does not exist: {snakefile}")

    snakemake_cmd = args.snakemake_cmd or config.get("snakemake_cmd") or "snakemake"
    snakemake_parts = shlex.split(str(snakemake_cmd))
    if not snakemake_parts:
        raise ValueError("Snakemake command is empty.")
    if shutil.which(snakemake_parts[0]) is None:
        raise FileNotFoundError(
            f"Snakemake executable not found: {snakemake_parts[0]}"
        )

    project_dir = config_path.parent
    cores = args.cores or config.get("cores") or config.get("N_CPUS") or 1

    command = [
        *snakemake_parts,
        "-s",
        str(snakefile),
        "--configfile",
        str(config_path),
        "--directory",
        str(project_dir),
        "--cores",
        str(cores),
    ]
    if args.dry_run:
        command.append("-n")
    command.extend(normalize_extra_args(args.snakemake_args))

    print("Running:", " ".join(command), file=sys.stderr)
    raise SystemExit(subprocess.call(command))


if __name__ == "__main__":
    main()
