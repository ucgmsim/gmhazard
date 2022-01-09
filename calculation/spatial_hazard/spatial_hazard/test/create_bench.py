import argparse
import pathlib

import numpy as np
import pandas as pd
import yaml

from spatial_hazard import correlate_ims


def create_correlated_im_bench_data(
    stations_ll_ffp, imdb_ffps, im, fault, seed, output_dir
):
    # Set the testing seed
    np.random.seed(seed)

    # Load the station data
    stations_df = pd.read_csv(stations_ll_ffp, " ", index_col=2)
    stations = stations_df.index.values

    # Get realisations
    print("Retrieving GMM parameters")
    emp_df = correlate_ims.load_stations_fault_data(imdb_ffps, stations, im, fault)

    print("Computing distance matrix")
    dist_matrix = correlate_ims.calculate_distance_matrix(stations, stations_df)

    print("Computing correlation matrix")
    R = correlate_ims.get_corr_matrix(stations, dist_matrix, im, emp_df)

    print("Generating realisation")
    random_IMs, between_event, within_event = correlate_ims.create_random_fields(
        1, R, stations, emp_df
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


def main(args):
    bench_dir = pathlib.Path(__file__).parent / "bench_data"
    config_dir = pathlib.Path(__file__).parent / "config"
    config_file = args.config

    # Check if the specified config_file is a full path or just a filename
    if not pathlib.Path(config_file).is_file():
        config_file = config_dir / config_file

    # Read config
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Benchmark data type (i.e. correlate_ims)
    type = config["type"]

    output_dir = pathlib.Path(bench_dir).resolve() / type
    output_dir.mkdir(parents=True, exist_ok=True)

    if type == "correlate_ims":
        stations_ll_ffp = config_dir / config["stations_ll"]
        imdb_ffps = [config_dir / imdb for imdb in config["imdbs"]]
        create_correlated_im_bench_data(
            stations_ll_ffp,
            imdb_ffps,
            config["im"],
            config["fault"],
            config["seed"],
            output_dir,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "config",
        type=str,
        help="Path of the testing config, can just be a filename, "
        "if the file is located in the config data_dir",
    )
    args = parser.parse_args()
    main(args)
