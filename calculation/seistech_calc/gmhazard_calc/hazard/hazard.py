import time
import multiprocessing as mp
from typing import Tuple, Dict, Optional

import numpy as np
import pandas as pd
from scipy.interpolate.interpolate import interp1d

import sha_calc as sha_calc
from gmhazard_calc import site
from gmhazard_calc import utils
from gmhazard_calc import shared
from gmhazard_calc import gm_data
from gmhazard_calc import site_source
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM
from .HazardResult import BranchHazardResult, EnsembleHazardResult


DEFAULT_N_IM_VALUES = 200


def run_ensemble_hazard(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    branch_hazard: Optional[Dict[str, BranchHazardResult]] = None,
    im_values: Optional[np.ndarray] = None,
    calc_percentiles: bool = True,
) -> EnsembleHazardResult:
    """Computes the weighted hazard curve for all branches in
    the specified ensemble.

    Parameters
    ----------
    ensemble: Ensemble
        ensemble to use for calculation
    site_info: SiteInfo
        The site at which to calculate the hazard curve
    im: IM
        IM object for specifying the IM to use for calculations
    branch_hazard: Dictionary of str: HazardResult, optional
        Where the key is the branch name the hazard result is for.
        If specified then this saves re-computing the hazard
        results for the branches.
    im_values: np.ndarray, optional
        The range of IM values for which to calculate the
        hazard, not used if branches_hazard is passed in
    calc_percentiles: bool, optional
        True or False to calculate the 16th and 84th percentiles

    Returns
    -------
    HazardResult
    """

    def get_weighted_branch_hazard(hazard: BranchHazardResult):
        return (
            hazard.branch.weight * hazard.fault_hazard,
            hazard.branch.weight * hazard.ds_hazard,
        )

    ensemble.check_im(im)

    # Get the hazard per branch
    if branch_hazard is None:
        branch_hazard = run_branches_hazard(
            ensemble,
            site_info,
            im,
            im_values=im_values,
        )

    # Combine the branches according to their weights
    fault_hazard, ds_hazard = None, None
    for branch_name, cur_hazard in branch_hazard.items():
        cur_fault_h, cur_ds_h = get_weighted_branch_hazard(cur_hazard)
        if fault_hazard is None:
            fault_hazard, ds_hazard = cur_fault_h, cur_ds_h
        else:
            fault_hazard += cur_fault_h
            ds_hazard += cur_ds_h

    # Compute 16th and 84th percentile if flag enabled
    percentiles = None
    if calc_percentiles:
        # Retrieving data
        im_values = fault_hazard.index.values
        excd_values, weights = [], []
        for cur_branch in branch_hazard.values():
            assert np.all(cur_branch.fault_hazard.index.values == im_values)
            excd_values.append(cur_branch.total_hazard.values)
            weights.append(cur_branch.branch.weight)
        excd_values, weights = np.asarray(excd_values).T, np.asarray(weights)
        weights = np.repeat(weights[None, ...], im_values.size, 0)

        # Sorting
        sort_ind = np.argsort(excd_values, axis=1)
        excd_values = np.take_along_axis(excd_values, sort_ind, 1)
        weights = np.take_along_axis(weights, sort_ind, 1)

        # Inverse CDF lookup
        cdf_x, cdf_y = excd_values, np.cumsum(weights, axis=1)
        x_values = sha_calc.shared.query_non_parametric_multi_cdf_invs(
            [0.16, 0.84], cdf_x, cdf_y
        )
        x_values = np.stack(x_values, axis=1)
        percentiles = pd.DataFrame(
            data=x_values, columns=["16th", "84th"], index=fault_hazard.index.values
        )

    return EnsembleHazardResult(
        im,
        site_info,
        fault_hazard,
        ds_hazard,
        ensemble,
        list(branch_hazard.values()),
        percentiles=percentiles,
    )


def run_branches_hazard(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    im_values: Optional[np.ndarray] = None,
) -> Dict[str, BranchHazardResult]:
    """Runs computation of the hazard curve for each of the branches in
    the specified IM-ensemble.

    Parameters
    ----------
    ensemble : Ensemble
        Ensemble to use for calculation
    site_info : SiteInfo
        The site at which to calculate the hazard curve
    im : IM
        IM Object to use for calculations
    im_values: array of floats, optional
        The IM values for which to calculate the hazard for.

    Returns
    -------
    Dict of str : HazardResult, where the key is the branch name
    """
    ensemble.check_im(im)
    im_ensemble = ensemble.get_im_ensemble(im.im_type)

    hazards = {}
    for branch_name, branch in im_ensemble.branches_dict.items():
        hazards[branch_name] = run_branch_hazard(
            branch, site_info, im, im_values=im_values
        )

    return hazards


def run_branch_hazard(
    branch: gm_data.Branch,
    site_info: site.SiteInfo,
    im: IM,
    im_values: Optional[np.ndarray] = None,
) -> BranchHazardResult:
    """Computes the hazard for a single branch

    Parameters
    ----------
    branch: Branch
        The branch for which to calculate the hazard curve
    site_info: SiteInfo
        The site at which to calculate the hazard curve
    im: IM
        IM Object used for calculations
    im_values: np.ndarray, optional
        The IM values for which to calculate the hazard for.

    Returns
    -------
    HazardResult
    """
    im_values = (
        utils.get_im_values(im, n_values=DEFAULT_N_IM_VALUES)
        if im_values is None
        else im_values
    )

    # Fault Hazard
    fault_gm_prob_df = shared.get_gm_prob_df(
        branch,
        site_info,
        im,
        im_values,
        const.SourceType.fault,
        ensemble=branch.im_ensemble.ensemble,
    )
    if fault_gm_prob_df is not None:
        fault_hazard = sha_calc.hazard_curve(
            fault_gm_prob_df, branch.rupture_df_id_ix["annual_rec_prob"]
        )
    else:
        fault_hazard = pd.Series(data=np.zeros(im_values.shape), index=im_values)

    # DS Hazard
    ds_gm_prob_df = shared.get_gm_prob_df(
        branch,
        site_info,
        im,
        im_values,
        const.SourceType.distributed,
        ensemble=branch.im_ensemble.ensemble,
    )
    if ds_gm_prob_df is not None:
        ds_hazard = sha_calc.hazard_curve(
            ds_gm_prob_df, branch.rupture_df_id_ix["annual_rec_prob"]
        )
    else:
        ds_hazard = pd.Series(data=np.zeros(im_values.shape), index=im_values)

    return BranchHazardResult(im, site_info, fault_hazard, ds_hazard, branch)


def run_full_hazard(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    im: IM,
    calc_percentiles: bool = False,
    im_values: Optional[np.ndarray] = None,
) -> Tuple[EnsembleHazardResult, Dict[str, BranchHazardResult]]:
    """Convenience function, computes the ensemble
     and hazard for all branches.

    Parameters
    ----------
    branch: Branch
        The branch for which to calculate the hazard curve
    site_info: SiteInfo
        The site at which to calculate the hazard curve
    im: IM
        IM Object to use for calculations
    calc_percentiles: bool, optional
        True or false for calculating 16th and 84th percentiles
    im_values: np.ndarray, optional
        The IM values for which to calculate the hazard for.

    Returns
    -------
    HazardResult:
        The ensemble hazard
    dict:
        The hazard for each branch, key is the branch name
    """
    branch_hazard = run_branches_hazard(ensemble, site_info, im, im_values=im_values)
    ens_hazard = run_ensemble_hazard(
        ensemble,
        site_info,
        im,
        calc_percentiles=calc_percentiles,
        branch_hazard=branch_hazard,
        im_values=im_values,
    )

    return ens_hazard, branch_hazard


def run_hazard_map(
    ensemble: gm_data.Ensemble, im: IM, exceedance: float, n_procs: Optional[int] = 4
) -> pd.DataFrame:
    """
    Computes the hazard at each station in the ensemble for the
    specified exceedance.

    Parameters
    ----------
    ensemble: Ensemble
    im: IM
        IM Object used for calculations
    exceedance: float
        The exceedance value
    n_procs:
        Number of processes to use

    Returns
    -------
    pd.Series
        format: index = station_name, values: exceedance probability
    """
    # Drop duplicate location stations
    stations_df = ensemble.stations.drop_duplicates(subset=["lon", "lat"])

    n_stations = stations_df.shape[0]
    if n_procs == 1:
        excd_probs = []
        for ix, station_name in enumerate(stations_df.index.values):
            excd_probs.append(
                _get_hazard(ensemble, station_name, im, exceedance, ix, n_stations)
            )
    else:
        with mp.Pool(n_procs) as p:
            excd_probs = p.starmap(
                _get_hazard,
                [
                    (ensemble, station_name, im, exceedance, ix, n_stations)
                    for ix, station_name in enumerate(stations_df.index.values)
                ],
            )

    result_df = stations_df.copy()
    result_df["value"] = excd_probs
    return result_df


def get_exceedance_rate(probability: float, years: int):
    """Gets the exceedance rate for the specified probability
    in number of specified years

    Parameters
    ----------
    probability: float
        The probability of interest (e.g. 50 for 50%)
    years: int
        The number of years

    Returns
    -------
    float
        The exceedance rate
    """
    return -1.0 / years * np.log(1 - (probability / 100))


def exceedance_to_im(
    exceedance: float, im_values: np.ndarray, hazard_values: np.ndarray
):
    """Converts the given exceedance rate to an IM value, based on the
    provided im and hazard values

    Parameters
    ----------
    exceedance: float
        The exceedance value of interest
    im_values: numpy array
        The IM values corresponding to the hazard values
        Has to be the same shape as hazard_values
    hazard_values: numpy array
        The hazard values corresponding to the IM values
        Has to be the same shape as im_values

    Returns
    -------
    float
        The IM value corresponding to the provided exceedance
    """
    return np.exp(
        interp1d(
            np.log(hazard_values) * -1,
            np.log(im_values),
            kind="linear",
            bounds_error=True,
        )(np.log(exceedance) * -1)
    )


def im_to_exceedance(im_value: float, im_values: np.ndarray, hazard_values: np.ndarray):
    """Inverse to exceedance_to_im"""
    return np.exp(
        interp1d(
            np.log(im_values), np.log(hazard_values), kind="linear", bounds_error=True
        )(np.log(im_value))
    )


def _get_hazard(
    ensemble: gm_data.Ensemble,
    station_name: str,
    im: IM,
    exceedance: float,
    ix: int,
    n_stations: int,
):
    """Computes the ensemble hazard curve for the specific station"""
    start_time = time.time()
    site_info = site.get_site_from_name(ensemble, station_name)
    im_value = run_ensemble_hazard(ensemble, site_info, im).exceedance_to_im(exceedance)

    print(
        f"Progress {ix}/{n_stations} - station {station_name} "
        f"- {time.time() - start_time}"
    )
    return im_value


def vs30_update(site_info: site.SiteInfo, hazard_result: BranchHazardResult):
    """Computes the updated hazard for the user specified vs30 value

    Parameters
    ----------
    site_info: SiteInfo
        Site of interest
    hazard_result: HazardResult
        The hazard result for the db vs30 value

    Returns
    -------
    flt_upd_hazard: pd.Series
        The fault based updated hazard
        format: index = IM values, values = exceedance probability
    ds_upd_hazard: pd.DataFrame
        The distributed seismicity based updated hazard
        format: index = IM values, values = exceedance probability
    """
    import empirical.util.classdef as classdef
    import empirical.util.empirical_factory as emp_factory

    branch, ensemble = hazard_result.branch, hazard_result.im_ensemble.ensemble
    im_ensemble = hazard_result.im_ensemble

    # Get IM of interest and the IM values of interest
    im = hazard_result.im
    im_values = hazard_result.im_values

    # Get the recurrance & gm prob dfs
    rec_prob = branch.rupture_df_id["annual_rec_prob"]
    flt_gm_prob_df = shared.get_gm_prob_df(
        branch, site_info, im, im_values, const.SourceType.fault, ensemble=ensemble
    )
    ds_gm_prob_df = shared.get_gm_prob_df(
        branch,
        site_info,
        im,
        im_values,
        const.SourceType.distributed,
        ensemble=ensemble,
    )

    # Get the fault and distributed disagg and combine to get the full disagg
    flt_disagg = sha_calc.disagg_exceedance_multi(
        flt_gm_prob_df, rec_prob, hazard_result.total_hazard
    )
    ds_disagg = sha_calc.disagg_exceedance_multi(
        ds_gm_prob_df, rec_prob, hazard_result.total_hazard
    )
    full_disagg = pd.concat([flt_disagg, ds_disagg])

    # Create distance lookup
    flt_distance_df = site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info)
    ds_distance_df = site_source.get_distance_df(ensemble.ds_ssddb_ffp, site_info)
    distance_lookup_df = pd.concat([flt_distance_df, ds_distance_df])

    # Create a rupture_id to location name lookup, since the data from the
    # the site-source db uses location names and not rupture ids
    flt_loc_names = site_source.rupture_id_to_loc_name(
        flt_disagg.index.values, const.SourceType.fault
    )
    ds_loc_names = site_source.rupture_id_to_loc_name(
        ds_disagg.index.values, const.SourceType.distributed
    )
    loc_names_lookup = pd.concat([flt_loc_names, ds_loc_names])

    # Compute the mean magnitude
    ruptures = full_disagg.index.values
    flt_ruptures = flt_disagg.index.values
    ds_ruptures = ds_disagg.index.values
    flt_mag_mean_df = shared.compute_contr_mean(
        im_ensemble.rupture_df_id.magnitude.loc[flt_ruptures], full_disagg.loc[flt_ruptures]
    )
    ds_mag_mean_df = shared.compute_contr_mean(
        im_ensemble.rupture_df_id.magnitude.loc[ds_ruptures], full_disagg.loc[ds_ruptures]
    )

    # Create a distance dataframe for the ruptures of interest
    # Note: Have to use reindex since there might be ruptures for which
    # there is no site-source data for the current station (reindex just sets those to nan)
    distance_df = distance_lookup_df.reindex(loc_names_lookup.loc[ruptures].values)
    distance_df = distance_df.set_index(ruptures)

    # Compute the mean rrup & rjb
    flt_rrup_mean_df = shared.compute_contr_mean(
        distance_df.rrup.loc[flt_ruptures], full_disagg.loc[flt_ruptures]
    )
    ds_rrup_mean_df = shared.compute_contr_mean(
        distance_df.rrup.loc[ds_ruptures], full_disagg.loc[ds_ruptures]
    )

    flt_rjb_mean_df = shared.compute_contr_mean(
        distance_df.rjb.loc[flt_ruptures], full_disagg.loc[flt_ruptures]
    )
    ds_rjb_mean_df = shared.compute_contr_mean(
        distance_df.rjb.loc[ds_ruptures], full_disagg.loc[ds_ruptures]
    )

    # Sanity check (can probably remove these at some point)
    assert np.all(np.isclose(flt_mag_mean_df.index.values, im_values))
    assert np.all(np.isclose(ds_mag_mean_df.index.values, im_values))
    assert np.all(np.isclose(flt_rrup_mean_df.index.values, im_values))
    assert np.all(np.isclose(ds_rrup_mean_df.index.values, im_values))
    assert np.all(np.isclose(flt_rjb_mean_df.index.values, im_values))
    assert np.all(np.isclose(ds_rjb_mean_df.index.values, im_values))

    # Compute the vs30 ratios for each IM value of the hazard data
    vs30_ratio, flt_vs30_ratio, ds_vs30_ratio = [], [], []
    for ix, im_value in enumerate(im_values):
        # Create the fault and site objects
        cur_flt_fault = classdef.Fault(
            Mw=flt_mag_mean_df.iloc[ix], rake=-90.0, dip=45.0, zbot=15.0, hdepth=5.0
        )
        cur_ds_fault = classdef.Fault(
            Mw=ds_mag_mean_df.iloc[ix], rake=-90.0, dip=45.0, zbot=15.0, hdepth=5.0
        )

        cur_flt_site_db = classdef.Site(
            rrup=float(flt_rrup_mean_df.iloc[ix]),
            rjb=float(flt_rjb_mean_df.iloc[ix]),
            rx=0,
            vs30=site_info.vs30,
        )
        cur_flt_site_user = classdef.Site(
            rrup=float(flt_rrup_mean_df.iloc[ix]),
            rjb=float(flt_rjb_mean_df.iloc[ix]),
            rx=0,
            vs30=site_info.user_vs30,
        )

        cur_ds_site_db = classdef.Site(
            rrup=float(ds_rrup_mean_df.iloc[ix]),
            rjb=float(ds_rjb_mean_df.iloc[ix]),
            rx=0,
            vs30=site_info.vs30,
        )
        cur_ds_site_user = classdef.Site(
            rrup=float(ds_rrup_mean_df.iloc[ix]),
            rjb=float(ds_rjb_mean_df.iloc[ix]),
            rx=0,
            vs30=site_info.user_vs30,
        )

        # Run the empirical model for using the db and user specified vs30
        flt_im_db, _ = emp_factory.compute_gmm(
            cur_flt_fault,
            cur_flt_site_db,
            classdef.GMM.CB_14,
            str(im),
            period=im.period,
        )
        flt_im_user, _ = emp_factory.compute_gmm(
            cur_flt_fault,
            cur_flt_site_user,
            classdef.GMM.CB_14,
            str(im),
            period=im.period,
        )

        ds_im_db, _ = emp_factory.compute_gmm(
            cur_ds_fault, cur_ds_site_db, classdef.GMM.CB_14, str(im), period=im.period
        )
        ds_im_user, _ = emp_factory.compute_gmm(
            cur_ds_fault,
            cur_ds_site_user,
            classdef.GMM.CB_14,
            str(im),
            period=im.period,
        )

        # Compute the vs30 ratio
        flt_vs30_ratio.append(flt_im_user / flt_im_db)
        ds_vs30_ratio.append(ds_im_user / ds_im_db)

    # Compute the updated IM values
    flt_vs30_updated = im_values * np.asarray(flt_vs30_ratio)
    ds_vs30_updated = im_values * np.asarray(ds_vs30_ratio)

    # Interpolate to return data at the same IM levels
    flt_mask = ~np.isnan(flt_vs30_updated)
    flt_vs30_updated_excd = np.interp(
        im_values,
        flt_vs30_updated[flt_mask],
        hazard_result.fault_hazard.values[flt_mask],
        right=0.0,
    )
    flt_upd_hazard = pd.Series(index=im_values, data=flt_vs30_updated_excd)

    ds_mask = ~np.isnan(ds_vs30_updated)
    ds_vs30_updated_excd = np.interp(
        im_values,
        ds_vs30_updated[ds_mask],
        hazard_result.ds_hazard.values[ds_mask],
        right=0.0,
    )
    ds_upd_hazard = pd.Series(index=im_values, data=ds_vs30_updated_excd)

    return flt_upd_hazard, ds_upd_hazard
