from typing import Union, Tuple

import pandas as pd
import numpy as np
from scipy import stats


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
    assert cdf_y[0] >= 0.0 and np.isclose(cdf_y[-1], 1.0, rtol=1e-2)

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
