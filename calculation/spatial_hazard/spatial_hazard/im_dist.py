from pathlib import Path
from typing import Sequence, Callable, List

import numpy as np
import pandas as pd
from scipy.linalg import cholesky

import gmhazard_calc as gc
import sha_calc as sha
from IM_calculation.source_site_dist.src_site_dist import calc_rrup_rjb


def compute_cond_lnIM(
    IM: gc.im.IM,
    rupture: str,
    int_stations: Sequence[str],
    stations_ll_ffp: str,
    gmm_params_ffp: Path,
    observations_ffp: Path,
    obs_site_filter_fn: Callable[[pd.DataFrame], List[str]] = None,
):
    """
    Computes the conditional lnIM distribution
    for each station of interest

    Parameters
    ----------
    IM: IM
        IM for which to compute
        the conditional IM distribution
    rupture: string
        The rupture of interest
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
    obs_site_filter_fn: callable
        Function that performs filtering on the distance
        between the site of interest and the available
        observation sites

        Use this to prevent global bias (wrt. to the empirical
        GMM) affecting the between-event term calculation

    Returns
    -------
    cond_df: dataframe
        Conditional lnIM distribution
        for each station of interest
    obs_df: series
        Observations data series
    obs_stations: dictionary
        A dictionary that constains
        the relevant observations stations
        for each site of interest as per the
        obs_site_filter_fn
    """
    int_stations = np.asarray(int_stations)

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

    print(f"Loading Observations")
    obs_df = pd.read_csv(observations_ffp, index_col=0, low_memory=False)
    obs_df = obs_df.loc[obs_df.evid == rupture]
    obs_df = obs_df.set_index("sta").sort_index()

    # Only need IM of interest
    obs_series = np.log(obs_df[str(IM)])
    del obs_df

    obs_stations = obs_series.index.values.astype(str)

    # Check that GMM data exists for all observed stations
    # Otherwise drop those stations
    mask = np.isin(obs_stations, gmm_params_df.index.values)
    if np.count_nonzero(~mask) > 0:
        print(
            f"Missing GMM parameters for (observation) stations:\n"
            f"{obs_stations[~mask]}\n\tDropping these stations"
        )
        obs_stations = obs_stations[mask]

    # Check that GMM data exists for all stations of interest
    # Otherwise drop them
    mask = np.isin(int_stations, gmm_params_df.index.values)
    if np.count_nonzero(~mask) > 0:
        print(
            f"Missing GMM parameters for sites of interest:\n"
            f"{int_stations[~mask]}\n\tDropping these stations"
        )
        int_stations = int_stations[mask]

    # Drop any sites of interest for which observations exists
    mask = np.isin(int_stations, obs_stations)
    if np.count_nonzero(mask) > 0:
        print(
            f"Observations exist for the following sites of interest:\n"
            f"{int_stations[mask]}\n\tDropping these stations"
        )
        int_stations = int_stations[~mask]

    # Relevant stations (Observation sites & Sites of interest)
    rel_stations = np.concatenate((int_stations, obs_stations))
    gmm_params_df = gmm_params_df.loc[rel_stations]

    print("Computing distance matrix")
    dist_matrix = calculate_distance_matrix(rel_stations, stations_df)

    print("Computing correlation matrix")
    R = get_corr_matrix(rel_stations, dist_matrix, IM)

    cond_df = pd.DataFrame(
        data=np.full((int_stations.shape[0], 2), np.nan),
        index=int_stations,
        columns=["mu", "sigma"],
    )
    obs_stations_used = {}
    for cur_station in int_stations:
        # Todo: Filtering of observations sites, to prevent "global" bias issues
        if obs_site_filter_fn is not None:
            raise NotImplementedError()
        else:
            obs_stations_used[cur_station] = cur_obs_stations = obs_stations

        cur_rel_sites = np.concatenate(([cur_station], cur_obs_stations))
        cur_cond_mu, cur_cond_sigma = sha.compute_cond_lnIM_dist(
            cur_station,
            gmm_params_df.loc[cur_rel_sites],
            obs_series.loc[cur_obs_stations],
            R.loc[cur_rel_sites, cur_rel_sites],
        )

        cond_df.loc[cur_station, ["mu", "sigma"]] = cur_cond_mu, cur_cond_sigma

    return cond_df, obs_series[obs_stations], obs_stations_used

def calculate_distance_matrix(stations: Sequence[str], locations_df: pd.DataFrame):
    """
    Given a set of stations and their locations (in lat, lon format),
    calculate the matrix containing
    the pairwise distance

    Parameters
    ----------
    stations: Sequence[str]
        List of the station names
    locations_df: pd.DataFrame
        Locations of each of the stations (in lat, lon)
    """
    distance_matrix = -1 * np.ones((len(stations), len(stations)))
    for i, station in enumerate(stations):
        cur_dist, _ = calc_rrup_rjb(
            np.asarray(
                [[locations_df.loc[station].lon, locations_df.loc[station].lat, 0]]
            ),
            np.stack(
                (
                    locations_df.loc[stations].lon,
                    locations_df.loc[stations].lat,
                    np.zeros(len(stations)),
                ),
                axis=1,
            ),
        )
        distance_matrix[i, :] = cur_dist
    return pd.DataFrame(index=stations, data=distance_matrix, columns=stations)


def get_corr_matrix(
    stations: Sequence[str], distance_matrix: pd.DataFrame, selected_im: gc.im.IM
):
    """
    Computes the correlation matrix for the specified stations
    using the Loth & Baker (2013) model.

    Parameters
    ----------
    stations: Sequence[str]
        List of the station names
    distance_matrix: pd.DataFrame
        Distance values between all site locations
    selected_im: IM
        IM to get correlations from the model
    """
    R = np.eye(len(stations))
    for i, station in enumerate(stations):
        correlation = sha.loth_baker_corr_model.get_correlations(
            str(selected_im),
            str(selected_im),
            distance_matrix.loc[stations, station].values,
        )
        assert np.all(
            correlation >= 0.0
        ), f"Correlation should be positive or 0. Error with {station} at index {i}"
        R[i, :] = R[:, i] = correlation

    # Make the diagonal values exactly 1.0
    assert np.all(np.isclose(np.diag(R), 1.0, rtol=1e-2))
    np.fill_diagonal(R, 1.0)

    return pd.DataFrame(index=stations, columns=stations, data=R)


def generate_im_values(
    N: int,
    R: pd.DataFrame,
    emp_df: pd.DataFrame,
):
    """
    Given a number of stations with their empirical values,
     create uncorrelated random values and then
    correlate them using the Cholesky decomposition
     of the correlation matrix (R).

    Parameters
    ----------
    N: int
        Number of realisations
    R: pd.Dataframe
        Correlation matrix (with unit variance) from
    emp_df: pd.Dataframe
        Empirical results with mu, between_event_sigma and within_event_sigma
    """
    mean_lnIM, between_event_std, within_event_std = (
        emp_df["mu"],
        emp_df["between_event_sigma"],
        emp_df["within_event_sigma"],
    )

    # Cholesky decomposition of the correlation matrix
    # Make positive definite if it isn't
    try:
        L = cholesky(R, lower=True)
    except np.linalg.LinAlgError:
        pd_R = sha.nearest_pd(R)
        L = cholesky(pd_R, lower=True)

    # Calculate random between event residual value
    #  per realisation and multiply by between event sigma
    between_event = (
        np.random.normal(0.0, 1.0, size=N)[:, np.newaxis]
        * between_event_std.values[np.newaxis, :]
    )

    # Calculate random within event residual value
    #  per site and per realisation
    # Then matrix multiply against the result of
    #  the Cholesky decomposition for each realisation
    within_event = np.matmul(
        L, np.random.normal(0.0, within_event_std, size=(N, len(within_event_std))).T
    ).T

    # Combine the between and within event values with
    #  the mean IM values broadcast across realisations
    im_values = mean_lnIM[None, :] + between_event + within_event

    return im_values, between_event, within_event
