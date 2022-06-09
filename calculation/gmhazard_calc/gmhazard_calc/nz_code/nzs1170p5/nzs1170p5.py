import time
import multiprocessing as mp
from typing import Optional, Union, Iterable

import pandas as pd
import numpy as np

import sha_calc as sha_calc
from gmhazard_calc import site
from gmhazard_calc import gm_data
from gmhazard_calc import site_source
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM, IMType, IMComponent
from .NZS1170p5Result import NZS1170p5Result
from .nzs_zfactor_2016 import ll2z

DEFAULT_NEAR_FAULT_DISTANCE = 200
CONTRIBUTING_FAULTS = [
    "AlpineF2K",
    "AlpineK2T",
    "AwatereNE",
    "AwatereSW",
    "ClarenceNE",
    "ClarenceCentr",
    "ClarenceSW",
    "HopeTARA",
    "Hope1888",
    "HopeCW",
    "HopeConway",
    "Kakapo",
    "JorKekNeed",
    "KekNeed",
    "Kelly",
    "MohakaN",
    "MohakaS",
    "WairarapNich",
    "Wairau",
    "WellWHV",
    "WellTeast",
    "WellP",
]
DEFAULT_RETURN_PERIODS = np.array([20, 25, 50, 100, 250, 500, 1000, 2000, 2500])
DEFAULT_EXCEEDANCE_VALUES = 1 / DEFAULT_RETURN_PERIODS


def run_ensemble_nzs1170p5(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    exceedance_values: np.array = DEFAULT_EXCEEDANCE_VALUES,
    soil_class: Optional[const.NZSSoilClass] = None,
    distance: Optional[float] = None,
    z_factor: Optional[float] = None,
    z_factor_radius: Optional[float] = ll2z.CITY_RADIUS_SEARCH,
) -> Union[NZS1170p5Result, None]:
    """
    Performs the NZ code spectra calculation
    as outlined in NZS1170.5 2004

    Parameters
    ----------
    ensemble: Ensemble
    site_info: SiteInfo
    im: IM
    exceedance_values: np.ndarray of floats, optional
        The exceedance values for which to calculate the NZ code hazard values
        Note: NZ code is only defined in the exceedance range 1/2500 < excd < 1/20
    soil_class: SoilClass, optional
    distance: float, optional
        Shortest distance to the nearest fault (of the 11 of interest)
        Referred to as D in the NZ code documentation
    z_factor: float, optional
        The hazard factor, referred to as Z in the NZ code documentation

    Returns
    -------
    NZS1170p5Result
    """
    if distance is None:
        distance = get_distance_from_site_info(ensemble, site_info)

    if z_factor is None:
        z_factor = float(
            ll2z.ll2z((site_info.lon, site_info.lat), radius_search=z_factor_radius)
        )

    if soil_class is None:
        soil_class = get_soil_class(site_info.vs30)

    if im.im_type != IMType.PGA and not im.is_pSA():
        raise Exception("Invalid IM type specified, has to be either PGA or pSA")
    sa_period = 0 if im.im_type == IMType.PGA else im.period

    result_dict, R_dict, N_dict, Ch_dict = {}, {}, {}, {}
    for cur_exceedance in exceedance_values:
        cur_rp = 1 / cur_exceedance

        if cur_rp < 20 or cur_rp > 2500:
            result_dict[cur_exceedance] = np.nan
        else:
            C, Ch, R, N = sha_calc.nzs1170p5_spectra(
                [sa_period], z_factor, cur_rp, distance, soil_class.value
            )
            result_dict[cur_exceedance] = float(C)
            R_dict[cur_exceedance] = R
            N_dict[cur_exceedance] = float(N)
            Ch_dict[cur_exceedance] = float(Ch)

    if im.component != IMComponent.Larger:
        if im.is_pSA() or im.im_type is IMType.PGA:
            ratio = sha_calc.get_computed_component_ratio(
                str(IMComponent.Larger),
                str(im.component),
                # Using period of 0.01 for PGA IM
                im.period if im.is_pSA() else 0.01,
            )
            result_dict = {key: value * ratio for key, value in result_dict.items()}

    if len(result_dict) > 0:
        return NZS1170p5Result(
            ensemble,
            site_info,
            im,
            sa_period,
            pd.Series(result_dict, name="im_values"),
            pd.Series(Ch_dict),
            soil_class,
            z_factor,
            pd.Series(R_dict),
            distance,
            pd.Series(N_dict),
        )

    return None


def run_hazard_map(
    ensemble: gm_data.Ensemble, im: IM, exceedance: float, n_procs: Optional[int] = 4
) -> pd.DataFrame:
    """
    Computes the NZ code hazard at each station in the ensemble for the
    specified exceedance.

    Note: If hdf5 locking issues occur, run this using the
    env variable HDF5_USE_FILE_LOCKING="False"

    Parameters
    ----------
    ensemble: Ensemble
    im: IM
        IM Object used for calculations
    exceedance: float
        The exceedance value
    n_procs:
        Number of processes to use

    Returns
    -------
    pd.Series
        format: index = station_name, values: exceedance probability
    """
    if im.im_type != IMType.PGA and not im.is_pSA():
        raise Exception(f"Invalid IM {im} specified, has to be either PGA or pSA")
    im_period = 0 if im.im_type == IMType.PGA else im.period

    # Drop duplicate location stations
    stations_df = ensemble.stations.drop_duplicates(subset=["lon", "lat"])

    n_stations = stations_df.shape[0]
    if n_procs == 1:
        excd_probs = []
        for ix, station_name in enumerate(stations_df.index.values):
            excd_probs.append(
                get_hazard(
                    ensemble, station_name, im_period, exceedance, ix, n_stations
                )
            )
    else:
        with mp.Pool(n_procs) as p:
            excd_probs = p.starmap(
                get_hazard,
                [
                    (ensemble, station_name, im_period, exceedance, ix, n_stations)
                    for ix, station_name in enumerate(stations_df.index.values)
                ],
            )

    result_df = stations_df.copy()
    result_df["value"] = excd_probs
    return result_df


def get_distance_from_site_info(ensemble: gm_data.Ensemble, site_info: site.SiteInfo):
    """Gets the near fault factor for the specified site"""
    distance_df = site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info)

    distance = DEFAULT_NEAR_FAULT_DISTANCE
    if distance_df is not None:
        cur_contr_faults = list(
            set.intersection(set(distance_df.index.values), CONTRIBUTING_FAULTS)
        )
        if len(cur_contr_faults) > 0:
            distance = distance_df.loc[cur_contr_faults].rrup.min()
    return distance


def get_soil_class(vs30: float):
    """Gets the soil class for the specified vs30
    Updated by Brendon and Robin on 23/05/2022
    Original post: https://uceqeng.slack.com/files/U3S75KRUH/F03FMJHM45D/image.png
    """
    assert not np.isnan(vs30), "NaN vs30 values are not allowed"

    if vs30 < 180:
        return const.NZSSoilClass.very_soft
    elif vs30 < 300:
        return const.NZSSoilClass.soft_or_deep_soil
    elif vs30 < 500:
        return const.NZSSoilClass.intermediate_soil
    elif vs30 < 2500:
        return const.NZSSoilClass.weak_rock
    else:
        return const.NZSSoilClass.rock


def get_hazard(
    ensemble: gm_data.Ensemble,
    station_name: str,
    im_periods: Union[Iterable[float], float],
    exceedance: float,
    ix: Optional[int] = None,
    n_stations: Optional[int] = None,
):
    """
    Computes the NZ code hazard for the single exceedance value

    Parameters
    ----------
    ensemble: Ensemble
    station_name: str
    im_periods: iterable of floats or single float
        The spectral acceleration periods of interest
    exceedance: float
        The annual exceedance of interest
    ix: int, optional
        Station index, only used for progress tracking when
        using this function in a multiprocessing manner
    n_stations: int, optional
        Same as ix

    Returns
    -------
    float or pd.Series
        Returns the single NZ code value if im_periods is a single float value,
        otherwise returns a pd.Series of format,
        index = SA period, values = NZ code values
    """
    # Compute nz code values
    start_time = time.time()
    site_info = site.get_site_from_name(ensemble, station_name)
    C, Ch, R, N = sha_calc.nzs1170p5_spectra(
        [im_periods] if isinstance(im_periods, float) else im_periods,
        ll2z.ll2z(
            (site_info.lon, site_info.lat), radius_search=ll2z.CITY_RADIUS_SEARCH
        ),
        1 / exceedance,
        get_distance_from_site_info(ensemble, site_info),
        get_soil_class(site_info.vs30).value,
    )

    if ix is not None and n_stations is not None:
        print(
            f"NZ Code Hazard - Progress {ix}/{n_stations} - station {station_name} "
            f"- {time.time() - start_time}"
        )

    return float(C) if C.size == 1 else C
