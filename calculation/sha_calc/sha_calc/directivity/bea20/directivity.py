import math
from pathlib import Path

import numpy as np
import pandas as pd

from qcore import srf
from IM_calculation.source_site_dist import src_site_dist
from sha_calc.directivity.bea20 import bea20, utils


def compute_directivity_effects(
    srf_file: str, srf_csv: Path, sites: np.ndarray, period: float = 3.0
):
    """Computes directivity effects at the given sites with the given srf data

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
    # Get rake, magnitude from srf_csv
    mag = pd.read_csv(srf_csv)["magnitude"][0]
    rake = pd.read_csv(srf_csv)["rake"][0]

    # Get planes and points from srf_file
    planes = srf.read_header(srf_file, idx=True)
    points = srf.read_latlondepth(srf_file)

    # Convert points to non dictionary format
    lon_lat_depth = np.asarray([[x["lon"], x["lat"], x["depth"]] for x in points])

    # Calculate rx ry from GC2
    rx, ry = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, sites, hypocentre_origin=True
    )

    # Gets the s_max values from the two end points of the fault
    nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)
    rx_end, ry_end = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
    )
    rx_end2, ry_end2 = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
    )
    s_max = (min(ry_end, ry_end2)[0], max(ry_end, ry_end2)[0])

    # Gets the plane index of the hypocentre
    plane_index = 0
    for index, plane in enumerate(planes):
        if plane["dhyp"] == -999.99:
            plane_index = index
            break

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

    return fd, fdi
