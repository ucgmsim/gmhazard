import pathlib
import time
from typing import List, Dict, Union

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

import constants as const
from empirical.util import empirical_factory
from empirical.util.classdef import Site, Fault, TectType


def get_sites(vs30_values: np.ndarray, rrup_value: float):
    """Creates a dictionary
    pair of a different Vs30 and Sites

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    rrup_value: float
        Rupture distance
    """
    return {
        vs30: Site(
            rrup=rrup_value,
            rjb=rrup_value,
            rx=rrup_value,
            ry=rrup_value,
            vs30=vs30,
            **const.CONST_SITE_PARAMS,
        )
        for vs30 in vs30_values
    }


def get_faults(vs30_values: np.ndarray, mag_dict: Dict):
    """Creates a dictionary
     based on a different Vs30, Magnitude and Faults

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    """
    faults = {}
    for tect_type in const.MODELS_DICT.keys():
        faults[tect_type] = {}
        for vs30 in vs30_values:
            faults[tect_type][vs30] = {}
            for mag in mag_dict[tect_type]:
                faults[tect_type][vs30][mag] = Fault(
                    Mw=mag,
                    tect_type=TectType[tect_type],
                    **const.CONST_FAULT_PARAMS[tect_type],
                )

    return faults


def get_computed_gmms(
    vs30_values: np.ndarray,
    sites: Dict,
    mag_dict: Dict,
    faults: Dict,
    period_values: np.ndarray,
    for_sigma: bool,
):
    """Get computed GMMs

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    sites: Dict
        nested dictionary of Sites with a different Vs30
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    faults: Dict
        nested dictionary of Faults with a different Vs30 and Magnitude
    period_values: np.ndarray
        list of Periods
    for_sigma: bool
        to be used for pSA Sigma vs T
        if True
        else pSA vs T
    """
    results_dict = {}
    for tect_type, im_models in const.MODELS_DICT.items():
        results_dict[tect_type] = {}
        results_dict[tect_type][const.PSA_IM_NAME] = {}
        for vs30 in vs30_values:
            results_dict[tect_type][const.PSA_IM_NAME][vs30] = {}
            for mag in mag_dict[tect_type]:
                results_dict[tect_type][const.PSA_IM_NAME][vs30][mag] = {}
                for model in im_models[const.PSA_IM_NAME]:
                    results = empirical_factory.compute_gmm(
                        faults[tect_type][vs30][mag],
                        sites[vs30],
                        empirical_factory.GMM[model],
                        const.PSA_IM_NAME,
                        period_values,
                    )
                    if isinstance(results, list):
                        results_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model] = [
                            result[1][0] if for_sigma else result[0]
                            for result in results
                        ]
                    else:
                        results_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model] = [
                            results[1][0] if for_sigma else results[0]
                        ]

    return results_dict


def plot_psha_psa_sigma(
    vs30_values: np.ndarray,
    mag_dict: Dict,
    period_values: np.ndarray,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
):
    """Plots for pSA sigma versus T

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    period_values: np.ndarray
        list of Periods
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    plot_directory: pathlib.PosixPath
        absolute path for a directory to store plot image
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        x_position = 0
        fig, ax = plt.subplots(
            len(vs30_values), len(mag_dict[tect_type]), figsize=(18, 8), dpi=300
        )
        for vs30 in vs30_values:
            y_position = 0
            for mag in mag_dict[tect_type]:
                for model in im_models[const.PSA_IM_NAME]:
                    ax[x_position, y_position].plot(
                        period_values,
                        result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model],
                        label=model,
                        color=const.DEFAULT_LABEL_COLOR[model],
                        linestyle="dashed" if model.endswith("NZ") else "solid",
                    )

                ax[x_position, y_position].set_title(
                    f"Sigma versus T - Mw{mag}, Vs30-{vs30}"
                )
                ax[x_position, y_position].legend(im_models[const.PSA_IM_NAME])
                ax[x_position, y_position].xaxis.set_label_text("Period [sec]")
                ax[x_position, y_position].yaxis.set_label_text("Sigma [Ln Units]")
                ax[x_position, y_position].set_xscale("log")
                ax[x_position, y_position].margins(x=0)
                ax[x_position, y_position].set_ylim([0.0001, 10])
                ax[x_position, y_position].xaxis.grid(
                    True, which="both", linestyle="dotted"
                )
                ax[x_position, y_position].yaxis.grid(
                    True, which="both", linestyle="dotted"
                )

                y_position += 1
            x_position += 1

        fig.tight_layout()
        plt.savefig(f"{plot_directory}/{tect_type}_pSA_sigma_versus_T.png")
        plt.close()


def plot_psha_psa(
    vs30_values: np.ndarray,
    mag_dict: Dict,
    period_values: np.ndarray,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
):
    """Plots for pSA versus T

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    period_values: np.ndarray
        list of Periods
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    plot_directory: pathlib.PosixPath
        absolute path for a directory to store plot image
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        x_position = 0
        fig, ax = plt.subplots(
            len(vs30_values), len(mag_dict[tect_type]), figsize=(18, 12), dpi=300
        )

        for vs30 in vs30_values:
            y_position = 0
            for mag in mag_dict[tect_type]:
                for model in im_models[const.PSA_IM_NAME]:
                    ax[x_position, y_position].plot(
                        period_values,
                        result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model],
                        label=model if x_position == 0 and y_position == 0 else None,
                        color=const.DEFAULT_LABEL_COLOR[model],
                        linestyle="dashed" if model.endswith("NZ") else "solid",
                    )

                if len(im_models) > 1:
                    # Create DatFrame to make life easier
                    df = np.log(
                        pd.DataFrame(
                            list(
                                result_dict[tect_type][const.PSA_IM_NAME][vs30][
                                    mag
                                ].values()
                            ),
                            columns=period_values,
                            index=list(
                                result_dict[tect_type][const.PSA_IM_NAME][vs30][
                                    mag
                                ].keys()
                            ),
                        )
                    )
                    average_medians = df.sum(axis=0) / len(
                        list(
                            result_dict[tect_type][const.PSA_IM_NAME][vs30][mag].keys()
                        )
                    )
                    sigma_intermodel = np.sqrt(
                        np.square(df - average_medians).sum(axis=0)
                        / len(
                            list(
                                result_dict[tect_type][const.PSA_IM_NAME][vs30][
                                    mag
                                ].keys()
                            )
                        )
                    )
                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(average_medians),
                        color="black",
                        label="average medians"
                        if x_position == 0 and y_position == 0
                        else None,
                    )
                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(np.add(average_medians, sigma_intermodel)),
                        color="black",
                        linestyle="--",
                        label="average medians + sigma intermodel"
                        if x_position == 0 and y_position == 0
                        else None,
                    )
                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(np.subtract(average_medians, sigma_intermodel)),
                        color="black",
                        linestyle="--",
                        label="average medians - sigma intermodel"
                        if x_position == 0 and y_position == 0
                        else None,
                    )

                ax[x_position, y_position].set_title(
                    f"SA versus T - Mw{mag}, Vs30-{vs30}"
                )
                ax[x_position, y_position].legend(im_models[const.PSA_IM_NAME])
                ax[x_position, y_position].xaxis.set_label_text("Period [sec]")
                ax[x_position, y_position].yaxis.set_label_text("SA [g]")
                ax[x_position, y_position].set_xscale("log")
                ax[x_position, y_position].set_yscale("log")
                ax[x_position, y_position].margins(x=0)
                ax[x_position, y_position].set_ylim([0.0001, 10])
                ax[x_position, y_position].xaxis.grid(
                    True, which="both", linestyle="dotted"
                )
                ax[x_position, y_position].yaxis.grid(
                    True, which="both", linestyle="dotted"
                )
                y_position += 1
            x_position += 1

        fig.tight_layout()
        plt.savefig(f"{plot_directory}/{tect_type}_pSA_versus_T.png")
        plt.close()


def plot_psha_median_psa(
    vs30_values: np.ndarray,
    mag_dict: Dict,
    period_values: np.ndarray,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
):
    """Plots for pSA versus T

    Parameters
    ----------
    vs30_values: np.ndarray
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    period_values: np.ndarray
        list of Periods
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    plot_directory: pathlib.PosixPath
        absolute path for a directory to store plot image
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        x_position = 0
        fig, ax = plt.subplots(
            len(vs30_values), len(mag_dict[tect_type]), figsize=(18, 18), dpi=300
        )
        for vs30 in vs30_values:
            y_position = 0
            for mag in mag_dict[tect_type]:
                # Create DatFrame to make life easier
                df = np.log(
                    pd.DataFrame(
                        list(result_dict[tect_type]["pSA"][vs30][mag].values()),
                        columns=period_values,
                        index=list(result_dict[tect_type]["pSA"][vs30][mag].keys()),
                    )
                )

                if len(im_models) > 1:
                    average_medians = df.sum(axis=0) / len(
                        list(result_dict[tect_type]["pSA"][vs30][mag].keys())
                    )
                    sigma_intermodel = np.sqrt(
                        np.square(df - average_medians).sum(axis=0)
                        / len(list(result_dict[tect_type]["pSA"][vs30][mag].keys()))
                    )

                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(average_medians),
                        c="k",
                        label="average medians",
                    )
                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(np.add(average_medians, sigma_intermodel)),
                        c="k",
                        linestyle="--",
                        label="average medians + sigma intermodel",
                    )
                    ax[x_position, y_position].plot(
                        period_values,
                        np.exp(np.subtract(average_medians, sigma_intermodel)),
                        c="k",
                        linestyle="--",
                        label="average medians - sigma intermodel",
                    )

                ax[x_position, y_position].set_title(f"Median - Mw{mag}, Vs30-{vs30}")
                ax[x_position, y_position].legend()
                ax[x_position, y_position].xaxis.set_label_text("Period [sec]")
                ax[x_position, y_position].yaxis.set_label_text("SA [g]")
                ax[x_position, y_position].set_xscale("log")
                ax[x_position, y_position].set_yscale("log")
                ax[x_position, y_position].margins(x=0)
                ax[x_position, y_position].set_ylim([0.0001, 10])
                ax[x_position, y_position].xaxis.grid(
                    True, which="both", linestyle="dotted"
                )
                ax[x_position, y_position].yaxis.grid(
                    True, which="both", linestyle="dotted"
                )

                y_position += 1
            x_position += 1

        fig.tight_layout()
        plt.savefig(f"{plot_directory}/{tect_type}_pSA_median_versus_T.png")
        plt.close()


def plot_psa_mag(
    vs30_values: np.ndarray,
    rrup_values: np.ndarray,
    mag_list: np.ndarray,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
    period,
    tect_type,
):
    """Plots for pSA versus Magnitude
    """
    fig, ax = plt.subplots(
        len(vs30_values), len(rrup_values), figsize=(18, 12), dpi=300
    )
    x_position = 0
    for vs30 in vs30_values:
        y_position = 0
        for rrup in rrup_values:
            psa_results = pd.DataFrame.from_dict(result_dict[vs30][rrup])
            for model, row in psa_results.iterrows():
                ax[x_position, y_position].plot(
                    mag_list,
                    row.values,
                    label=model,
                    color=const.DEFAULT_LABEL_COLOR[model],
                    linestyle="dashed" if model.endswith("NZ") else "solid",
                )

            ax[x_position, y_position].set_title(
                f"SA versus Magnitude - Rrup:{rrup}, Vs30:{vs30}"
            )
            ax[x_position, y_position].legend(psa_results.index.values)
            ax[x_position, y_position].xaxis.set_label_text("Magnitude")
            ax[x_position, y_position].yaxis.set_label_text("SA [g]")
            # ax[x_position, y_position].set_xscale("log")
            ax[x_position, y_position].set_yscale("log")
            ax[x_position, y_position].margins(x=0)
            ax[x_position, y_position].set_ylim([0.0001, 10])
            ax[x_position, y_position].xaxis.grid(
                True, which="both", linestyle="dotted"
            )
            ax[x_position, y_position].yaxis.grid(
                True, which="both", linestyle="dotted"
            )
            y_position += 1
        x_position += 1

    fig.tight_layout()
    plt.savefig(f"{plot_directory}/{tect_type}_{period}.png")
    plt.close()


def plot_psa_vs30(
    vs30_values: np.ndarray,
    rrup_values: np.ndarray,
    mag_list: np.ndarray,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
    tect_type,
    period=None,
):
    """Plots for SA versus Vs30
    """
    fig, ax = plt.subplots(len(mag_list), len(rrup_values), figsize=(18, 12), dpi=300)
    x_position = 0
    for mag in mag_list:
        y_position = 0
        for rrup in rrup_values:
            psa_results = pd.DataFrame.from_dict(result_dict[mag][rrup])
            for model, row in psa_results.iterrows():
                ax[x_position, y_position].plot(
                    vs30_values,
                    row.values,
                    label=model,
                    color=const.DEFAULT_LABEL_COLOR[model],
                    linestyle="dashed" if model.endswith("NZ") else "solid",
                )
            title = f"SA({period})" if period else "PGA"
            ax[x_position, y_position].set_title(
                f"{title} versus Vs30 - Rrup:{rrup}, Magnitude:{mag}"
            )
            ax[x_position, y_position].legend(psa_results.index.values)
            ax[x_position, y_position].xaxis.set_label_text("Vs30")
            ax[x_position, y_position].yaxis.set_label_text("SA [g]")
            ax[x_position, y_position].set_xscale("log")
            ax[x_position, y_position].set_yscale("log")
            ax[x_position, y_position].margins(x=0)
            ax[x_position, y_position].set_ylim([0.0001, 10])
            ax[x_position, y_position].xaxis.grid(
                True, which="both", linestyle="dotted"
            )
            ax[x_position, y_position].yaxis.grid(
                True, which="both", linestyle="dotted"
            )

            y_position += 1
        x_position += 1

    fig.tight_layout()
    plt.savefig(f"{plot_directory}/{tect_type}_{period if period else None}.png")
    plt.close()


def psa_sigma_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    psa_periods: np.ndarray,
    rrup_values: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA Sigma versus T

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    vs30_values: List
        list of Vs30s
    psa_periods: np.ndarray
        list of Periods
    rrup_values: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """
    faults = get_faults(vs30_values, mag_dict)
    for rrup in rrup_values:
        sites = get_sites(vs30_values, rrup)

        result_dict = get_computed_gmms(
            vs30_values, sites, mag_dict, faults, psa_periods, True
        )

        root_path = (
            pathlib.Path(__file__).resolve().parent.parent
            if save_path is None
            else save_path
        )
        plot_directory = root_path / "psa_sigma_period" / f"{rrup}"
        plot_directory.mkdir(exist_ok=True, parents=True)

        plot_psha_psa_sigma(
            vs30_values, mag_dict, psa_periods, result_dict, plot_directory
        )


def psa_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    psa_periods: np.ndarray,
    rrup_values: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA versus T

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    vs30_values: List
        list of Vs30s
    psa_periods: np.ndarray
        list of Periods
    rrup_values: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """
    faults = get_faults(vs30_values, mag_dict)
    for rrup in rrup_values:
        sites = get_sites(vs30_values, rrup)

        result_dict = get_computed_gmms(
            vs30_values, sites, mag_dict, faults, psa_periods, False
        )

        root_path = (
            pathlib.Path(__file__).resolve().parent.parent
            if save_path is None
            else save_path
        )

        plot_directory = root_path / "psa_period" / f"{rrup}"
        plot_directory.mkdir(exist_ok=True, parents=True)

        plot_psha_psa(vs30_values, mag_dict, psa_periods, result_dict, plot_directory)


def psa_median_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    psa_periods: np.ndarray,
    rrup_value: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA medians, std versus T

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    vs30_values: List
        list of Vs30s
    psa_periods: np.ndarray
        list of Periods
    rrup_value: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """
    faults = get_faults(vs30_values, mag_dict)
    for rrup in rrup_value:
        sites = get_sites(vs30_values, rrup)

        result_dict = get_computed_gmms(
            vs30_values, sites, mag_dict, faults, psa_periods, False
        )

        root_path = (
            pathlib.Path(__file__).resolve().parent.parent
            if save_path is None
            else save_path
        )
        plot_directory = root_path / "psa_median_period" / f"{rrup}"
        plot_directory.mkdir(exist_ok=True, parents=True)

        plot_psha_median_psa(
            vs30_values, mag_dict, psa_periods, result_dict, plot_directory
        )


def psa_mag_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    psa_periods: np.ndarray,
    rrup_values: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA versus Magnitude

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    vs30_values: List
        list of Vs30s
    psa_periods: np.ndarray
        list of Periods
    rrup_values: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """

    root_path = (
        pathlib.Path(__file__).resolve().parent.parent
        if save_path is None
        else save_path
    )
    plot_directory = root_path / "psa_mag"
    plot_directory.mkdir(exist_ok=True, parents=True)
    for tect_type, mag_list in mag_dict.items():
        for period in psa_periods:
            results = {}
            for vs30 in vs30_values:
                results[vs30] = {}
                for rrup in rrup_values:
                    results[vs30][rrup] = {}
                    site = Site(
                        rrup=rrup,
                        rjb=rrup,
                        rx=rrup,
                        ry=rrup,
                        vs30=vs30,
                        **const.CONST_SITE_PARAMS,
                    )
                    for mag in mag_list:
                        results[vs30][rrup][mag] = {}
                        fault = Fault(
                            Mw=mag,
                            tect_type=TectType[tect_type],
                            **const.CONST_FAULT_PARAMS[tect_type],
                        )

                        for model in const.MODELS_DICT[tect_type][const.PSA_IM_NAME]:
                            gmm_result = empirical_factory.compute_gmm(
                                fault,
                                site,
                                empirical_factory.GMM[model],
                                const.PSA_IM_NAME,
                                [period],
                            )
                            results[vs30][rrup][mag][model] = (
                                gmm_result[0][0]
                                if isinstance(gmm_result, list)
                                else gmm_result[0]
                            )
        plot_psa_mag(
            vs30_values,
            rrup_values,
            mag_list,
            results,
            plot_directory,
            period,
            tect_type,
        )


def psa_vs30_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    psa_periods: np.ndarray,
    rrup_values: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA versus Magnitude

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    psa_periods: np.ndarray
        list of Periods
    rrup_values: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """

    root_path = (
        pathlib.Path(__file__).resolve().parent.parent
        if save_path is None
        else save_path
    )
    plot_directory = root_path / "psa_vs30"
    plot_directory.mkdir(exist_ok=True, parents=True)
    for tect_type, mag_list in mag_dict.items():
        for period in psa_periods:
            results = {}
            for mag in mag_list:
                results[mag] = {}
                for rrup in rrup_values:
                    results[mag][rrup] = {}
                    fault = Fault(
                        Mw=mag,
                        tect_type=TectType[tect_type],
                        **const.CONST_FAULT_PARAMS[tect_type],
                    )
                    for vs30 in vs30_values:
                        results[mag][rrup][vs30] = {}
                        site = Site(
                            rrup=rrup,
                            rjb=rrup,
                            rx=rrup,
                            ry=rrup,
                            vs30=vs30,
                            **const.CONST_SITE_PARAMS,
                        )
                        for model in const.MODELS_DICT[tect_type][const.PSA_IM_NAME]:
                            gmm_result = empirical_factory.compute_gmm(
                                fault,
                                site,
                                empirical_factory.GMM[model],
                                const.PSA_IM_NAME,
                                [period],
                            )
                            results[mag][rrup][vs30][model] = (
                                gmm_result[0][0]
                                if isinstance(gmm_result, list)
                                else gmm_result[0]
                            )
        plot_psa_vs30(
            vs30_values,
            rrup_values,
            mag_list,
            results,
            plot_directory,
            tect_type,
            period,
        )


def pga_vs30_plot(
    mag_dict: Dict,
    vs30_values: np.ndarray,
    rrup_values: List[Union[float, int]],
    save_path: pathlib.PosixPath = None,
):
    """Plot function for a pSA versus Magnitude

    Parameters
    ----------
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    rrup_values: List[Union[float, int]]
        Rupture distance in km
    save_path: pathlib.PosixPath
        Directory to save plots
    """

    root_path = (
        pathlib.Path(__file__).resolve().parent.parent
        if save_path is None
        else save_path
    )
    plot_directory = root_path / "pga_vs30"
    plot_directory.mkdir(exist_ok=True, parents=True)
    for tect_type, mag_list in mag_dict.items():
        results = {}
        for mag in mag_list:
            results[mag] = {}
            for rrup in rrup_values:
                results[mag][rrup] = {}
                fault = Fault(
                    Mw=mag,
                    tect_type=TectType[tect_type],
                    **const.CONST_FAULT_PARAMS[tect_type],
                )
                for vs30 in vs30_values:
                    results[mag][rrup][vs30] = {}
                    site = Site(
                        rrup=rrup,
                        rjb=rrup,
                        rx=rrup,
                        ry=rrup,
                        vs30=vs30,
                        **const.CONST_SITE_PARAMS,
                    )
                    for model in const.MODELS_DICT[tect_type][const.PSA_IM_NAME]:
                        gmm_result = empirical_factory.compute_gmm(
                            fault,
                            site,
                            empirical_factory.GMM[model],
                            const.PGA_IM_NAME,
                        )
                        results[mag][rrup][vs30][model] = (
                            gmm_result[0][0]
                            if isinstance(gmm_result, list)
                            else gmm_result[0]
                        )
        plot_psa_vs30(
            vs30_values, rrup_values, mag_list, results, plot_directory, tect_type,
        )


if __name__ == "__main__":
    """Update those inputs to get different outputs"""
    mag_dict = {
        "ACTIVE_SHALLOW": [6, 7, 8],
        "SUBDUCTION_SLAB": [6, 7, 8],
        "SUBDUCTION_INTERFACE": [7, 8, 9],
    }
    vs30_list = np.array([200, 300, 400, 760])
    period_list = np.array([0.01, 0.1, 1.0, 2.0, 3.0, 5.0])
    rrup = np.array([75, 200])
    # Update the path to the directory to save plots
    save_path = pathlib.Path(
        "/home/tom/Documents/QuakeCoRE/resource/verification_plots/special"
    )
    start = time.time()
    psa_sigma_plot(mag_dict, vs30_list, period_list, rrup, save_path)
    psa_plot(mag_dict, vs30_list, period_list, rrup, save_path)
    psa_median_plot(mag_dict, vs30_list, period_list, rrup, save_path)

    # Special requests
    psa_mag_plot(mag_dict, vs30_list, period_list, rrup, save_path)
    vs30_list = np.arange(100, 2001, 100)
    psa_vs30_plot(mag_dict, vs30_list, period_list, rrup, save_path)
    pga_vs30_plot(mag_dict, vs30_list, rrup, save_path)

    print(f"Finished in {(time.time() - start):.2f}s")
