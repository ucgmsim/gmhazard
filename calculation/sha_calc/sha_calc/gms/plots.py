from typing import Dict
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import sha_calc.gcim.distributions as dist
from . import shared


def plot_IMi_GMS(
    gcim: dist.Uni_lnIMi_IMj,
    IMi: str,
    realisations: pd.Series,
    output_ffp: str,
    sel_gms_IM_values: pd.Series = None,
    alpha: float = 0.1,
):
    """Plots the conditional marginal distribution (CDF) for the
    specified IMi and the KS test limits for the specified alpha,
    along with the generated realisations and selected ground motions

    Parameters
    ----------
    gcim: SimGCIMResult
        GCIM distributions
    IMi: string
        IM for which to plot the GCIM
    realisations: pandas dataframe
        Realisation IM values
        Shape: [n_realisation, n_IMs]
    ground_motions: list of strings or list of list of strings, optional
        Names of the selected ground motions, if multiple list of names
        are passed in, then these are plotted separately
        Note: This assumes that the ground motions were selected
        from the same ground motions that were used
        to generate the GCIM (i.e. same IM dataframe)
    output_ffp: string
        Output full file path
    alpha: float, optional
    """

    def plot_cdf(values: np.ndarray, ax: plt.Axes, label: str, plot_kwargs: Dict):
        values = np.sort(values)
        y_values = np.arange(0, values.size) / float(values.size)
        ax.step(values, y_values, label=label, **plot_kwargs)
        ax.plot([values[-1], values[-1]], [y_values[-1], 1.0], **plot_kwargs)

    D_crit = shared.ks_critical_value(realisations.shape[0], alpha)

    rel_values = np.sort(realisations.values)
    cdf_x, cdf_y = gcim.cdf.index.values, gcim.cdf.values

    fig, ax = plt.subplots(figsize=(16, 10))

    plt.plot(cdf_x, cdf_y, "r-", label="GCIM distribution")
    plt.plot(cdf_x, cdf_y + D_crit, "r--", label=fr"KS bounds, $\alpha={alpha}$")
    plt.plot(cdf_x, cdf_y - D_crit, "r--")

    plot_cdf(rel_values, ax, "Realisations", {"c": "b", "linestyle": "-"})

    if sel_gms_IM_values is not None:
        plot_cdf(
            sel_gms_IM_values.values,
            ax,
            label="Selected ground motions",
            plot_kwargs={"c": "grey"},
        )

    plt.xscale("log")

    # Getting the ticks right
    major_ticks = np.power(10.0, np.arange(-5, 2, 1))
    minor_ticks = (np.arange(1, 10, 1)[:, np.newaxis] * major_ticks).T.ravel()
    ax.xaxis.set_ticks(major_ticks)
    ax.xaxis.set_ticks(minor_ticks, minor=True)

    # x & y limits and grid
    plt.xlim(
        [
            cdf_x[np.min(np.flatnonzero(~np.isclose(cdf_y, 0)))],
            cdf_x[np.max(np.flatnonzero(~np.isclose(cdf_y, 1.0)))],
        ]
    )
    plt.ylim([0.0, 1.0])
    plt.grid(which="major", linestyle="--", linewidth=1.0)
    plt.grid(which="minor", linestyle="--", linewidth=0.5)

    plt.xlabel(IMi)
    plt.ylabel("Cumulative Probability, CDF")
    plt.legend(loc="lower right")
    plt.tight_layout()

    plt.savefig(output_ffp)
    plt.close()


def gen_GMS_plots(
    gcim_dict: Dict[str, dist.Uni_lnIMi_IMj],
    realisations: pd.DataFrame,
    output_dir: str,
    sel_gms_IM_values: pd.DataFrame,
    alpha: float = 0.1,
):
    """
    Plots GCIM distribution for all the available IMs

    Parameters
    ----------
    See plot_GCIM function for parameter details
    """
    output_dir = Path(output_dir)
    for IMi, cur_gcim in gcim_dict.items():
        file_name = f"{IMi.replace('.', 'p')}.png" if "." in IMi else f"{IMi}.png"
        plot_IMi_GMS(
            cur_gcim,
            IMi,
            realisations[IMi],
            str(output_dir / file_name),
            alpha=alpha,
            sel_gms_IM_values=None
            if sel_gms_IM_values is None
            else sel_gms_IM_values[IMi],
        )
