"""
Plots three different depths of hypocentre location for a given function of the Bayless 2020 model
to see how it changes based on depth
"""
import argparse

import numpy as np
import matplotlib.pyplot as plt

import common
from gmhazard_calc import directivity


def plot_bayless_model(fault_name, nhm_dict, grid_space, period, model_key, output_dir):
    depths = [0, 0.5, 1]
    depth_texts = ["min", "half", "max"]

    fault, site_coords, planes, lon_lat_depth, x, y = directivity.utils.load_fault_info(
        fault_name, nhm_dict, grid_space
    )

    (
        nominal_strike,
        nominal_strike2,
    ) = directivity.calc_nominal_strike(lon_lat_depth)

    site_data = dict()
    sample = [24, 49, 74]

    # Custom hypo location
    for i, depth in enumerate(depths):
        total_length = 0
        for plane in planes:
            total_length += plane["length"]
            plane["shyp"] = -999.9
            plane["dhyp"] = -999.9

        planes[1]["dhyp"] = planes[1]["width"] * depth
        planes[1]["shyp"] = 0

        hypo_lon, hypo_lat = directivity.utils.get_hypo_lon_lat(planes, lon_lat_depth)

        fd, (
            phi_red,
            predictor_functions,
            other,
        ) = directivity.directivity._compute_directivity_effect(
            lon_lat_depth,
            planes,
            1,
            site_coords,
            nominal_strike,
            nominal_strike2,
            fault.mw,
            fault.rake,
            [period],
        )

        if model_key in predictor_functions:
            model_value = predictor_functions[model_key]
        elif model_key in other:
            model_value = other[model_key]
        elif model_key == "phi_red":
            model_value = phi_red
        else:
            raise KeyError(f"Could not find {model_key} from bea20 output")
        model_value = model_value.reshape((grid_space, grid_space))

        sites_fg = [model_value[x, y] for x in sample for y in sample]
        site_data[depth_texts[i]] = sites_fg

        title = f"{fault_name} {model_key} Hypocentre Depth = {planes[1]['dhyp']} \nLength={fault.length} Dip={fault.dip} Rake={fault.rake}"

        fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)

        c = ax1.pcolormesh(x, y, model_value, cmap="Reds", vmin=0, vmax=3)
        ax1.scatter(
            lon_lat_depth[:, 0][::2],
            lon_lat_depth[:, 1][::2],
            c=lon_lat_depth[:, 2][::2],
            label="srf points",
            s=1.0,
        )
        cb = plt.colorbar(c)
        cb.set_label(f"{model_key}")
        ax1.set_title(title)
        ax1.set_ylabel("Latitude")
        ax1.set_xlabel("Longitude")
        plt.plot(hypo_lon, hypo_lat, marker="X", color="black", markersize=10)
        fig.savefig(f"{output_dir}/{fault_name}_{depth_texts[i]}")
        np.save(f"{output_dir}/{fault_name}_{depth_texts[i]}_fg.npy", model_value)

    fig = plt.figure(figsize=(16, 10))
    for x in range(9):
        site_values = []
        for i, depth_text in enumerate(depth_texts):
            sites = site_data[depth_text]
            site_values.append(sites[x])

        ax1 = fig.add_subplot(3, 3, x + 1)
        ax1.set_xlabel("Hypocentre Percentage Depth")
        ax1.set_ylabel(model_key)
        ax1.set_title(f"{fault_name} Site {x + 1}")

        ax1.errorbar(
            x=[f"{d*100}%" for d in depths], y=site_values, marker=".", color="blue"
        )

    plt.subplots_adjust(
        left=0.1, bottom=0.1, right=0.9, top=0.9, wspace=0.4, hspace=0.4
    )

    plt.savefig(f"{output_dir}/{fault_name}_fg_sites.png")

    fphi_min = np.load(f"{output_dir}/{fault_name}_min_fg.npy")
    fphi_half = np.load(f"{output_dir}/{fault_name}_half_fg.npy")
    fphi_max = np.load(f"{output_dir}/{fault_name}_max_fg.npy")
    a = fphi_min == fphi_max
    b = fphi_half == fphi_max
    print(f"Are all values the same? {a.all() and b.all()}")


def parse_args():
    nhm_dict, faults, im, grid_space, _ = common.default_variables()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "model_key",
        help="Bayless model function to extract e.g. fG, S2",
    )
    parser.add_argument("output_dir")
    parser.add_argument(
        "--fault_name",
        default="Ashley",
        help="Fault to calculate results for",
    )
    parser.add_argument(
        "--grid_space",
        default=grid_space,
        help="Number of sites to do along each axis",
    )
    parser.add_argument(
        "--period",
        default=im.period,
        help="Period to calculate directivity for",
    )
    return parser.parse_args(), nhm_dict


if __name__ == "__main__":
    args, nhm_dict = parse_args()

    plot_bayless_model(
        args.fault_name,
        nhm_dict,
        args.grid_space,
        args.period,
        args.model_key,
        args.output_dir,
    )
