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
    gmm_params_df = pd.read_csv(gmm_params_ffp, index_col=0, dtype={"event": str})
    gmm_params_df = gmm_params_df.loc[gmm_params_df.event == fault]
    gmm_params_df = gmm_params_df.set_index("site").sort_index()

    im_columns = [
        f"{str(IM)}_mean",
        f"{str(IM)}_std_Total",
        f"{str(IM)}_std_Inter",
        f"{str(IM)}_std_Intra",
    ]
    gmm_params_df = gmm_params_df[im_columns]
    gmm_params_df.columns = ["mu", "sigma_total", "sigma_between", "sigma_within"]

    print(f"Loading Observations")
    obs_df = pd.read_csv(observations_ffp, index_col=0, low_memory=False)
    obs_df = obs_df.loc[obs_df.evid == fault]
    obs_df = obs_df.set_index("sta").sort_index()

    # Only need IM of interest
    obs_series = np.log(obs_df[str(IM)])
    del obs_df

    obs_stations = obs_series.index.values.astype(str)
    assert station not in obs_stations

    # Check that we have GMM data for all observed stations
    # Otherwise drop those stations
    mask = np.isin(obs_stations, gmm_params_df.index.values)
    if np.count_nonzero(mask) > 0:
        print(
            f"Missing GMM parameters for (observation) stations:\n"
            f"{obs_stations[~mask]}\n\tDropping these stations"
        )
        obs_stations = obs_stations[mask]

    # Stations of interest (with data)
    stations = np.concatenate(([station], obs_stations))
    gmm_params_df = gmm_params_df.loc[stations]

    print("Computing distance matrix")
    dist_matrix = sh.im_dist.calculate_distance_matrix(stations, stations_df)

    print("Computing correlation matrix")
    R = sh.im_dist.get_corr_matrix(stations, dist_matrix, IM)

    # C_c(i,j) = rho_{i,j} * \delta_{W_i} * \delta_{W_j}
    # Equation 4 in Bradley 2014
    C_c = pd.DataFrame(
        data=np.einsum(
            "i, ij, j -> ij",
            gmm_params_df.loc[obs_stations].sigma_within.values,
            R.loc[obs_stations, obs_stations],
            gmm_params_df.loc[obs_stations].sigma_within.values,
        ),
        index=obs_stations,
        columns=obs_stations,
    )
    # Sanity check
    assert np.all(
        np.isclose(
            np.diag(C_c.values),
            gmm_params_df.loc[obs_stations, "sigma_within"].values ** 2,
        )
    )

    total_residual = (
        obs_series.loc[obs_stations] - gmm_params_df.loc[obs_stations, "mu"]
    )

    # Compute the between event-residual using the observation stations
    # First part of Equation 3 numerator is just row-wise sum of inverse C_c
    C_c_inv = np.linalg.inv(C_c)
    numerator = np.einsum("ki, i -> ", C_c_inv, total_residual)
    denom = np.sum(
        (1 / gmm_params_df.loc[obs_stations].sigma_between.values ** 2)
        + np.sum(C_c_inv, axis=1)
    )
    between_residual = numerator / denom

    # Compute the within-event residual
    within_residual = total_residual - between_residual

    # Define the within-event residual distribution
    # Equation 5 in Bradley 2014
    within_residual_mu = np.zeros(stations.size)
    within_residual_cov = np.full((stations.size, stations.size), fill_value=np.nan)
    within_residual_cov[1:, 1:] = C_c
    within_residual_cov[0, 1:] = within_residual_cov[1:, 0] = (
        R.loc[obs_stations, station]
        * gmm_params_df.loc[station, "sigma_within"]
        * gmm_params_df.loc[obs_stations, "sigma_within"]
    )
    within_residual_cov[0, 0] = gmm_params_df.loc[station, "sigma_within"] ** 2


    # Define the conditional within-event distribution
    cond_within_residual_mu = np.einsum(
        "i, ij, j -> ", within_residual_cov[0, 1:], C_c_inv, within_residual.values
    )
    cond_within_residual_sigma = gmm_params_df.loc[
        station, "sigma_within"
    ] ** 2 - np.einsum(
        "i, ij, j -> ", within_residual_cov[0, 1:], C_c_inv, within_residual_cov[1:, 0]
    )

    # Define the conditional lnIM distriubtion
    cond_lnIM_mu = gmm_params_df.loc[station, "mu"] + between_residual + cond_within_residual_mu
    cond_ln_sigma = cond_within_residual_sigma



    print(cond_lnIM_mu, cond_ln_sigma)

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
