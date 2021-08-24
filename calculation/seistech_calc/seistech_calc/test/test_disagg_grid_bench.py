"""Disagg benchmark tests"""
import pathlib
from typing import Dict

import yaml
import pytest
import numpy as np

import seistech_calc as si


@pytest.fixture(scope="module")
def config():
    config_file = (
        pathlib.Path(__file__).resolve().parent / "bench_data/disagg_grid_config.yaml"
    )

    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    return config


def test_disagg(config):
    def test_data(
        im: si.im.IM,
        station_name: str,
        branch_name: str,
        disagg_grid: si.disagg.DisaggGridData,
        bench_dict: Dict,
    ):
        print(
            "Running - ensemble - {}, im - {}, station name - {}, "
            "branch {}".format(ensemble_id, im, station_name, branch_name)
        )

        # eps_bin_contr was 3-dimensional array, need to reshape
        eps_bin_contr_ndarray = bench_dict["eps_bin_contr"].reshape(
            np.stack(disagg_grid.eps_bin_contr, axis=0).shape
        )

        try:
            assert np.all(
                np.isclose(disagg_grid.flt_bin_contr, bench_dict["flt_bin_contr"])
            )
            assert np.all(
                np.isclose(disagg_grid.ds_bin_contr, bench_dict["ds_bin_contr"])
            )
            assert np.all(np.isclose(disagg_grid.eps_bin_contr, eps_bin_contr_ndarray))
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
    options = ["ds_bin_contr", "flt_bin_contr", "eps_bin_contr"]

    # Iterate over the ensembles to test
    results = []
    for ensemble_id in ensembles.keys():
        ens_config_ffp = (
            pathlib.Path(__file__).resolve().parent.parent
            / "gm_data/ensemble_configs/benchmark_tests"
            / f"{ensemble_id}.yaml"
        )
        ens = si.gm_data.Ensemble(ensemble_id, ens_config_ffp)
        exceedance = ensembles[ensemble_id]["exceedance"]

        ims = []
        for im_string in ensembles[ensemble_id]["ims"]:
            im = si.im.IM.from_str(im_string)
            if ens.im_ensembles[0].im_data_type == si.constants.IMDataType.parametric:
                ims.extend(
                    [si.im.IM(im.im_type, im.period, component) for component in
                     si.im.IM_COMPONENT_MAPPING[im.im_type]])
            else:
                ims.append(im)

        for im in ims:
            for station_name in ensembles[ensemble_id]["station_names"]:
                site = si.site.get_site_from_name(ens, station_name)

                # Test the individual dataset disagg results
                disagg_dict = si.disagg.run_branches_disagg(
                    ens.get_im_ensemble(im.im_type),
                    site,
                    im,
                    exceedance=exceedance,
                )
                for branch_name, branch_disagg in disagg_dict.items():
                    bench_dict = {}
                    for option in options:
                        bench_data_file_sim = (
                            pathlib.Path(__file__).resolve().parent
                            / f"bench_data/disagg_grid/{ensemble_id}"
                            / f"{im.file_format()}_{im.component}"
                            / f"{station_name.replace('.', 'p')}"
                            / f"{branch_name}"
                            / f"{option}.csv"
                        )
                        bench_dict[option] = np.loadtxt(
                            bench_data_file_sim, delimiter=","
                        )

                    branch_grid_data = si.disagg.run_disagg_gridding(branch_disagg)
                    results.append(
                        test_data(
                            im, station_name, branch_name, branch_grid_data, bench_dict
                        )
                    )

                # Test the ensemble disagg
                ens_disagg = si.disagg.run_ensemble_disagg(
                    ens, site, im, exceedance=exceedance
                )

                bench_dict = {}
                for option in options:
                    bench_data_file_ensemble = (
                        pathlib.Path(__file__).resolve().parent
                        / f"bench_data/disagg_grid/{ensemble_id}"
                        / f"{im.file_format()}_{im.component}"
                        / f"{station_name.replace('.', 'p')}"
                        / "ensemble"
                        / f"{option}.csv"
                    )
                    bench_dict[option] = np.loadtxt(
                        bench_data_file_ensemble, delimiter=","
                    )

                results.append(
                    test_data(
                        im,
                        station_name,
                        "ensemble",
                        si.disagg.run_disagg_gridding(ens_disagg),
                        bench_dict,
                    )
                )

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
