"""Writes the specified project as a zip file"""
import argparse
from pathlib import Path

import seistech_utils as su
import project_api as pa


def main(project_dir: Path, output_dir: Path, n_procs: int = 1):
    _, version_str = su.utils.get_package_version("project_api")
    project_dir_version_str = str(project_dir.parent.name)
    assert project_dir_version_str == version_str, "Versions have to match"

    zip_ffp = pa.utils.create_project_zip(
        project_dir.parent.parent,
        project_dir.name,
        version_str,
        output_dir,
        n_procs=n_procs,
    )
    print(f"Project zip file: {zip_ffp}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("project_dir", type=Path, help="Path to project directory")
    parser.add_argument("output_dir", type=Path, help="Output directory path")
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=1
    )

    args = parser.parse_args()

    main(args.project_dir, args.output_dir, n_procs=args.n_procs)
