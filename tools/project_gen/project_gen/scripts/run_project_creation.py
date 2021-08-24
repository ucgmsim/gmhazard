"""Script for manually creating a new project (and its data & results)
For re-computing the results of an existing project, use
"""
import argparse
from pathlib import Path

import yaml

import project_gen as pg


def main(
    project_params_ffp: Path,
    projects_base_dir: Path,
    scripts_dir: Path,
    n_procs: int = 6,
):
    with open(project_params_ffp, "r") as f:
        project_params = yaml.safe_load(f)

    pg.create_project(
        project_params,
        projects_base_dir,
        scripts_dir,
        n_procs=n_procs,
        new_project=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "project_parameters_config_ffp",
        type=Path,
        help="Path to a yaml file that contains the project parameters, "
        "for an example of project parameters see "
        "EXAMPLE_PROJECT_PARAMS in constants.py",
    )
    parser.add_argument(
        "projects_base_dir",
        type=Path,
        help="The base directory of the projects, above the version directories",
    )
    parser.add_argument(
        "scripts_dir",
        type=Path,
        help="The path to the Seistech Scripts Local scripts folder",
    )
    # Distributed seismicity calculation needs 2 processes to run
    parser.add_argument(
        "--n_procs",
        type=int,
        help="Number of processes to use - minimum is 2",
        default=2,
    )

    args = parser.parse_args()

    if args.n_procs < 2:
        parser.error("Minimum n_procs is 2.")

    main(
        args.project_parameters_config_ffp,
        args.projects_base_dir,
        args.scripts_dir,
        n_procs=args.n_procs,
    )
