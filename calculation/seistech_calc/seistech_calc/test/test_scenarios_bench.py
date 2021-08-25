"""Scenarios benchmark tests"""
import os
import pathlib

import yaml
import pytest
import pandas as pd
import numpy as np

import seistech_calc as sc


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/scenarios_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_scenarios(config):
    def test_data(
        station_name: str, percentiles_df: pd.DataFrame, bench_data: pd.DataFrame
    ):
        print(
            "Running - ensemble - {}, station name - {}, ".format(
                ensemble_id, station_name
            )
        )
        pd.testing.assert_frame_equal(bench_data, percentiles_df)
        print(
            "Ensemble - {}, station name - {} - PASSED".format(
                ensemble_id, station_name
            )
        )

    ensembles = config["ensembles"]

    for ensemble_id in ensembles.keys():
        ens_config_ffp = (
            pathlib.Path(os.getenv("ENSEMBLE_CONFIG_PATH"))
            / "benchmark_tests"
            / f"{ensemble_id}.yaml"
        )
        ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)
        components = (
            sc.im.IM_COMPONENT_MAPPING[sc.im.IMType.PGA]
            if ens.im_ensembles[0].im_data_type == sc.constants.IMDataType.parametric
            else [sc.im.IMComponent.RotD50]
        )
        for component in components:
            for station_name in ensembles[ensemble_id]["station_names"]:
                bench_data_file = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/scenarios/{ensemble_id}"
                    / str(component)
                    / f"{station_name.replace('.', 'p')}.csv"
                )
                bench_data = pd.read_csv(bench_data_file, index_col=0)

                site_info = sc.site.get_site_from_name(ens, station_name)

                ensemble_scenario = sc.scenario.run_ensemble_scenario(
                    ens, site_info, im_component=component
                )

                test_data(station_name, ensemble_scenario.percentiles, bench_data)
