from typing import Optional, List, Tuple, Dict, Union
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt, cm as cm, colors as ml_colors

from seistech_calc.im import IM
from seistech_calc import utils


GCIM_LABEL = {
    "16th": "GCIM - $16^{th}$ Percentile",
    "median": "GCIM - Median",
    "84th": "GCIM - $84^{th}$ Percentile",
}

IM_DISTRIBUTION_LABEL = {
    "PGA": "Peak ground acceleration, PGA (g)",
    "PGV": "Peak ground velocity, PGV (cm/s)",
    "CAV": "Cumulative absolute velocity, CAV (g.s)",
    "Ds595": "5-95% Significant duration, Ds595 (s)",
    "Ds575": "5-75% Significant duration, Ds575 (s)",
    "AI": "Arias intensity, AI (cms/s)",
}

DISAGG_DISTRIBUTION_LABEL = {
    "mag": "Magnitude ($M_{w}$)",
    "rrup": "Rupture distance $R_{rup}$",
}

CAUSAL_PARAMS_LABEL = {
    "vs30": "30m-averaged shear-wave velocity ($V_{s30}$)",
    "sf": "Scale Factor (SF)",
}


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
    nzs1170p5_hazard: pd.Series = None,
    nzta_hazard: pd.Series = None,
):
    """Plots the hazard curves for the specified data

    Parameters
    ----------
    hazard_df: pd.DataFrame
        Hazard data to plot
        format: index = IM Values, columns = [fault, ds, total, 16th, 84th]
    title: str
        Title of the plot
    im: IM
    save_file: str, optional
        Save the plot if specified
    nzs1170p5_hazard: pd.Series, optional
        The corresponding NZS1170.5 hazard data
        format: index = exceedance values, values = IM values
    nzta_hazard: pd.Series
        The corresponding NZTA hazard data
        format: index = exceedance values, values = IM values
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

    if nzs1170p5_hazard is not None:
        ax.plot(
            nzs1170p5_hazard.values,
            nzs1170p5_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="^",
            label="NZS1170.5",
        )

    if nzta_hazard is not None:
        ax.plot(
            nzta_hazard.values,
            nzta_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="s",
            markerfacecolor="none",
            label="NZTA",
        )

    _hazard_plot(im, im_values, title, save_file=save_file)


def plot_hazard_totals(
    hazard_df: pd.DataFrame,
    branch_hazard: Dict[str, pd.DataFrame],
    title: str,
    im: IM,
    save_file: str = None,
    nzs1170p5_hazard: pd.Series = None,
    nzta_hazard: pd.Series = None,
):
    """Similar to plot_hazard, except that it plots
    the ensemble total and the total for each branch

    Parameters
    ----------
    hazard_df: pd.DataFrame
        Hazard data to plot
        format: index = IM Values, columns = [fault, ds, total, 16th, 84th]
    branch_hazard: dict, optional
        If the main hazard (i.e. hazard_df) is ensemble hazard, then this
        option can be used to also plot all the branches hazard in the same
        plot. If one just wants to plot the hazard for a single branch, then
        this should parameter should be None, and the dataframe passed in using
        the hazard_df parameter
        The keys of the dictionary are expected to be the branches names, and the
        values pd.Dataframe of format: index = IM values, columns = [fault, ds, total]
    title: str
        Title of the plot
    im: IM
    save_file: str, optional
        Save the plot if specified
    nzs1170p5_hazard: pd.Series, optional
        The corresponding NZS1170.5 hazard data
        format: index = exceedance values, values = IM values
    nzta_hazard: pd.Series
        The corresponding NZTA hazard data
        format: index = exceedance values, values = IM values
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

    if nzs1170p5_hazard is not None:
        ax.plot(
            nzs1170p5_hazard.values,
            nzs1170p5_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="^",
            label="NZS1170.5",
        )

    if nzta_hazard is not None:
        ax.plot(
            nzta_hazard.values,
            nzta_hazard.index.values,
            color="black",
            linestyle="dotted",
            marker="s",
            markerfacecolor="none",
            label="NZTA",
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
    nzs1170p5_uhs: pd.DataFrame = None,
    station_name: str = None,
    legend_rp: bool = True,
    save_file: Path = None,
):
    """Plots the different uniform hazard spectra, also saves the
    plot if a save file is specified

    Parameters
    ----------
    uhs_df: pd.DataFrame
        The SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    nzs1170p5_uhs: pd.DataFrame
        The NZS1170.5 SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    station_name: str, optional
        Name of the station this plot is for, used for the plot title
    legend_rp: bool, optional
        If set then the legend labels the lines in terms of
        return period instead of exceedance rate
    save_file: Path, optional
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

    if nzs1170p5_uhs is not None:
        for col_ix, col in enumerate(nzs1170p5_uhs.columns.values):
            # Check that there are non-nan entries
            if np.count_nonzero(~np.isnan(nzs1170p5_uhs.iloc[:, col_ix].values)) > 0:
                ax.plot(
                    nzs1170p5_uhs.index.values,
                    nzs1170p5_uhs.iloc[:, col_ix].values,
                    label=f"NZS1170.5, RP={int(1 / col)}",
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
    uhs_df: pd.DataFrame,
    branch_uhs_df: pd.DataFrame,
    rp: int,
    nzs1170p5_uhs: pd.DataFrame = None,
    station_name: str = None,
    save_file: Path = None,
):
    """UHS plot for each RP with the branches and percentiles

    Parameters
    ----------
    uhs_df: pd.DataFrame
        The SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    branch_uhs_df: pd.DataFrame
        The SA IM values to plot for the different
        SA periods & branch's exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    rp: int
        Return period
    nzs1170p5_uhs: pd.DataFrame
        The NZS1170.5 SA IM values to plot for the different
        SA periods & exceedance probabilities
        format: index = SA periods, columns = exceedance probabilities
    station_name: str, optional
        Name of the station this plot is for, used for the plot title
    save_file: Path, optional
    """
    plt.figure(figsize=(12, 9))

    # Branches plots
    for ix, cur_col in enumerate(branch_uhs_df.columns):
        plt.plot(
            branch_uhs_df.index.values,
            branch_uhs_df[cur_col].values,
            linewidth=1,
            color="gray",
            label="Branches" if ix == 0 else None,
        )

    # NZS1170.5 plot
    if nzs1170p5_uhs is not None:
        for col_ix, col in enumerate(nzs1170p5_uhs.columns.values):
            if int(1 / col) == rp:
                if (
                    np.count_nonzero(~np.isnan(nzs1170p5_uhs.iloc[:, col_ix].values))
                    > 0
                ):
                    plt.plot(
                        nzs1170p5_uhs.index.values,
                        nzs1170p5_uhs.iloc[:, col_ix].values,
                        label="NZS1170.5",
                        color="black",
                    )

    # Site-specific plot
    plt.plot(
        uhs_df.index.values,
        uhs_df.get(f"{rp}_mean").values,
        label="Site-specific",
        color="blue",
    )

    # Percentile plots
    if f"{rp}_16th" in uhs_df and f"{rp}_84th" in uhs_df:
        plt.plot(
            uhs_df.index.values,
            uhs_df.get(f"{rp}_16th").values,
            color="black",
            linestyle="dashed",
            label="$16^{th}$ Percentile",
            linewidth=1,
            dashes=(5, 5),
        )
        plt.plot(
            uhs_df.index.values,
            uhs_df.get(f"{rp}_84th").values,
            color="black",
            linestyle="dashed",
            label="$84^{th}$ Percentile",
            linewidth=1,
            dashes=(5, 5),
        )

    plt.title(f"{station_name}, Return period - {rp}")
    plt.xlabel("Period (s)")
    plt.ylabel("SA (g)")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_im_distribution(
    gms_result_data: Dict,
    save_file: Path = None,
):
    """GMS IM distribution plot for each IM

    Parameters
    ----------
    gms_result_data: Dict,
    save_file: Path, optional
    """
    plots_data = utils.calculate_gms_im_distribution(gms_result_data)

    plt.figure(figsize=(16, 9))

    for im, data in plots_data.items():
        plt.plot(data.get("cdf_x"), data.get("cdf_y"), color="red", label="GCIM")
        plt.plot(
            data.get("upper_slice_cdf_x"),
            data.get("upper_slice_cdf_y"),
            color="red",
            linestyle="dashdot",
        )
        plt.plot(
            data.get("lower_slice_cdf_x"),
            data.get("lower_slice_cdf_y"),
            color="red",
            label="KS bounds, \u03B1 = 0.1",
            linestyle="dashdot",
        )
        plt.plot(
            data.get("realisations"),
            data.get("y_range"),
            color="blue",
            label="Realisations",
        )
        plt.plot(
            data.get("selected_gms"),
            data.get("y_range"),
            color="black",
            label="Selected Ground Motions",
        )

        plt.ylim(0, 1)
        plt.xlabel(
            f"Pseudo spectral acceleration, pSA({im.split('_')[-1]}) (g)"
            if im.startswith("pSA")
            else IM_DISTRIBUTION_LABEL[im]
        )
        plt.ylabel("Cumulative Probability, CDF")
        plt.title(f"{im}")
        plt.legend()

        if save_file is not None:
            plt.savefig(
                save_file / f"gms_im_distribution_{im.replace('.', 'p')}_plot.png"
            )
            plt.clf()
        else:
            plt.show()


def plot_gms_mw_rrup(
    metadata: Dict,
    bounds: Dict,
    save_file: Path = None,
):
    """GMS Magnitude and Rupture distance distribution plot

    Parameters
    ----------
    metadata: Dict
    bounds: Dict
    save_file: Path, optional
    """
    plt.figure(figsize=(16, 9))

    plt.scatter(
        metadata.get("rrup"),
        metadata.get("mag"),
        label="Selected GMs, $N_{gm}$=" + f"{len(metadata.get('rrup'))}",
        marker="s",
        edgecolors="black",
        facecolors="none",
    )
    # Boundary box plot
    plt.plot(
        [
            bounds["rrup_low"],
            bounds["rrup_high"],
            bounds["rrup_high"],
            bounds["rrup_low"],
            bounds["rrup_low"],
        ],
        [
            bounds["mw_low"],
            bounds["mw_low"],
            bounds["mw_high"],
            bounds["mw_high"],
            bounds["mw_low"],
        ],
        color="red",
        linestyle="dashed",
        label="Bounds",
        linewidth=1,
        dashes=(5, 5),
    )

    plt.xscale("log")
    plt.xlabel("Rupture distance, $R_{rup}$(km)")
    plt.ylabel("Magnitude, $M_{w}$")
    plt.title("Magnitude and Rupture distance ($M_{w}$-$R_{rup}$) distribution")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_causal_param(
    gms_result_data: Dict,
    bounds: Dict,
    metadata: str,
    save_file: Path = None,
):
    """GMS Causal Parameter's plot
     (Vs30, Scale Factor)

    Parameters
    ----------
    gms_result_data: Dict
    bounds: Dict
    metadata: str
    save_file: Path, optional
    """
    range_x, range_y = utils.calc_gms_causal_params(gms_result_data, metadata)

    plt.figure(figsize=(16, 9))
    bounds_y_range = [0, 1]

    plt.plot(
        range_x,
        range_y,
        color="black",
        label=CAUSAL_PARAMS_LABEL[metadata],
    )

    if bounds.get(metadata):
        plt.plot(
            [bounds.get(metadata).get("min"), bounds.get(metadata).get("min")],
            bounds_y_range,
            color="red",
            linestyle="dotted",
            label="Lower and upper bound limits",
        )
        plt.plot(
            [bounds.get(metadata).get("max"), bounds.get(metadata).get("max")],
            bounds_y_range,
            color="red",
            linestyle="dotted",
        )

    if metadata == "sf":
        plt.plot([1, 1], bounds_y_range, color="red", label="Reference point")

    elif metadata == "vs30":
        plt.plot(
            [bounds.get(metadata).get("vs30"), bounds.get(metadata).get("vs30")],
            bounds_y_range,
            color="red",
            label="Site-Specific $V_{s30}$",
        )

    plt.title(f"{CAUSAL_PARAMS_LABEL[metadata]} distribution")
    plt.xlabel(f"{CAUSAL_PARAMS_LABEL[metadata]}")
    plt.ylabel("Cumulative Probability, CDF")
    plt.ylim(ymin=0)
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_spectra(
    gms_result_data: Dict,
    save_file: Path = None,
):
    """GMS Pseudo acceleration response spectra plot

    Parameters
    ----------
    gms_result_data: Dict
    save_file: Path, optional
    """
    (
        gcim_df,
        realisations_df,
        selected_gms_df,
    ) = utils.calculate_gms_spectra(gms_result_data)

    plt.figure(figsize=(20, 9))

    for label, cur_gcim in gcim_df.iloc[:, 1:].iterrows():
        plt.plot(
            cur_gcim.index,
            cur_gcim.values,
            color="red",
            linestyle="solid" if label == "median" else "dashdot",
            label=GCIM_LABEL[label],
        )

    for cur_ix, cur_rel in realisations_df.iloc[:, 1:].iterrows():
        plt.plot(
            cur_rel.index.values,
            cur_rel.values,
            color="blue",
            linestyle="solid",
            label="Realisations" if cur_ix == 0 else None,
            linewidth=0.4,
        )

    for cur_ix, cur_rel in selected_gms_df.iloc[:, 1:].iterrows():
        plt.plot(
            cur_rel.index.values,
            cur_rel.values,
            color="black",
            linestyle="solid",
            label="Selected Ground Motions" if cur_ix == 0 else None,
            linewidth=0.4,
        )

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Period, T (s)")
    plt.ylabel("Spectral acceleration, SA (g)")
    plt.title("Pseudo acceleration response spectra")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_disagg_distribution(
    contribution: List,
    distribution: List,
    gms_metadata: List,
    bounds: Dict,
    metadata: str,
    save_file: Path = None,
):
    """GMS disaggregation distribution plot
    (Magnitude and Rupture distance)

    Parameters
    ----------
    contribution: List
    distribution: List
    gms_metadata: List
    bounds: Dict
    metadata: str
    save_file: Path, optional
    """
    range_x, range_y = utils.calculate_gms_disagg_distribution(gms_metadata[metadata])
    bounds_y_range = [0, 1]

    plt.figure(figsize=(16, 9))

    plt.plot(
        range_x,
        range_y,
        color="black",
        label=DISAGG_DISTRIBUTION_LABEL[metadata],
    )
    plt.plot(
        distribution, contribution, label="Disaggregation distribution", color="red"
    )

    plt.plot(
        [bounds[metadata]["min"], bounds[metadata]["min"]],
        bounds_y_range,
        color="red",
        linestyle="dotted",
        label="Lower and upper bound limits",
    )
    plt.plot(
        [bounds[metadata]["max"], bounds[metadata]["max"]],
        bounds_y_range,
        color="red",
        linestyle="dotted",
    )

    if metadata == "rrup":
        plt.xscale("log")
    plt.xlabel(DISAGG_DISTRIBUTION_LABEL[metadata])
    plt.ylabel("Cumulative Probability, CDF")
    plt.ylim(ymin=0)
    plt.title(f"{DISAGG_DISTRIBUTION_LABEL[metadata]} distribution")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_available_gm(
    metadata: Dict,
    bounds: Dict,
    num_in_bounds: int,
    save_file: Path = None,
):
    """GMS Available ground motions plot

    Parameters
    ----------
    metadata: Dict
    bounds: Dict
    num_in_bounds: int
    save_file: Path, optional
    """
    plt.figure(figsize=(16, 9))

    plt.scatter(
        metadata.get("rrup"),
        metadata.get("mag"),
        label=f"Dataset GMs (for the datapoints), N={len(metadata.get('rrup'))}\n"
        f"Causal params bounding box (for the bounding box), N={num_in_bounds}",
        marker="s",
        edgecolors="black",
        facecolors="none",
    )
    # Boundary box plot
    plt.plot(
        [
            bounds["rrup_low"],
            bounds["rrup_high"],
            bounds["rrup_high"],
            bounds["rrup_low"],
            bounds["rrup_low"],
        ],
        [
            bounds["mw_low"],
            bounds["mw_low"],
            bounds["mw_high"],
            bounds["mw_high"],
            bounds["mw_low"],
        ],
        color="red",
        linestyle="dashed",
        label="Bounds",
        linewidth=1,
        dashes=(5, 5),
    )

    plt.xscale("log")
    plt.xlabel("Rupture distance, $R_{rup}$(km)")
    plt.ylabel("Magnitude, $M_{w}$")
    plt.title("Available Ground Motions")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()
