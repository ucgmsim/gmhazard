"""Contains functions that are used by both the coreAPI and projectAPI for responses"""
import base64
from typing import Sequence

import pandas as pd

import gmhazard_calc as sc


def get_ensemble_hazard_response(
    ensemble_hazard: sc.hazard.EnsembleHazardResult, download_token: str
):
    """Creates the response for both core and project API"""
    return {
        "ensemble_id": ensemble_hazard.ensemble.name,
        "station": ensemble_hazard.site.station_name,
        "im": str(ensemble_hazard.im),
        "im_component": str(ensemble_hazard.im.component),
        "ensemble_hazard": ensemble_hazard.as_json_dict(),
        "branches_hazard": {
            branch_hazard.branch.name: branch_hazard.as_json_dict()
            for branch_hazard in ensemble_hazard.branch_hazard
        },
        "download_token": download_token,
    }


def get_ensemble_disagg(
    ensemble_disagg: Sequence[sc.disagg.EnsembleDisaggResult],
    metadata_df: Sequence[pd.DataFrame],
    src_png_data: Sequence[str],
    eps_png_data: Sequence[str],
    rps: Sequence[int],
    download_token: str,
):
    """Creates the response for both core and project API"""
    return {
        "ensemble_id": ensemble_disagg[0].ensemble.name,
        "station": {
            rps[idx]: ensemble.site_info.station_name
            for idx, ensemble in enumerate(ensemble_disagg)
        },
        "im": str(ensemble_disagg[0].im),
        "im_component": str(ensemble_disagg[0].im.component),
        "disagg_data": {
            rps[idx]: ensemble.to_dict(total_only=True)
            for idx, ensemble in enumerate(ensemble_disagg)
        },
        "extra_info": {
            rps[idx]: metadata.to_dict() for idx, metadata in enumerate(metadata_df)
        },
        "gmt_plot_src": {
            rps[idx]: base64.b64encode(src_png).decode()
            for idx, src_png in enumerate(src_png_data)
        },
        "gmt_plot_eps": {
            rps[idx]: base64.b64encode(eps_png).decode()
            for idx, eps_png in enumerate(eps_png_data)
        },
        "download_token": download_token,
    }


def get_ensemble_gms(
    gms_result: sc.gms.GMSResult,
    download_token: str,
    disagg_data: sc.disagg.EnsembleDisaggResult,
    site: str,
):
    """Creates the response for both the core and Project API"""
    return {
        "IMs": [str(im) for im in list(gms_result.IMs)],
        "IM_j": str(gms_result.IM_j),
        "im_j": gms_result.im_j,
        "gcim_cdf_x": {
            str(IMi): list(
                gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.index.values.astype(float)
            )
            for IMi in gms_result.IMs
        },
        "gcim_cdf_y": {
            str(IMi): list(gms_result.IMi_gcims[IMi].lnIMi_IMj.cdf.values.astype(float))
            for IMi in gms_result.IMs
        },
        "ks_bounds": gms_result.metadata_dict["ks_bounds"],
        "realisations": {
            str(key): value
            for key, value in gms_result.realisations.to_dict(orient="list").items()
        },
        "selected_GMs": {
            str(key): value
            for key, value in gms_result.selected_gms_im_df.to_dict(
                orient="list"
            ).items()
        },
        "selected_gms_metadata": {
            **gms_result.selected_gms_metdata_df.to_dict(orient="list"),
            **gms_result.selected_gms_im_16_84_df.to_dict(orient="list"),
            **gms_result.metadata_dict,
        },
        "download_token": download_token,
        "disagg_mean_values": disagg_data.mean_values.to_dict(),
        "gm_dataset_metadata": gms_result.gm_dataset.get_metadata_df(site).to_dict(
            orient="list"
        ),
        "n_gms_in_bounds": gms_result.gm_dataset.get_n_gms_in_bounds(
            gms_result.gm_dataset.get_metadata_df(site), gms_result.cs_param_bounds
        ),
    }


def get_default_causal_params(cs_param_bounds: sc.gms.CausalParamBounds):
    """Creates the response for both the core and Project API"""
    return {
        "mw_low": cs_param_bounds.mw_low,
        "mw_high": cs_param_bounds.mw_high,
        "rrup_low": cs_param_bounds.rrup_low,
        "rrup_high": cs_param_bounds.rrup_high,
        "vs30_low": cs_param_bounds.vs30_low,
        "vs30_high": cs_param_bounds.vs30_high,
        "contribution_df": cs_param_bounds.contr_df.to_dict("list")
        if cs_param_bounds.contr_df is not None
        else None,
    }


def get_ensemble_uhs(
    uhs_results: Sequence[sc.uhs.EnsembleUHSResult], download_token: str
):
    """Creates the response for both the core and Project API"""
    return {
        "ensemble_id": uhs_results[0].ensemble.name,
        "station": uhs_results[0].site_info.station_name,
        "uhs_results": {result.exceedance: result.to_dict() for result in uhs_results},
        "branch_uhs_results": None
        if uhs_results[0].branch_uhs is None
        else {result.exceedance: result.branch_uhs_dict() for result in uhs_results},
        "uhs_df": sc.uhs.EnsembleUHSResult.combine_results(uhs_results).to_dict(),
        "download_token": download_token,
    }


def get_ensemble_scenario_response(
    ensemble_scenario: sc.scenario.EnsembleScenarioResult, download_token: str
):
    """Creates the response for both core and project API"""
    return {
        "ensemble_scenario": ensemble_scenario.to_dict(),
        "download_token": download_token,
    }
