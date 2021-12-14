import argparse

import numpy as np
import pandas as pd
from random import sample

import common
from qcore.formats import load_station_file
from gmhazard_calc.directivity.HypoMethod import HypoMethod
from gmhazard_calc import directivity


def compute_nz_site_effect(
    sites_file, station_file, fault_name, nhyps, period, grid_space, method, output_dir
):
    site_names = sample(list(np.load(sites_file)), 1000)
    stat_df = load_station_file(station_file)

    site_coords = np.asarray(stat_df.loc[site_names].values)

    column_values = []
    for x in nhyps:
        column_values.append(f"FD_{x}")
        column_values.append(f"PHI_RED_{x}")
    df = pd.DataFrame(index=site_names, columns=column_values)

    # PREP
    fault, _, planes, lon_lat_depth, _, _ = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

    df = df.sort_index(ascending=False)

    for nhpy in nhyps:
        hypo_along_strike = nhpy
        hypo_down_dip = 1

        fdi, fdi_array, phi_red = directivity.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            hypo_along_strike,
            hypo_down_dip,
            fault.mw,
            fault.rake,
            periods=[period],
            method=method,
        )

        df[f"FD_{nhpy}"] = np.exp(fdi)
        df[f"PHI_RED_{nhpy}"] = phi_red

    df.to_csv(f"{output_dir}/{fault_name}_sites.csv")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("sites_file")
    parser.add_argument("station_file")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--fault_name",
        default="Wairau",
        help="Fault to calculate for",
    )
    parser.add_argument(
        "--nhyps",
        default=[5, 15, 30, 50, 100, 1000],
        nargs="+",
        help="List of Hypocentre comparisons",
    )
    parser.add_argument(
        "--period",
        default=im.period,
        help="Period to calculate directivity for",
    )
    parser.add_argument(
        "--grid_space",
        default=grid_space,
        help="Number of sites to do along each axis",
    )
    parser.add_argument(
        "--method",
        default="LATIN_HYPERCUBE",
        help="Method to place hypocentres",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    compute_nz_site_effect(
        args.sites_file,
        args.station_file,
        args.fault,
        args.nhyps,
        args.period,
        args.grid_space,
        HypoMethod[args.method],
        args.output_dir,
    )
