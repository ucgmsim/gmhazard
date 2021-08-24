"""Produces a table of the correlations for non-pSA IM, and for
pSA produces period-based plots"""
import argparse
from typing import Sequence
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sha_calc as sha_calc

DEFAULT_PERIODS = np.logspace(np.log(0.01000001), np.log(10.0), base=np.e)
DEFAULT_PERIODS[-1] = 10.0
DEFAULT_IMS = ["PGA", "PGV", "CAV", "ASI", "DSI", "SI", "Ds575", "Ds595", "AI"]


def main(
    output_dir: Path,
    pSA_periods: Sequence[float] = DEFAULT_PERIODS,
    ims: Sequence[str] = DEFAULT_IMS,
):
    pSA_periods = np.sort(np.asarray(pSA_periods))
    pSA_ims = np.char.add("pSA_", pSA_periods.astype(str))
    # Generate the plots
    for cur_im in ims:
        cur_corr = [
            sha_calc.get_im_correlations(cur_im, cur_pSA_im) for cur_pSA_im in pSA_ims
        ]

        plt.figure()
        plt.plot(DEFAULT_PERIODS, cur_corr)
        plt.semilogx()
        plt.xlabel("pSA period (s)")
        plt.ylabel(r"$\rho$")
        plt.title(f"Correlation of {cur_im} vs pSA")
        plt.savefig(output_dir / f"{cur_im}_pSA_comparison.png")
        plt.close()

    # Generate the csv
    im_correlations = [
        [sha_calc.get_im_correlations(cur_im_i, cur_im_j) for cur_im_i in ims]
        for cur_im_j in ims
    ]
    im_correlations_df = pd.DataFrame(data=im_correlations, columns=ims, index=ims)
    im_correlations_df.to_csv(output_dir / "IM_correlations.csv")


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("output_dir", type=Path)

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(args.output_dir)
