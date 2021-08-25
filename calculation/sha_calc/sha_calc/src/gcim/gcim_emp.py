"""Contains functions for computation of the empirically GMM (i.e. parametric) based GCIM"""

from typing import Dict, Sequence, Union, Tuple

import pandas as pd
import numpy as np
from scipy import stats

import sha_calc.src.disagg as disagg
import sha_calc.src.ground_motion as gm
from . import distributions as dist
from . import im_correlations


def compute_rupture_weights(
    im_j: float,
    branch_data: Dict[str, Tuple[pd.DataFrame, pd.Series]],
    im_j_delta: float = 0.001,
) -> pd.Series:
    """Computes the ruptures weights for IMj=imj
    as per equation (7) in Bradley (2010), "A generalized conditional
    intensity measure approach and holistic ground-motion selection"

    Parameters
    ----------
    im_j: float
        The conditioning IMj level for which to compute
        the rupture weights
    branch_data: dictionary
        The IM parameters (i.e. mu and sigma) and
        annual rupture probabilities for each branch
        of the logic tree
    im_j_delta: float
        The small increment im_j used
        Default value should be appropriate in mose cases

    Returns
    -------
    series
        Contribution weights (values) of each rupture (index) for IMj=imj
    """
    P_Rup_IMj = None
    for branch_name, (cur_IMj_df, cur_annual_rec_prob) in branch_data.items():
        # Compute the rupture weights via disagg (equal)
        cur_P_Rup_IMj = disagg.disagg_equal(
            gm.parametric_gm_excd_prob(im_j, cur_IMj_df).squeeze(),
            gm.parametric_gm_excd_prob(im_j + im_j_delta, cur_IMj_df).squeeze(),
            cur_annual_rec_prob,
        )
        cur_P_Rup_IMj = cur_P_Rup_IMj.to_frame(branch_name)

        P_Rup_IMj = (
            cur_P_Rup_IMj
            if P_Rup_IMj is None
            else pd.merge(
                P_Rup_IMj, cur_P_Rup_IMj, how="outer", right_index=True, left_index=True
            )
        )

    # Set any missing ruptures to 0
    P_Rup_IMj[P_Rup_IMj.isna()] = 0.0

    return P_Rup_IMj


def comb_lnIMi_IMj(lnIMi_IMj: Dict[str, dist.Uni_lnIMi_IMj], weights: pd.Series):
    """
    Combines multiple marginal (univariate) lnIMi|IMj distributions
    according to the given weights

    Parameters
    ----------
    lnIMi_IMj: dictionary
        The univariate marginal lnIMi|IMj distributions to
        combine. Keys of the dictionary have to exist in
        the weights series (index)
    weights: series
        The weights of the different distributions
        to combine. Have to sum to 1.0

    Returns
    -------
    Uni_lnIMi_IMj:
        The combined distribution
    """
    # Sanity check
    ref_lnIMi_IMj = next(iter(lnIMi_IMj.values()))
    assert all([cur_dist.compatible(ref_lnIMi_IMj) for cur_dist in lnIMi_IMj.values()])
    assert np.isclose(weights.sum(), 1.0, rtol=1e-3)

    branch_names = np.asarray(list(lnIMi_IMj.keys()))
    branch_mu_IMi_IMj = pd.Series(
        index=branch_names,
        data=[lnIMi_IMj[cur_name].mu for cur_name in branch_names],
        name="mu_IMi_IMj",
    )
    sigma_IMi_IMj_df = pd.Series(
        index=branch_names,
        data=[lnIMi_IMj[cur_name].sigma for cur_name in branch_names],
        name="sigma_IMi_IMj",
    )

    # Compute the combined mu and sigma
    mu_IMi_IMj = branch_mu_IMi_IMj.multiply(weights, axis=0).sum(axis=0)
    sigma_IMi_IMj = np.sqrt(
        (
            (
                (sigma_IMi_IMj_df ** 2) + ((branch_mu_IMi_IMj - mu_IMi_IMj) ** 2)
            ).multiply(weights, axis=0)
        ).sum(axis=0)
    )

    # Compute the IM values for +/- sigma
    z = np.linspace(-3, 3, 1000)
    cdf_x = pd.Series(
        data=np.exp(mu_IMi_IMj + sigma_IMi_IMj * z),
        name="cdf_x",
    )
    cdf_y = pd.Series(data=np.zeros(cdf_x.shape[0]), name="cdf_y")
    for cur_name, cur_lnIMi_IMj in lnIMi_IMj.items():
        cdf_y += (
            np.interp(
                cdf_x,
                cur_lnIMi_IMj.cdf.index.values,
                cur_lnIMi_IMj.cdf.values,
                left=0,
                right=1.0,
            )
            * weights[cur_name]
        )

    return dist.Uni_lnIMi_IMj(
        pd.Series(index=cdf_x.values, data=cdf_y.values),
        ref_lnIMi_IMj.IMi,
        ref_lnIMi_IMj.IMj,
        ref_lnIMi_IMj.im_j,
    )


def compute_lnIMi_IMj(
    uni_lnIMi_IMj_Rup: Dict[str, dist.Uni_lnIMi_IMj_Rup],
    P_Rup_IMj: pd.Series,
    IMj: str,
    im_j: float,
) -> Dict[str, dist.Uni_lnIMi_IMj]:
    """Computes the marginal (univariate)
    distribution lnIMi|IMj for each IMi

    Parameters
    ----------
    uni_lnIMi_IMj_Rup: dictionary
        The conditional univariate distribution lnIMi|IMj,Rup (value)
        for each IMi (key)
    P_Rup_IMj: series
        The rupture probability given IMj=im_j
    IMj: str
    im_j: float
        The conditioning IM name and value

    Returns
    -------
    dictionary of Uni_lnIMi_IMj (with IMi as key)
        The non-parametric target distribution lnIMi|IMj
        for each IMi
    """
    IMs = np.asarray(list(uni_lnIMi_IMj_Rup.keys()))
    mu_lnIMi_IMj_Rup, sigma_lnIMi_IMj_Rup = dist.Uni_lnIMi_IMj_Rup.combine(
        uni_lnIMi_IMj_Rup
    )

    # Sanity checks
    assert np.all(P_Rup_IMj.index.values == mu_lnIMi_IMj_Rup.index.values)

    # Compute the mean and sigma of the GCIMs
    # Note: These are only computed to determine the IM values of the non-parametric CDF
    mu_IMi_IMj = mu_lnIMi_IMj_Rup.multiply(P_Rup_IMj, axis=0).sum(axis=0)
    sigma_IMi_IMj = np.sqrt(
        (
            (
                (sigma_lnIMi_IMj_Rup ** 2) + ((mu_lnIMi_IMj_Rup - mu_IMi_IMj) ** 2)
            ).multiply(P_Rup_IMj, axis=0)
        ).sum(axis=0)
    )

    # Compute the CDF of the target distribution IMi|IMj between +/- 3 standard deviations for each IMi
    # As we are summing lognormal conditional distributions, the target distribution IMi|IMj
    # is not lognormal, hence it is computed as a non-parametric CDF
    z = np.linspace(-3, 3, 1000)
    # Compute the IM values for +/- sigma for each GCIM (i.e. f_IMi|IMj)
    cdf_x = np.exp(
        mu_IMi_IMj.loc[IMs].values
        + sigma_IMi_IMj.loc[IMs].values[np.newaxis, :] * z[:, np.newaxis]
    )
    cdf_y = np.full((z.size, IMs.size), np.nan)
    for ix, cur_z in enumerate(z):
        # Compute the corresponding z-value for the
        # f_IMi|Rup,IMj distributions for each rupture
        cur_z_IMi_Rup_IMj = (
            np.log(cdf_x[ix]) - mu_lnIMi_IMj_Rup.loc[:, IMs]
        ) / sigma_lnIMi_IMj_Rup.loc[:, IMs]

        # Compute the CDF, assumes that
        # IMi|IMj, Rup distributions are lognormal
        cdf_y[ix, :] = np.sum(
            stats.norm.cdf(cur_z_IMi_Rup_IMj) * P_Rup_IMj.values[:, np.newaxis], axis=0
        )

    cdf_x = pd.DataFrame(data=cdf_x, columns=IMs)
    cdf_y = pd.DataFrame(data=cdf_y, columns=IMs)
    assert np.all(~np.isnan(cdf_y))

    return {
        IMi: dist.Uni_lnIMi_IMj(
            pd.Series(index=cdf_x[IMi], data=cdf_y[IMi].values, name=IMi),
            IMi,
            IMj,
            im_j,
            mu=mu_IMi_IMj[IMi],
            sigma=sigma_IMi_IMj[IMi],
        )
        for IMi in IMs
    }


def compute_lnIMi_IMj_Rup(
    mu_lnIMi_Rup: pd.DataFrame,
    sigma_lnIMi_Rup: pd.DataFrame,
    corr_coeff: pd.Series,
    IMj: str,
    im_j: float,
) -> Dict[str, dist.Uni_lnIMi_IMj_Rup]:
    """Computes the univariate lnIMi|IMj,Rup distribution
     for each IMi using vectorization

    Parameters
    ----------
    mu_lnIMi_Rup, sigma_lnIMi_Rup: dataframe
        The mean and sigma value
        for each rupture and lnIMi

        Both indices and columns have to
        match across the dataframes

        format: index = rupture, columns = IMi
    corr_coeff: series
        The correlation coefficient
        for each lnIMi and lnIMj pair
        format: index = IMi
    IMj: string
    im_j: float
        The conditioning IM name & value

    Returns
    -------
    dictionary of Uni_lnIMi_IMj_Rup
    """
    assert np.all(mu_lnIMi_Rup.columns == sigma_lnIMi_Rup.columns)
    assert np.all(mu_lnIMi_Rup.index.values == sigma_lnIMi_Rup.index.values)

    mu_IMi_IMi_Rup, sigma_IMi_IMj_Rup = __compute_lnIMi_IMj_Rup_params(
        mu_lnIMi_Rup, sigma_lnIMi_Rup, corr_coeff, im_j
    )

    return {
        cur_im: dist.Uni_lnIMi_IMj_Rup(
            mu_IMi_IMi_Rup[cur_im], sigma_IMi_IMj_Rup[cur_im], cur_im, IMj, im_j
        )
        for cur_im in mu_lnIMi_Rup.columns
    }


def compute_lnIMi_IMj_Rup_single(
    mu_lnIMi_Rup: pd.Series,
    sigma_lnIMi_Rup: pd.Series,
    corr_coeff: float,
    IMi: str,
    IMj: str,
    im_j: float,
) -> dist.Uni_lnIMi_IMj_Rup:
    """Computes the univariate lnIMi|IMj,Rup distribution
    for a single IMi

    Parameters
    ----------
    mu_lnIMi_Rup, sigma_lnIMi_Rup: series
        The mean and sigma value
        for lnIMi|Rup for each rupture
        Generally retrieved from a GMM
    corr_coeff: float
        The correlation coefficient
        for lnIMi and lnIMj
    im_j: float
        The conditioning IM value

    Returns
    -------
    Uni_lnIMi_IMj_Rup
    """
    assert np.all(mu_lnIMi_Rup.index == sigma_lnIMi_Rup.index)

    mu_IMi_IMi_Rup, sigma_IMi_IMj_Rup = __compute_lnIMi_IMj_Rup_params(
        mu_lnIMi_Rup, sigma_lnIMi_Rup, corr_coeff, im_j
    )

    return dist.Uni_lnIMi_IMj_Rup(mu_IMi_IMi_Rup, sigma_IMi_IMj_Rup, IMi, IMj, im_j)


def __compute_lnIMi_IMj_Rup_params(
    mu_lnIMi_Rup: Union[pd.Series, pd.DataFrame],
    sigma_lnIMi_Rup: Union[pd.Series, pd.DataFrame],
    corr_coeff: Union[float, pd.Series],
    im_j: float,
):
    """Helper function, computes mu and sigma for the
    conditional (univariate) lnIMi|IMj,Rup distribution
    as per equations (10) and (11) in Bradley (2010),
    "A generalized conditional intensity measure approach
    and holistic ground-motion selection"
    """
    epsilon_IMj_Rup = (np.log(im_j) - mu_lnIMi_Rup) / sigma_lnIMi_Rup
    mu_IMi_IMi_Rup = mu_lnIMi_Rup + (sigma_lnIMi_Rup * corr_coeff).multiply(
        epsilon_IMj_Rup, axis=0
    )
    sigma_IMi_IMj_Rup = sigma_lnIMi_Rup * np.sqrt(1 - np.power(corr_coeff, 2))

    return mu_IMi_IMi_Rup, sigma_IMi_IMj_Rup


def get_multi_IM_IMj_Rup(
    uni_lnIMi_IMj_Rup: Dict[str, dist.Uni_lnIMi_IMj_Rup], IMj: str, im_j: float
) -> dist.Multi_lnIM_IMj_Rup:
    """Computes the correlation matrix and creates
    the multivariate lognormal IM|IMj,Rup distribution

    Parameters
    ----------
    uni_lnIMi_IMj_Rup: dictionary
        The univariate lnIMi|IMj,Rup
        distributions (value) per IMi (key)
    IMj: string
    im_j: float
        Conditioning IM name and value

    Returns
    -------
    Multi_lnIM_IMj_Rup
    """

    IMs = np.asarray(list(uni_lnIMi_IMj_Rup.keys()))

    # Compute the correlation matrix
    rho = compute_rho(IMs, IMj)

    # Combine mu and sigma values into a dataframe
    mu_df, sigma_df = dist.Uni_lnIMi_IMj_Rup.combine(uni_lnIMi_IMj_Rup)

    return dist.Multi_lnIM_IMj_Rup(mu_df, sigma_df, rho, IMs, IMj, im_j)


def compute_rho(IMs: Sequence[str], IMj: str) -> pd.DataFrame:
    """Computes the correlation matrix rho_lnIM|Rup,IMj as defined by equation (7)
    in "Bradley, B.A., 2012. A ground motion selection algorithm based on
    the generalized conditional intensity measure approach."

    Note this code can be optimized as the matrix is symmetric and the
    current implementation computes every entry.

    Parameters
    ----------
    IMs: numpy array of strings
        The IMs of interest
    IMj: str
        The conditioning IM

    Returns
    -------
    dataframe
        The correlation matrix
    """
    rho = np.full((len(IMs), len(IMs)), np.nan)
    for i, IM_i in enumerate(IMs):
        rho_i_j = im_correlations.get_im_correlations(IM_i, IMj)
        for j, IM_k in enumerate(IMs):
            rho_k_j = im_correlations.get_im_correlations(IM_k, IMj)
            rho_i_k = im_correlations.get_im_correlations(IM_i, IM_k)
            rho[i, j] = rho[j, i] = (rho_i_k - (rho_i_j * rho_k_j)) / (
                np.sqrt(1 - rho_i_j ** 2) * np.sqrt(1 - rho_k_j ** 2)
            )

    assert np.all(~np.isnan(rho))
    return pd.DataFrame(index=IMs, columns=IMs, data=rho)


def compute_correlation_matrix(IMs: np.ndarray, IM_j: str) -> pd.DataFrame:
    """Computes the correlation matrix rho_lnIM|Rup,IMj as defined by equation (7)
    in "Bradley, B.A., 2012. A ground motion selection algorithm based on
    the generalized conditional intensity measure approach."

    Note this code can be optimized as the matrix is symmetric and the
    current implementation computes every entry.

    Parameters
    ----------
    IMs: numpy array of strings
        The IMs of interest
    IM_j: str
        The conditioning IM

    Returns
    -------
    dataframe
        The correlation matrix
    """
    rho = np.full((IMs.size, IMs.size), np.nan)
    for i, IM_i in enumerate(IMs):
        rho_i_j = im_correlations.get_im_correlations(IM_i, IM_j)
        for j, IM_k in enumerate(IMs):
            rho_k_j = im_correlations.get_im_correlations(IM_k, IM_j)
            rho_i_k = im_correlations.get_im_correlations(IM_i, IM_k)
            rho[i, j] = rho[j, i] = (rho_i_k - (rho_i_j * rho_k_j)) / (
                np.sqrt(1 - rho_i_j ** 2) * np.sqrt(1 - rho_k_j ** 2)
            )

    assert np.all(~np.isnan(rho))
    return pd.DataFrame(index=IMs, columns=IMs, data=rho)
