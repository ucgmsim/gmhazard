import math
from typing import Sequence

import numpy as np

from IM_calculation.source_site_dist import src_site_dist
from gmhazard_calc.directivity import utils
from .HypoMethod import HypoMethod
from .EventType import EventType
from .NHypoData import NHypoData
import sha_calc


def compute_fault_directivity(
    lon_lat_depth: np.ndarray,
    planes: Sequence,
    sites: np.ndarray,
    n_hypo_data: NHypoData,
    mag: float,
    rake: float,
    periods: Sequence[float] = sha_calc.constants.DEFAULT_PSA_PERIODS,
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
    n_hypo_data: NHypoData
        Dataclass to store information on number of hypocentres and the method for placement
    mag: float
        The magnitude of the fault
    rake: float
        The rake of the fault
    periods: List[float], optional
        The periods to calculate for the bea20 model's fD
        If not set then will be all the default pSA periods for GMHazard
    """
    nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)

    # Customise the planes to set different hypocentres
    planes_list, plane_index_list, weights = utils.set_hypocentres(
        n_hypo_data,
        planes,
        EventType.from_rake(rake),
    )

    # Creating the array to store all fdi values
    fdi_array = np.zeros(
        (n_hypo_data.nhypo, len(sites), len(periods))
    )
    phired_array = np.zeros(
        (n_hypo_data.nhypo, len(sites), len(periods))
    )
    for index, planes in enumerate(planes_list):
        # Gets the plane index of the hypocentre
        plane_index = plane_index_list[index]

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

        fdi_array[index] = fdi
        phired_array[index] = phi_red

    if n_hypo_data.method == HypoMethod.UNIFORM_GRID:
        # Only apply weights if method type is uniform grid
        fdi_average = weights[:, None, None] * fdi_array
        phired_average = weights[:, None, None] * phired_array
        fdi_average = np.sum(fdi_average, axis=0)
        phired_average = np.sum(phired_average, axis=0)
    else:
        # Just average the fdi array for all other methods
        fdi_average = np.mean(fdi_array, axis=0)
        phired_average = np.mean(phired_array, axis=0)

    return fdi_average, fdi_array, phired_average


def _compute_directivity_effect(
    lon_lat_depth: np.ndarray,
    planes: Sequence,
    plane_index: int,
    sites: np.ndarray,
    nominal_strike: np.ndarray,
    nominal_strike2: np.ndarray,
    mag: float,
    rake: float,
    periods: Sequence[float],
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
    d = planes[plane_index]["dhyp"]

    # Use the bea20 model to work out directivity (fd) at the given sites
    fd, phi_red, predictor_functions, other = sha_calc.directivity.bea20.bea20(
        mag, ry, rx, s_max, d, t_bot, d_bot, rake, dip, np.asarray(periods)
    )
    return fd, (phi_red, predictor_functions, other)
