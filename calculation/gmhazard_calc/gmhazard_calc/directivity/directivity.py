import math
import multiprocessing as mp
from typing import Sequence
from dataclasses import dataclass

import numpy as np

import sha_calc
from IM_calculation.source_site_dist import src_site_dist
from gmhazard_calc.directivity import hypo_sampling
from gmhazard_calc.im import DEFAULT_PSA_PERIODS
from gmhazard_calc import constants


@dataclass
class NHypoData:
    """
    Class for keeping track of the
    correct number of hypocentre parameters
    for their method of placement
    """

    method: constants.HypoMethod
    nhypo: int = None
    hypo_along_strike: int = None
    hypo_down_dip: int = None
    seed: int = None

    def __post_init__(self):
        """
        Checks to ensure that the given parameters are correct for the method specified
        """
        if self.method == constants.HypoMethod.uniform_grid:
            if self.hypo_along_strike is None or self.hypo_down_dip is None:
                raise ValueError(
                    f"hypo_along_strike and hypo_down_dip need to be defined for {str(self.method)}"
                )
            else:
                self.nhypo = self.hypo_along_strike * self.hypo_down_dip
        elif (
            self.method == constants.HypoMethod.latin_hypercube
            or self.method == constants.HypoMethod.monte_carlo
        ):
            if self.nhypo is None:
                raise ValueError(f"nhypo needs to be defined for {str(self.method)}")


def set_hypocentres(
    n_hypo_data: NHypoData,
    planes: Sequence,
    event_type: constants.EventType,
):
    """
    Creates a List of planes each with a different set hypocentre for directivity calculations
    Sets a given amount of hypocentres along strike and down dip based on different distributions
    And the method and event type.

    Parameters
    ----------
    n_hypo_data: NHypoData
        Dataclass to store information on number of hypocentres and the method for placement
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    """
    # Gets the total length and removes any previous hypocentres
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    if n_hypo_data.method == constants.HypoMethod.latin_hypercube:
        return hypo_sampling.latin_hypercube_sampling(
            n_hypo_data.nhypo, planes, event_type, total_length, n_hypo_data.seed
        )
    elif n_hypo_data.method == constants.HypoMethod.monte_carlo:
        return hypo_sampling.mc_sampling(
            n_hypo_data.nhypo, planes, event_type, total_length, n_hypo_data.seed
        )
    elif n_hypo_data.method == constants.HypoMethod.uniform_grid:
        return hypo_sampling.uniform_grid(
            n_hypo_data.hypo_along_strike,
            n_hypo_data.hypo_down_dip,
            planes,
            event_type,
            total_length,
        )
    else:
        raise NotImplementedError(
            f"Method {n_hypo_data.method} is not currently implemented"
        )


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


def compute_fault_directivity(
    lon_lat_depth: np.ndarray,
    planes: Sequence,
    sites: np.ndarray,
    n_hypo_data: NHypoData,
    mag: float,
    rake: float,
    periods: Sequence[float] = DEFAULT_PSA_PERIODS,
    n_procs: int = 1,
):
    """
    Does the computation of directivity for a fault
    With any number of hypocentres.
    Can compute regardless if data came from an srf or nhm file.

    Parameters
    ----------
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format
        [[lon, lat, depth],...]
    planes: List
        List of the planes that make up the fault
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    n_hypo_data: NHypoData
        Dataclass to store information on number of hypocentres
        and the method for placement
    mag: float
        The magnitude of the fault
    rake: float
        The rake of the fault
    periods: List[float], optional
        The periods to calculate for the bea20 model's fD
        If not set then will be all the default pSA periods for GMHazard
    """
    nominal_strike, nominal_strike2 = calc_nominal_strike(lon_lat_depth)

    # Customise the planes to set different hypocentres
    hypo_planes, plane_ind, weights = set_hypocentres(
        n_hypo_data,
        planes,
        constants.EventType.from_rake(rake),
    )

    # Extract all hypocentre locations across strike
    shyps = np.asarray(
        [
            plane["shyp"]
            for hypo in hypo_planes
            for plane in hypo
            if plane["shyp"] != -999.9
        ]
    )
    # Combine nominal strike to the end of the site coords for computation speed
    combined_coords = np.concatenate([sites, nominal_strike, nominal_strike2])

    # Calculate rx ry from GC2
    rx, ry = src_site_dist.calc_rx_ry_GC2_multi_hypocentre(
        lon_lat_depth, planes, combined_coords, origin_offsets=shyps
    )

    # Extract the nominal strike ry values
    ry_start, ry_end = ry[:, -2], ry[:, -1]
    # Remove nominal strike rx, ry values from rx, ry
    rx, ry = rx[:, :-2], ry[:, :-2]

    if n_procs == 1:
        fdi, phired = [], []
        for ix, cur_planes in enumerate(hypo_planes):
            cur_fdi, (cur_phi_red, _, __) = _compute_directivity_effect(
                cur_planes,
                plane_ind[ix],
                rx[ix],
                ry[ix],
                ry_start[ix],
                ry_end[ix],
                mag,
                rake,
                periods,
            )

            fdi.append(cur_fdi)
            phired.append(cur_phi_red)
    else:
        # Compute directivity for all hypocentres
        with mp.Pool(n_procs) as pool:
            results = pool.starmap(
                _compute_directivity_effect,
                [
                    (
                        cur_planes,
                        plane_ind[ix],
                        rx[ix],
                        ry[ix],
                        ry_start[ix],
                        ry_end[ix],
                        mag,
                        rake,
                        periods,
                    )
                    for (ix, cur_planes) in enumerate(hypo_planes)
                ],
            )

        # Select fdi and phi_red from the results
        fdi = [cur_result[0] for cur_result in results]
        phired = [cur_result[1][0] for cur_result in results]

    # Combine results
    fdi = np.stack(fdi, axis=0)
    phired = np.stack(phired, axis=0)

    # Apply weights if uniform grid
    if n_hypo_data.method == constants.HypoMethod.uniform_grid:
        fdi_average = np.sum(weights[:, None, None] * fdi, axis=0)
        phired_average = np.sum(weights[:, None, None] * phired, axis=0)
    # Otherwise use average
    else:
        fdi_average = np.mean(fdi, axis=0)
        phired_average = np.mean(phired, axis=0)

    return fdi_average, fdi, phired_average


def _compute_directivity_effect(
    planes: Sequence,
    plane_index: int,
    rx: np.ndarray,
    ry: np.ndarray,
    ry_start: float,
    ry_end: float,
    mag: float,
    rake: float,
    periods: Sequence[float],
):
    """
    Does the computation of directivity and GC2 given a set of planes
    with a set hypocentre.

    Parameters
    ----------
    planes: List
        List of the planes that make up the fault
    plane_index: int
        The index in planes that the hypocentre is located in
    rx: np.ndarray
        The GC2 coordinates in km. Equivalent to U.
        A 1d array of length n where n is the number of sites.
    ry: np.ndarray
        The GC2 coordinates in km. Equivalent to T.
        A 1d array of length n where n is the number of sites.
    ry_start: float
        Ry value at the starting point of nominal strike
        (starting edge of the fault)
    ry_end: float
        Ry value at the ending point of nominal strike
        (ending edge of the fault)
    mag: float
        The magnitude of the fault
    rake: float
        The rake of the fault
    periods: List[float]
        The periods to calculate for the bea20 model's fD
    """
    # Gets the s_max ry values from the two end points of the fault in order
    s_max = (min(ry_start, ry_end), max(ry_start, ry_end))

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
