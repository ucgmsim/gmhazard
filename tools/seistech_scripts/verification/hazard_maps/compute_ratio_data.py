"""Script for creating ratio .xyz files
Requires the filenames to have different prefixes,
but otherwise the same name (for the same IM & return period)

E.g. if prefix_1 = v18p6sim and prefix_2 = v18p6emp
and the files in the data dir are
v18p6emp_pSA_3p0_2_50.csv
v18p6emp_pSA_3p0_10_50.csv
v18p6sim_pSA_3p0_2_50.csv
v18p6sim_pSA_3p0_10_50.csv

then two ratio files will be created, i.e
- v18p6sim_pSA_3p0_2_50.csv / v18p6emp_pSA_3p0_2_50.csv
- v18p6sim_pSA_3p0_10_50.csv / v18p6emp_pSA_3p0_10_50.csv

where the resulting files have are named using the following format
{prefix_1}_vs_{prefix_2}_{common_name}

Expects the csv files to have the following columns:
station_name, lon, lat, value
"""

import os
import json
import glob
import argparse

import pandas as pd
import numpy as np

import seistech_utils as su


def merge_station(ffp_1: str, ffp_2: str, lat_max_filter: float = None):
    df_1 = pd.read_csv(ffp_1, index_col="station_name")
    df_2 = pd.read_csv(ffp_2, index_col="station_name")

    # Ensure there are no stations with the same location..
    assert np.count_nonzero(df_1.duplicated(subset=["lon", "lat"], keep=False)) == 0
    assert np.count_nonzero(df_2.duplicated(subset=["lon", "lat"], keep=False)) == 0

    pd.set_option("use_inf_as_na", True)
    merged_df = df_1.merge(df_2, left_index=True, right_index=True)
    merged_df["ratio"] = np.log(merged_df.value_x / merged_df.value_y)

    if lat_max_filter is not None:
        merged_df = merged_df.loc[merged_df.lat_x <= lat_max_filter]

    return merged_df


def main(
    data_dir: str,
    prefix_1: str,
    prefix_2: str,
    lat_max_filter: float = None,
    no_clobber: bool = False,
):
    prefix_1_files = [
        os.path.basename(cur_file)
        for cur_file in glob.glob(os.path.join(data_dir, f"{prefix_1}_*.csv"))
    ]
    prefix_2_files = [
        os.path.basename(cur_file)
        for cur_file in glob.glob(os.path.join(data_dir, f"{prefix_2}_*.csv"))
    ]

    # match & merge
    # This assumes that apart from the prefix the files are named
    # using the same description pattern!
    prefix_1_names = [
        cur_file.replace(f"{prefix_1}_", "") for cur_file in prefix_1_files
    ]
    prefix_2_names = [
        cur_file.replace(f"{prefix_2}_", "") for cur_file in prefix_2_files
    ]
    for cur_file_1, cur_name_1 in zip(prefix_1_files, prefix_1_names):
        if cur_name_1 not in prefix_2_names:
            print(f"No matching prefix 2 file for {cur_file_1}, skipping")
            continue

        # Do nothing if "no_clobber" is specified and result file exists
        cur_out_ffp = os.path.join(data_dir, f"{prefix_1}_vs_{prefix_2}_{cur_name_1}")
        if no_clobber and os.path.exists(cur_out_ffp):
            continue

        # Merge
        cur_file_2 = prefix_2_files[prefix_2_names.index(cur_name_1)]
        merged_df = merge_station(
            os.path.join(data_dir, cur_file_1),
            os.path.join(data_dir, cur_file_2),
            lat_max_filter=lat_max_filter,
        )

        # Drop nan_values
        merged_df.dropna(subset=["lon_x", "lat_x", "ratio"], inplace=True)

        # Read meta data (expects this to be the same for
        # both files, except of ensemble_id)
        with open(
            su.utils.change_file_ext(os.path.join(data_dir, cur_file_1), "json"), "r"
        ) as f:
            meta_data = json.load(f)

        # Write new metadata file
        new_meta_data = meta_data.copy()
        new_meta_data["id"] = f"{prefix_1}/{prefix_2}"
        with open(su.utils.change_file_ext(cur_out_ffp, "json"), "w") as f:
            json.dump(new_meta_data, f)

        # Write the data
        merged_df.to_csv(
            cur_out_ffp,
            columns=["lon_x", "lat_x", "ratio"],
            header=["lon", "lat", "value"],
            index=True,
            index_label="station_name",
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "data_dir", type=str, help="Data directory that contains the hazard map data"
    )
    parser.add_argument(
        "prefix_1",
        type=str,
        help="Prefix of the filenames for the numerator for "
        "the ratio calculation ln(prefix_1/prefix_2)",
    )
    parser.add_argument(
        "prefix_2", type=str, help="Prefix of the filenames for denominator"
    )
    parser.add_argument(
        "--lat_max_filter",
        type=float,
        help="All entries with lat > lat_max_filter are removed",
    )
    parser.add_argument(
        "--no_clobber",
        action="store_true",
        help="If true, then existing ratio files are not overwritten",
        default=False,
    )

    args = parser.parse_args()

    main(
        args.data_dir,
        args.prefix_1,
        args.prefix_2,
        lat_max_filter=args.lat_max_filter,
        no_clobber=args.no_clobber,
    )
