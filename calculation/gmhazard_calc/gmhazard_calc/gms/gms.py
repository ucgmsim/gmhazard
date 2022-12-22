import time
from typing import Optional, Sequence, Dict, Tuple

import pandas as pd
import numpy as np
from scipy import stats

import sha_calc as sha
from gmhazard_calc.im import IM, IMType, to_im_list, to_string_list
from gmhazard_calc import gm_data
from gmhazard_calc import site
from gmhazard_calc import constants
from gmhazard_calc import hazard
from gmhazard_calc import shared
from gmhazard_calc import site_source
from gmhazard_calc import disagg
from gmhazard_calc import exceptions
from .GroundMotionDataset import GMDataset, HistoricalGMDataset
from .GMSResult import GMSResult
from .GCIMResult import BranchUniGCIM, IMEnsembleUniGCIM, SimUniGCIM
from .CausalParamBounds import CausalParamBounds

SF_LOW, SF_HIGH = 0.3, 10.0


def run_ensemble_gms(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    n_gms: int,
    IMj: IM,
    gm_dataset: GMDataset,
    IMs: np.ndarray,
    exceedance: float = None,
    im_j: float = None,
    n_replica: int = 10,
    im_weights: pd.Series = None,
    cs_param_bounds: CausalParamBounds = None,
    gms_id: str = None,
) -> GMSResult:
    """
    Performs ensemble based ground motion selection

    Parameters
    ----------
    ensemble: Ensemble
    site_info: SiteInfo
    n_gms: int
        Number of ground
    IMj: IM
        Conditioning IM
    gm_dataset: GMDataset
        The GM source (either simulations or historical) from which
        to select ground motions
    IMs: numpy array of strings
        The IMs to consider
    exceedance: float
        Exceedance of interest
        Either exceedance or im_j has to be specified
    im_j: float
        Level/Value of interest of the conditioning IM
    n_replica: int
        Number of times the GM selection process is repeated
    im_weights: Series
        Weighting of the IMs
    cs_param_bounds: CausalParamBounds
        The causal filter parameters to apply
        pre-ground motion selection

    Returns
    -------
    GMSResult
    """
    IMs = IMs[IMs != IMj]
    if im_weights is None:
        im_weights = default_IM_weights(IMj, IMs)

    # Sanity checks
    assert np.all(
        np.isin(to_string_list(IMs), im_weights.index)
    ), "IM weights are not specified for all IMs"

    assert np.isclose(np.sum(im_weights), 1.0), "IM weights need to sum to 1.0"
    ensemble.check_im(IMj)

    assert np.all(np.isin(IMs, ensemble.ims)), (
        f"Not all of the specified IM types are "
        f"available in the ensemble {ensemble.name}"
    )

    assert exceedance is not None or im_j is not None, (
        "Either the exceedance probability or the conditioning "
        "IM level has to be specified"
    )

    if exceedance is not None and im_j is not None:
        print(
            f"An exceedance level and a conditioning IM level were specified, "
            f"ignoring the exceedance level and using the conditioning IM"
        )
        exceedance = None

    # Compute ensemble hazard
    ens_hazard = hazard.run_ensemble_hazard(ensemble, site_info, IMj)
    if im_j is not None and not (
        ens_hazard.im_values.min() < im_j < ens_hazard.im_values.max()
    ):
        raise ValueError(
            "The specified conditioning IM value is not supported (too small or large)"
        )

    # Compute the conditioning IM level using the ensemble hazard
    if exceedance is not None:
        if not (
            ens_hazard.total_hazard.values.min()
            < exceedance
            < ens_hazard.total_hazard.values.max()
        ):
            raise ValueError(
                "The specified conditioning exceedance value is not supported (too small or large)"
            )
        im_j = ens_hazard.exceedance_to_im(exceedance)

    if ensemble.flt_im_data_type is constants.IMDataType.parametric:
        return _run_parametric_ensemble_gms(
            ensemble,
            site_info,
            n_gms,
            IMj,
            gm_dataset,
            IMs,
            im_j,
            exceedance=exceedance,
            n_replica=n_replica,
            im_weights=im_weights,
            cs_param_bounds=cs_param_bounds,
            gms_id=gms_id,
        )
    elif (
        ensemble.is_simple
        and ensemble.flt_im_data_type is constants.IMDataType.non_parametric
    ):
        return _run_non_parametric_ensemble_gms(
            ensemble,
            site_info,
            n_gms,
            IMj,
            gm_dataset,
            IMs,
            im_j,
            exceedance=exceedance,
            n_replica=n_replica,
            im_weights=im_weights,
            cs_param_bounds=cs_param_bounds,
            gms_id=gms_id,
        )
    else:
        raise NotImplementedError(
            "Hybrid ensembles are currently not supported for GMS"
        )


def _run_non_parametric_ensemble_gms(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    n_gms: int,
    IMj: IM,
    gm_dataset: GMDataset,
    IMs: np.ndarray,
    im_j: float,
    exceedance: float = None,
    n_replica: int = 10,
    im_weights: pd.Series = None,
    cs_param_bounds: CausalParamBounds = None,
    sigma_lnIMj: float = 0.05,
    gms_id: str = None,
) -> GMSResult:
    """Performs GMS based on a simulation ensemble

    Note: There are two simulation dataset used in this process,
    1) The simulations from the ensemble used to compute hazard and
        the non-parametric IMi|IMj distributions
    2) The simulation dataset (as given by gm_dataset) from
        which actual selection is performed
    They can obviously be the same, however are treated separately
    in this implementation
    """
    if cs_param_bounds is not None:
        raise ValueError(
            "Causal Parameters Bounds are not supported "
            "for non-parametric (site-specific) GMS"
        )

    n_ims = len(IMs)
    IMs_str = to_string_list(IMs)
    im_ensembles = list({ensemble.get_im_ensemble(IMi.im_type) for IMi in IMs})

    # Get the IMj im values for each simulation
    # from the ensemble, used to calculate IMi|IMj
    sim_lnIMj_df = (
        pd.concat(
            [
                shared.get_IM_values(
                    cur_branch.get_imdb_ffps(constants.SourceType.fault), site_info
                )
                for cur_branch in ensemble.get_im_ensemble(IMj.im_type).branches
            ]
        )[str(IMj)]
        .droplevel("fault")
        .apply(np.log)
    )

    # Get the IM values for the ground motions simulations to select from
    gm_lnIMi_df = gm_dataset.get_im_df(site_info, IMs_str, cs_param_bounds).apply(
        np.log
    )
    assert np.all(gm_lnIMi_df.columns == IMs_str)
    gm_lnIMj_df = gm_dataset.get_im_df(site_info, str(IMj), cs_param_bounds).apply(
        np.log
    )

    # Truncate
    n_trunc_sigmas = 3
    sim_lnIMj_df = sim_lnIMj_df.loc[
        (sim_lnIMj_df >= np.log(im_j) - n_trunc_sigmas * sigma_lnIMj)
        & (sim_lnIMj_df <= np.log(im_j) + n_trunc_sigmas * sigma_lnIMj)
    ]
    print(
        f"Number of simulation available to compute lnIMi|IMj: {sim_lnIMj_df.shape[0]}"
    )
    if sim_lnIMj_df.shape[0] < 20:
        raise exceptions.InsufficientNumberOfSimulationsError(
            IMj,
            f"{site_info} - IMj={IMj} - imj={im_j} - "
            f"Not enough simulations available to compute IMi|IMj accurately.",
        )

    # Relevant simulation ids
    sim_ids = sim_lnIMj_df.index.values.astype(str)

    # Compute alpha
    kernel = stats.norm(loc=np.log(im_j), scale=sigma_lnIMj)
    alpha = pd.Series(index=sim_lnIMj_df.index, data=kernel.pdf(sim_lnIMj_df.values))

    # Normalize
    alpha = alpha / alpha.sum()

    # Compute the IMi|IMj distributions
    sim_lnIMi_df = []
    IMi_gcims = {}
    for cur_im_ensemble in im_ensembles:
        cur_IMs = IMs[np.isin(IMs, cur_im_ensemble.ims)]

        # Retrieve the IM values
        # from the ensemble, used to calculate IMi|IMj
        cur_sim_lnIMi_df = (
            pd.concat(
                [
                    shared.get_IM_values(
                        cur_branch.get_imdb_ffps(constants.SourceType.fault),
                        site_info,
                        IMs=to_string_list(cur_IMs),
                    )
                    for cur_branch in cur_im_ensemble.branches
                ]
            )
            .droplevel("fault")
            .apply(np.log)
        )

        # Check that all required simulations exists
        assert np.all(
            np.isin(
                sim_lnIMj_df.index.values.astype(str),
                cur_sim_lnIMi_df.index.values.astype(str),
            )
        )

        # Drop any simulations that were truncated
        cur_sim_lnIMi_df = cur_sim_lnIMi_df.loc[sim_ids]
        sim_lnIMi_df.append(cur_sim_lnIMi_df)

        # Compute F_IMi|IMj for each IMi
        for cur_im in cur_IMs:
            cur_im_data_sorted = cur_sim_lnIMi_df[str(cur_im)].sort_values()
            cur_cdf_series = pd.Series(
                index=cur_im_data_sorted.values,
                data=np.cumsum(alpha.loc[cur_im_data_sorted.index].values),
            )

            cur_weighted_mean = np.sum(alpha * cur_sim_lnIMi_df[str(cur_im)])
            cur_weighted_std = np.sum(
                np.sqrt(
                    alpha * (cur_sim_lnIMi_df[str(cur_im)] - cur_weighted_mean) ** 2
                )
            )
            IMi_gcims[cur_im] = SimUniGCIM(
                ensemble,
                cur_im,
                IMj,
                im_j,
                sha.Uni_lnIMi_IMj(
                    cur_cdf_series,
                    str(cur_im),
                    str(IMj),
                    im_j,
                    mu=float(cur_weighted_mean),
                    sigma=float(
                        cur_weighted_std,
                    ),
                ),
            )

    sim_lnIMi_df = pd.concat(sim_lnIMi_df, axis=1)

    # Sanity check
    assert np.all(alpha.index == sim_lnIMi_df.index)

    # Compute equation 11 & 12 (from Bradley et al. 2015)
    weighted_mean = pd.DataFrame(
        index=sim_lnIMi_df.index,
        data=sim_lnIMi_df.values * alpha.values[:, np.newaxis],
        columns=sim_lnIMi_df.columns,
    )
    diff = sim_lnIMi_df - weighted_mean
    im_sigma = np.einsum(
        "p,pi,pk->ik", alpha, diff[IMs_str].values, diff[IMs_str].values
    )

    # Compute the correlations (equation 10)
    denominator = np.sqrt(
        np.diag(im_sigma)[:, np.newaxis] * np.diag(im_sigma)[:, np.newaxis].T
    )
    corr_matrix = im_sigma / denominator

    # Generate the realisations and
    # compute the misfits & replica score
    # (for each replica)
    rep_rel_lnIMi_dfs = []
    R_values, sel_gm_ind = [], []
    IMi_gcim_sigmas = pd.Series(
        {
            str(cur_im): cur_gcim.lnIMi_IMj.sigma
            for cur_im, cur_gcim in IMi_gcims.items()
        }
    )
    for replica_ix in range(n_replica):
        # Draw samples from MVN with covariance = correlation matrix
        mvn_samples = np.random.multivariate_normal(
            np.zeros(len(IMs)), corr_matrix, size=n_gms
        )

        # Transform to correlated vector of marginal uniform distribution
        U = np.full((n_gms, n_ims), fill_value=np.nan)
        for ix, cur_im in enumerate(IMs):
            U[:, ix] = stats.norm.cdf(mvn_samples[:, ix])
        U = pd.DataFrame(data=U, columns=IMs_str)

        # Transform to IM values
        cur_rel_im_values = np.full((n_gms, n_ims), fill_value=np.nan)
        for im_ix, cur_im in enumerate(IMs):
            cur_rel_im_values[:, im_ix] = sha.query_non_parametric_cdf_invs(
                U[str(cur_im)].values,
                IMi_gcims[cur_im].lnIMi_IMj.cdf.index.values,
                IMi_gcims[cur_im].lnIMi_IMj.cdf.values,
            )
        cur_rel_lnIMi_df = pd.DataFrame(data=cur_rel_im_values, columns=IMs_str)
        rep_rel_lnIMi_dfs.append(cur_rel_lnIMi_df)

        cur_diff = (
            cur_rel_lnIMi_df.values[
                :,
                np.newaxis,
                :,
            ]
            - gm_lnIMi_df.values
        )

        cur_misfit = pd.DataFrame(
            index=cur_rel_lnIMi_df.index,
            data=np.sum(
                im_weights.values
                * (cur_diff / IMi_gcim_sigmas.values[np.newaxis, np.newaxis, :]) ** 2,
                axis=2,
            ),
        )

        cur_selected_gms_ind = gm_lnIMi_df.index.values[
            cur_misfit.idxmin(axis=1).values
        ]

        D = ks_stats(
            IMs,
            gm_lnIMi_df.loc[cur_selected_gms_ind],
            {cur_key: cur_gcim.lnIMi_IMj for cur_key, cur_gcim in IMi_gcims.items()},
        )

        R_values.append(np.sum(im_weights * (D ** 2)))
        sel_gm_ind.append(list(cur_selected_gms_ind))

    # Only select from the replica which have number of unique GMs == n_gms, or
    # if there are none select from the set that has
    # number of unique GMs == max number of unique GMs
    # to prevent selection of duplicate GMs
    n_unique_gms = np.asarray(
        [np.count_nonzero(np.unique(cur_sel_gms_ind)) for cur_sel_gms_ind in sel_gm_ind]
    )
    filter_ind = np.flatnonzero(
        n_unique_gms == n_gms
        if np.any(n_unique_gms == n_gms)
        else n_unique_gms == n_unique_gms.max()
    )
    print(
        f"{gms_id} {site_info.station_name}:"
        f"{filter_ind.size} replica with {n_unique_gms.max()}"
        f" unique GMs (n_gms = {n_gms})"
    )

    # Select the best fitting set of ground motions (if multiple replica were run)
    selected_ix = np.argmin(R_values)
    gm_ind, rel_lnIMi_df = sel_gm_ind[selected_ix], rep_rel_lnIMi_dfs[selected_ix]

    return GMSResult(
        ensemble,
        site_info,
        IMj,
        im_j,
        IMs,
        pd.concat((gm_lnIMi_df.loc[gm_ind], gm_lnIMj_df.loc[gm_ind]), axis=1).apply(
            np.exp
        ),
        IMi_gcims,
        rel_lnIMi_df.apply(np.exp),
        gm_dataset,
        constants.GMSType.simulation,
        exceedance=exceedance,
    )


def _run_parametric_ensemble_gms(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    n_gms: int,
    IMj: IM,
    gm_dataset: HistoricalGMDataset,
    IMs: np.ndarray,
    im_j: float,
    exceedance: float = None,
    n_replica: int = 10,
    im_weights: pd.Series = None,
    cs_param_bounds: CausalParamBounds = None,
    gms_id: str = None,
) -> GMSResult:
    assert all(
        [
            ensemble.get_im_ensemble(IMi.im_type).im_data_type
            == constants.IMDataType.parametric
            for IMi in IMs
        ]
    ), "Currently only support GMS for fully parametric ensembles"

    IMs_str = to_string_list(IMs)

    # Compute the combined rupture weights
    P_Rup_IMj = sha.compute_rupture_weights(
        im_j,
        {
            cur_branch_name: (
                shared.get_IM_params(
                    IMj, cur_branch.get_imdb_ffps(constants.SourceType.fault), site_info
                ),
                cur_branch.flt_rupture_df.set_index("rupture_name").annual_rec_prob,
            )
            for cur_branch_name, cur_branch in ensemble.get_im_ensemble(
                IMj.im_type
            ).branches_dict.items()
        },
    )

    # Compute the adjusted branch weights
    IMj_adj_branch_weights, IMj_hazard_mean = shared.compute_adj_branch_weights(
        ensemble, IMj, im_j, site_info
    )

    # Combine & Apply the branch weights
    P_Rup_IMj = P_Rup_IMj.multiply(IMj_adj_branch_weights, axis=1).sum(axis=1)

    # Compute the correlation matrix
    rho = sha.compute_correlation_matrix(np.asarray(to_string_list(IMs)), str(IMj))

    # Get correlated vector
    v_vectors = sha.generate_correlated_vector(
        n_gms, np.asarray(to_string_list(IMs)), rho, n_replica=n_replica
    )

    # Pre-allocate the realisation IM value array (and array for
    # sigma of selected lnIMi|IMj,Rup distributions, required for residual calculation)
    rep_rel_lnIMi_data = [
        {IMi: np.full(n_gms, np.nan) for IMi in IMs} for ix in range(n_replica)
    ]
    rel_sigma_lnIMi_IMj_Rup = [
        {IMi: np.full(n_gms, np.nan) for IMi in IMs} for ix in range(n_replica)
    ]

    # Get list of ensembles that cover all IMi in IM vector (i.e. variable IMs)
    IMi_gcims = {}
    im_ensembles = list({ensemble.get_im_ensemble(IMi.im_type) for IMi in IMs})

    # Select the random ruptures to use for realisation generation
    # Shape: [N_GMs, N_Replica]
    rel_ruptures = np.random.choice(
        P_Rup_IMj.index.values.astype(str),
        size=n_gms * n_replica,
        replace=True,
        p=P_Rup_IMj.values,
    ).reshape((n_gms, n_replica))

    # Computation of GCIM distribution and random realisation generation
    # Overview of main steps:
    # Iterate over each IMEnsemble (i.e. IMi set) and compute
    # 1) Correlation coefficients
    # For each IMi in the IMi set:
    #   2) Branch hazard & mean hazard
    #   3) IMi value corresponding to exceedance of IMj=imj
    #   For each branch:
    #       4) Compute lnIMi|IMj,RUp and lnIMi|IMj
    #   5) Generate array of [n_gms, n_replica] random numbers
    #      between 0-1 for branch selection (same across IMi of
    #      the current IMi set)
    #   For each IMi in IMi set:
    #       6) Compute adjusted branch weights, using results from step 3)
    #       7) Compute combined (i.e. across branches) lnIMi|IMj
    #       For each replica_ix in n_replica:
    #           7) Select n_gms random branches using the adjusted
    #              branch weights for IMi
    #           For each of the selected branches / ruptures:
    #               8) Using current branch & rupture lnIMi|IMj,Rup
    #                  generate random realisation
    for cur_im_ensemble in im_ensembles:
        # Get the relevant IMi for this IMEnsemble
        cur_IMs = IMs[np.isin(IMs, cur_im_ensemble.ims)]

        # Get the correlation coefficients
        corr_coeffs = pd.Series(
            data=[sha.get_im_correlations(str(IMi), str(IMj)) for IMi in cur_IMs],
            index=to_string_list(cur_IMs),
        )

        # Compute the branch hazard for each of the current set of IMi
        cur_branch_hazard = {
            IMi: hazard.run_branches_hazard(ensemble, site_info, IMi) for IMi in cur_IMs
        }

        # Get the ensemble mean hazard IM value for each IMi (in the current set)
        # corresponding to the exceedance rate for IMj=imj
        # Needed to calculate the adjusted branch weight
        cur_ens_hazard = {
            IMi: hazard.run_ensemble_hazard(
                ensemble, site_info, IMi, branch_hazard=cur_branch_hazard[IMi]
            )
            for IMi in cur_IMs
        }
        cur_mean_hazard_im_values = pd.Series(
            data=[
                cur_ens_hazard[IMi].exceedance_to_im(IMj_hazard_mean) for IMi in cur_IMs
            ],
            index=cur_IMs,
        )

        cur_branch_gcims, cur_adj_branch_weights = {}, {}
        for cur_branch_name, cur_branch in cur_im_ensemble.branches_dict.items():
            # Retrieve the IM parameters
            im_df = shared.get_IM_values(
                cur_branch.get_imdb_ffps(constants.SourceType.fault), site_info
            )
            sigma_cols = [f"{IMi}_sigma" for IMi in cur_IMs]

            # Compute lnIMi|IMj, Rup
            cur_lnIMi_IMj_Rup = sha.compute_lnIMi_IMj_Rup(
                im_df[to_string_list(cur_IMs)],
                im_df[sigma_cols].rename(
                    columns={
                        sig_col: str(IMi) for sig_col, IMi in zip(sigma_cols, cur_IMs)
                    }
                ),
                corr_coeffs,
                str(IMj),
                im_j,
            )

            # Compute lnIMi|IMj
            cur_lnIMi_IMj = sha.compute_lnIMi_IMj(
                cur_lnIMi_IMj_Rup, P_Rup_IMj, str(IMj), im_j
            )

            # Create branch GCIM object and save to dictionary
            cur_branch_gcims[cur_branch_name] = {
                IMi: BranchUniGCIM(
                    IMi,
                    IMj,
                    im_j,
                    cur_branch,
                    cur_lnIMi_IMj_Rup[str(IMi)],
                    cur_lnIMi_IMj[str(IMi)],
                )
                for IMi in cur_IMs
            }

        # Pick N_gms random numbers, to select the branches for
        # realisation generation
        # Use the same random number for each IMi in the current set
        # to ensure consistent branch/model selection
        rand_branch_float = np.random.uniform(
            low=0.0, high=1.0, size=(n_gms, n_replica)
        )

        # Combine the branch lnIMi|IMj distributions for each of the current IMs
        # and generate random realisation
        cur_branch_names = np.asarray(list(cur_im_ensemble.branches_dict.keys()))
        for IMi in cur_IMs:
            # Compute the adjusted branch weights, using the
            # ensemble mean exceedance rate for IMj=imj and
            # the corresponding ensemble hazard mean IM value (for each IMi)
            cur_adj_branch_weights[IMi] = pd.Series(
                data=[
                    hazard.run_branch_hazard(
                        cur_branch, site_info, IMi
                    ).im_to_exceedance(cur_mean_hazard_im_values[IMi])
                    * cur_branch.weight
                    / IMj_hazard_mean
                    for cur_name, cur_branch in cur_im_ensemble.branches_dict.items()
                ],
                index=cur_branch_names,
            )

            # Combine the branches lnIMi|IMj to get
            # the target distribution for IMi
            comb_lnIMi_IMj = sha.comb_lnIMi_IMj(
                {
                    cur_name: cur_branch_gcim[IMi].lnIMi_IMj
                    for cur_name, cur_branch_gcim in cur_branch_gcims.items()
                },
                cur_adj_branch_weights[IMi],
            )
            IMi_gcims[IMi] = IMEnsembleUniGCIM(
                cur_im_ensemble,
                IMi,
                IMj,
                im_j,
                comb_lnIMi_IMj,
                {
                    cur_branch_name: cur_data[IMi]
                    for cur_branch_name, cur_data in cur_branch_gcims.items()
                },
            )

            # Generate realisation for current IMi,
            # 1) select random branch
            # 2) select random rupture
            # 3) Apply the mean & sigma of the selected lnIMi|IMj,Rup to the
            #    vector of correlated random numbers
            for replica_ix in range(n_replica):
                cur_branch_cdf = cur_adj_branch_weights[IMi].sort_values().cumsum()

                # Ensure it goes to exactly 1.0, to prevent any issues
                # (as rand_branch_float can go to 1.0)
                assert np.isclose(cur_branch_cdf.iloc[-1], 1.0, rtol=1e-3)
                cur_branch_cdf.iloc[-1] = 1.0

                # Select n_gms random branches based on IMi adjusted branch weights
                cur_sel_branches = sha.query_non_parametric_cdf_invs(
                    rand_branch_float[:, replica_ix],
                    cur_branch_cdf.index.values.astype(str),
                    cur_branch_cdf.values,
                )
                for rel_ix, (cur_branch_name, cur_rupture) in enumerate(
                    zip(cur_sel_branches, rel_ruptures[:, replica_ix])
                ):
                    # Apply mean & sigma of selected lnIMi|IMj,Rup to
                    # to correponding value of correlated vector
                    cur_branch_gcim = cur_branch_gcims[cur_branch_name][IMi]
                    rep_rel_lnIMi_data[replica_ix][IMi][rel_ix] = (
                        cur_branch_gcim.lnIMi_IMj_Rup.mu[cur_rupture]
                        + cur_branch_gcim.lnIMi_IMj_Rup.sigma[cur_rupture]
                        * v_vectors[replica_ix].loc[rel_ix, str(IMi)]
                    )
                    rel_sigma_lnIMi_IMj_Rup[replica_ix][IMi][
                        rel_ix
                    ] = cur_branch_gcim.lnIMi_IMj_Rup.sigma[cur_rupture]

    # Convert results to dataframes (one per replica)
    rep_rel_lnIMi_data = [
        pd.DataFrame(
            {str(cur_key): cur_value for cur_key, cur_value in cur_values.items()}
        )
        for cur_values in rep_rel_lnIMi_data
    ]
    rel_sigma_lnIMi_IMj_Rup = [
        pd.DataFrame(
            {str(cur_key): cur_value for cur_key, cur_value in cur_sigma_values.items()}
        )
        for cur_sigma_values in rel_sigma_lnIMi_IMj_Rup
    ]

    # Get the (scaled) ground motions IM values that fall
    # within the specified causal parameter bounds
    gm_IMj_df = gm_dataset.get_im_df(
        site_info,
        str(IMj),
        cs_param_bounds=cs_param_bounds,
    )
    sf = sha.compute_scaling_factor(gm_IMj_df.squeeze(), str(IMj), im_j)
    gm_lnIM_df = gm_dataset.get_im_df(
        site_info,
        IMs_str + [str(IMj)],
        cs_param_bounds=cs_param_bounds,
        sf=sf
    ).apply(np.log)
    assert np.all(np.isclose(gm_lnIM_df[str(IMj)], np.log(im_j)))

    # Sanity check
    assert (
        gm_lnIM_df.shape[0] > 0
    ), "No GMs to select from after applying the causual parameter bounds"
    assert np.allclose(gm_lnIM_df.loc[:, str(IMj)], np.log(im_j))

    print(
        f"{gms_id} {site_info.station_name}:\nPool of available GMs: {gm_lnIM_df.shape[0]}"
    )

    # Compute residuals and select GMs for each replica
    R_values, sel_gm_ind = [], []
    for replica_ix in range(n_replica):
        # Compute residuals between available GMs and current set of realisations
        cur_sigma_lnIMi_Rup_IMj = (
            rel_sigma_lnIMi_IMj_Rup[replica_ix].loc[:, IMs_str].values[:, np.newaxis, :]
        )
        cur_diff = (
            rep_rel_lnIMi_data[replica_ix]
            .loc[:, IMs_str]
            .values[:, np.newaxis, :]
            - gm_lnIM_df.loc[:, IMs_str].values
        )
        cur_misfit = pd.DataFrame(
            index=rep_rel_lnIMi_data[replica_ix].index,
            data=np.sum(
                im_weights.loc[to_string_list(IMs)].values
                * (cur_diff / cur_sigma_lnIMi_Rup_IMj) ** 2,
                axis=2,
            ),
        )

        # Select best matching GMs
        cur_selected_gms_ind = gm_lnIM_df.index.values[cur_misfit.idxmin(axis=1).values]

        # Compute the KS test statistic for each IM_i
        # I.e. Check how well the empirical distribution of selected GMs
        # matches with the target distribution (i.e. lnIMi|IMj)
        D = ks_stats(
            IMs,
            gm_lnIM_df.loc[cur_selected_gms_ind],
            {cur_IMi: cur_gcim.lnIMi_IMj for cur_IMi, cur_gcim in IMi_gcims.items()},
        )

        # Compute the overall residual & save selected ground motions
        R_values.append(np.sum(im_weights * (D ** 2)))
        sel_gm_ind.append(list(cur_selected_gms_ind))

    # Free memory, as these can be large if the
    # pool of available GMs is large
    del cur_diff
    del cur_misfit

    # Only select from the replica which have number of unique GMs == n_gms, or
    # if there are none select from the set that has
    # number of unique GMs == max number of unique GMs
    # to prevent selection of duplicate GMs
    n_unique_gms = np.asarray(
        [np.count_nonzero(np.unique(cur_sel_gms_ind)) for cur_sel_gms_ind in sel_gm_ind]
    )
    filter_ind = np.flatnonzero(
        n_unique_gms == n_gms
        if np.any(n_unique_gms == n_gms)
        else n_unique_gms == n_unique_gms.max()
    )
    print(
        f"{gms_id} {site_info.station_name}:"
        f"{filter_ind.size} replica with {n_unique_gms.max()}"
        f" unique GMs (n_gms = {n_gms}"
    )

    # Select the best fitting set of ground motions (if multiple replica were run)
    selected_ix = np.argmin(R_values)
    gm_ind, rel_lnIMi_df = sel_gm_ind[selected_ix], rep_rel_lnIMi_data[selected_ix]

    return GMSResult(
        ensemble,
        site_info,
        IMj,
        im_j,
        IMs,
        gm_lnIM_df.loc[gm_ind].apply(np.exp),
        IMi_gcims,
        rel_lnIMi_df.apply(np.exp),
        gm_dataset,
        constants.GMSType.empirical,
        cs_param_bounds=cs_param_bounds,
        sf=sf,
        exceedance=exceedance,
    )


def ks_stats(
    IMs: Sequence[IM],
    gms_im_df: pd.DataFrame,
    IMi_gcims: Dict[IM, sha.Uni_lnIMi_IMj],
):
    """
    Compute the KS test statistic for each IM_i
    Check how well the empirical distribution of selected GMs
    matches with the target distribution (i.e. lnIMi|IMj)

    Parameters
    ----------
    IMs: sequence of IMs
    gms_im_df: dataframe
        IM values of the selected GMs
    IMi_gcims:
        The univariate non-parametric IMi|IMj
        distributions

    Returns
    -------

    """
    D = []
    for IMi in IMs:
        cur_d, _ = stats.kstest(
            gms_im_df[str(IMi)].values,
            lambda x: sha.query_non_parametric_cdf(
                x,
                IMi_gcims[IMi].cdf.index.values,
                IMi_gcims[IMi].cdf.values,
            ),
        )
        D.append(cur_d)
    return pd.Series(index=to_string_list(IMs), data=D)


def default_IM_weights(IM_j: IM, IMs: np.ndarray) -> pd.Series:
    """
    Returns the default IM weights based on the conditioning IM

    If the conditioning IM (IM_j) is spectral acceleration (SA) the
    weighting is 70% across the SAs and 30% across all other IMs

    Otherwise a uniform weighting distribution is used


    Parameters
    ----------
    IM_j: IM
        Conditioning IM
    IMs: list of IM
        IM types for which to get the default weights

    Returns
    -------
    im_weights: pandas series
        Weigths for the specified IM types
    """
    # Use 70% (SA) / 30% (other) weighting if
    # conditioning IM is SA
    if IM_j.is_pSA():
        pSA_mask = np.asarray([cur_im.im_type is IMType.pSA for cur_im in IMs])
        n_pSA_IMs = np.count_nonzero(pSA_mask)
        n_other_IMs = IMs.size - n_pSA_IMs

        if n_other_IMs == 0:
            im_weights = np.ones(n_pSA_IMs, dtype=float) / n_pSA_IMs
        else:
            im_weights = np.full(IMs.size, np.nan)
            im_weights[pSA_mask] = (1.0 / n_pSA_IMs) * 0.7
            im_weights[~pSA_mask] = (1.0 / n_other_IMs) * 0.3

    # Otherwise, default to uniform weighting
    else:
        print(
            f"WARNING: Defaulting to uniform IM weighting as the "
            f"conditioning is not SA."
        )
        im_weights = np.ones(IMs.size, dtype=float) / IMs.size

    return pd.Series(data=im_weights, index=to_string_list(IMs))


def default_causal_params(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    IM_j: IM,
    exceedance: Optional[float] = None,
    im_value: Optional[float] = None,
    disagg_data: Optional[disagg.EnsembleDisaggResult] = None,
    sf_bounds: Tuple[float, float] = None,
) -> CausalParamBounds:
    """
    Computes default causal parameters based on

    "Tarbali, K. and Bradley, B.A., 2016.
    The effect of causal parameter bounds in PSHA‐based ground motion selection."

    Using criterion AC (Table III)


    Parameters
    ----------
    ensemble: Ensemble
    site_info: SiteInfo
    IM_j: IM
        Conditioning IM
    exceedance : float, optional
        Compute disagg at this exceedance, either the exceedance
        or the im_value parameter has to be given
    im_value: float, optional
        Compute disagg at this im value if required
    disagg_data: DisaggResult, optinal
        Computed Disagg data if pre-calculated

    Returns
    -------
    Magnitude bounds: pair of floats
        (Mw lower bound, Mw upper bound)
    Rrup bounds: pair of floats
        (Rrup lower bound, Rrup upper bound)
    Vs30 bounds: pair of floats
        (Vs30 lower bound, Vs30 upper bound)
    """
    # Calculate disagg if not already specified
    if disagg_data is None:
        disagg_data = disagg.run_ensemble_disagg(
            ensemble,
            site_info,
            IM_j,
            exceedance=exceedance,
            im_value=im_value,
            calc_mean_values=True,
        )

    if sf_bounds is None:
        sf_bounds = (SF_LOW, SF_HIGH)

    # Vs30 bounds
    vs_low, vs_high = site_info.vs30 * 0.5, site_info.vs30 * 1.5

    contr_df = pd.concat(
        (
            disagg_data.fault_disagg_id.contribution,
            disagg_data.ds_disagg_id.contribution,
        )
    )

    # Mw bounds
    contr_df = pd.merge(
        contr_df.to_frame("contribution"),
        ensemble.rupture_df_id.magnitude.to_frame("magnitude"),
        how="left",
        left_index=True,
        right_index=True,
    ).sort_values("magnitude")
    non_nan_mask = ~contr_df.magnitude.isna()
    mw_low = min(
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.01]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.1]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        - 0.5,
    )
    mw_high = max(
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.99]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.90]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        + 0.5,
    )

    # Get distances
    fault_rrup_disagg_df = site_source.match_ruptures(
        site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info),
        disagg_data.fault_disagg_id.contribution.copy(),
        constants.SourceType.fault,
    )
    ds_rrup_disagg_df = site_source.match_ruptures(
        site_source.get_distance_df(ensemble.ds_ssddb_ffp, site_info),
        disagg_data.ds_disagg_id.contribution.copy(),
        constants.SourceType.distributed,
    )
    contr_df = pd.merge(
        contr_df,
        pd.concat([fault_rrup_disagg_df.rrup, ds_rrup_disagg_df.rrup], axis=0).to_frame(
            "rrup"
        ),
        how="left",
        left_index=True,
        right_index=True,
    ).sort_values("rrup")
    non_nan_mask = ~contr_df.rrup.isna()
    # Rrup bounds
    rrup_low = min(
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.01]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.1]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        * 0.5,
    )
    rrup_high = max(
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.99]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha.query_non_parametric_cdf_invs(
            np.asarray([0.90]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        * 1.5,
    )

    return CausalParamBounds(
        ensemble,
        site_info,
        IM_j,
        (mw_low, mw_high),
        (rrup_low, rrup_high),
        (vs_low, vs_high),
        sf_bounds=sf_bounds,
        contr_df=contr_df,
        exceedance=exceedance,
        im_value=im_value,
    )
