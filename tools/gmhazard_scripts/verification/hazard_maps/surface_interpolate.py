"""
Takes one or more csv files as an input (the format is the standard hazard file to be plotted)
Then interpolates the file to the whole NZ dimensions with a 1k discretisation with GMT Surface

Outputs files in the same format with the suffix .surface.csv/json
"""

import argparse
import os
import shutil
import subprocess
import tempfile

import pandas as pd

import gmhazard_utils as su


def interpolate_hazard_csv(f_name):
    print(f"interpolating {f_name}")

    df = pd.read_csv(f_name)
    json_ffp = su.utils.change_file_ext(f_name, 'json')
    surface_json_ffp = su.utils.change_file_ext(f_name, "surface.json")
    shutil.copy(json_ffp, surface_json_ffp)

    with tempfile.TemporaryDirectory() as t_dir:
        f_basename = os.path.basename(f_name)
        xyz_ffp = os.path.join(t_dir, change_file_ext(f_basename, 'xyz'))
        surface_grd_ffp = change_file_ext(xyz_ffp, 'surface.grd')
        surface_xyz_ffp = change_file_ext(xyz_ffp, 'surface.xyz')
        surface_csv_ffp = change_file_ext(f_name, 'surface.csv')
        df.to_csv(xyz_ffp, columns=['lon', 'lat', 'value'], header=None, sep=" ", index=False)

        subprocess.call(["gmt", "surface", "-I1k", "-R166/179/-48/-34", f"-G{surface_grd_ffp}", xyz_ffp])
        with open(surface_xyz_ffp, 'w') as surface_xyz_fp:
            subprocess.call(["gmt", "grd2xyz", f"{surface_grd_ffp}"], stdout=surface_xyz_fp)

        surface_df = pd.read_csv(surface_xyz_ffp, delim_whitespace=True, header=None, names=['lon', 'lat', 'value'])
        surface_df.to_csv(surface_csv_ffp, index_label='station_name')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", nargs='+', help="space delimited list of files to process")

    args = parser.parse_args()

    for f_name in args.file:
        interpolate_hazard_csv(f_name)


if __name__ == '__main__':
    main()
