import json
from pathlib import Path
from typing import Dict, Tuple, Union

import pandas as pd
import numpy as np

import sha_calc as sha_calc
from gmhazard_calc.im import IM, to_im_list, to_string_list
from gmhazard_calc import gm_data
from gmhazard_calc import site
from gmhazard_calc import constants
from .GroundMotionDataset import GMDataset
from .CausalParamBounds import CausalParamBounds
from .GCIMResult import IMEnsembleUniGCIM, SimUniGCIM


class GMSResult:
    """
    Result of the ground motion
    selection operation

    Parameters
    ----------
    ensemble: Ensemble
        The Ensemble used
    site_info: SiteInfo
        The site for which GMS was performed
    IMj: IM
        Conditioning IM type
    im_j: float
        The conditioning IM value
    IMs: numpy array of strings
        The IM vector
    selected_gms_im_df: dataframe
        The IM values of the selected GMs
    IMi_gcims: dictionary
        The GCIMs for each IMi
    realisations: dataframe
        The IM values of the realisations
    gm_dataset: GMDataset
        The dataset from which the ground motions
        were selected
    cs_param_bounds: CausalParamBounds
        The causal parameter bounds imposed
    sf: dataframe
        The scaling factor for each of
        the selected ground motions
    """

    SELECTED_GMS_IMS_FN = "selected_gm_ims.csv"
    REALISATIONS_FN = "realisations.csv"
    SF_FN = "sf.csv"

    GCIM_CDF_X_FN = "cdf_x.csv"
    GCIM_CDF_Y_FN = "cdf_y.csv"

    VARIABLES_FN = "variables.json"

    SELECTED_GMS_METDATA_FN = "selected_gms_metadata.csv"
    SELECTED_GMS_IM_16_84_FN = "selected_gms_im_16_84_df.csv"

    def __init__(
        self,
        ensemble: gm_data.Ensemble,
        site_info: site.SiteInfo,
        IMj: IM,
        im_j: float,
        IMs: np.ndarray,
        selected_gms_im_df: pd.DataFrame,
        IMi_gcims: Dict[str, Union[SimUniGCIM, IMEnsembleUniGCIM]],
        realisations: pd.DataFrame,
        gm_dataset: GMDataset,
        gms_type: constants.GMSType,
        exceedance: float = None,
        cs_param_bounds: CausalParamBounds = None,
        sf: pd.DataFrame = None,
        metadata: Tuple[pd.DataFrame, Dict, pd.DataFrame] = (None, None, None),
    ):
        self.ensemble = ensemble
        self.site_info = site_info
        self.gm_dataset = gm_dataset

        self.IM_j = IMj
        self.im_j = im_j
        self.IMs = IMs

        self.exceedance = exceedance

        self.cs_param_bounds = cs_param_bounds

        self.IMi_gcims = IMi_gcims
        self.realisations = realisations
        self.selected_gms_im_df = selected_gms_im_df

        self.gms_type = gms_type

        self.sf = sf

        self._metadata_dict, self._selected_gms_metadata_df = metadata[1], metadata[0]
        self._selected_gms_im_16_84_df = metadata[2]

    @property
    def metadata_dict(self) -> Dict:
        if self._metadata_dict is None:
            self._compute_metadata()

        return self._metadata_dict

    @property
    def selected_gms_metdata_df(self):
        if self._selected_gms_metadata_df is None:
            self._compute_metadata()

        return self._selected_gms_metadata_df

    @property
    def selected_gms_im_16_84_df(self):
        if self._selected_gms_im_16_84_df is None:
            self._compute_metadata()

        return self._selected_gms_im_16_84_df

    @property
    def selected_gms_ids(self) -> np.ndarray:
        return self.selected_gms_im_df.index.values

    def _compute_metadata(self) -> None:
        """Computes/Collects the metadata"""
        self._selected_gms_metadata_df = self.gm_dataset.get_metadata_df(
            self.site_info, self.selected_gms_ids
        )

        if "sf" in self._selected_gms_metadata_df.columns:
            self._selected_gms_metadata_df["sf"] = self.sf.loc[
                self._selected_gms_metadata_df.index
            ]

        # Get 16/84th for each selected GM
        n_gms = self.selected_gms_im_df.shape[0]
        var_dict = {}
        for cur_im in self.selected_gms_im_df.columns:
            cur_result = sha_calc.query_non_parametric_cdf_invs(
                np.asarray([0.16, 0.84]),
                np.sort(self.selected_gms_im_df[cur_im].values),
                np.linspace(1.0 / n_gms, 1.0, n_gms),
            )
            var_dict[f"{cur_im}"] = {"16th": cur_result[0], "84th": cur_result[1]}
        self._selected_gms_im_16_84_df = pd.DataFrame(var_dict)

        # Get the 16th, mean and 84th values for magnitude/rrup of the selected GMs
        self._metadata_dict = dict(
            selected_gms_agg={
                "mag_mean": float(self._selected_gms_metadata_df.mag.mean()),
                "mag_error_bounds": list(
                    sha_calc.query_non_parametric_cdf_invs(
                        np.asarray([0.16, 0.84]),
                        self._selected_gms_metadata_df.sort_values("mag").mag.values,
                        np.linspace(1.0 / n_gms, 1.0, n_gms),
                    )
                ),
                "rrup_mean": float(self._selected_gms_metadata_df.rrup.mean()),
                "rrup_error_bounds": list(
                    sha_calc.query_non_parametric_cdf_invs(
                        np.asarray([0.16, 0.84]),
                        self._selected_gms_metadata_df.sort_values("rrup").rrup.values,
                        np.linspace(1.0 / n_gms, 1.0, n_gms),
                    )
                ),
            },
            ks_bounds=sha_calc.shared.ks_critical_value(
                self.realisations.shape[0], 0.1
            ),
        )

    def save(self, base_dir: Path, id: str) -> Path:
        save_dir = base_dir / self.get_save_dir(id)
        save_dir.mkdir(exist_ok=True, parents=False)

        self.site_info.save(save_dir)
        self.selected_gms_im_df.to_csv(save_dir / self.SELECTED_GMS_IMS_FN)
        self.realisations.to_csv(save_dir / self.REALISATIONS_FN)

        if self.cs_param_bounds is not None:
            self.cs_param_bounds.save(save_dir)

        if self.sf is not None:
            self.sf.to_csv(save_dir / self.SF_FN)

        # Generate the metadata if needed
        if self._metadata_dict is None:
            self._compute_metadata()
        self._selected_gms_metadata_df.to_csv(save_dir / self.SELECTED_GMS_METDATA_FN)
        self._selected_gms_im_16_84_df.to_csv(save_dir / self.SELECTED_GMS_IM_16_84_FN)

        with open(save_dir / self.VARIABLES_FN, "w") as f:
            json.dump(
                dict(
                    IM_j=str(self.IM_j),
                    im_j=self.im_j,
                    IMs=to_string_list(self.IMs),
                    ensemble_params=self.ensemble.get_save_params(),
                    gm_dataset_id=self.gm_dataset.name,
                    metadata_dict=self._metadata_dict,
                    gms_type=self.gms_type.value,
                    exceedance=self.exceedance,
                ),
                f,
            )

        # Save GCIM
        for IMi, cur_gcim in self.IMi_gcims.items():
            cur_gcim.save(save_dir)

        return save_dir

    @staticmethod
    def get_save_dir(id: str):
        return f"gms_{id}"

    @classmethod
    def load(cls, data_dir: Path):
        site_info = site.SiteInfo.load(data_dir)
        selected_gm_im_df = pd.read_csv(data_dir / cls.SELECTED_GMS_IMS_FN, index_col=0)
        realisations = pd.read_csv(data_dir / cls.REALISATIONS_FN, index_col=0)

        cs_param_bounds = (
            CausalParamBounds.load(data_dir / "causal_param_bounds")
            if (data_dir / "causal_param_bounds").exists()
            else None
        )
        sf = (
            pd.read_csv(data_dir / cls.SF_FN, index_col=0)
            if (data_dir / cls.SF_FN).exists()
            else None
        )

        with open(data_dir / cls.VARIABLES_FN, "r") as f:
            variable_dict = json.load(f)
        ensemble = gm_data.Ensemble.load(variable_dict["ensemble_params"])

        gms_type = constants.GMSType(variable_dict["gms_type"])

        IMs = np.asarray(to_im_list(variable_dict["IMs"]))
        if gms_type is constants.GMSType.empirical:
            IMi_gcims = {
                IMi: IMEnsembleUniGCIM.load(
                    data_dir / f"{IMi}", ensemble.get_im_ensemble(IMi.im_type)
                )
                for IMi in IMs
            }
        else:
            IMi_gcims = {
                IMi: SimUniGCIM.load(
                    data_dir / f"{IMi}", ensemble
                )
                for IMi in IMs
            }

        return cls(
            ensemble,
            site_info,
            IM.from_str(variable_dict["IM_j"]),
            variable_dict["im_j"],
            IMs,
            selected_gm_im_df,
            IMi_gcims,
            realisations,
            GMDataset.get_GMDataset(variable_dict["gm_dataset_id"]),
            constants.GMSType(variable_dict["gms_type"]),
            cs_param_bounds=cs_param_bounds,
            sf=sf,
            exceedance=variable_dict.get("exceedance"),
            metadata=(
                pd.read_csv(data_dir / cls.SELECTED_GMS_METDATA_FN, index_col=0),
                variable_dict["metadata_dict"],
                pd.read_csv(data_dir / cls.SELECTED_GMS_IM_16_84_FN, index_col=0),
            ),
        )
