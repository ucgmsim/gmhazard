import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

import gmhazard_calc as gc
import spatial_hazard as sh


def main(
    IM: gc.im.IM,
    fault: str,
    N: int,
    int_stations: Sequence[str],
    stations_ll_ffp: str,
    gmm_params_ffp: Path,
    observations_ffp: Path,
    output_dir: Path,
    n_procs: int,
):
    # Compute the conditional distribution for all sites of interest
    cond_df, obs_series, obs_stations_used = sh.im_dist.compute_cond_lnIM(
        IM, fault, int_stations, stations_ll_ffp, gmm_params_ffp, observations_ffp
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("IM", type=str, help="IM of interest")
    parser.add_argument(
        "fault",
        type=str,
        help="The fault for which to compute spatial_correlation hazard",
    )
    parser.add_argument("N", type=int, help="Number of realisations to generate")
    parser.add_argument("station", type=str, nargs="+", help="Site of interest")
    parser.add_argument(
        "stations_ll_ffp",
        type=str,
        help="Path to the stations ll file. Has to contain the station of interest.",
    )
    parser.add_argument("gmm_params_ffp", type=str, help="Path to the GMM params ")
    parser.add_argument(
        "observation_ffp", type=str, help="Path to the observational data"
    )
    parser.add_argument("output_dir", type=Path, help="Path of the output directory")
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )

    args = parser.parse_args()

    main(
        gc.im.IM.from_str(args.IM),
        args.fault,
        args.N,
        args.station,
        args.stations_ll_ffp,
        args.gmm_params_ffp,
        args.observation_ffp,
        args.output_dir,
        args.n_procs,
    )
