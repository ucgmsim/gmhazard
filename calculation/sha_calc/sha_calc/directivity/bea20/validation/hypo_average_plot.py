import argparse
from pathlib import Path

import numpy as np

from qcore import srf
from sha_calc.directivity.bea20.validation import plots
from sha_calc.directivity.bea20.directivity import compute_directivity_srf_multi


def hypo_average_plots(
    srf_file: str, srf_csv: Path, output_dir: Path, period: float = 3.0
):
    """
    Creates 6 plots to show total directivity effects at a given srf after hypocentre averaging

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    output_dir: Path
        Path to the location of the output plot directory
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    """

    lon_lat_depth = srf.read_srf_points(srf_file)

    lon_values = np.linspace(
        lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, 100
    )
    lat_values = np.linspace(
        lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, 100
    )

    x, y = np.meshgrid(lon_values, lat_values)
    site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

    fdi_average, fdi_array, _ = compute_directivity_srf_multi(
        srf_file, srf_csv, site_coords, periods=[period]
    )

    # im = IM(IMType.pSA, period=3.0)
    # ens = gmhazard_calc.gm_data.Ensemble("v20p5emp")
    # branch = ens.get_im_ensemble(im.im_type).branches[0]
    #
    # nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)
    #
    # # for key, fault in nhm_dict.items():
    # fault = nhm_dict["AlpineK2T"]
    # planes, lon_lat_depth = rupture.get_fault_header_points(fault)
    # lon_values = np.linspace(
    #     lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, 100
    # )
    # lat_values = np.linspace(
    #     lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, 100
    # )
    #
    # x, y = np.meshgrid(lon_values, lat_values)
    # site_coords = np.stack((x, y), axis=2).reshape(-1, 2)
    # fdi_average, fdi_array = sha_calc.bea20.compute_fault_directivity(lon_lat_depth, planes, site_coords, 10, 2, fault.mw, fault.rake, [im.period])

    for index, fdi in enumerate(fdi_array):
        plots.plot_fdi(
            x,
            y,
            fdi.reshape((100, 100)),
            lon_lat_depth,
            Path(f"{output_dir}/hypo_plot_{index}.png"),
        )

    plots.plot_fdi(
        x,
        y,
        fdi_average.reshape((100, 100)),
        lon_lat_depth,
        Path(f"{output_dir}/hypo_average_plot.png"),
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("srf_file", type=str)
    parser.add_argument("srf_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--period", type=float, default=3.0)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    hypo_average_plots(args.srf_file, args.srf_csv, args.output_dir, args.period)
