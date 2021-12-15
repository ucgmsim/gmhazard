import argparse
from pathlib import Path

from qcore import nhm
from gmhazard_calc import gm_data, directivity
from gmhazard_calc.im import IM, IMType


def hypo_average_plots(
    fault_name: str, output_dir: Path, period: float = 3.0, grid_space: int = 100
):
    """
    Creates directivity effect plots for a given fault after hypocentre averaging and each hypocentre directivity effect

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

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(fault_name, nhm_dict, grid_space)

    n_hypo_data = directivity.NHypoData(directivity.HypoMethod.LATIN_HYPERCUBE, nhypo=10)

    fd, fd_array, _ = directivity.compute_fault_directivity(
        lon_lat_depth,
        planes,
        site_coords,
        n_hypo_data,
        fault.mw,
        fault.rake,
        periods=[im.period],
    )

    for index, fdi in enumerate(fd_array):
        directivity.validation.plots.plot_fdi(
            x,
            y,
            fdi.reshape((grid_space, grid_space)),
            lon_lat_depth,
            Path(f"{output_dir}/hypo_plot_{index}.png"),
        )

    directivity.validation.plots.plot_fdi(
        x,
        y,
        fd.reshape((grid_space, grid_space)),
        lon_lat_depth,
        Path(f"{output_dir}/hypo_average_plot.png"),
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
    hypo_average_plots(args.fault, args.output_dir, args.period, args.grid_space)
