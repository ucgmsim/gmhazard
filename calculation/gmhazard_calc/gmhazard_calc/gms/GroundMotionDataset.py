import os
from glob import glob
from pathlib import Path
from shutil import copyfile
from typing import Tuple, List, Any, Sequence

import pandas as pd
import numpy as np
import yaml

from qcore.timeseries import BBSeis
from qcore import simulation_structure as ss

import sha_calc as sha
from gmhazard_calc.im import IM, IMType, to_im_list, to_string_list
from gmhazard_calc import site
from gmhazard_calc import constants
from gmhazard_calc import dbs
from .CausalParamBounds import CausalParamBounds


def load_gm_dataset_configs():
    data = {}
    GM_DATASET_CONFIG_PATH = os.getenv("GM_DATASET_CONFIG_PATH")

    if GM_DATASET_CONFIG_PATH is None:
        return data

    cfgs = glob(os.path.join(GM_DATASET_CONFIG_PATH, "*.yaml"))

    for i, c in enumerate(cfgs):
        u_name = os.path.basename(c)[:-5]
        with open(c) as y:
            data[u_name] = yaml.safe_load(y)

    return data


class GMDataset:
    """Represents a ground motion source for
    ground motion selection

    Parameters
    ----------
    name: str
        Name of ground motion source
    """

    gms_sources = load_gm_dataset_configs()

    def __init__(self, name):
        self.name = name
        self._config = self.gms_sources[name]

    @property
    def ims(self):
        raise NotImplementedError()

    def get_waveforms(
        self, gms: Sequence[Any], site_info: site.SiteInfo, output_dir: str
    ) -> List:
        """Retrieves and saves the waveforms as text
        files in the specified output directory

        Parameters
        ----------
        gms: list of tuple of strings
            The selected ground motions, tuple has to be
            of format (rupture_name, simulation_name)
        site_info: SiteInfo
        output_dir: str
        """
        raise NotImplementedError()

    def get_im_df(
        self,
        site_info: site.SiteInfo,
        IMs: Sequence[str],
        cs_param_bounds: CausalParamBounds = None,
        sf: pd.Series = None,
    ) -> pd.DataFrame:
        """
        Gets the IM dataframe for the ground motions in this dataset

        If filter_params is specified then all records that aren't
        within the specified bounds are dropped

        If a scaling factor is specified for a HistoricalGMDataset, then
        the IM values are amplitude scaled accordingly before being returned
        Note I: This does not update the underlying IM dataframe of the dataset!
        Note II: This parameter is completely ignored for SimulationGMDataset

        Parameters
        ----------
        site_info: SiteInfo
            Site of interest
        IMs: array of IM
            The IMs of interest
        cs_param_bounds: CausalFilterParams, optional
            The causal filter parameters to use
        sf: series, optional
            The scaling factor for each GM, only relevant for
            HistoricalGMDataset, leave as None for SimulationGMDataset

        Returns
        -------
        dataframe
        """
        raise NotImplementedError()

    def get_metadata_df(
        self, site_info: site.SiteInfo, selected_gms: Sequence[Any] = None
    ) -> pd.DataFrame:
        """
        Gets the metadata dataframe

        Parameters
        ----------
        site_info: SiteInfo, optional
            Site of interest, not relevant historical GM dataset
        selected_gms: list, optional
            The ids of the selected ground motions

        Returns
        -------
        dataframe
        """
        raise NotImplementedError

    def get_n_gms_in_bounds(
        self,
        metadata_df: pd.DataFrame,
        cs_param_bounds: CausalParamBounds,
        ignore_vs30: bool = False,
    ):
        """Returns the number of ground motions in
        the specified causal parameter bounds
        """
        if cs_param_bounds is None:
            return metadata_df.shape[0]

        return np.count_nonzero(
            self._get_filter_mask(metadata_df, cs_param_bounds, ignore_vs30=ignore_vs30)
        )

    def _get_filter_mask(
        self,
        metadata_df: pd.DataFrame,
        cs_param_bounds: CausalParamBounds,
        ignore_vs30: bool = False,
    ) -> np.ndarray:
        mask = np.ones(metadata_df.shape[0], dtype=bool)
        if cs_param_bounds.mw_low is not None:
            mask &= (metadata_df.mag.values > cs_param_bounds.mw_low) & (
                metadata_df.mag.values < cs_param_bounds.mw_high
            )
        if cs_param_bounds.rrup_low is not None:
            mask &= (metadata_df.rrup.values > cs_param_bounds.rrup_low) & (
                metadata_df.rrup.values < cs_param_bounds.rrup_high
            )
        if cs_param_bounds.vs30_low is not None and not ignore_vs30:
            mask &= (metadata_df.vs30.values > cs_param_bounds.vs30_low) & (
                metadata_df.vs30.values < cs_param_bounds.vs30_high
            )

        return mask

    @staticmethod
    def get_GMDataset(name: str) -> "GMDataset":
        """Creates an GMDataset instance for the specified GMDataset ID"""
        config = GMDataset.gms_sources[name]
        gms_type = constants.GMSourceType(config["type"])

        if gms_type is constants.GMSourceType.simulations:
            return SimulationGMDataset(name)
        elif gms_type is constants.GMSourceType.historical:
            return HistoricalGMDataset(name)
        else:
            return MixedGMDataset(name)


class HistoricalGMDataset(GMDataset):
    """
    Represents dataset of historical GM records

    Supports filtering of records via CausalParamBounds
    """

    def __init__(self, name):
        super().__init__(name)

        # Historical
        self.empirical_IM_csv_ffp = self._config["empirical_IM_csv_ffp"]
        self.empirical_GMS_dir = Path(self._config["empirical_GMs_dir"])

        self._im_df = pd.read_csv(self.empirical_IM_csv_ffp, index_col=0)

        # Remove duplicates
        self._im_df = self._im_df.loc[~self._im_df.index.duplicated()]

    @property
    def ims(self):
        # Get all IMs from the dataframe columns that are supported by GMHazard
        return [
            IM.from_str(cur_col)
            for cur_col in self._im_df.columns
            if IMType.has_value(cur_col)
        ]

    @property
    def gm_ids(self):
        return self._im_df.index.values

    def get_waveforms(
        self, gms: List[Any], site_info: site.SiteInfo, output_dir: str
    ) -> List:
        """See GMDataset method for parameter specifications"""
        no_waveforms = []
        file_name_template = "RSN{}_{}.AT2"
        output_dir = Path(output_dir)
        for gm in gms:
            if (self.empirical_GMS_dir / file_name_template.format(gm, 1)).is_file():
                copyfile(
                    self.empirical_GMS_dir / file_name_template.format(gm, 1),
                    output_dir / file_name_template.format(gm, 1),
                )
                copyfile(
                    self.empirical_GMS_dir / file_name_template.format(gm, 2),
                    output_dir / file_name_template.format(gm, 2),
                )
                if (
                    self.empirical_GMS_dir / file_name_template.format(gm, 3)
                ).is_file():
                    copyfile(
                        self.empirical_GMS_dir / file_name_template.format(gm, 3),
                        output_dir / file_name_template.format(gm, 3),
                    )
            else:
                no_waveforms.append(gm)

        return no_waveforms

    def get_im_df(
        self,
        site_info: site.SiteInfo,
        IMs: Sequence[str],
        cs_param_bounds: CausalParamBounds = None,
        sf: pd.Series = None,
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        im_df = self._im_df.copy().loc[:, IMs]
        metadata_df = self.get_metadata_df(site_info)

        # CS Param bounds filtering
        if cs_param_bounds is not None:
            mask = (
                np.ones(im_df.shape[0], dtype=bool)
                if cs_param_bounds is None
                else self._get_filter_mask(
                    metadata_df.loc[im_df.index], cs_param_bounds
                )
            )
            im_df = im_df.loc[mask]

        # Apply amplitude scaling, if a scaling factor is given
        if sf is not None:
            # Perform filtering based on SF
            mask = (
                np.ones(im_df.shape[0], dtype=bool)
                if cs_param_bounds is None
                else self._get_filter_mask(
                    metadata_df.loc[im_df.index], cs_param_bounds, sf=sf
                )
            )
            im_df = im_df.loc[mask]

            # Sanity check
            if sf.shape[0] < im_df.shape[0]:
                print(
                    "WARNING: Scaling factors have only been provided for a subset "
                    "of available GMs, all GMs without a SF specified will be ignored!"
                )

            # Scale GMs
            im_df = sha.apply_amp_scaling(im_df, sf.loc[mask])

        return im_df

    def compute_scaling_factor(
        self,
        IMj: IM,
        im_j: float,
        gm_ids: np.ndarray = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Scales the GM records such that IMj == imj

        Parameters
        ----------
        gm_ids: array of strings
            The ground motion IDs to amplitude scale
        IMj: IM
        im_j: float
            The IM and its value, used to compute the scaling factor
        IMs: string
            The IMs to scale

        Returns
        -------
        series:
            The scaling factor for each of the specified GMs
        """
        gm_ids = self._im_df.index.values if gm_ids is None else gm_ids

        return sha.compute_scaling_factor(str(IMj), im_j, self._im_df.loc[gm_ids, :])

    def apply_amp_scaling(self, sf: pd.Series):
        """
        Applies amplitude to the specified GMs

        Parameters
        ----------
        sf: series
            The scaling factor for each GM of interest
            index: GM ids, value: scaling factor

        Returns
        -------
        dataframe:
            The scaled IMs
        """
        return

    def get_metadata_df(
        self, site_info: site.SiteInfo, selected_gms: List[Any] = None
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        meta_df = pd.read_csv(self.empirical_IM_csv_ffp, index_col=0).loc[
            :, ["mag", "rrup", "vs30"]
        ]

        # Drop duplicates
        meta_df = meta_df.loc[~meta_df.index.duplicated()]

        if selected_gms is not None:
            return meta_df.loc[selected_gms]
        return meta_df

    def _get_filter_mask(
        self,
        metadata_df: pd.DataFrame,
        cs_param_bounds: CausalParamBounds,
        ignore_vs30: bool = False,
        sf: pd.Series = None,
    ) -> np.ndarray:
        if sf is not None:
            assert sf.shape[0] == metadata_df.shape[0]

        mask = super()._get_filter_mask(
            metadata_df, cs_param_bounds, ignore_vs30=ignore_vs30
        )

        if sf is not None and cs_param_bounds.sf_low is not None:
            mask &= (sf.values > cs_param_bounds.sf_low) & (
                sf.values < cs_param_bounds.sf_high
            )

        return mask


class SimulationGMDataset(GMDataset):
    """
    Represents Simulation GM dataset

    Used for site-specific GM selection,
    i.e. only supports simulation based GMS and
        does not support filtering by CausalParamBounds
        as only simulations from the site
        of interest are used
    """

    def __init__(self, name: str):
        super().__init__(name)

        # Simulation
        self.imdb_ffps = self._config["simulations_imdbs"]
        self.simulation_dirs = [
            Path(cur_dir) for cur_dir in self._config["simulations_dirs"]
        ]
        self.source_metadata_df = pd.read_csv(
            self._config["source_metadata_ffp"], index_col=0
        )

        self.vs30_params_csv_ffp = self._config["vs30_params_csv_ffp"]
        self.site_source_db_ffp = self._config["site_source_db_ffp"]

        self._ims = None

    @property
    def ims(self):
        if self._ims is None:
            for cur_imdb_ffp in self.imdb_ffps:
                with dbs.IMDBNonParametric(cur_imdb_ffp) as imdb:
                    cur_ims = [im for im in imdb.ims if IMType.has_value(im)]
                    if self._ims is None:
                        self._ims = set(cur_ims)
                    else:
                        self._ims.intersection_update(cur_ims)

        self._ims = to_im_list(list(self._ims))

        return self._ims

    def get_waveforms(
        self, gms: List[str], site_info: site.SiteInfo, output_dir: str
    ) -> List:
        """See GMDataset method for parameter specifications"""
        return _get_sim_waveforms(self.simulation_dirs, gms, site_info, output_dir)

    def get_im_df(
        self,
        site_info: site.SiteInfo,
        IMs: Sequence[str],
        cs_param_bounds: CausalParamBounds = None,
        **kwargs,
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        im_dfs = []
        for cur_imdb_ffp in self.imdb_ffps:
            with dbs.IMDBNonParametric(cur_imdb_ffp) as db:
                cur_im_data = db.im_data(site_info.station_name)
                if cur_im_data is None:
                    continue

                im_dfs.append(cur_im_data.reset_index(0))

        if len(im_dfs) == 0:
            raise ValueError(f"No IM data found for station {site_info.station_name}")
        im_df = pd.concat(im_dfs, axis=0)

        if cs_param_bounds is not None:
            raise ValueError(
                "CausalParamBounds should not be specified for "
                "simulation based GMS as it is already site-specific"
            )

        return im_df.loc[:, IMs]

    def get_metadata_df(
        self, site_info: site.SiteInfo, selected_gms: List[Any] = None
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        vs30_df = pd.read_csv(
            self.vs30_params_csv_ffp,
            names=["station", "vs30"],
            delimiter="\s+",
            index_col="station",
        )
        site_vs30 = float(vs30_df.loc[site_info.station_name])

        # Site-source dataframe
        site_source_df = _get_site_source_df(
            self.site_source_db_ffp, site_info.station_name
        )

        if selected_gms is not None:
            meta_data = []
            for cur_rel in selected_gms:
                meta_data.append(
                    (
                        self.source_metadata_df.loc[cur_rel, "mag"],
                        site_source_df.loc[cur_rel.split("_")[0]].rrup,
                        site_vs30,
                    )
                )
            meta_df = pd.DataFrame.from_records(meta_data, index=selected_gms)
            meta_df.columns = ["mag", "rrup", "vs30"]
        else:
            meta_df = pd.merge(
                self.source_metadata_df,
                site_source_df,
                how="left",
                left_on="fault",
                right_index=True,
            )
            meta_df["vs30"] = site_vs30
            meta_df = meta_df[["fault", "mag", "rrup", "vs30"]]

        return meta_df


class MixedGMDataset(GMDataset):
    """
    GM dataset that consists of both
    observed and simulation records

    For the case where GMS is run using
    an parametric ensemble, but set of available
    GM records to select from is supplemented with
    simulations

    Note: Currently only supports selecting from simulations
    Todo: Complete this
    """

    def __init__(self, name):
        super().__init__(name)

        # Simulation
        self.imdb_ffps = self._config["simulations"]["imdbs"]
        self.simulation_dirs = self._config["simulations"]["waveforms_dirs"]
        self.source_metadata_df = pd.read_csv(
            self._config["simulations"]["source_metadata_ffp"], index_col=0
        )

        self.vs30_params_csv_ffp = self._config["simulations"]["vs30_params_csv_ffp"]
        self.site_source_db_ffp = self._config["simulations"]["site_source_db_ffp"]
        self.sources_dir = Path(self._config["simulations"]["sources_dir"])

        self._ims = None

    @property
    def ims(self):
        if self._ims is None:
            for cur_imdb_ffp in self.imdb_ffps:
                with dbs.IMDBNonParametric(cur_imdb_ffp) as imdb:
                    cur_ims = [im for im in imdb.ims if IMType.has_value(im)]
                    if self._ims is None:
                        self._ims = set(cur_ims)
                    else:
                        self._ims.intersection_update(cur_ims)

        self._ims = to_im_list(list(self._ims))

        return self._ims

    def get_waveforms(
        self, gms: Sequence[Any], site_info: site.SiteInfo, output_dir: str
    ) -> List:
        """See GMDataset method for parameter specifications"""
        return _get_sim_waveforms(self.simulation_dirs, gms, site_info, output_dir)

    def get_im_df(
        self,
        site_info: site.SiteInfo,
        IMs: Sequence[str],
        cs_param_bounds: CausalParamBounds = None,
        sf: pd.Series = None,
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        if cs_param_bounds is None:
            # Need some sanity checking here to
            # as the number of records could be massive
            raise NotImplementedError()

        # Filter based on Vs30
        vs30_df = pd.read_csv(
            self.vs30_params_csv_ffp,
            names=["station", "vs30"],
            delimiter="\s+",
            index_col="station",
        )
        vs30_mask = (vs30_df.vs30 >= cs_param_bounds.vs30_low) & (
            vs30_df.vs30 <= cs_param_bounds.vs30_high
        )
        station_ids = vs30_df.index.values.astype(str)[vs30_mask]

        # Filter realisations based on magnitude
        realisations = self.source_metadata_df.loc[
            (self.source_metadata_df.mag >= cs_param_bounds.mw_low)
            & (self.source_metadata_df.mag <= cs_param_bounds.mw_high)
        ].index.values.astype(str)

        im_dfs = []

        # Iterate over each IMDB and get the
        # data for all available stations
        with dbs.SiteSourceDB(
            self.site_source_db_ffp, constants.SourceType.fault
        ) as ssdb:
            for cur_imdb_ffp in self.imdb_ffps:
                with dbs.IMDBNonParametric(cur_imdb_ffp) as db:
                    # Iterate over each station
                    for cur_station_id in station_ids:
                        # Get the IM data
                        cur_im_df = db.im_data(cur_station_id, im=IMs)
                        if cur_im_df is None:
                            continue

                        cur_im_df = cur_im_df.reset_index(0)
                        cur_im_df["site"] = cur_station_id

                        # Identify faults that meet rrup bounds
                        cur_dist_df = ssdb.station_data(cur_station_id)
                        cur_faults = cur_dist_df.loc[
                            (cur_dist_df.rrup >= cs_param_bounds.rrup_low)
                            & (cur_dist_df.rrup <= cs_param_bounds.rrup_high)
                        ].index.values.astype(str)

                        # Filter based on rrup
                        cur_im_df = cur_im_df.loc[np.isin(cur_im_df.fault, cur_faults)]

                        # Filter based on mag
                        cur_im_df = cur_im_df.loc[
                            np.isin(cur_im_df.index.values, realisations)
                        ]

                        if cur_im_df.shape[0] > 0:
                            im_dfs.append(cur_im_df)

        im_df = pd.concat(im_dfs, axis=0)

        # Give each GM record a unique id
        im_df.index = np.char.add(
            np.char.add(im_df.index.values.astype(str), "_"),
            im_df.site.values.astype(str),
        )
        im_df = im_df.loc[:, IMs]

        # Apply amp scaling if specified
        if sf is not None:
            # Sanity check
            if not np.all(sf.index == im_df.index):
                raise ValueError(
                    "The scaling factor and IM dataframe indices have to match"
                )

            if cs_param_bounds.sf_bounds is not None:
                mask = (sf >= cs_param_bounds.sf_low) & (sf <= cs_param_bounds.sf_high)
                sf = sf.loc[mask]
                im_df = im_df.loc[mask]

            im_df = sha.apply_amp_scaling(im_df, sf)

        return im_df

    def get_metadata_df(
        self, site_info: site.SiteInfo, selected_gms: Sequence[Any] = None
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        vs30_df = pd.read_csv(
            self.vs30_params_csv_ffp,
            names=["station", "vs30"],
            delimiter="\s+",
            index_col="station",
        )

        # Site-source dataframe
        if selected_gms is not None:
            rel_ids = [cur_id.rsplit("_", maxsplit=1)[0] for cur_id in selected_gms]
            faults = [cur_rel_id.split("_")[0] for cur_rel_id in rel_ids]
            sites = [cur_id.rsplit("_", maxsplit=1)[1] for cur_id in selected_gms]

            meta_data = []
            for cur_rel_id, cur_fault, cur_site_name in zip(rel_ids, faults, sites):
                cur_site_source_df = _get_site_source_df(
                    self.site_source_db_ffp, cur_site_name
                )

                meta_data.append(
                    (
                        self.source_metadata_df.loc[cur_rel_id, "mag"],
                        cur_site_source_df.loc[cur_fault].rrup,
                        vs30_df.loc[cur_site_name, "vs30"],
                    )
                )
            meta_df = pd.DataFrame.from_records(meta_data, index=selected_gms)
            meta_df.columns = ["mag", "rrup", "vs30"]
        else:
            # This would be massive, as it would encompass all site-source combinations
            raise NotImplementedError()

            # meta_df = pd.merge(
            #     self.source_metadata_df,
            #     site_source_df,
            #     how="left",
            #     left_on="fault",
            #     right_index=True,
            # )
            # meta_df["vs30"] = site_vs30
            # meta_df = meta_df[["fault", "mag", "rrup", "vs30"]]

        return meta_df


def _get_site_source_df(site_source_db_ffp: Path, site_name: str):
    with dbs.SiteSourceDB(str(site_source_db_ffp), constants.SourceType.fault) as ssdb:
        return ssdb.station_data(site_name)


def _get_sim_waveforms(
    simulation_dirs: Sequence[Path],
    gms: Sequence[Any],
    site_info: site.SiteInfo,
    output_dir: str,
) -> List:
    no_waveforms = []
    for sim_name in gms:
        # Find & Save the binary waveform
        for cur_dir in simulation_dirs:
            # Check that simulation directory exists
            if (cur_sim_dir := Path(ss.get_sim_dir(str(cur_dir), sim_name))).exists():
                # Find the BB file
                if len(bb_ffps := list(cur_sim_dir.rglob("*BB.bin"))) == 1:
                    # Convert to text files and store in the specified output directory
                    cur_bb = BBSeis(bb_ffps[0])
                    cur_bb.save_txt(
                        site_info.station_name, prefix=f"{output_dir}/{sim_name}_"
                    )
                    continue

            no_waveforms.append(sim_name)
    return no_waveforms
