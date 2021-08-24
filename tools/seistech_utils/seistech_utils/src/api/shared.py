"""Contains functions that are used by both the coreAPi and projectAPI"""
import logging
import zipfile
from pathlib import Path
from typing import Sequence

import yaml
import numpy as np
import pandas as pd

import seistech_calc as si
from . import utils


def write_hazard_download_data(
    ensemble_hazard: si.hazard.EnsembleHazardResult,
    nzs1170p5_hazard: si.nz_code.nzs1170p5.NZS1170p5Result,
    out_dir: str,
    nzta_hazard: si.nz_code.nzta_2018.NZTAResult = None,
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

        nzta_metadata = {"NZTA_metadata": {"soil_class": nzta_hazard.soil_class.value,}}

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
    si.plots.plt_hazard(
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
    si.plots.plt_hazard_totals(
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
    ensemble_hazard: si.hazard.EnsembleHazardResult,
    nzs1170p5_hazard: si.nz_code.nzs1170p5.NZS1170p5Result,
    tmp_dir: str,
    nzta_hazard: si.nz_code.nzta_2018.NZTAResult = None,
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
    disagg_data: si.disagg.EnsembleDisaggData,
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
    ensemble_disagg: si.disagg.EnsembleDisaggData,
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
    uhs_results: Sequence[si.uhs.EnsembleUHSResult],
    nzs1170p5_results: Sequence[si.nz_code.nzs1170p5.NZS1170p5Result],
    out_dir: str,
    prefix: str = None,
):
    prefix = "" if prefix is None else f"{prefix}_"
    ensemble = uhs_results[0].ensemble

    # UHS
    uhs_ffp = Path(out_dir) / f"{prefix}uhs.csv"
    uhs_df = si.uhs.EnsembleUHSResult.combine_results(uhs_results)
    uhs_df.to_csv(uhs_ffp, index_label="pSA_periods")

    # Branches - Each RP
    branches_uhs_ffps = []
    if uhs_results[0].branch_uhs is not None:
        for result in uhs_results:
            branches_uhs_ffp = (
                Path(out_dir)
                / f"{prefix}{int(1 / result.branch_uhs[0].exceedance)}_branches_uhs.csv"
            )
            branches_uhs_df = si.uhs.BranchUHSResult.combine_results(result.branch_uhs)
            branches_uhs_df.to_csv(
                str(branches_uhs_ffp), index_label="sa_periods", mode="a"
            )
            branches_uhs_ffps.append(str(branches_uhs_ffp))

    # NZS1170p5 - UHS
    nzs1170p5_uhs_ffp = Path(out_dir) / f"{prefix}nz_code_uhs.csv"
    nzs1170p5_df = si.nz_code.nzs1170p5.NZS1170p5Result.combine_results(
        nzs1170p5_results
    )
    nzs1170p5_df.to_csv(str(nzs1170p5_uhs_ffp), index_label="pSA_periods")

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
    si.plots.plt_uhs(
        uhs_df,
        nz_code_uhs=nzs1170p5_df,
        station_name=uhs_results[0].site_info.station_name,
        save_file=str(uhs_plot_ffp),
    )

    return (uhs_ffp, nzs1170p5_uhs_ffp, meta_data_ffp, uhs_plot_ffp, *branches_uhs_ffps)


def create_uhs_download_zip(
    uhs_results: Sequence[si.uhs.EnsembleUHSResult],
    nzs1170p5_results: Sequence[si.nz_code.nzs1170p5.NZS1170p5Result],
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


def get_available_im_dict(
    ims: Sequence[si.im.IM], components: Sequence[si.im.IMComponent] = None
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
                and (im.is_pSA() or im.im_type == si.im.IMType.PGA)
                else [str(im.component)],
            }
    return im_dict
