import argparse
import numpy as np
import os
import pandas as pd
from typing import List, Union, Dict

from qcore import nhm, formats, geo
from IM_calculation.source_site_dist import src_site_dist

import gmhazard_calc as sc

POINTS_PER_KILOMETER = (
    1 / 0.1
)  # 1km divided by distance between points (1km/0.1km gives 100m grid)

RJB_MAX_DIST = 500  # Calculation distance is 200, but larger distances are required for simulation disaggregation
STATION_TOO_FAR_KEY = -1


def compute_site_source_distances(
    stations: np.ndarray, faults: Dict[str, Union[nhm.NHMFault, dict]]
):
    """
    Computes the site-source distances for the given stations and faults

    Parameters
    ----------
    stations: numpy array of floats
        The stations data
        Format: [lon, lat]
    faults: dictionary
        Either a fault_name -> NHMFault object dictionary or
        fault_name -> dictionary with keys [lon, lat, depth]
        The first format is used for calculating site-source distances for
        finite faults and the 2nd for computing site-source distances for
        point sources

    Returns
    -------
    structured numpy array
        With columns [fault_id, rjb, rrup, rx, ry, rtvz]
    """
    distances = np.full(
        fill_value=STATION_TOO_FAR_KEY,
        shape=(len(faults), len(stations)),
        dtype=[
            ("fault_id", np.int64),
            ("rjb", np.float64),
            ("rrup", np.float64),
            ("rx", np.float64),
            ("ry", np.float64),
            ("rtvz", np.float64),
        ],
    )

    n_faults = len(faults)
    faults = dict(sorted(faults.items(), key=lambda item: item[0]))
    for index, (cur_fault_name, cur_fault_data) in enumerate(faults.items()):
        print(f"Processing fault {(index + 1)} / {n_faults}")

        srf_header = None
        if isinstance(cur_fault_data, nhm.NHMFault):
            srf_header, srf_points = get_fault_header_points(faults[cur_fault_name])
            srf_points = np.asarray(srf_points)
        # Point source
        else:
            srf_points = np.asarray(
                [
                    [
                        cur_fault_data["lon"],
                        cur_fault_data["lat"],
                        cur_fault_data["depth"],
                    ]
                ]
            )

        rrup, rjb = src_site_dist.calc_rrup_rjb(srf_points, stations)

        too_far_mask = rjb > RJB_MAX_DIST

        distances[index, :]["fault_id"] = index

        distances[index, :]["rrup"][~too_far_mask] = rrup[~too_far_mask]
        distances[index, :]["rjb"][~too_far_mask] = rjb[~too_far_mask]

        distances[index, :]["rtvz"] = float("nan")

        if srf_header is not None:
            (
                distances[index, :]["rx"][~too_far_mask],
                distances[index, :]["ry"][~too_far_mask],
            ) = src_site_dist.calc_rx_ry(
                srf_points, srf_header, stations[~too_far_mask], type=1
            )
        else:
            # Set Rx/Ry to rrup for point sources
            distances[index, :]["rx"][~too_far_mask] = rrup[~too_far_mask]
            distances[index, :]["ry"][~too_far_mask] = rrup[~too_far_mask]

    return distances


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


def load_args():
    parser = argparse.ArgumentParser(
        "Script for calculating source-site-distances for the specified faults and stations"
    )
    parser.add_argument(
        "ssddb",
        type=str,
        default="flt_site_source.db",
        help="Path to the DB to be written",
    )
    parser.add_argument(
        "--nhm_file", type=str, help="Path to the NHM ERF", default=None
    )
    parser.add_argument(
        "--gcmt_ffp", type=str, help="Path to the GCMT csv file", default=None
    )
    parser.add_argument(
        "station_file",
        help="List of stations for a specific domain. Source to site distances "
        "will be calculated for all stations in the station_file.",
    )

    args = parser.parse_args()

    if args.nhm_file is None and args.gcmt_ffp is None:
        raise argparse.ArgumentError(
            "Either the nhm_file or the gcmt_ffp option have to be specified, quitting!"
        )
    if args.nhm_file is not None and args.gcmt_ffp is not None:
        raise argparse.ArgumentError(
            "Only one of nhm_file and gcmt_ffp should be specified, quitting!"
        )

    return args


def store_site_sources_distance_data(
    distances: np.ndarray, stations: pd.DataFrame, ssddb: sc.dbs.SiteSourceDB
):
    with ssddb as ssd:
        for index, station_name in enumerate(stations.index):
            station_mask = distances[:, index]["rjb"] != STATION_TOO_FAR_KEY
            if np.sum(station_mask) > 0:
                station_frame = pd.DataFrame(distances[:, index][station_mask])
                ssd.write_site_distances_data(station_name, station_frame)


def main():
    args = load_args()
    if os.path.exists(args.ssddb):
        print(f"A site-source db already exists at location {args.ssddb}")

    stations = formats.load_station_file(args.station_file)
    stations.insert(2, "depth", 0)

    if args.nhm_file is not None:
        fault_data_ffp = os.path.abspath(args.nhm_file)
        nhm_data = nhm.load_nhm(fault_data_ffp)
        fault_df = pd.DataFrame(sorted(nhm_data.keys()), columns=["fault_name"])

        site_source_distance_data = compute_site_source_distances(
            stations.to_numpy(), nhm_data
        )
    else:
        fault_data_ffp = os.path.abspath(args.gcmt_ffp)
        fault_df = pd.read_csv(fault_data_ffp)
        fault_df.rename(
            columns={
                "PublicID": "fault_name",
                "Latitude": "lat",
                "Longitude": "lon",
                "CD": "depth",
            },
            inplace=True,
        )
        fault_df = fault_df.sort_values("fault_name").set_index(
            np.arange(fault_df.shape[0])
        )

        site_source_distance_data = compute_site_source_distances(
            stations.to_numpy(),
            fault_df.set_index("fault_name")
            .loc[:, ("lon", "lat", "depth")]
            .to_dict("index"),
        )

        fault_df = fault_df["fault_name"].to_frame()

    ssddb = sc.dbs.SiteSourceDB(
        args.ssddb, source_type=sc.constants.SourceType.fault, writeable=True
    )
    with ssddb as ssd:
        ssd.write_site_data(stations[["lon", "lat"]])
        ssd.write_fault_data(fault_df)
        ssd.write_attributes(
            os.path.basename(fault_data_ffp), os.path.basename(args.station_file)
        )

    store_site_sources_distance_data(site_source_distance_data, stations, ssddb)


if __name__ == "__main__":
    main()
