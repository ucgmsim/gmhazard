from typing import List

import numpy as np
from EventType import EventType
import distributions


def set_hypocentres(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    fault_name: str = "Nothing",
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
    """

    # Gets the total length and removes any previous hypocentres
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    # return distributions.monte_carlo_distribution(hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length)

    # return distributions.monte_carlo_grid(
    #     hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length
    # )
    #
    return distributions.latin_hypercube(
        hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length
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
