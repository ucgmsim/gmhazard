import json
from pathlib import Path
from dataclasses import dataclass
from typing import Tuple, ClassVar

import pandas as pd

from seistech_calc.im import IM
from seistech_calc import gm_data
from seistech_calc import site


@dataclass
class CausalParamBounds:
    ensemble: gm_data.Ensemble
    site_info: site.SiteInfo
    IM_j: IM
    mw_bounds: Tuple[float, float]
    rrup_bounds: Tuple[float, float]
    vs30_bounds: Tuple[float, float]
    sf_bounds: Tuple[float, float] = (None, None),
    contr_df: pd.DataFrame = None
    exceedance: float = None
    im_value: float = None

    ATTRIBUTES_FN: ClassVar[str] = "attributes.csv"
    CONTRIBUTIONS_FN: ClassVar[str] = "contributions.csv"

    def __post_init__(self):
        assert (
            self.exceedance is not None or self.im_value is not None
        ), "One of exceedance or im_value has to be specified"

        if self.contr_df is not None:
            self.contr_df.sort_values("contribution", ascending=False, inplace=True)

    @property
    def mw_low(self):
        return self.mw_bounds[0]

    @property
    def mw_high(self):
        return self.mw_bounds[1]

    @property
    def rrup_low(self):
        return self.rrup_bounds[0]

    @property
    def rrup_high(self):
        return self.rrup_bounds[1]

    @property
    def vs30_low(self):
        return self.vs30_bounds[0]

    @property
    def vs30_high(self):
        return self.vs30_bounds[1]

    @property
    def sf_low(self):
        return self.sf_bounds[0]

    @property
    def sf_high(self):
        return self.sf_bounds[1]

    def save(self, base_dir: Path):
        save_dir = base_dir / f"causal_param_bounds"
        save_dir.mkdir(exist_ok=False, parents=False)

        self.contr_df.to_csv(save_dir / self.CONTRIBUTIONS_FN)

        with open(save_dir / self.ATTRIBUTES_FN, "w") as f:
            json.dump(
                dict(
                    IM_j=str(self.IM_j),
                    ensemble_params=self.ensemble.get_save_params(),
                    mw_bounds=self.mw_bounds,
                    rrup_bounds=self.rrup_bounds,
                    vs30_bounds=self.vs30_bounds,
                    sf_bounds=self.sf_bounds,
                    exceedance=self.exceedance,
                    im_value=self.im_value,
                ),
                f,
            )

        self.site_info.save(save_dir)

    @classmethod
    def load(cls, data_dir: Path):
        with open(data_dir / cls.ATTRIBUTES_FN, "r") as f:
            attributs_dict = json.load(f)

        return CausalParamBounds(
            gm_data.Ensemble.load(attributs_dict["ensemble_params"]),
            site.SiteInfo.load(data_dir),
            IM.from_str(attributs_dict["IM_j"]),
            attributs_dict["mw_bounds"],
            attributs_dict["rrup_bounds"],
            attributs_dict["vs30_bounds"],
            attributs_dict["sf_bounds"],
            contr_df=pd.read_csv(data_dir / cls.CONTRIBUTIONS_FN, index_col=0),
            exceedance=attributs_dict["exceedance"],
            im_value=attributs_dict["im_value"],
        )
