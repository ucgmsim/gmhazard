"""Uniform hazard spectra benchmark tests"""
import pathlib

import yaml
import pytest
import pandas as pd
import numpy as np

import seistech_calc as si


@pytest.fixture(scope="module")
def config():
    config_file = pathlib.Path(__file__).resolve().parent / "bench_data/uhs_config.yaml"

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_uhs(config):
    def test_data(station_name: str, uhs_df: pd.DataFrame, bench_data: pd.DataFrame):
        print(
            "Running - ensemble - {}, station name - {}, ".format(
                ensemble_id, station_name
            )
        )
        pd.testing.assert_frame_equal(bench_data, uhs_df)
        print(
            "Ensemble - {}, station name - {} - PASSED".format(
                ensemble_id, station_name
            )
        )

    ensembles = config["ensembles"]

    for ensemble_id in ensembles.keys():
        ens_config_ffp = (
            pathlib.Path(__file__).resolve().parent.parent
            / "gm_data/ensemble_configs/benchmark_tests"
            / f"{ensemble_id}.yaml"
        )
        ens = si.gm_data.Ensemble(ensemble_id, ens_config_ffp)
        components = (
            si.im.IM_COMPONENT_MAPPING[si.im.IMType.PGA]
            if ens.im_ensembles[0].im_data_type == si.constants.IMDataType.parametric
            else [si.im.IMComponent.RotD50]
        )
        for component in components:
            for station_name in ensembles[ensemble_id]["station_names"]:
                bench_data_file = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/uhs/{ensemble_id}"
                    / str(component)
                    / f"{station_name.replace('.', 'p')}.csv"
                )
                bench_data = pd.read_csv(bench_data_file, index_col=0)

                site_info = si.site.get_site_from_name(ens, station_name)

                uhs_results = si.uhs.run_ensemble_uhs(
                    ens,
                    site_info,
                    np.asanyarray(ensembles[ensemble_id]["exceedance_levels"]),
                    im_component=component,
                )
                df = si.uhs.EnsembleUHSResult.combine_results(uhs_results)

                test_data(station_name, df, bench_data)
