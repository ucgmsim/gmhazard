"""Generates a custom distributed seismicity ERF file from
a distributed seismicity NHM file"""

import argparse
import os

import pandas as pd

import seistech_calc as si

ANNUAL_REC_PROB = "annual_rec_prob"
RUP_NAME = "rupture_name"
MAG_NAME = "mw"


def write_ds_erf(save_location: str, background_values: pd.DataFrame):
    """Stores the background data to a csv file"""
    location = os.path.abspath(save_location)
    background_values.to_csv(
        location, header=[RUP_NAME, ANNUAL_REC_PROB, MAG_NAME], index=False
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ds_nhm_ffp", type=str, help="The distributed seismicity nhm file path"
    )
    parser.add_argument("output_ffp", type=str, help="Output file path")
    args = parser.parse_args()

    nhm_df = si.utils.read_ds_nhm(args.ds_nhm_ffp)
    rupture_df = si.utils.calculate_rupture_rates(nhm_df)
    write_ds_erf(args.output_ffp, rupture_df)


if __name__ == "__main__":
    main()
