"""Disagg benchmark tests"""
import os
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd

from seistech_calc import disagg
from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc import constants
from seistech_calc.im import IM, IM_COMPONENT_MAPPING


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/disagg_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_disagg(config):
    def test_data(
        im: IM,
        station_name: str,
        branch_name: str,
        disagg: disagg.DisaggData,
        bench_data: pd.DataFrame,
    ):
        print(
            "Running - ensemble - {}, im - {}, station name - {}, "
            "dataset {}".format(ensemble_id, im, station_name, branch_name)
        )
        bench_total_contr = bench_data.squeeze()

        try:
            # Sanity check
            assert np.isclose(disagg.total_contributions.sum(), 1.0)

            # Benchmark checking
            assert np.all(
                np.isclose(bench_total_contr.values, disagg.total_contributions.values)
            )
        except AssertionError:
            print(
                "Ensemble - {}, im - {}, station name - {}, branch {} "
                "- FAILED - Results are different".format(
                    ensemble_id, im, station_name, branch_name
                )
            )
            return 1

        print(
            "Ensemble - {}, im - {}, station name - {}, branch {} "
            "- PASSED".format(ensemble_id, im, station_name, branch_name)
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
        exceedance = ensembles[ensemble_id]["exceedance"]

        ims = []
        for im_string in ensembles[ensemble_id]["ims"]:
            im = IM.from_str(im_string)
            if ens.im_ensembles[0].im_data_type == constants.IMDataType.parametric:
                ims.extend(
                    [
                        IM(im.im_type, im.period, component)
                        for component in IM_COMPONENT_MAPPING[im.im_type]
                    ]
                )
            else:
                ims.append(im)

        for im in ims:
            for station_name in ensembles[ensemble_id]["station_names"]:
                site_info = site.get_site_from_name(ens, station_name)

                # Test the individual branches disagg results
                disagg_dict = disagg.run_branches_disagg(
                    ens.get_im_ensemble(im.im_type),
                    site_info,
                    im,
                    exceedance=exceedance,
                )
                for branch_name, branch_disagg in disagg_dict.items():
                    bench_data_file_sim = (
                        pathlib.Path(__file__).resolve().parent
                        / f"bench_data/disagg/{ensemble_id}"
                        / f"{im.file_format()}_{im.component}"
                        / f"{station_name.replace('.', 'p')}"
                        / f"{branch_name}.csv"
                    )
                    bench_data = pd.read_csv(bench_data_file_sim, index_col=0)
                    results.append(
                        test_data(
                            im, station_name, branch_name, branch_disagg, bench_data
                        )
                    )

                bench_data_file_ensemble = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/disagg/{ensemble_id}"
                    / f"{im.file_format()}_{im.component}"
                    / f"{station_name.replace('.', 'p')}"
                    / "ensemble.csv"
                )
                bench_data = pd.read_csv(bench_data_file_ensemble, index_col=0)
                results.append(
                    test_data(
                        im,
                        station_name,
                        "ensemble",
                        disagg.run_ensemble_disagg(
                            ens, site_info, im, exceedance=exceedance
                        ),
                        bench_data,
                    )
                )

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
