"""Ground motion selection functionality for simulations based on the following papers:
- Bradley, Brendon A. "A generalized conditional intensity measure approach and holistic ground‐motion selection."
Earthquake Engineering & Structural Dynamics 39.12 (2010): 1321-1342.
- Bradley, Brendon A. "A ground motion selection algorithm based on the generalized conditional intensity measure approach."
Soil Dynamics and Earthquake Engineering 40 (2012): 48-61.
- Bradley, Brendon A., Lynne S. Burks, and Jack W. Baker. "Ground motion selection for simulation‐based seismic hazard and structural reliability assessment."
Earthquake Engineering & Structural Dynamics 44.13 (2015): 2321-2340.
"""

import numpy as np
import pandas as pd
from scipy import stats

from . import shared


def compute_weighted_sigma(im_df: pd.DataFrame, alpha: pd.Series) -> pd.Series:
    """Computes the weighted sigma_lnIMi|Rup,IMj from equation 10 in [1],
    which for the simulation based GM selection process is rupture
    independent (as no rupture selection is done)

    [1] Bradley, Brendon A. "A ground motion selection
    algorithm based on the generalized conditional
    intensity measure approach."

    Parameters
    ----------
    im_df: pandas dataframe
        The IM values for each simulation
        Shape: [n_simulation, n_IMs]
    alpha: pandas series
        The normalized simulation weights

    Returns
    -------
    pandas series
        The weighted standard deviation for each IM
    """
    # Sanity checks
    assert np.isclose(np.sum(alpha), 1.0), "The simulations have to be normalized"
    im_df, alpha = shared.__align_check_indices(im_df, alpha)

    # Compute the weighted mean
    mu_ln = np.sum((alpha.values * np.log(im_df.values.T)).T, axis=0)

    # Compute the weighted standard deviation
    # Note: This requires the weights to be normalized (hence the assert above)
    sigma_ln = np.sqrt(
        np.sum((alpha.values * ((np.log(im_df.values) - mu_ln) ** 2).T).T, axis=0)
        / (1 - np.sum(alpha.values ** 2))
    )

    return pd.Series(data=sigma_ln, index=im_df.columns)
