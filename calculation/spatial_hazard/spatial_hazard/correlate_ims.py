from typing import Sequence

import numpy as np
import pandas as pd
from scipy.linalg import cholesky

import gmhazard_calc as gc
import sha_calc
from IM_calculation.source_site_dist.src_site_dist import calc_rrup_rjb


def load_stations_fault_data(
    imdb_ffps: Sequence[str], stations: Sequence[str], im: gc.im.IM, fault: str
):
    """
    Loads the IM data for the specified stations and fault from the IMDBs

    Parameters
    ----------
    imdb_ffps: Sequence[str]
        List of imdb full file paths to load
    stations: Sequence[str]
        List of stations to grab data for from the imdbs
    im: IM
        IM Object to extract values from the imdb
    fault: String
        Fault name to extract data from the imdb
    """
    # Obtain the given IMDB with the correct fault information
    fault_imdbs = []
    for imdb_ffp in imdb_ffps:
        with gc.dbs.IMDB.get_imdb(imdb_ffp, writeable=False) as imdb:
            if fault in imdb._ruptures().values:
                fault_imdbs.append(imdb_ffp)
    # Ensure only 1 IMDB has the given fault data
    assert len(fault_imdbs) == 1

    # Extract rupture data from imdb for each station and combine to a DataFrame
    site_rupture_data = []
    with gc.dbs.IMDB.get_imdb(fault_imdbs[0], writeable=False) as imdb:
        for station in stations:
            cur_data = imdb.im_data(station, im, incl_inter_intra=True)
            # Check fault data was found
            assert cur_data is not None
            site_rupture_data.append(cur_data.loc[fault])
    return pd.DataFrame(site_rupture_data, index=stations)


def calculate_distance_matrix(stations: Sequence[str], locations_df: pd.DataFrame):
    """
    Given a set of stations and their locations (in lat, lon format), calculate the matrix containing
    the pairwise distance between each one

    Parameters
    ----------
    stations: Sequence[str]
        List of the stations
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
        List of the stations
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
        ), f"Correlation should be positive or 0. Error with {i}, {station}"
        R[i, :] = R[:, i] = correlation

    return pd.DataFrame(index=stations, columns=stations, data=R)


def create_random_fields(
    N: int,
    R: pd.DataFrame,
    n_stations: int,
    emp_df: pd.DataFrame,
):
    """
    Given a number of stations with their empirical values, create uncorrelated random values and then
    correlate them using the Cholesky decomposition of the correlation matrix (R).

    Parameters
    ----------
    N: int
        Number of realisations
    R: pd.Dataframe
        Correlation matrix (with unit variance) from
    n_stations: int
        Number of stations
    emp_df: pd.Dataframe
        Empirical results with mu, sigma_inter and sigma_intra
    """
    mean_lnIM, between_event_std, within_event_std = (
        emp_df["mu"],
        emp_df["sigma_inter"],
        emp_df["sigma_intra"],
    )

    # Cholesky decomposition of the correlation matrix
    # Make positive definite if it isn't
    try:
        L = cholesky(R, lower=True)
    except np.linalg.LinAlgError:
        pd_R = sha_calc.nearest_pd(R)
        L = cholesky(pd_R, lower=True)

    # Calculate random between event residual value per realisation and multiply by between event sigma
    between_event = (
        np.random.normal(0.0, 1.0, size=N)[:, None] * between_event_std[None, :]
    )

    # Calculate random within event residual value per site and per realisation
    # Calculate random within event residual value per site and per realisation
    # Then matrix multiply against the result of the Cholesky decomposition for each realisation
    within_event = np.matmul(
        L, np.random.normal(0.0, within_event_std, size=(N, n_stations)).T
    ).T

    # Combine the between and within event values with the mean IM values broadcast across realisations
    im_values = mean_lnIM[None, :] + between_event + within_event

    return im_values, between_event, within_event
