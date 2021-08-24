from pathlib import Path
from typing import Dict, List
import json

import numpy as np
import pandas as pd

import seistech_calc.site as site
import seistech_calc.exceptions as exceptions
import seistech_calc.gm_data as gm_data
from seistech_calc.im import IM


class HazardResult:
    """Contains the hazard calculation result data (this can be at data set
    or ensemble level)

    Parameters
    ----------
    im
    site
    fault_hazard
    ds_hazard

    Attributes
    ----------
    im : IM
        IM Object for the hazard curve.
    site : SiteInfo
        The Site of this result
    fault_hazard: pd.Series
        Fault based hazard
    ds_hazard: pd.Series
        Distributed seismicity hazard
    im_values : numpy array
        The IM values for which hazard was calculated
    total_hazard: pd.Series
        Summation of fault and distributed seismicity hazard
    """

    # File names for saving
    METADATA_FN = "metadata.json"
    FAULT_HAZARD_FN = "fault_hazard.csv"
    DS_HAZARD_FN = "ds_hazard.csv"
    PERCENTILES_FN = "percentiles.csv"

    def __init__(
        self,
        im: IM,
        site: site.SiteInfo,
        fault_hazard: pd.Series,
        ds_hazard: pd.Series,
    ):
        self.im = im
        self.fault_hazard = fault_hazard
        self.ds_hazard = ds_hazard
        self.site = site

        assert np.all(self.fault_hazard.index.values == self.ds_hazard.index.values)

    @property
    def im_values(self):
        return self.fault_hazard.index.values

    @property
    def total_hazard(self):
        return self.fault_hazard + self.ds_hazard

    def exceedance_to_im(self, exceedance: float):
        """Converts the given exceedance rate to an IM value
        for the current hazard result
        """
        from . import hazard

        try:
            return hazard.exceedance_to_im(
                exceedance, self.im_values, self.total_hazard.values
            )
        except ValueError:
            raise exceptions.ExceedanceOutOfRangeError(
                self.im,
                exceedance,
                f"The specified exceedance value {exceedance} is out of"
                f" range for this hazard result for {self.im}",
            )

    def im_to_exceedance(self, im_value: float):
        """Converts the given im_value to the corresponding exceedance rate"""
        from . import hazard

        return hazard.im_to_exceedance(im_value, self.im_values, self.total_hazard)

    def as_dataframe(self) -> pd.DataFrame:
        df = pd.concat([self.fault_hazard, self.ds_hazard, self.total_hazard], axis=1)
        df.columns = ["fault", "ds", "total"]
        df.index.name = "im_values"

        return df

    def as_json_dict(self) -> Dict[str, Dict[str, str]]:
        """Returns the data as a dictionary of dictionaries with the
        values string encoded, specifically the exceedance rates are
        in the exponential format due to large number of decimal places.
        This fixes the issue of using .as_dataframe().to_json(), which
        does not handle exceedance rate values with more than 10 decimal places,
        as it doesn't use the exponential format.
        """
        result_dict = {}
        for name, hazard_series in zip(
            ["fault", "ds", "total"],
            [self.fault_hazard, self.ds_hazard, self.total_hazard],
        ):
            result_dict[name] = {
                cur_im_value: f"{cur_excd:.10E}"
                for cur_im_value, cur_excd in hazard_series.iteritems()
            }

        return result_dict

    def _save(self, dir: Path, metadata: Dict = None):
        """Saves the HazardResult data in the specified directory"""
        self.fault_hazard.to_csv(dir / self.FAULT_HAZARD_FN)
        self.ds_hazard.to_csv(dir / self.DS_HAZARD_FN)

        self.site.save(dir)

        # Save the metadata
        metadata = metadata if metadata is not None else {}
        with open(dir / self.METADATA_FN, "w") as f:
            json.dump({**{"im": str(self.im)}, **metadata}, f)

    @classmethod
    def _load_data(cls, data_dir: Path):
        """Loads the generic HazardResult data from the specified directory,
        for loading of BranchHazardResult or EnsembleHazardResult"""
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return (
            metadata,
            site.SiteInfo.load(data_dir),
            pd.read_csv(data_dir / cls.FAULT_HAZARD_FN, index_col=0).squeeze(),
            pd.read_csv(data_dir / cls.DS_HAZARD_FN, index_col=0).squeeze(),
        )


class BranchHazardResult(HazardResult):
    """Exactly the same as HazardResult, except that it
    also uses stores the branch the result belongs to.
    """

    def __init__(
        self,
        im: IM,
        site: site.SiteInfo,
        fault_hazard: pd.Series,
        ds_hazard: pd.Series,
        branch: gm_data.Branch,
    ):
        super().__init__(im, site, fault_hazard, ds_hazard)
        self.branch = branch
        self.im_ensemble = branch.im_ensemble

    def save(self, base_dir: Path):
        """Saves an BranchHazardResult as csv & json files
        Creates a new directory in the specified base directory
        """
        save_dir = base_dir / f"{self.branch.name}"
        save_dir.mkdir(parents=False, exist_ok=False)

        self._save(save_dir, metadata={"branch_name": self.branch.name})

    @classmethod
    def load(cls, save_dir: Path, branch: gm_data.Branch):
        metadata, site_info, fault_hazard, ds_hazard = cls._load_data(save_dir)

        return cls(
            IM.from_str(metadata["im"]), site_info, fault_hazard, ds_hazard, branch
        )


class EnsembleHazardResult(HazardResult):
    """Exactly the same as HazardResult, except that it
    also uses stores the ensemble the result belongs to,
    and the individual hazard results of the its branches
    """

    def __init__(
        self,
        im: IM,
        site: site.SiteInfo,
        fault_hazard: pd.Series,
        ds_hazard: pd.Series,
        ensemble: gm_data.Ensemble,
        branch_hazard: List[BranchHazardResult],
        percentiles: pd.DataFrame = None,
    ):
        super().__init__(im, site, fault_hazard, ds_hazard)
        self.ensemble = ensemble
        self.branch_hazard = branch_hazard
        self.percentiles = percentiles

    @property
    def branch_hazard_dict(self) -> Dict[str, BranchHazardResult]:
        return {cur_hazard.branch.name: cur_hazard for cur_hazard in self.branch_hazard}

    def as_dataframe(self) -> pd.DataFrame:
        """ Converts ensemble hazard to a dataframe, including 16/84th percentile if available"""
        df = super().as_dataframe()
        if self.percentiles is not None:
            df = pd.concat([df, self.percentiles], axis=1)

        return df

    def save(self, base_dir: Path):
        """Saves an EnsembleHazardResult as csv & json files
        Creates a new directory in the specified base directory
        """
        save_dir = base_dir / f"hazard_{self.im.file_format()}"
        save_dir.mkdir(exist_ok=False, parents=True)

        # Save the ensemble hazard
        super()._save(save_dir, {"ensemble_params": self.ensemble.get_save_params()})

        # Save the branches hazard
        branch_hazard_dir = save_dir / "branch_hazard"
        branch_hazard_dir.mkdir(parents=False, exist_ok=False)
        for cur_branch_hazard in self.branch_hazard:
            cur_branch_hazard.save(branch_hazard_dir)

        # Save the percentiles
        if self.percentiles is not None:
            self.percentiles.to_csv(save_dir / self.PERCENTILES_FN)

        return save_dir

    @classmethod
    def load(cls, data_dir: Path):
        metadata, site_info, fault_hazard, ds_hazard = cls._load_data(data_dir)

        # Load the ensemble
        ensemble = gm_data.Ensemble.load(metadata["ensemble_params"])
        im = IM.from_str(metadata["im"])

        # Load the branches, each directory in the branch_hazard folder
        branch_hazard = []
        for entry in (data_dir / "branch_hazard").iterdir():
            if entry.is_dir():
                branch_hazard.append(
                    BranchHazardResult.load(
                        entry,
                        ensemble.get_im_ensemble(im.im_type).branches_dict[entry.name],
                    )
                )

        # Load the percentiles
        percentiles_ffp = data_dir / cls.PERCENTILES_FN
        percentiles = (
            None
            if not percentiles_ffp.exists()
            else pd.read_csv(percentiles_ffp, index_col=0)
        )

        return cls(
            im,
            site_info,
            fault_hazard,
            ds_hazard,
            ensemble,
            branch_hazard,
            percentiles,
        )
