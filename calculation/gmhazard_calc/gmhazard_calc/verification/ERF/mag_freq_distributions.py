import pathlib
import argparse
import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

from qcore.nhm import load_nhm


class ScalarFormatterClass(ScalarFormatter):
    def _set_format(self):
        self.format = "%1.4f"


def plot_mw_frequency(fault_data_path: str, ds_data_path: str):
    """Magnitude - frequency distribution

    Parameters
    fault_data_path: str
    ds_data_path: str
    """
    plot_directory = pathlib.Path(__file__).resolve().parent.parent / "plot"
    plot_directory.mkdir(exist_ok=True, parents=True)

    # Fault data
    fault_data = load_nhm(fault_data_path)
    results = []
    for nhm_fault in fault_data.values():
        results.append([nhm_fault.name, nhm_fault.mw, 1 / nhm_fault.recur_int_median])
    fault_df = pd.DataFrame(results, columns=["Name", "Mw", "recur_median"])

    # DS data
    ds_df = pd.read_csv(ds_data_path)

    # Sort by Mw
    fault_df = fault_df.sort_values(by=["Mw"])
    ds_df = ds_df.sort_values(by=["mw"])

    # DS and Fault have a different range of Mw so sample it
    mw_range = np.arange(5, 9, 0.01)
    clean_mw_range = ["%.2f" % mw for mw in mw_range]

    # Because for fault, we want sum or recurrences that is bigger than or equal to the current Mw
    # So even out Fault data starts from 5.52 Mw, can be used on 5.00 Mw
    # as it is still smaller than 5.52 Mw
    fault_result_dict = {}
    for mw in clean_mw_range:
        fault_result_dict[float(mw)] = fault_df.loc[
            fault_df.Mw >= float(mw), "recur_median"
        ].sum()

    # Sum the annual_rec_prob for each Mw
    aggregation_function = {"annual_rec_prob": "sum"}
    ds_df_new = ds_df.groupby(ds_df["mw"]).aggregate(aggregation_function)

    # bring back index to mw column
    ds_df_new.reset_index(level=0, inplace=True)
    # Just like fault, do the same process on DS based on Mw
    ds_result_dict = {}
    for _, row in ds_df_new.iterrows():
        ds_result_dict[row["mw"]] = ds_df_new.loc[
            ds_df_new.mw >= row.mw, "annual_rec_prob"
        ].sum()

    # To combine recurrences between Fault data and DS data
    sorted_combined = {}

    for mw, prob in ds_result_dict.items():
        if mw in fault_result_dict:
            sorted_combined[mw] = ds_result_dict[mw] + fault_result_dict[mw]

    # Add rest of fault result after the last Mw that can be found from ds_result_dict
    last_mw_from_ds_data = list(ds_result_dict.keys())[-1]
    for mw, prob in fault_result_dict.items():
        if mw > last_mw_from_ds_data:
            sorted_combined[mw] = prob

    # Plot using matplotlib
    fig, ax = plt.subplots(figsize=(18, 13.5), dpi=300)

    ax.plot(
        list(fault_result_dict.keys()),
        list(fault_result_dict.values()),
        label="Fault",
        linestyle="dashdot",
    )
    ax.plot(
        list(ds_result_dict.keys()),
        list(ds_result_dict.values()),
        label="Distributed",
        linestyle="dotted",
    )
    ax.plot(
        list(sorted_combined.keys()),
        list(sorted_combined.values()),
        label="Combined",
        linestyle="solid",
    )
    ax.legend(fontsize="x-large")
    ax.xaxis.set_label_text("Mw")
    ax.yaxis.set_label_text("Number/yr (>=M)")
    ax.set_yscale("log")

    ax.set_xlim(
        min(min(list(fault_result_dict.keys())), min(list(ds_result_dict.keys())))
    )

    # Set the y-axis label, currently supports 4 dp, refer to the ScalarFormatterClass
    for axis in [ax.yaxis]:
        formatter = ScalarFormatterClass()
        formatter.set_scientific(False)
        axis.set_major_formatter(formatter)

    # plt.show()
    plt.savefig(f"{plot_directory}/magnitude_frequency_distribution.png")
    print("Plotting job is finished")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--fault",
        type=str,
        help="Fault data path (default: path from env.",
        default=os.getenv("FAULT_DATA_PATH"),
    )
    parser.add_argument(
        "--ds",
        type=str,
        help="DS data path (default: path from env.",
        default=os.getenv("DS_DATA_PATH"),
    )
    args = parser.parse_args()

    plot_mw_frequency(args.fault, args.ds)
