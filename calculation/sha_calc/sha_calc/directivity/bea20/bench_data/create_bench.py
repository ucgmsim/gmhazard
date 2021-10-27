from pathlib import Path

import numpy as np
import pandas as pd

from qcore import srf
from sha_calc.directivity.bea20 import directivity

FAULTS = ["AlpineK2T", "Ashley", "Browning", "Hossack"]
SRF_LOCATION = Path("/mnt/mantle_data/seistech")


def create_benchmark_data():
    """Creates the benchmark data with 4 different faults using 9 points and saving the fd results"""
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

        fd, _ = directivity.compute_directivity_srf_multi(
            srf_file, srf_csv, site_coords
        )

        pd.DataFrame(fd).to_csv(Path(__file__).parent / f"{fault}_fd.csv")


if __name__ == "__main__":
    create_benchmark_data()
