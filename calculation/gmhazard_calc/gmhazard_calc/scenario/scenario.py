from typing import List

import pandas as pd
import numpy as np
from scipy import stats

import sha_calc as sha_calc
from gmhazard_calc.im import IMComponent, IM, to_string_list
from gmhazard_calc import site
from gmhazard_calc import gm_data
from gmhazard_calc import shared
from gmhazard_calc import constants
from .ScenarioResult import BranchScenarioResult
from .ScenarioResult import EnsembleScenarioResult


def run_ensemble_scenario(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im_component: IMComponent = IMComponent.RotD50,
):
    """
    Computes the branch weighted curve for all branched in the given Ensemble for a Scenario

    Parameters
    ----------
    ensemble: Ensemble
        ensemble to use for calculation
    site_info: SiteInfo
        site scenario is for
    im_component: IMComponent
        desired IM Component for the data

    Returns
    -------
    EnsembleScenarioResult
    """
    ims = shared.get_SA_ims(ensemble.ims, component=im_component)
    scenario_branches = run_branches_scenario(ensemble, ims, site_info)

    # Calculate mu
    mu = sum(
        cur_scenario.branch.weight * cur_scenario.mu_data
        for cur_scenario in scenario_branches
    )

    # Calculate variance / sigma
    variance = 0
    for cur_scenario in scenario_branches:
        weighted_variance = cur_scenario.branch.weight * np.square(
            cur_scenario.sigma_data
        )
        weighted_variance.columns = mu.columns
        variance += weighted_variance
        variance += np.square(cur_scenario.branch.weight) * np.square(
            cur_scenario.mu_data - mu
        )
    sigma = np.sqrt(variance)

    # Get above and below std
    below_std = np.exp(-sigma) * mu
    above_std = np.exp(sigma) * mu
    below_std.columns = [f"{im}_16th" for im in ims]
    above_std.columns = [f"{im}_84th" for im in ims]

    percentiles = below_std.join(above_std)
    # Gets an interleaved order of columns between both below_std and above_std
    ordered_columns = list(sum(zip(below_std.columns, above_std.columns), ()))
    percentiles = percentiles[ordered_columns]

    return EnsembleScenarioResult(
        ensemble, scenario_branches, site_info, ims, mu, percentiles
    )


def run_branches_scenario(
    ensemble: gm_data.Ensemble, ims: List[IM], site_info: site.SiteInfo
):
    """
    Computes the branch weighted curve for all branched in the given Ensemble for a Scenario

    Parameters
    ----------
    ensemble: Ensemble
        im_ensemble to use for calculation
    ims: List[IM]
        ims to perform over for the branches
    site_info: SiteInfo
        site scenario is for

    Returns
    -------
    List of BranchScenarioResult
    """
    im_ensemble = ensemble.get_im_ensemble(ims[0].im_type)

    # Checks scenarios is only being computed for empirical data
    assert im_ensemble.im_data_type == constants.IMDataType.parametric

    scenarios = [
        run_branch_scenario(ensemble, ims, branch, site_info)
        for branch_name, branch in im_ensemble.branches_dict.items()
    ]
    return scenarios


def run_branch_scenario(
    ensemble: gm_data.Ensemble,
    ims: List[IM],
    branch: gm_data.Branch,
    site_info: site.SiteInfo,
):
    """
    Computes the branches Scenario Result

    Parameters
    ----------
    ensemble: Ensemble
        ensemble to use for calculation
    ims: List[IM]
        ims to perform over for the branches
    branch: Branch
        branch to run scenario over
    site_info: SiteInfo
        site scenario is for

    Returns
    -------
    BranchScenarioResult
    """
    im_data, _ = shared.get_im_data(
        branch, ensemble, site_info, constants.SourceType.fault
    )

    mu_data = np.exp(im_data.loc[:, to_string_list(ims)])
    sigma_data = im_data.loc[:, [str(im) + "_sigma" for im in ims]]

    return BranchScenarioResult(branch, site_info, ims, mu_data, sigma_data)


def filter_ruptures(ensemble_scenario, top_results: int = 20):
    """
    Filters the ruptures on the scenario to the top top_results, specified by the user and sorted alphabetically
    Parameters
    ----------
    ensemble_scenario: EnsembleScenarioResult
        ensemble scenario to filter
    top_results: int
        number of results to show at the end of the filter and reorder

    Returns
    -------
    EnsembleScenarioResult
    """
    # Getting the top ruptures
    mu_data = ensemble_scenario.mu_data
    sort_ind = np.argsort(stats.gmean(mu_data, axis=1))
    ruptures_sorted = mu_data.index.values[sort_ind]
    ruptures_filtered = ruptures_sorted[::-1][:top_results]

    # Applying the filter
    ensemble_scenario.mu_data, ensemble_scenario.percentiles = (
        mu_data.loc[ruptures_filtered].sort_index(),
        ensemble_scenario.percentiles.loc[ruptures_filtered].sort_index(),
    )

    return ensemble_scenario
