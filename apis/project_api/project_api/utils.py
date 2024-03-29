import os
import shutil
import zipfile
import tempfile
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List
from collections import namedtuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
import yaml

import gmhazard_calc as gc
import api_utils as au
import project_gen as pg


Location = namedtuple("Location", ["name", "vs30_values", "z1p0_values", "z2p5_values"])


class Project:
    def __init__(self, project_config: Dict):
        self.config = project_config
        self.ensemble_ffp = project_config["ensemble_ffp"]

        project_params = project_config["project_parameters"]

        if "locations" in project_params.keys():
            self.locations = {}
            self.station_ids = [
                cur_site.station_name for cur_site in pg.get_site_infos(project_params)
            ]
        else:
            self.station_ids = project_params["location_ids"]

        self.ims = gc.im.to_im_list(project_params["ims"])
        self.components = (
            [
                gc.im.IMComponent[component]
                for component in project_params["im_components"]
            ]
            if "im_components" in project_params
            else [gc.im.IMComponent.RotD50]
        )
        self.disagg_rps = project_params["disagg_return_periods"]
        self.uhs_return_periods = project_params["uhs_return_periods"]

        self.gms_params = None
        if "gms" in project_params:
            self.gms_params = [
                GMSParams.from_dict(gms_id, gms_config_dict)
                for gms_id, gms_config_dict in project_params["gms"].items()
            ]

    @classmethod
    def load(cls, project_config_ffp: Path):
        with open(project_config_ffp, "r") as f:
            return cls(yaml.safe_load(f))


@dataclass
class GMSParams:
    id: str
    IM_j: gc.im.IM
    dataset_id: str
    im_j: float = None
    exceedance: float = None
    IMs: np.ndarray = None
    n_gms: int = 10
    n_replica: int = 10

    def __post_init__(self):
        assert (
            self.im_j is not None or self.exceedance is not None
        ), "Either im_j or the exceedance rate has to be specified"

    def to_dict(self):
        return dict(
            IM_j=self.IM_j,
            dataset_id=self.dataset_id,
            im_j=self.im_j,
            exceedance=self.exceedance,
            IMs=self.IMs,
            n_gms=self.n_gms,
            n_replica=self.n_replica,
        )

    @classmethod
    def from_dict(cls, gms_id: str, gms_config: Dict):
        return cls(
            gms_id,
            gms_config["IMj"],
            gms_config["dataset_id"],
            im_j=gms_config.get("im_j"),
            exceedance=gms_config.get("exceedance"),
            IMs=gms_config.get("IMs"),
            n_gms=gms_config.get("n_gms"),
            n_replica=gms_config.get("n_replica"),
        )


def get_project(version_str: str, project_id: str) -> Project:
    from .server import BASE_PROJECTS_DIR

    project_dir = BASE_PROJECTS_DIR / version_str / project_id
    return Project.load(project_dir / f"{project_id}.yaml")


def load_hazard_data(results_dir: Path, im: gc.im.IM):
    ensemble_hazard = gc.hazard.EnsembleHazardResult.load(
        results_dir / f"hazard_{im.file_format()}"
    )
    nzs1170p5_hazard = (
        gc.nz_code.nzs1170p5.NZS1170p5Result.load(
            results_dir / f"hazard_nzs1170p5_{im.file_format()}"
        )
        if im.im_type == gc.im.IMType.pSA or im.im_type == gc.im.IMType.PGA
        else None
    )

    nzta_hazard = (
        gc.nz_code.nzta_2018.NZTAResult.load(results_dir / "hazard_nzta")
        if im.im_type == gc.im.IMType.pSA or im.im_type == gc.im.IMType.PGA
        else None
    )

    return ensemble_hazard, nzs1170p5_hazard, nzta_hazard


def load_disagg_data(station_data_dir: Path, im: gc.im.IM, rps: List[int]):
    ensemble_results, metadata_results = [], []
    src_pngs, eps_pngs = [], []

    for rp in rps:
        # No data exists for that RP
        if not (
            data_dir := station_data_dir / f"disagg_{im.file_format()}_{rp}"
        ).exists():
            print(f"No data available for disagg {im} and RP {rp}, skipping")
            continue

        ensemble_results.append(gc.disagg.EnsembleDisaggResult.load(data_dir))

        metadata_results.append(
            pd.read_csv(
                data_dir / f"disagg_{im.file_format()}_{rp}_metadata.csv",
                index_col=0,
            )
        )

        with open(data_dir / f"disagg_{im.file_format()}_{rp}_src.png", "rb") as f:
            src_png_data = f.read()
            src_pngs.append(src_png_data)

        with open(data_dir / f"disagg_{im.file_format()}_{rp}_eps.png", "rb") as f:
            eps_png_data = f.read()
            eps_pngs.append(eps_png_data)

    return ensemble_results, metadata_results, src_pngs, eps_pngs


def load_scenario_rupture_metadata(
    project_dir: Path,
    project_id: str,
    station_id: str,
    im_component: gc.im.IMComponent,
    ruptures: List[str],
):
    with open(project_dir / f"{project_id}.yaml", "r") as f:
        project_dict = yaml.safe_load(f)

    project_params = project_dict["project_parameters"]
    ims = gc.shared.get_SA_ims(
        gc.im.to_im_list(project_params["ims"]), component=im_component
    )

    station_data_dir = project_dir / "results" / station_id / str(im_component)

    # Annual recurrence rate, Magnitude, and Rrup are specified values for each
    # rupture, nothing to do with IM. Hence, choose any directory
    data_dir = list(station_data_dir.glob(f"disagg_{ims[0].file_format()}*"))[0]
    metadata_df = pd.read_csv(list(data_dir.glob("*_metadata.csv"))[0], index_col=0)

    ensemble_disagg_result = gc.disagg.EnsembleDisaggResult.load(data_dir)
    merged_metadata_df = ensemble_disagg_result.total_contributions_df.merge(
        metadata_df, how="left", left_index=True, right_index=True
    )
    # Drop unnecessary columns and rows
    merged_metadata_df = merged_metadata_df.drop(
        labels=["contribution", "epsilon"], axis=1
    ).drop(labels=["distributed_seismicity"], axis=0)

    # Swap columns
    merged_metadata_df = merged_metadata_df.reindex(
        columns=["rupture_name", "annual_rec_prob", "magnitude", "rrup"]
    )
    # Filters the metadata by the given ruptures which are the top 20
    # based on geometric mean
    return merged_metadata_df.loc[merged_metadata_df["rupture_name"].isin(ruptures)]


def load_uhs_data(results_dir: Path, rps: List[int]):
    ensemble = gc.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rps[0]}").ensemble

    uhs_results = [
        gc.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rp}", ensemble=ensemble)
        for rp in rps
    ]

    nzs1170p5_results = [
        gc.nz_code.nzs1170p5.NZS1170p5Result.load(cur_dir, ensemble=ensemble)
        for cur_dir in (results_dir / "uhs_nzs1170p5").glob("uhs_*")
    ]

    return uhs_results, nzs1170p5_results


def load_gms_data(station_data_dir: Path, gms_id: str):
    data_dir = station_data_dir / f"gms_{gms_id}"

    gms_result = gc.gms.GMSResult.load(data_dir)

    disagg_data = None
    if (
        disagg_data_dir := data_dir
        / "disagg_data"
        / f"disagg_{str(gms_result.IM_j).replace('.', 'p')}"
        f"_{int(1 / gms_result.exceedance)}"
    ).exists():
        disagg_data = gc.disagg.EnsembleDisaggResult.load(
            disagg_data_dir,
        )

    return gms_result, disagg_data


def create_project_zip(
    base_project_dir: Path,
    project_id: str,
    version_str: str,
    output_dir: Path,
    n_procs: int = 1,
):
    """Saves the project as zip file (in download format)"""
    project = Project.load(
        base_project_dir / version_str / project_id / f"{project_id}.yaml"
    )

    with tempfile.TemporaryDirectory() as data_tmp_dir:
        data_tmp_dir = Path(data_tmp_dir)
        if n_procs == 1:
            for cur_station_id in project.station_ids:
                _write_station(
                    data_tmp_dir,
                    project,
                    base_project_dir
                    / version_str
                    / project_id
                    / "results"
                    / cur_station_id,
                    project_id,
                    cur_station_id,
                )
        else:
            with mp.Pool(n_procs) as p:
                p.starmap(
                    _write_station,
                    [
                        (
                            data_tmp_dir,
                            project,
                            base_project_dir
                            / version_str
                            / project_id
                            / "results"
                            / cur_station_id,
                            project_id,
                            cur_station_id,
                        )
                        for cur_station_id in project.station_ids
                    ],
                )

        zip_ffp = Path(output_dir) / f"{project_id}.zip"
        with zipfile.ZipFile(zip_ffp, mode="w") as cur_zip:
            for cur_dir, cur_dir_names, cur_file_names in os.walk(
                data_tmp_dir / project_id
            ):
                for cur_filename in cur_file_names:
                    cur_zip.write(
                        os.path.join(cur_dir, cur_filename),
                        os.path.relpath(
                            os.path.join(cur_dir, cur_filename),
                            os.path.join(data_tmp_dir / project_id, ".."),
                        ),
                    )

            return zip_ffp


def _write_station(
    data_tmp_dir: Path,
    project: Project,
    cur_data_dir: Path,
    project_id: str,
    station_id: str,
):
    output_dir = data_tmp_dir / project_id / station_id
    output_dir.mkdir(exist_ok=False, parents=True)

    shutil.copy(cur_data_dir / "context_map_plot.png", output_dir)
    shutil.copy(cur_data_dir / "vs30_map_plot.png", output_dir)

    for cur_gms_param in project.gms_params:
        if not (
            cur_gms_dir := cur_data_dir
            / gc.gms.GMSResult.get_save_dir(cur_gms_param.id)
        ).exists():
            print(
                f"Failed to write GMS results for id {cur_gms_param.id}, "
                f"as the path {cur_gms_dir} does not exists"
            )
            continue

        cur_gms_result, cur_disagg_data = load_gms_data(cur_data_dir, cur_gms_param.id)

        (out_dir := output_dir / cur_gms_param.id).mkdir(exist_ok=False)
        au.api.write_gms_download_data(
            cur_gms_result,
            str(out_dir),
            disagg_data=cur_disagg_data,
        )

    for component in project.components:
        cur_comp_out_dir = output_dir / str(component)
        cur_comp_out_dir.mkdir(exist_ok=False)

        for cur_im in project.ims:
            # Load & write hazard
            ensemble_hazard, nzs1170p5_hazard, nzta_hazard = load_hazard_data(
                cur_data_dir / str(component), cur_im
            )
            au.api.write_hazard_download_data(
                ensemble_hazard,
                str(cur_comp_out_dir),
                nzs1170p5_hazard,
                nzta_hazard=nzta_hazard,
            )

            # Load disagg data
            (
                ensemble_disagg,
                metadata_df,
                src_png_data,
                eps_png_data,
            ) = load_disagg_data(
                cur_data_dir / str(component), cur_im, project.disagg_rps
            )
            mean_values = {
                cur_rp: cur_disagg.mean_values
                for cur_disagg, cur_rp in zip(ensemble_disagg, project.disagg_rps)
            }
            contributions = {
                cur_rp: cur_disagg.total_contributions
                for cur_disagg, cur_rp in zip(ensemble_disagg, project.disagg_rps)
            }

            # Write disagg data
            au.api.write_disagg_download_data(
                ensemble_disagg,
                metadata_df,
                str(cur_comp_out_dir),
                src_plot_data=src_png_data,
                eps_plot_data=eps_png_data,
            )

            pd.concat(contributions, axis=1).to_csv(
                cur_comp_out_dir / f"{cur_im}_disagg_contributions.csv"
            )
            pd.concat(mean_values, axis=1).to_csv(
                cur_comp_out_dir / f"{cur_im}_disagg_mean_values.csv"
            )

        # Load & Write UHS
        uhs_results, nzs1170p5_results = load_uhs_data(
            cur_data_dir / str(component), project.uhs_return_periods
        )
        au.api.write_uhs_download_data(
            uhs_results, nzs1170p5_results, str(cur_comp_out_dir)
        )
