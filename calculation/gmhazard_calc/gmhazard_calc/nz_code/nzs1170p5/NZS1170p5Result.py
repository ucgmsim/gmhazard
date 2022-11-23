import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import gm_data
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM


class NZS1170p5Result:
    """Contains the hazards results from NZ code

    Parameters
    ----------
    ensemble,
    site_info,
    im,
    sa_period,
    hazard,
    Ch,
    Z,
    R,
    D,
    N,

    Attributes
    ----------
    ensemble: gm_data.Ensemble
        The ensemble that was used to compute this result,
        note this only affects the near fault distance calculation
        as it specifies which site-source was used
    site_info: site.SiteInfo
        Details of the site the result was computed for
    im: IM
    sa_period: float
    im_values: pd.Series
        The exceedance values and their corresponding IM values,
        based on the NZ code
        format: index = exceedance probabilities, values: IM values
    Ch: float
        The spectral shape factor used
    soil_class: SoilClass
        The soil class for the site of interest
    Z: float
        The hazard factor used
    R: pd.Series
        The return period factors used, returned as pandas series
        as R is a function of exceedance probability
        format: index = exceedance probability, value = R used
    D: float
        The near fault distance used
    N: float
        The near fault factor used
    """

    # Filenames for saving/loading
    CH_FN = "Ch.csv"
    IM_VALUES_FN = "im_values.csv"
    R_FN = "R.csv"
    N_FN = "N.csv"
    METADATA_FN = "metadata.csv"

    def __init__(
        self,
        ensemble: gm_data.Ensemble,
        site_info: site.SiteInfo,
        im: IM,
        sa_period: float,
        im_values: pd.Series,
        Ch: pd.Series,
        soil_class: const.NZSSoilClass,
        Z: float,
        R: pd.Series,
        D: float,
        N: pd.Series,
    ):
        self.ensemble = ensemble
        self.site_info = site_info
        self.im = im
        self.sa_period = sa_period
        self.im_values = im_values
        self.Ch = Ch
        self.soil_class = soil_class
        self.Z = Z
        self.R = R
        self.D = D
        self.N = N

    def to_dict(self, nan_to_string: bool = False):
        return {
            "ensemble_id": self.ensemble.name,
            "station": self.site_info.station_name,
            "im": str(self.im),
            "sa_period": self.sa_period,
            "im_values": self.im_values.replace(np.nan, "nan").to_dict()
            if nan_to_string
            else self.im_values.to_dict(),
            "Ch": self.Ch.replace(np.nan, "nan").to_dict()
            if nan_to_string
            else self.Ch.to_dict(),
            "soil_class": self.soil_class.value,
            "Z": self.Z,
            "R": self.R.to_dict(),
            "D": self.D,
            "N": self.N.to_dict(),
        }

    def save(self, base_dir: Path, prefix: str):
        data_dir = base_dir / self.get_save_dir(self.im, prefix)
        data_dir.mkdir(exist_ok=False, parents=False)

        self.site_info.save(data_dir)
        self.im_values.to_csv(data_dir / self.IM_VALUES_FN)
        self.Ch.to_csv(data_dir / self.CH_FN)
        self.R.to_csv(data_dir / self.R_FN)
        self.N.to_csv(data_dir / self.N_FN)

        with open(data_dir / self.METADATA_FN, "w") as f:
            json.dump(
                {
                    "ensemble_params": self.ensemble.get_save_params(),
                    "im": str(self.im),
                    "sa_period": self.sa_period,
                    "soil_class": self.soil_class.value,
                    "Z": self.Z,
                    "D": self.D,
                },
                f,
            )

        return data_dir

    @staticmethod
    def get_save_dir(im: IM, prefix: str):
        return f"{prefix}_nzs1170p5_{im.file_format()}"

    @classmethod
    def load(cls, data_dir: Path, ensemble: gm_data.Ensemble = None):
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return cls(
            gm_data.Ensemble.load(metadata["ensemble_params"])
            if ensemble is None
            else ensemble,
            site.SiteInfo.load(data_dir),
            IM.from_str(metadata["im"]),
            metadata["sa_period"],
            pd.read_csv(
                data_dir / cls.IM_VALUES_FN,
                index_col=0,
                float_precision="round_trip",
            ).squeeze("columns"),
            pd.read_csv(data_dir / cls.CH_FN, index_col=0).squeeze("columns"),
            const.NZSSoilClass(metadata["soil_class"]),
            metadata["Z"],
            pd.read_csv(data_dir / cls.R_FN, index_col=0).squeeze("columns"),
            metadata["D"],
            pd.read_csv(data_dir / cls.N_FN, index_col=0).squeeze("columns"),
        )

    @staticmethod
    def combine_results(nzs1170p5_results: Sequence["NZS1170p5Result"]) -> pd.DataFrame:
        """
        Combines several NZ code results into a single dataframe,
        assumes that all results were computed for the same exceedance values

        Note: Does not handle multiple results with the same SA period

        Parameters
        ----------
        nzs1170p5_results: List of NZS1170p5Result

        Returns
        -------
        pd.DataFrame
            format: index: SA periods, columns: exceedance probabilities
        """
        exceedance_values = nzs1170p5_results[0].im_values.index.values

        result_dict = {}
        for result in nzs1170p5_results:
            assert np.all(np.isclose(result.im_values.index.values, exceedance_values))
            result_dict[result.sa_period] = result.im_values.values

        return pd.DataFrame.from_dict(
            result_dict, orient="index", columns=exceedance_values
        ).sort_index()
