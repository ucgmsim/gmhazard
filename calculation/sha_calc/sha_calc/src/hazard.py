import pandas as pd
import numpy as np


def hazard_single(gm_prob: pd.Series, rec_prob: pd.Series):
    """
    Calculates the exceedance probability given the specified
    ground motion probabilities and rupture recurrence rates

    Note: All ruptures specified in gm_prob have to exist
    in rec_prob

    Parameters
    ----------
    gm_prob: pd.Series
        The ground motion probabilities
        format: index = rupture_name, values = probability
    rec_prob: pd.Series
        The recurrence probabilities of the ruptures
        format: index = rupture_name, values = probability

    Returns
    -------
    float
        The exceedance probability
    """
    ruptures = gm_prob.index.values
    return np.sum(gm_prob[ruptures] * rec_prob[ruptures])


def hazard_curve(gm_prob_df: pd.DataFrame, rec_prob: pd.Series):
    """
    Calculates the exceedance probabilities for the
    specified IM values (via the gm_prob_df)

    Note: All ruptures specified in gm_prob_df have to exist
    in rec_prob

    Parameters
    ----------
    gm_prob_df: pd.DataFrame
        The ground motion probabilities for every rupture
        for every IM level.
        format: index = rupture_name, columns = IM_levels
    rec_prob: pd.Series
        The recurrence probabilities of the ruptures
        format: index = rupture_name, values = probability

    Returns
    -------
    pd.Series
        The exceedance probabilities for the different IM levels
        format: index = IM_levels, values = exceedance probability
    """
    data = np.sum(
        gm_prob_df.values * rec_prob[gm_prob_df.index.values].values.reshape(-1, 1),
        axis=0,
    )
    return pd.Series(index=gm_prob_df.columns.values, data=data)
