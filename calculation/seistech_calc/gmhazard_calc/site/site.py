from typing import Union

import numpy as np

from gmhazard_calc import gm_data
from .SiteInfo import SiteInfo
from qcore.geo import closest_location


def get_site_from_coords(
    ensemble: Union[str, gm_data.Ensemble],
    lat: float,
    lon: float,
    user_vs30: float = None,
):
    """Returns a SiteInfo for the
    snapped location of the specified coordinates

    Parameters
    ----------
    ensemble: Ensemble
    lat: float
        Latitude
    lon: float
        Longitude
    user_vs30: float
        A user specified vs30, which potentially differs from the one used

    Returns
    -------
    SiteInfo
        Corresponding to the snapped location
    float
        Distance of the snapped location from the specified location
    """
    if isinstance(ensemble, str):
        ensemble = gm_data.Ensemble(ensemble)

    # Get the closest station
    i, d = closest_location(
        np.vstack((ensemble.stations.lon.values, ensemble.stations.lat.values)).T,
        lon,
        lat,
    )

    return (
        get_site_from_name(
            ensemble, ensemble.stations.index.values[i], user_vs30=user_vs30
        ),
        d,
    )


def get_site_from_name(
    ensemble: Union[str, gm_data.Ensemble],
    station_name: str,
    user_vs30: float = None,
):
    """Returns a SiteInfo for the specified station

    Parameters
    ----------
    ensemble: Ensemble
    station_name: str
    user_vs30: float, optional
        A user specified vs30, which potentially differs from the one used

    Returns
    -------
    SiteInfo
    """
    if isinstance(ensemble, str):
        ensemble = gm_data.Ensemble(ensemble)

    # Check the specified station is in the ensemble
    if station_name not in ensemble.stations.index.values:
        raise ValueError(
            f"The station name {station_name} is not a valid "
            f"station for ensemble {ensemble.name}."
        )

    # Get the db vs30 value for the specified station_name
    db_vs30 = (
        ensemble.vs30_df.loc[station_name, "vs30"]
        if ensemble.vs30_df is not None
        else None
    )
    # Get the Z values for the specified station_name
    z1p0 = (
        ensemble.z_df.loc[station_name, "Z1.0"]
        if ensemble.z_df is not None and station_name in ensemble.z_df.index
        else None
    )
    z2p5 = (
        ensemble.z_df.loc[station_name, "Z2.5"]
        if ensemble.z_df is not None and station_name in ensemble.z_df.index
        else None
    )

    mask = ensemble.stations.index.values == station_name
    lat = ensemble.stations.lat.values[mask][0]
    lon = ensemble.stations.lon.values[mask][0]

    return SiteInfo(
        station_name, lat, lon, db_vs30, user_vs30=user_vs30, z1p0=z1p0, z2p5=z2p5
    )
