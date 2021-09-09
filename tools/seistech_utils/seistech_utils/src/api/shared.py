"""Contains functions that are used by both the coreAPi and projectAPI"""
import logging
import zipfile
import os
from pathlib import Path
from typing import Sequence

import yaml
import flask
import numpy as np
import pandas as pd

import seistech_calc as sc
from . import utils
from . import shared_responses as sr


def write_hazard_download_data(
    ensemble_hazard: sc.hazard.EnsembleHazardResult,
    nzs1170p5_hazard: sc.nz_code.nzs1170p5.NZS1170p5Result,
    out_dir: str,
    nzta_hazard: sc.nz_code.nzta_2018.NZTAResult = None,
    prefix: str = None,
):
    prefix = "" if prefix is None else f"{prefix}_"
    ensemble, site_info = ensemble_hazard.ensemble, ensemble_hazard.site
    branches_hazard = ensemble_hazard.branch_hazard_dict

    # Ensemble hazard
    ens_hazard_ffp = (
        Path(out_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_hazard.csv"
    )
    ensemble_hazard.as_dataframe().to_csv(
        ens_hazard_ffp, index_label="im_values", mode="a"
    )

    # Branches - total hazard
    branches_hazard_ffp = (
        Path(out_dir)
        / f"{prefix}{ensemble_hazard.im.file_format()}_branches_hazard.csv"
    )
    branches_total_hazard_dict = {}
    branch_im_values = list(branches_hazard.values())[0].total_hazard.index.values
    for cur_name, cur_data in branches_hazard.items():
        branches_total_hazard_dict[cur_name] = cur_data.total_hazard.values

        # Sanity check
        assert np.all(np.isclose(cur_data.total_hazard.index.values, branch_im_values))

    # Include mean, 16th and 84th in the branch files
    branches_total_hazard_dict["mean"] = ensemble_hazard.total_hazard.values
    if ensemble_hazard.percentiles is not None:
        branches_total_hazard_dict["16th"] = ensemble_hazard.percentiles["16th"].values
        branches_total_hazard_dict["84th"] = ensemble_hazard.percentiles["84th"].values
    assert np.allclose(ensemble_hazard.total_hazard.index.values, branch_im_values)

    branches_total_hazard_df = pd.DataFrame.from_dict(branches_total_hazard_dict)
    branches_total_hazard_df.index = branch_im_values
    branches_total_hazard_df.to_csv(
        branches_hazard_ffp, index_label="im_values", mode="a"
    )

    # NZS1170p5 hazard
    nzs1170p5_ffp = (
        Path(out_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_nzs1170p5.csv"
    )
    nzs1170p5_metadata = (
        f"Z: {nzs1170p5_hazard.Z}, D: {nzs1170p5_hazard.D}, "
        f"N: {nzs1170p5_hazard.N.values[0]}, Ch: {nzs1170p5_hazard.Ch.iloc[0]}\n"
    )
    utils.add_metadata_header(
        str(nzs1170p5_ffp), ensemble, site_info, nzs1170p5_metadata
    )
    nzs1170p5_hazard.im_values.to_csv(
        nzs1170p5_ffp, index_label="exceedance", header=True, mode="a"
    )

    # NZTA_hazard
    nzta_metadata, nzta_ffp = {}, None
    if nzta_hazard is not None:
        nzta_ffp = (
            Path(out_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_nzta.csv"
        )
        nzta_metadata = f"Soil Class: {nzta_hazard.soil_class.value}"
        utils.add_metadata_header(str(nzta_ffp), ensemble, site_info, nzta_metadata)
        nzta_hazard.pga_values.to_csv(
            nzta_ffp, index_label="exceedance", header=True, mode="a", index=True
        )

        nzta_metadata = {
            "NZTA_metadata": {
                "soil_class": nzta_hazard.soil_class.value,
            }
        }

    # Metadata
    metadata = {
        "ensemble_id": ensemble.name,
        "station": site_info.station_name,
        "lon": float(site_info.lon),
        "lat": float(site_info.lat),
        "vs30": float(site_info.vs30),
        "user_vs30": float(site_info.user_vs30)
        if site_info.user_vs30 is not None
        else site_info.user_vs30,
        "im": str(ensemble_hazard.im),
        "git_version_hash": utils.get_repo_version(),
        "NZS1170.5_metadata": {
            "Z": float(nzs1170p5_hazard.Z),
            "D": float(nzs1170p5_hazard.D),
            "N": float(nzs1170p5_hazard.N.values[0]),
            "Ch": float(nzs1170p5_hazard.Ch.values[0]),
            "soil_class": nzs1170p5_hazard.soil_class.value,
            "R": nzs1170p5_hazard.R.to_dict(),
        },
    }

    meta_data_ffp = (
        Path(out_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_metadata.yaml"
    )
    with meta_data_ffp.open(mode="w") as f:
        yaml.safe_dump({**metadata, **nzta_metadata}, f)

    # Hazard & hazard branches plot
    # Temporarily disable logging, as matplotlib spams..
    logging.debug("Creating hazard plots for downloading")
    logging.disable(level=logging.ERROR)

    hazard_plot_ffp = (
        Path(out_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_hazard.png"
    )
    sc.plots.plt_hazard(
        ensemble_hazard.as_dataframe(),
        "Hazard",
        ensemble_hazard.im,
        str(hazard_plot_ffp),
        nzs1170p5_hazard.im_values,
        nzta_hazard.pga_values if nzta_hazard is not None else None,
    )

    hazard_branch_plot_ffp = (
        Path(out_dir)
        / f"{prefix}{ensemble_hazard.im.file_format()}_hazard_branches.png"
    )
    sc.plots.plt_hazard_totals(
        ensemble_hazard.as_dataframe(),
        {
            key: cur_branch_hazard.as_dataframe()
            for key, cur_branch_hazard in branches_hazard.items()
        },
        "Branches Hazard",
        ensemble_hazard.im,
        str(hazard_branch_plot_ffp),
        nzs1170p5_hazard.im_values,
        nzta_hazard.pga_values if nzta_hazard is not None else None,
    )
    logging.disable(level=logging.NOTSET)

    return (
        ens_hazard_ffp,
        branches_hazard_ffp,
        nzs1170p5_ffp,
        nzta_ffp,
        meta_data_ffp,
        hazard_plot_ffp,
        hazard_branch_plot_ffp,
    )


def create_hazard_download_zip(
    ensemble_hazard: sc.hazard.EnsembleHazardResult,
    nzs1170p5_hazard: sc.nz_code.nzs1170p5.NZS1170p5Result,
    tmp_dir: str,
    nzta_hazard: sc.nz_code.nzta_2018.NZTAResult = None,
    prefix: str = None,
):
    ffps = write_hazard_download_data(
        ensemble_hazard,
        nzs1170p5_hazard,
        tmp_dir,
        nzta_hazard=nzta_hazard,
        prefix=prefix,
    )

    # Create zip file
    logging.debug("Creating zip file")
    zip_ffp = Path(tmp_dir) / f"{prefix}{ensemble_hazard.im.file_format()}_hazard.zip"
    with zipfile.ZipFile(str(zip_ffp), mode="w") as cur_zip:
        for cur_ffp in ffps:
            if cur_ffp is not None:
                cur_zip.write(cur_ffp, Path(cur_ffp).name)

    return str(zip_ffp)


def write_disagg_download_data(
    disagg_data: sc.disagg.EnsembleDisaggResult,
    metadata_df: pd.DataFrame,
    out_dir: str,
    src_plot_data: bytes = None,
    eps_plot_data: bytes = None,
    prefix: str = None,
):
    prefix = "" if prefix is None else f"{prefix}_"
    ensemble = disagg_data.ensemble

    # Save total contributions + extra data
    disagg_data_ffp = (
        Path(out_dir)
        / f"{prefix}{disagg_data.im.file_format()}_{int(1 / disagg_data.exceedance)}_disagg.csv"
    )
    disagg_df = disagg_data.total_contributions_df.merge(
        metadata_df, how="left", left_index=True, right_index=True
    )

    disagg_df.loc[
        :,
        [
            "rupture_name",
            "contribution",
            "epsilon",
            "annual_rec_prob",
            "magnitude",
            "rrup",
        ],
    ].to_csv(disagg_data_ffp, index=True, mode="a", index_label="rupture_id")

    # Create metadata file
    meta_data_ffp = (
        Path(out_dir)
        / f"{prefix}{disagg_data.im.file_format()}_{int(1 / disagg_data.exceedance)}_metadata.yaml"
    )
    with meta_data_ffp.open(mode="w") as f:
        yaml.safe_dump(
            {
                "ensemble_id": ensemble.name,
                "station": disagg_data.site_info.station_name,
                "lon": float(disagg_data.site_info.lon),
                "lat": float(disagg_data.site_info.lat),
                "vs30": float(disagg_data.site_info.vs30),
                "user_vs30": float(disagg_data.site_info.user_vs30)
                if disagg_data.site_info.user_vs30 is not None
                else None,
                "im": str(disagg_data.im),
                "exceedance": disagg_data.exceedance,
                "im_value": float(disagg_data.im_value),
                "git_version_hash": utils.get_repo_version(),
            },
            f,
        )

    mean_values_ffp = None
    if disagg_data.mean_values is not None:
        mean_values_ffp = (
            Path(out_dir)
            / f"{prefix}{disagg_data.im.file_format()}_{int(1 / disagg_data.exceedance)}_mean_values.csv"
        )
        disagg_data.mean_values.to_frame().T.to_csv(mean_values_ffp, index=False)

    # Write & add plots
    src_plot_ffp, eps_plot_ffp = None, None
    if src_plot_data is not None:
        src_plot_ffp = (
            Path(out_dir)
            / f"{prefix}{disagg_data.im.file_format()}_{int(1 / disagg_data.exceedance)}_disagg_src_plot.png"
        )
        with src_plot_ffp.open(mode="wb") as f:
            f.write(src_plot_data)

    if eps_plot_data is not None:
        eps_plot_ffp = (
            Path(out_dir)
            / f"{prefix}{disagg_data.im.file_format()}_{int(1 / disagg_data.exceedance)}_disagg_eps_plot.png"
        )
        with eps_plot_ffp.open(mode="wb") as f:
            f.write(eps_plot_data)

    return disagg_data_ffp, meta_data_ffp, mean_values_ffp, src_plot_ffp, eps_plot_ffp


def create_disagg_download_zip(
    ensemble_disagg: sc.disagg.EnsembleDisaggResult,
    metadata_df: pd.DataFrame,
    data_dir: str,
    src_plot_data: bytes = None,
    eps_plot_data: bytes = None,
    prefix: str = None,
):
    # Write the data
    ffps = write_disagg_download_data(
        ensemble_disagg,
        metadata_df,
        data_dir,
        src_plot_data,
        eps_plot_data,
        prefix=prefix,
    )

    # Create zip file
    zip_ffp = (
        Path(data_dir)
        / f"{prefix}{ensemble_disagg.im.file_format()}_{int(1 / ensemble_disagg.exceedance)}_disagg.zip"
    )
    with zipfile.ZipFile(str(zip_ffp), mode="w") as cur_zip:
        for cur_ffp in ffps:
            if cur_ffp is not None:
                cur_zip.write(cur_ffp, Path(cur_ffp).name)

    return zip_ffp


def write_uhs_download_data(
    uhs_results: Sequence[sc.uhs.EnsembleUHSResult],
    nzs1170p5_results: Sequence[sc.nz_code.nzs1170p5.NZS1170p5Result],
    out_dir: str,
    prefix: str = None,
):
    prefix = "" if prefix is None else f"{prefix}_"
    ensemble = uhs_results[0].ensemble

    # UHS
    uhs_ffp = Path(out_dir) / f"{prefix}uhs.csv"
    uhs_df = sc.uhs.EnsembleUHSResult.combine_results(uhs_results)
    uhs_df.to_csv(uhs_ffp, index_label="pSA_periods")

    # NZS1170.5 - UHS
    nzs1170p5_uhs_ffp = Path(out_dir) / f"{prefix}nzs1170p5_uhs.csv"
    nzs1170p5_df = sc.nz_code.nzs1170p5.NZS1170p5Result.combine_results(
        nzs1170p5_results
    )
    nzs1170p5_df.to_csv(nzs1170p5_uhs_ffp, index_label="pSA_periods")

    # Branches - Each RP
    branches_uhs_ffps = []
    uhs_branches_plot_ffps = []
    if uhs_results[0].branch_uhs is not None:
        for result in uhs_results:
            branches_uhs_ffp = (
                Path(out_dir)
                / f"{prefix}{int(1 / result.branch_uhs[0].exceedance)}_branches_uhs.csv"
            )
            uhs_branches_plot_ffp = (
                Path(out_dir)
                / f"branches_uhs_plot_rp_{int(1 / result.branch_uhs[0].exceedance)}.png"
            )
            branches_uhs_df = sc.uhs.BranchUHSResult.combine_results(result.branch_uhs)
            branches_uhs_df.to_csv(branches_uhs_ffp, index_label="sa_periods", mode="a")
            branches_uhs_ffps.append(branches_uhs_ffp)
            # Creating UHS branches plots
            sc.plots.plt_uhs_branches(
                uhs_df,
                branches_uhs_df,
                int(1 / result.branch_uhs[0].exceedance),
                nzs1170p5_uhs=nzs1170p5_df,
                station_name=uhs_results[0].site_info.station_name,
                save_file=uhs_branches_plot_ffp,
            )
            uhs_branches_plot_ffps.append(uhs_branches_plot_ffp)

    # Metadata
    meta_data_ffp = Path(out_dir) / f"{prefix}uhs_metadata.yaml"
    with meta_data_ffp.open(mode="w") as f:
        yaml.safe_dump(
            {
                "ensemble_id": ensemble.name,
                "station": uhs_results[0].site_info.station_name,
                "lon": float(uhs_results[0].site_info.lon),
                "lat": float(uhs_results[0].site_info.lat),
                "vs30": float(uhs_results[0].site_info.vs30),
                "user_vs30": float(uhs_results[0].site_info.user_vs30)
                if uhs_results[0].site_info.user_vs30 is not None
                else None,
                "exceedances": float(uhs_results[0].exceedance),
                "git_version_hash": utils.get_repo_version(),
                "NZS1170.5_metadata": {
                    "Ch": float(nzs1170p5_results[0].Ch.iloc[0]),
                    "N": float(nzs1170p5_results[0].N.iloc[0]),
                    "D": float(nzs1170p5_results[0].D),
                    "Z": float(nzs1170p5_results[0].Z),
                    "R": nzs1170p5_results[0].R.to_dict(),
                    "soil_class": nzs1170p5_results[0].soil_class.value,
                },
            },
            f,
        )

    # Create UHS plot
    uhs_plot_ffp = Path(out_dir) / f"{prefix}uhs.png"
    sc.plots.plt_uhs(
        uhs_df,
        nzs1170p5_uhs=nzs1170p5_df,
        station_name=uhs_results[0].site_info.station_name,
        save_file=uhs_plot_ffp,
    )

    return (
        uhs_ffp,
        nzs1170p5_uhs_ffp,
        meta_data_ffp,
        uhs_plot_ffp,
        *branches_uhs_ffps,
        *uhs_branches_plot_ffps,
    )


def create_uhs_download_zip(
    uhs_results: Sequence[sc.uhs.EnsembleUHSResult],
    nzs1170p5_results: Sequence[sc.nz_code.nzs1170p5.NZS1170p5Result],
    tmp_dir: str,
    prefix: str = None,
):
    ffps = write_uhs_download_data(uhs_results, nzs1170p5_results, tmp_dir, prefix)

    # Create zip file
    zip_ffp = Path(tmp_dir) / f"{prefix}UHS.zip"
    with zipfile.ZipFile(str(zip_ffp), mode="w") as cur_zip:
        for cur_ffp in ffps:
            cur_zip.write(cur_ffp, Path(cur_ffp).name)

    return zip_ffp


def write_gms_download_data(
    gms_result: sc.gms.GMSResult,
    app: flask.app,
    out_dir: str,
    disagg_data: sc.disagg.EnsembleDisaggData,
    cs_param_bounds: sc.gms.CausalParamBounds = None,
    prefix: str = None,
):
    prefix = "" if prefix is None else f"{prefix}_"

    missing_waveforms = gms_result.gm_dataset.get_waveforms(
        gms_result.selected_gms_ids, gms_result.site_info, out_dir
    )
    if len(missing_waveforms) > 0:
        app.logger.info(
            f"Failed to find waveforms for simulations: {missing_waveforms}"
        )

    if cs_param_bounds is not None:
        default_causal_params = sr.get_default_causal_params(cs_param_bounds)
        # Bounds with min/max values
        causal_params_bounds = sr.get_causal_params_bounds(cs_param_bounds)

        selected_gms_metadata = {
            **gms_result.selected_gms_metdata_df.to_dict(orient="list"),
            # mean and error bounds for selected GMs, used in Mw Rrup plot
            **gms_result.metadata_dict,
        }

        # Mw and Rrup distribution plot
        sc.plots.plt_gms_mw_rrup(
            selected_gms_metadata,
            disagg_data.mean_values,
            selected_gms_metadata["selected_gms_agg"],
            bounds=default_causal_params,
            save_file=Path(out_dir) / f"{prefix}gms_mw_rrup_plot.png",
        )
        # Pseudo acceleration response spectra plot
        sc.plots.plt_gms_spectra(
            gms_result,
            save_file=Path(out_dir) / f"{prefix}gms_spectra_plot.png",
        )
        # IM distribution plots
        sc.plots.plt_gms_im_distribution(gms_result, save_file=Path(out_dir))
        # Disagg Distribution plots (Mw Distribution or Rrup distribution)
        contribution_df_data = default_causal_params["contribution_df"]
        if contribution_df_data is not None:
            sorted_rrup, rrup_cdf = utils.calc_cdf(
                contribution_df_data["contribution"][:], contribution_df_data["rrup"][:]
            )
            sorted_mag, mag_cdf = utils.calc_cdf(
                contribution_df_data["contribution"][:],
                contribution_df_data["magnitude"][:],
            )
            sorted_contribution_df = {
                "magnitude": sorted_mag.tolist(),
                "mag_contribution": mag_cdf.tolist(),
                "rrup": sorted_rrup.tolist(),
                "rrup_contribution": rrup_cdf.tolist(),
            }

            sc.plots.plt_gms_disagg_distribution(
                sorted_contribution_df["mag_contribution"],
                sorted_contribution_df["magnitude"],
                selected_gms_metadata,
                "mag",
                bounds=causal_params_bounds,
                save_file=Path(out_dir)
                / f"{prefix}gms_mag_disagg_distribution_plot.png",
            )

            sc.plots.plt_gms_disagg_distribution(
                sorted_contribution_df["rrup_contribution"],
                sorted_contribution_df["rrup"],
                selected_gms_metadata,
                "rrup",
                bounds=causal_params_bounds,
                save_file=Path(out_dir)
                / f"{prefix}gms_rrup_disagg_distribution_plot.png",
            )
        # Causal Parameters plots
        sc.plots.plt_gms_causal_param(
            gms_result,
            "vs30",
            bounds=causal_params_bounds,
            save_file=Path(out_dir) / f"{prefix}gms_vs30_causal_param_plot.png",
        )

        sc.plots.plt_gms_causal_param(
            gms_result,
            "sf",
            bounds=causal_params_bounds,
            save_file=Path(out_dir) / f"{prefix}gms_sf_causal_param_plot.png",
        )

        # Available Ground Motions plot
        sc.plots.plt_gms_available_gm(
            gms_result.gm_dataset.get_metadata_df(gms_result.site_info).to_dict(
                orient="list"
            ),
            gms_result.gm_dataset.get_n_gms_in_bounds(
                gms_result.gm_dataset.get_metadata_df(gms_result.site_info),
                cs_param_bounds,
            ),
            bounds=default_causal_params,
            save_file=Path(out_dir) / f"{prefix}gms_available_gm_plot.png",
        )

    return os.listdir(out_dir)


def create_gms_download_zip(
    gms_result: sc.gms.GMSResult,
    app: flask.app,
    tmp_dir: str,
    disagg_data: sc.disagg.EnsembleDisaggData,
    cs_param_bounds: sc.gms.CausalParamBounds = None,
    prefix: str = None,
):

    ffps = write_gms_download_data(
        gms_result,
        app,
        tmp_dir,
        disagg_data,
        cs_param_bounds=cs_param_bounds,
        prefix=prefix,
    )

    zip_ffp = os.path.join(
        tmp_dir,
        f"{prefix}{gms_result.ensemble.name}_{gms_result.IM_j.file_format()}_{gms_result.gm_dataset.name}_waveforms.zip",
    )

    with zipfile.ZipFile(zip_ffp, mode="w") as cur_zip:
        for cur_file in ffps:
            if cur_file != os.path.basename(zip_ffp):
                cur_zip.write(
                    os.path.join(tmp_dir, cur_file),
                    arcname=os.path.basename(cur_file),
                )
    return zip_ffp


def write_scenario_download_data(
    ensemble_scenario: sc.scenario.EnsembleScenarioResult,
    out_dir: str,
    prefix: str = None,
):
    """Writes the scenario data into 6 different files
    1 for the main scenario data which stores the 16th, 50th and 84th percentiles as well as the mu data
    4 for the different tectonic types which stores all the scenarios related to that tectonic type and holds
    each models data for that given scenario
    1 for the scenario metadata
    All files are appended to an ffps list to be zipped together

    Parameters
    ----------
    ensemble_scenario: EnsembleScenarioResult
        ensemble scenario to grab results from
    out_dir: str
        The output directory to write the 6 files to
    prefix: str
        The prefix for all the filenames (generally project_id or ensemble_id)

    Returns
    -------
    List[Path]"""
    prefix = "" if prefix is None else f"{prefix}_"
    ensemble, site_info = ensemble_scenario.ensemble, ensemble_scenario.site_info
    branch_scenarios = ensemble_scenario.branch_scenarios

    ffps = []

    # Ensemble scenario
    ens_scenario_ffp = Path(out_dir) / f"{prefix}scenarios.csv"

    # Combining mu and percentiles dataframes
    mu = ensemble_scenario.mu_data.add_suffix("_mu")
    mu_percentiles_dataframe = mu.join(ensemble_scenario.percentiles)
    mu_percentiles_dataframe = mu_percentiles_dataframe.reindex(
        sorted(mu_percentiles_dataframe.columns), axis=1
    )
    mu_percentiles_dataframe.to_csv(ens_scenario_ffp, index_label="scenarios", mode="a")
    ffps.append(ens_scenario_ffp)

    # Keeps track of the ffps that have been added to the models_df and the models
    model_tec_type_ffps = []
    models = []
    # Starting dataframe for the model data from the branches
    all_models_im_rupture_df = pd.DataFrame()

    # Tech Type Files
    rup_tec_df = pd.DataFrame(
        data=branch_scenarios[0].branch.flt_rupture_df["tectonic_type"].values,
        index=branch_scenarios[0].branch.flt_rupture_df["rupture_name"],
    )

    # Ensemble Scenario Branches
    for branch_scenario in branch_scenarios:
        for leaf in branch_scenario.branch.leafs:
            if (
                len(leaf.flt_imdb_ffps) != 0
                and leaf.flt_imdb_ffps[0] not in model_tec_type_ffps
            ):
                # Naming the columns to the model for the branches given im / rupture data
                model_im_rupture_df = branch_scenario.mu_data.add_suffix(
                    f"_{leaf.model}"
                )
                # If empty create the first dataframe
                if all_models_im_rupture_df.empty:
                    # Grabs ruptures that relate to the given tectonic type on the leaf
                    all_models_im_rupture_df = model_im_rupture_df.loc[
                        model_im_rupture_df.index.intersection(
                            rup_tec_df[rup_tec_df[0] == leaf.tec_type].index
                        ),
                        :,
                    ]
                # If same model has already come across append additional rows
                elif leaf.model in models:
                    # Grabs ruptures that relate to the given tectonic type on the leaf and appends to the all_models df
                    all_models_im_rupture_df = all_models_im_rupture_df.append(
                        model_im_rupture_df.loc[
                            model_im_rupture_df.index.intersection(
                                rup_tec_df[rup_tec_df[0] == leaf.tec_type].index
                            ),
                            :,
                        ]
                    )
                else:
                    # Merge the dataframes on an outer so that each scenario's rows only have values for the models
                    # that correspond to their given tectonic type
                    all_models_im_rupture_df = all_models_im_rupture_df.join(
                        model_im_rupture_df.loc[
                            model_im_rupture_df.index.intersection(
                                rup_tec_df[rup_tec_df[0] == leaf.tec_type].index
                            ),
                            :,
                        ],
                        how="outer",
                    )
                models.append(leaf.model)
                model_tec_type_ffps.append(leaf.flt_imdb_ffps[0])

    # Creating each tectonic type csv from the all_models_im_rupture_df
    for tec_type in [
        "ACTIVE_SHALLOW",
        "VOLCANIC",
        "SUBDUCTION_INTERFACE",
        "SUBDUCTION_SLAB",
    ]:
        # Filtering the all_models_im_rupture_df by the scenarios that match the given tectonic type
        # Sorting the dataframes so order is paired by IM then Model not Model then IM
        tec_type_df = all_models_im_rupture_df.loc[
            all_models_im_rupture_df.index.intersection(
                rup_tec_df[rup_tec_df[0] == tec_type].index
            ),
            :,
        ].dropna(axis=1)
        tec_type_df = tec_type_df.reindex(sorted(tec_type_df.columns), axis=1)

        # Writing to csv and saving the ffp
        if not tec_type_df.empty:
            tec_type_ffp = (
                Path(out_dir) / f"{prefix}{tec_type.lower()}_scenario_models.csv"
            )
            tec_type_df.to_csv(tec_type_ffp, index_label="scenarios", mode="a")
            ffps.append(tec_type_ffp)

    # Metadata
    metadata = {
        "ensemble_id": ensemble.name,
        "station": site_info.station_name,
        "lon": float(site_info.lon),
        "lat": float(site_info.lat),
        "vs30": float(site_info.vs30),
        "user_vs30": float(site_info.user_vs30) if site_info.user_vs30 else None,
        "ims": sc.im.to_string_list(ensemble_scenario.ims),
        "im_component": str(ensemble_scenario.ims[0].component),
        "git_version_hash": utils.get_repo_version(),
    }
    meta_data_ffp = Path(out_dir) / f"{prefix}scenario_metadata.yaml"
    with open(meta_data_ffp, "w") as f:
        yaml.safe_dump(metadata, f)

    ffps.append(meta_data_ffp)

    return ffps


def create_scenario_download_zip(
    ensemble_scenario: sc.scenario.EnsembleScenarioResult,
    tmp_dir: str,
    prefix: str = None,
):
    ffps = write_scenario_download_data(
        ensemble_scenario,
        out_dir=tmp_dir,
        prefix=prefix,
    )

    # Create zip file
    logging.debug("Creating zip file")
    zip_ffp = Path(tmp_dir) / f"{prefix}scenario.zip"
    with zipfile.ZipFile(zip_ffp, mode="w") as cur_zip:
        for cur_ffp in ffps:
            if cur_ffp is not None:
                cur_zip.write(cur_ffp, cur_ffp.name)

    return zip_ffp


def get_available_im_dict(
    ims: Sequence[sc.im.IM], components: Sequence[sc.im.IMComponent] = None
):
    im_dict = {}
    for im in ims:
        if str(im.im_type) in im_dict:
            if str(im.component) not in im_dict[str(im.im_type)]["components"]:
                im_dict[str(im.im_type)]["components"].append(str(im.component))
            if im.is_pSA() and im.period not in im_dict[str(im.im_type)]["periods"]:
                im_dict[str(im.im_type)]["periods"].append(im.period)
        else:
            im_dict[str(im.im_type)] = {
                "periods": [im.period] if im.is_pSA() else None,
                "components": [str(component) for component in components]
                if components is not None
                and (im.is_pSA() or im.im_type == sc.im.IMType.PGA)
                else [str(im.component)],
            }
    return im_dict
