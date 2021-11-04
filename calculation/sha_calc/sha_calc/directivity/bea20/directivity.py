import math
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import time

from qcore import srf
from IM_calculation.source_site_dist import src_site_dist
from sha_calc.directivity.bea20 import bea20, utils
from sha_calc.constants import DEFAULT_PSA_PERIODS


def compute_directivity_srf_single(
    srf_file: str, srf_csv: Path, sites: np.ndarray, periods: List[float] = DEFAULT_PSA_PERIODS
):
    """Computes directivity effects at the given sites with the given srf data for a single hypocentre

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    periods: List[float], optional
        The periods to calculate for the bea20 model's fD
        If not set then will be all the default pSA periods for GMHazard
    """
    (
        mag,
        rake,
        planes,
        lon_lat_depth,
    ) = _srf_pre_process(srf_file, srf_csv)

    hyp_along_strike = 1
    hyp_down_dip = 1

    return compute_fault_directivity(
        lon_lat_depth,
        planes,
        sites,
        hyp_along_strike,
        hyp_down_dip,
        mag,
        rake,
        periods=periods,
    )


def compute_directivity_srf_multi(
    srf_file: str, srf_csv: Path, sites: np.ndarray, periods: List[float] = DEFAULT_PSA_PERIODS
):
    """Computes directivity effects at the given sites with the given srf data using hypocentre averaging

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    periods: List[float], optional
        The periods to calculate for the bea20 model's fD
        If not set then will be all the default pSA periods for GMHazard
    """
    (
        mag,
        rake,
        planes,
        lon_lat_depth,
    ) = _srf_pre_process(srf_file, srf_csv)

    # TODO Update with best practice for hypocentre averaging
    hyp_along_strike = 10
    hyp_down_dip = 2

    return compute_fault_directivity(
        lon_lat_depth,
        planes,
        sites,
        hyp_along_strike,
        hyp_down_dip,
        mag,
        rake,
        periods=periods,
    )


def compute_fault_directivity(
    lon_lat_depth: np.ndarray,
    planes: List,
    sites: np.ndarray,
    hyp_along_strike: int,
    hyp_down_dip: int,
    mag: float,
    rake: float,
    periods: List[float] = DEFAULT_PSA_PERIODS,
    return_fdi_array: bool = False,
    fault_name: str = "Nothing",
):
    """
    Does the computation of directivity for a fault with any number of hypocentres.
    Can compute regardless if data came from an srf or nhm file.

    Parameters
    ----------
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format [[lon, lat, depth],...]
    planes: List
        List of the planes that make up the fault
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    hyp_along_strike: int
        Number of hypocentres across strike
    hyp_down_dip: int
        Number of hypocentres down dip
    mag: float
        The magnitude of the fault
    rake: float
        The rake of the fault
    periods: List[float], optional
        The periods to calculate for the bea20 model's fD
        If not set then will be all the default pSA periods for GMHazard
    return_fdi_array: bool, optional
        Decides if all results from each hypocentre calculation is saved and returned
        Default is False due to the high RAM requirement for higher hypocentre runs
    """
    nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)

    if hyp_down_dip == 1 and hyp_along_strike == 1:
        planes_list, plane_index = utils.set_hypocentres(
            1, 1, planes, utils.EventType.from_rake(rake)
        )

        return _compute_directivity_effect(
            lon_lat_depth,
            planes_list[0],
            plane_index[0],
            sites,
            nominal_strike,
            nominal_strike2,
            mag,
            rake,
            periods,
        )
    else:
        # Customise the planes to set different hypocentres
        planes_list, planes_index = utils.set_hypocentres(
            hyp_along_strike, hyp_down_dip, planes, utils.EventType.from_rake(rake), fault_name=fault_name
        )

        # Creating the array to store all fdi values
        if return_fdi_array:
            fdi_array = np.zeros((hyp_along_strike * hyp_down_dip, 10000, 1))
            phired_array = np.zeros((hyp_along_strike * hyp_down_dip, 10000, 1))
        else:
            fdi_array = np.asarray([])
            phired_array = np.asarray([])

        for index, planes in enumerate(planes_list):
            # Gets the plane index of the hypocentre
            plane_index = planes_index[index]

            print(f"Computing Directivity {fault_name} {index+1}/{hyp_along_strike * hyp_down_dip}")

            fdi, (phi_red, predictor_functions, other) = _compute_directivity_effect(
                lon_lat_depth,
                planes,
                plane_index,
                sites,
                nominal_strike,
                nominal_strike2,
                mag,
                rake,
                periods,
            )

            # Check if fdi_array is needed and if not then sum results to manage RAM better
            if return_fdi_array:
                fdi_array[index] = fdi
                phired_array[index] = phi_red
            else:
                if len(fdi_array) == 0:
                    fdi_array = fdi
                    phired_array = phi_red
                else:
                    fdi_array = np.add(fdi_array, fdi)
                    phired_array = np.add(phired_array, phi_red)

        # Check if fdi_array is needed and if not then create mean from the summed results to manage RAM better
        if return_fdi_array:
            fdi_average = np.mean(fdi_array, axis=0)
            phired_average = np.mean(phired_array, axis=0)
        else:
            fdi_average = np.divide(fdi_array, hyp_down_dip * hyp_along_strike)
            phired_average = np.divide(phired_array, hyp_down_dip * hyp_along_strike)

        return fdi_average, fdi_array, phired_average  # Ignore fdi_array for now


def _compute_directivity_effect(
    lon_lat_depth: np.ndarray,
    planes: List,
    plane_index: int,
    sites: np.ndarray,
    nominal_strike: np.ndarray,
    nominal_strike2: np.ndarray,
    mag: float,
    rake: float,
    periods: List[float],
):
    """
    Does the computation of directivity and GC2 given a set of planes with a set hypocentre.

    Parameters
    ----------
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format [[lon, lat, depth],...]
    planes: List
        List of the planes that make up the fault
    plane_index: int
        The index in planes that the hypocentre is located in
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    nominal_strike: np.ndarray
        The nominal strike coordinates (edge of the fault) with the highest longitiude value
    nominal_strike2: np.ndarray
        The nominal strike coordinates (edge of the fault) with the lowest longitiude value
    mag: float
        The magnitude of the fault
    rake: float
        The rake of the fault
    periods: List[float]
        The periods to calculate for the bea20 model's fD
    """
    # Calculate rx ry from GC2
    rx, ry = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, sites, hypocentre_origin=True
    )

    # Gets the s_max values from the two end points of the fault
    rx_end, ry_end = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
    )
    rx_end2, ry_end2 = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
    )
    s_max = (min(ry_end, ry_end2)[0], max(ry_end, ry_end2)[0])

    # Trig to calculate extra features of the fault for directivity based on plane info
    z_tor = planes[plane_index]["dtop"]
    dip = planes[plane_index]["dip"]
    d_bot = z_tor + planes[plane_index]["width"] * math.sin(math.radians(dip))
    t_bot = z_tor / math.tan(math.radians(dip)) + planes[0]["width"] * math.cos(
        math.radians(dip)
    )
    d = (planes[plane_index]["dhyp"] - z_tor) / math.sin(math.radians(dip))

    # Use the bea20 model to work out directivity (fd) at the given sites
    fd, phi_red, predictor_functions, other = bea20(
        mag, ry, rx, s_max, d, t_bot, d_bot, rake, dip, np.asarray(periods)
    )

    return fd, (phi_red, predictor_functions, other)


def _srf_pre_process(srf_file: str, srf_csv: Path):
    """
    Does the srf pre processing steps for computing directivity such as getting the
    magnitude, rake, planes and lon_lat_depth values.

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    """
    # Get rake, magnitude from srf_csv
    mag = pd.read_csv(srf_csv)["magnitude"][0]
    rake = pd.read_csv(srf_csv)["rake"][0]

    # Get planes and points from srf_file
    planes = srf.read_header(srf_file, idx=True)
    lon_lat_depth = srf.read_srf_points(srf_file)

    return mag, rake, planes, lon_lat_depth
