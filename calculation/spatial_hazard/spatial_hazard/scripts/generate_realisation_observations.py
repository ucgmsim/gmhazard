import argparse
from pathlib import Path
from typing import Sequence
import multiprocessing as mp

import numpy as np
import pandas as pd

import gmhazard_calc as gc
import spatial_hazard as sh
from pygmt_helper import plotting


def main(
    IM: gc.im.IM,
    rupture: str,
    N: int,
    stations_ll_ffp: str,
    gmm_params_ffp: Path,
    observations_ffp: Path,
    output_dir: Path,
    n_procs: int,
    map_data_ffp: Path = None,
    int_stations: Sequence[str] = None,
):
    """

    Parameters
    ----------
    IM: IM
        IM for which to compute
        the conditional IM distribution
    rupture: string
        The rupture of interest
    N
    int_stations: sequence of strings
        The stations of interest
    stations_ll_ffp: Path
        Path to the stations .ll file
    gmm_params_ffp: Path
        Path to the empirical GMM parameters

        Expects columns names
        [{IM}_mean, {IM}_std_Total, {IM}_std_Inter, {IM}_std_Intra]
    observations_ffp: Path
        Path to the observations

        Expected file format is that of the
        NZ GMDB flatfile i.e. Columns ["evid", "sta" "{IM}"]
    output_dir
    n_procs
    """
    # Load the data
    # Load the station data
    stations_df = pd.read_csv(
        stations_ll_ffp, sep=" ", index_col=2, header=None, names=["lon", "lat"]
    )

    # Get GMM parameters
    print("Retrieving GMM parameters")
    gmm_params_df = pd.read_csv(gmm_params_ffp, index_col=0, dtype={"event": str})
    gmm_params_df = gmm_params_df.loc[gmm_params_df.event == rupture]
    gmm_params_df = gmm_params_df.set_index("site").sort_index()

    im_columns = [
        f"{str(IM)}_mean",
        f"{str(IM)}_std_Total",
        f"{str(IM)}_std_Inter",
        f"{str(IM)}_std_Intra",
    ]
    gmm_params_df = gmm_params_df[im_columns]
    gmm_params_df.columns = ["mu", "sigma_total", "sigma_between", "sigma_within"]

    # Use all stations with empirical GMM parameters
    # if not specific stations of interests are specified
    int_stations = (
        gmm_params_df.index.values if int_stations is None else np.asarray(int_stations)
    )

    # Add lat/lon for plotting later
    gmm_params_df = gmm_params_df.merge(stations_df, left_index=True, right_index=True)

    # Add median
    gmm_params_df["median"] = np.exp(gmm_params_df["mu"].values)

    print(f"Loading Observations")
    obs_df = pd.read_csv(observations_ffp, index_col=0, low_memory=False)
    obs_df = obs_df.loc[obs_df.evid == rupture]
    obs_df = obs_df.set_index("sta").sort_index()

    # Only need IM of interest
    obs_series = np.log(obs_df[str(IM)])
    del obs_df

    # Compute the conditional distribution for all sites of interest
    cond_df, obs_series, obs_stations, obs_station_masks = sh.im_dist.compute_cond_lnIM(
        IM, int_stations, stations_df, gmm_params_df, obs_series
    )
    assert not np.any(np.isin(obs_series.index.values, cond_df.index.values))

    # Combine into single dataframe
    comb_df = pd.concat((cond_df, obs_series.to_frame("mu")), axis=0)
    comb_df["observation"] = False
    comb_df.loc[obs_stations, "observation"] = True
    comb_df.loc[obs_stations, "sigma"] = 0.0
    comb_df = comb_df.merge(stations_df, how="inner", left_index=True, right_index=True)

    # Compute median
    comb_df["median"] = np.exp(comb_df.mu)

    # Generate plots
    print(f"Generating plots")
    map_data = (
        plotting.NZMapData.load(map_data_ffp) if map_data_ffp is not None else None
    )
    results = []
    with mp.Pool(6) as p:
        results.append(
            p.apply_async(
                sh.plots.gen_spatial_plot,
                (
                    comb_df,
                    "median",
                    (172.6909, -43.566),
                    (50, 50),
                    output_dir / "median.png",
                    "Conditional Median",
                    None,
                    map_data,
                    True,
                    1.2,
                ),
            )
        )
        results.append(
            p.apply_async(
                sh.plots.gen_spatial_plot,
                (
                    comb_df,
                    "sigma",
                    (172.6909, -43.566),
                    (50, 50),
                    output_dir / "sigma.png",
                    "Conditional Sigma",
                    None,
                    map_data,
                    True,
                    0.7,
                ),
            )
        )
        results.append(
            p.apply_async(
                sh.plots.gen_spatial_plot,
                (
                    gmm_params_df,
                    "median",
                    (172.6909, -43.566),
                    (50, 50),
                    output_dir / "gmm_mu.png",
                    "Marginal Median",
                    None,
                    map_data,
                    True,
                    1.2,
                ),
            )
        )
        results.append(
            p.apply_async(
                sh.plots.gen_spatial_plot,
                (
                    gmm_params_df,
                    "sigma_total",
                    (172.6909, -43.566),
                    (50, 50),
                    output_dir / "gmm_sigma.png",
                    "Marginal Sigma",
                    None,
                    map_data,
                    True,
                    0.7,
                ),
            )
        )

        # Wait for completion
        [cur_res.get() for cur_res in results]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("IM", type=str, help="IM of interest")
    parser.add_argument(
        "fault",
        type=str,
        help="The fault for which to compute spatial_correlation hazard",
    )
    parser.add_argument("N", type=int, help="Number of realisations to generate")
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
    parser.add_argument("--stations", type=str, nargs="+", help="Site of interest")
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )
    parser.add_argument(
        "--map_data_ffp", type=Path, help="Path to the qcore map data", default=None
    )

    args = parser.parse_args()

    main(
        gc.im.IM.from_str(args.IM),
        args.fault,
        args.N,
        args.stations_ll_ffp,
        args.gmm_params_ffp,
        args.observation_ffp,
        args.output_dir,
        n_procs=args.n_procs,
        int_stations=args.stations,
        map_data_ffp=args.map_data_ffp,
    )
