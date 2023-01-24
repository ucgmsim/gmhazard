import pickle
from pathlib import Path
from typing import Sequence, Callable, List, Dict, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.linalg import cholesky
from scipy.spatial import KDTree

import gmhazard_calc as gc
import sha_calc as sha
from IM_calculation.source_site_dist.src_site_dist import calc_rrup_rjb
from qcore import geo


@dataclass
class CondLnIMDistributionResult:
    """
    IM: gc.im.IM
        The IM for which this distribution is
    cond_lnIM_df: dataframe
        Conditional lnIM distribution
        for each station of interest
    obs_df: series
        Observations data series
    obs_stations: array of strings
        Array of the observation stations used
    obs_station_mask: dictionary
        A dictionary that contains
        a mask for the relevant observations
        stations for each site of interest
        as per the obs_site_filter_fn
    combined_df: dataframe
        Contains data for both the
        sites of interest and the
        observation sites (only the
        ones with gmm parameters)
    R: dataframe
        Correlation matrix
    """

    IM: gc.im.IM
    cond_lnIM_df: pd.DataFrame
    obs_stations: np.ndarray
    obs_series: pd.Series
    obs_stations_masks: Dict[str, np.ndarray]
    combined_df: pd.DataFrame

    R: pd.DataFrame

    def save(self, output_ffp: Path):
        with open(output_ffp, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(self, data_ffp: Path):
        with open(data_ffp, "rb") as f:
            return pickle.load(f)


def obs_site_filter(hypo_loc: Tuple[float, float], station_df: pd.DataFrame, int_stations: np.ndarray, obs_stations: np.ndarray, distance_matrix: pd.DataFrame):
    # Compute R_min for each site of interest
    src_site_dist = pd.Series(data=geo.get_distances(station_df.loc[int_stations, ["lon", "lat"]].values, hypo_loc[0], hypo_loc[1]), index=int_stations)
    r_min = src_site_dist * 1.5

    # Sanity check
    assert np.all(r_min.index == distance_matrix.loc[int_stations].index)

    r_min_mask = distance_matrix.loc[int_stations, obs_stations].values < r_min.values[:, np.newaxis]





    print(f"wtf")


def compute_cond_lnIM(
    IM: gc.im.IM,
    int_stations: np.ndarray,
    stations_df: pd.DataFrame,
    gmm_params_df: pd.DataFrame,
    obs_series: pd.Series,
    hypo_loc: Tuple[float, float],
    obs_site_filter_fn: Callable[[pd.DataFrame], List[str]] = obs_site_filter,
) -> CondLnIMDistributionResult:
    """
    Computes the conditional lnIM distribution
    for each station of interest

    Parameters
    ----------
    IM: IM
        IM for which to compute
        the conditional IM distribution
    int_stations: sequence of strings
        The stations of interest
    stations_df: dataframe
    gmm_params_df: dataframe
        Dataframe with empirical GMMs parameters

        Expects columns names
        [{IM}_mean, {IM}_std_Total, {IM}_std_Inter, {IM}_std_Intra]
    obs_series: series
        Observations IM values for each station
    hypo_loc: pair of floats
        The lon and lat value of the hypocentre
    obs_site_filter_fn: callable
        Function that performs filtering on the distance
        between the site of interest and the available
        observation sites

        Use this to prevent global bias (wrt. to the empirical
        GMM) affecting the between-event term calculation

    Returns
    -------
    CondLnIMDistributionResult
    """
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
    obs_series = obs_series.loc[obs_stations]

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

    print(
        f"Computing results for {int_stations.size} stations of interest, "
        f"with {obs_stations.size} observation stations available"
    )

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
    obs_station_mask = {}
    for cur_station in int_stations:
        # Todo: Filtering of observations sites, to prevent "global" bias issues
        if obs_site_filter_fn is not None:
            obs_site_filter_fn(hypo_loc, stations_df, int_stations, obs_stations, dist_matrix)
        else:
            obs_station_mask[cur_station] = cur_mask = np.ones(
                obs_stations.shape, dtype=bool
            )

        cur_rel_sites = np.concatenate(([cur_station], obs_stations[cur_mask]))
        cur_cond_mu, cur_cond_sigma = sha.compute_cond_lnIM_dist(
            cur_station,
            gmm_params_df.loc[cur_rel_sites],
            obs_series.loc[obs_stations[cur_mask]],
            R.loc[cur_rel_sites, cur_rel_sites],
        )

        cond_df.loc[cur_station, ["mu", "sigma"]] = cur_cond_mu, cur_cond_sigma

    # Combine into single data frame
    combined_df = pd.concat((cond_df, obs_series.to_frame("mu")), axis=0)
    combined_df["observation"] = False
    combined_df.loc[obs_stations, "observation"] = True
    combined_df.loc[obs_stations, "sigma"] = 0.0

    # Compute median
    combined_df["median"] = np.exp(combined_df.mu)

    return CondLnIMDistributionResult(
        IM, cond_df, obs_stations, obs_series, obs_station_mask, combined_df, R
    )


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
