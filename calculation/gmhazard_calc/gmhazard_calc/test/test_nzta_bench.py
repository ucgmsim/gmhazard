"""NZTA benchmark tests"""
import os
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import nz_code
from gmhazard_calc import gm_data
from gmhazard_calc import constants
from gmhazard_calc.im import IMType, IM_COMPONENT_MAPPING, IMComponent


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/nzta_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_nzta_hazard(config):
    def test_data(
        station_name: str,
        ensemble_id: str,
        nzta_result: nz_code.nzta_2018.NZTAResult,
        bench_df: pd.DataFrame,
    ):
        print(f"Running - ensemble - {ensemble_id}, station name - {station_name}")

        try:
            assert np.allclose(
                nzta_result.pga_values.index.values,
                bench_df["pga_values"].index.values,
            )
            assert np.allclose(
                nzta_result.pga_values.values,
                bench_df["pga_values"].values,
                equal_nan=True,
            )
            # bench_df["M_eff"] is no longer a single value, this column is filled
            # with the same value hence decided to use min value
            assert np.isclose(nzta_result.M_eff, bench_df["M_eff"].min(0))
            assert np.isclose(nzta_result.C0_1000, bench_df["C0_1000"].min(0))
        except AssertionError:
            print(
                f"Ensemble - {ensemble_id}, "
                f"station name - {station_name}- FAILED - Results are different"
            )
            return 1

        print(f"Ensemble - {ensemble_id}, station name - {station_name}- PASSED")
        return 0

    ensembles = config["ensembles"]

    # Iterate over the ensembles to test
    results = []
    for ensemble_id in ensembles.keys():
        ens_config_ffp = (
            pathlib.Path(os.getenv("ENSEMBLE_CONFIG_PATH"))
            / "benchmark_tests"
            / f"{ensemble_id}.yaml"
        )

        ens = gm_data.Ensemble(ensemble_id, ens_config_ffp)
        components = (
            IM_COMPONENT_MAPPING[IMType.PGA]
            if ens.im_ensembles[0].im_data_type == constants.IMDataType.parametric
            else [IMComponent.Larger]
        )
        for component in components:
            for station_name in ensembles[ensemble_id]["station_names"]:
                site_info = site.get_site_from_name(ens, station_name)
                nzta_result = nz_code.nzta_2018.run_ensemble_nzta(
                    ens, site_info, im_component=component
                )

                bench_data_file = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/nzta/{ensemble_id}"
                    / str(component)
                    / f"{station_name.replace('.', 'p')}.csv"
                )
                bench_data = pd.read_csv(bench_data_file, index_col=0)

                results.append(
                    test_data(station_name, ensemble_id, nzta_result, bench_data)
                )

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
