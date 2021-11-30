#!/bin/env python3
"""Script for computing and saving the hazard map data,
i.e. the exceedance probability for each station at a
given exceedance level.
"""
import json
import argparse

import numpy as np

from gmhazard_calc.im import IM
import gmhazard_utils as su
import gmhazard_calc as sc


def main(args):
    ensemble = sc.gm_data.Ensemble(args.ensemble_id)

    if args.nz_code:
        hazard_map_data = sc.nz_code.nzs1170p5.run_hazard_map(
            ensemble, IM.from_str(args.im), args.exceedance, n_procs=args.n_procs
        )
    else:
        hazard_map_data = sc.hazard.run_hazard_map(
            ensemble, IM.from_str(args.im), args.exceedance, n_procs=args.n_procs
        )

    if np.any(hazard_map_data.isna()):
        print("Note: The resulting hazard map data contains np.nan values!")

    # Save some meta data
    meta_data = {
        "id": args.ensemble_id,
        "im": args.im,
        "exceedance": args.exceedance,
        "excd_title": args.exceedance
        if args.exceedance_title is None
        else args.exceedance_title,
        "nz_code": args.nz_code,
    }
    with open(su.utils.change_file_ext(args.save_file, "json"), "w",) as f:
        json.dump(meta_data, f)

    # Save the data
    hazard_map_data.to_csv(args.save_file, index_label="station_name")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("ensemble_id", type=str, help="The ensemble to use")
    parser.add_argument(
        "im", type=str, help="IM name, if pSA has to be in format pSA_X.Y"
    )
    parser.add_argument("exceedance", type=float, help="The exceedance value")
    parser.add_argument("save_file", type=str, help="Path of the save file")
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )
    parser.add_argument(
        "--nz_code",
        action="store_true",
        default=False,
        help="If set, then the hazard is calculated based on the NZ code",
    )
    parser.add_argument(
        "--exceedance_title",
        type=str,
        help="Exceedance part of the title",
        default=None,
    )

    args = parser.parse_args()

    main(args)
