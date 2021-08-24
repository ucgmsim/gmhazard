import hashlib
from typing import TYPE_CHECKING, Dict, List, Union, Sequence

import numpy as np
import pandas as pd

import seistech_calc as si
from .Branch import Branch

if TYPE_CHECKING:
    from .Ensemble import Ensemble


class IMEnsemble:
    """
    Represents an IM-Ensemble

    Parameters
    ----------
    ims: sequence of IMType or IMType
        The IMs this IM-Ensemble supports
    ensemble: Ensemble
        The parent ensemble
    config: dictionary
        The IMEnsemble details from the ensemble config
    use_im_data_cache: bool
        If True then caching is used when retrieving
        values from the IMDBs
        Note: This can result in large memory usage very fast
    """

    def __init__(
        self,
        ims: Union[Sequence[si.im.IMType], si.im.IMType],
        ensemble: "Ensemble",
        config: Dict,
        use_im_data_cache: bool = False,
    ):

        self.ims = [ims] if isinstance(ims, si.im.IMType) else ims
        self._config = config
        self.ensemble = ensemble

        self.use_im_data_cache = use_im_data_cache
        self._im_data_cache = None

        # Load the branches of the ensemble
        self.branches_dict = {
            key: Branch(key, self, value) for key, value in self._config.items()
        }
        self.branches = list(self.branches_dict.values())
        self.branch_weights = {
            cur_name: cur_branch.weight
            for cur_name, cur_branch in self.branches_dict.items()
        }

        self._stations, self._rupture_df = None, None

        if si.im.IMType.pSA in self.ims:
            self.ims = set(list(self.branches[0].ims))
            for cur_branch in self.branches:
                self.ims.intersection_update(list(cur_branch.ims))
        else:
            self.ims = [si.im.IM(im) for im in self.ims]

        # Apply IM Components
        self.ims = np.asarray(
            [
                si.im.IM(cur_im.im_type, period=cur_im.period, component=cur_comp)
                for cur_im in self.ims
                for cur_comp in si.im.IM_COMPONENT_MAPPING[cur_im.im_type]
            ]
        )

    @property
    def stations(self) -> pd.DataFrame:
        if self._stations is None:
            branch_stations = set.intersection(
                *[set(branch.stations) for branch in self.branches_dict.values()]
            ).intersection(self.ensemble.stations_ll_df.index)

            self._stations = self.ensemble.stations_ll_df.loc[
                branch_stations
            ].sort_index()
        return self._stations

    @property
    def rupture_df(self) -> pd.DataFrame:
        if self._rupture_df is None:
            self._rupture_df = pd.concat(
                [branch.rupture_df for branch in self.branches_dict.values()]
            )

            # Combine the rupture dfs from the branches
            # & drop duplicates (based on index)
            self._rupture_df = self.rupture_df.groupby(self.rupture_df.index).first()
        return self._rupture_df

    @property
    def fault_rupture_df(self):
        return self.rupture_df.loc[
            self.rupture_df.rupture_type == si.constants.SourceType.fault.value, :
        ]

    @property
    def im_data_type(self):
        return (
            si.constants.IMDataType.mixed
            if len({cur_branch.im_data_type for cur_branch in self.branches}) > 1
            else self.branches[0].im_data_type
        )

    def check_im(self, im: si.im.IM):
        """Checks if the specified IM type is supported by
        the ensemble, otherwise raises an exception
        """
        if im not in self.ims:
            raise ValueError(
                f"The specified IM type {im} is not valid for this ensemble."
            )
