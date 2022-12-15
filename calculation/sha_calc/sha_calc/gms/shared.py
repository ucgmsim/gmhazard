from typing import Union, Tuple, Sequence, List

import pandas as pd
import numpy as np
from scipy import stats
from numpy import linalg as la
from scipy.linalg import cholesky


def ks_critical_value(n_trials, alpha):
    return stats.ksone.ppf(1 - alpha / 2, n_trials)


def query_non_parametric_cdf_invs(
    y: np.ndarray, cdf_x: np.ndarray, cdf_y: np.ndarray
) -> np.ndarray:
    """Retrieve the x-values for the specified y-values given the
    non-parametric cdf function
    Note: Since this is for a discrete CDF,
    the inversion function returns the x value
    corresponding to F(x) >= y

    Parameters
    ----------
    y: array of floats
    cdf_x: array of floats
    cdf_y: array of floats
        The x and y values of the non-parametric cdf

    Returns
    -------
    y: array of floats
        The corresponding y-values
    """
    assert cdf_y[0] >= 0.0 and np.isclose(cdf_y[-1], 1.0, rtol=1e-2)
    assert np.all((y > 0.0) & (y < 1.0))

    mask, x = cdf_y >= y[:, np.newaxis], []
    return np.asarray(
        [cdf_x[np.min(np.flatnonzero(mask[ix, :]))] for ix in range(y.size)]
    )


def query_non_parametric_multi_cdf_invs(
    y: Sequence, cdf_x: np.ndarray, cdf_y: np.ndarray
) -> List:
    """Retrieve the x-values for the specified y-values given a
    multidimensional array of non-parametric cdf along each row
    Note: Since this is for a discrete CDF,
    the inversion function returns the x value
    corresponding to F(x) >= y

    Parameters
    ----------
    y: Sequence of floats
    cdf_x: 2d array of floats
    cdf_y: 2d array of floats
        The x and y values of the non-parametric cdf
        With each row representing one CDF

    Returns
    -------
    y: List
        The corresponding y-values
    """
    x_values = []
    for cur_y in y:
        diff = cdf_y - cur_y
        x_values.append(
            [
                cdf_x[ix, :][np.min(np.flatnonzero(diff[ix, :] > 0))]
                for ix in range(len(cdf_x))
            ]
        )
    return x_values


def query_non_parametric_cdf(
    x: np.ndarray, cdf_x: np.ndarray, cdf_y: np.ndarray
) -> np.ndarray:
    """Retrieve the y-values for the specified x-values given the
    non-parametric cdf function

    Parameters
    ----------
    x: array of floats
    cdf_x: array of floats
    cdf_y: array of floats
        The x and y values of the non-parametric cdf

    Returns
    -------
    y: array of floats
        The corresponding y-values
    """
    assert cdf_y[0] >= 0.0 and np.isclose(
        cdf_y[-1], 1.0, rtol=1e-2
    ), f"cdf_y[0] = {cdf_y[0]}, cdf_y[-1] = {cdf_y[-1]}"

    mask, y = cdf_x <= x[:, np.newaxis], []
    for ix in range(x.size):
        cur_ind = np.flatnonzero(mask[ix, :])
        y.append(cdf_y[np.max(cur_ind)] if cur_ind.size > 0 else 0.0)

    return np.asarray(y)


def __align_check_indices(
    df_1: Union[pd.DataFrame, pd.Series], df_2: Union[pd.DataFrame, pd.Series]
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Checks that the indices of the two dataframes match exactly,
    sorts the indices if required

    Raises exception if they don't match
    """
    if np.any(df_1.index != df_2.index):
        df_1.sort_index(inplace=True)
        df_2.sort_index(inplace=True)
        assert np.all(df_1.index == df_2.index), "The indices have to match"

    return df_1, df_2

def nearest_pd(A):
    """Find the nearest positive-definite matrix to input

    From stackoverflow:
    https://stackoverflow.com/questions/43238173/python-convert-matrix-to-positive-semi-definite

    A Python/Numpy port of John D'Errico's `nearestSPD` MATLAB code [1], which
    credits [2].

    [1] https://www.mathworks.com/matlabcentral/fileexchange/42885-nearestspd

    [2] N.J. Higham, "Computing a nearest symmetric positive semidefinite
    matrix" (1988): https://doi.org/10.1016/0024-3795(88)90223-6
    """
    B = (A + A.T) / 2
    _, s, V = la.svd(B)

    H = np.dot(V.T, np.dot(np.diag(s), V))

    A2 = (B + H) / 2

    A3 = (A2 + A2.T) / 2

    if is_pd(A3):
        return A3

    spacing = np.spacing(la.norm(A))
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
        mineig = np.min(np.real(la.eigvals(A3)))
        A3 += I * (-mineig * k ** 2 + spacing)
        k += 1

    return A3


def is_pd(B):
    """Returns true when input is positive-definite, via Cholesky"""
    try:
        _ = cholesky(B, lower=True)
        return True
    except la.LinAlgError:
        return False





