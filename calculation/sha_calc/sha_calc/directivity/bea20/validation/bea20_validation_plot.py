import argparse
from pathlib import Path

import numpy as np

from qcore import srf
from sha_calc.directivity.bea20.validation import plots
from sha_calc.directivity.bea20.directivity import compute_directivity_single_hypo


def bea20_directivity_plots(
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

    (
        fd,
        fdi,
        phi_red,
        phi_redi,
        predictor_functions,
        other,
    ) = compute_directivity_single_hypo(srf_file, srf_csv, site_coords, period)

    s2 = other["S2"].reshape((100, 100))
    f_s2 = predictor_functions["fs2"].reshape((100, 100))
    f_theta = predictor_functions["ftheta"].reshape((100, 100))
    f_g = predictor_functions["fG"].reshape((100, 100))
    f_dist = predictor_functions["fdist"].reshape((100, 100))
    fdi = fdi.reshape((100, 100))

    plots.validation_plot(
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
    parser.add_argument("srf_file", type=str)
    parser.add_argument("srf_csv", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--period", type=float, default=3.0)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    bea20_directivity_plots(args.srf_file, args.srf_csv, args.output_dir, args.period)
