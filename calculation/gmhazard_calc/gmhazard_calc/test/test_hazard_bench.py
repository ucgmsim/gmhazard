"""Hazard benchmark tests"""
import os
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import hazard
from gmhazard_calc import gm_data
from gmhazard_calc import constants
from gmhazard_calc.im import IM, IM_COMPONENT_MAPPING


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/hazard_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_hazard(config):
    def test_data(
        im: IM,
        station_name: str,
        dataset_name: str,
        hazard: hazard.EnsembleHazardResult,
        bench_df: pd.DataFrame,
    ):
        print(
            "Running - ensemble - {}, im - {}, station name - {}, "
            "dataset {}".format(ensemble_id, im, station_name, dataset_name)
        )
        hazard_df = hazard.as_dataframe()
        try:
            assert np.all(
                np.isclose(hazard_df.ds, bench_df.ds)
                & np.isclose(hazard_df.fault, bench_df.fault)
                & np.isclose(hazard_df.total, bench_df.total)
            )
        except AssertionError:
            print(
                "Ensemble - {}, im - {}, station name - {}, dataset {} "
                "- FAILED - Results are different".format(
                    ensemble_id, im, station_name, dataset_name
                )
            )
            return 1

        print(
            "Ensemble - {}, im - {}, station name - {}, dataset {} "
            "- PASSED".format(ensemble_id, im, station_name, dataset_name)
        )
        return 0

    ensembles = config["ensembles"]

    # Iterate over the ensembles to test
    for ensemble_id in ensembles.keys():
        ens_config_ffp = (
            pathlib.Path(os.getenv("ENSEMBLE_CONFIG_PATH"))
            / "benchmark_tests"
            / f"{ensemble_id}.yaml"
        )
        ens = gm_data.Ensemble(ensemble_id, ens_config_ffp)

        results = []
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

                # Test the individual dataset hazard results
                branches_hazard = hazard.run_branches_hazard(ens, site_info, im)
                for branch_name, dset_hazard in branches_hazard.items():
                    bench_data_file_sim = (
                        pathlib.Path(__file__).resolve().parent
                        / f"bench_data/hazard/{ensemble_id}"
                        / f"{im.file_format()}_{im.component}"
                        / f"{station_name.replace('.', 'p')}"
                        / f"{branch_name}.csv"
                    )
                    bench_data = pd.read_csv(bench_data_file_sim, index_col=0)
                    results.append(
                        test_data(
                            im,
                            station_name,
                            dset_hazard.branch.name,
                            dset_hazard,
                            bench_data,
                        )
                    )

                # Test the weighted hazard
                ens_hazard = hazard.run_ensemble_hazard(ens, site_info, im)
                bench_data_file_ensemble = (
                    pathlib.Path(__file__).resolve().parent
                    / f"bench_data/hazard/{ensemble_id}"
                    / f"{im.file_format()}_{im.component}"
                    / f"{station_name.replace('.', 'p')}"
                    / "ensemble.csv"
                )
                bench_data = pd.read_csv(bench_data_file_ensemble, index_col=0)
                results.append(
                    test_data(im, station_name, "ensemble", ens_hazard, bench_data)
                )

        if np.sum(results) > 0:
            raise AssertionError(
                "Some of the benchmark tests failed, "
                "check the output to determine which ones failed."
            )
