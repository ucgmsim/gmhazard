"""Contains the classes that represent the different distributions used for GMS"""

from typing import Dict, Sequence

import pandas as pd
import numpy as np


class CondIMjDist:
    """Represents any distribution
    that is conditional on IMj

    Parameters
    ----------
    See the Attributes

    Attributes
    ----------
    IMj: string
        Conditioning IM name
    im_j: float
        Conditioning IM value
    """

    def __init__(self, IMj: str, im_j: float):
        self.IMj, self.im_j = IMj, im_j


class UniIMiDist:
    """Represents any univariate
    IMi distribution

    Parameters
    ----------
    See the Attributes

    Attributes
    ----------
    IMi: string
    """

    def __init__(self, IMi: str):
        self.IMi = IMi


class Uni_lnIMi_IMj_Rup(UniIMiDist, CondIMjDist):
    """Represents the (parametric) univariate
    lognormal IMi|IMj,Rup distribution
    for each rupture

    Parameters
    ----------
    See the Attributes

    Attributes
    ----------
    mu, sigma: series
        The mean & sigma values
        (i.e. mu_IMi|IMj,Rup and sigma_IMi|IMj,Rup)
        for each rupture
    """

    def __init__(
        self, mu: pd.Series, sigma: pd.Series, IMi: str, IMj: str, im_j: float
    ):
        UniIMiDist.__init__(self, IMi)
        CondIMjDist.__init__(self, IMj, im_j)

        self.mu, self.sigma = mu, sigma

    @staticmethod
    def combine(uni_lnIMi_IMj_Rup: Dict[str, "Uni_lnIMi_IMj_Rup"]):
        IMs = np.asarray(list(uni_lnIMi_IMj_Rup.keys()))
        mu_df = pd.concat([uni_lnIMi_IMj_Rup[IMi].mu for IMi in IMs], axis=1)
        sigma_df = pd.concat([uni_lnIMi_IMj_Rup[IMi].sigma for IMi in IMs], axis=1)
        mu_df.columns, sigma_df.columns = IMs, IMs

        return mu_df, sigma_df


class Multi_lnIM_IMj_Rup(CondIMjDist):
    """Represents the (parametric) multivariate
    lognormal IM|IMj,Rup (where IM is the vector
    of IMi)

    Parameters
    ----------
    See the Attributes

    Attributes
    ----------
    mu, sigma: dataframe
        The mean & sigma values for
        each IMi and Rup
        format: index = rupture, columns = IMi
    rho: dataframe
        The correlation matrix of the IMi,
        i.e. rho_lnIM|IMj,Rup
    IMs: sequence of strings
        The different IMi this multivariate
         distribution is for
    """

    def __init__(
        self,
        mu: pd.DataFrame,
        sigma: pd.DataFrame,
        rho: pd.DataFrame,
        IMs: Sequence[str],
        IMj: str,
        im_j: float,
    ):
        super().__init__(IMj, im_j)

        self.IMs = IMs
        self.rho = rho
        self.mu, self.sigma = mu, sigma


class Uni_lnIMi_IMj(UniIMiDist, CondIMjDist):
    """Represents the non-parametric IMi|IMj distribution

    Parameters
    ----------
    See the Attributes

    Attributes
    ----------
    cdf: series
        The CDF values for the distribution
        format: index = IMi values, y = P(IMi =< imi)
    mu, sigma: float
        The calculated mean and standard deviation, however these
        do not specify the distribution (since it is non-parametric) and
        are only included for the case when multiple Uni_lnIMi_IMj distributions
        are combined (e.g. for a logic tree case), in which case these values are
        used to compute the lnIMi values of the resulting non-parametric CDF.
        Otherwise these parameters/attributes should just be ignored.
    """

    def __init__(
        self,
        cdf: pd.Series,
        IMi: str,
        IMj: str,
        im_j: float,
        mu: float = None,
        sigma: float = None,
    ):
        UniIMiDist.__init__(self, IMi)
        CondIMjDist.__init__(self, IMj, im_j)

        self.cdf = cdf

        self.mu = mu
        self.sigma = sigma

    def compatible(self, other: "Uni_lnIMi_IMj"):
        return (
            self.IMi == other.IMi and self.IMj == other.IMj and self.im_j == other.im_j
        )
