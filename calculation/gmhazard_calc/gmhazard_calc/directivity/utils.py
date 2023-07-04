from typing import Sequence
import math

import numpy as np

from qcore.nhm import get_fault_header_points


def get_hypo_lon_lat(planes: Sequence, lon_lat_depth: np.ndarray):
    """
    Gets the approximate location of the hypocentre
    based on the lon lat depth values available for the fault

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
