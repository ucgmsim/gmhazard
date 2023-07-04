import itertools
import multiprocessing as mp
from contextlib import contextmanager
from typing import Optional, Dict, List, Union, Sequence

import h5py
import tables
import numpy as np
import pandas as pd

from gmhazard_calc import utils
from gmhazard_calc import constants as const
from gmhazard_calc.im import IM
from .BaseDB import BaseDB, check_open


def get_station_ruptures(imdb_ffp: str, station: str):
    """Gets all ruptures names for a specific station

    Note I: Only for internal use by the add_rupture_lookup function
    Note II: Has to be outside of the class, as it is called using
    MP which does not support class or static methods
    """
    with IMDB.get_imdb(imdb_ffp) as db:
        if isinstance(db, IMDBNonParametric):
            im_data = db.im_data(station)
            if im_data is not None:
                return im_data.index.levels[0].values.astype(str)
        elif isinstance(db, IMDBParametric):
            im_data = db.im_data(station)
            if im_data is not None:
                return im_data.index.values.astype(str)


class IMDB(BaseDB):

    # Attributes of the databases
    IMDB_TYPE = "imdb_type"
    IMS_KEY = "ims"

    def __init__(
        self, db_ffp: str, writeable: bool = False, source_type: const.SourceType = None
    ):
        super().__init__(db_ffp, writeable=writeable)

        # Set the source type
        if source_type is None:
            with h5py.File(self.db_ffp, mode="r") as h5_store:
                if "source_type" in h5_store.attrs.keys():
                    self._source_type = const.SourceType(
                        h5_store.attrs["source_type"].decode()
                    )
                else:
                    raise TypeError(
                        "Database does not have a source_type, "
                        "must specify one in the command"
                    )
        else:
            self._source_type = const.SourceType(source_type)

    @property
    def source_type(self) -> const.SourceType:
        return self._source_type

    @property
    @check_open
    def imdb_type(self) -> const.IMDataType:
        """Either parametric or non_parametric"""
        im_format_type = self.attributes.get(self.IMDB_TYPE)

        if im_format_type is None:
            raise Exception(
                "The provided db file is not a valid IMBD as it is"
                " missing the im_type attribute, which specifies "
                "whether the data is in a parametric format or "
                "non-parametric format."
            )
        return const.IMDataType(im_format_type)

    @property
    @check_open
    def ims(self) -> np.ndarray:
        """Array of IMs stored in the db"""
        return self.attributes[self.IMS_KEY]

    @check_open
    def sites(self) -> pd.DataFrame:
        """Retrieves the sites which were processed during creation of this db.

        Note: This does not mean that data exists for every station, as some stations
        do not have any data associated with them, hence there is no
        entry in im_data for these.


        Returns
        -------
        pd.DataFrame:
            index = station name, columns = [lat, lon]
        """
        return self._db["sites"]

    @check_open
    def rupture_data(self, rupture_name: str, im: Optional[IM] = None):
        """
        Gets the IM values for all stations for a specific rupture

        Parameters
        ----------
        rupture_name: str
            Rupture of interest
        im: IM, optional

        Returns
        -------
        im_values: pd.DataFrame or pd.Series
            Returns dataframe if no im is specified, format
                multi index = (station, simulation), columns = IM values
            If an im is specified returns a series of format
                multi index = (station, simulation), value = im value
        """
        stations = None
        try:
            stations = self._db.get(self.get_rupture_lookup_path(rupture_name))
        except KeyError:
            pass

        if stations is None or stations.size == 0:
            return None
        stations = stations.values.astype(str)

        # Collect the data from each station
        # If this is ever to slow, this can be easily multi-processed using
        # pool and writing a function that just reads the IM data for a
        # given imdb_ffp and station.
        station_data = []
        for cur_station in stations:
            cur_im_data = self.im_data(cur_station, im=im).loc[rupture_name]
            if im is None and isinstance(cur_im_data, pd.Series):
                cur_im_data = cur_im_data.to_frame().T

            station_data.append(cur_im_data)

        df = pd.concat(station_data, axis=0, keys=stations, sort=False)
        return df

    def rupture_names(self) -> np.ndarray:
        """Returns an array with the names of all the ruptures
        for which there is a data in the IMDB

        Implemented by the specialisation classes
        """
        raise NotImplementedError

    def im_data(self, station: str, im: Optional[IM] = None):
        """Retrieves the IM data, implemented by
        the specialisation classes
        """
        raise NotImplementedError

    @check_open(writeable=True)
    def write_sites(self, site_df: pd.DataFrame) -> None:
        """Write the sites

        Parameters
        ----------
        site_df: pd.DataFrame
            index = station name, columns = [lat, lon]
        """
        if utils.check_names(["lon", "lat"], site_df.columns.values):
            self._db["sites"] = site_df

    @check_open(writeable=True)
    def write_im_data(self, station_name: str, im_df: pd.DataFrame) -> None:
        """Writes the IM data for the specified station

        Parameters
        ----------
        station_name: str
        im_df: pd.DataFrame
            The dataframe to write
        """
        self._db[self.get_im_data_path(station_name)] = im_df

    @check_open(writeable=True)
    def add_im_data(self, station_name: str, im_df: pd.DataFrame) -> None:
        """Adds the given IM df to the existing IM df for the specified station
        If no entry for this station exists one is created

        Parameters
        ----------
        station_name: str
        im_df: pd.DataFrame
            The dataframe to write
        """
        path = self.get_im_data_path(station_name)

        # Check if there is already an existing entry for this station
        # Using try/except instead of checking .keys as it is sig. faster
        cur_df = None
        try:
            cur_df = self._db[path]
        except KeyError:
            pass

        if cur_df is not None:
            # Check that the number of ruptures match
            assert cur_df.shape[0] == im_df.shape[0]

            # Delete the existing one
            self._db.remove(path)

            # Create updated
            cur_df = pd.concat([cur_df, im_df], axis=1)
        else:
            cur_df = im_df
        # Write
        self.write_im_data(station_name, cur_df)

    @check_open(writeable=True)
    def write_rupture_lookup(self, rupture_lookup: Dict[str, List[str]]):
        for cur_rup, cur_stations in rupture_lookup.items():
            # Save as series (index is meaningless)
            self._db[self.get_rupture_lookup_path(cur_rup)] = pd.Series(
                data=cur_stations
            )

    @staticmethod
    def get_im_data_path(station: str) -> str:
        """Returns the database path for the IM data of the specified station"""
        return f"/im_data/station_{station}"

    @staticmethod
    def get_rupture_lookup_path(rupture_name: str) -> str:
        """Returns the database path for the event based data links"""
        return f"/rupture_lookup/rupture_{rupture_name}"

    @staticmethod
    @contextmanager
    def get_imdb(imdb_ffp: str, writeable: bool = False) -> "IMDB":
        """Creates a contextmanager for the appropriate IMDB instance,
        based on the im_db_type
        """
        with h5py.File(imdb_ffp, mode="r") as h:
            imdb_type = h.attrs[IMDB.IMDB_TYPE].decode()
        if imdb_type == const.IMDataType.non_parametric.value:
            imdb = IMDBNonParametric(imdb_ffp, writeable=writeable)
        elif imdb_type == const.IMDataType.parametric.value:
            imdb = IMDBParametric(imdb_ffp, writeable=writeable)
        else:
            raise Exception(
                f"The specified IMDB has a im_db_type attribute of {imdb_type}, "
                f"which is not valid, has to be either "
                f"{const.IMDataType.non_parametric.value} or "
                f"{const.IMDataType.parametric.value}"
            )
        imdb.open()
        yield imdb
        imdb.close()

    @staticmethod
    def add_rupture_lookup(db_ffp: str, n_procs: int):
        """
        Add a lookup to get stations for each rupture and to get the full list of rupture names
        WARNING:
        Could take a long time for large DB's such as a Distributed Seismicity db
        Should only be used for a Fault db

        Parameters
        ----------
        db_ffp: str
            Full file path to the db file to add the rupture lookup
        n_procs: int
            Number of processes to use
        """
        with IMDB.get_imdb(db_ffp) as db:
            stations = db.sites().index.values

        # Iterate over all stations and get all ruptures for each station
        print("Collecting ruptures for each station")
        with mp.Pool(n_procs) as pool:
            result = pool.starmap(
                get_station_ruptures,
                [(db_ffp, cur_station) for cur_station in stations],
            )

        # Invert the result, i.e. for each rupture get all stations
        print("Computing rupture lookup")
        rupture_lookup = {}
        for cur_station, cur_ruptures in zip(stations, result):
            if cur_ruptures is not None:
                for cur_rup in cur_ruptures:
                    if cur_rup in rupture_lookup.keys():
                        rupture_lookup[cur_rup].append(cur_station)
                    else:
                        rupture_lookup[cur_rup] = [cur_station]

        # Write
        print("Writing")
        with IMDB.get_imdb(db_ffp, writeable=True) as db:
            db.write_rupture_lookup(rupture_lookup)
            db.write_attributes(
                rupture_names=np.asarray(list(rupture_lookup.keys()), dtype=str)
            )

    @check_open
    def get_stored_stations(self):
        return [
            stat.split("im_data/")[-1].replace("station_", "")
            for stat in self._db.keys()
        ]


class IMDBParametric(IMDB):
    def __init__(
        self, db_ffp: str, writeable: bool = False, source_type: const.SourceType = None
    ):
        super().__init__(db_ffp, writeable=writeable, source_type=source_type)

    @property
    def imdb_type(self) -> const.IMDataType:
        """Required for when database is opened in write mode"""
        if self.writeable:
            return const.IMDataType.parametric
        else:
            return super().imdb_type

    @check_open
    def _ruptures(self) -> pd.Series:
        """Returns a dataframe of all the ruptures in the IMDB

        Format: index = imdb_rupture_id, values = rupture_name
        """
        return self._db["ruptures"]

    @check_open()
    def rupture_names(self) -> Union[None, np.ndarray]:
        """Returns an array with the names of all the ruptures
        for which there is a data in the IMDB

        Note: This will only return values if rupture based
        lookup has been added to this IMDB, otherwise returns None
        """
        return self.get_attributes().get("rupture_names")

    @check_open
    def im_data(
        self,
        station: str,
        im: Optional[Union[List[IM], IM]] = None,
        incl_within_between_sigma: bool = False,
    ) -> Union[pd.DataFrame, pd.Series, None]:
        """Retrieves the IM parameters for the ruptures
        at a specific site

        Parameters
        ----------
        station: str
        im: IM or list[IM], optional
            IM(s) of interest
            if this is unspecified then it is equivalent to setting all IMs
        incl_within_between_sigma: bool
            Boolean flag to determine to either extract mu and total standard deviation or
            mu, between-event and within-event standard deviation

        Returns
        -------
        im_params, pd.DataFrame or None
            If an im is specified returns a df of format
                index = rupture, columns = [mu, sigma]
            Otherwise returns a dataframe of format
                index = rupture,
                columns = [im_1_mean, im_1_std, im_2_mean, im_2_std...]
            Returns None if there is no data in the IMDB for that station
        """
        df = None
        try:
            df = self._db.get(self.get_im_data_path(station))
        except KeyError:
            pass

        if df is None or df.size == 0:
            return None

        # Performance hack, replaces the following line of code
        # df.index = self._ruptures().loc[df.index.values, "rupture_name"].values.astype(str)
        with tables.open_file(self.db_ffp, mode="r") as fileh:
            lookup_indices = fileh.root.ruptures.table.read_coordinates(
                df.index.values
            )["values_block_0"].reshape(-1)
            df.index = fileh.root.ruptures.meta.values_block_0.meta.table.read_coordinates(
                lookup_indices
            )[
                "values"
            ].astype(
                str
            )

        if im is not None:
            ims = im if isinstance(im, list) else [im]
            # Setting columns to extract from the DB
            if incl_within_between_sigma:
                single_im_columns = ["mu", "between_event_sigma", "within_event_sigma"]
                im_columns = list(
                    (
                        itertools.chain(
                            *[
                                (f"{im}", f"{im}_sigma_inter", f"{im}_sigma_intra")
                                for im in set(ims)
                            ]
                        )
                    )
                )
            else:
                single_im_columns = ["mu", "sigma"]
                im_columns = list(
                    (itertools.chain(*[(f"{im}", f"{im}_sigma") for im in set(ims)]))
                )
            df = df.loc[:, im_columns]
            if len(ims) == 1:
                df.columns = single_im_columns
        return df

    @check_open(writeable=True)
    def write_attributes(
        self, erf_ffp: str = None, station_list_ffp: str = None, **kwargs
    ):
        """Writes the relevant parametric attributes in the database

        The erf_ffp and station_list_ffp, should be set
        when the database is written initially.
        """
        super().write_attributes(
            erf_ffp=erf_ffp,
            station_list_ffp=station_list_ffp,
            source_type=self._source_type.value,
            imdb_type=self.imdb_type.value,
            **kwargs,
        )

    @check_open(writeable=True)
    def write_rupture_data(self, rupture_df: pd.DataFrame) -> None:
        """Writes the rupture names to the database"""
        if utils.check_names(["rupture_name"], rupture_df.columns.values):
            self._db.put("ruptures", rupture_df, format="t")


class IMDBNonParametric(IMDB):
    def __init__(
        self,
        db_ffp: str,
        writeable: Optional[bool] = False,
        source_type: const.SourceType = None,
    ):
        super().__init__(db_ffp, writeable=writeable, source_type=source_type)
        self.writeable = writeable

        self._attrs = None

    @property
    def imdb_type(self) -> const.IMDataType:
        """Required for when database is opened in write mode"""
        if self.writeable:
            return const.IMDataType.non_parametric
        else:
            return super().imdb_type

    def rupture_names(self) -> np.ndarray:
        """Returns an array with the names of all the ruptures
        for which there is a data in the IMDB
        """
        ruptures = self.get_attributes().get("rupture_names")
        if ruptures is not None:
            return ruptures

        return np.unique(
            np.array(
                list(
                    np.char.split(
                        self.simulations().values.astype(str), "_", maxsplit=1
                    )
                )
            )[:, 0]
        )

    @check_open
    def simulations(self) -> pd.Series:
        """Retrieves the simulations in this imdb

        Returns
        -------
        pd.Series
            Index = simulation index, values = simulation names
        """
        return self._db["simulations"]

    @check_open
    def im_data(
        self, station: str, im: Optional[Union[Sequence[str], str]] = None
    ) -> Union[None, pd.DataFrame, pd.Series]:
        """Retrieves the IM dataframe for all
        simulations for the specified station

        Parameters
        ----------
        station: str
        im: IM or list[IM], optional
            IM(s) of interest
            if this is unspecified then it is equivalent to setting all IMs

        Returns
        -------
        im_values: pd.DataFrame or pd.Series
            If a single im is specified returns a series of format
                multi index = (rupture, simulation), value = im value
            Otherwise Returns dataframe with the specified format
                multi index = (rupture, simulation), columns = IM values
        """
        df = None
        try:
            df = self._db.get(self.get_im_data_path(station))
        except KeyError:
            pass

        if df is None or df.size == 0:
            return None

        simulations = self.simulations()
        df["realisation"] = simulations.iloc[df.index.values].values
        df["fault"] = np.stack(
            np.char.split(df.realisation.values.astype(str), "_", maxsplit=1)
        )[:, 0]
        df.sort_values(["fault", "realisation"], inplace=True)

        # Create hierarchical dataframe index (fault, realisation)
        df.index = pd.MultiIndex.from_frame(df.loc[:, ["fault", "realisation"]])
        df.drop(columns=["fault", "realisation"], inplace=True)

        if im is not None:
            return df[im]
        return df

    @check_open(writeable=True)
    def write_attributes(self, **kwargs):
        """Writes the relevant parametric attributes in the database"""
        super().write_attributes(
            imdb_type=np.string_(self.imdb_type.value),
            source_type=np.string_(self._source_type.value),
            **kwargs,
        )

    @check_open(writeable=True)
    def write_simulations(self, simulations: pd.Series) -> None:
        """Writes the simulations

        Parameters
        ----------
        simulations: pd.Series
            index = simulation id, values = simulation name
        """
        if not isinstance(simulations, pd.Series):
            raise ValueError(
                "Has to be a pd.Series with id as index and simulation names as values"
            )
        self._db["simulations"] = simulations
