"""Script for generating the ground motion selection results"""
import argparse
from pathlib import Path

import project_gen as pg


def main(project_dir: Path, n_procs: int):
    pg.gen_gms_project_data(project_dir, n_procs=n_procs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "project_dir", type=str, help="Project directory for which to run GM selection"
    )
    parser.add_argument("--n_procs", type=int, default=1, help="Number of processes to use")

    args = parser.parse_args()

    main(Path(args.project_dir), n_procs=args.n_procs)
