import pandas as pd
import numpy as np
import scipy.stats as stats

from sha_calc.src.hazard import hazard_single


def disagg_equal(gm_prob: pd.Series, gm_prob_delta: pd.Series, rec_prop: pd.Series):
    # Calculate exceedance probability (hazard)
    excd_prob = hazard_single(gm_prob, rec_prop)
    excd_prob_delta = hazard_single(gm_prob_delta, rec_prop)

    excd_prob_diff = excd_prob - excd_prob_delta

    excd_disagg = disagg_exceedance(gm_prob, rec_prop, excd_prob)
    excd_disagg_delta = disagg_exceedance(gm_prob_delta, rec_prop, excd_prob_delta)

    return (1 / excd_prob_diff) * (
        excd_disagg * excd_prob - excd_disagg_delta * excd_prob_delta
    )


def disagg_exceedance(
    gm_prob: pd.Series, rec_prob: pd.Series, excd_prob: float = None
) -> pd.Series:
    """Calculates the contribution for each rupture for exceeding
     the specified IM level (implicitly defined via gm_prob)

    Note: All ruptures specified in gm_prob have to exist
    in rec_prob

    Parameters
    ----------
    gm_prob: pd.Series
        The ground motion probabilities
        format: index = rupture_id, values = probability
    rec_prob: pd.Series
        The recurrence probabilities of the ruptures
        format: index = rupture_id, values = probability
    excd_prob: float, optional
        The exceedance probability to use for the calculation
        Is calculated from the passed in data, however
        this will not be correct if only for example
        the fault portion of the data is passed in.

    Returns
    -------
    pd.Series
        Contribution per rupture
        format: index = rupture_name, values = contribution
    """
    # Calculate the exceedance probability if not passed
    if excd_prob is None:
        excd_prob = hazard_single(gm_prob, rec_prob)

    # Calculate the contribution of each rupture
    ruptures = gm_prob.index.values
    return (gm_prob[ruptures] * rec_prob[ruptures]) / excd_prob


def disagg_exceedance_multi(
    gm_prob_df: pd.DataFrame, rec_prob: pd.Series, excd_prob: pd.Series
) -> pd.DataFrame:
    """Calculates the contribution for each rupture for
     exceeding the specified IM levels (implicitly defined via gm_prob)

    Note: All ruptures specified in gm_prob have to exist
    in rec_prob

    Parameters
    ----------
    gm_prob_df: pd.DataFrame
        The ground motion probabilities for each IM level
        format: index = rupture_id, columns = IM levels
    rec_prob: pd.Series
        The recurrence probabilities of the ruptures
        format: index = rupture_id, values = probability
    excd_prob: pd.Series
        The exceedance probability for each IM level
        format: index = IM level, values = exceedance probability

    Returns
    -------
    pd.DataFrame
        Contribution per rupture at each IM level
        format: index = rupture_name, columns = IM level
    """
    # Sanity check that the IM values match up
    assert np.all(np.isclose(gm_prob_df.columns.values, excd_prob.index.values))

    ruptures = gm_prob_df.index.values
    return (
        gm_prob_df.loc[ruptures].multiply(rec_prob.loc[ruptures], axis=0)
        / excd_prob.values
    )


def epsilon_para(gm_params_df: pd.DataFrame, gm_prob: pd.Series) -> pd.Series:
    """
    Computes epsilon for the specified ruptures for IM values
    that have a lognormal distribution

    Parameters
    ----------
    gm_params_df: pandas dataframe
        The parameters of the distribution, where
        mu and sigma are the mean and std (of the normal distribution)
        format: index = rupture_id, columns = [mu, sigma]
    gm_prob: pd.Series
        The ground motion probabilities
        format: index = rupture_id, values = probability

    Returns
    -------
    pd.Series
        The epsilon values for each rupture
        format: index = rupture_id, values = epsilon values
    """
    ruptures = list(set(gm_params_df.index.values) & set(gm_prob.index.values))
    mu, sigma = gm_params_df.mu.loc[ruptures], gm_params_df.sigma.loc[ruptures]
    epsilon_values = (stats.norm.ppf(1 - gm_prob.loc[ruptures], mu, sigma) - mu) / sigma
    return pd.Series(index=ruptures, data=epsilon_values)


def epsilon_non_para_single(im_values: np.ndarray, gm_prob: float) -> float:
    """
    Computes epsilon for a single rupture from a
    non-parametric distribution

    Parameters
    ----------
    im_values: float array
        Array of the IM values
    gm_prob: float
        The probability of exceedance for the current rupture,
        i.e. P(IM > im | rup_i)

    Returns
    -------
    float
        epsilon value
    """
    # Get the cdf
    quantiles, counts = np.unique(im_values, return_counts=True)
    ecdf = np.cumsum(counts).astype(np.float) / im_values.size

    # Get the IM value using linear interpolation
    if ecdf.min() <= (1 - gm_prob) <= ecdf.max():
        im_value = float(np.interp([1 - gm_prob], ecdf, quantiles, left=0))
    # Allow interpolation for gm_prob < min(im_values)
    # Note: This assumes that the smallest valid IM value is 0
    elif 0 <= (1 - gm_prob) < ecdf.min():
        im_value = float(
            np.interp([1 - gm_prob], [0, ecdf.min()], [0, im_values.min()])
        )
    else:
        raise ValueError(
            f"The value {gm_prob} is not valid for parameter gm_prob, "
            f"has to be between 0 and 1"
        )

    # Return epsilon
    return (im_value - im_values.mean()) / np.std(im_values)


def epsilon_non_para(im_values: pd.Series, gm_prob: pd.Series) -> pd.Series:
    """
    Calculates epsilon for the given ruptures from a non-parametric
    distribution

    Parameters
    ----------
    im_values: pd.Series
        The IM values for each rupture and for each "realisation"
         in each rupture
        format: index = MultiIndex[rupture_name, realisation_name], values = IM value
    gm_prob: pd.Series
        The ground motion probabilities
        format: index = rupture_id, values = probability

    Returns
    -------
    pd.Series
        Epsilon values
        format: index = rupture_id, values: epsilon
    """
    return pd.Series(
        {
            rupture: epsilon_non_para_single(
                im_values.loc[rupture].values, gm_prob.loc[rupture]
            )
            for rupture in np.unique(im_values.index.get_level_values(0))
        }
    )


def disagg_mean_weights(
    hazard_mean: float, hazard_models: pd.Series, prior_weights: pd.Series
) -> pd.Series:
    """
    Computes the adjusted disagg mean weights using equations (9) and (10) from
    "Consideration and Propagation of Ground Motion Selection
    Epistemic Uncertainties to Seismic Performance
    Metrics (Karim Tarbali, 2018)"

    Note I: All parameters need to be specific for
    the IM level of interest
    Note II: Assumes that model_names are consistent throughout

    Parameters
    ----------
    hazard_mean: float
        The mean hazard
    hazard_models: pd.Series
        The hazard values of the different models
        format: index = model_names, values = values
    prior_weights: pd.Series
        Weights of the different models
        format: index = model_names, values = weights

    Returns
    -------
    pd.Series
        The adjusted weights for each hazard model
        format: index = model/branch, values = adjusted weights
    """
    # Just to ensure a consistent order is used throughout
    model_names = hazard_models.index.values

    # Work out the new weights
    adj_weights = (
        hazard_models[model_names] * prior_weights[model_names]
    ) / hazard_mean

    return adj_weights
