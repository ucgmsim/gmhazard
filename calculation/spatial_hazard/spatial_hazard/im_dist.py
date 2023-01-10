from typing import Sequence

import numpy as np
import pandas as pd
from scipy.linalg import cholesky

import gmhazard_calc as gc
import sha_calc
from IM_calculation.source_site_dist.src_site_dist import calc_rrup_rjb


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
        correlation = sha_calc.spatial_hazard.loth_baker_model.get_correlations(
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
        pd_R = sha_calc.nearest_pd(R)
        L = cholesky(pd_R, lower=True)

    # Calculate random between event residual value
    #  per realisation and multiply by between event sigma
    between_event = (
        np.random.normal(0.0, 1.0, size=N)[:, np.newaxis] * between_event_std.values[np.newaxis, :]
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
