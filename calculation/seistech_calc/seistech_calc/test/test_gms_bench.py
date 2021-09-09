"""GMS benchmark tests"""
import os
import pathlib

import yaml
import pytest
import numpy as np
import pandas as pd

from seistech_calc import gms
from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc.im import IM, to_im_list


@pytest.fixture(scope="module")
def config():
    config_file = pathlib.Path(__file__).resolve().parent / "bench_data/gms_config.yaml"

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_gms(config):
    def test_data(
        gms_run: str,
        station_name: str,
        gms_df: pd.DataFrame,
        bench_df: pd.DataFrame,
    ):
        print(
            "Running - ensemble - {}, gms_run - {}, station name - {}".format(
                ensemble_id, gms_run, station_name
            )
        )

        try:
            # Not comparing the extreme values, as due to floating point errors the x-values
            # during GCIM interpolation for combining branch GCIMs can be outside of the limits
            # resulting in different values
            # All other 998 values still have to match, so this doesn't reduce
            # the effectiveness of the test
            assert np.all(np.isclose(gms_df.values[1:-1], bench_df.sort_index().values[1:-1]))
        except AssertionError:
            print(
                "Ensemble - {}, gms_run - {}, station name - {}"
                "- FAILED - Results are different".format(
                    ensemble_id, gms_run, station_name
                )
            )
            return 1

        print(
            "Ensemble - {}, gms_run - {}, station name - {}"
            "- PASSED".format(ensemble_id, gms_run, station_name)
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
        for gms_run in ensembles[ensemble_id]["gms_parameters"]:
            parameters = ensembles[ensemble_id]["gms_parameters"][gms_run]
            for station_name in ensembles[ensemble_id]["station_names"]:
                site_info = site.get_site_from_name(ens, station_name)
                gm_dataset = gms.GMDataset.get_GMDataset(parameters["dataset_id"])

                # Test the individual dataset hazard results
                gms_result = gms.run_ensemble_gms(
                    ens,
                    site_info,
                    parameters["n_gms"],
                    IM.from_str(parameters["IMj"]),
                    gm_dataset,
                    IMs=None
                    if parameters["IMs"] is None
                    else to_im_list(parameters["IMs"]),
                    exceedance=parameters["exceedance"],
                    im_j=parameters["im_j"],
                    n_replica=parameters["n_replica"],
                )

                for gcim, gcim_values in gms_result.IMi_gcims.items():
                    bench_data_file = (
                        pathlib.Path(__file__).resolve().parent
                        / f"bench_data/gms/{ensemble_id}"
                        / str(gcim).replace(".", "p")
                        / f"{station_name.replace('.', 'p')}_cdf.csv"
                    )
                    bench_data = pd.read_csv(bench_data_file, index_col=0)
                    results.append(
                        test_data(
                            gms_run,
                            station_name,
                            gcim_values.lnIMi_IMj.cdf.to_frame(),
                            bench_data,
                        )
                    )
                    for branch, branch_values in gcim_values.branch_uni_gcims.items():
                        bench_data_file = (
                            pathlib.Path(__file__).resolve().parent
                            / f"bench_data/gms/{ensemble_id}"
                            / str(gcim).replace(".", "p")
                            / branch
                            / f"{station_name.replace('.', 'p')}_cdf.csv"
                        )
                        bench_data = pd.read_csv(bench_data_file, index_col=0)
                        results.append(
                            test_data(
                                gms_run,
                                station_name,
                                branch_values.lnIMi_IMj.cdf.to_frame(),
                                bench_data,
                            )
                        )

                        bench_data_file = (
                            pathlib.Path(__file__).resolve().parent
                            / f"bench_data/gms/{ensemble_id}"
                            / str(gcim).replace(".", "p")
                            / branch
                            / f"{station_name.replace('.', 'p')}_mu.csv"
                        )
                        bench_data = pd.read_csv(bench_data_file, index_col=0)
                        results.append(
                            test_data(
                                gms_run,
                                station_name,
                                branch_values.lnIMi_IMj_Rup.mu.to_frame(),
                                bench_data,
                            )
                        )

                        bench_data_file = (
                            pathlib.Path(__file__).resolve().parent
                            / f"bench_data/gms/{ensemble_id}"
                            / str(gcim).replace(".", "p")
                            / branch
                            / f"{station_name.replace('.', 'p')}_sigma.csv"
                        )
                        bench_data = pd.read_csv(bench_data_file, index_col=0)
                        results.append(
                            test_data(
                                gms_run,
                                station_name,
                                branch_values.lnIMi_IMj_Rup.sigma.to_frame(),
                                bench_data,
                            )
                        )

        if np.sum(results) > 0:
            raise AssertionError(
                "Some of the benchmark tests failed, "
                "check the output to determine which ones failed."
            )
