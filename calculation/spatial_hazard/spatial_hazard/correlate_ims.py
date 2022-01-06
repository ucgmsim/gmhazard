from typing import Sequence

import numpy as np
import pandas as pd
from scipy.linalg import cholesky

import gmhazard_calc as gc
from spatial_hazard import models
from IM_calculation.source_site_dist.src_site_dist import calc_rrup_rjb


def load_stations_data(imdb_ffps: Sequence[str], stations: Sequence[str], im: gc.im.IM):
    """Loads the IM data for the specified stations from the IMDBs"""
    result_dict = {station: [] for station in stations}
    for imdb_ffp in imdb_ffps:
        print("Getting {}".format(imdb_ffp))
        with gc.dbs.IMDB.get_imdb(imdb_ffp, writeable=False) as imdb:
            imdb_stations = imdb.sites().index
            for station in stations:
                if station not in imdb_stations:
                    print("Station {} has no entries here".format(station))
                cur_data = imdb.im_data(station, im)
                if cur_data is not None:
                    result_dict[station].append(cur_data)

    result_dict = {key: pd.concat(value) for key, value in result_dict.items()}
    return result_dict


def load_stations_fault_data(
    imdb_ffps: Sequence[str], stations: Sequence[str], im: gc.im.IM, fault: str
):
    """Loads the IM data for the specified stations and fault from the IMDBs"""
    stations_data = load_stations_data(imdb_ffps, stations, im)

    return pd.DataFrame(
        {
            cur_station: cur_df.loc[fault].to_dict()
            for cur_station, cur_df in stations_data.items()
        }
    ).T


def calculate_distance_matrix(
    stations: Sequence[str], locations_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Given a set of stations and their locations (in lat, lon format), calculate the matrix containing
    the pairwise distance between each one

    Parameters
    ----------
    stations: List[str]
        List of the stations
    locations_df: pd.DataFrame
        Locations of each of the stations (in lat, lon)

    Returns
    -------

    """
    distance_matrix = -np.ones((len(stations), len(stations)))
    for i, station_1 in enumerate(stations):
        cur_dist, _ = calc_rrup_rjb(
            np.asarray(
                [[locations_df.loc[station_1].lon, locations_df.loc[station_1].lat, 0]]
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


def get_corr_matrix(stations, distance_matrix, selected_im, emp_df):
    """
    Computes the correlation matrix for the specified stations
    using the Loth & Baker (2013) model.

    Parameters
    ----------
    stations: sequence of strings
    distance_matrix: dataframe
    selected_im: IM
    emp_df: dataframe

    Returns
    -------
    R: dataframe
        The correlation matrix of the given station
    """
    assert np.all(
        distance_matrix.index.values == emp_df.index.values
    ), "Order of the stations has to be the same"

    # Compute correlation matrix
    R = np.eye(len(stations))
    for i, station_i in enumerate(stations):
        correlation = models.loth_baker_model.get_correlations(
            str(selected_im),
            str(selected_im),
            distance_matrix.loc[stations, station_i].values,
        )
        assert np.all(
            correlation >= 0.0
        ), "Correlation should be positive or 0. Error with {}, {}".format(i, station_i)
        R[i, :] = R[:, i] = correlation

    R = pd.DataFrame(index=stations, columns=stations, data=R)
    return R


def create_random_fields(
    N: int,
    R: pd.DataFrame,
    stations: Sequence[str],
    emp_df: pd.DataFrame,
):
    """
    Given a set of stations, create uncorrelated random values and then
    correlate them using the Cholesky decomposition of the correlation matrix (R).

    Parameters
    ----------
    N: int
        Number of realisations
    R: dataframe
        Correlation matrix (with unit variance) from
    stations: list of strings
    emp_df: dataframe
    """
    mean_lnIM, between_event_std, within_event_std = (
        emp_df["mu"],
        emp_df["sigma_inter"],
        emp_df["sigma_intra"],
    )

    # Decompose the covariance matrix
    # L = np.linalg.cholesky(nearest_pd(R))

    # Cholesky decomposition of the correlation matrix
    # Make positive definite if it isn't
    try:
        L = cholesky(R, lower=True)
    except np.linalg.LinAlgError:
        pd_R = nearest_pd(R)
        L = cholesky(pd_R, lower=True)

    random_IMs = np.zeros((N, len(stations)))
    between_event = np.zeros((N, len(stations)))
    within_event = np.zeros((N, len(stations)))

    for i in range(N):
        # Compute one single between event for everyone
        normalized_between_event = np.random.normal(0.0, 1.0)
        between_event_term = normalized_between_event * between_event_std

        # correlate the within event term using L (Box-Muller)
        within_event_term = np.matmul(L, np.random.normal(0.0, within_event_std))

        # We now have a perturbated mean field
        IM = mean_lnIM + between_event_term + within_event_term

        # Add it to the list
        random_IMs[i, :] = IM
        between_event[i, :] = between_event_term
        within_event[i, :] = within_event_term

    return random_IMs, between_event, within_event


def nearest_pd(A):
    """Find the nearest positive-definite matrix to input

    A Python/Numpy port of John D'Errico's `nearestSPD` MATLAB code [1], which
    credits [2].

    [1] https://www.mathworks.com/matlabcentral/fileexchange/42885-nearestspd

    [2] N.J. Higham, "Computing a nearest symmetric positive semidefinite
    matrix" (1988): https://doi.org/10.1016/0024-3795(88)90223-6
    """
    B = (A + A.T) / 2
    _, s, V = np.linalg.svd(B)

    H = np.dot(V.T, np.dot(np.diag(s), V))

    A2 = (B + H) / 2

    A3 = (A2 + A2.T) / 2

    if is_pd(A3):
        return A3

    spacing = np.spacing(np.linalg.norm(A))
    # The above is different from [1]. It appears that MATLAB's `chol` Cholesky
    # decomposition will accept matrixes with exactly 0-eigenvalue, whereas
    # Numpy's will not. So where [1] uses `eps(mineig)` (where `eps` is Matlab
    # for `np.spacing`), we use the above definition. CAVEAT: our `spacing`
    # will be much larger than [1]'s `eps(mineig)`, since `mineig` is usually on
    # the order of 1e-16, and `eps(1e-16)` is on the order of 1e-34, whereas
    # `spacing` will, for Gaussian random matrixes of small dimension, be on
    # othe order of 1e-16. In practice, both ways converge, as the unit test
    # below suggests.
    I = np.eye(A.shape[0])
    k = 1
    while not is_pd(A3):
        mineig = np.min(np.real(np.linalg.eigvals(A3)))
        A3 += I * (-mineig * k ** 2 + spacing)
        k += 1

    return A3


def is_pd(B):
    """Returns true when input is positive-definite, via Cholesky"""
    try:
        _ = cholesky(B, lower=True)
        return True
    except np.linalg.LinAlgError:
        return False
