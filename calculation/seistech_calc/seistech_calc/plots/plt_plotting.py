from typing import Optional, List, Tuple, Dict, Union

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt, cm as cm, colors as ml_colors

from seistech_calc.im import IM


def plot_disagg_src_type(
    flt_bin_contr: np.ndarray,
    ds_bin_contr: np.ndarray,
    mag_edges: np.ndarray,
    rrup_edges: np.ndarray,
    mag_bin_size: float,
    rrup_bin_size: float,
    save_file: Optional[str] = None,
    title: Optional[str] = None,
    fig_kwargs: Optional[Dict[str, object]] = None,
):
    """
    Plots the disaggregation histogram for magnitude and rupture distance
    binned by source type (i.e. fault and distributed seismicity)

    Parameters
    ----------
    flt_bin_contr: np.ndararry of float
        Matrix of shape [n_mag_bins, n_rrup_bins], with each value
        giving summed contribution of all ruptures in that specific bin
    ds_bin_contr: np.ndararry of float
        Matrix of shape [n_mag_bins, n_rrup_bins], with each value
        giving summed contribution of all ruptures in that specific bin
    mag_edges: np.ndarray
        The magnitude bin edges, shape [n_mag_bins + 1]
    rrup_edges: np.ndarray
        The rrup bin edges, shape [n_rrup_bins + 1]
    mag_bin_size: float, optional
        Magnitude bin size
    rrup_bin_size: float, optional
        Rupture distance bin size
    save_file: str, optional
        Full file path of save location for the plot
    title: str, optional
        Title of the plot
    fig_kwargs: Dictionary, optional
        Keyword arguments for the plt.figure call,
        such as figsize, dpi, etc.
    """
    if fig_kwargs is None:
        fig_kwargs = {}

    flt_bin_contr, ds_bin_contr = (
        flt_bin_contr.ravel() * 100,
        ds_bin_contr.ravel() * 100,
    )

    mag_pos, rrup_pos = np.meshgrid(mag_edges[:-1], rrup_edges[:-1], indexing="ij")
    mag_pos, rrup_pos = mag_pos.ravel(), rrup_pos.ravel()

    fig = plt.figure(**fig_kwargs)
    ax = fig.add_subplot(111, projection="3d")
    flt_mask, ds_mask = flt_bin_contr > 0, ds_bin_contr > 0

    # Plot fault
    if np.any(flt_mask):
        ax.bar3d(
            rrup_pos[flt_mask],
            mag_pos[flt_mask],
            0,
            rrup_bin_size / 1.5,
            mag_bin_size / 1.5,
            flt_bin_contr[flt_mask],
            # matplotlib bug hack..
            color="royalblue"
            if len(rrup_pos[flt_mask]) != len("royalblue")
            else "blue",
        )
    # Plot ds
    if np.any(ds_mask):
        ax.bar3d(
            rrup_pos[ds_mask],
            mag_pos[ds_mask],
            flt_bin_contr[ds_mask],
            rrup_bin_size / 1.5,
            mag_bin_size / 1.5,
            ds_bin_contr[ds_mask],
            # matplotlib bug hack... (https://github.com/matplotlib/matplotlib/issues/15815)
            color="lime" if len(rrup_pos[ds_mask]) != len("lime") else "green",
        )

    ax.set_xlim((0.0, rrup_edges.max() + (rrup_bin_size / 2)))
    ax.set_xticks(np.arange(0, rrup_edges.max() + rrup_bin_size, 20))
    ax.set_ylim((5.0, 9.0))
    ax.set_xlabel("Rupture Distance")
    ax.set_ylabel("Magnitude")
    ax.set_zlabel("% Contribution")
    ax.set_title(title)

    plt.legend(
        [
            plt.Rectangle((0, 0), 1, 1, fc="lime"),
            plt.Rectangle((0, 0), 1, 1, fc="royalblue"),
        ],
        ["ds", "fault"],
    )

    if save_file is not None:
        plt.savefig(save_file)
    else:
        plt.show()

    plt.close()


def plot_disagg_epsilon(
    eps_bins: List[Tuple[float, float]],
    eps_bin_contr: List[np.ndarray],
    mag_edges: np.ndarray,
    rrup_edges: np.ndarray,
    mag_bin_size: float,
    rrup_bin_size: float,
    save_file: Optional[str] = None,
    title: Optional[str] = None,
    fig_kwargs: Optional[Dict] = None,
):
    """Plots the disaggregation histogram for magnitude and rupture distance
    binned by epsilon

    Parameters
    ----------
    eps_bins: list of float tuples
        The min and max value of the epsilon bins
    eps_bin_contr: List of float arrays
        The contribution of the different eps bins
        Each array has shape [n_mag_bins, n_rrup_bins]
    mag_edges: np.ndarray
        The magnitude bin edges, shape [n_mag_bins + 1]
    rrup_edges: np.ndarray
        The rrup bin edges, shape [n_rrup_bins + 1]
    mag_bin_size: float, optional
        Magnitude bin size
    rrup_bin_size: float, optional
        Rupture distance bin size
    save_file: str, optional
        Full file path of save location for the plot
    title: str, optional
        Title of the plot
    fig_kwargs: Dictionary, optional
        Keyword arguments for the plt.figure call,
        such as figsize, dpi, etc.
    """
    if fig_kwargs is None:
        fig_kwargs = {}

    mag_pos, rrup_pos = np.meshgrid(mag_edges[:-1], rrup_edges[:-1], indexing="ij")

    mag_pos = mag_pos.ravel()
    rrup_pos = rrup_pos.ravel()

    # This is a hack, due to a matplolib bug...
    colours = [
        "darkred",
        "red",
        "firebrick",
        "lightcoral",
        "lavender",
        "lightsteelblue",
        "blue",
        "darkblue",
    ]
    assert len(colours) == len(eps_bin_contr)

    cmap = cm.get_cmap("seismic_r")
    cmap_colours = [
        cmap(cl_value) for cl_value in np.linspace(0.25, 0.75, len(eps_bin_contr))
    ]
    legend_proxies, legend_labels = [], []

    fig = plt.figure(**fig_kwargs)
    ax = fig.add_subplot(111, projection="3d")
    cur_sum_contr = None
    for ix, (eps_bin, eps_bin_contr) in enumerate(zip(eps_bins, eps_bin_contr)):
        eps_bin_contr = eps_bin_contr.ravel()
        cur_mask = eps_bin_contr > 0.0

        legend_proxies.append(
            plt.Rectangle((0, 0), 1, 1, fc=ml_colors.to_hex(colours[ix]))
        )
        legend_labels.append(rf"{eps_bin[0]} <= $\epsilon$ < {eps_bin[1]}")
        if eps_bin_contr[cur_mask].size > 0:
            ax.bar3d(
                rrup_pos[cur_mask],
                mag_pos[cur_mask],
                0 if cur_sum_contr is None else cur_sum_contr[cur_mask],
                rrup_bin_size / 1.5,
                mag_bin_size / 1.5,
                eps_bin_contr[cur_mask] * 100,
                # matplotlib bug hack... (https://github.com/matplotlib/matplotlib/issues/15815)
                color=ml_colors.to_hex(cmap_colours[ix])
                if len(rrup_pos[cur_mask]) != 7
                else colours[ix],
            )

            cur_sum_contr = (
                eps_bin_contr
                if cur_sum_contr is None
                else cur_sum_contr + (eps_bin_contr * 100)
            )

    ax.set_xlim((0.0, rrup_edges.max() + (rrup_bin_size / 2)))
    ax.set_xticks(np.arange(0, rrup_edges.max() + rrup_bin_size, 20))
    ax.set_ylim((5.0, 9.0))
    ax.set_xlabel("Rrup")
    ax.set_ylabel("Magnitude")
    ax.set_zlabel("% Contribution")
    ax.set_title(title)

    plt.legend(legend_proxies, legend_labels, loc="upper left")

    if save_file is not None:
        plt.savefig(save_file)
    else:
        plt.show()

    plt.close()


def plot_hazard(
    hazard_df: pd.DataFrame,
    title: str,
    im: IM,
    save_file: str = None,
    nz_code_hazard: pd.Series = None,
    nzta_hazard: pd.Series = None,
):
    """Plots the hazard curves, also saves the plot
    if a save file is specified
    """
    fig, ax = plt.subplots(figsize=(12, 9))

    im_values = hazard_df.index.values
    ax.plot(im_values, hazard_df.get("total").values, color="black", label="Total")
    ax.plot(im_values, hazard_df.get("fault").values, color="red", label="Fault")
    ax.plot(
        im_values,
        hazard_df.get("ds").values,
        color="green",
        label="Distributed Seismicity",
    )

    if "16th" in hazard_df and "84th" in hazard_df:
        ax.plot(
            im_values,
            hazard_df.get("16th").values,
            color="black",
            linestyle="dashed",
            label="$16^{th}$ Percentile",
        )
        ax.plot(
            im_values,
            hazard_df.get("84th").values,
            color="black",
            linestyle="dashed",
            label="$84^{th}$ Percentile",
        )

    if nz_code_hazard is not None:
        ax.plot(
            nz_code_hazard.values,
            nz_code_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="^",
            label="NZS1170.5 Code",
        )

    if nzta_hazard is not None:
        ax.plot(
            nzta_hazard.values,
            nzta_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="s",
            markerfacecolor="none",
            label="NZTA Code",
        )

    _hazard_plot(im, im_values, title, save_file=save_file)


def plot_hazard_totals(
    hazard_df: pd.DataFrame,
    branch_hazard: Dict[str, pd.DataFrame],
    title: str,
    im: IM,
    save_file: str = None,
    nz_code_hazard: pd.Series = None,
    nzta_hazard: pd.Series = None,
):
    """Similar to plot_hazard, except that it plots
    the ensemble total and the total for each branch
    """
    fig, ax = plt.subplots(figsize=(12, 9))

    im_values = hazard_df.index.values

    # Plot the individual branches totals
    for ix, (cur_name, cur_hazard_df) in enumerate(branch_hazard.items()):
        label = None if ix > 0 else "Individual branches"
        ax.plot(
            im_values,
            cur_hazard_df.get("total").values,
            linewidth=1,
            color="gray",
            label=label,
        )

    if nz_code_hazard is not None:
        ax.plot(
            nz_code_hazard.values,
            nz_code_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="^",
            label="NZS1170.5 Code",
        )

    if nzta_hazard is not None:
        ax.plot(
            nzta_hazard.values,
            nzta_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="s",
            markerfacecolor="none",
            label="NZTA Code",
        )

    # Plot the ensemble total last (to ensure its on top)
    ax.plot(
        im_values,
        hazard_df.get("total").values,
        label="Ensemble mean",
        linewidth=2,
        color="k",
    )

    if "16th" in hazard_df and "84th" in hazard_df:
        ax.plot(
            im_values,
            hazard_df.get("16th").values,
            color="black",
            linestyle="dashed",
            label="$16^{th}$ Percentile",
        )
        ax.plot(
            im_values,
            hazard_df.get("84th").values,
            color="black",
            linestyle="dashed",
            label="$84^{th}$ Percentile",
        )

    _hazard_plot(im, im_values, title, save_file=save_file)


def _hazard_plot(im: IM, im_values: np.ndarray, title: str, save_file: str = None):
    """Internal function, sets the details for a hazard plot"""
    plt.yscale("log")
    plt.xscale("log")

    plt.ylim((1e-5, 1))
    plt.xlim((im_values.min(), im_values.max()))

    plt.title(title)
    plt.xlabel(f"{im}")
    plt.ylabel("Annual rate of exceedance")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
    else:
        plt.show()

    plt.close()


def plot_uhs(
    uhs_df: pd.DataFrame,
    nz_code_uhs: pd.DataFrame = None,
    station_name: str = None,
    legend_rp: bool = True,
    save_file: str = None,
):
    """Plots the different uniform hazard spectra, also saves the
    plot if a save file is specified

    Parameters
    ----------
    uhs_df: pd.DataFrame
        The SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    nz_code_uhs: pd.DataFrame
        The NZ code SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    station_name: str, optional
        Name of the station this plot is for, used for the plot title
    legend_rp: bool, optional
        If set then the legend labels the lines in terms of
        return period instead of exceedance rate
    save_file: str, optional
    """

    def get_legend_label(rp: Union[str, int]):
        rp = int(rp.split("_")[0]) if isinstance(rp, str) else rp

        return f"{rp}" if legend_rp else f"{1 / rp:.4f}"

    fig, ax = plt.subplots(figsize=(12, 9))
    for col_ix, col in enumerate(uhs_df.columns.values):
        if col.endswith("mean"):
            ax.plot(
                uhs_df.index.values,
                uhs_df.iloc[:, col_ix].values,
                label=get_legend_label(col),
            )

    if nz_code_uhs is not None:
        for col_ix, col in enumerate(nz_code_uhs.columns.values):
            # Check that there are non-nan entries
            if np.count_nonzero(~np.isnan(nz_code_uhs.iloc[:, col_ix].values)) > 0:
                ax.plot(
                    nz_code_uhs.index.values,
                    nz_code_uhs.iloc[:, col_ix].values,
                    label=f"NZS1170.5 Code - {get_legend_label(int(1 / col))}",
                    color="k",
                )

    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")

    plt.legend(title="Return period" if legend_rp else "Exceedance")

    if station_name is not None:
        plt.title(station_name)

    if save_file is not None:
        plt.savefig(save_file)
    else:
        plt.show()


def plot_uhs_branches(
    branch_uhs_df: pd.DataFrame,
    mean_period_values: np.ndarray,
    mean_sa_values: np.ndarray,
    rp: int,
    station: str = None,
    save_ffp: str = None,
):
    """Plots the branches UHS and ensemble mean for one exceedance rate"""
    plt.figure(figsize=(12, 9))

    for ix, cur_col in enumerate(branch_uhs_df.columns):
        plt.plot(
            branch_uhs_df.index.values,
            branch_uhs_df[cur_col].values,
            linewidth=1,
            color="gray",
            label="Branches" if ix == 0 else None,
        )

    plt.plot(
        mean_period_values,
        mean_sa_values,
        linewidth=2,
        color="black",
        label="Ensemble Mean",
    )

    plt.title(f"{station}, Return period - {rp}")
    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")

    plt.legend(title="Return period")

    if save_ffp is not None:
        plt.savefig(save_ffp)
        plt.close()
    else:
        plt.show()
