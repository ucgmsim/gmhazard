from typing import List, Dict, Union

import numpy as np

from qcore import nhm, geo

POINTS_PER_KILOMETER = (
    1 / 0.1
)  # 1km divided by distance between points (1km/0.1km gives 100m grid)


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
            if current_length < distance < (current_length + plane["length"]):
                plane["shyp"] = distance - (total_length / 2)
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


def get_fault_header_points(fault: nhm.NHMFault):
    srf_points = []
    srf_header: List[Dict[str, Union[int, float]]] = []
    lon1, lat1 = fault.trace[0]
    lon2, lat2 = fault.trace[1]
    strike = geo.ll_bearing(lon1, lat1, lon2, lat2, midpoint=True)

    if 180 > fault.dip_dir - strike >= 0:
        # If the dipdir is not to the right of the strike, turn the fault around
        indexes = range(len(fault.trace))
    else:
        indexes = range(len(fault.trace) - 1, -1, -1)

    plane_offset = 0
    for i, i2 in zip(indexes[:-1], indexes[1:]):
        lon1, lat1 = fault.trace[i]
        lon2, lat2 = fault.trace[i2]

        strike = geo.ll_bearing(lon1, lat1, lon2, lat2, midpoint=True)
        plane_point_distance = geo.ll_dist(lon1, lat1, lon2, lat2)

        nstrike = round(plane_point_distance * POINTS_PER_KILOMETER)
        strike_dist = plane_point_distance / nstrike

        end_strike = geo.ll_bearing(lon1, lat1, lon2, lat2)
        for j in range(nstrike):
            top_lat, top_lon = geo.ll_shift(lat1, lon1, strike_dist * j, end_strike)
            srf_points.append((top_lon, top_lat, fault.dtop))

        height = fault.dbottom - fault.dtop

        width = abs(height / np.tan(np.deg2rad(fault.dip)))
        dip_dist = height / np.sin(np.deg2rad(fault.dip))

        ndip = int(round(dip_dist * POINTS_PER_KILOMETER))
        hdip_dist = width / ndip
        vdip_dist = height / ndip

        for j in range(1, ndip):
            hdist = j * hdip_dist
            vdist = j * vdip_dist + fault.dtop
            for local_lon, local_lat, local_depth in srf_points[
                plane_offset : plane_offset + nstrike
            ]:
                new_lat, new_lon = geo.ll_shift(
                    local_lat, local_lon, hdist, fault.dip_dir
                )
                srf_points.append((new_lon, new_lat, vdist))

        plane_offset += nstrike * ndip
        srf_header.append({"nstrike": nstrike, "ndip": ndip, "strike": strike})

    return srf_header, srf_points