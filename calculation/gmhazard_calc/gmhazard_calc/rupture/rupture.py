import math
from typing import TYPE_CHECKING, List, Dict, Union

import pandas as pd
import numpy as np

from gmhazard_calc import utils
from gmhazard_calc import constants as const
from qcore import nhm, geo

if TYPE_CHECKING:
    from gmhazard_calc import gm_data

RUPTURE_FAULT_DF_COLUMNS = [
    "rupture_name",
    "annual_rec_prob",
    "magnitude",
    "tectonic_type",
]
RUPTURE_DS_DF_COLUMNS = ["rupture_name", "annual_rec_prob", "magnitude"]
POINTS_PER_KILOMETER = (
    1 / 0.1
)  # 1km divided by distance between points (1km/0.1km gives 100m grid)


def rupture_df_from_erf(
    erf_ffp: str, erf_file_type: const.ERFFileType = const.ERFFileType.flt_nhm
):
    """Creates a standardised pandas dataframe for the
    ruptures in the given erf file.

    Parameters
    ----------
    erf_ffp : str
        Path to the ERF file
    erf_file_type : ERFFileType
        Type of the erf file

    Returns
    -------
    DataFrame
        index = rupture id
        columns = [rupture name, annual recurrence probability, magnitude, tectonic type]
    """
    erf_name = utils.get_erf_name(erf_ffp)
    if erf_file_type is const.ERFFileType.flt_nhm:
        nhm_infos = nhm.load_nhm(erf_ffp)

        rupture_dict = {
            f"{info.name}_{erf_name}": [
                info.name,
                1 / info.recur_int_median,
                info.mw,
                info.tectonic_type,
            ]
            for key, info in nhm_infos.items()
            if info.recur_int_median > 0
        }

        return pd.DataFrame.from_dict(
            rupture_dict, orient="index", columns=RUPTURE_FAULT_DF_COLUMNS
        ).sort_index()

    elif erf_file_type is const.ERFFileType.ds_erf:
        df = pd.read_csv(erf_ffp)
        df.columns = RUPTURE_DS_DF_COLUMNS
        df.index = rupture_name_to_id(df.rupture_name.values.astype(str), erf_ffp)
        return df.sort_index()

    raise NotImplementedError("The specified erf file type is currently not supported")


def rupture_name_to_id(rupture_names: np.ndarray, erf_ffp: str):
    """Converts the given ruptures names to rupture ids

    Parameters
    ----------
    rupture_names: numpy array of strings
    erf_name: str

    Returns
    -------
    numpy array of strings
    """
    return np.char.add(rupture_names.astype(str), f"_{utils.get_erf_name(erf_ffp)}")


def rupture_id_to_ix(
    ensemble: "gm_data.Ensemble",
    rupture_ids: np.ndarray,
):
    """Converts the rupture_id values to rupture_id_ix values
    Note: Should only be used for DS at this stage
    """
    return ensemble.get_rupture_id_indices(rupture_ids)


def rupture_name_to_id_ix(
    ensemble: "gm_data.Ensemble",
    erf_ffp: str,
    rupture_names: np.ndarray,
):
    """Convertes the rupture names to rupture_id_ix values"""
    return rupture_id_to_ix(ensemble, rupture_name_to_id(rupture_names, erf_ffp))


def rupture_id_ix_to_rupture_id(
    ensemble: "gm_data.Ensemble", rupture_id_ind: np.ndarray
):
    """Converts rupture id ix to rupture ids"""
    return ensemble.get_rupture_ids(rupture_id_ind)


def get_fault_header_points(fault: nhm.NHMFault):
    """
    Calculates and produces fault information such as the entire trace and fault header info per plane

    Parameters
    ----------
    fault: nhm.NHMFault
        A fault object from an NHM file
    """
    srf_points = []
    srf_header: List[Dict[str, Union[int, float]]] = []
    lon1, lat1 = fault.trace[0]
    lon2, lat2 = fault.trace[1]
    strike = geo.ll_bearing(lon1, lat1, lon2, lat2, midpoint=True)

    # If the dip direction is not to the right of the strike, turn the fault around
    indexes = (
        np.arange(len(fault.trace))
        if 180 > fault.dip_dir - strike >= 0
        else np.flip(np.arange(len(fault.trace)))
    )

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
            srf_points.append([top_lon, top_lat, fault.dtop])

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
                srf_points.append([new_lon, new_lat, vdist])

        plane_offset += nstrike * ndip
        srf_header.append(
            {
                "nstrike": nstrike,
                "ndip": ndip,
                "strike": strike,
                "length": plane_point_distance,
                "dip": fault.dip,
                "dtop": fault.dtop,
                "width": fault.dbottom / math.sin(math.radians(fault.dip)),
                "dhyp": -999.9,
                "shyp": -999.9,
            }
        )

    return srf_header, np.asarray(srf_points)
