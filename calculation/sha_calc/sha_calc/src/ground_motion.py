from typing import Union

import pandas as pd
import numpy as np
from scipy.stats import norm


def non_parametric_gm_excd_prob(im_level: float, im_values: pd.Series):
    """
    Calculates the ground motion exceedance probability for each rupture
    for the specified im_level, for non-parametric data (e.g. from simulations)

    Parameters
    ----------
    im_level: float
        The IM level for which to calculate the ground motion exceedance probability
    im_values: pd.Series
        The IM values for each rupture and for each "realisation"
         in each rupture
        format: index = MultiIndex[rupture_name, realisation_name], values = IM value

    Returns
    -------
    pd.Series
        The exceedance probability for each rupture
    """
    # Count the number of realisations per rupture
    rupture_count = im_values.groupby(level=0).count().sort_index()

    # Count the number of realisation with IM values greater than the specified IM level
    greater_count = (
        (im_values > im_level).groupby(level=0).agg(np.count_nonzero).sort_index()
    )

    return greater_count / rupture_count


def parametric_gm_excd_prob(im_levels: Union[float, np.ndarray], im_params: pd.DataFrame):
    """
    Calculates the ground motion exceedance probability for each rupture
    for the specified IM levels, from a parametric distribution

    Parameters
    ----------
    im_levels: float or array
        The IM level(s) for which to calculate the ground motion exceedance probability
    im_params: pd.DataFrame
        The IM distribution parameters for for each rupture
        format: index = rupture_name, columns = [mu, sigma]

    Returns
    -------
    pd.DataFrame
        The exceedance probability for each rupture at each IM level
        shape: [n_ruptures, n_im_levels]
    """
    im_levels = np.asarray(im_levels).reshape(1, -1)

    results = norm.sf(
        np.log(im_levels),
        im_params.mu.values.reshape(-1, 1),
        im_params.sigma.values.reshape(-1, 1),
    )
    return pd.DataFrame(
        index=im_params.index.values, data=results, columns=im_levels.reshape(-1)
    )
