from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from gmhazard_calc import utils
from gmhazard_calc import rupture
from gmhazard_calc import constants as const
from .Leaf import Leaf

if TYPE_CHECKING:
    from .IMEnsemble import IMEnsemble


class Branch:
    """Represents a branch of an Ensemble.

    Parameters
    ----------
    name: str
    im_ensemble: IMEnsemble
    config : dict
        Dictionary with initial details of the DataSet

    Attributes
    ----------
    name : str
        name is to be unique within an Ensemble
    im_ensemble: IMEnsemble
        The IM-Ensemble the branch belongs to
    rupture_df: dataframe
        The rupture dataframe of the branch
        format: index = rupture id
        columns = [rupture name, annual recurrence probability, magnitude]
    stations: array of strings
        Stations supported by the Branch
    ims: array of strings
        IMs supported by the Branch
    flt_im_data_type, ds_im_data_type: const.IMDataType
        The data type of the fault and distributed
        of the IM data, i.e. either parametric or non-parametric
    leafs_dict: dictionary
    leafs: list of strings
        The leafs of the branch
    weight : float
        The weight associated with this specific data set
    """

    def __init__(self, name: str, im_ensemble: "IMEnsemble", config: dict):
        self.name = name
        self.im_ensemble = im_ensemble
        self._config = config

        # Load when requested for the first time
        self.flt_erf_ffp = config["flt_erf"]
        self.ds_erf_ffp = config["ds_erf"]
        self._rupture_df = None
        self._flt_rupture_df, self._ds_rupture_df = None, None

        self.leafs_dict = {
            leaf_id: Leaf(
                leaf_id, self, leaf_config["flt_imdbs"], leaf_config["ds_imdbs"]
            )
            for leaf_id, leaf_config in self._config["leaves"].items()
        }
        self.leafs = list(self.leafs_dict.values())

        self.weight = config["weight"]

        self._stations = None

        # Temporary until we define IM type as
        # an object instead of string
        self._ims = None

        self._flt_im_data_type, self._ds_im_data_type = None, None

    @property
    def stations(self) -> np.ndarray:
        """Available stations of the branch, defined as
        the intersection of the stations of all leafs
        of the branch"""
        if self._stations is None:
            flt_stations = [leaf.flt_stations for leaf in self.leafs]
            ds_stations = [leaf.ds_stations for leaf in self.leafs]

            self._stations = np.asarray(
                list(
                    set(np.concatenate(flt_stations)) | set(np.concatenate(ds_stations))
                )
            )

        return self._stations

    @property
    def flt_rupture_df(self):
        """Standardised dataframe that contains
        information for fault ruptures, format:
        index = rupture id
        columns = [rupture name, annual recurrence probability, magnitude]
        """
        if self._flt_rupture_df is None:
            self._flt_rupture_df = self.im_ensemble.ensemble.load_erf(
                self.flt_erf_ffp,
                const.ERFFileType.from_str(self._config["flt_erf_type"]),
            )
        return self._flt_rupture_df

    @property
    def ds_rupture_df(self):
        """Standardised dataframe that contains
        information for ds ruptures, format:
        index = rupture id
        columns = [rupture name, annual recurrence probability, magnitude]
        """
        if self._ds_rupture_df is None:
            self._ds_rupture_df = self.im_ensemble.ensemble.load_erf(
                self.ds_erf_ffp, const.ERFFileType.from_str(self._config["ds_erf_type"])
            )

        return self._ds_rupture_df

    @property
    def rupture_df_id_ix(self) -> pd.DataFrame:
        """Standardised dataframe that contains
        information for fault and ds ruptures, format:
        index = rupture id ix
        columns = [rupture name, annual recurrence probability, magnitude, tectonic type]
        """
        return pd.concat([self.flt_rupture_df, self.ds_rupture_df], sort=True)

    @property
    def rupture_df_id(self) -> pd.DataFrame:
        """Standardised dataframe that contains
        information for fault and ds ruptures, format:
        index = rupture id
        columns = [rupture name, annual recurrence probability, magnitude, tectonic type]
        """
        rupture_df = pd.concat([self.flt_rupture_df, self.ds_rupture_df], sort=True)
        return rupture_df.set_index(
            rupture.rupture_id_ix_to_rupture_id(
                self.im_ensemble.ensemble, rupture_df.index.values
            ),
            inplace=False,
        )

    @property
    def flt_erf_name(self) -> str:
        return utils.get_erf_name(self.flt_erf_ffp)

    @property
    def ds_erf_name(self) -> str:
        return utils.get_erf_name(self.ds_erf_ffp)

    @property
    def ims(self):
        """The IM types supported by the branch"""
        if self._ims is None:
            self._ims = set(list(self.leafs[0].ims))
            for cur_leaf in self.leafs[1:]:
                self._ims.intersection_update(list(cur_leaf.ims))

            self._ims = np.asarray(list(self._ims))
        return self._ims

    def get_imdb_ffps(self, source_type: const.SourceType) -> np.ndarray:
        """Gets the IMDBs ffps for the specified source type
        from all the leafs of the current branch"""
        return np.concatenate(
            [
                cur_leaf.flt_imdb_ffps
                if source_type is const.SourceType.fault
                else cur_leaf.ds_imdb_ffps
                for cur_leaf in self.leafs
            ]
        )

    def rupture_name_to_id(
        self, rupture_names: np.ndarray, source_type: const.SourceType
    ):
        """
        Converts rupture names to rupture ids, using the branch erf file for the
        specified source type.

        Parameters
        ----------
        rupture_names: np.ndarray
            1D numpy array of rupture names to convert, has
            to be of type str (i.e. np.unicode or np.string)
        source_type: const.SourceType
            The source type, which determines which erf file to use
            as postfix

        Returns
        -------
        np.ndarray
        """
        return rupture.rupture_name_to_id(
            rupture_names,
            self.flt_erf_ffp
            if source_type is const.SourceType.fault
            else self.ds_erf_ffp,
        )

    @property
    def im_data_type(self):
        return (
            const.IMDataType.mixed
            if self.ds_im_data_type is not self.flt_im_data_type
            else self.flt_im_data_type
        )

    @property
    def flt_im_data_type(self):
        if self._flt_im_data_type is None:
            for leaf in self.leafs:
                try:
                    assert (
                        self._flt_im_data_type is leaf.flt_im_data_type
                        or leaf.flt_im_data_type is None
                        or self._flt_im_data_type is None
                    )
                except AssertionError:
                    raise AssertionError(
                        "The fault IMDBs of a branch has to be the same source type"
                    )
                if leaf.flt_im_data_type is not None:
                    self._flt_im_data_type = leaf.flt_im_data_type
        return self._flt_im_data_type

    @property
    def ds_im_data_type(self):
        if self._ds_im_data_type is None:
            for leaf in self.leafs:
                try:
                    assert (
                        self._ds_im_data_type is leaf.ds_im_data_type
                        or leaf.ds_im_data_type is None
                        or self._ds_im_data_type is None
                    )
                except AssertionError:
                    raise AssertionError(
                        "Some of the benchmark tests failed, "
                        "check the output to determine which ones failed."
                    )
                if leaf._ds_im_data_type is not None:
                    self._ds_im_data_type = leaf.ds_im_data_type
        return self._ds_im_data_type
