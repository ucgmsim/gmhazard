import numpy as np
import pandas as pd


def compute_cond_lnIM_dist(
    station: str,
    gm_params_df: pd.DataFrame,
    obs_lnIM_series: pd.Series,
    R: pd.DataFrame,
):
    """
    Compues the lnIM distribution for a site of interest
        conditioned on observations (from the same event);
        with the marginal distribution given by a
        empirical GMMs

    Parameters
    ----------
    station: string
        Site of interest
    gmm_params_df: dataframe
        Dataframe that contains the empirical
        GMM model parameters for the site of interest
        and the observation sites

        Index must be the sites
            (Site of interest + Observation sites)
        Columns are [mu, sigma_total,
            sigma_between, sigma_within]
    obs_lnIM_series: series
        lnIM values at the observation sites
    R: dataframe
        Correlation matrix between the
        all relevant sites (site of interest +
        observation sites)

    Returns
    -------
    cond_lnIM_mu: float
        The conditional mean estimation of lnIM
        at the site of interest
    cond_lnIM_sigma
        The conditional sigma estimation of lnIM
        at the site of interest
    """
    obs_stations = obs_lnIM_series.index.values.astype(str)

    # Sanity checks
    assert np.all(np.isin(obs_stations, gm_params_df.index))
    assert station in gm_params_df.index and station not in obs_stations

    # Relevant stations (Observation sites & Sites of interest)
    rel_stations = np.concatenate(([station], obs_stations))
    gm_params_df = gm_params_df.loc[rel_stations]

    # Compute covariance matrix of within-event residuals
    # C_c(i,j) = rho_{i,j} * \delta_{W_i} * \delta_{W_j}
    # Equation 4 in Bradley 2014
    C_c = pd.DataFrame(
        data=np.einsum(
            "i, ij, j -> ij",
            gm_params_df.loc[obs_stations].sigma_within.values,
            R.loc[obs_stations, obs_stations].values,
            gm_params_df.loc[obs_stations].sigma_within.values,
        ),
        index=obs_stations,
        columns=obs_stations,
    )
    # Compute the inverse covariance matrix
    C_c_inv = np.linalg.inv(C_c)

    # Sanity check
    assert np.all(
        np.isclose(
            np.diag(C_c.values),
            gm_params_df.loc[obs_stations, "sigma_within"].values ** 2,
        )
    )

    # Compute the total residual
    total_residual = (
        obs_lnIM_series.loc[obs_stations] - gm_params_df.loc[obs_stations, "mu"]
    )

    if np.all(gm_params_df.sigma_between == 0):
        # Between-event residual is zero
        # when the GM parameters are computed
        # from simulation realisations
        between_residual = 0.0
    else:
        # Compute the between event-residual using the observation stations
        # First part of Equation 3 numerator is just row-wise sum of inverse C_c
        numerator = np.einsum("ki, i -> ", C_c_inv, total_residual)
        denom = np.sum(
            (1 / gm_params_df.loc[obs_stations].sigma_between.values ** 2)
            + np.sum(C_c_inv, axis=1)
        )
        between_residual = numerator / denom

    # Compute the within-event residual
    within_residual = total_residual - between_residual

    # Define the within-event residual distribution
    # Equation 5 in Bradley 2014
    within_residual_cov = np.full(
        (rel_stations.size, rel_stations.size), fill_value=np.nan
    )
    within_residual_cov[1:, 1:] = C_c
    within_residual_cov[0, 0:] = within_residual_cov[0:, 0] = (
        R.loc[rel_stations, station].values
        * gm_params_df.loc[station, "sigma_within"]
        * gm_params_df.loc[rel_stations, "sigma_within"].values
    )
    within_residual_cov = pd.DataFrame(
        data=within_residual_cov, index=rel_stations, columns=rel_stations
    )
    # Sanity check, diagonal terms are just sigma_within**2
    assert np.all(
        np.isclose(
            np.diag(within_residual_cov.values),
            gm_params_df.loc[rel_stations, "sigma_within"].values ** 2,
        )
    )

    # Define the conditional within-event distribution
    cond_within_residual_mu = np.einsum(
        "i, ij, j -> ",
        within_residual_cov.values[0, 1:],
        C_c_inv,
        within_residual.values,
    )
    cond_within_residual_sigma = np.sqrt(gm_params_df.loc[
        station, "sigma_within"
    ] ** 2 - np.einsum(
        "i, ij, j -> ",
        within_residual_cov.values[0, 1:],
        C_c_inv,
        within_residual_cov.values[1:, 0],
    ))

    # Define the conditional lnIM distriubtion
    cond_lnIM_mu = (
        gm_params_df.loc[station, "mu"] + between_residual + cond_within_residual_mu
    )
    cond_lnIM_sigma = cond_within_residual_sigma

    return cond_lnIM_mu, cond_lnIM_sigma
