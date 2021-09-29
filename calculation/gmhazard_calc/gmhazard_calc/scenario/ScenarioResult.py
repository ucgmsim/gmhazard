from pathlib import Path
from typing import List, Dict
import json

import pandas as pd

from gmhazard_calc.im import IM, to_string_list, to_im_list
from gmhazard_calc import site
from gmhazard_calc import gm_data


class ScenarioResult:
    """Contains Rupture information for scenario result data

    Parameters
    ----------
    site_info
    ims
    mu_data

    Attributes
    ----------
    site_info : SiteInfo
        The Site of this result
    ims : List[IM]
        The list of IMs that is supported for the scenario (Generally SA IMs)
    mu_data : Dataframe
        Dataframe containing the mu data for each rupture over the list of IMs
    """

    # Filenames for saving/loading
    METADATA_FN = "metadata.json"
    MU_DATA_FN = "mu_data.csv"
    PERCENTILES_FN = "percentiles.csv"

    def __init__(
        self,
        site_info: site.SiteInfo,
        ims: List[IM],
        mu_data: pd.DataFrame,
    ):
        self.site_info = site_info
        self.ims = ims
        self.mu_data = mu_data

    def to_dict(self):
        """Returns a dictionary ready to jsonify for a ScenarioResult
        This includes, station, ims, rupture, pos and neg sigma data"""
        return {
            "station": self.site_info.station_name,
            "ims": to_string_list(self.ims),
            "mu_data": self.mu_data.transpose().to_dict(orient="list"),
        }

    def _save(self, data_dir: Path, metadata: Dict = None):
        """Saves the ScenarioResult data in the specified directory"""
        # Save the metadata
        metadata = metadata if metadata is not None else {}
        with open(data_dir / self.METADATA_FN, "w") as f:
            json.dump({**{"ims": to_string_list(self.ims)}, **metadata}, f)

        self.site_info.save(data_dir)

        self.mu_data.to_csv(str(data_dir / self.MU_DATA_FN))

    @classmethod
    def _load_data(cls, data_dir: Path):
        """Loads the generic ScenarioResult data from the specified directory,
        for loading of BranchScenarioResult or EnsembleScenarioResult"""
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return (
            metadata,
            site.SiteInfo.load(data_dir),
            pd.read_csv(str(data_dir / cls.MU_DATA_FN), index_col=0),
        )


class BranchScenarioResult(ScenarioResult):
    """Contains Rupture information for a given branch for a scenario result

    Parameters
    ----------
    branch
    site_info
    ims
    mu_data
    sigma_data

    Attributes
    ----------
    branch: Branch
        The branch that the results are computed for
    site_info : SiteInfo
        The Site of this result
    ims : List[IM]
        The list of IMs that is supported for the scenario (Generally SA IMs)
    mu_data : Dataframe
        Dataframe containing the mu data for each rupture over the list of IMs
    sigma_data : Dataframe
        Dataframe containing the sigma data for each rupture over the list of IMs
    """

    # Filenames for saving/loading
    SIGMA_DATA_FN = "sigma_data.csv"

    def __init__(
        self,
        branch: gm_data.Branch,
        site_info: site.SiteInfo,
        ims: List[IM],
        mu_data: pd.DataFrame,
        sigma_data: pd.DataFrame,
    ):
        super().__init__(site_info, ims, mu_data)
        self.branch = branch
        self.sigma_data = sigma_data

    def to_dict(self):
        """Returns a dictionary ready to jsonify for a BranchScenarioResult
        This includes the standard ScenarioResult dictionary with an extra info from the EnsembleScenarioResult"""
        return {
            **super().to_dict(),
            "branch": self.branch.name,
            "sigma_data": self.sigma_data.transpose().to_dict(orient="list"),
        }

    def save(self, data_dir: Path):
        """Saves the BranchScenarioResult data in the specified directory"""
        data_dir = data_dir / f"{self.branch.name}"
        data_dir.mkdir(exist_ok=False, parents=False)

        super()._save(data_dir, {"branch_name": self.branch.name})

        self.sigma_data.to_csv(str(data_dir / self.SIGMA_DATA_FN))

    @classmethod
    def load(cls, data_dir: Path, branch: gm_data.Branch):
        """Loads a BranchScenarioResult from a specified directory"""
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return cls(
            branch,
            site.SiteInfo.load(data_dir),
            to_im_list(metadata["ims"]),
            pd.read_csv(str(data_dir / cls.MU_DATA_FN), index_col=0),
            pd.read_csv(str(data_dir / cls.SIGMA_DATA_FN), index_col=0),
        )


class EnsembleScenarioResult(ScenarioResult):
    """Contains Rupture information for and ensemble scenario result set of data

    Parameters
    ----------
    ensemble
    branch_scenarios
    site_info
    ims
    mu_data
    percentiles

    Attributes
    ----------
    ensemble: Ensemble
        The ensemble to perform calculations on
    branch_scenarios: List[BranchScenarioResult]
        List of branch scenario results
    site_info : SiteInfo
        The Site of this result
    ims : List[IM]
        The list of IMs that is supported for the scenario (Generally SA IMs)
    mu_data : Dataframe
        Dataframe containing the mu data for each rupture over the list of IMs
    percentiles : Dataframe
        Dataframe containing the 16th and 84th percentile data for each rupture over the list of IMs
    """

    def __init__(
        self,
        ensemble: gm_data.Ensemble,
        branch_scenarios: List[BranchScenarioResult],
        site_info: site.SiteInfo,
        ims: List[IM],
        mu_data: pd.DataFrame,
        percentiles: pd.DataFrame,
    ):
        super().__init__(site_info, ims, mu_data)
        self.ensemble = ensemble
        self.percentiles = percentiles
        self.branch_scenarios = branch_scenarios

    def to_dict(self):
        """Returns a dictionary ready to jsonify for a EnsembleScenarioResult
        This includes the standard ScenarioResult dictionary with an extra info from the EnsembleScenarioResult"""
        return {
            **super().to_dict(),
            "ensemble_id": self.ensemble.name,
            "percentiles": {
                "16th": self.percentiles.loc[
                    :, self.percentiles.columns.str.endswith("_16th")
                ]
                .transpose()
                .to_dict(orient="list"),
                "50th": self.percentiles.loc[
                    :, self.percentiles.columns.str.endswith("_50th")
                ]
                .transpose()
                .to_dict(orient="list"),
                "84th": self.percentiles.loc[
                    :, self.percentiles.columns.str.endswith("_84th")
                ]
                .transpose()
                .to_dict(orient="list"),
            },
        }

    def save(self, base_dir: Path):
        """Saves the EnsembleScenarioResult data in the specified directory"""
        data_dir = base_dir / f"scenario"
        data_dir.mkdir(exist_ok=True, parents=True)

        # Save the ensemble scenario
        super()._save(data_dir, {"ensemble_params": self.ensemble.get_save_params()})

        self.percentiles.to_csv(str(data_dir / self.PERCENTILES_FN))

        # Save the branch scenarios
        branch_scenarios_dir = data_dir / "branch_scenarios"
        branch_scenarios_dir.mkdir(parents=False, exist_ok=False)
        for cur_branch_scenarios in self.branch_scenarios:
            cur_branch_scenarios.save(branch_scenarios_dir)

    @staticmethod
    def get_save_dir():
        return "scenario"

    @classmethod
    def load(cls, data_dir: Path):
        """Loads the generic ScenarioResult data from the specified directory,
        for loading of BranchScenarioResult or EnsembleScenarioResult"""
        (
            metadata,
            site_info,
            mu_data,
        ) = cls._load_data(data_dir)

        ensemble = gm_data.Ensemble.load(metadata["ensemble_params"])
        percentiles = pd.read_csv(str(data_dir / cls.PERCENTILES_FN), index_col=0)

        # Load the branches, each directory in the branch_scenarios folder
        branches_ffp = data_dir / "branch_scenarios"
        branch_scenarios = (
            None
            if not branches_ffp.exists()
            else [
                BranchScenarioResult.load(
                    entry,
                    ensemble.get_im_ensemble(
                        IM.from_str(metadata["ims"][0]).im_type
                    ).branches_dict[entry.name],
                )
                for entry in branches_ffp.iterdir()
                if entry.is_dir()
            ]
        )

        return cls(
            ensemble,
            branch_scenarios,
            site_info,
            to_im_list(metadata["ims"]),
            mu_data,
            percentiles,
        )
