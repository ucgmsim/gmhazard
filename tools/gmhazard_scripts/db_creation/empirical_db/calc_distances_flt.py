import os
import argparse

import numpy as np
import pandas as pd
from typing import Union, Dict

from qcore import nhm, formats
from IM_calculation.source_site_dist import src_site_dist

import gmhazard_calc as gc

# 1km divided by distance between points (1km/0.1km gives 100m grid)
POINTS_PER_KILOMETER = 1 / 0.1

# Calculation distance is 200, but larger
# distances are required for simulation disaggregation
RJB_MAX_DIST = 500
STATION_TOO_FAR_KEY = -1

DIR_SUPPORTED_TECTONIC_TYPYES = ["ACTIVE_SHALLOW", "VOLCANIC"]


def compute_site_source_distances(
    stations: np.ndarray,
    faults: Dict[str, Union[nhm.NHMFault, dict]],
    calculate_directivity: bool = True,
    n_procs: int = 1,
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
    calculate_directivity: bool, optional
        True to calculate directivity and return numpy array of
         site directivity amplification values per fault
    n_procs: int, optional
        Number of processes to use for the directivity
        calculation

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
    directivity = (
        np.full(
            fill_value=0,
            shape=(len(faults), len(stations), len(gc.im.DEFAULT_PSA_PERIODS) * 2),
            dtype=np.float64,
        )
        if calculate_directivity
        else None
    )

    n_faults = len(faults)
    faults = dict(sorted(faults.items(), key=lambda item: item[0]))
    for index, (cur_fault_name, cur_fault_data) in enumerate(faults.items()):
        print(f"Processing fault {(index + 1)} / {n_faults}")

        srf_header = None
        if isinstance(cur_fault_data, nhm.NHMFault):
            srf_header, srf_points = nhm.get_fault_header_points(
                faults[cur_fault_name]
            )
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

        if (
            calculate_directivity
            and cur_fault_data.tectonic_type in DIR_SUPPORTED_TECTONIC_TYPYES
        ):
            n_hypo_data = gc.directivity.NHypoData(
                gc.constants.HypoMethod.latin_hypercube, nhypo=100
            )
            fd, _, phi_red = gc.directivity.compute_fault_directivity(
                srf_points,
                srf_header,
                stations[~too_far_mask, :2],
                n_hypo_data,
                cur_fault_data.mw,
                cur_fault_data.rake,
                n_procs=n_procs,
            )

            directivity[index, ~too_far_mask, :31] = fd
            directivity[index, ~too_far_mask, 31:] = phi_red

        if srf_header is not None:
            (
                distances[index, :]["rx"][~too_far_mask],
                distances[index, :]["ry"][~too_far_mask],
            ) = src_site_dist.calc_rx_ry(
                srf_points, srf_header, stations[~too_far_mask], type=2
            )
        else:
            # Set Rx/Ry to rrup for point sources
            distances[index, :]["rx"][~too_far_mask] = rrup[~too_far_mask]
            distances[index, :]["ry"][~too_far_mask] = rrup[~too_far_mask]

    return distances, directivity


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
        "station_file",
        help="List of stations for a specific domain. Source to site distances "
        "will be calculated for all stations in the station_file.",
    )
    parser.add_argument(
        "--nhm_file", type=str, help="Path to the NHM ERF", default=None
    )
    parser.add_argument(
        "--gcmt_ffp", type=str, help="Path to the GCMT csv file", default=None
    )
    parser.add_argument(
        "--n_procs",
        help="Number of processes to use for the directivity calculation, "
        "does not affect distance calculation as it uses numba (uses all available cores)",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--no_directivity",
        action="store_false",
        dest="directivity",
        help="Flag to turn off directivity calculation",
        default=True,
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
    distances: np.ndarray, stations: pd.DataFrame, ssddb: gc.dbs.SiteSourceDB
):
    with ssddb as ssd:
        for index, station_name in enumerate(stations.index):
            station_mask = distances[:, index]["rjb"] != STATION_TOO_FAR_KEY
            if np.sum(station_mask) > 0:
                station_frame = pd.DataFrame(distances[:, index][station_mask])
                ssd.write_site_distances_data(station_name, station_frame)


def store_site_sources_directivity_data(
    directivity: np.ndarray, stations: pd.DataFrame, ssddb: gc.dbs.SiteSourceDB
):
    with ssddb as ssd:
        for index, station_name in enumerate(stations.index):
            station_frame = pd.DataFrame(
                directivity[:, index],
                columns=[
                    str(gc.im.IM(gc.im.IMType.pSA, period)) + mu_sigma
                    for mu_sigma in ["", "_sigma"]
                    for period in gc.im.DEFAULT_PSA_PERIODS
                ],
            )
            ssd.write_site_directivity_data(station_name, station_frame)


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

        site_source_distance_data, directivity_data = compute_site_source_distances(
            stations.to_numpy(),
            nhm_data,
            calculate_directivity=args.directivity,
            n_procs=args.n_procs,
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

        site_source_distance_data, directivity_data = compute_site_source_distances(
            stations.to_numpy(),
            fault_df.set_index("fault_name")
            .loc[:, ("lon", "lat", "depth")]
            .to_dict("index"),
            calculate_directivity=False,
        )

        fault_df = fault_df["fault_name"].to_frame()

    ssddb = gc.dbs.SiteSourceDB(
        args.ssddb, source_type=gc.constants.SourceType.fault, writeable=True
    )
    with ssddb as ssd:
        ssd.write_site_data(stations[["lon", "lat"]])
        ssd.write_fault_data(fault_df)
        ssd.write_attributes(
            os.path.basename(fault_data_ffp), os.path.basename(args.station_file)
        )

    store_site_sources_distance_data(site_source_distance_data, stations, ssddb)
    if directivity_data is not None:
        store_site_sources_directivity_data(directivity_data, stations, ssddb)


if __name__ == "__main__":
    main()
