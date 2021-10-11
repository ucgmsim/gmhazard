import json
from pathlib import Path

import numpy as np
import pandas as pd

from gmhazard_calc import site
from gmhazard_calc import gm_data
from gmhazard_calc import constants as const


class NZTAResult:
    """
    Contains the hazard from the NZTA code
    for the site of interest

    Attributes
    ----------
    ensemble: gm_data.Ensemble
        The ensemble, does not affect the calculation,
        purely included for completeness
    site_info: site.SiteInfo
        Details of the site the result was computed for
    M_eff: series
        The effective magnitude (value) for the specified
        return period (RP), this can be None if the RP is not
        within a range where M_eff is defined by NZTA manual
    pga_values: series
        The PGA (value) for each exceedance (index)
    C0_1000: series
        The C0_1000 (value) for the specified return period
    nearest_town: string
        Name of the nearest town, used for
        C0_1000 selection (which is used for PGA)
    """

    PGA_VALUES_FN = "pga.csv"
    C0_1000_VALUES_FN = "c0_1000.csv"
    METADATA_FN = "metadata.csv"

    def __init__(
        self,
        ensemble: gm_data.Ensemble,
        site_info: site.SiteInfo,
        soil_class: const.NZTASoilClass,
        pga_values: pd.Series,
        M_eff: float,
        C0_1000: float,
        nearest_town: str,
    ):
        self.ensemble = ensemble
        self.site_info = site_info
        self.soil_class = soil_class

        self.M_eff = M_eff
        self.pga_values = pga_values
        self.pga_values.name = "PGA"

        # Metadata
        self.nearest_town = nearest_town
        self.C0_1000 = C0_1000

    def to_dict(self, nan_to_string: bool = False):
        return {
            "ensemble_id": self.ensemble.name,
            "station": self.site_info.station_name,
            "soil_class": self.soil_class.value,
            "pga_values": self.pga_values.replace(np.nan, "nan").to_dict()
            if nan_to_string
            else self.pga_values.to_dict(),
            "M_eff": self.M_eff,
            "c0_1000": self.C0_1000,
            "nearest_town": self.nearest_town,
        }

    def save(self, base_dir: Path):
        data_dir = base_dir / self.get_save_dir()
        data_dir.mkdir(exist_ok=False, parents=False)

        self.site_info.save(data_dir)
        self.pga_values.to_csv(data_dir / self.PGA_VALUES_FN, index_label="exceedance")

        with open(data_dir / self.METADATA_FN, "w") as f:
            json.dump(
                {
                    "ensemble_params": self.ensemble.get_save_params(),
                    "nearest_town": self.nearest_town,
                    "soil_class": self.soil_class.value,
                    "M_eff": self.M_eff,
                    "c0_1000": self.C0_1000,
                },
                f,
            )

    @staticmethod
    def get_save_dir():
        return "hazard_nzta"

    @classmethod
    def load(cls, data_dir: Path):
        with open(data_dir / cls.METADATA_FN, "r") as f:
            metadata = json.load(f)

        return cls(
            gm_data.Ensemble.load(metadata["ensemble_params"]),
            site.SiteInfo.load(data_dir),
            const.NZSSoilClass(metadata["soil_class"]),
            pd.read_csv(
                data_dir / cls.PGA_VALUES_FN, index_col=0, float_precision="round_trip"
            ).squeeze(),
            metadata["M_eff"],
            metadata["c0_1000"],
            metadata["nearest_town"],
        )
