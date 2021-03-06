import pathlib
from typing import List, Dict, Union

import numpy as np
import matplotlib.pyplot as plt

import constants as const
from empirical.util import empirical_factory
from empirical.util.classdef import Site, Fault, TectType


def init_setup(mag_dict: Dict, vs30_values: List):
    """Create nested dictionaries for fault and result
    based on a different vs30, mag and model

    Parameters
    ----------
    mag_dict: Dict
        List of Magnitudes
    vs30_values: List
        List of Vs30s
    """
    faults = {}
    result_dict = {}
    for tect_type, im_models in const.MODELS_DICT.items():
        faults[tect_type] = {}
        result_dict[tect_type] = {const.PSA_IM_NAME: {}}
        for vs30 in vs30_values:
            faults[tect_type][vs30] = {}
            result_dict[tect_type][const.PSA_IM_NAME][vs30] = {}
            for mag in mag_dict[tect_type]:
                faults[tect_type][vs30][mag] = []
                result_dict[tect_type][const.PSA_IM_NAME][vs30][mag] = {}
                for model in im_models[const.PSA_IM_NAME]:
                    result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model] = []

    return faults, result_dict


def get_sites(vs30_values: List, rrup_value: float):
    """Creates a dictionary
    pair of a different Vs30 and Sites

    Parameters
    ----------
    vs30_values: List
        list of Vs30s
    rrup_value: float
        Rupture distance
    """
    sites = {vs30: [] for vs30 in vs30_values}

    for vs30 in vs30_values:
        sites[vs30].append(
            Site(
                rrup=rrup_value,
                rjb=rrup_value,
                rx=rrup_value,
                ry=rrup_value,
                vs30=vs30,
                **const.CONST_SITE_PARAMS,
            )
        )

    return sites


def get_faults(vs30_values: List, mag_dict: Dict, faults: Dict):
    """Creates a dictionary
     based on a different Vs30, Magnitude and Faults

    Parameters
    ----------
    vs30_values: List
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    faults: Dict
        nested dictionary
    """
    for tect_type in const.MODELS_DICT.keys():
        for vs30 in vs30_values:
            for mag in mag_dict[tect_type]:
                faults[tect_type][vs30][mag].append(
                    Fault(
                        Mw=mag,
                        tect_type=TectType[tect_type],
                        **const.CONST_FAULT_PARAMS[tect_type],
                    )
                )

    return faults


def get_computed_gmms(
    vs30_values: List,
    sites: Dict,
    mag_dict: Dict,
    faults: Dict,
    result_dict: Dict,
    period_values: List,
    for_sigma: bool,
):
    """Get computed GMMs

    Parameters
    ----------
    vs30_values: List
        list of Vs30s
    sites: Dict
        nested dictionary of Sites with a different Vs30
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    faults: Dict
        nested dictionary of Faults with a different Vs30 and Magnitude
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    period_values: List
        list of Periods
    for_sigma: bool
        to be used for pSA Sigma vs T
        if True
        else pSA vs T
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        for vs30 in vs30_values:
            for site in sites[vs30]:
                for mag in mag_dict[tect_type]:
                    for fault in faults[tect_type][vs30][mag]:
                        for model in im_models[const.PSA_IM_NAME]:
                            results = empirical_factory.compute_gmm(
                                fault,
                                site,
                                empirical_factory.GMM[model],
                                const.PSA_IM_NAME,
                                period_values,
                            )

                            result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][
                                model
                            ] = [
                                result[1][0] if for_sigma else result[0]
                                for result in results
                            ]

    return result_dict


def plot_psha_psa_sigma(
    vs30_values: List,
    mag_dict: Dict,
    period_values: List,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
):
    """Plots for pSA sigma versus T

    Parameters
    ----------
    vs30_values: List
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    period_values: List
        list of Periods
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    plot_directory: pathlib.PosixPath
        absolute path for a directory to store plot image
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        x_position = 0
        fig, ax = plt.subplots(
            len(vs30_values), len(mag_dict[tect_type]), figsize=(18, 13.5), dpi=300
        )
        for vs30 in vs30_values:
            y_position = 0
            for mag in mag_dict[tect_type]:
                color_index = 0
                for model in im_models[const.PSA_IM_NAME]:
                    # To match the color with global version
                    if model.endswith("NZ"):
                        color_index -= 1
                    ax[x_position, y_position].plot(
                        period_values,
                        result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model],
                        label=model,
                        color=const.DEFAULT_LABEL_COLOR[color_index],
                        linestyle="dashed" if model.endswith("NZ") else "solid",
                    )
                    color_index += 1

                ax[x_position, y_position].set_title(
                    f"Sigma versus T - Mw{mag}, Vs30-{vs30}"
                )
                ax[x_position, y_position].legend(im_models[const.PSA_IM_NAME])
                ax[x_position, y_position].xaxis.set_label_text("Period [sec]")
                ax[x_position, y_position].yaxis.set_label_text("Sigma [Ln Units]")
                ax[x_position, y_position].set_xscale("log")
                ax[x_position, y_position].set_ylim([0, 1])
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
    vs30_values: List,
    mag_dict: Dict,
    period_values: List,
    result_dict: Dict,
    plot_directory: pathlib.PosixPath,
):
    """Plots for pSA versus T

    Parameters
    ----------
    vs30_values: List
        list of Vs30s
    mag_dict: Dict
        Dictionary with a different Mw lists for a different tectonic type
    period_values: List
        list of Periods
    result_dict: Dict
        nested dictionary with a different Vs30 and Magnitude
    plot_directory: pathlib.PosixPath
        absolute path for a directory to store plot image
    """
    for tect_type, im_models in const.MODELS_DICT.items():
        x_position = 0
        fig, ax = plt.subplots(
            len(vs30_values), len(mag_dict[tect_type]), figsize=(18, 13.5), dpi=300
        )
        for vs30 in vs30_values:
            y_position = 0
            for mag in mag_dict[tect_type]:
                color_index = 0
                for model in im_models[const.PSA_IM_NAME]:
                    # To match the color with global version
                    if model.endswith("NZ"):
                        color_index -= 1
                    ax[x_position, y_position].plot(
                        period_values,
                        result_dict[tect_type][const.PSA_IM_NAME][vs30][mag][model],
                        label=model,
                        color=const.DEFAULT_LABEL_COLOR[color_index],
                        linestyle="dashed" if model.endswith("NZ") else "solid",
                    )
                    color_index += 1

                ax[x_position, y_position].set_title(
                    f"SA versus T - Mw{mag}, Vs30-{vs30}"
                )
                ax[x_position, y_position].legend(im_models[const.PSA_IM_NAME])
                ax[x_position, y_position].xaxis.set_label_text("Period [sec]")
                ax[x_position, y_position].yaxis.set_label_text("SA [g]")
                ax[x_position, y_position].set_xscale("log")
                ax[x_position, y_position].set_yscale("log")
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


def psa_sigma_plot(
    mag_dict: Dict,
    vs30_values: List,
    psa_periods: np.ndarray,
    rrup_value: Union[float, int],
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
    rrup_value: Union[float, int]
        Rupture distance in km
    """

    plot_directory = (
        pathlib.Path(__file__).resolve().parent.parent / "plot" / "psa_sigma_period"
    )
    plot_directory.mkdir(exist_ok=True, parents=True)

    faults, result_dict = init_setup(mag_dict, vs30_values)
    sites = get_sites(vs30_values, rrup_value)

    faults = get_faults(vs30_values, mag_dict, faults)

    result_dict = get_computed_gmms(
        vs30_values, sites, mag_dict, faults, result_dict, psa_periods, True
    )

    plot_psha_psa_sigma(vs30_values, mag_dict, psa_periods, result_dict, plot_directory)


def psa_plot(
    mag_dict: Dict,
    vs30_values: List,
    psa_periods: np.ndarray,
    rrup_value: Union[float, int],
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
    rrup_value: Union[float, int]
        Rupture distance in km
    """
    plot_directory = (
        pathlib.Path(__file__).resolve().parent.parent / "plot" / "psa_period"
    )
    plot_directory.mkdir(exist_ok=True, parents=True)

    faults, result_dict = init_setup(mag_dict, vs30_values)
    sites = get_sites(vs30_values, rrup_value)

    faults = get_faults(vs30_values, mag_dict, faults)

    result_dict = get_computed_gmms(
        vs30_values, sites, mag_dict, faults, result_dict, psa_periods, False
    )

    plot_psha_psa(vs30_values, mag_dict, psa_periods, result_dict, plot_directory)


if __name__ == "__main__":
    """Update those inputs to get different outputs"""
    mag_dict = {
        "ACTIVE_SHALLOW": [5, 6, 7, 8],
        "SUBDUCTION_SLAB": [5, 6, 7],
        "SUBDUCTION_INTERFACE": [7, 8, 9],
    }
    vs30_list = [200, 400, 760]
    period_list = np.linspace(0.01, 10, 200)
    rrup = 200

    psa_sigma_plot(mag_dict, vs30_list, period_list, rrup)
    psa_plot(mag_dict, vs30_list, period_list, rrup)
