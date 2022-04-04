from pathlib import Path
from typing import TYPE_CHECKING, List

import numpy as np

from gmhazard_calc import dbs
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM, IMType

if TYPE_CHECKING:
    from .Branch import Branch


class Leaf:
    """
    Represents a Leaf of a Branch

    Parameters
    ----------
    branch: Branch
    flt_imdb_ffps: list of IMDBs
    ds_imdb_ffps: list of IMDBs
    id: str

    Attributes
    ----------
    branch: Branch
        The Branch the leaf is part of
    flt_imdb_ffps: list of IMDBs
    ds_imdb_ffps: list of IMDBs
        The fault and distributed seismicity
        IMDBs that make up this leaf
    model: str
        The model used for the leaf
    tec_type: str
        The tectonic type of the model for the leaf
    id: str
    stations: list of strings
        Available stations of the Leaf, defined as:
            [fault_db_1 | fault_db_2 | fault_db_3 | ...] & [ds_db_1 | ds_db_2 | ...]
    ims: list of IMs
        Available IMs of the Leaf, defined as:
            Intersection of IMs across all IMDBS
    im_data_type: IMDataType
        The type of the IM data, either
        parametric or non-parametric
    """

    def __init__(
        self,
        id: str,
        branch: "Branch",
        flt_imdb_ffps: List[str],
        ds_imdb_ffps: List[str],
    ):
        self.id = id
        self.branch = branch
        self.flt_imdb_ffps = flt_imdb_ffps
        self.ds_imdb_ffps = ds_imdb_ffps

        # Grabs the model and tec_type from the ffps available in the leaf
        path = (
            Path(flt_imdb_ffps[0]) if len(flt_imdb_ffps) != 0 else Path(ds_imdb_ffps[0])
        )
        split_fp = path.stem.split("_")
        self.model = "_".join(split_fp[:2])
        self.tec_type = "_".join(split_fp[2:-1])

        self._flt_stations, self._ds_stations, self._ims = None, None, None
        self._flt_im_data_type, self._ds_im_data_type = None, None

        # Have to use a separate variable, as some
        # metadata values can be None
        self._metadata_loaded = False

    def __load_IMDB_metadata(self) -> None:
        """Get available IMs and stations of the leaf"""
        self._flt_stations, self._ds_stations = [], []
        for cur_imdb_ffp in self.flt_imdb_ffps + self.ds_imdb_ffps:
            with dbs.IMDB.get_imdb(cur_imdb_ffp) as cur_imdb:
                # Stations
                if cur_imdb_ffp in self.flt_imdb_ffps:
                    self._flt_stations.append(
                        cur_imdb.sites().index.values.astype(str)
                    )
                elif cur_imdb_ffp in self.ds_imdb_ffps:
                    self._ds_stations.append(
                        cur_imdb.sites().index.values.astype(str)
                    )

                # IMs (intersection of IMs across all dbs)
                if self._ims is None:
                    self._ims = set(
                        [
                            IM.from_str(im_string)
                            for im_string in cur_imdb.ims
                            if IMType.has_value(im_string)
                        ]
                    )
                else:
                    self._ims.intersection_update(
                        [
                            IM.from_str(im_string)
                            for im_string in cur_imdb.ims
                            if IMType.has_value(im_string)
                        ]
                    )

                # IM data type
                if cur_imdb.source_type is const.SourceType.fault:
                    if self._flt_im_data_type is None:
                        self._flt_im_data_type = cur_imdb.imdb_type
                    assert self._flt_im_data_type is cur_imdb.imdb_type, (
                        "IM data types have to match across IMDBs of "
                        "the same source type"
                    )
                if cur_imdb.source_type is const.SourceType.distributed:
                    if self._ds_im_data_type is None:
                        self._ds_im_data_type = cur_imdb.imdb_type
                    assert self._ds_im_data_type is cur_imdb.imdb_type, (
                        "IM data types have to match across IMDBs of "
                        "the same source type"
                    )

        self._flt_stations = (
            np.concatenate(self._flt_stations)
            if len(self._flt_stations) >= 1
            else np.asarray(self._flt_stations)
        )
        self._ds_stations = (
            np.concatenate(self._ds_stations)
            if len(self._ds_stations) >= 1
            else np.asarray(self._ds_stations)
        )

        self._metadata_loaded = True

    @property
    def flt_stations(self) -> np.ndarray:
        if self._metadata_loaded is False:
            self.__load_IMDB_metadata()
        return self._flt_stations

    @property
    def ds_stations(self) -> np.ndarray:
        if self._metadata_loaded is False:
            self.__load_IMDB_metadata()
        return self._ds_stations

    @property
    def ims(self) -> np.ndarray:
        if self._metadata_loaded is False:
            self.__load_IMDB_metadata()
        return np.asarray(list(self._ims))

    @property
    def flt_im_data_type(self):
        if self._metadata_loaded is False:
            self.__load_IMDB_metadata()
        return self._flt_im_data_type

    @property
    def ds_im_data_type(self):
        if self._metadata_loaded is False:
            self.__load_IMDB_metadata()
        return self._ds_im_data_type
