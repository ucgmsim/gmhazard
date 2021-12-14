from typing import Sequence
import math

import numpy as np

from gmhazard_calc.directivity import hypo_sampling
from gmhazard_calc.rupture import get_fault_header_points
from .EventType import EventType
from .HypoMethod import HypoMethod


def set_hypocentres(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: Sequence,
    event_type: EventType,
    method=HypoMethod.LATIN_HYPERCUBE,
):
    """
    Creates a List of planes each with a different set hypocentre for directivity calculations
    Sets a given amount of hypocentres along strike and down dip based on different distributions
    And the method and event type.

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
        return hypo_sampling.latin_hypercube(
            hypo_along_strike * hypo_down_dip, planes, event_type, total_length
        )
    elif method == HypoMethod.MONTE_CARLO:
        return hypo_sampling.mc_sampling(
            hypo_along_strike * hypo_down_dip, planes, event_type, total_length
        )
    elif method == HypoMethod.UNIFORM_GRID:
        return hypo_sampling.even_grid(
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


def get_hypo_lon_lat(planes: Sequence, lon_lat_depth: np.ndarray):
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


def load_fault_info(fault_name: str, nhm_dict: dict, grid_space: int):
    """
    Loads the fault information for a given fault and sets up a grid of sites around the fault

    Parameters
    ----------
    fault_name: str
        Fault to grab information for
    nhm_dict: dict
        Dictionary of the nhm fault information given from an nhm file
    grid_space: int
        Number of sites to generate along one axis ( total sites = grid_space * grid_space )

    """
    fault = nhm_dict[fault_name]
    planes, lon_lat_depth = get_fault_header_points(fault)

    lon_values = np.linspace(
        lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, grid_space
    )
    lat_values = np.linspace(
        lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, grid_space
    )

    x, y = np.meshgrid(lon_values, lat_values)
    site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

    return fault, site_coords, planes, lon_lat_depth, x, y
