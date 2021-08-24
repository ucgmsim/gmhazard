"""Ground motion selection functionality for simulations based on the following papers:
- Bradley, Brendon A. "A generalized conditional intensity measure approach and holistic ground‐motion selection."
Earthquake Engineering & Structural Dynamics 39.12 (2010): 1321-1342.
- Bradley, Brendon A. "A ground motion selection algorithm based on the generalized conditional intensity measure approach."
Soil Dynamics and Earthquake Engineering 40 (2012): 48-61.
- Bradley, Brendon A., Lynne S. Burks, and Jack W. Baker. "Ground motion selection for simulation‐based seismic hazard and structural reliability assessment."
Earthquake Engineering & Structural Dynamics 44.13 (2015): 2321-2340.
"""
from typing import Iterable, Tuple

import numpy as np
import pandas as pd
from numpy import linalg as la
from scipy.linalg import cholesky


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
        pd_rho = nearest_pd(rho)
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
