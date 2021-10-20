"""Script for manually creating a new project (and its data & results)

It is possible to resume calculations (of the results not dbs) of a broken run,
however no checks for completeness are performed (so the calculations
being processed at the time of failure will be incomplete and its
up to the user to clean these up)
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
    erf_dir: Path = None,
    erf_pert_dir: Path = None,
    flt_erf_version: str = "NHM",
    setup_only: bool = False,
    model_config_ffp: Path = pg.MODEL_CONFIG_PATH,
    empirical_weight_config_ffp: Path = pg.EMPIRICAL_WEIGHT_CONFIG_PATH,
):
    with open(project_params_ffp, "r") as f:
        project_params = yaml.safe_load(f)

    pg.create_project(
        project_params,
        projects_base_dir,
        scripts_dir,
        n_procs=n_procs,
        new_project=False,
        erf_dir=erf_dir,
        erf_pert_dir=erf_pert_dir,
        flt_erf_version=flt_erf_version,
        setup_only=setup_only,
        model_config_ffp=model_config_ffp,
        empirical_weight_config_ffp=empirical_weight_config_ffp,
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
        help="The path to the GMHazard Scripts Local scripts folder",
    )
    # Distributed seismicity calculation needs 2 processes to run
    parser.add_argument(
        "--n_procs",
        type=int,
        help="Number of processes to use - minimum is 2",
        default=2,
    )
    parser.add_argument(
        "--erf_dir", type=Path, help="Path to the ERF directory", default=None
    )
    parser.add_argument(
        "--erf_pert_dir",
        type=Path,
        help="Path to the directory of pertubated ERFs",
        default=None,
    )
    parser.add_argument(
        "--flt_erf_version",
        type=str,
        choices=list(pg.FLT_ERF_MAPPING.keys()),
        help="The ERF version to use",
        default="NHM_v21p8p1",
    )
    parser.add_argument(
        "--setup_only",
        action="store_true",
        help="If set, only the config and DBs are generated, "
        "but no results are computed",
        default=False,
    )
    parser.add_argument(
        "--model_config_ffp",
        type=Path,
        help="Path to the empirical model config file to use.",
        default=pg.MODEL_CONFIG_PATH,
    )
    parser.add_argument(
        "--empirical_weight_config_ffp",
        type=Path,
        help="Path to the GMM weights config file that matches with the empirical model config.",
        default=pg.EMPIRICAL_WEIGHT_CONFIG_PATH,
    )
    args = parser.parse_args()

    if args.n_procs < 2:
        parser.error("Minimum n_procs is 2.")

    main(
        args.project_parameters_config_ffp,
        args.projects_base_dir,
        args.scripts_dir,
        n_procs=args.n_procs,
        erf_dir=args.erf_dir,
        erf_pert_dir=args.erf_pert_dir,
        flt_erf_version=args.flt_erf_version,
        setup_only=args.setup_only,
        model_config_ffp=args.model_config_ffp,
        empirical_weight_config_ffp=args.empirical_weight_config_ffp,
    )
