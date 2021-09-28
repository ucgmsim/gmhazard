from typing import Union, Optional, Dict

import pandas as pd
import numpy as np

import sha_calc as sha_calc
from gmhazard_calc import site
from gmhazard_calc import utils
from gmhazard_calc import shared
from gmhazard_calc import hazard
from gmhazard_calc import gm_data
from gmhazard_calc import site_source
from gmhazard_calc import rupture
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM
from .DisaggResult import BranchDisaggResult, EnsembleDisaggResult, DisaggGridData


def run_ensemble_disagg(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    exceedance: Optional[float] = None,
    im_value: Optional[float] = None,
    calc_mean_values: Optional[bool] = False,
    hazard_result: Optional[hazard.EnsembleHazardResult] = None,
) -> EnsembleDisaggResult:
    """Computes the ensemble disagg, combining the different
    branches as per equations (9) and (10) from
    "Consideration and Propagation of Ground Motion Selection
    Epistemic Uncertainties to Seismic Performance
    Metrics (Karim Tarbali, 2018)"

    Parameters
    ----------
    ensemble: Ensemble
    site_info: SiteInfo
    im: IM
    exceedance : float, optional
        Compute disagg at this exceedance, either the exceedance
        or the im_value parameter has to be given
    im_value: float, optional
        Compute disagg at this im value

    Returns
    -------
    BaseDisaggResult
    """
    ensemble.check_im(im)

    # Select the IMEnsemble
    im_ensemble = ensemble.get_im_ensemble(im.im_type)

    # Get the IM value of interest
    im_value = _get_im_value_and_checks(
        ensemble, site_info, im, exceedance, im_value, hazard_result=hazard_result
    )

    # Compute disagg for each branch
    branches_dict = run_branches_disagg(im_ensemble, site_info, im, None, im_value)

    fault_disagg_df = pd.DataFrame(
        {
            (branch_name, column): disagg_result.fault_disagg_id_ix[column]
            for branch_name, disagg_result in branches_dict.items()
            for column in ["contribution", "epsilon"]
        }
    )
    ds_disagg_df = pd.DataFrame(
        {
            (branch_name, column): disagg_result.ds_disagg_id_ix[column]
            for branch_name, disagg_result in branches_dict.items()
            for column in ["contribution", "epsilon"]
        }
    )
    del branches_dict

    # Fault disagg branches mean
    adj_branch_weights, _ = shared.compute_adj_branch_weights(
        ensemble, im, im_value, site_info
    )
    fault_disagg_mean = (
        fault_disagg_df.multiply(adj_branch_weights, axis=1, level=0)
        .groupby(axis=1, level=1)
        .sum()
    )

    # DS disagg branches mean
    ds_disagg_mean = (
        ds_disagg_df.multiply(adj_branch_weights, axis=1, level=0)
        .groupby(axis=1, level=1)
        .sum()
    )

    mean_values = None
    if calc_mean_values:
        # Use rupture_ids (due to required location matching for rrup mean)
        full_disagg = pd.concat([fault_disagg_mean, ds_disagg_mean])
        full_disagg.index = rupture.rupture_id_ix_to_rupture_id(
            ensemble, full_disagg.index.values
        )

        # Compute mean magnitude
        mag_mean = shared.compute_contr_mean(
            im_ensemble.rupture_df_id.magnitude,
            full_disagg.contribution.to_frame(),
        ).values[0]

        mag_16th, mag_84th = shared.compute_contr_16_84(
            im_ensemble.rupture_df_id.magnitude, full_disagg.contribution.to_frame()
        )

        # Epsilon mean, ignore entries with epsilon np.inf
        mask = np.abs(full_disagg.epsilon) != np.inf
        epsilon_mean = shared.compute_contr_mean(
            full_disagg.epsilon.loc[mask],
            full_disagg.contribution.loc[mask].to_frame(),
        ).values[0]

        # Rrrup mean
        # Convert to rupture_id for matching
        fault_rrup_disagg_df = fault_disagg_mean.contribution.copy()
        fault_rrup_disagg_df.index = rupture.rupture_id_ix_to_rupture_id(
            ensemble, fault_rrup_disagg_df.index.values.astype(str)
        )

        ds_rrup_disagg_df = ds_disagg_mean.contribution.copy()
        ds_rrup_disagg_df.index = rupture.rupture_id_ix_to_rupture_id(
            ensemble, ds_rrup_disagg_df.index.values.astype(str)
        )

        # Get distances
        fault_rrup_disagg_df = site_source.match_ruptures(
            site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info),
            fault_rrup_disagg_df,
            const.SourceType.fault,
        )
        ds_rrup_disagg_df = site_source.match_ruptures(
            site_source.get_distance_df(ensemble.ds_ssddb_ffp, site_info),
            ds_rrup_disagg_df,
            const.SourceType.distributed,
        )

        # Ignore nan entries (due to 200 km limit in SiteSourceDB)
        rrup_disagg_df = pd.concat([fault_rrup_disagg_df.rrup, ds_rrup_disagg_df.rrup])
        mask = ~rrup_disagg_df.isna()
        rrup_mean = shared.compute_contr_mean(
            rrup_disagg_df.loc[mask],
            full_disagg.contribution.loc[mask].to_frame(),
        ).values[0]

        rrup_16th, rrup_84th = shared.compute_contr_16_84(
            rrup_disagg_df.loc[mask], full_disagg.contribution.loc[mask].to_frame()
        )

        mean_values = pd.Series(
            index=[
                "magnitude_16th",
                "magnitude",
                "magnitude_84th",
                "epsilon",
                "rrup_16th",
                "rrup",
                "rrup_84th",
            ],
            data=[
                mag_16th,
                mag_mean,
                mag_84th,
                epsilon_mean,
                rrup_16th,
                rrup_mean,
                rrup_84th,
            ],
        )

    return EnsembleDisaggResult(
        fault_disagg_mean,
        ds_disagg_mean,
        site_info,
        im,
        im_value,
        ensemble,
        im_ensemble,
        exceedance=exceedance,
        mean_values=mean_values,
    )


def run_branches_disagg(
    im_ensemble: gm_data.IMEnsemble,
    site_info: site.SiteInfo,
    im: IM,
    exceedance: Optional[float] = None,
    im_value: Optional[float] = None,
) -> Dict[str, BranchDisaggResult]:
    """Computes the disagg for every branch in the ensemble

    Parameters
    ----------
    im_ensemble: IMEnsemble
    site_info: SiteInfo
    im: IM
    exceedance : float, optional
        Compute disagg at this exceedance, either the exceedance
        or the im_value parameter has to be given
    im_value: float, optional
        Compute disagg at this im value

    Returns
    -------
    Dictionary
        Keys are the branch names
    """
    # Consistency checks
    im_ensemble.check_im(im)
    im_value = _get_im_value_and_checks(
        im_ensemble.ensemble, site_info, im, exceedance=exceedance, im_level=im_value
    )

    # Compute disagg for each branch
    branch_disagg_dict = {}
    for branch_name, branch in im_ensemble.branches_dict.items():
        branch_disagg_dict[branch_name] = run_branch_disagg(
            im_ensemble, branch, site_info, im, None, im_value
        )

    return branch_disagg_dict


def run_branch_disagg(
    im_ensemble: gm_data.IMEnsemble,
    branch: gm_data.Branch,
    site_info: site.SiteInfo,
    im: IM,
    exceedance: Optional[float] = None,
    im_value: Optional[float] = None,
) -> BranchDisaggResult:
    """Computes the disagg a single branch of an ensemble

    Parameters
    ----------
    im_ensemble: IMEnsemble
    branch: Branch
    site_info: SiteInfo
    im: IM
    exceedance : float, optional
        Compute disagg at this ensemble exceedance, either the exceedance
        or the im_value parameter has to be given
        Note: The IM value used to perform disagg is calculated using the
        mean ensemble hazard, not the branch hazard.
    im_value: float, optional
        Compute disagg at this im value
    """
    # Consistency checks
    im_ensemble.check_im(im)
    im_value = _get_im_value_and_checks(
        im_ensemble.ensemble, site_info, im, exceedance=exceedance, im_level=im_value
    )

    # Get the ground motion probabilities
    fault_gm_prob = shared.get_gm_prob(
        branch,
        site_info,
        im,
        im_value,
        const.SourceType.fault,
        ensemble=im_ensemble.ensemble,
    )
    ds_gm_prob = shared.get_gm_prob(
        branch,
        site_info,
        im,
        im_value,
        const.SourceType.distributed,
        ensemble=im_ensemble.ensemble,
    )

    # Get the recurrence probabilities
    rec_prob_df = branch.rupture_df_id_ix["annual_rec_prob"]

    # Compute the branch hazard for the specified IM value
    excd_prob = sha_calc.hazard_single(
        pd.concat([fault_gm_prob, ds_gm_prob]), rec_prob_df
    )

    # Fault based disagg
    fault_disagg = sha_calc.disagg_exceedance(
        fault_gm_prob, rec_prob_df, excd_prob=excd_prob
    )
    fault_disagg.name = "contribution"
    fault_epsilon = _compute_epsilon(
        branch,
        fault_gm_prob,
        site_info,
        im,
        const.SourceType.fault,
        ensemble=im_ensemble.ensemble,
    )
    fault_disagg = pd.merge(
        fault_disagg, fault_epsilon, left_index=True, right_index=True
    )

    # DS based disagg
    ds_disagg = sha_calc.disagg_exceedance(ds_gm_prob, rec_prob_df, excd_prob=excd_prob)
    ds_disagg.name = "contribution"
    ds_epsilon = _compute_epsilon(
        branch,
        ds_gm_prob,
        site_info,
        im,
        const.SourceType.distributed,
        ensemble=im_ensemble.ensemble,
    )
    ds_disagg = pd.merge(ds_disagg, ds_epsilon, left_index=True, right_index=True)

    return BranchDisaggResult(
        fault_disagg, ds_disagg, site_info, im, im_value, branch, exceedance=exceedance
    )


def run_disagg_gridding(
    disagg_data: Union[BranchDisaggResult, EnsembleDisaggResult],
    mag_min: float = 5.0,
    mag_n_bins: int = 16,
    mag_bin_size: float = 0.25,
    rrup_min: float = 0.0,
    rrup_n_bins: int = 20,
    rrup_bin_size: float = 10,
) -> DisaggGridData:
    """Computes the 2d histogram using magnitude and rrup as x and y,
    with weights given by the contribution of each rupture

    Parameters
    ----------
    disagg_data: BaseDisaggResult
    mag_min: float
        Minimum magnitude
    mag_n_bins: int
        Number of magnitude bins
    mag_bin_size: float
        Magnitude size of the bins
    rrup_min: float
        Minimum rrup
    rrup_n_bins: int
        Number of rrup bins
    rrup_bin_size: float
        Rrup size of the bins

    Returns
    -------
    DisaggGridData
    """
    ensemble = (
        disagg_data.ensemble
        if isinstance(disagg_data, EnsembleDisaggResult)
        else disagg_data.im_ensemble.ensemble
    )
    im_ensemble = disagg_data.im_ensemble

    # Get rupture details for the flt ruptures
    flt_ruptures = pd.merge(
        im_ensemble.rupture_df_id,
        disagg_data.fault_disagg_id,
        left_index=True,
        right_index=True,
    )

    # Add distance data to fault rupture data
    dist_df = site_source.get_distance_df(ensemble.flt_ssddb_ffp, disagg_data.site_info)
    if dist_df is None:
        raise Exception(
            f"No distance data available for station {disagg_data.site_info.station_name}, "
            f"can't perform gridding without distance data!"
        )
    flt_ruptures = site_source.match_ruptures(
        dist_df, flt_ruptures.copy(), const.SourceType.fault
    )

    # Get rupture details for the ds ruptures
    ds_ruptures = pd.merge(
        im_ensemble.rupture_df_id,
        disagg_data.ds_disagg_id,
        left_index=True,
        right_index=True,
    )

    # Add DS location name to DS rupture data
    ds_ruptures["loc_name"] = np.asarray(
        list(np.chararray.split(ds_ruptures.index.values.astype(str), "--")), dtype=str
    )[:, 0]
    ds_ruptures["rupture_id"] = ds_ruptures.index.values

    # Add distance data to DS rupture data
    dist_df = site_source.get_distance_df(ensemble.ds_ssddb_ffp, disagg_data.site_info)
    if dist_df is None:
        raise Exception(
            f"No distance data available for station {disagg_data.site_info.station_name}, "
            f"can't perform gridding without distance data!"
        )
    ds_ruptures = site_source.match_ruptures(
        dist_df, ds_ruptures.copy(), const.SourceType.distributed
    )

    # Drop nan values (ruptures for which rrup is not available, due to rrup > 200km)
    flt_ruptures.dropna(axis=0, how="any", subset=np.asarray(["rrup"]), inplace=True)
    ds_ruptures.dropna(axis=0, how="any", subset=np.asarray(["rrup"]), inplace=True)
    rupture_df = pd.concat([flt_ruptures, ds_ruptures], sort=True)

    mag_bins = np.arange(
        mag_min, mag_min + ((mag_n_bins + 1) * mag_bin_size), mag_bin_size
    )
    rrup_bins = np.arange(
        rrup_min, rrup_min + ((rrup_n_bins + 1) * rrup_bin_size), rrup_bin_size
    )

    # Bin by fault and distributed seismicity
    mask = rupture_df.rupture_type == const.SourceType.fault.value
    flt_bin_contr, mag_edges, rrup_edges = np.histogram2d(
        rupture_df.magnitude.loc[mask],
        rupture_df.rrup.loc[mask],
        bins=(mag_bins, rrup_bins),
        weights=rupture_df.contribution.loc[mask].values,
    )

    mask = rupture_df.rupture_type == const.SourceType.distributed.value
    ds_bin_contr, _, __ = np.histogram2d(
        rupture_df.magnitude.loc[mask],
        rupture_df.rrup.loc[mask],
        bins=(mag_bins, rrup_bins),
        weights=rupture_df.contribution.loc[mask].values,
    )

    # Epsilon bin definitions
    eps_bins = [
        (-np.inf, -2),
        (-2, -1),
        (-1, -0.5),
        (-0.5, 0),
        (0, 0.5),
        (0.5, 1),
        (1, 2),
        (2, np.inf),
    ]
    eps_bin_contr = []
    for ix, (cur_bin_min, cur_bin_max) in enumerate(eps_bins):
        cur_mask = (cur_bin_min <= rupture_df.epsilon.values) & (
            rupture_df.epsilon.values < cur_bin_max
        )
        cur_bin_contr, _, __ = np.histogram2d(
            rupture_df.magnitude.loc[cur_mask],
            rupture_df.rrup.loc[cur_mask],
            bins=(mag_bins, rrup_bins),
            weights=rupture_df.contribution.loc[cur_mask].values,
        )
        eps_bin_contr.append(cur_bin_contr)

    return DisaggGridData(
        disagg_data,
        flt_bin_contr,
        ds_bin_contr,
        eps_bins,
        eps_bin_contr,
        mag_edges,
        rrup_edges,
        mag_min,
        mag_n_bins,
        mag_bin_size,
        rrup_min,
        rrup_n_bins,
        rrup_bin_size,
    )


def _get_im_value_and_checks(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    exceedance: float = None,
    im_level: float = None,
    hazard_result: hazard.HazardResult = None,
) -> float:
    """Performs consistency checks and computes the IM level if not provided"""
    if exceedance is None and im_level is None:
        raise ValueError("Either the exceendance or the IM level has to be specified.")
    if exceedance is not None and im_level is not None:
        print(
            "Both the exceedance and the IM level have been specified, "
            "using the IM level for the calculation."
        )

    # Retrieve the IM level from the ensemble hazard result
    if im_level is None:
        hazard_result = (
            hazard.run_ensemble_hazard(ensemble, site_info, im)
            if hazard_result is None
            else hazard_result
        )
        im_level = hazard_result.exceedance_to_im(exceedance)

    return im_level


def _compute_epsilon(
    branch: gm_data.Branch,
    gm_prob_df: pd.Series,
    site_info: site.SiteInfo,
    im: IM,
    source_type: const.SourceType,
    ensemble: gm_data.Ensemble = None,
):
    """Computes epsilon for the specified branch using the provided
    rupture exceedance probabilities

    Parameters
    ----------
    branch: Branch
    gm_prob_df: pd.DataFrame
    site_info: SiteInfo
    im: IM
    source_type: SourceType
    ensemble: Ensemble, optional
        If specified and the Ensemble has IM data
        caching enabled then IM data is retrieved from
        the cache if possible

    Returns
    -------
    pd.Series
        Epsilon for each rupture
    """
    im_data, im_data_type = shared.get_im_data(
        branch,
        ensemble,
        site_info,
        source_type,
        im_component=im.component,
        as_rupture_id_ix=True,
    )

    if im_data_type is const.IMDataType.parametric:
        epsilon = sha_calc.epsilon_para(utils.to_mu_sigma(im_data, im), gm_prob_df)
    else:
        epsilon = sha_calc.epsilon_non_para(im_data[str(im)], gm_prob_df)

    epsilon.name = "epsilon"
    return epsilon
