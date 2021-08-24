from typing import Dict


def get_station_ids(project_params: Dict):
    """Get the full list of stations ids from the project parameters"""
    station_ids = []
    for cur_loc_id in project_params["locations"]:
        for cur_list_ind, cur_vs30 in enumerate(
            project_params["locations"][cur_loc_id]["vs30"]
        ):
            z1p0 = project_params["locations"][cur_loc_id]["z1.0"][cur_list_ind]
            z2p5 = project_params["locations"][cur_loc_id]["z2.5"][cur_list_ind]
            station_ids.append(
                create_station_id(cur_loc_id, cur_vs30, z1p0=z1p0, z2p5=z2p5)
            )
    return station_ids


def create_station_id(loc_name, vs30, z1p0=None, z2p5=None):
    """ Creates a projects station id based on if Z1.0/Z2.5 values were specified or not"""
    station_id = f"{loc_name}_{str(vs30).replace('.', 'p')}"
    if z1p0 is not None and z2p5 is not None:
        station_id += f"_{str(z1p0).replace('.', 'p')}_{str(z2p5).replace('.', 'p')}"
    return station_id
