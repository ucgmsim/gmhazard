from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt


def validation_plot(
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
):
    """
    Plots 6 directivity figures from the output of the bea20 model.

    Parameters
    ----------
    x: np.ndarray
        Array of longitude values of sites
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    y: np.ndarray
        Array of latitude values of sites
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    s2: np.ndarray
        s2 output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    f_s2: np.ndarray
        f_s2 output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    f_theta: np.ndarray
        f_theta output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    f_g: np.ndarray
        f_g output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    f_dist: np.ndarray
        f_dist output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    fdi: np.ndarray
        fdi output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format [[lon, lat, depth],...]
    output_dir: Path
        Path to the location of the output plot directory
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
    plt.colorbar(m, pad=0.01)
    ax6.set_title(r"$f_Di$")

    fig.savefig(f"{output_dir}/directivity_validation_plot.png")


def plot_fdi(
    x: np.ndarray,
    y: np.ndarray,
    fdi: np.ndarray,
    lon_lat_depth: np.ndarray,
    output_ffp: Path,
    title: str = r"$f_Di$",
):
    """
    Plots fdi values based on the given srf and site x, y locations.

    Parameters
    ----------
    x: np.ndarray
        Array of longitude values of sites
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    y: np.ndarray
        Array of latitude values of sites
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    fdi: np.ndarray
        fdi output from the bea20 model for each site
        Dimension of n * m where n is number of sites across the x axis and m is the number of sites across the y axis
    lon_lat_depth: np.ndarray
        Each point of the srf fault in an array with the format [[lon, lat, depth],...]
    output_ffp: Path
        Ffp to the location of the output plot image
    title: string, optional
        The title for the plot
    """
    fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)

    c = ax1.pcolormesh(x, y, np.exp(fdi), cmap="bwr")
    ax1.scatter(
        lon_lat_depth[:, 0][::2],
        lon_lat_depth[:, 1][::2],
        c=lon_lat_depth[:, 2][::2],
        label="srf points",
        s=1.0,
    )
    cb = plt.colorbar(c)
    cb.set_label("fD")
    plt.ylabel("Latitude")
    plt.xlabel("Longitude")
    ax1.set_title(title)

    fig.savefig(f"{output_ffp}")
