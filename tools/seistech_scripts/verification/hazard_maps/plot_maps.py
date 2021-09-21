"""Script for creating lots of ratio plots using plot_items
Note: Pretty sure this only works on hypocentre/epicentre/mahuika

Input files are required to have the following columns:
station_name, lon, lat, value
"""
import os
import json
import glob
import shutil
import argparse
import subprocess
import tempfile
import multiprocessing as mp
from typing import Dict

import yaml
import pandas as pd

import seistech_utils as su

PLOT_CMD_TEMPLATE = "{} {} --xyz {} -f {} --xyz-cpt-labels {} --title"

EXCD_IM_SCALING_LOOKUP = {
    "0.00040405": {  # 2% in 50 years (rounded to 8 decimal points)
        "PGV": 80,
        "PGA": 1.0,
        "pSA_0.1": 2.5,
        "pSA_0.2": 2.5,
        "pSA_0.5": 1.5,
        "pSA_1.0": 0.8,
        "pSA_2.0": 0.6,
        "pSA_3.0": 0.6,
        "pSA_5.0": 0.4,
    },
    "0.00210721": {  # 10% in 50 years (rounded to 8 decimal points)
        "PGV": 80,
        "PGA": 1.0,
        "pSA_0.1": 2.5,
        "pSA_0.2": 2.5,
        "pSA_0.5": 1.5,
        "pSA_1.0": 0.8,
        "pSA_2.0": 0.6,
        "pSA_3.0": 0.6,
        "pSA_5.0": 0.4,
    },
    "0.01386294": { # 50% in 50 years (rounded to 8 decimal points)
        "PGV": 80,
        "PGA": 1.0,
        "pSA_0.1": 2.5,
        "pSA_0.2": 2.5,
        "pSA_0.5": 1.5,
        "pSA_1.0": 0.8,
        "pSA_2.0": 0.6,
        "pSA_3.0": 0.6,
        "pSA_5.0": 0.4,
    }
}


def plot(
    plot_items_ffp: str,
    in_ffp: str,
    options_dict: Dict,
    tmp_dir: str,
    use_excd_im_scaling: bool = False,
    no_clobber: bool = False,
):
    """Creates a plot using the specified plot options"""
    # Read the metadata file
    with open(su.utils.change_file_ext(in_ffp, "json")) as f:
        meta_data = json.load(f)

    # Look up the scaling to use
    if use_excd_im_scaling:
        excd, im = float(meta_data["exceedance"]), meta_data["im"]
        try:
            max_scale = EXCD_IM_SCALING_LOOKUP[f"{excd:.8f}"][im]
        except:
            print(
                f"ERROR: No scaling specified for exceedance {excd:.8f} and IM {im}, no plotting was done."
            )
            return
        else:
            options_dict["options"]["xyz-cpt-max"] = max_scale

    # Get the plotting flags
    plot_options = []
    for cur_flag in options_dict["flags"]:
        plot_options.append(f"--{cur_flag}")

    # Get the key-value plotting options
    for key, value in options_dict["options"].items():
        plot_options.append(f"--{key} {value}")
    plot_options = " ".join(plot_options)

    title = meta_data.get("plot_title")
    if title is None:
        title = (
            f"{'NZ Code' if meta_data.get('nz_code') else meta_data['id']}, "
            f"{meta_data['im']}, {meta_data['excd_title']}"
        )

    # Create temporary .xyz file for plotting
    # Cleaning up of the tmp dir has to be done by the calling function
    df = pd.read_csv(in_ffp)
    tmp_xyz_ffp = os.path.join(
        tmp_dir, su.utils.change_file_ext(os.path.basename(in_ffp), "xyz")
    )
    df.to_csv(
        tmp_xyz_ffp, sep=" ", columns=["lon", "lat", "value"], header=False, index=False
    )

    out_f = os.path.basename(in_ffp).split(".")[0]
    cmd = PLOT_CMD_TEMPLATE.format(
        plot_items_ffp, plot_options, tmp_xyz_ffp, out_f, meta_data["im"]
    ).split(" ")
    cmd.append(title)

    # Skip file if no_clobber is set and the file already exists
    if not (no_clobber and os.path.exists(su.utils.change_file_ext(in_ffp, "png"))):
        result = run_plot(cmd, in_ffp, out_f, "")

    if "regions" in options_dict:
        for region_name in options_dict["regions"]:
            if not (no_clobber and os.path.exists(out_f + f"_{region_name}.png")):
                region_cmd = list(cmd)
                region_cmd.extend(["-r", options_dict["regions"][region_name]])
                result = run_plot(region_cmd, in_ffp, out_f, f"_{region_name}")

    return result


def run_plot(cmd, in_ffp, out_f, region_name=""):
    print(f"Plotting {os.path.basename(in_ffp)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Hack, since plot_items doesn't support saving to a full path
    if result.returncode == 0:
        cur_dir = os.getcwd()
        shutil.move(
            os.path.join(cur_dir, f"{out_f}_0.png"),
            os.path.join(os.path.dirname(in_ffp), f"{out_f}{region_name}.png"),
        )
    print("----------------------------------------------")
    print(f"Cmd:\n{cmd}\n")
    print(f"stdout:\n{result.stdout.decode()}")
    print(f"stderr:\n{result.stderr.decode()}")
    print("----------------------------------------------")

    return result


def main(
    plot_items_ffp: str,
    data_dir: str,
    file_filter: str,
    plot_options_config: str,
    n_procs: int = 1,
    no_clobber: bool = False,
    recursive: bool = False,
    use_excd_im_scaling: bool = False,
):
    file_pattern = (
        os.path.join(data_dir, "**", file_filter)
        if recursive
        else os.path.join(data_dir, file_filter)
    )
    files = glob.glob(file_pattern, recursive=recursive)

    with open(plot_options_config, "r") as f:
        options_dict = yaml.safe_load(f)

    # Create a temporary dir for the .xyz files
    with tempfile.TemporaryDirectory() as tmp_dir:
        if n_procs == 1:
            for cur_file in files:
                result = plot(
                    plot_items_ffp,
                    cur_file,
                    options_dict,
                    tmp_dir,
                    use_excd_im_scaling,
                    no_clobber,
                )
        else:
            with mp.Pool(n_procs) as p:
                results = p.starmap(
                    plot,
                    [
                        (
                            plot_items_ffp,
                            cur_file,
                            options_dict,
                            tmp_dir,
                            use_excd_im_scaling,
                            no_clobber,
                        )
                        for cur_file in files
                    ],
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("plot_items_ffp", type=str)
    parser.add_argument("data_dir", type=str, help="Based data directory")
    parser.add_argument(
        "file_filter",
        type=str,
        help="Glob filter that will be used to select the files to plot",
    )
    parser.add_argument(
        "plot_options_config", type=str, help="Config file with the gmt plot options"
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="If set then glob searches for files recursively",
        default=False,
    )
    parser.add_argument("--n_procs", type=int, default=1)
    parser.add_argument(
        "--no_clobber",
        action="store_true",
        help="If set, then existing ratio plots are not overwritten",
        default=False,
    )
    parser.add_argument("--use_excd_im_scaling", action="store_true", default=False)

    args = parser.parse_args()

    main(
        args.plot_items_ffp,
        args.data_dir,
        args.file_filter,
        args.plot_options_config,
        n_procs=args.n_procs,
        no_clobber=args.no_clobber,
        recursive=args.recursive,
        use_excd_im_scaling=args.use_excd_im_scaling,
    )
