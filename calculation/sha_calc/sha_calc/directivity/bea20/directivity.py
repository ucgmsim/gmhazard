import math
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from qcore import srf
from IM_calculation.source_site_dist import src_site_dist
from sha_calc.directivity.bea20 import bea20, utils


def get_directivity_effects(
    srf_file: str, srf_csv: Path, sites: np.ndarray, period: float = 3.0
):
    """Calculates directivity effects at the given sites and srf

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    sites: np.ndarray
        Numpy array full of site lon/lat values [[lon, lat],...]
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    """

    # Get rake, magnitude from srf_csv
    mag = pd.read_csv(srf_csv)["magnitude"][0]
    rake = pd.read_csv(srf_csv)["rake"][0]

    # Get planes and points from srf_file
    planes = srf.read_header(srf_file, idx=True)
    points = srf.read_latlondepth(srf_file)

    # Customise the planes to set different hypocentres
    n_hypo = 10
    planes_list, planes_index = utils.set_hypocenters(n_hypo, planes, [0.5])

    # Convert points to non dictionary format
    lon_lat_depth = np.asarray([[x["lon"], x["lat"], x["depth"]] for x in points])

    # Creating the average arrays
    (
        fd_average,
        fdi_average,
        phi_red_average,
        phi_redi_average,
        predictor_functions_average,
        other_average,
    ) = (
        np.asarray([]),
        np.asarray([]),
        np.asarray([]),
        np.asarray([]),
        np.asarray([]),
        np.asarray([]),
    )

    for index, planes in enumerate(planes_list):

        # Calculate rx ry from GC2
        rx, ry = src_site_dist.calc_rx_ry_GC2(
            lon_lat_depth, planes, sites, hypocentre_origin=True
        )

        # Gets the s_max values from the two end points of the fault
        nominal_strike, nominal_strike2 = utils.calc_nominal_strike(lon_lat_depth)
        rx_end, ry_end = src_site_dist.calc_rx_ry_GC2(
            lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
        )
        rx_end2, ry_end2 = src_site_dist.calc_rx_ry_GC2(
            lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
        )
        s_max = [min(ry_end, ry_end2)[0], max(ry_end, ry_end2)[0]]

        # Gets the plane index of the hypocenter
        plane_index = planes_index[index]

        # Trig to calculate extra features of the fault for directivity based on plane info
        z_tor = planes[plane_index]["dtop"]
        dip = planes[plane_index]["dip"]
        d_bot = z_tor + planes[plane_index]["width"] * math.sin(math.radians(dip))
        t_bot = z_tor / math.tan(math.radians(dip)) + planes[plane_index][
            "width"
        ] * math.cos(math.radians(dip))
        d = (planes[plane_index]["dhyp"] - z_tor) / math.sin(math.radians(dip))

        # Use the bea20 model to work out directivity (fd) at the given sites
        fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20.bea20(
            mag, ry, rx, s_max, d, t_bot, d_bot, rake, dip, period
        )

        s2 = other["S2"].reshape((100, 100))
        f_s2 = predictor_functions["fs2"].reshape((100, 100))
        f_theta = predictor_functions["ftheta"].reshape((100, 100))
        f_g = predictor_functions["fG"].reshape((100, 100))
        f_dist = predictor_functions["fdist"].reshape((100, 100))
        fdi = fdi.reshape((100, 100))

        hypo_lon, hypo_lat = srf.get_hypo(srf_file, custom_planes=utils.remove_plane_idx(planes))

        # Plot each hypocenter adjustment
        plot(
            np.asarray([coord[0] for coord in sites]).reshape((100, 100)),
            np.asarray([coord[1] for coord in sites]).reshape((100, 100)),
            s2,
            f_s2,
            f_theta,
            f_g,
            f_dist,
            fdi,
            lon_lat_depth,
            Path("/home/joel/local/AlpineK2T"),
            hypo_lon,
            hypo_lat,
            True
        )

        if fdi_average.size == 0:
            (
                fd_average,
                fdi_average,
                phi_red_average,
                phi_redi_average,
                predictor_functions_average,
                other_average,
            ) = (
                fd,
                fdi,
                phi_red,
                phi_redi,
                predictor_functions,
                other,
            )
        else:
            (
                fd_average,
                fdi_average,
                phi_red_average,
                phi_redi_average,
            ) = (
                np.add(fd_average, fd),
                np.add(fdi_average, fdi),
                np.add(phi_red_average, phi_red),
                np.add(phi_redi_average, phi_redi),
            )
            for key, value in predictor_functions.items():
                predictor_functions_average[key] = np.add(predictor_functions_average[key], predictor_functions[key])
            for key, value in other.items():
                other_average[key] = np.add(other_average[key], other[key])

    (
        fd_average,
        fdi_average,
        phi_red_average,
        phi_redi_average,
    ) = (
        np.divide(fd_average, n_hypo),
        np.divide(fdi_average, n_hypo),
        np.divide(phi_red_average, n_hypo),
        np.divide(phi_redi_average, n_hypo),
    )
    for key, value in predictor_functions_average.items():
        predictor_functions_average[key] = np.divide(predictor_functions_average[key], n_hypo)
    for key, value in other_average.items():
        other_average[key] = np.divide(other_average[key], n_hypo)

    return fd_average, fdi_average, phi_red_average, phi_redi_average, predictor_functions_average, other_average


def directivity_plots(
    srf_file: str, srf_csv: Path, output_dir: Path, period: float = 3.0
):
    """
    Creates 6 plots to show directivity effects at a given srf

    Parameters
    ----------
    srf_file: str
        String of the ffp to the location of the srf file
    srf_csv: Path
        Path to the location of the srf csv file
    output_dir: Path
        Path to the location of the output plot directory
    period: float, optional
        Float to indicate which period to extract from fD to get fDi
    """

    points = srf.read_latlondepth(srf_file)

    lon_lat_depth = np.asarray([[x["lon"], x["lat"], x["depth"]] for x in points])

    lon_values = np.linspace(
        lon_lat_depth[:, 0].min() - 0.5, lon_lat_depth[:, 0].max() + 0.5, 100
    )
    lat_values = np.linspace(
        lon_lat_depth[:, 1].min() - 0.5, lon_lat_depth[:, 1].max() + 0.5, 100
    )

    x, y = np.meshgrid(lon_values, lat_values)
    site_coords = np.stack((x, y), axis=2).reshape(-1, 2)

    fd, fdi, phi_red, phi_redi, predictor_functions, other = get_directivity_effects(
        srf_file, srf_csv, site_coords, period
    )

    s2 = other["S2"].reshape((100, 100))
    f_s2 = predictor_functions["fs2"].reshape((100, 100))
    f_theta = predictor_functions["ftheta"].reshape((100, 100))
    f_g = predictor_functions["fG"].reshape((100, 100))
    f_dist = predictor_functions["fdist"].reshape((100, 100))
    fdi = fdi.reshape((100, 100))

    hypo_lon, hypo_lat = srf.get_hypo(srf_file)

    plot(
        x,
        y,
        s2,
        f_s2,
        f_theta,
        f_g,
        f_dist,
        fdi,
        lon_lat_depth,
        output_dir,
        hypo_lon,
        hypo_lat,
    )


def plot(
    x: np.ndarray,
    y: np.ndarray,
    s2: np.ndarray,
    f_s2: np.ndarray,
    f_theta: np.ndarray,
    f_g: np.ndarray,
    f_dist: np.ndarray,
    fdi: np.ndarray,
    lon_lat_depth: np.ndarray,
    output_dir: Path,
    hypo_lon: float,
    hypo_lat: float,
    show_hypo: bool = False,
):
    """
    Plots directivity values output of the bea20 model.
    Extracted so it can be used for testing specific hypocentre scenarios.

    Parameters
    ----------
    x: np.ndarray
        Array of longitude values of sites
    y: np.ndarray
        Array of latitude values of sites
    s2: np.ndarray
        s2 output from the bea20 model for each site
    f_s2: np.ndarray
        f_s2 output from the bea20 model for each site
    f_theta: np.ndarray
        f_theta output from the bea20 model for each site
    f_g: np.ndarray
        f_g output from the bea20 model for each site
    f_dist: np.ndarray
        f_dist output from the bea20 model for each site
    fdi: np.ndarray
        fdi output from the bea20 model for each site
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format [[lon, lat, depth],...]
    output_dir: Path
        Path to the location of the output plot directory
    hypo_lon: float
        Longitude value of the hypocentre
    hypo_lat: float
        Latitude value of the hypocentre
    show_hypo: bool, optional
        If true then will show the hypocentre on the plot
    """

    fig = plt.figure(figsize=(16, 10))

    ax1 = fig.add_subplot(2, 3, 1)
    m = ax1.contourf(x, y, s2, cmap="bwr", vmin=10.0, vmax=70.0, levels=7)
    ax1.contour(x, y, s2, colors="k", linewidths=0.3, levels=7)
    ax1.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax1.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax1.set_title("S2")

    ax2 = fig.add_subplot(2, 3, 2)
    m = ax2.contourf(x, y, f_s2, cmap="bwr", levels=13)
    ax2.contour(x, y, f_s2, colors="k", linewidths=0.3, levels=13)
    ax2.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax2.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax2.set_title(r"$f_{S2}$")

    ax3 = fig.add_subplot(2, 3, 3)
    m = ax3.contourf(x, y, f_theta, cmap="bwr", levels=19)
    ax3.contour(x, y, f_theta, colors="k", linewidths=0.3, levels=19)
    ax3.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax3.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax3.set_title(r"$f_\theta$")

    ax4 = fig.add_subplot(2, 3, 4)
    m = ax4.contourf(x, y, f_g, cmap="bwr", levels=19)
    ax4.contour(x, y, f_g, colors="k", linewidths=0.3, levels=19)
    ax4.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax4.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax4.set_title(r"$f_G$")

    ax5 = fig.add_subplot(2, 3, 5)
    m = ax5.contourf(x, y, f_dist, cmap="bwr", levels=11)
    ax5.contour(x, y, f_dist, colors="k", linewidths=0.3, levels=11)
    ax5.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax5.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax5.set_title(r"$f_{dist}$")

    ax6 = fig.add_subplot(2, 3, 6)
    m = ax6.contourf(x, y, np.exp(fdi), cmap="bwr", levels=11)
    ax6.contour(x, y, np.exp(fdi), colors="k", linewidths=0.3, levels=11)
    ax6.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    if show_hypo:
        ax6.scatter(
            hypo_lon,
            hypo_lat,
            label="Hypocentre",
            marker="x",
            c="k",
            s=50.0,
        )
    plt.colorbar(m, pad=0.01)
    ax6.set_title(r"$f_Di$")

    fig.savefig(f"{output_dir}/directivity_plots{hypo_lon}.png")
