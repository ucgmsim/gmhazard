import os
from typing import Union

import math
import pandas as pd
import numpy as np

import sha_calc as sha
from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc import constants as const
from seistech_calc.im import IMComponent
from .NZTAResult import NZTAResult
from qcore import geo

# The following CSV file was based on p.147 NZTA Bridge Manual Commentary,
# where, Lat and Lon of each town was obtained from wikipedia (produced by geohack.toolforge.org)
# if the Lat and Lon is in water, a government office location is used instead.
# (eg. regional council for Huntly, Thames, police station for Oban)
# Vs30 values were obtained from Kevin's vs30 map (Release 2020: https://github.com/ucgmsim/Vs30/releases/tag/1)
NZTA_LOOKUP_FFP = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "NZTA_data_lat_lon_vs30.csv"
)

DEFAULT_RETURN_PERIODS = np.array([20, 25, 50, 100, 250, 500, 1000, 2000, 2500])
DEFAULT_EXCEEDANCE_VALUES = 1 / DEFAULT_RETURN_PERIODS


def run_ensemble_nzta(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    exceedance_values: np.ndarray = DEFAULT_EXCEEDANCE_VALUES,
    soil_class: const.NZTASoilClass = None,
    im_component: IMComponent = IMComponent.RotD50,
):
    """Runs NZTA for the specified site and ensemble
    Note:

    Parameters
    ----------
    ensemble: Ensemble
        The ensemble does not affect calculation at all,
            purely included for consistency/completeness
    site_info: SiteInfo
        The site for which to compute NZTA code hazard
    exceedance_values: array of floats, optional
    soil_class: NZTASoilClass, optional
        The soil class to use, if not specified then
        this is computed based on the vs30 of the site

    Returns
    -------
    NZTAResult
    """
    # Load the required NZTA data
    nzta_df = pd.read_csv(NZTA_LOOKUP_FFP, header=0, index_col=0)

    soil_class = (
        soil_class if soil_class is not None else get_soil_class(site_info.vs30)
    )

    # Get the return periods
    rp_values = 1 / exceedance_values

    # Compute PGA and retrieve effective magnitude
    C0_1000, nearest_town = get_C0_1000(
        site_info.lat, site_info.lon, soil_class, nzta_df=nzta_df
    )
    pga_values, M_eff = [], None
    for cur_rp in rp_values:
        cur_pga, M_eff = get_pga_meff(C0_1000, nearest_town, cur_rp, nzta_df=nzta_df)
        pga_values.append(cur_pga)

    if im_component != IMComponent.Larger:
        ratio = sha.get_computed_component_ratio(
            str(IMComponent.Larger),
            str(im_component),
            # Using period of 0.01 for PGA IM
            0.01,
        )
        pga_values = [value * ratio for value in pga_values]

    return NZTAResult(
        ensemble,
        site_info,
        soil_class,
        pd.Series(index=exceedance_values, data=pga_values),
        M_eff,
        C0_1000,
        nearest_town,
    )


def get_C0_1000(
    lat: float,
    lon: float,
    soil_class: const.NZTASoilClass,
    nzta_df: pd.DataFrame = None,
):
    """
    Returns
    -------
    1. C_0,1000 value for the given vs30 value at the closest location
    2. the name of the closest town
    """
    nzta_df = (
        pd.read_csv(NZTA_LOOKUP_FFP, header=0, index_col=0)
        if nzta_df is None
        else nzta_df
    )

    town, _ = __location_lookup(lat, lon, nzta_df)
    if soil_class is const.NZTASoilClass.rock:
        return nzta_df["C_0_1000_AB"].loc[town], town
    else:
        return nzta_df["C_0_1000_DE"].loc[town], town


def get_pga_meff(
    C0_1000: float,
    town: str,
    RP: Union[int, float],
    nzta_df: pd.DataFrame = None,
):
    """
    Returns
    -------
    float/NaN:
        PGA computed based on c_0,1000 value for the given location and return period
        if C_0,1000 is not 0 else NaN
    float:
        Effective magnitudes for design return period (years)
    """
    nzta_df = (
        pd.read_csv(NZTA_LOOKUP_FFP, header=0, index_col=0)
        if nzta_df is None
        else nzta_df
    )

    R = sha.get_return_period_factor(RP)

    return (
        C0_1000 * R / 1.3 if C0_1000 != 0 else np.nan,
        __get_meff(town, RP, nzta_df),
    )


def get_soil_class(vs30: float):
    return (
        const.NZTASoilClass.rock
        if vs30 > 500
        else const.NZTASoilClass.soft_or_deep_soil
    )


def __get_meff(town: str, rp: Union[float, int], nzta_df: pd.DataFrame):
    """
    Returns
    -------
    dataframe, dataframe
        Effective magnitudes for design return periods (500-2500, 50-250 years)
    """
    if 50 <= rp <= 250:
        return nzta_df["Meff_50_250"].loc[town]
    elif 500 <= rp <= 2500:
        return nzta_df["Meff_500_2500"].loc[town]

    return None


def __location_lookup(lat: float, lon: float, nzta_df: pd.DataFrame):
    """
    Returns
    -------
    string:
        name of the closest town
    float:
        distance to closest town
    """
    idx, dist = geo.closest_location(
        np.array([nzta_df["lon"].values, nzta_df["lat"].values]).T, lon, lat
    )
    assert idx < len(nzta_df.index)

    return list(nzta_df.index)[idx], dist
