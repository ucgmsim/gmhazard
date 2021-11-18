import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

from sha_calc.directivity.bea20.EventType import EventType
import common

# Load common variables
nhm_dict, faults, im, grid_space, _ = common.default_variables()
hypo_along_strikes = [200, 50, 20, 5]
hypo_down_dips = [100, 20, 5, 2]

for fault_name in faults:

    fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
    for hypo_along_strike in hypo_along_strikes:

        csv = f"Strike_Distribution_{fault_name}_{hypo_along_strike}.csv"
        truncated_distribution = pd.read_csv(
            f"/home/joel/local/directivity/distributions2/{csv}", index_col=0
        ).to_numpy()
        ax1.hist(
            truncated_distribution,
            weights=np.ones(len(truncated_distribution)) / len(truncated_distribution),
            label=hypo_along_strike,
            histtype="step",
        )
        fig.gca().yaxis.set_major_formatter(PercentFormatter(1))
        ax1.legend()
    ax1.set_title(f"{fault_name} Strike Distribution for range of hypocentres")
    ax1.set_ylabel("Percentage of hypocentres")
    ax1.set_xlabel("Spread across strike")
    fig.savefig(
        f"/home/joel/local/directivity/distributions2/{fault_name}_strike_distribution.png"
    )

    fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
    for hypo_down_dip in hypo_down_dips:
        fault = nhm_dict[fault_name]
        event_type = EventType.from_rake(fault.rake)
        csv = f"Down_Dip_Distribution_{fault_name}_{event_type}_{hypo_down_dip}.csv"
        truncated_distribution = pd.read_csv(
            f"/home/joel/local/directivity/distributions2/{csv}", index_col=0
        ).to_numpy()
        ax1.hist(
            truncated_distribution,
            weights=np.ones(len(truncated_distribution)) / len(truncated_distribution),
            label=hypo_down_dip,
            histtype="step",
        )
        fig.gca().yaxis.set_major_formatter(PercentFormatter(1))
        ax1.legend()
    ax1.set_title(f"{fault_name} Down Dip Distribution for range of hypocentres")
    ax1.set_ylabel("Percentage of hypocentres")
    ax1.set_xlabel("Spread down dip")
    fig.savefig(
        f"/home/joel/local/directivity/distributions2/{fault_name}_down_dip_distribution.png"
    )
