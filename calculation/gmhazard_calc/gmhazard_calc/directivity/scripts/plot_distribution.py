"""
Plots the distribution of hypocentre across strike and dip from a saved dataframe of distribution values
"""
import argparse

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from gmhazard_calc.constants import EventType
import common


def plot_distribution(
    input_dir,
    faults,
    hypo_along_strikes,
    hypo_down_dips,
    output_dir,
):
    for fault_name in faults:
        fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
        for hypo_along_strike in hypo_along_strikes:
            csv = f"Strike_Distribution_{fault_name}_{hypo_along_strike}.csv"
            truncated_distribution = pd.read_csv(
                f"{input_dir}/{csv}", index_col=0
            ).to_numpy()
            ax1.hist(
                truncated_distribution,
                weights=np.ones(len(truncated_distribution))
                / len(truncated_distribution),
                label=hypo_along_strike,
                histtype="step",
            )
            fig.gca().yaxis.set_major_formatter(PercentFormatter(1))
            ax1.legend()
        ax1.set_title(f"{fault_name} Strike Distribution for range of hypocentres")
        ax1.set_ylabel("Percentage of hypocentres")
        ax1.set_xlabel("Spread across strike")
        fig.savefig(f"{output_dir}/{fault_name}_strike_distribution.png")

        fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
        for hypo_down_dip in hypo_down_dips:
            fault = nhm_dict[fault_name]
            event_type = EventType.from_rake(fault.rake)
            csv = f"Down_Dip_Distribution_{fault_name}_{event_type}_{hypo_down_dip}.csv"
            truncated_distribution = pd.read_csv(
                f"{input_dir}/{csv}", index_col=0
            ).to_numpy()
            ax1.hist(
                truncated_distribution,
                weights=np.ones(len(truncated_distribution))
                / len(truncated_distribution),
                label=hypo_down_dip,
                histtype="step",
            )
            fig.gca().yaxis.set_major_formatter(PercentFormatter(1))
            ax1.legend()
        ax1.set_title(f"{fault_name} Down Dip Distribution for range of hypocentres")
        ax1.set_ylabel("Percentage of hypocentres")
        ax1.set_xlabel("Spread down dip")
        fig.savefig(f"{output_dir}/{fault_name}_down_dip_distribution.png")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--faults",
        default=faults,
        nargs="+",
        help="List of faults to produce results for",
    )
    parser.add_argument(
        "--nstrikes",
        default=[200, 50, 20, 5],
        nargs="+",
        help="Number of hypocentres along strike",
    )
    parser.add_argument(
        "--ndips",
        default=[100, 20, 5, 2],
        nargs="+",
        help="Number of hypocentres down dip",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    plot_distribution(
        args.input_dir,
        args.faults,
        args.nstrikes,
        args.ndips,
        args.output_dir,
    )
