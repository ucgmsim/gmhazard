import pickle
import json
from pathlib import Path
from typing import List, Tuple, Optional, Dict

import numpy as np
import pandas as pd

from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc import rupture
from seistech_calc.im import IM


class BaseDisaggResult:
    """
    This class should not be instantiated,
    it is only to be used as an base class

    Parameters
    ----------
    fault_disagg
    ds_disagg
    site_info
    im
    im_value
    exceedance
    mean_values

    Attributes
    ----------
    fault_disagg: pd.Data
        Fault based disagg
        format: index = rupture_id_ix, columns = [rupture contribution, epsilon]
    ds_disagg: pd.DataFrame
        Distributed seismicity disagg
        format: index = rupture_id_ix, columns = [rupture contribution, epsilon]
    site_info: SiteInfo
    im: IM
    im_value: float
        The IM value for which this disagg result is for
    exceedance: float, optional
        The exceendace for which this disagg result is for
    mean_values: float, optional
        The rupture mean values, computed as
        rupture quantity of interest * rupture_contribution
    """

    # Filenames for saving
    METADATA_FN = "metadata.json"
    FAULT_DISAGG_FN = "fault_disagg.csv"
    DS_DISAGG_FN = "ds_disagg.csv"
    MEAN_VALUES_FN = "mean_values.csv"

    def __init__(
        self,
        fault_disagg: pd.DataFrame,
        ds_disagg: pd.DataFrame,
        site_info: site.SiteInfo,
        im: IM,
        im_value: float,
        ensemble: gm_data.Ensemble,
        exceedance: Optional[float] = None,
        mean_values: Optional[pd.Series] = None,
    ):
        self._fault_disagg = fault_disagg.sort_values("contribution", ascending=False)
        self._ds_disagg = ds_disagg.sort_values("contribution", ascending=False)

        self.site_info = site_info
        self.im = im
        self.im_value = im_value
        self.exceedance = exceedance
        self.mean_values = mean_values

        self._ensemble = ensemble

    @property
    def fault_disagg_id_ix(self):
        return self._fault_disagg

    @property
    def ds_disagg_id_ix(self):
        return self._ds_disagg

    @property
    def fault_disagg_id(self):
        return self._fault_disagg.set_index(
            rupture.rupture_id_ix_to_rupture_id(
                self._ensemble, self._fault_disagg.index.values
            ),
            inplace=False,
        )

    @property
    def ds_disagg_id(self):
        return self._ds_disagg.set_index(
            rupture.rupture_id_ix_to_rupture_id(
                self._ensemble, self._ds_disagg.index.values
            ),
            inplace=False,
        )

    @property
    def total_contributions(self) -> pd.Series:
        return self.fault_disagg_id.contribution.append(
            pd.Series({"distributed_seismicity": self.ds_disagg_id.contribution.sum()})
        ).sort_values(ascending=False)

    @property
    def total_contributions_df(self) -> pd.DataFrame:
        df = (
            self.fault_disagg_id[["contribution", "epsilon"]]
            .append(
                pd.DataFrame.from_dict(
                    {
                        "distributed_seismicity": {
                            "contribution": self.ds_disagg_id.contribution.sum(),
                            "epsilon": np.nan,
                        }
                    },
                    orient="index",
                )
            )
            .sort_values("contribution", ascending=False)
        )
        df.index.name = "record_id"

        return df

    @property
    def contribution_df(self) -> pd.DataFrame:
        return pd.concat(
            (self.fault_disagg_id.contribution, self.ds_disagg_id.contribution)
        )

    def to_dict(self, total_only: bool = False):
        data = {
            "station": self.site_info.station_name,
            "im": str(self.im),
            "im_value": self.im_value,
            "total_contribution": self.total_contributions.to_dict(),
            "mean_values": self.mean_values.to_dict()
            if self.mean_values is not None
            else None,
        }

        if not total_only:
            data["fault_disagg"] = self.fault_disagg_id.to_dict()
            data["ds_disagg"] = self.ds_disagg_id.to_dict()

        return data

    def save(self, base_dir: Path):
        raise NotImplementedError()

    def load(self, data_dir: Path):
        raise NotImplementedError()

    def _save(self, data_dir: Path, metadata: Dict = None):
        self.fault_disagg_id.to_csv(data_dir / self.FAULT_DISAGG_FN)
        self.ds_disagg_id.to_csv(data_dir / self.DS_DISAGG_FN)
        self.site_info.save(data_dir)

        # Save the metadata
        metadata = metadata if metadata is not None else metadata
        with open(data_dir / self.METADATA_FN, "w") as f:
            json.dump(
                {
                    **{
                        "im": str(self.im),
                        "im_value": self.im_value,
                        "exceedance": self.exceedance,
                    },
                    **metadata,
                },
                f,
            )

        if self.mean_values is not None:
            self.mean_values.to_csv(data_dir / self.MEAN_VALUES_FN)


class BranchDisaggResult(BaseDisaggResult):
    """Exactly the same as DataDisagg, except that it
    also uses stores the branch & ensemble the result belongs to.
    """

    def __init__(
        self,
        fault_disagg: pd.DataFrame,
        ds_disagg: pd.DataFrame,
        site_info: site.SiteInfo,
        im: IM,
        im_value: float,
        branch: gm_data.Branch,
        exceedance: Optional[float] = None,
    ):
        super().__init__(
            fault_disagg,
            ds_disagg,
            site_info,
            im,
            im_value,
            branch.im_ensemble.ensemble,
            exceedance=exceedance,
        )
        self.branch = branch
        self.im_ensemble = branch.im_ensemble

    def save(self, base_dir: Path):
        raise NotImplementedError()

    @classmethod
    def load(cls, dir: Path):
        raise NotImplementedError()


class EnsembleDisaggResult(BaseDisaggResult):
    """Exactly the same as DataDisagg, except that it
    also uses stores the IM ensemble the result belongs to.
    """

    def __init__(
        self,
        fault_disagg: pd.DataFrame,
        ds_disagg: pd.DataFrame,
        site_info: site.SiteInfo,
        im: IM,
        im_value: float,
        ensemble: gm_data.Ensemble,
        im_ensemble: gm_data.IMEnsemble,
        exceedance: Optional[float] = None,
        mean_values: Optional[pd.Series] = None,
    ):
        super().__init__(
            fault_disagg,
            ds_disagg,
            site_info,
            im,
            im_value,
            ensemble,
            exceedance=exceedance,
            mean_values=mean_values,
        )
        self.ensemble = ensemble
        self.im_ensemble = im_ensemble

    def save(self, base_dir: Path):
        """Saves an EnsembleDisaggResult as csv & json files
        Creates a new directory in the specified base directory
        """
        save_dir = base_dir / self.get_save_dir(
            self.im, exceedance=self.exceedance, im_value=self.im_value
        )
        save_dir.mkdir(exist_ok=False, parents=False)

        self._save(
            save_dir, metadata={"ensemble_params": self.ensemble.get_save_params()}
        )

        return save_dir

    @staticmethod
    def get_save_dir(im: IM, exceedance: float = None, im_value: float = None):
        assert (
            exceedance is not None or im_value is not None
        ), "Either exceedance or im_value has to have a value"
        return f"disagg_{im.file_format()}_{int(1 / exceedance) if exceedance is not None else str(im_value).replace('.', 'p')}"

    @classmethod
    def load(cls, data_dir: Path):
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        mean_values = (
            pd.read_csv(data_dir / cls.MEAN_VALUES_FN, index_col=0).squeeze()
            if (data_dir / cls.MEAN_VALUES_FN).exists()
            else None
        )

        im = IM.from_str(metadata["im"])
        ensemble = gm_data.Ensemble.load(metadata["ensemble_params"])

        site_info = site.SiteInfo.load(data_dir)
        fault_disagg = pd.read_csv(data_dir / cls.FAULT_DISAGG_FN, index_col=0)
        ds_disagg = pd.read_csv(data_dir / cls.DS_DISAGG_FN, index_col=0)

        fault_disagg.index = rupture.rupture_id_to_ix(ensemble, fault_disagg.index.values)
        ds_disagg.index = rupture.rupture_id_to_ix(ensemble, ds_disagg.index.values)

        return cls(
            fault_disagg,
            ds_disagg,
            site_info,
            im,
            metadata["im_value"],
            ensemble,
            ensemble.get_im_ensemble(im.im_type),
            exceedance=metadata["exceedance"],
            mean_values=mean_values,
        )


class DisaggGridData:
    """
    Parameters
    ----------
    disagg_data
    flt_bin_contr
    ds_bin_contr
    mag_edges
    rrup_edges
    mag_min
    mag_n_bins
    mag_bin_size
    rrup_min
    rrup_n_bins
    rrup_bin_size

    Attributes
    ----------
    disagg_data: BaseDisaggResult
        The underlying disagg data
    flt_bin_contr: float array
        The fault % contributions of each bin
        shape [n_mag_bins, n_rrup_bins]
    ds_bin_contr: float array
        The ds % contributions of each bin
        shape [n_mag_bins, n_rrup_bins]
    eps_bins: list of float tuples
        The min and max value of the epsilon bins
    eps_bin_contr: List of float arrays
        The contribution of the different eps bins
        Each array has shape [n_mag_bins, n_rrup_bins]
    mag_edges: float array
        The edge values of the magnitude bins
        shape [n_mag_bins]
    rrup_edges: float array
        The edge values of the rrup bins
        shape [n_rrup_bins]
    mag_min: float
        Minimum magnitude
    mag_n_bins: int
        Number of magnitude bins
    mag_bin_size: float
        Magnitude size of the bins
    rrup_min: float
        Minimum rrup
    rrup_n_bins: int
        Number of rrup bins
    rrup_bin_size: float
        Rrup size of the bins
    """

    # Filenames for saving/loading
    FLT_BIN_CONTR_FN = "flt_bin_contr.npy"
    DS_BIN_CONTR_FN = "ds_bin_contr.npy"
    EPS_BINS_FN = "eps_bins.pickle"
    EPS_BINS_CONTR_FN = "eps_bins_contr.pickle"
    MAG_EDGES_FN = "mag_edges.npy"
    RRUP_EDGES_FN = "rrup_edges.npy"
    METADATA_FN = "metadata.json"

    def __init__(
        self,
        disagg_data: BaseDisaggResult,
        flt_bin_contr: np.array,
        ds_bin_contr: np.array,
        eps_bins: List[Tuple[float, float]],
        eps_bin_contr: List[np.ndarray],
        mag_edges: np.array,
        rrup_edges: np.array,
        mag_min: float,
        mag_n_bins: int,
        mag_bin_size: float,
        rrup_min: float,
        rrup_n_bins: int,
        rrup_bin_size: float,
    ):
        self.disagg_data = disagg_data

        self.flt_bin_contr = flt_bin_contr
        self.ds_bin_contr = ds_bin_contr

        self.eps_bins = eps_bins
        self.eps_bin_contr = eps_bin_contr

        self.mag_edges = mag_edges
        self.rrup_edges = rrup_edges

        self.rrup_bin_size = rrup_bin_size
        self.rrup_n_bins = rrup_n_bins
        self.rrup_min = rrup_min
        self.mag_bin_size = mag_bin_size
        self.mag_n_bins = mag_n_bins
        self.mag_min = mag_min

    def to_dict(self):
        return {
            "disagg_data": self.disagg_data.to_dict(),
            "flt_bin_contr": self.flt_bin_contr.tolist(),
            "ds_bin_contr": self.ds_bin_contr.tolist(),
            "eps_bins": self.eps_bins,
            "eps_bin_contr": [contr.tolist() for contr in self.eps_bin_contr],
            "mag_edges": self.mag_edges.tolist(),
            "rrup_edges": self.rrup_edges.tolist(),
            "mag_min": self.mag_min,
            "mag_n_bins": self.mag_n_bins,
            "mag_bin_size": self.mag_bin_size,
            "rrup_min": self.rrup_min,
            "rrup_n_bins": self.rrup_n_bins,
            "rrup_bin_size": self.rrup_bin_size,
        }

    def save(self, base_dir: Path, save_disagg_data: bool = False):
        name_tag = (
            int(1 / self.disagg_data.exceedance)
            if self.disagg_data.exceedance is not None
            else self.disagg_data.im_value
        )
        save_dir = (
            base_dir
            / f"disagg_grid_data_{self.disagg_data.im.file_format()}_{name_tag}"
        )
        save_dir.mkdir(exist_ok=False, parents=False)

        np.save(str(save_dir / self.FLT_BIN_CONTR_FN), self.flt_bin_contr)
        np.save(str(save_dir / self.DS_BIN_CONTR_FN), self.ds_bin_contr)

        with open(save_dir / self.EPS_BINS_FN, "wb") as f:
            pickle.dump(self.eps_bins, f)

        with open(save_dir / self.EPS_BINS_CONTR_FN, "wb") as f:
            pickle.dump(self.eps_bin_contr, f)

        np.save(str(save_dir / self.MAG_EDGES_FN), self.mag_edges)
        np.save(str(save_dir / self.RRUP_EDGES_FN), self.rrup_edges)

        # Save the disagg data if specified
        disagg_data_save_dir = (
            str(self.disagg_data.save(save_dir))
            if save_disagg_data is not None
            else None
        )

        with open(save_dir / self.METADATA_FN, "w") as f:
            json.dump(
                {
                    "rrup_bin_size": self.rrup_bin_size,
                    "rrup_n_bins": self.rrup_n_bins,
                    "rrup_min": self.rrup_min,
                    "mag_bin_size": self.mag_bin_size,
                    "mag_n_bins": self.mag_n_bins,
                    "mag_min": self.mag_min,
                    "disagg_data_save_dir": disagg_data_save_dir,
                },
                f,
            )

        return save_dir

    @classmethod
    def load(cls, data_dir: Path, disagg_data: BaseDisaggResult = None):
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        if disagg_data is None:
            if metadata.get("disagg_data_save_dir") is None:
                raise Exception(
                    "Either the DisaggResult has to be saved with the DisaggGridData, "
                    "or has to be provided."
                )

            disagg_data = BaseDisaggResult.load(Path(metadata["disagg_data_save_dir"]))

        with open(data_dir / cls.EPS_BINS_FN, "rb") as f:
            eps_bins = pickle.load(f)

        with open(data_dir / cls.EPS_BINS_CONTR_FN, "rb") as f:
            eps_bin_contr = pickle.load(f)

        return cls(
            disagg_data,
            np.load(str(data_dir / cls.FLT_BIN_CONTR_FN)),
            np.load(str(data_dir / cls.DS_BIN_CONTR_FN)),
            eps_bins,
            eps_bin_contr,
            np.load(str(data_dir / cls.MAG_EDGES_FN)),
            np.load(str(data_dir / cls.RRUP_EDGES_FN)),
            metadata["mag_min"],
            metadata["mag_n_bins"],
            metadata["mag_bin_size"],
            metadata["rrup_min"],
            metadata["rrup_n_bins"],
            metadata["rrup_bin_size"],
        )
