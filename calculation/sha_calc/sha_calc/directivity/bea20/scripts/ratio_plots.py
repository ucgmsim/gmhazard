import numpy as np
import matplotlib.pyplot as plt

import common

# Load common variables
nhm_dict, faults, im, grid_space, _ = common.default_variables()
fault_types = ["Strike Slip", "Strike Slip", "Strike Slip", "Dip Slip", "Dip Slip", "Dip Slip"]
nhyps = [5, 15, 30, 50]

for fault_name in faults:
    for nhyp in nhyps:
        fault, _, planes, lon_lat_depth, x, y = common.load_fault_info(fault_name, nhm_dict, grid_space)

        try:
            fdi_average = np.load(
                f"/home/joel/local/directivity/latin/mc/data/{fault_name}_{nhyp}_total_fd.npy")
            fdi_average = np.mean(fdi_average, axis=0)
            fdi_average = fdi_average.reshape((grid_space, grid_space))

            new_fd = np.load(
                f"/mnt/mantle_data/joel_scratch/directivity/latin_mc/{fault_name}_{nhyp}_fd_average.npy")
            new_fd = new_fd.reshape((grid_space, grid_space))

            ratio = new_fd / fdi_average

            title = f"{fault_name} Length={fault.length} Dip={fault.dip} Rake={fault.rake}"
            fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)

            c = ax1.pcolormesh(x, y, ratio, cmap='bwr', vmax=1.2, vmin=0.8)
            ax1.scatter(
                lon_lat_depth[:, 0][::2],
                lon_lat_depth[:, 1][::2],
                c=lon_lat_depth[:, 2][::2],
                label="srf points",
                s=1.0,
            )
            plt.colorbar(c)
            ax1.set_title(title)

            fig.savefig(f"/home/joel/local/directivity/latin/mc/depth_fix/ratio/{fault_name}_{nhyp}.png")
        except FileNotFoundError:
            print(f"Could not find file - Skipping {fault_name} {nhyp}")
