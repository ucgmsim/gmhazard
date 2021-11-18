import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import common

# Load common variables
nhm_dict, faults, im, grid_space, _ = common.default_variables()
nhyps = [5, 15, 30, 50]

for fault_name in faults:

    fault, _, planes, lon_lat_depth, x, y = common.load_fault_info(fault_name, nhm_dict, grid_space)

    modes = ["std", "mean bias"]

    baseline_array = pd.read_csv(f"/home/joel/local/directivity/new_baseline/{fault_name}_20000.csv",
                                 index_col=0).to_numpy().reshape((10000, 1))

    for mode in modes:
        fig = plt.figure(figsize=(16, 10))

        for i, nhyp in enumerate(nhyps):
            fd_array = np.load(f"/home/joel/local/directivity/latin/mc/data/{fault_name}_{nhyp}_total_fd.npy")
            ratio = np.log(fd_array / baseline_array)

            if mode == "std":
                values = np.std(ratio, axis=0).reshape((grid_space, grid_space))
            else:
                values = np.mean(ratio, axis=0).reshape((grid_space, grid_space))

            ax1 = fig.add_subplot(2, 3, i + 1)
            if mode == "std":
                bounds = list(np.round(np.linspace(0, 0.05, 13), 3))
                c = plt.contourf(x, y, values, levels=bounds, cmap=plt.cm.get_cmap('Reds', 12), extend='max')
                # c = ax1.pcolormesh(x, y, values, cmap='Reds', vmax=0.05, vmin=0, shading='flat')
            else:
                bounds = list(np.round(np.linspace(-0.03, 0.03, 21), 3))
                colour_map = ['#ff0000', '#ff1b1b', '#ff3636', '#ff5151', '#ff6b6b', '#ff8686', '#ffa1a1', '#ffbcbc', '#ffd7d7', '#ffffff', '#ffffff', '#d7d7ff', '#bcbcff', '#a1a1ff', '#8686ff', '#6b6bff', '#5151ff', '#3636ff', '#1b1bff', '#0000ff']
                colour_map.reverse()
                c = plt.contourf(x, y, values, levels=bounds, colors=colour_map)
                # c = ax1.pcolormesh(x, y, values, cmap='bwr', vmax=0.3, vmin=-0.3, shading='flat')
            ax1.scatter(
                lon_lat_depth[:, 0][::2],
                lon_lat_depth[:, 1][::2],
                c=lon_lat_depth[:, 2][::2],
                label="srf points",
                s=1.0,
            )
            cb = plt.colorbar(c, pad=0)
            if mode == "mean bias":
                cb.set_label('mean of (ln(estimate) - ln(exact))')
            else:
                cb.set_label('std of (ln(estimate) - ln(exact))')
            ax1.set_title(f"{nhyp} Hypocentres")
            plt.xlabel("Longitude")
            plt.ylabel("Latitude")

        plt.subplots_adjust(left=0.1,
                            bottom=0.1,
                            right=0.95,
                            top=0.90,
                            wspace=0.40,
                            hspace=0.35)
        fig.suptitle(f'{fault_name} {mode} across all sites', fontsize=16)
        if mode == "mean bias":
            fig.savefig(f"/home/joel/local/directivity/latin/mc/plots/{fault_name}_mean_bias.png")
        else:
            fig.savefig(f"/home/joel/local/directivity/latin/mc/plots/{fault_name}_{mode}.png")
        plt.close()
