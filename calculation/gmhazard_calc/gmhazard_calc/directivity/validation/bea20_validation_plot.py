import argparse
from pathlib import Path

from qcore import nhm
from gmhazard_calc import gm_data, directivity
from gmhazard_calc.im import IM, IMType


def bea20_directivity_plots(
    fault_name: str, output_dir: Path, period: float = 3.0, grid_space: int = 100
):
    """
    Creates 6 plots to show total directivity effects for a given fault with a single hypocentre

    Parameters
    ----------
    fault_name: str
        Name of the fault to produce plots for
    output_dir: Path
        Path to the location of the output plot directory
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    grid_space: int, optional
        The grid spacing to use for generating directivity and to show resolution for plots
    """
    im = IM(IMType.pSA, period=period)
    ens = gm_data.Ensemble("v20p5emp")
    branch = ens.get_im_ensemble(im.im_type).branches[0]
    nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )
    nominal_strike, nominal_strike2 = directivity.utils.calc_nominal_strike(
        lon_lat_depth
    )

    plane_index = [i for i, plane in enumerate(planes) if plane["shyp"] != -999.9][0]

    fdi, (
        phi_red,
        predictor_functions,
        other,
    ) = directivity.directivity._compute_directivity_effect(
        lon_lat_depth,
        planes,
        plane_index,
        site_coords,
        nominal_strike,
        nominal_strike2,
        fault.mw,
        fault.rake,
        [period],
    )

    s2 = other["S2"].reshape((100, 100))
    f_s2 = predictor_functions["fs2"].reshape((100, 100))
    f_theta = predictor_functions["ftheta"].reshape((100, 100))
    f_g = predictor_functions["fG"].reshape((100, 100))
    f_dist = predictor_functions["fdist"].reshape((100, 100))
    fdi = fdi.reshape((100, 100))

    directivity.validation.plots.validation_plot(
        x,
        y,
        s2,
        f_s2,
        f_theta,
        f_g,
        f_dist,
        fdi,
        lon_lat_depth,
        output_dir,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("fault", type=str)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--period", type=float, default=3.0)
    parser.add_argument("--grid_space", type=int, default=100)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    bea20_directivity_plots(args.fault, args.output_dir, args.period, args.grid_space)
