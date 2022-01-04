from typing import Optional, List, Tuple, Dict, Union
from pathlib import Path

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt, cm as cm, colors as ml_colors

import sha_calc as sha_calc
from gmhazard_calc import gms
from gmhazard_calc.im import IM


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
    gms_result: gms.GMSResult,
    save_file: Path = None,
):
    """Plots the CDF of the GCIM and selected GMs
    for each specified IM

    Also shows the KS bounds

    Parameters
    ----------
    gms_result: gms.GMSResult,
    save_file: Path, optional
    """
    ks_bounds = gms_result.metadata_dict["ks_bounds"]

    # Add the minimum value for each IM's into the 0 index
    # to achieve the empirical distribution function with matplotlib's step plotting
    realisations = pd.DataFrame(
        data=np.concatenate(
            (
                gms_result.realisations.min(axis=0).values[None, :],
                gms_result.realisations.values,
            )
        ),
        columns=gms_result.realisations.columns.values,
    )
    selected_gms = pd.DataFrame(
        data=np.concatenate(
            (
                gms_result.selected_gms_im_df.min(axis=0).values[None, :],
                gms_result.selected_gms_im_df.values,
            )
        ),
        columns=gms_result.selected_gms_im_df.columns.values,
    )

    plt.figure(figsize=(16, 9))

    for IMi in gms_result.IMs:
        plt.plot(
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.index.values,
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.values,
            color="red",
            label="GCIM",
        )
        plt.plot(
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.index.values,
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.values + ks_bounds,
            color="red",
            label="KS bounds, \u03B1 = 0.1",
            linestyle="dashdot",
        )
        plt.plot(
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.index.values,
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.values - ks_bounds,
            color="red",
            linestyle="dashdot",
        )

        # Sort before plotting
        plt.step(
            realisations.loc[:, str(IMi)].sort_values().values,
            np.linspace(0, 1, len(realisations.loc[:, str(IMi)])),
            where="post",
            color="blue",
            label="Realisations",
        )

        plt.step(
            selected_gms.loc[:, str(IMi)].sort_values().values,
            np.linspace(0, 1, len(selected_gms.loc[:, str(IMi)])),
            where="post",
            color="black",
            label="Selected Ground Motions",
        )

        plt.xlim(xmin=0)
        plt.ylim(0, 1)
        plt.xlabel(
            f"Pseudo spectral acceleration, pSA({str(IMi).split('_')[-1]}) (g)"
            if str(IMi).startswith("pSA")
            else IM_DISTRIBUTION_LABEL[str(IMi)]
        )
        plt.ylabel("Cumulative Probability, CDF")
        plt.title(f"{IMi}")
        plt.legend()

        if save_file is not None:
            plt.savefig(
                save_file / f"gms_im_distribution_{str(IMi).replace('.', 'p')}_plot.png"
            )
            plt.clf()
        else:
            plt.show()


def plot_gms_mw_rrup(
    gms_result: gms.GMSResult,
    disagg_mean_values: pd.Series,
    cs_param_bounds: gms.CausalParamBounds = None,
    save_file: Path = None,
):
    """Magnitude - Distance (Rrup) plot of the selected GMs and the mean of the
    disaggregation distribution and selected ground motions with 16th and 84th
    percentile limits.

    Parameters
    ----------
    gms_result: gms.GMSResult
    disagg_mean_values: pd.Series
    cs_param_bounds: gms.CausalParamBounds, optional
    save_file: Path, optional
    """
    metadata = {
        **gms_result.selected_gms_metdata_df.to_dict(orient="list"),
        # mean and error bounds for selected GMs, used in Mw Rrup plot
        **gms_result.metadata_dict,
    }

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
    if cs_param_bounds is not None:
        plt.plot(
            [
                cs_param_bounds.rrup_low,
                cs_param_bounds.rrup_high,
                cs_param_bounds.rrup_high,
                cs_param_bounds.rrup_low,
                cs_param_bounds.rrup_low,
            ],
            [
                cs_param_bounds.mw_low,
                cs_param_bounds.mw_low,
                cs_param_bounds.mw_high,
                cs_param_bounds.mw_high,
                cs_param_bounds.mw_low,
            ],
            color="red",
            linestyle="dashed",
            label="Bounds",
            linewidth=1,
            dashes=(5, 5),
        )

    # Error bounds
    plt.errorbar(
        disagg_mean_values["rrup"],
        disagg_mean_values["magnitude"],
        fmt="^",
        xerr=[
            [disagg_mean_values["rrup"] - disagg_mean_values["rrup_16th"]],
            [disagg_mean_values["rrup_84th"] - disagg_mean_values["rrup"]],
        ],
        yerr=[
            [disagg_mean_values["magnitude"] - disagg_mean_values["magnitude_16th"]],
            [disagg_mean_values["magnitude_84th"] - disagg_mean_values["magnitude"]],
        ],
        capsize=15,
        color=[1, 0, 0, 0.4],
        label="Mean $M_{w}$-$R_{rup}$ of disaggregation distribution\n"
        + "$16^{th}$ to $84^{th}$ percentile $M_{w}$-$R_{rup}$ limits.",
    )

    selected_gms_agg = metadata["selected_gms_agg"]
    plt.errorbar(
        selected_gms_agg["rrup_mean"],
        selected_gms_agg["mag_mean"],
        fmt="^",
        xerr=[
            [selected_gms_agg["rrup_mean"] - selected_gms_agg["rrup_error_bounds"][0]],
            [selected_gms_agg["rrup_error_bounds"][1] - selected_gms_agg["rrup_mean"]],
        ],
        yerr=[
            [selected_gms_agg["mag_mean"] - selected_gms_agg["mag_error_bounds"][0]],
            [selected_gms_agg["mag_error_bounds"][1] - selected_gms_agg["mag_mean"]],
        ],
        capsize=15,
        color=[0, 0, 0, 0.4],
        label="Mean $M_{w}$-$R_{rup}$ of selected GMs\n"
        + "$16^{th}$ to $84^{th}$ percentile $M_{w}$-$R_{rup}$ limits.",
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
    gms_result: gms.GMSResult,
    metadata_key: str,
    cs_param_bounds: gms.CausalParamBounds = None,
    save_file: Path = None,
):
    """CDF plot of the selected GMs for Vs30 and
    Scaling Factor (separate plots)

    Also shows causal bounding parameters if specified

    Parameters
    ----------
    gms_result: gms.GMSResult
    metadata_key: str
        Currently only support vs30 and sf
    cs_param_bounds: gms.CausalParamBounds, optional
    save_file: Path, optional
    """
    selected_gms_metadata = gms_result.selected_gms_metdata_df.to_dict(orient="list")
    bounds = _get_causal_params_bounds(cs_param_bounds)
    # To achieve Empirical distribution function with matplotlib's step plotting
    copied_metadata = selected_gms_metadata[metadata_key][:]
    copied_metadata.append(min(copied_metadata))
    copied_metadata.sort()

    plt.figure(figsize=(16, 9))
    bounds_y_range = [0, 1]

    plt.step(
        copied_metadata,
        np.linspace(0, 1, len(copied_metadata)),
        where="post",
        color="black",
        label=CAUSAL_PARAMS_LABEL[metadata_key],
    )

    if bounds is not None and bounds.get(metadata_key) is not None:
        plt.plot(
            [bounds.get(metadata_key).get("min"), bounds.get(metadata_key).get("min")],
            bounds_y_range,
            color="red",
            linestyle="dotted",
            label="Lower and upper bound limits",
        )
        plt.plot(
            [bounds.get(metadata_key).get("max"), bounds.get(metadata_key).get("max")],
            bounds_y_range,
            color="red",
            linestyle="dotted",
        )

    if metadata_key == "sf":
        plt.plot([1, 1], bounds_y_range, color="red", label="Reference point")

    elif metadata_key == "vs30":
        plt.plot(
            [
                bounds.get(metadata_key).get("vs30"),
                bounds.get(metadata_key).get("vs30"),
            ],
            bounds_y_range,
            color="red",
            label="Site-Specific $V_{s30}$",
        )

    plt.title(f"{CAUSAL_PARAMS_LABEL[metadata_key]} distribution")
    plt.xlabel(f"{CAUSAL_PARAMS_LABEL[metadata_key]}")
    plt.ylabel("Cumulative Probability, CDF")
    plt.ylim(ymin=0)
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_spectra(
    gms_result: gms.GMSResult,
    save_file: Path = None,
):
    """Plot of the pSA values of the realisations and
     selected ground motions and the median, 16th,
     and 84th percentile of the GCIM

    Parameters
    ----------
    gms_result: gms.GMSResult
    save_file: Path, optional
    """
    (
        gcim_df,
        realisations_df,
        selected_gms_df,
    ) = _prepare_gms_spectra(gms_result)

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
    contribution_df: pd.DataFrame,
    gms_result: gms.GMSResult,
    metadata_key: str,
    cs_param_bounds: gms.CausalParamBounds = None,
    save_file: Path = None,
):
    """CDF plots for the selected GMs and
    all ruptures (disaggregation) for Magnitude
    and Distance (Rrup)

    Also shows causal bounding parameters if specified

    Parameters
    ----------
    contribution_df: pd.DataFrame
        Contribution of the ruptures corresponding to the distribution
        index = list of either Mw or Rrup values
        values = contributions
    gms_result: gms.GMSResult
    metadata_key: str
    cs_param_bounds: gms.CausalParamBounds, optional
    save_file: Path, optional
    """
    bounds = _get_causal_params_bounds(cs_param_bounds)
    bounds_y_range = [0, 1]
    # To achieve Empirical distribution function with matplotlib's step plotting
    metadata_values = list(
        gms_result.selected_gms_metdata_df.loc[:, metadata_key].values
    )
    metadata_values.append(min(metadata_values))
    metadata_values.sort()

    contribution_df = contribution_df.sort_index(ascending=True)

    plt.figure(figsize=(16, 9))

    plt.step(
        metadata_values,
        np.linspace(0, 1, len(metadata_values)),
        where="post",
        color="black",
        label=DISAGG_DISTRIBUTION_LABEL[metadata_key],
    )
    plt.plot(
        contribution_df.index.values,
        np.cumsum(contribution_df.values),
        label="Disaggregation distribution",
        color="red",
    )

    if bounds is not None:
        plt.plot(
            [bounds[metadata_key]["min"], bounds[metadata_key]["min"]],
            bounds_y_range,
            color="red",
            linestyle="dotted",
            label="Lower and upper bound limits",
        )
        plt.plot(
            [bounds[metadata_key]["max"], bounds[metadata_key]["max"]],
            bounds_y_range,
            color="red",
            linestyle="dotted",
        )

    if metadata_key == "rrup":
        plt.xscale("log")
    plt.xlabel(DISAGG_DISTRIBUTION_LABEL[metadata_key])
    plt.ylabel("Cumulative Probability, CDF")
    plt.ylim(ymin=0)
    plt.title(f"{DISAGG_DISTRIBUTION_LABEL[metadata_key]} distribution")
    plt.legend()

    if save_file is not None:
        plt.savefig(save_file)
        plt.close()
    else:
        plt.show()


def plot_gms_available_gm(
    gms_result: gms.GMSResult,
    cs_param_bounds: gms.CausalParamBounds,
    save_file: Path = None,
):
    """Distance (Rrup) - Magnitude plot of the GMs in the GM-dataset

    Also shows a bounding box to visualise the causal bound parameters

    Parameters
    ----------
    gms_result: gms.GMSResult
    cs_param_bounds: gms.CausalParamBounds
    save_file: Path, optional
    """
    n_gms_in_bounds = gms_result.gm_dataset.get_n_gms_in_bounds(
        gms_result.gm_dataset.get_metadata_df(gms_result.site_info),
        cs_param_bounds,
    )

    plt.figure(figsize=(16, 9))

    plt.scatter(
        list(
            gms_result.gm_dataset.get_metadata_df(gms_result.site_info)
            .loc[:, "rrup"]
            .values
        ),
        list(
            gms_result.gm_dataset.get_metadata_df(gms_result.site_info)
            .loc[:, "mag"]
            .values
        ),
        label=f"Dataset GMs (for the datapoints), "
        f"N={gms_result.gm_dataset.get_metadata_df(gms_result.site_info).index.size}\n"
        f"Causal params bounding box (for the bounding box), N={n_gms_in_bounds}",
        marker="s",
        edgecolors="black",
        facecolors="none",
    )
    # Boundary box plot
    plt.plot(
        [
            cs_param_bounds.rrup_low,
            cs_param_bounds.rrup_high,
            cs_param_bounds.rrup_high,
            cs_param_bounds.rrup_low,
            cs_param_bounds.rrup_low,
        ],
        [
            cs_param_bounds.mw_low,
            cs_param_bounds.mw_low,
            cs_param_bounds.mw_high,
            cs_param_bounds.mw_high,
            cs_param_bounds.mw_low,
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


def _prepare_gms_spectra(
    gms_result: gms.GMSResult,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create data for Spectra plot from the given GMS data

    Parameters
    ----------
    gms_result: gms.GMSResult

    Returns
    -------
    gcim_df: pd.DataFrame
        Includes 84th, median and 16th percentiles along with IMs
    realisations_df: pd.DataFrame
    selected_gms_df: pd.DataFrame,
    """
    cdf_x = {
        str(IMi): list(
            gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.index.values.astype(float)
        )
        for IMi in gms_result.IMs
    }
    cdf_y = {
        str(IMi): list(gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.values.astype(float))
        for IMi in gms_result.IMs
    }
    realisations = {
        str(key): value
        for key, value in gms_result.realisations.to_dict(orient="list").items()
    }
    selected_gms = {
        str(key): value
        for key, value in gms_result.selected_gms_im_df.to_dict(orient="list").items()
    }
    im_j = gms_result.im_j
    IM_j = str(gms_result.IM_j)

    # for CDF_X
    cdf_x_df = pd.DataFrame(cdf_x)
    cdf_x_df.columns = [
        float(cur_col.split("_")[-1]) if cur_col.startswith("pSA") else 0.0
        for cur_col in cdf_x_df.columns
    ]
    cdf_x_df = cdf_x_df.T.sort_index().T

    # For CDF_Y
    cdf_y_df = pd.DataFrame(cdf_y)
    cdf_y_df.columns = [
        float(cur_col.split("_")[-1]) if cur_col.startswith("pSA") else 0.0
        for cur_col in cdf_y_df.columns
    ]
    cdf_y_df = cdf_y_df.T.sort_index().T

    upper_bound, median, lower_bound = sha_calc.query_non_parametric_multi_cdf_invs(
        [0.84, 0.5, 0.16], cdf_x_df.T.values, cdf_y_df.T.values
    )

    gcim_df = pd.DataFrame(
        index=cdf_x_df.columns,
        columns=np.asarray(["84th", "median", "16th"]),
        data=np.asarray([upper_bound, median, lower_bound]).T,
    ).T

    if IM_j.startswith("pSA"):
        gcim_df[float(IM_j.split("_")[-1])] = im_j
        gcim_df = gcim_df.T.sort_index().T

    # Realisations
    realisations_df = pd.DataFrame(realisations)
    realisations_df.columns = [
        float(cur_col.split("_")[-1]) if cur_col.startswith("pSA") else 0.0
        for cur_col in realisations_df.columns
    ]
    if IM_j.startswith("pSA"):
        realisations_df[float(IM_j.split("_")[-1])] = im_j

    realisations_df = realisations_df.T.sort_index().T

    # Selected Ground Motions
    selected_gms_df = pd.DataFrame(selected_gms)
    selected_gms_df.columns = [
        float(cur_col.split("_")[-1]) if cur_col.startswith("pSA") else 0.0
        for cur_col in selected_gms_df.columns
    ]
    selected_gms_df = selected_gms_df.T.sort_index().T

    return (
        gcim_df,
        realisations_df,
        selected_gms_df,
    )


def _get_causal_params_bounds(cs_param_bounds: gms.CausalParamBounds):
    return {
        "mag": {
            "min": cs_param_bounds.mw_low,
            "max": cs_param_bounds.mw_high,
        },
        "rrup": {
            "min": cs_param_bounds.rrup_low,
            "max": cs_param_bounds.rrup_high,
        },
        "vs30": {
            "min": cs_param_bounds.vs30_low,
            "max": cs_param_bounds.vs30_high,
            "vs30": cs_param_bounds.site_info.db_vs30,
        },
    }
