import numpy as np
from typing import List

from qcore import srf


def remove_plane_idx(planes: List):
    """
    Removes the idx from the plane

    Parameters
    ----------
    planes: List
        List of planes to remove the idx dict format from
    """
    new_planes = []
    for plane in planes:
        new_planes.append((
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
                ))
    return new_planes

def set_hypocenters(n_hypo: int, planes: List, depth_method: List):
    """
    Creates a List of planes each with a different set hypocenter for directivity calculations
    Sets n_hypo amount of hypocenters across the planes evenly

    Parameters
    ----------
    n_hypo: int
        Number of hypocenters across strike to set
    planes: list
        The planes to adjust and set the hypocenter on
    depth_method: List
        How deep the hypocenter is to be placed e.g. [0.5] would be every hypocenter at 50% depth
        where as [0.33, 0.66] would be every 2nd hypocenter would have a depth of 66% and every other would have 33%
    """

    # Gets the total length and removes any previous hypocenters
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    # Works out the distances across the length of the fault for each hypocenter
    distances = [(total_length/n_hypo * x) - ((total_length/n_hypo)/2) for x in range(1, n_hypo+1)]

    depth_index = 0
    planes_list = []
    planes_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if current_length < distance and (current_length + plane["length"]) > distance:
                plane["shyp"] = distance - (current_length + plane["length"] / 2)
                plane["dhyp"] = plane["width"] * depth_method[depth_index]
                depth_index = (depth_index + 1) % len(depth_method)
                planes_index.append(index)
            current_length += plane["length"]
        planes_list.append(planes_copy)
    return planes_list, planes_index


def calc_nominal_strike(traces):
    """Gets the start and ending trace of the fault and ensures order for largest lat value first"""
    depth = traces[0][2]
    trace_end_index = 0
    for index, trace in enumerate(traces):
        if depth != trace[2]:
            trace_end_index = index - 1
            break
    trace_start, trace_end = [traces[0][0], traces[0][1]], [
        traces[trace_end_index][0],
        traces[trace_end_index][1],
    ]
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])