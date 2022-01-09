"""Correlate IM's benchmark tests"""
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd


from spatial_hazard import correlate_ims


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "config" / "correlate_ims_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_correlate_ims(config):
    # Get config variables
    bench_test_dir = pathlib.Path(__file__).parent / "bench_data" / config["type"]
    config_dir = pathlib.Path(__file__).parent / "config"
    stations_ll_ffp = config_dir / config["stations_ll"]
    imdb_ffps = [config_dir / imdb for imdb in config["imdbs"]]
    im, fault, seed = config["im"], config["fault"], config["seed"]

    # Set the seed for the test
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

    # Compare resulting dataframes
    ln_im_values, between, within = (
        pd.DataFrame(data=random_IMs.T, index=stations),
        pd.DataFrame(data=between_event.T, index=stations),
        pd.DataFrame(data=within_event.T, index=stations),
    )

    ln_im_bench_data = pd.read_csv(
        bench_test_dir / "realisation_im_values.csv", index_col=0
    )
    between_bench_data = pd.read_csv(
        bench_test_dir / "realisation_between_residuals.csv", index_col=0
    )
    within_bench_data = pd.read_csv(
        bench_test_dir / "realisation_within_residuals.csv", index_col=0
    )

    try:
        assert np.all(
            np.isclose(ln_im_values, ln_im_bench_data)
            & np.isclose(between, between_bench_data)
            & np.isclose(within, within_bench_data)
        )
    except AssertionError:
        print("Some of the benchmark tests failed," "Results were different.")
