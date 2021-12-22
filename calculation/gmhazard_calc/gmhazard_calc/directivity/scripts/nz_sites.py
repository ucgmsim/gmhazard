"""
Compute directivity values for NZ site locations
"""
import argparse

import numpy as np
import pandas as pd
from random import sample

import common
import qcore.formats as formats
from gmhazard_calc.directivity.HypoMethod import HypoMethod
from gmhazard_calc import directivity


def compute_nz_site_effect(
    sites_file,
    station_file,
    fault_name,
    nhyps,
    nstrikes,
    ndips,
    period,
    grid_space,
    method,
    output_dir,
):
    site_names = sample(list(np.load(sites_file)), 1000)
    stat_df = formats.load_station_file(station_file)

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

    nhyps_length = len(nstrikes) if nhyps is None else len(nhyps)

    for i in range(nhyps_length):
        n_hypo_data = directivity.NHypoData(
            method,
            None if nhyps is None else nhyps[i],
            None if nstrikes is None else nstrikes[i],
            None if ndips is None else ndips[i],
        )

        fdi, fdi_array, phi_red = directivity.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            n_hypo_data,
            fault.mw,
            fault.rake,
            periods=[period],
        )

        df[f"FD_{n_hypo_data.nhypo}"] = np.exp(fdi)
        df[f"PHI_RED_{n_hypo_data.nhypo}"] = phi_red

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
        "--nstrikes",
        default=None,
        nargs="+",
        help="List of hypocentres along strike",
    )
    parser.add_argument(
        "--ndips",
        default=None,
        nargs="+",
        help="List of hypocentres down dip",
    )
    parser.add_argument(
        "--nhypos",
        default=None,
        nargs="+",
        help="List of hypocentre totals",
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
        args.nstrikes,
        args.ndips,
        args.period,
        args.grid_space,
        HypoMethod[args.method],
        args.output_dir,
    )
