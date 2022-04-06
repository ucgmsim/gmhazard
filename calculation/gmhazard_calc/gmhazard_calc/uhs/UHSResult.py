import json
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
import pandas as pd

from gmhazard_calc.im import IMType
from gmhazard_calc import gm_data
from gmhazard_calc import site


class BaseUHSResult:
    """Contains uniform hazard spectra result data

    Parameters
    ----------
    site_info
    exceedance
    period_values
    sa_values

    Attributes
    ----------
    site_info : SiteInfo
        The Site of this result
    exceedance: float
        The exceedance probability this result is for
    period_values: np.ndarray
        The period values
    sa_values: np.ndarray
        The spectral acceleration values
    """

    # Filenames for saving/loading
    METADATA_FN = "metadata.json"
    SA_VALUES_FN = "sa_values.npy"
    PERIOD_VALUES_FN = "period_values.npy"
    PERCENTILE_VALUES_FN = "percentile_values.csv"

    def __init__(
        self,
        site_info: site.SiteInfo,
        exceedance: float,
        period_values: np.ndarray,
        sa_values: np.ndarray,
    ):
        self.site_info = site_info
        self.sa_values = sa_values
        self.period_values = period_values
        self.exceedance = exceedance

    def as_dataframe(self):
        """Returns the result as a pandas series,
        format: index = SA periods, values = IM values
        """
        return pd.DataFrame(index=self.period_values, data=self.sa_values)

    def to_dict(self):
        """Returns a dictonary ready to jsonify for a UHSResult
        This includes, station, exceedance, period and sa values"""
        return {
            "station": self.site_info.station_name,
            "exceedance": self.exceedance,
            "period_values": self.period_values.tolist(),
            "sa_values": ["nan" if np.isnan(sa_value) else sa_value for sa_value in self.sa_values],
        }

    def _save(self, data_dir: Path, metadata: Dict = None):
        """Saves the UHSResult data in the specified directory"""
        # Save the metadata
        metadata = metadata if metadata is not None else {}
        with open(data_dir / self.METADATA_FN, "w") as f:
            json.dump({**{"exceedance": self.exceedance}, **metadata}, f)

        self.site_info.save(data_dir)

        np.save(str(data_dir / self.PERIOD_VALUES_FN), self.period_values)
        np.save(str(data_dir / self.SA_VALUES_FN), self.sa_values)

    @classmethod
    def _load_data(cls, data_dir: Path):
        """Loads the generic UHSResult data from the specified directory,
        for loading of BranchUHSResult or EnsembleUHSResult"""
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return (
            metadata,
            site.SiteInfo.load(data_dir),
            np.load(str(data_dir / cls.PERIOD_VALUES_FN), allow_pickle=True),
            np.load(str(data_dir / cls.SA_VALUES_FN), allow_pickle=True),
        )


class BranchUHSResult(BaseUHSResult):
    """Exactly the same as UHSResult, except that it
    also uses stores the branch the result belongs to.
    """

    def __init__(
        self,
        branch: gm_data.Branch,
        site_info: site.SiteInfo,
        exceedance: float,
        period_values: np.ndarray,
        sa_values: np.ndarray,
    ):
        super().__init__(site_info, exceedance, period_values, sa_values)
        self.branch = branch

    def to_dict(self):
        """Returns the BranchUHSResult to a dictonary ready to jsonify"""
        return {**super().to_dict(), "branch_name": self.branch.name}

    def save(self, base_dir: Path):
        """Saves the BranchUHSResult data in the specified directory"""
        data_dir = base_dir / f"{self.branch.name}"
        data_dir.mkdir(exist_ok=False, parents=False)

        self._save(data_dir, metadata={"branch_name": self.branch.name})

    @classmethod
    def load(cls, data_dir: Path, ensemble: gm_data.Ensemble):
        """Loads a BranchUHSResult from a specified directory"""
        metadata, site_info, period_values, sa_values = cls._load_data(data_dir)

        return cls(
            ensemble.get_im_ensemble(IMType.pSA).branches_dict[metadata["branch_name"]],
            site_info,
            metadata["exceedance"],
            period_values,
            sa_values,
        )

    @staticmethod
    def combine_results(uhs_results: Sequence["BranchUHSResult"]):
        """
        Combines several Branch UHS results into a single dataframe

        Note: Does not handle multiple same exceedance values or different
        period values between the results

        Parameters
        ----------
        uhs_results: List of BranchUHSResult

        Returns
        -------
        pd.DataFrame
            With the periods as the index and the different branches as columns
        """
        periods = uhs_results[0].period_values
        branches, sa_values = [], []
        for result in uhs_results:
            # Require all results to have the same periods values
            assert np.all(np.isclose(result.period_values, periods))

            branches.append(result.branch.name)
            sa_values.append(result.sa_values)

        return pd.DataFrame(
            index=periods, data=np.asarray(sa_values).T, columns=branches
        ).sort_index()


class EnsembleUHSResult(BaseUHSResult):
    """Exactly the same as UHSResult, except that it
    also uses stores the ensemble the result belongs to and the branch data.
    """

    def __init__(
        self,
        ensemble: gm_data.Ensemble,
        branch_uhs: List[BranchUHSResult],
        site_info: site.SiteInfo,
        exceedance: float,
        period_values: np.ndarray,
        sa_values: np.ndarray,
        percentiles: pd.DataFrame = None,
    ):
        super().__init__(site_info, exceedance, period_values, sa_values)
        self.ensemble = ensemble
        self.branch_uhs = branch_uhs
        self.percentiles = percentiles

    def to_dict(self):
        """Returns the EnsembleUHSResult to a dictonary ready to jsonify
        does not include branches, adds percentiles"""
        if self.percentiles is not None:
            percentiles = {
                key: {
                    exceedance: sa_value for exceedance, sa_value in value.iteritems()
                }
                for key, value in self.percentiles.fillna("nan").items()
            }
        else:
            percentiles = None
        return {
            **super().to_dict(),
            "ensemble_id": self.ensemble.name,
            "percentiles": percentiles,
        }

    def branch_uhs_dict(self) -> Dict[str, str]:
        """Returns the branchs as a dictionary of their branch name as the key
        and the branch as a json"""
        return {cur_uhs.branch.name: cur_uhs.to_dict() for cur_uhs in self.branch_uhs}

    def save(self, base_dir: Path):
        """Saves the EnsembleUHSResult data in the specified directory"""
        data_dir = base_dir / f"uhs_{int(1 / self.exceedance)}"
        data_dir.mkdir(exist_ok=True, parents=True)

        # Save the ensemble uhs
        super()._save(data_dir, {"ensemble_params": self.ensemble.get_save_params()})

        # Save the percentiles
        if self.percentiles is not None:
            self.percentiles.to_csv(data_dir / self.PERCENTILE_VALUES_FN)

        # Save the branches uhs
        branch_uhs_dir = data_dir / "branch_uhs"
        branch_uhs_dir.mkdir(parents=False, exist_ok=False)
        for cur_branch_uhs in self.branch_uhs:
            cur_branch_uhs.save(branch_uhs_dir)

        return data_dir

    @classmethod
    def load(cls, data_dir: Path, ensemble=None):
        """Loads a EnsembleUHSResult from a specified directory
        This also loads the BranchUHSResults and percentiles"""
        metadata, site_info, period_values, sa_values = cls._load_data(data_dir)

        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)
        if ensemble is None:
            ensemble = gm_data.Ensemble.load(metadata["ensemble_params"])
        # Load the branches, each directory in the branch_uhs folder
        branches_ffp = data_dir / "branch_uhs"
        branch_uhs = (
            None
            if not branches_ffp.exists()
            else [
                BranchUHSResult.load(entry, ensemble)
                for entry in branches_ffp.iterdir()
                if entry.is_dir()
            ]
        )

        # Load the percentiles
        percentiles_ffp = data_dir / cls.PERCENTILE_VALUES_FN
        percentiles = (
            pd.read_csv(percentiles_ffp, index_col=0)
            if percentiles_ffp.exists()
            else None
        )

        return cls(
            ensemble,
            branch_uhs,
            site_info,
            metadata["exceedance"],
            period_values,
            sa_values,
            percentiles=percentiles,
        )

    @staticmethod
    def combine_results(uhs_results: Sequence["EnsembleUHSResult"]):
        """
        Combines several Ensemble UHS results into a single dataframe,
        used for csv creation

        Note: Does not handle multiple same exceedance values or different
        period values between the results

        Parameters
        ----------
        uhs_results: List of EnsembleUHSResult

        Returns
        -------
        pd.DataFrame
            With the periods as the index and the different return periods
            with percentiles as columns
        """
        periods = uhs_results[0].period_values
        column_values, sa_values = [], []
        for result in uhs_results:
            # Require all results to have the same periods values
            assert np.all(np.isclose(result.period_values, periods))

            # Adding the means
            column_values.append(str(int(1 / result.exceedance)) + "_mean")
            sa_values.append(result.sa_values)

            # Adding the percentiles
            if result.percentiles is not None:
                for percentile in result.percentiles.iteritems():
                    column_values.append(
                        str(int(1 / result.exceedance)) + "_" + str(percentile[0])
                    )
                    sa_values.append(percentile[1].values)

        return pd.DataFrame(
            index=periods, data=np.asarray(sa_values).T, columns=column_values
        ).sort_index().fillna("nan")
