"""
Script to read empirical txt files and save them into a parametric db

Assumes Ds / fault & zhao (subduction) / bradley (shallow crustal)
"""
import argparse
import glob
import os

import numpy as np
import pandas as pd

from qcore import formats
from gmhazard_calc.constants import SourceType
import gmhazard_calc.utils as utils
import common


def read_file(ffp):
    return pd.read_csv(
        ffp,
        sep="\t",
        names=("fault", "mag", "rrup", "med", "dev", "prob", "tect_type"),
        usecols=(0, 1, 2, 5, 6, 7, 8),
        dtype={
            "fault": object,
            "mag": np.float32,
            "rrup": np.float32,
            "med": np.float32,
            "dev": np.float32,
            "prob": np.float32,
            "tect-type": object,
        },
        engine="c",
        skiprows=1,
    )


def get_ds_rupture_names(ds_df, ds_erf_df):
    ds_df = ds_df.sort_values("prob")
    ds_erf_df.sort_values("annual_rec_prob", inplace=True)

    # probability values have a maximum deviation of 1e-3 so shouldn't impact hazard values
    df = pd.merge_asof(ds_df, ds_erf_df, left_on="prob", right_on="annual_rec_prob")

    cols = list(df.columns)
    cols.remove("fault")
    cols.remove("mw")
    cols.remove("mag")
    cols.remove("annual_rec_prob")
    cols.remove("rrup")
    return df[cols]


def get_flt_rupture_names(flt_data, flt_erf_df):
    flt_data = flt_data.drop(["rrup", "prob", "mag"], axis=1)
    return flt_data.merge(flt_erf_df, left_on="fault", right_on="rupture_name")


def store_empiricals(emp_folder, output_folder, ll_ffp, ds_erf_ffp, flt_nhm_ffp):
    im_folders = glob.glob(os.path.join(emp_folder, "*"))
    ims = get_im_names(im_folders)

    site_df = formats.load_station_file(ll_ffp)

    sites = [
        "_".join(os.path.basename(file).split("_")[0:3])
        for file in glob.glob(os.path.join(im_folders[0], "Emp*"))
    ]
    n_sites = len(sites)

    emp_models = ["Z06", "B10"]
    source_types = ["ds", "flt"]
    imdb_ds_dict, __ = common.open_imdbs_from_list(
        emp_models, output_folder, SourceType.distributed
    )
    imdb_flt_dict, __ = common.open_imdbs_from_list(emp_models, output_folder, SourceType.fault)

    ds_erf_df = pd.read_csv(
        ds_erf_ffp,
        dtype={
            "rupture_name": "category",
            "annual_rec_prob": np.float32,
            "mw": np.float32,
        },
    )
    ds_rupture_df = pd.DataFrame(ds_erf_df["rupture_name"].astype("category"))

    flt_erf_df = utils.flt_nhm_to_rup_df(flt_nhm_ffp)
    flt_erf_df = pd.DataFrame(flt_erf_df.rupture_name)
    # makes a copy of index that is preserved in merge
    ds_erf_df["index"] = ds_erf_df.index
    flt_erf_df["index"] = flt_erf_df.index

    for i, site in enumerate(sites):
        print(f"Processing site: {i} / {n_sites}")
        station_name, data = get_site_data(site, emp_folder, site_df)

        ds_mask = data.fault == "PointEqkSource"
        ds_data = data[ds_mask]
        flt_data = data[~ds_mask]

        ds_data = get_ds_rupture_names(ds_data, ds_erf_df)
        flt_data = get_flt_rupture_names(flt_data, flt_erf_df)

        ds_model_mask = ds_data.tect_type == "Active Shallow Crust "
        flt_model_mask = flt_data.tect_type == "Subduction Interface "

        ds_b10_data = ds_data[ds_model_mask]  # matches shallow crustal
        flt_b10_data = flt_data[~flt_model_mask]  # matches shallow crustal and volcanic
        ds_z06_data = ds_data[~ds_model_mask]  # matches subduction slab
        flt_z06_data = flt_data[flt_model_mask]  # matches subduction interface

        flt_b10_data.index = flt_b10_data["index"]
        flt_z06_data.index = flt_z06_data["index"]
        ds_b10_data.index = ds_b10_data["index"]
        ds_z06_data.index = ds_z06_data["index"]

        ds_b10_data = ds_b10_data.drop(
            ["rupture_name", "prob", "tect_type", "index"], axis=1
        )
        flt_b10_data = flt_b10_data.drop(
            ["rupture_name", "tect_type", "fault", "index"], axis=1
        )
        ds_z06_data = ds_z06_data.drop(
            ["rupture_name", "prob", "tect_type", "index"], axis=1
        )
        flt_z06_data = flt_z06_data.drop(
            ["rupture_name", "tect_type", "fault", "index"], axis=1
        )

        imdb_ds_dict["B10"].write_im_data(station_name, ds_b10_data)
        imdb_ds_dict["Z06"].write_im_data(station_name, ds_z06_data)
        imdb_flt_dict["B10"].write_im_data(station_name, flt_b10_data)
        imdb_flt_dict["Z06"].write_im_data(station_name, flt_z06_data)

    rupture_df = pd.DataFrame(flt_erf_df["rupture_name"])
    common.write_data_and_close(
        imdb_ds_dict,
        "NZBCK211_OpenSHA.txt",
        ds_rupture_df,
        site_df,
        "non_uniform_whole_nz_with_real_stations-hh400_v18p6.vs30",
        ims,
    )
    common.write_data_and_close(
        imdb_flt_dict,
        "NZ_FLTmodel_2010_v18p6.txt",
        rupture_df,
        site_df,
        "non_uniform_whole_nz_with_real_stations-hh400_v18p6.vs30",
        ims,
    )


def get_im_names(im_folders):
    return [utils.convert_im_type(os.path.basename(folder)) for folder in im_folders]


def get_site_data(site_fname, emp_folder, site_df):
    im_files = glob.glob(os.path.join(emp_folder, "*", site_fname + "_*"))

    data = site_fname.split("_")
    lat = float(data[1].replace("p", ".")[3:])  # Convert Lat-38p45764 to a float
    lon = float(data[2].replace("p", ".")[3:])  # Convert Lon174p89444 to a float
    site_index = (np.abs(site_df.lon - lon) + np.abs(site_df.lat - lat)).idxmin()
    site_name = site_df.loc[site_index].name

    n_faults = float("nan")
    combined_im_df = None

    for im_file in im_files:
        im_name = utils.convert_im_type(
            os.path.basename(os.path.abspath(os.path.join(im_file, "../")))
        )
        sigma_im_name = im_name + "_sigma"
        im_df = read_file(im_file)

        n_faults = len(im_df) if np.isnan(n_faults) else n_faults
        if n_faults != len(im_df):
            raise AssertionError(
                f"number of lines in empirical file are not consistent for {site_name, lon, lat}"
            )

        # rename the median and std columns to include the im name to allow merging
        im_df.columns = np.concatenate(
            [im_df.columns[:3].values, im_name, sigma_im_name, im_df.columns[5:]],
            axis=None,
        )

        im_df = im_df[im_df.prob > 0]

        if combined_im_df is None:
            combined_im_df = im_df
        else:
            combined_im_df = combined_im_df.merge(
                im_df[[im_name, sigma_im_name]], left_index=True, right_index=True
            )

    return site_name, combined_im_df


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("emp_folder")
    parser.add_argument("db_output_folder")
    parser.add_argument("station_file")
    parser.add_argument("ds_erf_ffp")
    parser.add_argument("flt_nhm_ffp")

    return parser.parse_args()


def main():
    args = parse_args()
    store_empiricals(
        args.emp_folder,
        args.db_output_folder,
        args.station_file,
        args.ds_erf_ffp,
        args.flt_nhm_ffp,
    )


if __name__ == "__main__":
    main()
