"""Script for computing the results for the specified project"""
from pathlib import Path
import argparse

import project_gen as pg


def main(project_dir: Path, n_procs: int = 4):
    # Run Hazard, Disagg, UHS and GMS
    pg.gen_psha_project_data(project_dir, n_procs=n_procs)
    pg.gen_gms_project_data(project_dir, n_procs=n_procs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "project_dir",
        type=str,
        help="Path to the project directory for which to compute results",
    )
    parser.add_argument("--n_procs", type=int, help="Number of processes to use")

    args = parser.parse_args()

    main(Path(args.project_dir), n_procs=args.n_procs)
