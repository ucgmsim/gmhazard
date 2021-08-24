from pathlib import Path
from typing import Dict, List
from collections import namedtuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
import yaml

import seistech_calc as si
import project_gen as pg
from .server import BASE_PROJECTS_DIR

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
            # Checks that we have the same lengths for Vs30 and Z1.0, Z2.5 values for correct mapping
            assert len(z1p0) == len(cur_data["vs30"]) and len(z1p0) == len(z2p5)
            self.locations[cur_loc_id] = Location(
                cur_data["name"], cur_data["vs30"], z1p0, z2p5,
            )
        self.station_ids = [
            pg.utils.create_station_id(cur_loc, cur_vs30, z1p0=cur_z1p0, z2p5=cur_z2p5)
            for cur_loc, cur_data in self.locations.items()
            for cur_vs30, cur_z1p0, cur_z2p5 in zip(
                cur_data.vs30_values, cur_data.z1p0_values, cur_data.z2p5_values
            )
        ]

        self.ims = si.im.to_im_list(project_params["ims"])
        self.components = [
            si.im.IMComponent[component]
            for component in project_params["im_components"]
        ]
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
    IM_j: si.im.IM
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
    project_dir = BASE_PROJECTS_DIR / version_str / project_id
    return Project.load(project_dir / f"{project_id}.yaml")


def load_hazard_data(results_dir: Path, im: si.im.IM):
    ensemble_hazard = si.hazard.EnsembleHazardResult.load(
        results_dir / f"hazard_{im.file_format()}"
    )
    nzs1170p5_hazard = si.nz_code.nzs1170p5.NZS1170p5Result.load(
        results_dir / f"hazard_nzs1170p5_{im.file_format()}"
    )

    nzta_hazard = (
        si.nz_code.nzta_2018.NZTAResult.load(results_dir / "hazard_nzta")
        if im.im_type == si.im.IMType.PGA
        else None
    )

    return ensemble_hazard, nzs1170p5_hazard, nzta_hazard


def load_disagg_data(station_data_dir: Path, im: si.im.IM, rp: int):
    data_dir = station_data_dir / f"disagg_{im.file_format()}_{rp}"
    ensemble_disagg = si.disagg.EnsembleDisaggData.load(data_dir)

    metadata_df = pd.read_csv(
        data_dir / f"disagg_{im.file_format()}_{rp}_metadata.csv", index_col=0,
    )

    with open(data_dir / f"disagg_{im.file_format()}_{rp}_src.png", "rb") as f:
        src_png_data = f.read()

    with open(data_dir / f"disagg_{im.file_format()}_{rp}_eps.png", "rb") as f:
        eps_png_data = f.read()

    return ensemble_disagg, metadata_df, src_png_data, eps_png_data


def load_uhs_data(results_dir: Path, rps: List[int]):
    ensemble = si.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rps[0]}").ensemble

    uhs_results = [
        si.uhs.EnsembleUHSResult.load(results_dir / f"uhs_{rp}") for rp in rps
    ]
    # Need to fix the `uhs_nz11750` before we generate new project data
    nzs1170p5_results = [
        si.nz_code.nzs1170p5.NZS1170p5Result.load(cur_dir, ensemble=ensemble)
        for cur_dir in (results_dir / "uhs_nz11750").glob("uhs_*")
    ]

    return uhs_results, nzs1170p5_results


def load_gms_data(station_data_dir: Path, gms_id: str):
    data_dir = station_data_dir / f"gms_{gms_id}"

    gms_result = si.gms.GMSResult.load(data_dir)
    cs_param_bounds = si.gms.CausalParamBounds.load(data_dir / "causal_param_bounds")

    return gms_result, cs_param_bounds
