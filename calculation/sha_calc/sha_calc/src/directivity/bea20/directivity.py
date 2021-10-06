import numpy as np
import pandas as pd
import math
from pathlib import Path
from typing import List

import utils
import bea20
from qcore import srf
from IM_calculation.source_site_dist import src_site_dist

def get_directivity_effects(srf_file: Path, srf_csv: Path, sites: List, period: float = 3.0):
    """Calculates directivity effects at the given sites and srf"""

    # Get rake, magnitude from srf_csv
    mag = pd.read_csv(srf_csv)["magnitude"][0]
    rake = pd.read_csv(srf_csv)["rake"][0]

    # Get planes and points from srf_file
    planes = srf.read_header(str(srf_file), idx=True)
    points = srf.read_latlondepth(str(srf_file))

    # Convert points to non dictionary format
    lon_lat_depth = np.asarray([[x["lon"], x["lat"], x["depth"]] for x in points])

    # Calculate rx ry from GC2
    rx, ry = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, np.asarray(sites), hypocentre_origin=True
    )

    # Gets the s_max values from the two end points of the fault
    nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)
    rx_end, ry_end = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
    )
    rx_end2, ry_end2 = src_site_dist.calc_rx_ry_GC2(
        lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
    )
    s_max = [min(ry_end, ry_end2)[0], max(ry_end, ry_end2)[0]]

    # Gets the plane index of the hypocenter
    plane_index = 0
    for index, plane in enumerate(planes):
        if plane["dhyp"] == -999.99:
            plane_index = index
            break

    # Trig to calculate extra features of the fault for directivity based on plane info
    z_tor = planes[plane_index]["dtop"]
    dip = planes[plane_index]["dip"]
    d_bot = z_tor + planes[plane_index]["width"] * math.sin(dip * math.pi / 180)
    t_bot = z_tor / math.tan(dip * math.pi / 180) + planes[0]["width"] * math.cos(dip * math.pi / 180)
    d = (planes[plane_index]["dhyp"] - z_tor) / math.sin(dip * math.pi / 180)

    # Ensures the model selects the type of fault based on the rake value
    force_type = 0

    # Use the bea20 model to work out directivity (fd) at the given sites
    fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20.bea20(
        mag, ry, rx, s_max, d, t_bot, d_bot, rake, dip, force_type, period
    )

    return fd
