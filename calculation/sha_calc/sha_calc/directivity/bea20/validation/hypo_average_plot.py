import argparse
from pathlib import Path

import numpy as np

from qcore import srf
from sha_calc.directivity.bea20.validation import plots
from sha_calc.directivity.bea20.directivity import (
    compute_directivity_effect,
    directivity_pre_process,
)
from sha_calc.directivity.bea20 import utils


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

    (
        mag,
        rake,
        planes,
        lon_lat_depth,
        nominal_strike,
        nominal_strike2,
    ) = directivity_pre_process(srf_file, srf_csv)

    # Customise the planes to set different hypocentres
    n_hypo = 20  # TODO Update with best practice for hypocentre averaging
    planes_list, planes_index = utils.set_hypocentres(n_hypo, planes, [1 / 3, 2 / 3])

    # Creating the average array
    fdi_average = []

    for index, planes in enumerate(planes_list):
        # Gets the plane index of the hypocentre
        plane_index = planes_index[index]

        (
            fd,
            fdi,
            phi_red,
            phi_redi,
            predictor_functions,
            other,
        ) = compute_directivity_effect(
            lon_lat_depth,
            planes,
            plane_index,
            site_coords,
            nominal_strike,
            nominal_strike2,
            mag,
            rake,
            period,
        )

        fdi_average.append(fdi)

        plots.plot_fdi(
            x,
            y,
            fdi.reshape((100, 100)),
            lon_lat_depth,
            Path(f"{output_dir}/hypo_plot_{index}.png"),
        )

    fdi_average = (np.mean(fdi_average, axis=0),)

    fdi_average = fdi_average.reshape((100, 100))

    plots.plot_fdi(
        x,
        y,
        fdi_average,
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
