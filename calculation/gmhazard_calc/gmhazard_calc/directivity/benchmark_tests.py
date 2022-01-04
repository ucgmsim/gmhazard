"""
Tests the benchmark test data for 4 different faults
Generates 9 sites locations close to the outer edges of the fault
And uses a period of 3 and 100 hypocentres
With latin hypercube and a set seed
This is compared to original created results
"""
from pathlib import Path

import numpy as np
import pandas as pd

from qcore import nhm
from gmhazard_calc import gm_data, rupture, directivity
from gmhazard_calc.im import IM, IMType

FAULTS = ["AlpineK2T", "Ashley", "Browning", "Hossack"]


def test_directivity():
    def test_data(
        fault: str,
        fd_result: pd.DataFrame,
        bench_data: pd.DataFrame,
    ):
        print(f"Directivity test for fault - {fault}")

        try:
            # Benchmark checking
            assert np.all(np.isclose(bench_data.values, fd_result.values))
        except AssertionError:
            print(
                f"Directivity test for fault - {fault} - FAILED - Results are different"
            )
            return 1

        print(f"Directivity test for fault - {fault} - PASSED")
        return 0

    # Iterate over the faults to test
    results = []

    im = IM(IMType.pSA, period=3.0)
    ens = gm_data.Ensemble("v20p5emp")
    branch = ens.get_im_ensemble(im.im_type).branches[0]
    nhm_dict = nhm.load_nhm(branch.flt_erf_ffp)

    for fault_name in FAULTS:
        fault = nhm_dict[fault_name]
        planes, lon_lat_depth = rupture.get_fault_header_points(fault)

        lon_values = np.linspace(
            lon_lat_depth[:, 0].min() - 0.25, lon_lat_depth[:, 0].max() + 0.25, 3
        )
        lat_values = np.linspace(
            lon_lat_depth[:, 1].min() - 0.25, lon_lat_depth[:, 1].max() + 0.25, 3
        )

        x, y = np.meshgrid(lon_values, lat_values)
        site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

        n_hypo_data = directivity.NHypoData(
            directivity.HypoMethod.LATIN_HYPERCUBE, nhypo=100, seed=1
        )

        fd, _, _ = directivity.compute_fault_directivity(
            lon_lat_depth,
            planes,
            site_coords,
            n_hypo_data,
            fault.mw,
            fault.rake,
            periods=[im.period],
        )

        bench_data = pd.read_csv(
            Path(__file__).parent / "bench_data" / f"{fault_name}_fd.csv", index_col=0
        )

        results.append(test_data(fault_name, pd.DataFrame(fd), bench_data))

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
