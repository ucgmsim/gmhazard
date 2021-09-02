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

import seistech_calc as sc
import seistech_utils as su
import project_gen as pg


Location = namedtuple("Location", ["name", "vs30_values", "z1p0_values", "z2p5_values"])


class Project:
    def __init__(self, project_config: Dict):
        self.config = project_config
        self.ensemble_ffp = project_config["ensemble_ffp"]

        project_params = project_config["project_parameters"]

        self.locations = {}
        for cur_loc_id, cur_data in project_params["locations"].items():
            z1p0 = (
                cur_data["z1.0"]
                if "z1.0" in cur_data
                else [None] * len(cur_data["vs30"])
            )
            z2p5 = (
                cur_data["z2.5"]
                if "z2.5" in cur_data
                else [None] * len(cur_data["vs30"])
            )
            # Checks that we have the same lengths for
            # Vs30 and Z1.0, Z2.5 values for correct mapping
            assert len(z1p0) == len(cur_data["vs30"]) and len(z1p0) == len(z2p5)
            self.locations[cur_loc_id] = Location(
                cur_data["name"],
                cur_data["vs30"],
                z1p0,
                z2p5,
            )
        self.station_ids = [
            pg.utils.create_station_id(cur_loc, cur_vs30, z1p0=cur_z1p0, z2p5=cur_z2p5)
            for cur_loc, cur_data in self.locations.items()
            for cur_vs30, cur_z1p0, cur_z2p5 in zip(
                cur_data.vs30_values, cur_data.z1p0_values, cur_data.z2p5_values
            )
        ]

        self.ims = sc.im.to_im_list(project_params["ims"])
        self.components = (
            [
                sc.im.IMComponent[component]
                for component in project_params["im_components"]
            ]
            if "im_components" in project_params
            else [sc.im.IMComponent.RotD50]
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
    IM_j: sc.im.IM
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


def load_hazard_data(results_dir: Path, im: sc.im.IM):
    ensemble_hazard = sc.hazard.EnsembleHazardResult.load(
        results_dir / f"hazard_{im.file_format()}"
    )
    nzs1170p5_hazard = sc.nz_code.nzs1170p5.NZS1170p5Result.load(
        results_dir / f"hazard_nzs1170p5_{im.file_format()}"
    )

    nzta_hazard = (
        sc.nz_code.nzta_2018.NZTAResult.load(results_dir / "hazard_nzta")
        if im.im_type == sc.im.IMType.PGA
        else None
    )

    return ensemble_hazard, nzs1170p5_hazard, nzta_hazard


def load_disagg_data(station_data_dir: Path, im: sc.im.IM, rp: int):
    data_dir = station_data_dir / f"disagg_{im.file_format()}_{rp}"
    ensemble_disagg = sc.disagg.EnsembleDisaggData.load(data_dir)

    metadata_df = pd.read_csv(
        data_dir / f"disagg_{im.file_format()}_{rp}_metadata.csv",
        index_col=0,
    )

    with open(data_dir / f"disagg_{im.file_format()}_{rp}_src.png", "rb") as f:
        src_png_data = f.read()

    with open(data_dir / f"disagg_{im.file_format()}_{rp}_eps.png", "rb") as f:
        eps_png_data = f.read()

    return ensemble_disagg, metadata_df, src_png_data, eps_png_data


def load_uhs_data(results_dir: Path, rps: List[int]):
    ensemble = sc.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rps[0]}").ensemble

    uhs_results = [
        sc.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rp}") for rp in rps
    ]
    # Need to fix the `uhs_nz11750` before we generate new project data
    nzs1170p5_results = [
        sc.nz_code.nzs1170p5.NZS1170p5Result.load(cur_dir, ensemble=ensemble)
        for cur_dir in (results_dir / "uhs_nzs1170p5").glob("uhs_*")
    ]

    return uhs_results, nzs1170p5_results


def load_gms_data(station_data_dir: Path, gms_id: str):
    data_dir = station_data_dir / f"gms_{gms_id}"

    gms_result = sc.gms.GMSResult.load(data_dir)
    cs_param_bounds = sc.gms.CausalParamBounds.load(data_dir / "causal_param_bounds")
    disagg_data = sc.disagg.EnsembleDisaggData.load(data_dir / "disagg_data")

    return gms_result, cs_param_bounds, disagg_data


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

    for component in project.components:
        cur_comp_out_dir = output_dir / str(component)
        cur_comp_out_dir.mkdir(exist_ok=False)

        for cur_im in project.ims:
            # Load & write hazard
            ensemble_hazard, nzs1170p5_hazard, nzta_hazard = load_hazard_data(
                cur_data_dir / str(component), cur_im
            )
            su.api.write_hazard_download_data(
                ensemble_hazard,
                nzs1170p5_hazard,
                str(cur_comp_out_dir),
                nzta_hazard=nzta_hazard,
            )

            # Load & Write disagg for all return periods
            mean_values, contributions = {}, {}
            for cur_rp in project.disagg_rps:
                try:
                    (
                        ensemble_disagg,
                        metadata_df,
                        src_png_data,
                        eps_png_data,
                    ) = load_disagg_data(cur_data_dir / str(component), cur_im, cur_rp)
                except FileNotFoundError:
                    print(
                        f"Failed to write disagg data for IM {cur_im} "
                        f"and RP {cur_rp} as the "
                        f"results are missing or incomplete"
                    )
                else:
                    su.api.write_disagg_download_data(
                        ensemble_disagg,
                        metadata_df,
                        str(cur_comp_out_dir),
                        src_plot_data=src_png_data,
                        eps_plot_data=eps_png_data,
                    )

                    mean_values[cur_rp] = ensemble_disagg.mean_values
                    contributions[cur_rp] = ensemble_disagg.total_contributions

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
        su.api.write_uhs_download_data(
            uhs_results, nzs1170p5_results, str(cur_comp_out_dir)
        )
