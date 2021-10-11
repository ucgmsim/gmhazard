import h5py
import numpy as np

from seistech_calc import utils
from seistech_calc import constants as const
from .BaseDB import BaseDB, check_open


class SiteSourceDB(BaseDB):
    """Class that handles retrieving/writing data with a SiteSourceDB"""

    def __init__(self, source_site_db_path: str, source_type=None, writeable=False):
        super().__init__(source_site_db_path, writeable=writeable)

        self._db_path = source_site_db_path

        if source_type is None:
            with h5py.File(self._db_path, mode="r") as h5_store:
                if "source_type" in h5_store.attrs.keys():
                    self._source_type = const.SourceType(
                        h5_store.attrs["source_type"].decode()
                    )
                else:
                    raise TypeError(
                        "database does not have an source_type, must specify one in the command"
                    )
        else:
            self._source_type = const.SourceType(source_type)

        self._db = None

        self._keys_cache = None

    @check_open
    def faults(self):
        """Get the faults/sources in the db"""
        return self._db["faults"]

    @check_open
    def stations(self):
        """Get the input stations/site info in the db"""
        return self._db["sites"]

    def stored_stations(self):
        """Get the stations that have data stored in the db"""
        pass

    @check_open
    def station_data(self, station_name: str):
        """Retrieves data for a specific station/site

        Parameters
        ----------
        station_name: str
            The station name for which to retrieve the data

        Returns
        -------
        pd.DataFrame
            with the available faults as index and properties as columns
        """
        try:
            df = self._db[self.station_distance_h5_key(station_name)]
        except KeyError:
            return None

        df.index = self.faults().loc[df.fault_id].fault_name
        return df.drop("fault_id", axis=1)

    @check_open
    def has_station_data(self, station_name):
        """
        Checks if there is data stored for the station.
        If a station was used as an input but did not contain data it will return false.
        :param station_name: Station to be checked
        :return: True if station has data, False otherwise
        """
        key = self.station_distance_h5_key(station_name)

        if not self._keys_cache:
            self._keys_cache = set(self._db.keys())

        return key in self._keys_cache

    @check_open
    def fault_station_data(self, station_name: str, fault_name: str):
        """Returns the properties for the specified source-site combination

        Parameters
        ----------
        station_name: str
            The station name
        fault_name:
            The fault name

        Returns
        -------
        pd.Series
        """
        raise NotImplementedError

    def write_attributes(self, erf_fname, station_list_fname, **kwargs):
        """
        Stores attributes into the ssd h5
        """
        super().write_attributes(
            source_type=np.string_(self._source_type.value),
            erf_fname=erf_fname,
            station_list_fname=station_list_fname,
            **kwargs,
        )

    @check_open
    def write_site_data(self, site_df):
        if utils.check_names(["lon", "lat"], site_df.columns.values):
            self._db["sites"] = site_df

    @check_open
    def write_fault_data(self, fault_df):
        if utils.check_names(["fault_name"], fault_df.columns.values):
            self._db["faults"] = fault_df
        else:
            raise ValueError(
                "Columns are not as expected. Must have 1 columns "
                "('fault_name') and an index"
            )

    @check_open
    def write_site_distances_data(self, station, distance_df):
        """
        fault_id is the index of the fault_name in the fault_data table

        The rest of the columns are distance values, set to nan if there is no calculation.

        """
        if utils.check_names(
            ["fault_id", "rjb", "rrup", "rx", "ry", "rtvz"], distance_df.columns.values
        ):
            self._db[self.station_distance_h5_key(station)] = distance_df
        else:
            raise ValueError(
                "Columns are not as expected. Must have 6 columns "
                "('fault_id', 'rjb', 'rrup', 'rx', 'ry', 'rtvz') and an index"
            )

    @staticmethod
    def station_distance_h5_key(name):
        return f"/distances/station_{name}"