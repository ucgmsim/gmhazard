from typing import List

import pandas as pd
import numpy as np
from scipy import stats

import sha_calc as sha_calc
from seistech_calc.im import IMComponent, IM, to_string_list
from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc import shared
from seistech_calc import constants
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

    # Combine the branches according to their weights
    mu, sigma, weights = None, None, []
    for cur_scenario in scenario_branches:
        cur_mu = cur_scenario.branch.weight * cur_scenario.mu_data
        cur_sigma = cur_scenario.branch.weight * cur_scenario.sigma_data
        weights.append(cur_scenario.branch.weight)
        if mu is None:
            mu, sigma = cur_mu, cur_sigma

            # Creates a multi-index dataframe with IM / Rupture as indexes and one column for the branch
            # Values for this dataframe is the Scenario Branch IM data
            im_branch_ruptures = pd.concat(
                [
                    pd.DataFrame(
                        val,
                        index=cur_scenario.mu_data.index.values,
                        columns=[cur_scenario.branch.name],
                    )
                    for val in cur_scenario.mu_data.T.values
                ],
                keys=cur_scenario.mu_data,
            )
        else:
            mu = mu.add(cur_mu)
            sigma = sigma.add(cur_sigma)

            # Creates a multi-index dataframe with IM / Rupture as indexes and one column for the branch
            # Values for this dataframe is the Scenario Branch IM data
            # Add another branch to the dataframe as a new column via join
            im_branch_ruptures = im_branch_ruptures.join(
                pd.concat(
                    [
                        pd.DataFrame(
                            val,
                            index=cur_scenario.mu_data.index.values,
                            columns=[cur_scenario.branch.name],
                        )
                        for val in cur_scenario.mu_data.T.values
                    ],
                    keys=cur_scenario.mu_data,
                )
            )

    # Calculating Percentiles
    im_branch_ruptures, weights = np.asarray(im_branch_ruptures), np.asarray(weights)
    weights = np.repeat(weights[None, ...], len(im_branch_ruptures), 0)

    # Sorting
    sort_ind = np.argsort(im_branch_ruptures, axis=1)
    im_branch_ruptures = np.take_along_axis(im_branch_ruptures, sort_ind, 1)
    weights = np.take_along_axis(weights, sort_ind, 1)

    # Inverse CDF lookup
    cdf_x, cdf_y = im_branch_ruptures, np.cumsum(weights, axis=1)
    x_values = sha_calc.shared.query_non_parametric_multi_cdf_invs(
        [0.16, 0.5, 0.84], cdf_x, cdf_y
    )

    # Combining Percentiles
    x_values = np.stack(x_values, axis=1)
    split_ruptures_on_im = np.split(x_values, len(ims))
    percentiles = pd.DataFrame()
    for i in range(0, len(split_ruptures_on_im)):
        cur_im_df = pd.DataFrame(
            split_ruptures_on_im[i],
            columns=[f"{ims[i]}_16th", f"{ims[i]}_50th", f"{ims[i]}_84th"],
            index=mu.index,
        )
        percentiles = cur_im_df if percentiles.empty else percentiles.join(cur_im_df)

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
