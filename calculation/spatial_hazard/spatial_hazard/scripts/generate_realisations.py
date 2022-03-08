import argparse
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

import gmhazard_calc as gc
from spatial_hazard import correlate_ims
from spatial_hazard import plots


def main(
    IM: gc.im.IM,
    fault: str,
    N: int,
    stations_ll_ffp: str,
    imdb_ffps: Sequence[str],
    output_dir: Path,
    n_procs: int,
):
    # Load the station data
    stations_df = pd.read_csv(stations_ll_ffp, " ", index_col=2)
    stations = stations_df.index.values

    # Get realisations
    print("Retrieving GMM parameters")
    emp_df = correlate_ims.load_stations_fault_data(imdb_ffps, stations, IM, fault)

    print("Computing distance matrix")
    dist_matrix = correlate_ims.calculate_distance_matrix(stations, stations_df)

    assert np.all(
        dist_matrix.index.values == emp_df.index.values
    ), "Order of the stations has to be the same"

    print("Computing correlation matrix")
    R = correlate_ims.get_corr_matrix(stations, dist_matrix, IM)

    print("Generating realisation")
    random_IMs, between_event, within_event = correlate_ims.generate_im_values(
        N, R, emp_df
    )

    ln_im_values, between, within = (
        pd.DataFrame(data=random_IMs.T, index=stations),
        pd.DataFrame(data=between_event.T, index=stations),
        pd.DataFrame(data=within_event.T, index=stations),
    )

    # Save the data
    ln_im_values.to_csv(output_dir / "realisation_im_values.csv", index_label="station")
    between.to_csv(
        output_dir / "realisation_between_residuals.csv", index_label="station"
    )
    within.to_csv(
        output_dir / "realisation_within_residuals.csv", index_label="station"
    )
    emp_df.to_csv(output_dir / "gmm_parameters.csv", index_label="station")

    # Generate the plots
    plot_dir = output_dir / "plots"
    plot_dir.mkdir(exist_ok=True)

    im_values = ln_im_values.apply(np.exp)
    plots.plot_realisations(
        im_values,
        stations_df,
        plot_dir,
        f"{fault}_{IM.file_format()}_Realisation",
        label=f"{IM}",
        n_procs=n_procs,
        cpt_max=0.125,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("IM", type=str, help="IM of interest")
    parser.add_argument(
        "fault", type=str, help="The fault for which to compute spatial hazard"
    )
    parser.add_argument("N", type=int, help="Number of realisations to generate")
    parser.add_argument(
        "stations_ll_ffp",
        type=str,
        help="Path to the stations ll file. Has to contain the stations of interest.",
    )
    parser.add_argument(
        "imdb_ffps", type=str, nargs="+", help="Path of the different IMDBs to use"
    )
    parser.add_argument("output_dir", type=Path, help="Path of the output directory")
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )

    args = parser.parse_args()

    main(
        gc.im.IM.from_str(args.IM),
        args.fault,
        args.N,
        args.stations_ll_ffp,
        args.imdb_ffps,
        args.output_dir,
        args.n_procs,
    )
