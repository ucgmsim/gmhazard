import math
import numbers
from typing import Sequence, Union, Tuple
from pathlib import Path

import pandas as pd


R_T_DICT = {
    "RotD100/RotD50": {
        "R": [0, 1.188, 1.225, 1.241, 1.287, 1.287],
        "T": [0, 0.12, 0.41, 3.14, 10],
    },
    "Larger/RotD50": {
        "R": [0, 1.107, 1.133, 1.149, 1.178, 1.178],
        "T": [0, 0.1, 0.45, 4.36, 8.78],
    },
}


def get_component_ratio(
    im_type: str,
    current_component: str,
    wanted_component: str,
    magnitude: Union[float, pd.Series] = 2,
    period: float = None,
) -> Tuple[Union[float, pd.Series], Union[float, pd.Series]]:
    """
    Retrieves the average IM component ratio for the specified magnitude from the electronic supplement of paper
    "Relations between Some Horizontal-Component Ground-Motion Intensity Measures Used in Practice (Boore 2017)".

    Note: As discussed in the paper, magnitude and distance dependence is small compared to the ratio scatter,
    therefore it is generally recommended to use the ratio equation from the paper instead (equation 2),
    implemented in the function get_computed_component_ratio()

    Note: This function is not optimised for a large number of lookups (i.e. large number of different magnitude values)

    Currently Supports:
    RotD50, RotD100, Larger for PGA, pSA, PGV

    Parameters
    ----------
    im_type: str
        The IM Type as a string e.g. PGA, pSA
    current_component: str
        The current component the values are calculated at e.g. RotD50
    wanted_component: str
        The wanted component the values to get the ratio for e.g. RotD100
    magnitude: Union[float, Series]
        Magnitude to be used for lookup for ratio conversions
    period: float
        Used for specifying the period for a pSA IM
    """

    if im_type not in ["pSA", "PGA", "PGV"] or (im_type == "pSA" and period is None):
        raise ValueError(
            "im_type has to be one of [pSA, PGA, PGV] and for pSA a period has to be specified"
        )

    # Setting the period for 0 or -1 if PGA or PGV and ensure magnitudes is a Series
    if im_type != "pSA":
        period = 0 if im_type == "PGA" else -1
    magnitudes = (
        pd.Series(magnitude) if isinstance(magnitude, numbers.Real) else magnitude
    )

    # Checks if the ratio needs to be flipped and sets correct components for fetching files
    flip = False
    if current_component == "RotD100":
        flip = True
        current_component, wanted_component = wanted_component, current_component
    mu_data, sigma_data = [], []

    for mag in magnitudes:
        # Load ratio file
        mmin, mmax = _get_min_max_mag(mag)
        file_name = f"{current_component}_min_{mmin}_max_{mmax}.csv"
        df = pd.read_csv(
            Path(__file__).resolve().parent / "David_M_Boore_2017" / file_name
        )

        # Get the ratios of interest
        component_column_mu = (
            f"{wanted_component}.{current_component}"
            if current_component == "RotD50"
            else f"{current_component}.{wanted_component}"
        )
        component_column_sigma = (
            f"Sdev{wanted_component.strip('Rot')}{current_component.strip('Rot')}"
            if current_component == "RotD50"
            else f"Sdev{current_component.strip('Rot')}{wanted_component.strip('Rot')}"
        )
        mu, sigma = df.loc[
            df["Per(s)"] == period, [component_column_mu, component_column_sigma]
        ].values[0]

        # Flip results if needed and add result
        if flip:
            mu, sigma = 1 / mu, 1 / sigma
        mu_data.append(mu)
        sigma_data.append(sigma)

    return (
        pd.Series(mu_data, index=magnitudes.index),
        pd.Series(sigma_data, index=magnitudes.index),
    )


def _get_min_max_mag(magnitude: float):
    range_list = [(3, 4), (4, 5), (5, 6), (6, 7), (7, 8), (5.5, 9), (2, 9)]
    for magnitude_range in range_list:
        low, high = magnitude_range
        if low <= magnitude < high:
            return magnitude_range
    raise ValueError(
        f"Magnitude value {magnitude} was not within the expected range of 2, 9"
    )


def get_computed_component_ratio(
    current_component: str, wanted_component: str, period: float
):
    """
    Computes the average IM Component ratio for a given period using (equation 2) from the paper
    "Relations between Some Horizontal-Component Ground-Motion Intensity Measures Used in Practice (Boore 2017)".

    Currently Supports:
    RotD50, RotD100, Larger

    Parameters
    ----------
    current_component: str
        The current component the values are calculated at e.g. RotD50
    wanted_component: str
        The wanted component the values to get the ratio for e.g. RotD100
    period: float
        Used for specifying the period for a pSA IM
    """
    if current_component == "RotD50":
        # Converts from RotD50 -> Larger/RotD100
        r_t_values = R_T_DICT[f"{wanted_component}/{current_component}"]
        return _compute_ratio(r_t_values["R"], r_t_values["T"], period)
    elif wanted_component == "RotD50":
        # Converts from Larger/RotD100 -> RotD50
        r_t_values = R_T_DICT[f"{current_component}/{wanted_component}"]
        return 1 / _compute_ratio(r_t_values["R"], r_t_values["T"], period)
    else:
        # Converts from Larger -> RotD100 or vise versa
        r_t_values = R_T_DICT[f"{current_component}/RotD50"]
        ratio_rotD50 = 1 / _compute_ratio(r_t_values["R"], r_t_values["T"], period)
        r_t_values = R_T_DICT[f"{wanted_component}/RotD50"]
        return ratio_rotD50 * _compute_ratio(r_t_values["R"], r_t_values["T"], period)


def _compute_ratio(R: Sequence[float], T: Sequence[float], period: float):
    """Computes the ratio between two components using Equation 2 of the Boore paper with the specified coefficients"""
    return max(
        R[1],
        max(
            min(
                R[1] + (R[2] - R[1]) / math.log(T[2] / T[1]) * math.log(period / T[1]),
                R[2] + (R[3] - R[2]) / math.log(T[3] / T[2]) * math.log(period / T[2]),
            ),
            min(
                R[3] + (R[4] - R[3]) / math.log(T[4] / T[3]) * math.log(period / T[3]),
                R[5],
            ),
        ),
    )
