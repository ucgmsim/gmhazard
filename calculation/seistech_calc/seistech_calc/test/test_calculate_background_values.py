from os import path

import numpy as np
import pytest
import pandas as pd

import seistech_calc as si


@pytest.mark.parametrize(
    ["input_data", "benchmark_data"],
    [
        (
            si.utils.read_ds_nhm(
                path.join(
                    path.dirname(__file__),
                    "bench_data",
                    "ds_nhm",
                    "NZBCK211_OpenSHA_sample.txt",
                )
            ),
            pd.read_csv(
                path.join(
                    path.dirname(__file__), "bench_data", "ds_nhm", "sample_output.txt"
                )
            ),
        )
    ],
)
def test_calculate_background_values(
    input_data: pd.DataFrame, benchmark_data: pd.DataFrame
):
    tested_data = si.utils.calculate_rupture_rates(input_data)
    assert np.all(
        np.isclose(
            tested_data.annual_rec_prob.values, benchmark_data.annual_rec_prob.values
        )
    )
