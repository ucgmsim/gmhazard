import multiprocessing as mp
from typing import Union, List, Iterable, Dict

import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import shared
from gmhazard_calc import hazard
from gmhazard_calc import gm_data
from gmhazard_calc import exceptions
from gmhazard_calc.nz_code import nzs1170p5
from gmhazard_calc.im import IM, IMType, IMComponent
from .UHSResult import BaseUHSResult, EnsembleUHSResult, BranchUHSResult

DEFAULT_PSA_PERIODS = [
    0.01,
    0.02,
    0.03,
    0.04,
    0.05,
    0.075,
    0.1,
    0.12,
    0.15,
    0.17,
    0.2,
    0.25,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.75,
    0.8,
    0.9,
    1.0,
    1.25,
    1.5,
    2.0,
    2.5,
    3.0,
    4.0,
    5.0,
    6,
    7.5,
    10.0,
]


def run_ensemble_uhs(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    exceedance_values: np.ndarray,
    n_procs: int = 1,
    calc_percentiles: bool = False,
    im_component: IMComponent = IMComponent.RotD50,
) -> List[EnsembleUHSResult]:
    """Calculates the uniform hazard spectra

    Parameters
    ----------
    ensemble : Ensemble
        Ensemble to use for calculation, ensemble id or Ensemble object
    site_info : SiteInfo
        Hazard for this site / location name
    exceedance_values : np.ndarray
        The exceedance values of interest
    n_procs: int, optional
        How many processes to use for uhs calculation
    calc_percentiles: bool, optional
        True or false for calculating 16th and 84th percentiles

    Returns
    -------
    List of EnsembleUHSResult
        In the same order as the specified exceedance_values
    """
    # Get pSA IM and periods that are in all the datasets
    pSA_ims = shared.get_SA_ims(ensemble.ims, component=im_component)
    # Gets the period values, 0 period is for PGA
    pSA_periods = np.asarray([im.period if im.is_pSA() else 0 for im in pSA_ims])

    # Get the pSA values
    if n_procs == 1:
        pSA_values_tuple = [
            __get_pSA_values(
                ensemble, site_info, cur_pSA_im, exceedance_values, calc_percentiles
            )
            for cur_pSA_im in pSA_ims
        ]
    else:
        with mp.Pool(processes=n_procs) as pool:
            pSA_values_tuple = pool.starmap(
                __get_pSA_values,
                [
                    (
                        ensemble,
                        site_info,
                        cur_pSA_im,
                        exceedance_values,
                        calc_percentiles,
                    )
                    for cur_pSA_im in pSA_ims
                ],
            )

    # Create the result objects
    pSA_values, pSA_branch_values, percentiles = zip(*pSA_values_tuple)

    # Mean pSA values
    # shape: (n_periods/n_pSA_IMs, n_exceedances)
    pSA_values = np.stack(pSA_values)

    # Branch pSA values
    # shape: (n_periods/n_pSA_IMs, n_exceedances, n_branches)
    pSA_branch_values = np.stack(pSA_branch_values)

    # Percentiles (16th and 84th)
    # shape: (n_periods/n_pSA_IMs, n_exceedances, 2)
    percentiles = np.stack(percentiles)

    ensemble_uhs_list = []
    for ix, cur_exceedance in enumerate(exceedance_values):
        branch_uhs = [
            BranchUHSResult(
                cur_branch,
                site_info,
                cur_exceedance,
                pSA_periods,
                pSA_branch_values[:, ix, ib],
            )
            for ib, cur_branch in enumerate(
                ensemble.get_im_ensemble(IMType.pSA).branches
            )
        ]
        ensemble_uhs_list.append(
            EnsembleUHSResult(
                ensemble,
                branch_uhs,
                site_info,
                cur_exceedance,
                pSA_periods,
                pSA_values[:, ix],
                pd.DataFrame(
                    data=percentiles[:, ix], columns=["16th", "84th"], index=pSA_periods
                )
                if calc_percentiles
                else None,
            )
        )

    return ensemble_uhs_list


def __get_pSA_values(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    cur_pSA_im: IM,
    exceedance_values: np.ndarray,
    calc_percentiles: bool = False,
):
    """
    Calculates the pSA values for each of the given exceedance values for branches and the mean

    Parameters
    ----------
    ensemble: Ensemble
        Ensemble to use for calculation
    site_info:  SiteInfo
        Hazard for this site / location name
    cur_pSA_im: IM
        Current pSA IM (i.e. the current pSA period)
    exceedance_values: np.ndarray
        The exceedance values of interest
    calc_percentiles: bool, optional
        True or false for calculating 16th and 84th percentiles

    Returns
    -------
    pSA_values: np.ndarray
        Array of pSA values for the mean, of shape (no. exceedance_values)
    pSA_branch_values: np.ndarray
        Array of pSA values for the branches, of shape (no. exceedance_values, no. branches)
    pSA_percentiles: np.ndarray
        Array of pSA values for each of the percentiles, of shape (no. exceedance values, no. percentiles)
    """
    hazard_mean, hazard_branches = hazard.run_full_hazard(
        ensemble, site_info, cur_pSA_im, calc_percentiles=calc_percentiles
    )

    pSA_values, pSA_branch_values = [], []
    pSA_percentiles = []
    for cur_exceedance in exceedance_values:
        try:
            pSA_values.append(hazard_mean.exceedance_to_im(cur_exceedance))
        except exceptions.ExceedanceOutOfRangeError:
            pSA_values.append(np.nan)

        if calc_percentiles:
            try:
                pSA_percentiles.append(
                    [
                        hazard.exceedance_to_im(
                            cur_exceedance, hazard_mean.im_values, percentile[1]
                        )
                        for percentile in hazard_mean.percentiles.items()
                    ]
                )
            except ValueError:
                pSA_percentiles.append([np.nan, np.nan])

        try:
            pSA_branch_values.append(
                [
                    cur_branch.exceedance_to_im(cur_exceedance)
                    for cur_branch in hazard_branches.values()
                ]
            )
        except exceptions.ExceedanceOutOfRangeError as ex:
            pSA_branch_values.append(np.full(len(hazard_branches), np.nan))

    return (
        np.asarray(pSA_values),
        np.asarray(pSA_branch_values),
        np.asarray(pSA_percentiles) if calc_percentiles else None,
    )


def run_nzs1170p5_uhs(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    exceedance_values: np.ndarray,
    pSA_periods: Iterable[float] = None,
    opt_nzs1170p5_args: Dict = None,
) -> Union[None, List[nzs1170p5.NZS1170p5Result]]:
    """Computes the UHS for NZ code

    Note: unlike uniform_hazard_spectra, the resulting
    list is per pSA_periods, NOT exceedance!
    """
    if opt_nzs1170p5_args is None:
        im_component = IMComponent.Larger
        opt_nzs1170p5_args = {}
    else:
        if opt_nzs1170p5_args.get("im_component") is None:
            im_component = IMComponent.Larger
        else:
            im_component = opt_nzs1170p5_args.get("im_component")
            del opt_nzs1170p5_args["im_component"]

    pSA_periods = DEFAULT_PSA_PERIODS if pSA_periods is None else pSA_periods

    results = []
    for cur_period in pSA_periods:
        im = (
            IM(IMType.pSA, period=cur_period, component=im_component)
            if cur_period > 0
            else IM(IMType.PGA, component=im_component)
        )

        results.append(
            nzs1170p5.run_ensemble_nzs1170p5(
                ensemble, site_info, im, exceedance_values, **opt_nzs1170p5_args
            )
        )

    # Return None if all of the specified exceedance values
    # are out of bounds
    return results if any(results) else None


def run_uhs_single(
    ensemble: gm_data.Ensemble, site_info: site.SiteInfo, exceedance_value: float
):
    """Calculates the uniform hazard spectra for a single exceedance

    Parameters
    ----------
    ensemble : Ensemble
        Ensemble to use for calculation, ensemble id or Ensemble object
    site_info : SiteInfo
        Hazard for this site / location name
    exceedance_value : float
        The exceedance value of interest

    Returns
    -------
    BaseUHSResult
    """
    return run_ensemble_uhs(ensemble, site_info, np.asarray([exceedance_value]))[0]
