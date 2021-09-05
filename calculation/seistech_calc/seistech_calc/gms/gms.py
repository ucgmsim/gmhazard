from typing import Optional, List, Sequence

import pandas as pd
import numpy as np
from scipy import stats

import sha_calc as sha_calc
from seistech_calc.im import IM, IMType, to_im_list, to_string_list
from seistech_calc import gm_data
from seistech_calc import site
from seistech_calc import constants
from seistech_calc import hazard
from seistech_calc import shared
from seistech_calc import site_source
from seistech_calc import disagg
from .GroundMotionDataset import GMDataset, HistoricalGMDataset
from .GMSResult import GMSResult
from .GCIMResult import BranchUniGCIM, IMEnsembleUniGCIM
from .CausalParamBounds import CausalParamBounds

SF_LOW, SF_HIGH = 0.3, 3.0


def run_ensemble_gms(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    n_gms: int,
    IMj: IM,
    gm_dataset: GMDataset,
    IMs: np.ndarray = None,
    exceedance: float = None,
    im_j: float = None,
    n_replica: int = 10,
    im_weights: pd.Series = None,
    cs_param_bounds: CausalParamBounds = None,
) -> GMSResult:
    """
    Performs ensemble based ground motion selection

    Note: Currently only supports Ensembles based on
    empirical GMMs (i.e. parametric)

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
    # Use all available IMs if none are specified
    if IMs is None:
        IMs = np.asarray(list(set(ensemble.ims.copy()).intersection(gm_dataset.ims)))

    IMs = IMs[IMs != IMj]
    if im_weights is None:
        im_weights = default_IM_weights(IMj, IMs)
    else:
        im_weights.index = to_im_list(im_weights.index)

    # Sanity checks
    assert np.all(
        np.isin(IMs, im_weights.index)
    ), "IM weights are not specified for all IMs"
    assert np.isclose(np.sum(im_weights), 1.0), "IM weights need to sum to 1.0"
    ensemble.check_im(IMj)

    assert np.all(
        np.isin(IMs, ensemble.ims)
    ), f"Not all of the specified IM types are availble in the ensemble {ensemble.name}"
    assert exceedance is not None or im_j is not None, (
        "Either the exceedance probability or the conditioning "
        "IM level has to be specified"
    )
    assert all(
        [
            ensemble.get_im_ensemble(IMi.im_type).im_data_type
            == constants.IMDataType.parametric
            for IMi in IMs
        ]
    ), "Currently only support GMS for fully parametric ensembles"

    if exceedance is not None and im_j is not None:
        print(
            f"An exceedance level and a conditioning IM level were specified, "
            f"ignoring the exceedance level and using the conditioning IM"
        )
        exceedance = None

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

    # Compute the combined rupture weights
    P_Rup_IMj = sha_calc.compute_rupture_weights(
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
    rho = sha_calc.compute_correlation_matrix(np.asarray(to_string_list(IMs)), str(IMj))

    # Get correlated vector
    v_vectors = sha_calc.generate_correlated_vector(
        n_gms, np.asarray(to_string_list(IMs)), rho, n_replica=n_replica
    )

    # Pre-allocate the realisation IM value array (and array for
    # sigma of selected lnIMi|IMj,Rup distributions, required for residual calculation)
    rel_IM_values = [
        {IMi: np.full(n_gms, np.nan) for IMi in IMs} for ix in range(n_replica)
    ]
    rel_sigma_lnIMi_IMj_Rup = [
        {IMi: np.full(n_gms, np.nan) for IMi in IMs} for ix in range(n_replica)
    ]

    # Get list of ensembles that cover all IMi in IM vector (i.e. variable IMs)
    IMi_gcims = {}
    im_ensembles = list({ensemble.get_im_ensemble(IMi.im_type) for IMi in IMs})

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
    #           For each of the selected branches:
    #               8) Select random rupture using rupture weights (at IMj=imj)
    #               9) Using current branch & rupture lnIMi|IMj,Rup
    #                  generate random realisation
    for cur_im_ensemble in im_ensembles:
        # Get the relevant IMi for this IMEnsemble
        cur_IMs = IMs[np.isin(IMs, cur_im_ensemble.ims)]

        # Get the correlation coefficients
        corr_coeffs = pd.Series(
            data=[sha_calc.get_im_correlations(str(IMi), str(IMj)) for IMi in cur_IMs],
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
            cur_lnIMi_IMj_Rup = sha_calc.compute_lnIMi_IMj_Rup(
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
            cur_lnIMi_IMj = sha_calc.compute_lnIMi_IMj(
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
            comb_lnIMi_IMj = sha_calc.comb_lnIMi_IMj(
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
                # Select n_gms random branches based on IMi adjusted branch weights
                cur_branch_cdf = cur_adj_branch_weights[IMi].sort_values().cumsum()
                cur_sel_branches = sha_calc.query_non_parametric_cdf_invs(
                    rand_branch_float[:, replica_ix],
                    cur_branch_cdf.index.values.astype(str),
                    cur_branch_cdf.values,
                )
                for rel_ix, cur_branch_name in enumerate(cur_sel_branches):
                    # Select random rupture based on rupture contributions at IMj=imj
                    cur_rupture = np.random.choice(
                        P_Rup_IMj.index.values.astype(str), size=1, p=P_Rup_IMj.values
                    )[0]

                    # Apply mean & sigma of selected lnIMi|IMj,Rup to
                    # to correponding value of correlated vector
                    cur_branch_gcim = cur_branch_gcims[cur_branch_name][IMi]
                    rel_IM_values[replica_ix][IMi][rel_ix] = (
                        cur_branch_gcim.lnIMi_IMj_Rup.mu[cur_rupture]
                        + cur_branch_gcim.lnIMi_IMj_Rup.sigma[cur_rupture]
                        * v_vectors[replica_ix].loc[rel_ix, str(IMi)]
                    )
                    rel_sigma_lnIMi_IMj_Rup[replica_ix][IMi][
                        rel_ix
                    ] = cur_branch_gcim.lnIMi_IMj_Rup.sigma[cur_rupture]

    # Convert results to dataframes (one per replica)
    rel_IM_values = [pd.DataFrame(cur_values) for cur_values in rel_IM_values]
    rel_sigma_lnIMi_IMj_Rup = [
        pd.DataFrame(cur_sigma_values) for cur_sigma_values in rel_sigma_lnIMi_IMj_Rup
    ]

    # IM scaling, such that IM_j=im_j for all
    # ground motions in the GM dataset
    sf = None
    if isinstance(gm_dataset, HistoricalGMDataset):
        sf = gm_dataset.compute_scaling_factor(IMj, im_j)

    # Get the (scaled) ground motions IM values that fall
    # within the specified causal parameter bounds
    gms_im_df = gm_dataset.get_im_df(
        site_info,
        np.concatenate((to_string_list(IMs), [str(IMj)])),
        cs_param_bounds=cs_param_bounds,
        sf=sf,
    )
    gms_im_df.columns = to_im_list(gms_im_df.columns)
    assert (
        gms_im_df.shape[0] > 0
    ), "No GMs to select from after applying the causual parameter bounds"
    assert np.allclose(gms_im_df.loc[:, IMj], im_j)

    # Compute residuals and select GMs for each replica
    R_values, sel_gms_ind = [], []
    for replica_ix in range(n_replica):
        # Compute residuals between available GMs and current set of realisations
        cur_sigma_IMi_Rup_IMj = (
            rel_sigma_lnIMi_IMj_Rup[replica_ix].loc[:, IMs].values[:, np.newaxis, :]
        )
        cur_diff = rel_IM_values[replica_ix].loc[:, IMs].values[
            :, np.newaxis, :
        ] - np.log(gms_im_df.loc[:, IMs].values)
        cur_misfit = pd.DataFrame(
            index=rel_IM_values[replica_ix].index,
            data=np.sum(
                im_weights.loc[IMs].values * (cur_diff / cur_sigma_IMi_Rup_IMj) ** 2,
                axis=2,
            ),
        )

        # Select best matching GMs
        cur_selected_gms_ind = gms_im_df.index.values[cur_misfit.idxmin(axis=1).values]

        # Compute the KS test statistic for each IM_i
        # I.e. Check how well the empirical distribution of selected GMs
        # matches with the target distribution (i.e. lnIMi|IMj)
        D = []
        for IMi in IMs:
            cur_d, _ = stats.kstest(
                gms_im_df.loc[cur_selected_gms_ind, IMi].values,
                lambda x: sha_calc.query_non_parametric_cdf(
                    x,
                    IMi_gcims[IMi].lnIMi_IMj.cdf.index.values,
                    IMi_gcims[IMi].lnIMi_IMj.cdf.values,
                ),
            )
            D.append(cur_d)
        D = pd.Series(index=IMs, data=D)

        # Compute the overall residual & save selected ground motions
        R_values.append(np.sum(im_weights * (D ** 2)))
        sel_gms_ind.append(list(cur_selected_gms_ind))

    # Select the best fitting set of ground motions (if multiple replica were run)
    selected_ix = np.argmin(R_values)
    sel_gms_ind, rel_IM_values = sel_gms_ind[selected_ix], rel_IM_values[selected_ix]

    return GMSResult(
        ensemble,
        site_info,
        IMj,
        im_j,
        IMs,
        gms_im_df.loc[sel_gms_ind],
        IMi_gcims,
        rel_IM_values.apply(np.exp),
        gm_dataset,
        cs_param_bounds,
        sf=sf,
    )


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

    return pd.Series(data=im_weights, index=IMs)


def default_causal_params(
    ensemble: gm_data.Ensemble,
    site_info: site.SiteInfo,
    IM_j: IM,
    exceedance: Optional[float] = None,
    im_value: Optional[float] = None,
    disagg_data: Optional[disagg.EnsembleDisaggData] = None,
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
    disagg_data: DisaggData, optinal
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

    # Vs30 bounds
    vs_low, vs_high = site_info.vs30 * 0.5, site_info.vs30 * 1.5

    contr_df = pd.concat(
        (disagg_data.fault_disagg.contribution, disagg_data.ds_disagg.contribution)
    )

    # Mw bounds
    contr_df = pd.merge(
        contr_df.to_frame("contribution"),
        ensemble.rupture_df.magnitude.to_frame("magnitude"),
        how="left",
        left_index=True,
        right_index=True,
    ).sort_values("magnitude")
    non_nan_mask = ~contr_df.magnitude.isna()
    mw_low = min(
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.01]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.1]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        - 0.5,
    )
    mw_high = max(
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.99]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.90]),
            contr_df.magnitude.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        + 0.5,
    )

    # Get distances
    fault_rrup_disagg_df = site_source.match_ruptures(
        site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info),
        disagg_data.fault_disagg.contribution.copy(),
        constants.SourceType.fault,
    )
    ds_rrup_disagg_df = site_source.match_ruptures(
        site_source.get_distance_df(ensemble.ds_ssddb_ffp, site_info),
        disagg_data.ds_disagg.contribution.copy(),
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
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.01]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.1]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0]
        * 0.5,
    )
    rrup_high = max(
        sha_calc.query_non_parametric_cdf_invs(
            np.asarray([0.99]),
            contr_df.rrup.values[non_nan_mask],
            contr_df.contribution.cumsum().values[non_nan_mask],
        )[0],
        sha_calc.query_non_parametric_cdf_invs(
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
        sf_bounds=(SF_LOW, SF_HIGH),
        contr_df=contr_df,
        exceedance=exceedance,
        im_value=im_value,
    )
