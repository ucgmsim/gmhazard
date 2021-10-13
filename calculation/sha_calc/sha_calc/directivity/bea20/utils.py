from typing import List

import numpy as np


def remove_plane_idx(planes: List):
    """
    Removes the idx from the plane

    Parameters
    ----------
    planes: List
        List of planes to remove the idx dict format from
    """
    return [
        (
            float(plane["centre"][0]),
            float(plane["centre"][1]),
            int(plane["nstrike"]),
            int(plane["ndip"]),
            float(plane["length"]),
            float(plane["width"]),
            plane["strike"],
            plane["dip"],
            plane["dtop"],
            plane["shyp"],
            plane["dhyp"],
        )
        for plane in planes
    ]


def set_hypocentres(n_hypo: int, planes: List, depth_method: List):
    """
    Creates a List of planes each with a different set hypocentre for directivity calculations
    Sets n_hypo amount of hypocentres across the planes evenly

    Parameters
    ----------
    n_hypo: int
        Number of hypocentres across strike to set
    planes: list
        The planes to adjust and set the hypocentre on
    depth_method: List
        How deep the hypocentre is to be placed e.g. [0.5] would be every hypocentre at 50% depth
        where as [0.33, 0.66] would be every 2nd hypocentre would have a depth of 66% and every other would have 33%
    """

    # Gets the total length and removes any previous hypocentres
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    # Works out the distances across the length of the fault for each hypocentre
    distances = [
        (total_length / n_hypo * x) - ((total_length / n_hypo) / 2)
        for x in range(1, n_hypo + 1)
    ]

    depth_index = 0
    planes_list = []
    planes_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if (
                current_length < distance
                and (current_length + plane["length"]) > distance
            ):
                plane["shyp"] = distance - (current_length + plane["length"] / 2)
                plane["dhyp"] = plane["width"] * depth_method[depth_index]
                depth_index = (depth_index + 1) % len(depth_method)
                planes_index.append(index)
            current_length += plane["length"]
        planes_list.append(planes_copy)
    return planes_list, planes_index


def calc_nominal_strike(traces: np.ndarray):
    """
    Gets the start and ending trace of the fault and ensures order for largest lon value first

    Parameters
    ----------
    traces: np.ndarray
        Array of traces of points across a fault with the format [[lon, lat, depth],...]
    """
    # Lowest depth point
    depth = traces[0][2]
    trace_end_index = 0

    # Loops to find the last point with that depth value to find the end points of the fault at the highest depth
    for index, trace in enumerate(traces):
        if depth != trace[2]:
            trace_end_index = index - 1
            break

    # Extract just lat and lon for the start and end of the traces
    trace_start, trace_end = [traces[0][0], traces[0][1]], [
        traces[trace_end_index][0],
        traces[trace_end_index][1],
    ]

    # Ensures correct order
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])
