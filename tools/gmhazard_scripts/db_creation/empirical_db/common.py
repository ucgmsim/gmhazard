"""
This file contains functions used by both calc_emp_ds.py and calculate_emp_flt.py
"""
import os
import time
import multiprocessing as mp

import numpy as np
import pandas as pd

from empirical.util import empirical_factory, classdef, openquake_wrapper_vectorized
from empirical.util.classdef import Site, Fault, GMM, TectType
from qcore import formats
from gmhazard_calc.nz_code.nzs1170p5.nzs_zfactor_2016.ll2z import ll2z
from gmhazard_calc.rupture import rupture as gc_rupture
from gmhazard_calc.im import IM, IMType
from gmhazard_calc import utils, dbs, directivity
import sha_calc

# fmt: off
PERIOD = [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.12, 0.15, 0.17, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8,
          0.9, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0]
# fmt: on

IM_TYPE_LIST = [
    IMType.PGA,
    IMType.pSA,
    IMType.Ds595,
    IMType.Ds575,
    IMType.AI,
    IMType.CAV,
    IMType.PGV,
]

MAX_RJB = 200
MAG = [
    5.25,
    5.75,
    6.25,
    6.75,
    7.25,
    8.0,
]  # Definitions for the maximum magnitude / rjb relation
DIST = [125, 150, 175, 200, 250, 300]


def open_imdbs(model_dict_ffp, output_dir, source_type, suffix=None):
    """
    Parse the model dictionary for the models that can be written to, and create objects to write to them.

    :param model_dict_ffp: Filepath to the model_dict which will specify which
    :param output_dir: Folder that IMDBs are to be saved to.
    :return: A dictionary containing open parametric IMDBs ready to write empirical values to.
    """
    model_list = empirical_factory.get_models_from_dict(model_dict_ffp)
    return open_imdbs_from_list(model_list, output_dir, source_type, suffix)


def open_imdbs_from_list(item_list, output_dir, source_type, suffix=None):
    imdb_dict = {}
    stations_calculated = set()

    for model_name in item_list:
        imdb_ffp = os.path.join(
            output_dir, utils.create_parametric_db_name(model_name, source_type, suffix)
        )
        imdb = dbs.IMDBParametric(imdb_ffp, source_type=source_type, writeable=True)
        imdb.open()
        stations_calculated = stations_calculated.union(imdb.get_stored_stations())
        imdb.close()
        imdb_dict[model_name] = imdb
    return imdb_dict, stations_calculated


def get_work(distance_store, vs30_file, z_file, rank, size, stations_calculated=None):
    """

    :param stations_calculated:
    :param distance_store: A source_site_distance db object
    :param vs30_file: file containing lon, lat, vs30 value
    :param z_file: file containing station_name, z1.0, z2.5
    :param rank: rank of MPI process
    :param size: number of MPI processors running
    :return: tuple containing (fault dataframe, number of stations, site dataframe, work)
    fault_dataframe: dataframe containing ids and fault_names
    site_dataframe: dataframe containing lat, lon, station_name and vs30 - includes Z values if file specified
    """
    station_df = distance_store.stations()
    vs30_df = formats.load_vs30_file(vs30_file)
    site_df = station_df.merge(vs30_df, left_index=True, right_index=True)

    # Combine Z-values and site data (if available)
    site_df = (
        site_df.join(formats.load_z_file(z_file)) if z_file is not None else site_df
    )

    site_to_do_df = site_df

    if stations_calculated is not None and len(stations_calculated) > 0:
        site_to_do_df = site_to_do_df[~site_to_do_df.index.isin(stations_calculated)]

    fault_df = distance_store.faults()
    fault_df["fault_name"] = fault_df["fault_name"].astype("category")

    n_stations = len(site_to_do_df)
    work = site_to_do_df[rank::size] if rank is not None and size is not None else None

    return fault_df, n_stations, site_df, work


def get_im_list(im_types, periods):
    ims = []
    for im_type in im_types:
        if im_type is IMType.pSA:
            ims.extend([IM(im_type, period=period) for period in periods])
        else:
            ims.append(IM(im_type))
    return ims


def curate_im_list(tect_type_model_dict, model, periods):
    im_types = [
        IMType[im]
        for tect_type, im_dict in tect_type_model_dict.items()
        for im, component_dict in im_dict.items()
        for gmm in component_dict["geom"]
        if tect_type in model and gmm in model
    ]

    return get_im_list(im_types, periods)


def write_metadata_and_close(
    imdb_dict,
    nhm_ffp,
    rupture_df,
    site_df,
    vs30_ffp,
    psa_periods=None,
    ims=None,
    tect_type_model_dict_ffp=None,
    rupture_lookup=False,
):
    """
    Writes metadata, rupture_df and closes the IMDBs for the ones opened by open_imdbs
    :param imdb_dict: dictionary returned by the function open_imdbs
    :param nhm_ffp: filepath to nhm file (can be flt or ds)
    :param rupture_df: rupture_df - faults considered for calculation
    :param site_df: site dataframe to save in IMDB - what sites were the input for creating this IMDB
    :param vs30_ffp: filepath to vs30 file
    :param ims: List of IMs these DBs contain
    :param rupture_lookup: Flag to add rupture lookup data to the imdb
    :return: None
    """

    if psa_periods is None:
        psa_periods = list()
    tect_type_model_dict = empirical_factory.read_model_dict(tect_type_model_dict_ffp)

    for imdb_keys in imdb_dict.keys():
        imdb_dict[imdb_keys].open()
        imdb_dict[imdb_keys].write_sites(site_df[["lat", "lon"]])
        imdb_dict[imdb_keys].write_rupture_data(rupture_df)
        im_list = (
            get_im_list(ims, psa_periods)
            if tect_type_model_dict_ffp is None
            else curate_im_list(tect_type_model_dict, imdb_keys, psa_periods)
        )
        imdb_dict[imdb_keys].write_attributes(
            os.path.basename(nhm_ffp),
            os.path.basename(vs30_ffp),
            ims=np.asarray(im_list, dtype=str),
        )
        imdb_dict[imdb_keys].close()
        if rupture_lookup:
            imdb_dict[imdb_keys].add_rupture_lookup(imdb_dict[imdb_keys].db_ffp, 1)


def get_max_dist_zfac_scaled(site):
    z_factor = float(ll2z((site.lon, site.lat), radius_search=0))
    # interpolate the max_distance between 200-300 based on z-factor (0.3-0.1)
    return max((max(DIST) - MAX_RJB) * (0.3 - z_factor) / 0.2, 0) + MAX_RJB


def __process_rupture(
    rupture,
    site,
    im_types,
    tect_type_model_dict,
    directivity_adjustment,
    psa_periods,
    keep_sigma_components,
    fault_im_result_dict,
    use_directivity=True,
):
    """Helper MP function for calculate_emp_site"""
    fault = Fault(
        Mw=rupture.mag,
        hdepth=rupture.dbot,
        zbot=rupture.dbot,
        ztor=rupture.dtop,
        dip=rupture.dip,
        rake=rupture.rake,
        tect_type=classdef.TectType[rupture.tect_type],
    )

    site.Rjb = rupture["rjb"]
    site.Rrup = rupture["rrup"]
    # Currently 0 as Rtvz calculation is done in the empirical engine
    site.Rtvz = 0  # rupture["rtvz"]
    site.fpeak = np.array([12])
    rx = rupture["rx"]
    site.Rx = 0 if np.isnan(rx) else rx
    ry = rupture["ry"]
    site.Ry = 0 if np.isnan(ry) else ry

    for im_type in im_types:
        GMMs = empirical_factory.determine_all_gmm(
            fault, str(im_type), tect_type_model_dict
        )
        for GMM, __comp in GMMs:
            db_type = f"{GMM.name}_{fault.tect_type.name}"
            values = empirical_factory.compute_gmm(
                fault,
                site,
                GMM,
                str(im_type),
                psa_periods if im_type is IMType.pSA else None,
            )
            if im_type is not IMType.pSA:
                values = [values]
            for i, value in enumerate(values):
                full_im_name = (
                    IM(im_type, period=psa_periods[i])
                    if im_type is IMType.pSA
                    else IM(im_type)
                )
                mean = np.log(value[0])
                stdev, sigma_inter, sigma_intra = value[1]
                if use_directivity and im_type is IMType.pSA:
                    mean += directivity_adjustment.loc[str(full_im_name)]
                    stdev += directivity_adjustment.loc[f"{full_im_name}_sigma"]

                fault_im_result_dict[db_type][str(full_im_name)] = mean
                if keep_sigma_components:
                    fault_im_result_dict[db_type][
                        f"{full_im_name}_sigma_inter"
                    ] = sigma_inter
                    fault_im_result_dict[db_type][
                        f"{full_im_name}_sigma_intra"
                    ] = sigma_intra
                else:
                    fault_im_result_dict[db_type][f"{full_im_name}_sigma"] = stdev

    print(rupture.rupture_name)
    print(fault_im_result_dict)
    time.sleep(100)
    return rupture.rupture_name, fault_im_result_dict


def calculate_emp_site(
    im_types,
    psa_periods,
    imdb_dict,
    fault_df,
    rupture_df,
    distance_store,
    nhm_data,
    vs30,
    z1p0,
    z2p5,
    station_name,
    tect_type_model_dict,
    max_rjb=MAX_RJB,
    dist_filter_by_mag=False,
    return_vals=False,
    keep_sigma_components=False,
    use_directivity=True,
    n_procs: int = 1,
):
    """
    Calculates (and writes) all empirical values for all ruptures in nhm_data at a given site.
    Where rjb values are <=200

    :param im_types: What ims to calculate
    :param psa_periods: if pSA is specified what pSA periods to calculate
    :param imdb_dict: imdb dictionary as returned by open_imdbs
    :param fault_df: list of faults considered
    :param rupture_df: list of ruptures considered - these will be used as indexes for the data stored by each site
    :param distance_store: site source distance h5 - to determine wether the site-source needs to be calculated
    :param nhm_data: rupture dataframe returned from utils.py from either a nhm background sources or fault file
    :param vs30: vs30 value at the given station
    :param z1p0: Z1.0 value at the given station
    :param z2p5: Z2.5 value at the given station
    :param station_name: the stations name for the specific station
    :param tect_type_model_dict_ffp: the relation between tectonic type and which empirical model(s) to use
    :param return_vals: flag to return the values instead of writing them to the DB - specifically for the single
                        writer MPI paradigm
    :param use_directivity: flag to apply the directivity effect to each of the fault calculations. Applies only on pSA
    :return: if return vals is set - a Dictionary of dataframes are returned
    """
    # Sets Z1.0 and Z2.5 to None if NaN
    z1p0 = None if z1p0 is None or np.isnan(float(z1p0)) else z1p0
    z2p5 = None if z1p0 is None or np.isnan(float(z2p5)) else z2p5
    site = Site(vs30=vs30, z1p0=z1p0, z2p5=z2p5)

    distance_df = fault_df.merge(
        distance_store.station_data(station_name),
        left_on="fault_name",
        right_index=True,
    )

    matching_df = nhm_data.merge(
        distance_df, left_on="fault_name", right_on="fault_name"
    )

    dir_data = distance_store.station_directivity_data(station_name)
    if use_directivity and dir_data is not None:
        directivity_df = fault_df.merge(
            dir_data, left_on="fault_name", right_index=True,
        )

    if dist_filter_by_mag:
        max_dist = np.minimum(np.interp(matching_df.mag, MAG, DIST), max_rjb)
    else:
        max_dist = max_rjb
    matching_df = matching_df[matching_df["rjb"] < max_dist]

    if n_procs == 1:
        results = []
        for index, rupture in matching_df.iterrows():
            results.append(
                __process_rupture(
                    rupture,
                    site,
                    im_types,
                    tect_type_model_dict,
                    directivity_df.iloc[index] if use_directivity else None,
                    psa_periods,
                    keep_sigma_components,
                    {key: {} for key in imdb_dict.keys()},
                    use_directivity,
                )
            )
    else:
        with mp.Pool(n_procs) as p:
            results = p.starmap(
                __process_rupture,
                [
                    (
                        rupture,
                        site,
                        im_types,
                        tect_type_model_dict,
                        directivity_df.iloc[index] if use_directivity else None,
                        psa_periods,
                        keep_sigma_components,
                        {key: {} for key in imdb_dict.keys()},
                        use_directivity,
                    )
                    for index, rupture in matching_df.iterrows()
                ],
            )

    im_result_dict = {key: {} for key in imdb_dict.keys()}
    for cur_rupture_name, cur_fault_im_dict in results:
        cur_rupture_id = rupture_df[
            rupture_df["rupture_name"] == cur_rupture_name
        ].index.values.item()
        for cur_gmm, cur_im_dict in cur_fault_im_dict.items():
            im_result_dict[cur_gmm][cur_rupture_id] = cur_im_dict

    im_result_df_dict = {key: {} for key in imdb_dict.keys()}
    for imdb_key in imdb_dict.keys():
        im_result_df_dict[imdb_key] = pd.DataFrame.from_dict(
            im_result_dict[imdb_key], orient="index"
        )

    if return_vals:
        return im_result_df_dict
    else:
        write_result_to_db(im_result_df_dict, imdb_dict, station_name)


def write_result_to_db(im_result_df_dict, imdb_dict, station_name):
    """
    Takes a dictionary of IM result dataframes and writes them to the IMDB that has the corresponding key in the IMDB
    dict
    :param im_result_df_dict: Dictionary containing the calculation
    :param imdb_dict: Dictionary containing the IMDB objects that will get IM data written to
    :param station_name: Station name to be written to as they key for accessing the data
    """
    s_time = time.perf_counter()
    for imdb_key in imdb_dict.keys():
        site_im_df = im_result_df_dict[imdb_key]
        if not site_im_df.empty:
            imdb_dict[imdb_key].open()
            imdb_dict[imdb_key].write_im_data(station_name, site_im_df)
            imdb_dict[imdb_key].close()
    print(f"{station_name} took {time.perf_counter() - s_time:.2f}s to write.")


def new_calculate_emp_site(
    im_types,
    psa_periods,
    imdb_dict,
    fault_df,
    rupture_df,
    distance_store,
    nhm_data,
    vs30,
    z1p0,
    z2p5,
    station_name,
    tect_type_model_dict,
    max_rjb=MAX_RJB,
    dist_filter_by_mag=False,
    return_vals=False,
    keep_sigma_components=False,
    use_directivity=True,
    n_procs: int = 1,
):
    print(im_types)
    print(psa_periods)
    print(imdb_dict)
    print(fault_df)
    print(rupture_df)
    print(distance_store)
    print(nhm_data)
    print(vs30)
    print(z1p0)
    print(z2p5)
    print(station_name)
    print(tect_type_model_dict)
    """
    Calculates (and writes) all empirical values for all ruptures in nhm_data at a given site.
    Where rjb values are <=200

    :param im_types: What ims to calculate
    :param psa_periods: if pSA is specified what pSA periods to calculate
    :param imdb_dict: imdb dictionary as returned by open_imdbs
    :param fault_df: list of faults considered
    :param rupture_df: list of ruptures considered - these will be used as indexes for the data stored by each site
    :param distance_store: site source distance h5 - to determine wether the site-source needs to be calculated
    :param nhm_data: rupture dataframe returned from utils.py from either a nhm background sources or fault file
    :param vs30: vs30 value at the given station
    :param z1p0: Z1.0 value at the given station
    :param z2p5: Z2.5 value at the given station
    :param station_name: the stations name for the specific station
    :param tect_type_model_dict_ffp: the relation between tectonic type and which empirical model(s) to use
    :param return_vals: flag to return the values instead of writing them to the DB - specifically for the single
                        writer MPI paradigm
    :param use_directivity: flag to apply the directivity effect to each of the fault calculations. Applies only on pSA
    :return: if return vals is set - a Dictionary of dataframes are returned
    """
    # Sets Z1.0 and Z2.5 to None if NaN
    z1p0 = None if z1p0 is None or np.isnan(float(z1p0)) else z1p0
    z2p5 = None if z1p0 is None or np.isnan(float(z2p5)) else z2p5
    site = Site(vs30=vs30, z1p0=z1p0, z2p5=z2p5)

    distance_df = fault_df.merge(
        distance_store.station_data(station_name),
        left_on="fault_name",
        right_index=True,
    )

    matching_df = nhm_data.merge(
        distance_df, left_on="fault_name", right_on="fault_name"
    )

    dir_data = distance_store.station_directivity_data(station_name)
    if use_directivity and dir_data is not None:
        directivity_df = fault_df.merge(
            dir_data, left_on="fault_name", right_index=True,
        )

    if dist_filter_by_mag:
        max_dist = np.minimum(np.interp(matching_df.mag, MAG, DIST), max_rjb)
    else:
        max_dist = max_rjb
    matching_df = matching_df[matching_df["rjb"] < max_dist]

    # Adding missing columns
    matching_df["vs30"] = site.vs30
    matching_df["vs30measured"] = site.vs30measured
    matching_df["z1pt0"] = site.z1p0
    matching_df["z2pt5"] = site.z2p5
    matching_df["hypo_depth"] = matching_df["dbot"]
    matching_df["ztor"] = matching_df["dtop"]
    matching_df["rx"] = matching_df["rx"].fillna(0)
    matching_df["ry"] = matching_df["ry"].fillna(0)
    # OQ uses ry0 term
    matching_df = matching_df.rename(columns={"ry": "ry0"})
    # rtvz
    if matching_df.get("rtvz") is None:
        matching_df["rtvz"] = 0
    else:
        # OQ models we have, do not support Volcanic, hence rtvz will always be 0
        # unless it is already specified
        matching_df.loc[:, "rtvz"] = matching_df.loc[:, "rtvz"].fillna(0)
        matching_df.loc[matching_df["rtvz"] <= 0, "rtvz"] = 0

    results = []
    for tect_type in matching_df["tect_type"].unique():
        results.append(
            __new_process_rupture(
                matching_df,
                im_types,
                tect_type,
                tect_type_model_dict,
                directivity_df if use_directivity else None,
                psa_periods,
                keep_sigma_components,
                {key: {} for key in imdb_dict.keys()},
                use_directivity,
            )
        )

    breakpoint()
    im_result_dict = {key: {} for key in imdb_dict.keys()}
    for cur_rupture_name, cur_fault_im_dict in results:
        cur_rupture_id = rupture_df[
            rupture_df["rupture_name"] == cur_rupture_name
        ].index.values.item()
        for cur_gmm, cur_im_dict in cur_fault_im_dict.items():
            im_result_dict[cur_gmm][cur_rupture_id] = cur_im_dict

    im_result_df_dict = {key: {} for key in imdb_dict.keys()}
    for imdb_key in imdb_dict.keys():
        im_result_df_dict[imdb_key] = pd.DataFrame.from_dict(
            im_result_dict[imdb_key], orient="index"
        )

    if return_vals:
        return im_result_df_dict
    else:
        write_result_to_db(im_result_df_dict, imdb_dict, station_name)


def __new_process_rupture(
    rupture,
    im_types,
    tect_type,
    tect_type_model_dict,
    directivity_adjustment,
    psa_periods,
    keep_sigma_components,
    fault_im_result_dict,
    use_directivity=True,
):
    """Helper MP function for calculate_emp_site"""
    fault = Fault(
        Mw=rupture.mag,
        hdepth=rupture.dbot,
        zbot=rupture.dbot,
        ztor=rupture.dtop,
        dip=rupture.dip,
        rake=rupture.rake,
        tect_type=classdef.TectType[tect_type],
    )

    for im_type in im_types:
        GMMs = empirical_factory.determine_all_gmm(
            fault, str(im_type), tect_type_model_dict
        )
        for GMM, __comp in GMMs:
            db_type = f"{GMM.name}_{fault.tect_type.name}"
            # values = empirical_factory.compute_gmm(
            #     fault,
            #     site,
            #     GMM,
            #     str(im_type),
            #     psa_periods if im_type is IMType.pSA else None,
            # )

            answer = openquake_wrapper_vectorized.oq_run(
                GMM,
                classdef.TectType[tect_type],
                rupture.loc[rupture["tect_type"] == fault.tect_type.name],
                str(im_type),
                psa_periods if im_type is IMType.pSA else None,
            )
            answer = answer.set_index(rupture.loc[rupture["tect_type"] == fault.tect_type.name].index)
            if len(fault_im_result_dict[db_type]) == 0:
                fault_im_result_dict[db_type] = [answer]
            else:
                fault_im_result_dict[db_type].append(answer)
            # fault_im_result_dict[db_type][f"{full_im_name}_sigma"] = stdev

            # for i, value in enumerate(values):
            #     full_im_name = (
            #         IM(im_type, period=psa_periods[i])
            #         if im_type is IMType.pSA
            #         else IM(im_type)
            #     )
            #     mean = np.log(value[0])
            #     stdev, sigma_inter, sigma_intra = value[1]
            #     if use_directivity and im_type is IMType.pSA:
            #         mean += directivity_adjustment.loc[str(full_im_name)]
            #         stdev += directivity_adjustment.loc[f"{full_im_name}_sigma"]
            #
            #     fault_im_result_dict[db_type][str(full_im_name)] = mean
            #     if keep_sigma_components:
            #         fault_im_result_dict[db_type][
            #             f"{full_im_name}_sigma_inter"
            #         ] = sigma_inter
            #         fault_im_result_dict[db_type][
            #             f"{full_im_name}_sigma_intra"
            #         ] = sigma_intra
            #     else:
            #         fault_im_result_dict[db_type][f"{full_im_name}_sigma"] = stdev

    return rupture.rupture_name, fault_im_result_dict
