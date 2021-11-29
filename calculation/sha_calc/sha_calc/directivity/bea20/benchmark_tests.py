from pathlib import Path

import numpy as np
import pandas as pd

from qcore import srf
from sha_calc.directivity.bea20 import directivity

FAULTS = ["AlpineK2T", "Ashley", "Browning", "Hossack"]
SRF_LOCATION = Path("/mnt/mantle_data/seistech")  # TODO Change to virtual srfs


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
    for fault in FAULTS:
        srf_file = str(SRF_LOCATION / "srfs" / f"{fault}_REL01.srf")
        srf_csv = SRF_LOCATION / "srfs" / f"{fault}_REL01.csv"

        lon_lat_depth = srf.read_srf_points(srf_file)

        lon_values = np.linspace(
            lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, 3
        )
        lat_values = np.linspace(
            lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, 3
        )

        x, y = np.meshgrid(lon_values, lat_values)
        site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

        fd, _, _, _, _, _ = directivity.compute_directivity_hypo_averaging(
            srf_file, srf_csv, site_coords
        )

        bench_data = pd.read_csv(
            Path(__file__).parent / "bench_data" / f"{fault}_fd.csv", index_col=0
        )

        results.append(test_data(fault, pd.DataFrame(fd), bench_data))

    if np.sum(results) > 0:
        raise AssertionError(
            "Some of the benchmark tests failed, "
            "check the output to determine which ones failed."
        )
