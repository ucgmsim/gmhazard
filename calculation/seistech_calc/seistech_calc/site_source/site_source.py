from typing import Union

import numpy as np
import pandas as pd


import seistech_calc.dbs as dbs
import seistech_calc.site as site
import seistech_calc.constants as const

def get_distance_df(
    site_source_db_ffp: str, site_info: site.SiteInfo
) -> Union[None, pd.DataFrame]:
    """Retrieves the distances for all sources for the specified site

    Parameters
    ----------
    site_source_db_ffp: str
        Path to the site source db
    site_info: SiteInfo
        The site of interest

    Returns
    -------
    pd.DataFrame
        format: index = fault_name, columns = [rjb, rrup, rx, ry, rtvz]
    """
    with dbs.SiteSourceDB(site_source_db_ffp) as db:
        return db.station_data(site_info.station_name)


def rupture_id_to_loc_name(rupture_ids: np.ndarray, src_type: const.SourceType) -> pd.Series:
    """Converts rupture ids to location names,
    for DS the location name is just the lon/lat part of the rupture id and
    for fault it is that fault name

    Parameters
    ----------
    rupture_ids: np.array of strings
        The rupture ids to convert, have to all be of the same
        source type
    src_type: const.SourceType
        Source type of the rupture ids to convert

    Returns
    -------
    pd.Series
        format: index = rupture id, value = location name
    """
    if src_type is const.SourceType.distributed:
        loc_names = np.asarray(
            list(np.chararray.split(rupture_ids.astype(str), "--")), dtype=str
        )[:, 0]
    else:
        loc_names = np.asarray(
            list(np.chararray.split(rupture_ids.astype(str), "_")), dtype=str
        )[:, 0]

    return pd.Series(index=rupture_ids, data=loc_names)

def match_ruptures(
    distance_df: pd.DataFrame,
    data_df: Union[pd.DataFrame, pd.Series],
    src_type: const.SourceType,
) -> pd.DataFrame:
    """Merges the distance dataframe with the data dataframe.

    Parameters
    ----------
    distance_df: pd.DataFrame
        The distance dataframe from distance_df function
        format: index = fault_name, columns = [rjb, rrup, rx, ry, rtvz]
    data_df: pd.DataFrame or pd.Series
        Dataframe that contains some data, the index has to be
        the rupture_id to use for matching
    src_type: const.SourceType
        The source type of the data dataframe

    Returns
    -------
    pd.DataFrame
        The data_df with the distance data
    """
    if isinstance(data_df, pd.Series):
        data_df = data_df.to_frame()

    loc_names = rupture_id_to_loc_name(data_df.index.values.astype(str), src_type)
    if src_type is const.SourceType.distributed:
        data_df["loc_name"] = loc_names.values
        data_df["rupture_id"] = data_df.index.values
        data_df = pd.merge(
            data_df, distance_df, how="left", left_on="loc_name", right_on="fault_name"
        )
        data_df.drop(columns=["loc_name"], inplace=True)
        return data_df.set_index("rupture_id")

    elif src_type is const.SourceType.fault:
        data_df["rupture_name"] = loc_names.values
        data_df["rupture_id"] = data_df.index.values
        data_df = pd.merge(
            data_df,
            distance_df,
            how="left",
            left_on="rupture_name",
            right_on="fault_name",
        )
        data_df.drop(columns=["rupture_name"], axis=1, inplace=True)
        return data_df.set_index("rupture_id")
