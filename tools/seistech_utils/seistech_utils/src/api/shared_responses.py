"""Contains functions that are used by both the coreAPI and projectAPI for responses"""
import os
import zipfile
from typing import Dict, Sequence

import flask
import pandas as pd

import seistech_calc as sc


def get_ensemble_hazard_response(
    ensemble_hazard: sc.hazard.EnsembleHazardResult, download_token: str
):
    """ Creates the response for both core and project API"""
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
    ensemble_disagg: sc.disagg.EnsembleDisaggData,
    metadata_df: pd.DataFrame,
    src_png_data: str,
    eps_png_data: str,
    download_token: str,
):
    """ Creates the response for both core and project API"""
    return {
        "ensemble_id": ensemble_disagg.ensemble.name,
        "station": ensemble_disagg.site_info.station_name,
        "im": str(ensemble_disagg.im),
        "im_component": str(ensemble_disagg.im.component),
        "disagg_data": ensemble_disagg.to_dict(total_only=True),
        "extra_info": metadata_df.to_dict(),
        "gmt_plot_src": src_png_data,
        "gmt_plot_eps": eps_png_data,
        "download_token": download_token,
    }


def get_ensemble_gms(
    gms_result: sc.gms.GMSResult,
    download_token: str,
    disagg_data: sc.disagg.EnsembleDisaggData,
    site: str,
):
    """ Creates the response for both the core and Project API"""
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


def download_gms_result(gms_result: sc.gms.GMSResult, app: flask.app, tmp_dir: str):
    """ Create the zip for the core and project API responses"""
    missing_waveforms = gms_result.gm_dataset.get_waveforms(
        gms_result.selected_gms_ids, gms_result.site_info, tmp_dir
    )
    if len(missing_waveforms) > 0:
        app.logger.info(
            f"Failed to find waveforms for simulations: {missing_waveforms}"
        )

    zip_ffp = os.path.join(
        tmp_dir,
        f"{gms_result.ensemble.name}_{gms_result.IM_j.file_format()}_{gms_result.gm_dataset.name}_waveforms.zip",
    )
    with zipfile.ZipFile(zip_ffp, mode="w") as cur_zip:
        for cur_file in os.listdir(tmp_dir):
            if cur_file != os.path.basename(zip_ffp):
                cur_zip.write(
                    os.path.join(tmp_dir, cur_file),
                    arcname=os.path.basename(cur_file),
                )
    return zip_ffp


def get_default_causal_params(cs_param_bounds: sc.gms.CausalParamBounds):
    """ Creates the response for both the core and Project API"""
    return {
        "mw_low": cs_param_bounds.mw_low,
        "mw_high": cs_param_bounds.mw_high,
        "rrup_low": cs_param_bounds.rrup_low,
        "rrup_high": cs_param_bounds.rrup_high,
        "vs30_low": cs_param_bounds.vs30_low,
        "vs30_high": cs_param_bounds.vs30_high,
        "contribution_df": cs_param_bounds.contr_df.to_dict("list"),
    }


def get_ensemble_uhs(
    uhs_results: Sequence[sc.uhs.EnsembleUHSResult], download_token: str
):
    """ Creates the response for both the core and Project API"""
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
    """ Creates the response for both core and project API"""
    return {
        "ensemble_scenario": ensemble_scenario.to_dict(),
        "download_token": download_token,
    }
