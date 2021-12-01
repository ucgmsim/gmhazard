from typing import List
import math

import numpy as np

from sha_calc.directivity.bea20.EventType import EventType
from sha_calc.directivity.bea20.HypoMethod import HypoMethod
from sha_calc.directivity.bea20 import distributions


def set_hypocentres(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    method=HypoMethod.LATIN_HYPERCUBE,
):
    """
    Creates a List of planes each with a different set hypocentre for directivity calculations
    Sets a given amount of hypocentres along strike and down dip based on different distributions and the event type.

    Parameters
    ----------
    hypo_along_strike: int
        Number of hypocentres across strike to set
    hypo_down_dip: int
        Number of hypocentres down dip to set
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    method: HypoMethod, optional
        Method to place hypocentres across strike and dip
    """

    # Gets the total length and removes any previous hypocentres
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    if method == HypoMethod.LATIN_HYPERCUBE:
        return distributions.latin_hypercube(
            hypo_along_strike * hypo_down_dip, planes, event_type, total_length
        )
    elif method == HypoMethod.MONTE_CARLO:
        return distributions.monte_carlo_distribution(
            hypo_along_strike * hypo_down_dip, planes, event_type, total_length
        )
    elif method == HypoMethod.MONTE_CARLO_GRID:
        return distributions.monte_carlo_grid(
            hypo_along_strike, hypo_down_dip, planes, event_type, total_length
        )
    elif method == HypoMethod.GRID:
        return distributions.even_grid(
            hypo_along_strike, hypo_down_dip, planes, event_type, total_length
        )
    else:
        raise NotImplementedError(f"Method {method} is not currently implemented")


def calc_nominal_strike(traces: np.ndarray):
    """
    Gets the start and ending trace of the fault and ensures order for largest lon value first

    Parameters
    ----------
    traces: np.ndarray
        Array of traces of points across a fault with the format [[lon, lat, depth],...]
    """

    # Extract just lat and lon for the start and end of the traces
    trace_start, trace_end = [traces[0][0], traces[0][1]], [
        traces[-1][0],
        traces[-1][1],
    ]

    # Ensures correct order
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])


def get_hypo_lon_lat(planes: List, lon_lat_depth: np.ndarray):
    """
    Gets the approximate location of the hypocentre based on the lon lat depth values available for the fault

    Parameters
    ----------
    planes: List
        The list of planes with only 1 hypocentre location and the rest of dhyp/shyp being -999.9
    lon_lat_depth: np.ndarray
        The longitude latitude and depth values for the given fault from an srf or nhm file
    """
    length_from_start = 0
    previous_n = 0
    n_plane = 0
    hplane = []
    total_length = sum([plane["length"] for plane in planes])
    for i, plane in enumerate(planes):
        if plane["shyp"] != -999.9:
            ratio_length = round(
                (((total_length / 2) - length_from_start) + plane["shyp"])
                / plane["length"]
                * plane["nstrike"]
            )
            n_plane = plane["nstrike"] * plane["ndip"]
            hplane = plane
            break
        else:
            length_from_start += plane["length"]
            previous_n += plane["nstrike"] * plane["ndip"]

    lld_slice = lon_lat_depth[previous_n : previous_n + n_plane]
    hdepth = hplane["dhyp"] * math.sin(math.radians(hplane["dip"]))
    lld_depth_check = abs(lld_slice[:, 2] - hdepth)
    min_val = min(lld_depth_check)
    min_indices = [i for i, x in enumerate(lld_depth_check) if x == min_val]
    min_slice = lld_slice[min_indices]
    hypo = min_slice[ratio_length]

    return hypo[0], hypo[1]
