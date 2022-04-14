#!/usr/bin/env python3
"""Script to calculate rupture distance for empirical distributed seismicity

Writes distances to site source db specified
"""

import argparse
import os

from mpi4py import MPI
import numba
import numpy as np
import pandas as pd

from qcore import formats
from qcore import geo

import gmhazard_calc as sc
import common

MAX_RJB = max(common.DIST)

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
master = 0
is_master = not rank

def calculate_distances(background_file, ll_file, ssddb_path):
    """
    Calculates site-source-distances for every fault in the background file at every station in the ll file.

    Stores the value if rjb < MAX_RJB, and then calculates rrup.
    rx,ry,rtvz is NaN as it is calculating for non-volcanic point sources

    :param background_file: Background seismicity txt file
    :param ll_file: Station file
    :param ssddb_path: Output file path
    :return: None
    """
    background_data = sc.utils.read_ds_nhm(background_file)
    site_df = formats.load_station_file(ll_file)
    n_stations = len(site_df)

    fault_df = None
    if is_master:
        fault_list = [
            sc.utils.create_ds_fault_name(row.source_lat, row.source_lon, row.source_depth)
            for __, row in background_data.iterrows()
        ]
        fault_df = pd.DataFrame(fault_list, columns=["fault_name"])
    fault_df = comm.bcast(fault_df, root=master)

    work = site_df[rank::size]

    with sc.dbs.SiteSourceDB(
        ssddb_path, sc.constants.SourceType.distributed.value, writeable=True
    ) as distance_store:
        for site_index, site in work.iterrows():
            distance_df = pd.DataFrame()
            print(
                f"Processing site {(site_df.index.get_loc(site_index) + 1)} / {n_stations} - Rank: {rank}"
            )

            rjb = geo.get_distances(
                background_data[["source_lon", "source_lat"]].values, site.lon, site.lat
            )
            mask = rjb <= MAX_RJB
            if np.any(mask):
                rrup = np.sqrt(
                    rjb[mask] ** 2 + background_data["source_depth"][mask] ** 2
                )

                distance_df["fault_id"] = fault_df["fault_name"][mask].index
                distance_df["rjb"] = rjb[mask]
                distance_df["rrup"] = rrup.values
                distance_df["rx"] = np.nan
                distance_df["ry"] = np.nan
                distance_df["rtvz"] = np.nan

                distance_store.write_site_distances_data(site.name, distance_df)

            else:
                print(f"no data found for site: {site.name}")

        distance_store.write_site_data(site_df)
        distance_store.write_fault_data(fault_df)
        distance_store.write_attributes(
            erf_fname=os.path.basename(background_file),
            station_list_fname=os.path.basename(ll_file),
        )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("background_txt", help="background txt file")
    parser.add_argument("ll_file")
    parser.add_argument("output_path")

    return parser.parse_args()


def calculate_ds_distances():
    args = None
    if is_master:
        args = parse_args()
    args = comm.bcast(args, root=master)

    calculate_distances(args.background_txt, args.ll_file, args.output_path)
    MPI.Finalize()


if __name__ == "__main__":
    calculate_ds_distances()
