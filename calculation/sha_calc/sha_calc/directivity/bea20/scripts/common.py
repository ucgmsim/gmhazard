import numpy as np

import gmhazard_calc
from gmhazard_calc.im import IM, IMType
from qcore import nhm


def load_fault_info(fault_name: str, nhm_dict: dict, grid_space: int):
    fault = nhm_dict[fault_name]
    planes, lon_lat_depth = gmhazard_calc.rupture.get_fault_header_points(fault)

    lon_values = np.linspace(
        lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, grid_space
    )
    lat_values = np.linspace(
        lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, grid_space
    )

    x, y = np.meshgrid(lon_values, lat_values)
    site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

    return fault, site_coords, planes, lon_lat_depth, x, y


def default_variables():
    im = IM(IMType.pSA, period=3.0)
    ens = gmhazard_calc.gm_data.Ensemble("v20p5emp")
    branch = ens.get_im_ensemble(im.im_type).branches[0]
    nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)
    faults = ["AlpineK2T", "AlfMakuri", "Wairau", "ArielNorth", "Swedge1", "Ashley"]
    nhyps = [5, 15, 30, 50, 100]
    grid_space = 100
    return nhm_dict, faults, im, grid_space, nhyps
