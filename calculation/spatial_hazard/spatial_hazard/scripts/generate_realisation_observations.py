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
    station: str,
    stations_ll_ffp: str,
    gmm_params_ffp: Path,
    observations_ffp: Path,
    output_dir: Path,
    n_procs: int,
):
    # Load the station data
    stations_df = pd.read_csv(
        stations_ll_ffp, sep=" ", index_col=2, header=None, names=["lon", "lat"]
    )

    # Get GMM parameters
    print("Retrieving GMM parameters")
    gmm_params_df = pd.read_csv(gmm_params_ffp, index_col=0)
    gmm_params_df = gmm_params_df.loc[gmm_params_df.event_id == fault]
    gmm_params_df = gmm_params_df.set_index("site")


    print(f"Loading Observations")
    obs_df = pd.read_csv(observations_ffp, index_col=0, low_memory=False)
    obs_df = obs_df.loc[obs_df.evid == fault]
    obs_df = obs_df.set_index("sta")

    assert station not in obs_df.index.values

    print("Computing distance matrix")
    dist_matrix = sh.im_dist.calculate_distance_matrix([station], stations_df)

    assert np.all(dist_matrix.index.values == gmm_params_df.index.values) and np.all(
        dist_matrix.index.values == obs_df.index.values
    ), "Order of the stations has to be the same"

    print("Computing correlation matrix")
    R = sh.im_dist.get_corr_matrix(stations, dist_matrix, IM)

    # print("Generating realisation")
    # random_IMs, between_event, within_event = sh.im_dist.generate_im_values(
    #     N, R, emp_df
    # )
    #
    # ln_im_values, between, within = (
    #     pd.DataFrame(data=random_IMs.T, index=stations),
    #     pd.DataFrame(data=between_event.T, index=stations),
    #     pd.DataFrame(data=within_event.T, index=stations),
    # )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("IM", type=str, help="IM of interest")
    parser.add_argument(
        "fault", type=str, help="The fault for which to compute spatial hazard"
    )
    parser.add_argument("N", type=int, help="Number of realisations to generate")
    parser.add_argument("station", type=str, help="Site of interest")
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
