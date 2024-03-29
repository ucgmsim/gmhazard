import os
import hashlib
from glob import glob
from typing import Dict, TYPE_CHECKING

import yaml
import numpy as np
import pandas as pd

from gmhazard_calc import utils
from gmhazard_calc import rupture
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM, IMType, IMComponent
from qcore.formats import load_station_file
from .IMEnsemble import IMEnsemble

if TYPE_CHECKING:
    from gmhazard_calc.site.SiteInfo import SiteInfo


def load_data():
    data = {}
    ENSEMBLE_CONFIG_PATH = os.getenv("ENSEMBLE_CONFIG_PATH")

    if ENSEMBLE_CONFIG_PATH is None:
        return data

    cfgs = glob(os.path.join(ENSEMBLE_CONFIG_PATH, "*.yaml"))

    for i, c in enumerate(cfgs):
        u_name = os.path.basename(c)[:-5]
        with open(c) as y:
            data[u_name] = yaml.safe_load(y)

    return data


ensemble_dict = load_data()


class Ensemble:
    """Represents an ensemble of DataSets.

    Parameters
    ----------
    name : str
        name of the ensemble self._config
    config_ffp: string, optional
        If given, then the specified file will be
         used as ensemble config
    use_im_data_cache: bool, optional
        If True, all retrieved IM values from any
        IMDB are stored in a cache for speedup of calculations
        that use the same (or overlapping) IM values
        The cache exists for the life time of the ensemble instance
        Default is False
    lazy_loading: bool, optional
        If True, then properties such as stations, IMs and rupture_df are
        loaded lazily. Otherwise they are loaded on instance creation.

    Attributes
    ----------
    name : str
        Name of the ensemble
    im_ensembles_dict: dictionary
        Dictionary of the IMEnsembles that make up
        this ensemble with the IM as key
    ims: list of IM
        IMs available in this ensemble.
    """

    def __init__(
        self,
        name: str,
        config_ffp: str = None,
        use_im_data_cache: bool = False,
        lazy_loading: bool = True,
    ):
        self.name, self._config_ffp = name, config_ffp

        if config_ffp is None:
            self._config = ensemble_dict[name]
        else:
            with open(config_ffp, "r") as f:
                self._config = yaml.safe_load(f)

        # Stations from the stations file, does NOT define the
        # supported stations of the ensemble, use the stations property
        self.stations_ll_df = load_station_file(self._config["stations"])

        # Load the IMEnsembles
        self.im_ensembles_dict = {
            IMType[im_string]: IMEnsemble(
                IMType[im_string],
                self,
                self._config["datasets"][im_string],
                use_im_data_cache=use_im_data_cache,
            )
            for im_string in self._config["datasets"]
        }
        self.im_ensembles = list(self.im_ensembles_dict.values())

        # Load the vs30 values
        self.vs30_df = (
            None
            if self._config.get("vs30") is None
            else pd.read_csv(
                self._config["vs30"],
                delim_whitespace=True,
                index_col=0,
                header=None,
                names=["vs30"],
            )
        )

        # Load the Z values
        self.z_df = (
            None
            if self._config.get("z") is None
            else pd.read_csv(
                self._config["z"],
                delim_whitespace=True,
                header=None,
                index_col=0,
                names=["Z1.0", "Z2.5"],
            )
        )

        self.flt_ssddb_ffp = self._config["flt_ssdb"]
        self.ds_ssddb_ffp = self._config["ds_ssdb"]

        self._stations, self._rupture_df = None, None
        self._ims = None

        # Create the rupture_id lookup, needed as rupture_ids are very long and
        # therefore use a significant amount of memory for ensembles with
        # a large number of branches
        # rupture_id = "-41.8_172.0_10.0--6.8_ACTIVE_SHALLOW_NZ_DSmodel_2015"
        # rupture_id_ix = 0 (an integer)
        self._rupture_id_ix_lookup = None

        # IM data cache to reduce number of IMDB reads required
        # Note: This cache is purely in memory and exists per
        # Ensemble instance
        self.use_im_data_cache = use_im_data_cache
        self._im_data_cache = {} if self.use_im_data_cache else None

        # Rupture dfs of the branches, not to be used by the ensemble directly
        # purely exists to prevent duplicate loading of rupture dfs by branches
        # with the same rupture erf
        self._branch_rupture_dfs = {}

        self._is_simple = None

        if not lazy_loading:
            self.__load_rupture_df()
            self.__load_stations()

    @property
    def is_simple(self):
        """
        True if each IMEnsemble only has a
        single branch with weight = 1
        """
        if self._is_simple is None:
            self._is_simple = all(
                [
                    len(cur_im_ens.branches) == 1
                    and cur_im_ens.branches[0].weight == 1.0
                    for cur_im_ens in self.im_ensembles
                ]
            )
        return self._is_simple

    @property
    def flt_im_data_type(self):
        return (
            const.IMDataType.mixed
            if len({cur_branch.flt_im_data_type for cur_branch in self.im_ensembles}) > 1
            else self.im_ensembles[0].flt_im_data_type
        )

    @property
    def ds_im_data_type(self):
        return (
            const.IMDataType.mixed
            if len({cur_branch.ds_im_data_type for cur_branch in self.im_ensembles}) > 1
            else self.im_ensembles[0].ds_im_data_type
        )

    @property
    def stations(self):
        """Dataframe of available stations in the ensemble, defined as
        the intersection of the stations of the different IMEnsembles
        Format: index = station_name, columns = lon, lat"""
        if self._stations is None:
            self.__load_stations()

        return self._stations

    @property
    def ims(self):
        if self._ims is None:
            self.__load_ims()
        return self._ims

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
            rupture.rupture_id_ix_to_rupture_id(self, self._rupture_df.index.values)
        )

    @property
    def fault_rupture_df(self):
        return self.rupture_df_id.loc[
            self.rupture_df_id.rupture_type == const.SourceType.fault.value, :
        ]

    @property
    def station_ffp(self):
        return self._config["stations"]

    def get_rupture_id_indices(self, rupture_ids: np.ndarray):
        """Gets the rupture_id_ix values for the given rupture_ids
        Adds any missing rupture ids to the lookup
        """
        # Add ids if needed
        missing_ids = np.unique(
            rupture_ids[
                ~utils.pandas_isin(rupture_ids, self._rupture_id_ix_lookup.index.values)
            ]
            if self._rupture_id_ix_lookup is not None
            else rupture_ids
        )
        if missing_ids.size > 0:
            last_rupture_id_ix = (
                -1
                if self._rupture_id_ix_lookup is None
                else self._rupture_id_ix_lookup.values.max()
            )

            self._rupture_id_ix_lookup = pd.concat(
                (
                    self._rupture_id_ix_lookup,
                    pd.Series(
                        index=missing_ids,
                        data=np.arange(
                            last_rupture_id_ix + 1,
                            last_rupture_id_ix + missing_ids.shape[0] + 1,
                        ),
                    ),
                )
            )

        # Ensure that there are no duplicates in the lookup
        assert (
            self._rupture_id_ix_lookup.index.unique().size
            == self._rupture_id_ix_lookup.size
        )

        # Get indices
        return self._rupture_id_ix_lookup.loc[rupture_ids].values

    def get_rupture_ids(self, rupture_id_ind: np.ndarray):
        """Convert rupture id indices to rupture ids"""
        result = self._rupture_id_ix_lookup.iloc[rupture_id_ind].index.values.astype(
            str
        )

        return result

    def load_erf(self, erf_ffp: str, erf_type: const.ERFFileType):
        """This function should only be used by Branches, for
        the ensemble erf, use the rupture_df property!!
        """
        if erf_ffp in self._branch_rupture_dfs.keys():
            return self._branch_rupture_dfs[erf_ffp]
        else:
            rupture_df = rupture.rupture_df_from_erf(erf_ffp, erf_type)
            rupture_df["rupture_type"] = (
                "flt" if erf_type == const.ERFFileType.flt_nhm else "ds"
            )

            # Convert to rupture id ix
            rupture_df.index = self.get_rupture_id_indices(rupture_df.index.values)

            self._branch_rupture_dfs[erf_ffp] = rupture_df
            return rupture_df

    def get_im_ensemble(self, im_type: IMType) -> IMEnsemble:
        return self.im_ensembles_dict[im_type]

    def check_im(self, im: IM):
        """Checks if the specified IM type is supported by
        the ensemble, otherwise raises an exception
        """
        if im not in self.ims:
            raise ValueError(
                f"The specified IM type {im} is not valid for this ensemble."
            )

    def _get_cache_key(self, site_info: "SiteInfo", imdb_ffp: str):
        """Returns the IM data cache key for the specified site and IMBD file"""
        return hashlib.sha256(f"{site_info}_{imdb_ffp}".encode()).hexdigest()

    def get_cache_value(self, site_info: "SiteInfo", imdb_ffp: str):
        """Gets the IM dataframe from the IM data cache, returns False if
        no entry is available for the specified site and IMDB file"""
        key = self._get_cache_key(site_info, imdb_ffp)
        if self.use_im_data_cache and key in self._im_data_cache.keys():
            return (
                self._im_data_cache[key].copy()
                if self._im_data_cache[key] is not None
                else None
            )
        return False

    def update_cache(self, site_info: "SiteInfo", imdb_ffp: str, im_data: pd.DataFrame):
        """Adds a IM data cache entry for the specified site and IMDB file"""
        key = self._get_cache_key(site_info, imdb_ffp)
        if self.use_im_data_cache and key not in self._im_data_cache.keys():
            self._im_data_cache[key] = im_data.copy() if im_data is not None else None
            return True
        return False

    def clear_cache(self):
        """Empties the cache"""
        self._im_data_cache = {} if self._im_data_cache is not None else None

    def get_save_params(self):
        """Returns a dictionary that contains all parameters
        required for loading of the ensemble"""
        return {
            "name": self.name,
            "config_ffp": self._config_ffp,
            "use_im_data_cache": self.use_im_data_cache,
        }

    @classmethod
    def load(cls, ensemble_params: Dict):
        config_ffp = ensemble_params.get("config_ffp")
        if config_ffp is not None:
            return cls(
                ensemble_params["name"],
                config_ffp=config_ffp,
                use_im_data_cache=ensemble_params["use_im_data_cache"],
            )

        return cls(
            ensemble_params["name"],
            use_im_data_cache=ensemble_params["use_im_data_cache"],
        )

    def get_component_ims(self, component: IMComponent):
        return [cur_im for cur_im in self.ims if cur_im.component is component]

    def __load_stations(self):
        station_ids = set(list(self.im_ensembles[0].stations.index.values.astype(str)))
        for cur_im_ensemble in self.im_ensembles[1:]:
            station_ids.intersection_update(
                list(cur_im_ensemble.stations.index.values.astype(str))
            )
        self._stations = self.stations_ll_df.loc[list(station_ids)]

    def __load_rupture_df(self):
        for im_ensemble in self.im_ensembles:
            if self._rupture_df is None:
                self._rupture_df = im_ensemble.rupture_df_id_ix
            else:
                # Append and drop duplicates
                self._rupture_df = pd.concat(
                    [self._rupture_df, im_ensemble.rupture_df_id_ix]
                )
                self._rupture_df = self._rupture_df.loc[
                    ~self._rupture_df.index.duplicated()
                ]

    def __load_ims(self):
        self._ims = list(
            set(np.concatenate([im_ensemble.ims for im_ensemble in self.im_ensembles]))
        )
