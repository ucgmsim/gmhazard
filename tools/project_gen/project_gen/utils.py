from typing import Dict

import numpy as np

import gmhazard_calc as gc


def get_site_infos(project_params: Dict):
    """Get the site infos from the project params"""
    site_infos = []

    for cur_loc_id in project_params["locations"]:
        # Use the specified names
        names = project_params["locations"][cur_loc_id].get("names")
        cur_lon = project_params["locations"][cur_loc_id]["lon"]
        cur_lat = project_params["locations"][cur_loc_id]["lat"]

        # Otherwise generate names
        for cur_ix, (cur_vs30, cur_z1p0, cur_2p5) in enumerate(
            zip(
                project_params["locations"][cur_loc_id]["vs30"],
                project_params["locations"][cur_loc_id]["z1.0"],
                project_params["locations"][cur_loc_id]["z2.5"],
            )
        ):
            site_infos.append(gc.site.SiteInfo(
                names[cur_ix]
                if names is not None
                else __create_station_id(cur_loc_id, cur_vs30, cur_z1p0, cur_2p5),
                cur_lat, cur_lon, cur_vs30, z1p0=cur_z1p0, z2p5=cur_2p5
            ))

    return site_infos


def __create_station_id(loc_name, vs30, z1p0=None, z2p5=None):
    """ Creates a projects station id based on if Z1.0/Z2.5 values were specified or not"""
    station_id = f"{loc_name}_{str(vs30).replace('.', 'p')}"
    if z1p0 is not None and z2p5 is not None:
        station_id += f"_{str(z1p0).replace('.', 'p')}_{str(z2p5).replace('.', 'p')}"
    return station_id
