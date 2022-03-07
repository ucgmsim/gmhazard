#!/usr/bin/env python3
"""Script to calculate IMs for fault based empirical

Writes to multiple empirical DB depending on the config
"""
import math
import time
import argparse
import multiprocessing as mp
from typing import Dict, Sequence

import numpy as np
import pandas as pd

import common
import gmhazard_calc as sc
from empirical.util import empirical_factory


def calculate_flt(
    nhm_ffp,
    site_source_db_ffp,
    vs30_ffp,
    z_ffp,
    ims,
    psa_periods,
    output_dir,
    tect_type_model_dict_ffp,
    keep_sigma=False,
    suffix=None,
    rupture_lookup=False,
    use_directivity: bool = True,
    n_procs: int = 1,
):
    nhm_data = sc.utils.flt_nhm_to_rup_df(nhm_ffp)

    imdb_dict, __ = common.open_imdbs(
        tect_type_model_dict_ffp,
        output_dir,
        sc.constants.SourceType.fault,
        suffix=suffix,
    )

    with sc.dbs.SiteSourceDB(site_source_db_ffp, writeable=False) as distance_store:
        distance_stations = np.asarray(distance_store.stored_stations())

        fault_df, _, site_df, work = common.get_work(
            distance_store, vs30_ffp, z_ffp, None, None
        )

    # Drop stations for which there is no distance data
    site_df = site_df.loc[np.isin(site_df.index.values, distance_stations)]
    n_stations = site_df.shape[0]

    # Setup some extra data
    tect_type_model_dict = empirical_factory.read_model_dict(tect_type_model_dict_ffp)
    rupture_df = fault_df.copy(deep=True)
    rupture_df.columns = ["rupture_name"]

    # Process stations in batch of 1000 (and save in between)
    for ix in range(math.ceil(n_stations / 1000)):
        cur_site_df = site_df.iloc[(ix * 1000) : (ix + 1) * 1000]

        start_time = time.time()
        if n_procs == 1:
            im_data = []
            for _, cur_site in cur_site_df.iterrows():
                im_data.append(
                    _process_site(
                        cur_site,
                        site_source_db_ffp,
                        fault_df,
                        rupture_df,
                        keep_sigma,
                        ims,
                        psa_periods,
                        imdb_dict,
                        nhm_data,
                        tect_type_model_dict,
                        use_directivity,
                    )
                )
        else:
            with mp.Pool(n_procs) as p:
                im_data = p.starmap(
                    _process_site,
                    [
                        (
                            cur_site,
                            site_source_db_ffp,
                            fault_df,
                            rupture_df,
                            keep_sigma,
                            ims,
                            psa_periods,
                            imdb_dict,
                            nhm_data,
                            tect_type_model_dict,
                            use_directivity,
                        )
                        for _, cur_site in cur_site_df.iterrows()
                    ],
                )

        print(
            f"Computed data for sites {ix * 1000} - {(ix + 1) * 1000}, "
            f"took {time.time() - start_time:.2f} seconds; writing to DB"
        )
        _write_result_to_db(im_data, imdb_dict)

    common.write_metadata_and_close(
        imdb_dict,
        nhm_ffp,
        rupture_df,
        site_df,
        vs30_ffp,
        psa_periods,
        ims,
        tect_type_model_dict_ffp,
        rupture_lookup=rupture_lookup,
    )


def _write_result_to_db(im_data, imdb_dict):
    s_time = time.perf_counter()
    for imdb_key in imdb_dict.keys():
        imdb_dict[imdb_key].open()
        for cur_site_name, cur_im_data in im_data:
            cur_im_df = cur_im_data[imdb_key]
            if not cur_im_df.empty:
                imdb_dict[imdb_key].write_im_data(cur_site_name, cur_im_df)
        imdb_dict[imdb_key].close()
    print(f"Took {time.perf_counter() - s_time:.2f}s to write {len(im_data)} stations.")


def _process_site(
    site,
    site_source_db_ffp: str,
    fault_df: pd.DataFrame,
    rupture_df: pd.DataFrame,
    keep_sigma: bool,
    ims: Sequence[str],
    psa_periods,
    imdb_dict,
    nhm_data,
    tect_type_model_dict: Dict,
    use_directivity: bool,
):
    with sc.dbs.SiteSourceDB(site_source_db_ffp, writeable=False) as distance_store:
        max_dist = common.get_max_dist_zfac_scaled(site)
        print(f"Processing site {site.name}")
        result = common.calculate_emp_site(
            ims,
            psa_periods,
            imdb_dict,
            fault_df,
            rupture_df,
            distance_store,
            nhm_data,
            site.vs30,
            site.z1p0 if hasattr(site, "z1p0") else None,
            site.z2p5 if hasattr(site, "z2p5") else None,
            site.name,
            tect_type_model_dict,
            max_dist,
            keep_sigma_components=keep_sigma,
            use_directivity=use_directivity,
            n_procs=1,
            return_vals=True,
        )

        return site.name, result


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nhm_ffp", help="full file path to the nhm file")
    parser.add_argument("site_source_db")
    parser.add_argument("vs30_file")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--z-file", help="File name of the Z data",
    )
    parser.add_argument(
        "--periods",
        default=common.PERIOD,
        type=float,
        nargs="+",
        help="Which pSA periods to calculate for",
    )
    parser.add_argument(
        "--im",
        default=common.IM_TYPE_LIST,
        nargs="+",
        help="Which IMs to calculate",
        type=sc.im.IMType,
    )
    parser.add_argument(
        "--model-dict",
        help="model dictionary to specify which model to use for each tect-type",
    )
    parser.add_argument(
        "--keep-sigma",
        "-ks",
        action="store_true",
        help="flag to keep sigma_inter and sigma_intra instead of sigma_total",
    )
    parser.add_argument(
        "--suffix", "-s", help="suffix for the end of the imdb files", default=None,
    )
    parser.add_argument(
        "--rupture_lookup",
        "-rl",
        help="flag to run rupture lookup function when creating the db",
        default=False,
    )
    parser.add_argument(
        "--n-procs", type=int, help="Number of processes to use", default=1
    )
    parser.add_argument(
        "--no-directivity",
        action="store_true",
        type=bool,
        default=False,
        help="Disable adding directivity adjustment",
    )

    return parser.parse_args()


def calculate_emp_flt():
    args = parse_args()
    calculate_flt(
        args.nhm_ffp,
        args.site_source_db,
        args.vs30_file,
        args.z_file,
        args.im,
        args.periods,
        args.output_dir,
        args.model_dict,
        args.keep_sigma,
        suffix=args.suffix,
        rupture_lookup=args.rupture_lookup,
        n_procs=args.n_procs,
        use_directivity=not args.no_directivity,
    )


if __name__ == "__main__":
    calculate_emp_flt()
