import numpy as np
import matplotlib.pyplot as plt

import common

# Load common variables
nhm_dict, faults, im, grid_space, _ = common.default_variables()
fault_types = [
    "Strike Slip",
    "Strike Slip",
    "Strike Slip",
    "Dip Slip",
    "Dip Slip",
    "Dip Slip",
]
nhyps = [5, 15, 30, 50]
sample = [24, 49, 74]

for fault_name in faults:

    sites = [[x, y] for x in sample for y in sample]
    for x, site in enumerate(sites):
        fig = plt.figure(figsize=(16, 10))
        for i, nhyp in enumerate(nhyps):
            total = np.load(
                f"/home/joel/local/directivity/latin/mc/data/{fault_name}_{nhyp}_total_fd.npy"
            ).reshape((100, 100, 100, 1))
            site_100 = total[:, site[0], site[1]]
            ax1 = fig.add_subplot(2, 2, i + 1)
            ax1.set_xlabel("fD")
            ax1.set_ylabel("Count")
            plt.title(f"{fault_name} {nhyp} Site {x+1}")

            plt.hist(site_100)

        plt.subplots_adjust(
            left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4
        )

        plt.savefig(
            f"/home/joel/local/directivity/latin/mc/plots/sites/convergance_{fault_name}_site_{x}.png"
        )
