import pathlib

import numpy as np
import matplotlib.pyplot as plt

import sha_calc as sha_calc


def get_correlation_data():
    """Get three different variables to plot contour plots with
    Baker 2008 implementation on OpenSHA"""
    period_values = np.logspace(-2, 1, num=100, base=10.0)
    x_data, y_data = np.meshgrid(period_values, period_values)
    results = []
    for period_a in period_values:
        period_a_result = []
        for period_b in period_values:
            col_result = sha_calc.src.gcim.im_correlations.baker_correlations_2008(
                f"pSA_{period_a}", f"pSA_{period_b}"
            )
            period_a_result.append(col_result)
        results.append(period_a_result)

    return x_data, y_data, np.array(results)


def get_contour_plots(x: np.ndarray, y: np.ndarray, z: np.ndarray):
    """Get pSA correlation contour plots

    Parameter
    ---------
    x: np.ndarray
        rectangular grid out of an array of periods
    y: np.ndarray
        rectangular grid out of an array of periods
    z: np.ndarray
        list of spectral acceleration correlation
        coefficients based on Baker 2008 implementation
    """
    plot_directory = pathlib.Path(__file__).resolve().parent.parent / "plot"
    plot_directory.mkdir(exist_ok=True, parents=True)

    fig, ax = plt.subplots(figsize=(18, 13.5))
    cs = ax.contour(x, y, z)
    ax.clabel(cs, inline=True, fontsize=8)
    ax.set_title("baker_correlations_2008")
    ax.axes.set_aspect("equal")
    ax.xaxis.set_label_text("T [s]")
    ax.yaxis.set_label_text("T [s]")
    ax.set_xscale("log")
    ax.set_yscale("log")

    plt.savefig(f"{plot_directory}/psa_correlation_contour.png")


if __name__ == "__main__":
    x_data, y_data, z_data = get_correlation_data()
    get_contour_plots(x_data, y_data, z_data)
