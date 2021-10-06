from typing import Tuple

import numpy as np
import pandas as pd
from scipy import stats


def comp_weighted_corr_matrix(im_df: pd.DataFrame, alpha: pd.Series) -> pd.DataFrame:
    """
    Computes the weighted correlation matrix for all given IMs

    Parameters
    ----------
    im_df: pandas dataframe
        The IM values for each simulation
        Shape: [n_simulation, n_IMs]
    alpha: pandas series
        The normalized weights for each simulation

    Returns
    -------
    pandas dataframe
        The correlation matrix
        Shape: [n_ims, n_ims]
    """
    # Ensure same order
    im_df.sort_index(inplace=True)
    alpha.sort_index(inplace=True)

    # Sanity check
    assert np.all(im_df.index == alpha.index)

    # Compute the weighted covariance matrix
    cov_matrix = np.cov(np.log(im_df.values), rowvar=False, aweights=alpha.values)

    # Compute the denominator
    var_vector = cov_matrix[np.identity(cov_matrix.shape[0], dtype=bool)]
    denominator = np.sqrt(np.dot(var_vector.reshape(-1, 1), var_vector.reshape(1, -1)))

    # Compute the correlation matrix
    corr_matrix = cov_matrix / denominator

    return pd.DataFrame(data=corr_matrix, index=im_df.columns, columns=im_df.columns)


def comp_weighted_CDF(
    im_df: pd.DataFrame, alpha: pd.Series
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Computes the non-parametric marginal weighted CDF for each IM

    Parameters
    ----------
    im_df: pandas dataframe
        The IM values for each simulation
        Shape: [n_simulation, n_IMs]
    alpha: pandas series
        The normalized weights for each simulation

    Returns
    -------
    cdf_x: pandas dataframe
    cdf_y: pandas dataframe
        The x and y values for the cdf for each IM
        Shape: [n_simulations, n_IMs]
    """
    assert np.isclose(alpha.sum(), 1), "The weights have to be normalized"

    cdf_x, cdf_y = np.full(im_df.shape, np.nan), np.full(im_df.shape, np.nan)
    for ix, cur_im in enumerate(im_df.columns):
        # Get the current data
        cur_x = im_df[cur_im]
        cur_weights = alpha.loc[cur_x.index]

        # Compute weighted cdf
        sort_ind = np.argsort(cur_x)
        cdf_x[:, ix], cdf_y[:, ix] = cur_x[sort_ind], np.cumsum(cur_weights[sort_ind])

    cdf_x = pd.DataFrame(data=cdf_x, columns=im_df.columns)
    cdf_y = pd.DataFrame(data=cdf_y, columns=im_df.columns)
    return cdf_x, cdf_y


def comp_kernel_weights(
    IMj_series: pd.DataFrame, im_j: float, sigma_lnIMj: float = 0.05, std_th: float = 3
) -> pd.Series:
    """
    Computes the kernel weights for each simulation using a lognormal
    distribution with mu = log(im_j) and sigma = sigma_lnIMj

    Parameters
    ----------
    IMj_series: pandas series
        Series with the IM_j values for each simulation
    im_j: float
        The IM
    sigma_lnIMj: float
        The standard deviation limit at which weights are set to zero
        Set to None for no threshold

    Returns
    -------
    weights: pandas series
        The weights for each simulation
    """
    n_sigmas = (np.log(IMj_series) - np.log(im_j)) / sigma_lnIMj

    weights = stats.norm.pdf(n_sigmas)
    if std_th is not None:
        weights[np.abs(n_sigmas) > std_th] = 0

    return pd.Series(data=weights, index=n_sigmas.index)
