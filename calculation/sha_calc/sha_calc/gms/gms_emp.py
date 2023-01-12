"""Ground motion selection functionality for simulations based on the following papers:
- Bradley, Brendon A. "A generalized conditional intensity measure approach and holistic ground‐motion selection."
Earthquake Engineering & Structural Dynamics 39.12 (2010): 1321-1342.
- Bradley, Brendon A. "A ground motion selection algorithm based on the generalized conditional intensity measure approach."
Soil Dynamics and Earthquake Engineering 40 (2012): 48-61.
- Bradley, Brendon A., Lynne S. Burks, and Jack W. Baker. "Ground motion selection for simulation‐based seismic hazard and structural reliability assessment."
Earthquake Engineering & Structural Dynamics 44.13 (2015): 2321-2340.
"""
from typing import Iterable, Tuple, Sequence

import numpy as np
import pandas as pd
from scipy.linalg import cholesky

from . import shared


GM_SCALING_ALPHA = {
    "pga": 1,
    "pgv": 1,
    "psa": 1,
    "ai": 2,
    "ds595": 0,
    "ds575": 0,
    "cav": 1,
    "asi": 1,
    "si": 1,
    "dsi": 1,
}


def generate_correlated_vector(
    n_gms: int, IMs: np.ndarray, rho: pd.DataFrame, n_replica: int = 1
):
    """Computes a correlated vector (along axis 1)
    of shape [n_gms, len(IMs)]

    Parameters
    ----------
    n_gms: int
        Number of GMs
    IMs: array of strings
        Names of the IMs
    rho: dataframe
        The correlation matrix
        format: index = IMs, columns = IMs (same order)
    n_replica: int
        Number of replica

    Returns
    -------
    list of dataframe
        The n_replica correlated vectors
    """
    u_vectors = [np.random.normal(0, 1, (n_gms, IMs.size)) for ix in range(n_replica)]
    try:
        L = cholesky(rho, lower=True)
    except np.linalg.LinAlgError:
        pd_rho = shared.nearest_pd(rho)
        L = cholesky(pd_rho, lower=True)
    v_vectors = [pd.DataFrame(data=np.dot(L, u.T).T, columns=IMs) for u in u_vectors]

    return v_vectors


def gm_scaling(
    im_df: pd.DataFrame, IM_j: str, im_j: float, IMs: np.ndarray
) -> Tuple[pd.DataFrame, pd.Series]:
    """Scales the IMs of the ground motions as specified in equations
    13 and 14 of "Bradley, B.A., 2012. A ground motion selection algorithm
    based on the generalized conditional intensity measure approach."

    Only valid for IMs that scale analytically.

    Parameters
    ----------
    im_df: pandas dataframe
        The IM dataframe which contains the unscaled IM values
        The index of dataframes have to be the identifier for
        the ground motions (the selected ones will be returned)
    IM_j: string
        Name of the conditioning IM
    im_j: float
        Value to scale the GMs IMs to (for IM_j)
    IMs: numpy array of strings
        The IMs to scale

    Returns
    -------
    pandas dataframe
        The scaled IMs for each ground motion
        Shape: [n_GMs, n_IMs]
    """
    # Sanity checks
    assert IM_j in im_df.columns, "The IM dataframe must contain the conditioning IM"
    assert np.all(
        np.isin(IMs, im_df.columns)
    ), "All IMs of interest must be in the IM dataframe"

    # Get the alpha values for the IMs
    alphas = get_scale_alpha(IMs)

    # Get alpha for IM_j
    alpha_IMj = get_scale_alpha([IM_j])[0]

    # Compute the scaling factor for each ground motion
    sf = (im_j / im_df.loc[:, IM_j]) ** (1 / alpha_IMj)
    sf.name = "SF"

    scaled_ims = im_df.loc[:, IMs] * (sf.values[:, np.newaxis] ** alphas[np.newaxis, :])

    return scaled_ims, sf


def get_scale_alpha(IMs: Iterable[str]):
    """Gets the scaling alpha integer for
    the specified IMs
    """
    alphas = []

    for cur_im in IMs:
        cur_im = cur_im.strip().lower()
        cur_alpha = (
            GM_SCALING_ALPHA["psa"]
            if cur_im.startswith("psa")
            else GM_SCALING_ALPHA.get(cur_im)
        )

        if cur_alpha is None:
            raise KeyError(f"No scaling alpha for IM {cur_im} available.")

        alphas.append(cur_alpha)

    return pd.Series(data=alphas, index=IMs)

def compute_scaling_factor(gm_im_values: pd.Series, im_name: str, im_value: float):
    """
    Computes the amplitude scaling factor such that IM_j == im_j
    for all of the specified GM ids.
    See equations (13) and (14) of Bradley 2012

    Parameters
    ----------
    im_name: str
        Name of the IM to scale
    im_value: float
        The IM to scale and the target value
    im_df: series
        GM records (index) and the IM to scale on (values)

    Returns
    -------
    series:
        Scaling factor for each GM record
    """
    # Compute the scaling factor
    IMj_alpha = get_scale_alpha([im_name]).loc[str(im_name)]
    sf = np.power(im_value / gm_im_values, 1.0 / IMj_alpha)

    return sf

def apply_amp_scaling(im_df: pd.DataFrame, sf: pd.Series):
    """
    Applies amplitude to the specified GMs

    Note: The indices of im_df and sf have to match

    Parameters
    ----------
    im_df: dataframe
        The IM records to scale

        Note: All columns are assumed to be IMs
    sf: series
        The scaling factor for each GM of interest
        index: GM ids, value: scaling factor

    Returns
    -------
    dataframe:
        The scaled IMs
    """
    assert np.all(im_df.index == sf.index)

    im_names = im_df.columns.values.astype(str)
    IMs_alpha = get_scale_alpha(im_names)

    im_sf_df = pd.DataFrame(
        index=sf.index, data=np.power(sf.values[:, np.newaxis], IMs_alpha.values[np.newaxis, :]), columns=im_names
    )

    scaled_im_df = im_df * im_sf_df
    return scaled_im_df