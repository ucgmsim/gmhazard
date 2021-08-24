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
import seistech_calc as si
from .CausalParamBounds import CausalParamBounds


def load_gm_dataset_configs():
    data = {}
    cfgs = glob(os.path.join(os.path.dirname(__file__), "gm_dataset_configs", "*.yaml"))

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
        self, gms: Sequence[Any], site_info: si.site.SiteInfo, output_dir: str
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
        raise NotImplementedError

    def get_im_df(
        self,
        site_info: si.site.SiteInfo,
        IMs: np.ndarray,
        filter_params: CausalParamBounds = None,
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
        filter_params: CausalFilterParams, optional
            The causal filter parameters to use
        sf: series, optional
            The scaling factor for each GM, only relevant for
            HistoricalGMDataset, leave as None for SimulationGMDataset

        Returns
        -------
        dataframe
        """
        raise NotImplementedError

    def get_metadata_df(
        self, site_info: si.site.SiteInfo, selected_gms: Sequence[Any] = None
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
        gms_type = si.constants.GMSourceType(config["type"])

        return (
            SimulationGMDataset(name)
            if gms_type is si.constants.GMSourceType.simulations
            else HistoricalGMDataset(name)
        )


class HistoricalGMDataset(GMDataset):
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
        # Get all IMs from the dataframe columns that are supported by seistech
        return [
            si.im.IM.from_str(cur_col)
            for cur_col in self._im_df.columns
            if si.im.IMType.has_value(cur_col)
        ]

    @property
    def gm_ids(self):
        return self._im_df.index.values

    def get_waveforms(
        self, gms: List[Any], site_info: si.site.SiteInfo, output_dir: str
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
        site_info: si.site.SiteInfo,
        IMs: np.ndarray,
        cs_param_bounds: CausalParamBounds = None,
        sf: pd.Series = None,
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        im_df = self._im_df.copy()

        # Apply amplitude scaling, if a scaling factor is given
        if sf is not None:
            if sf.shape[0] < self._im_df.shape[0]:
                print(
                    "WARNING: Scaling factors have only been provided for a subset "
                    "of available GMs, all GMs without a SF specified will be ignored!"
                )
            im_df = self.apply_amp_scaling(IMs, sf)

        mask = (
            np.ones(im_df.shape[0], dtype=bool)
            if cs_param_bounds is None
            else self._get_filter_mask(
                self.get_metadata_df(site_info).loc[im_df.index], cs_param_bounds, sf=sf
            )
        )

        return im_df.loc[mask, IMs]

    def compute_scaling_factor(
        self,
        IMj: si.im.IM,
        im_j: float,
        gm_ids: np.ndarray = None,
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Computes the amplitude scaling factor such that IM_j == im_j
        for all of the specified GM ids.
        See equations (13) and (14) of Bradley 2012

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

        # Compute the scaling factor
        IMj_alpha = sha.get_scale_alpha([str(IMj)]).loc[str(IMj)]
        sf = np.power(im_j / self._im_df.loc[gm_ids, str(IMj)], 1.0 / IMj_alpha)

        return sf

    def apply_amp_scaling(self, IMs: np.ndarray, sf: pd.Series):
        """
        Applies amplitude to the specified GMs

        Parameters
        ----------
        IMs: array of strings
            The IM types to scale and return
        sf: series
            The scaling factor for each GM of interest
            index: GM ids, value: scaling factor

        Returns
        -------
        dataframe:
            The scaled IMs
        """
        IMs_alpha = sha.get_scale_alpha(IMs).loc[IMs].values
        im_sf_df = pd.DataFrame(
            index=sf.index, data=np.power(sf.values[:, None], IMs_alpha), columns=IMs
        )
        scaled_im_df = self._im_df.loc[sf.index, IMs] * im_sf_df
        return scaled_im_df

    def get_metadata_df(
        self, site_info: si.site.SiteInfo, selected_gms: List[Any] = None
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
        mask = super()._get_filter_mask(
            metadata_df.loc[self.gm_ids], cs_param_bounds, ignore_vs30=ignore_vs30
        )

        if sf is not None and cs_param_bounds.sf_low is not None:
            mask &= (sf.values > cs_param_bounds.sf_low) & (
                sf.values < cs_param_bounds.sf_high
            )

        return mask


class SimulationGMDataset(GMDataset):
    def __init__(self, name: str):
        super().__init__(name)

        # Simulation
        self.imdb_ffp = self._config["simulations_imdb"]
        self.simulation_dir = self._config["simulations_dir"]
        self.source_metadata_df = pd.read_csv(
            self._config["source_metadata_ffp"], index_col=0
        )

        self.vs30_params_csv_ffp = self._config["vs30_params_csv_ffp"]
        self.site_source_db_ffp = self._config["site_source_db_ffp"]
        self.sources_dir = Path(self._config["sources_dir"])

        self._ims = None

    @property
    def ims(self):
        if self._ims is None:
            # Using a leaf here is a bit of a hack, however loading IM values will
            # get an overhaul in the near future, so this will be updated as well then
            with si.dbs.IMDBNonParametric(self.imdb_ffp) as imdb:
                self._ims = [si.im.IM.from_str(im) for im in imdb.ims if si.im.IMType.has_value(im)]

        return self._ims

    def get_waveforms(
        self, gms: List[str], site_info: si.site.SiteInfo, output_dir: str
    ) -> List:
        """See GMDataset method for parameter specifications"""
        no_waveforms = []
        for sim_name in gms:
            # Find the binary waveform
            cur_bb_bin_path = ss.get_bb_bin_path(
                ss.get_sim_dir(self.simulation_dir, sim_name)
            )

            # Convert to text files and store in the specified output directory
            if os.path.isfile(cur_bb_bin_path):
                bb = BBSeis(cur_bb_bin_path)
                bb.save_txt(site_info.station_name, prefix=f"{output_dir}/{sim_name}_")
            else:
                no_waveforms.append(sim_name)
        return no_waveforms

    def get_im_df(
        self,
        site_info: si.site.SiteInfo,
        IMs: np.ndarray,
        cs_param_bounds: CausalParamBounds = None,
        **kwargs,
    ) -> pd.DataFrame:
        """See GMDataset method for parameter specifications"""
        # Using a leaf here is a bit of a hack, however loading IM values will
        # get an overhaul in the near future, so this will be updated as well then
        leaf = si.gm_data.Leaf(None, self.imdb_ffp, si.constants.SourceType.fault)
        im_df = si.shared.get_IM_values([leaf], site_info).reset_index(0)

        if cs_param_bounds is not None:
            # Add source metadata
            assert np.all(
                np.isin(im_df.index, self.source_metadata_df.index)
            ), "No source metadata for all realisations"
            im_df = self.source_metadata_df.join(im_df, how="inner")

            # Add Add site_source metadata
            site_source_df = self._get_site_source_df(site_info)
            assert np.all(
                np.isin(
                    np.unique(im_df.fault),
                    np.unique(site_source_df.index.values.astype(str)),
                )
            )
            im_df = im_df.merge(site_source_df, left_on="fault", right_index=True)

            # Get the filter mask
            mask = self._get_filter_mask(im_df, cs_param_bounds, ignore_vs30=True)

            return im_df.loc[mask, IMs]

        return im_df.loc[:, IMs]

    def _get_site_source_df(self, site_info: si.site.SiteInfo):
        with si.dbs.SiteSourceDB(self.site_source_db_ffp, si.constants.SourceType.fault) as ssdb:
            return ssdb.station_data(site_info.station_name)

    def get_metadata_df(
        self, site_info: si.site.SiteInfo, gm_ids: List[Any] = None
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
        site_source_df = self._get_site_source_df(site_info)

        meta_dict = {}
        for cur_rel in gm_ids:
            meta_dict[cur_rel] = [
                self.source_metadata_df.loc[cur_rel, "mag"],
                site_source_df.loc[cur_rel.split("_")[0]].rrup,
                site_vs30,
            ]
        meta_df = pd.DataFrame.from_dict(meta_dict, orient="index")
        meta_df.columns = ["mag", "rrup", "vs30"]

        return meta_df
