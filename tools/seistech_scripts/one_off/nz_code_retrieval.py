"""
Retrieves either NZTA or NZS1170.5 code values
for the given locations
"""

from pathlib import Path
import argparse
import multiprocessing as mp
from typing import Sequence

import numpy as np
import pandas as pd

import sha_calc as sha
import seistech_calc as sc

DEFAULT_RETURN_PERIODS = np.array([20, 25, 50, 100, 250, 500, 1000, 2000, 2500])
DEFAULT_EXCEEDANCE_VALUES = 1 / DEFAULT_RETURN_PERIODS

DEFAULT_IMS = [
    "PGA",
    "pSA_0.01",
    "pSA_0.02",
    "pSA_0.03",
    "pSA_0.04",
    "pSA_0.05",
    "pSA_0.075",
    "pSA_0.1",
    "pSA_0.12",
    "pSA_0.15",
    "pSA_0.17",
    "pSA_0.2",
    "pSA_0.25",
    "pSA_0.3",
    "pSA_0.4",
    "pSA_0.5",
    "pSA_0.6",
    "pSA_0.7",
    "pSA_0.75",
    "pSA_0.8",
    "pSA_0.9",
    "pSA_1.0",
    "pSA_1.25",
    "pSA_1.5",
    "pSA_2.0",
    "pSA_2.5",
    "pSA_3.0",
    "pSA_4.0",
    "pSA_5.0",
    "pSA_6.0",
    "pSA_7.5",
    "pSA_10.0",
]


def main(
    input_data_ffp: str,
    output_dir: Path,
    nz_code_type: str,
    nzta_csv_ffp: Path = None,
    ims: Sequence[str] = DEFAULT_IMS,
    n_procs: int = 4,
):
    # Load the required data
    data_df = pd.read_csv(input_data_ffp)

    # Need an ensemble
    ens = sc.gm_data.Ensemble("v20p5emp")

    if nz_code_type == "NZS1170.5":
        with mp.Pool(n_procs) as pool:
            results = pool.starmap(
                _process_nzs1170p5_station,
                [
                    (
                        ens,
                        cur_row.lat,
                        cur_row.lon,
                        cur_row.vs30,
                        ims,
                        ix,
                        data_df.shape[0],
                    )
                    for ix, (cur_id, cur_row) in enumerate(data_df.iterrows())
                ],
            )

        # Extract and save
        grouped_sublists = list(zip(*results))
        np.save(
            str(output_dir / "NZS1170p5_im_values.npy"),
            np.stack(grouped_sublists[0], axis=0),
        )
        np.save(
            str(output_dir / "NZS1170p5_Z_values.npy"),
            np.stack(grouped_sublists[1], axis=0),
        )
        np.save(
            str(output_dir / "NZS1170p5_N_values.npy"),
            np.stack(grouped_sublists[2], axis=0),
        )
        np.save(
            str(output_dir / "NZS1170p5_R_values.npy"),
            np.stack(grouped_sublists[3], axis=0),
        )
        np.save(
            str(output_dir / "NZS1170p5_Ch_values.npy"),
            np.stack(grouped_sublists[4], axis=0),
        )

    elif nz_code_type == "NZTA":
        assert nzta_csv_ffp is not None, (
            "Path to the NZTA csv is required when " "computing NZTA code PGA values"
        )
        nzta_df = pd.read_csv(nzta_csv_ffp, header=0, index_col=0)

        with mp.Pool(n_procs) as pool:
            results = pool.starmap(
                _process_nzta_station,
                [
                    (
                        ens,
                        cur_row.lat,
                        cur_row.lon,
                        cur_row.vs30,
                        nzta_df,
                        ix,
                        data_df.shape[0],
                    )
                    for ix, (cur_id, cur_row) in enumerate(data_df.iterrows())
                ],
            )
            grouped_sublists = list(zip(*results))
            np.save(
                str(output_dir / "NZTA_PGA_values.npy"),
                np.stack(grouped_sublists[0], axis=0),
            )
            np.save(
                str(output_dir / "NZTA_town_index.npy"),
                np.stack(grouped_sublists[1], axis=0),
            )


def _process_nzta_station(
    ens: sc.gm_data.Ensemble,
    lat: float,
    lon: float,
    vs30: float,
    nzta_df: pd.DataFrame,
    ix: int,
    n_locs: int,
):
    print(f"Processing location {ix + 1}/{n_locs}")

    # Set result to nan if no vs30 values are available
    if np.isnan(vs30):
        return np.full(len(DEFAULT_EXCEEDANCE_VALUES), np.nan), np.nan

    site_info = sc.site.SiteInfo(f"site_{ix}", lat, lon, vs30)

    result = sc.nz_code.nzta_2018.run_ensemble_nzta(
        ens, site_info, exceedance_values=DEFAULT_EXCEEDANCE_VALUES
    )
    return (
        result.pga_values.loc[DEFAULT_EXCEEDANCE_VALUES].values,
        np.flatnonzero(nzta_df.index.values == result.nearest_town)[0],
    )


def _process_nzs1170p5_station(
    ens: sc.gm_data.Ensemble,
    lat: float,
    lon: float,
    vs30: float,
    ims: Sequence[str],
    ix: int,
    n_locs: int,
):
    print(f"Processing location {ix + 1}/{n_locs}")
    # Get the periods
    sa_periods = [0 if im == "PGA" else sc.utils.get_period_from_pSA(im) for im in ims]

    # Set result to nan if no vs30 values are available
    if np.isnan(vs30):
        return (
            np.full((len(sa_periods), len(DEFAULT_EXCEEDANCE_VALUES)), np.nan),
            np.nan,
            np.full(len(sa_periods), np.nan),
            np.full(len(DEFAULT_EXCEEDANCE_VALUES), np.nan),
            np.full(len(sa_periods), np.nan),
        )

    site_info = sc.site.SiteInfo(f"site_{ix}", lat, lon, vs30)

    distance = sc.nz_code.nzs1170p5.get_distance_from_site_info(ens, site_info)
    z_factor = float(sc.nz_code.nzs1170p5.ll2z((site_info.lon, site_info.lat)))
    soil_class = sc.nz_code.nzs1170p5.get_soil_class(site_info.vs30)

    results, R_values, N_values, Ch_values = [], [], [], []
    for cur_exceedance in DEFAULT_EXCEEDANCE_VALUES:
        cur_rp = 1 / cur_exceedance

        if cur_rp < 20 or cur_rp > 2500:
            raise NotImplementedError()
        else:
            C, Ch, R, N = sha.nzs1170p5_spectra(
                sa_periods, z_factor, cur_rp, distance, soil_class.value
            )
            results.append(C)
            R_values.append(R)
            N_values.append(N)
            Ch_values.append(Ch)

    return (
        np.stack(results, axis=1),
        z_factor,
        N_values[0],
        np.asarray(R_values),
        Ch_values[0],
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "input_data",
        type=str,
        help="Path to input csv, must contain columns lon, lat and vs30",
    )
    parser.add_argument("output_dir", type=Path, help="Output directory path")
    parser.add_argument(
        "nz_code_type",
        type=str,
        help="The NZCode for which to generate data",
        choices=["NZS1170.5", "NZTA"],
    )
    parser.add_argument(
        "--nzta_town_csv",
        type=Path,
        help="Path to the NZTA town csv, required when computing NZTA",
    )
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )

    args = parser.parse_args()

    main(
        args.input_data,
        args.output_dir,
        args.nz_code_type,
        nzta_csv_ffp=args.nzta_town_csv,
        n_procs=args.n_procs,
    )
