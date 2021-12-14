import gmhazard_calc
from gmhazard_calc.im import IM, IMType
from qcore import nhm


def default_variables():
    im = IM(IMType.pSA, period=3.0)
    ens = gmhazard_calc.gm_data.Ensemble("v20p5emp")
    branch = ens.get_im_ensemble(im.im_type).branches[0]
    nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)
    faults = ["AlpineK2T", "AlfMakuri", "Wairau", "ArielNorth", "Swedge1", "Ashley"]
    nhyps = [5, 15, 30, 50, 100]
    grid_space = 100
    return nhm_dict, faults, im, grid_space, nhyps
