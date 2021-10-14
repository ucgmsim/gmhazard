import math
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd

from qcore import srf
from IM_calculation.source_site_dist import src_site_dist
from sha_calc.directivity.bea20 import bea20, utils


def compute_directivity_single_hypo(
    srf_file: str, srf_csv: Path, sites: np.ndarray, period: float = 3.0
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
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    """
    (
        mag,
        rake,
        planes,
        lon_lat_depth,
        nominal_strike,
        nominal_strike2,
    ) = directivity_pre_process(srf_file, srf_csv)

    # Gets the plane index of the hypocentre
    plane_index = 0
    for index, plane in enumerate(planes):
        if plane["dhyp"] == -999.99:
            plane_index = index
            break

    fd, fdi, phi_red, phi_redi, predictor_functions, other = compute_directivity_effect(
        lon_lat_depth,
        planes,
        plane_index,
        sites,
        nominal_strike,
        nominal_strike2,
        mag,
        rake,
        period,
    )

    return fdi


def compute_directivity_hypo_averaging(
    srf_file: str, srf_csv: Path, sites: np.ndarray, period: float = 3.0
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
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    """
    (
        mag,
        rake,
        planes,
        lon_lat_depth,
        nominal_strike,
        nominal_strike2,
    ) = directivity_pre_process(srf_file, srf_csv)

    # Customise the planes to set different hypocentres
    n_hypo = 20  # TODO Update with best practice for hypocentre averaging
    planes_list, planes_index = utils.set_hypocentres(n_hypo, planes, [1 / 3, 2 / 3])

    # Creating the average arrays
    (
        fd_average,
        fdi_average,
        phi_red_average,
        phi_redi_average,
        predictor_functions_average,
        other_average,
    ) = (
        [],
        [],
        [],
        [],
        {"fG": [], "fdist": [], "ftheta": [], "fphi": [], "fs2": []},
        {
            "Per": [],
            "Rmax": [],
            "Footprint": [],
            "Tpeak": [],
            "fG0": [],
            "bmax": [],
            "S2": [],
        },
    )

    for index, planes in enumerate(planes_list):
        # Gets the plane index of the hypocentre
        plane_index = planes_index[index]

        (
            fd,
            fdi,
            phi_red,
            phi_redi,
            predictor_functions,
            other,
        ) = compute_directivity_effect(
            lon_lat_depth,
            planes,
            plane_index,
            sites,
            nominal_strike,
            nominal_strike2,
            mag,
            rake,
            period,
        )

        fd_average.append(fd)
        fdi_average.append(fdi)
        phi_red_average.append(phi_red)
        phi_redi_average.append(phi_redi)
        for key, value in predictor_functions.items():
            predictor_functions_average[key].append(value)
        for key, value in other.items():
            other_average[key].append(value)

    (fd_average, fdi_average, phi_red_average, phi_redi_average,) = (
        np.mean(fd_average, axis=0),
        np.mean(fdi_average, axis=0),
        np.mean(phi_red_average, axis=0),
        np.mean(phi_redi_average, axis=0),
    )
    for key, value in predictor_functions_average.items():
        predictor_functions_average[key] = np.mean(
            predictor_functions_average[key], axis=0
        )
    for key, value in other_average.items():
        other_average[key] = np.mean(other_average[key], axis=0)

    return (
        fd_average,
        fdi_average,
        phi_red_average,
        phi_redi_average,
        predictor_functions_average,
        other_average,
    )


def directivity_pre_process(srf_file: str, srf_csv: Path):
    """
    Does the pre processing steps for computing directivity such as getting the
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

    nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)

    return mag, rake, planes, lon_lat_depth, nominal_strike, nominal_strike2


def compute_directivity_effect(
    lon_lat_depth: np.ndarray,
    planes: List,
    plane_index: int,
    sites: np.ndarray,
    nominal_strike: np.ndarray,
    nominal_strike2: np.ndarray,
    mag: float,
    rake: float,
    period: float,
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
    period: float
        The period for fdi to extract from the bea20 models fd
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
    fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20.bea20(
        mag, ry, rx, s_max, d, t_bot, d_bot, rake, dip, period
    )

    return fd, fdi, phi_red, phi_redi, predictor_functions, other
