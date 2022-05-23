"""NZS1170p5 benchmark tests"""
import os
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import nz_code
from gmhazard_calc import gm_data
from gmhazard_calc.im import IM, IM_COMPONENT_MAPPING, IMComponent


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/nzs1170p5_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_hazard(config):
    def test_data(
        im: IM,
        station_name: str,
        ensemble_id: str,
        z_factor_radius: float,
        nz_code_result: nz_code.nzs1170p5.NZS1170p5Result,
        bench_df: pd.DataFrame,
    ):
        print(
            f"Running - ensemble - {ensemble_id}, im - {im}, station name - {station_name}, Z-factor radius {z_factor_radius}"
        )
        # Convert dataframe to series
        bench_series = bench_df[str(z_factor_radius)].iloc[:]

        try:
            assert np.all(
                np.isclose(
                    nz_code_result.im_values.index.values, bench_series.index.values
                )
            )
            assert np.all(
                np.isclose(nz_code_result.im_values.values, bench_series.values)
            )
        except AssertionError:
            print(
                f"Ensemble - {ensemble_id}, im - {im}, "
                f"station name - {station_name}- FAILED - Results are different"
            )
            return 1

        print(
            f"Ensemble - {ensemble_id}, im - {im}, station name - {station_name}- PASSED"
        )
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

        ims = []
        for im_string in ensembles[ensemble_id]["ims"]:
            im = IM.from_str(im_string)
            if ensembles[ensemble_id]["components"]:
                ims.extend(
                    [
                        IM(im.im_type, im.period, component)
                        for component in IM_COMPONENT_MAPPING[im.im_type]
                    ]
                )
            else:
                im.component = IMComponent.Larger
                ims.append(im)

        for im in ims:
            for station_name in ensembles[ensemble_id]["station_names"]:
                bench_data_file = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/nzs1170p5/{ensemble_id}"
                    / f"{station_name.replace('.', 'p')}"
                    / f"{im.file_format()}_{im.component}.csv"
                )
                bench_data = pd.read_csv(bench_data_file, index_col=0)
                for radius in ensembles[ensemble_id]["z_factor_radius"]:
                    site_info = site.get_site_from_name(ens, station_name)
                    nz_code_result = nz_code.nzs1170p5.run_ensemble_nzs1170p5(
                        ens, site_info, im, z_factor_radius=radius
                    )

                    results.append(
                        test_data(
                            im,
                            station_name,
                            ensemble_id,
                            radius,
                            nz_code_result,
                            bench_data,
                        )
                    )

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
