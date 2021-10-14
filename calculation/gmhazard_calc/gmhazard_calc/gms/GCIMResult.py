import json
from pathlib import Path
from typing import Dict

import pandas as pd

import sha_calc as sha_calc
from gmhazard_calc.im import IM
from gmhazard_calc import gm_data


class BranchUniGCIM(sha_calc.UniIMiDist, sha_calc.CondIMjDist):
    """Represents the GCIM for a specific IMi and branch

    Parameters:
    -----------
    See Attributes

    Attributes:
    -----------
    IMi: IM
        IM Object of the IMi
    IMj: IM
        Conditioning IM
    im_j: float
        Value of the conditioning IM
    branch: Branch
    lnIMi_IMj_Rup: Uni_lnIMi_IMj_Rup
        Conditional lnIMi|IMj,Rup distributions
    lnIMi_IMj: Uni_lnIMi_IMj
        Marginal lnIMi|IMj distribution
    """

    VARIABLES_FN = "variables.json"
    LNIMI_IMJ_RUP_MU_FN = "lnIMi_IMj_rup_mu_fn.csv"
    LNIMI_IMJ_RUP_SIGMA_FN = "lnIMi_IMj_rup_sigma_fn.csv"
    LNIMI_IMJ_CDF_FN = "lnIMi_IMj_fn.csv"

    def __init__(
        self,
        IMi: IM,
        IMj: IM,
        im_j: float,
        branch: gm_data.Branch,
        lnIMi_IMj_Rup: sha_calc.Uni_lnIMi_IMj_Rup,
        lnIMi_IMj: sha_calc.Uni_lnIMi_IMj,
    ):
        sha_calc.UniIMiDist.__init__(self, IMi)
        sha_calc.CondIMjDist.__init__(self, IMj, im_j)

        self.branch = branch

        self.lnIMi_IMj_Rup = lnIMi_IMj_Rup
        self.lnIMi_IMj = lnIMi_IMj

    def save(self, base_dir: Path):
        save_dir = base_dir / self.branch.name
        save_dir.mkdir(exist_ok=False)

        with open(save_dir / self.VARIABLES_FN, "w") as f:
            json.dump(
                dict(
                    IMi=str(self.IMi),
                    IMj=str(self.IMj),
                    im_j=self.im_j,
                    branch_name=self.branch.name,
                ),
                f,
            )

        self.lnIMi_IMj_Rup.mu.to_csv(save_dir / self.LNIMI_IMJ_RUP_MU_FN)
        self.lnIMi_IMj_Rup.sigma.to_csv(save_dir / self.LNIMI_IMJ_RUP_SIGMA_FN)
        self.lnIMi_IMj.cdf.to_csv(save_dir / self.LNIMI_IMJ_CDF_FN)

    @classmethod
    def load(cls, data_dir: Path, branch: gm_data.Branch):
        with open(data_dir / f"{cls.VARIABLES_FN}", "r") as f:
            variables_dict = json.load(f)
        assert branch.name == variables_dict["branch_name"]

        IMi = IM.from_str(variables_dict["IMi"])
        IMj, im_j = IM.from_str(variables_dict["IMj"]), variables_dict["im_j"]

        lnIMi_IMj_Rup = sha_calc.Uni_lnIMi_IMj_Rup(
            pd.read_csv(data_dir / cls.LNIMI_IMJ_RUP_MU_FN, index_col=0).squeeze(),
            pd.read_csv(data_dir / cls.LNIMI_IMJ_RUP_SIGMA_FN, index_col=0).squeeze(),
            IMi,
            IMj,
            im_j,
        )

        lnIMi_IMj = sha_calc.Uni_lnIMi_IMj(
            pd.read_csv(data_dir / cls.LNIMI_IMJ_CDF_FN, index_col=0).squeeze(),
            IMi,
            IMj,
            im_j,
        )

        return cls(IMi, IMj, im_j, branch, lnIMi_IMj_Rup, lnIMi_IMj)


class IMEnsembleUniGCIM(sha_calc.UniIMiDist, sha_calc.CondIMjDist):
    """Represents the GCIM for a specific IMi and IMEnsemble

    Parameters:
    -----------
    See Attributes

    Attributes:
    -----------
    im_ensemble: IMEnsemble
    IMi: IM
        IM Object of the IMi
    IMj: IM
        Conditioning IM
    im_j: float
        Value of the conditioning IM
    branch_uni_gcims: dictionary
        Dictionary of the branch GCIM's that
        make up this combined GCIM
    """

    VARIABLES_FN = "variables.json"
    LNIMI_IMJ_CDF_FN = "lnIMi_IMj_cdf.csv"

    def __init__(
        self,
        im_ensemble: gm_data.IMEnsemble,
        IMi: IM,
        IMj: IM,
        im_j: float,
        ln_IMi_IMj: sha_calc.Uni_lnIMi_IMj,
        branch_uni_gcims: Dict[str, BranchUniGCIM],
    ):
        sha_calc.UniIMiDist.__init__(self, IMi)
        sha_calc.CondIMjDist.__init__(self, IMj, im_j)

        self.lnIMi_IMj = ln_IMi_IMj
        self.im_ensemble = im_ensemble

        self.branch_uni_gcims = branch_uni_gcims

    def save(self, base_dir: Path):
        save_dir = base_dir / f"{self.IMi}"
        save_dir.mkdir(exist_ok=False)

        with open(save_dir / self.VARIABLES_FN, "w") as f:
            json.dump(dict(IMi=str(self.IMi), IMj=str(self.IMj), im_j=self.im_j), f)

        self.lnIMi_IMj.cdf.to_csv(save_dir / self.LNIMI_IMJ_CDF_FN)

        for cur_branch_name, branch_gcim in self.branch_uni_gcims.items():
            branch_gcim.save(save_dir)

    @classmethod
    def load(cls, data_dir: Path, im_ensemble: gm_data.IMEnsemble):
        with open(data_dir / cls.VARIABLES_FN, "r") as f:
            variables_dict = json.load(f)

        IMi = IM.from_str(variables_dict["IMi"])
        IMj, im_j = IM.from_str(variables_dict["IMj"]), variables_dict["im_j"]

        sha_calc.Uni_lnIMi_IMj(
            pd.read_csv(data_dir / cls.LNIMI_IMJ_CDF_FN, index_col=0).squeeze(),
            IMi,
            IMj,
            im_j,
        )

        return cls(
            im_ensemble,
            IMi,
            IMj,
            im_j,
            sha_calc.Uni_lnIMi_IMj(
                pd.read_csv(data_dir / cls.LNIMI_IMJ_CDF_FN, index_col=0).squeeze(),
                IMi,
                IMj,
                im_j,
            ),
            {
                cur_branch_name: BranchUniGCIM.load(
                    data_dir / cur_branch_name, cur_branch
                )
                for cur_branch_name, cur_branch in im_ensemble.branches_dict.items()
            },
        )
