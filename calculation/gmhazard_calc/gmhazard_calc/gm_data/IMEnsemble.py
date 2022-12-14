from typing import TYPE_CHECKING, Dict, Union, Sequence

import numpy as np
import pandas as pd

from gmhazard_calc import rupture
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM, IMType, IM_COMPONENT_MAPPING
from .Branch import Branch

if TYPE_CHECKING:
    from .Ensemble import Ensemble


class IMEnsemble:
    """
    Represents an IM-Ensemble

    Parameters
    ----------
    im_types: sequence of IMType or IMType
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
        im_types: Union[Sequence[IMType], IMType],
        ensemble: "Ensemble",
        config: Dict,
        use_im_data_cache: bool = False,
        lazy_loading: bool = True,
    ):
        self._im_types = [im_types] if isinstance(im_types, IMType) else im_types
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
        self._ims = None

        if not lazy_loading:
            self.__load_ims()
            self.__load_rupture_df()
            self.__load_stations()

    @property
    def ims(self):
        if self._ims is None:
            self.__load_ims()

        return self._ims

    @property
    def stations(self) -> pd.DataFrame:
        if self._stations is None:
            self.__load_stations()

        return self._stations

    @property
    def rupture_df_id_ix(self) -> pd.DataFrame:
        if self._rupture_df is None:
            self.__load_rupture_df()

        return self._rupture_df

    @property
    def rupture_df_id(self) -> pd.DataFrame:
        if self._rupture_df is None:
            self.__load_rupture_df()

        return self._rupture_df.set_index(
            rupture.rupture_id_ix_to_rupture_id(
                self.ensemble, self._rupture_df.index.values
            )
        )

    @property
    def fault_rupture_df(self):
        return self.rupture_df_id.loc[
            self.rupture_df_id.rupture_type == const.SourceType.fault.value, :
        ]

    @property
    def im_data_type(self):
        return (
            const.IMDataType.mixed
            if len({cur_branch.im_data_type for cur_branch in self.branches}) > 1
            else self.branches[0].im_data_type
        )

    @property
    def flt_im_data_type(self):
        return (
            const.IMDataType.mixed
            if len({cur_branch.flt_im_data_type for cur_branch in self.branches}) > 1
            else self.branches[0].flt_im_data_type
         )

    @property
    def ds_im_data_type(self):
        return (
            const.IMDataType.mixed
            if len({cur_branch.ds_im_data_type for cur_branch in self.branches}) > 1
            else self.branches[0].ds_im_data_type
        )

    def check_im(self, im: IM):
        """Checks if the specified IM is supported by
        the ensemble, otherwise raises an exception
        """
        if im not in self.ims:
            raise ValueError(
                f"The specified IM type {im} is not valid for this ensemble."
            )

    def __load_rupture_df(self):
        # Identify all unique ERFs, and then use corresponding branches to
        # create IMEnsemble rupture dataframe
        _, flt_ind = np.unique(
            [cur_branch.flt_erf_ffp for cur_branch in self.branches], return_index=True
        )
        _, ds_ind = np.unique(
            [cur_branch.ds_erf_ffp for cur_branch in self.branches], return_index=True
        )
        branch_ind = np.concatenate((flt_ind, ds_ind))

        for ix in branch_ind:
            cur_branch = self.branches[ix]
            if self._rupture_df is None:
                self._rupture_df = cur_branch.rupture_df_id_ix
            else:
                # Append and drop duplicates
                self._rupture_df = pd.concat(
                    [self._rupture_df, cur_branch.rupture_df_id_ix]
                )
                self._rupture_df = self._rupture_df.loc[
                    ~self._rupture_df.index.duplicated()
                ]

    def __load_ims(self):
        if IMType.pSA in self._im_types:
            self._ims = set(list(self.branches[0].ims))
            for cur_branch in self.branches:
                self._ims.intersection_update(list(cur_branch.ims))

            # Ensure only ims of IMType.pSA are exposed
            self._ims = [cur_im for cur_im in self._ims if cur_im.im_type == IMType.pSA]
        else:
            self._ims = [IM(im) for im in self._im_types]

        # Apply IM Components
        self._ims = np.asarray(
            [
                IM(cur_im.im_type, period=cur_im.period, component=cur_comp)
                for cur_im in self._ims
                for cur_comp in IM_COMPONENT_MAPPING[cur_im.im_type]
            ]
        )

    def __load_stations(self):
        branch_stations = list(
            set.intersection(
                *[set(branch.stations) for branch in self.branches_dict.values()]
            ).intersection(self.ensemble.stations_ll_df.index)
        )

        self._stations = self.ensemble.stations_ll_df.loc[branch_stations].sort_index()
