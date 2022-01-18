#!/usr/bin/env python3
"""Script to calculate IMs for fault based empirical

Writes to multiple empirical DB depending on the config
"""

import argparse

from mpi4py import MPI

import gmhazard_calc as sc
import common

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()
if size > 1:
    print(
        "MPI multiprocessing is unsupported at this stage - "
        "please re-run again with only one process"
    )
    exit()
master = 0
is_master = not rank


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
):
    nhm_data = sc.utils.flt_nhm_to_rup_df(nhm_ffp)

    imdb_dict, __ = common.open_imdbs(
        tect_type_model_dict_ffp,
        output_dir,
        sc.constants.SourceType.fault,
        suffix=suffix,
    )

    with sc.dbs.SiteSourceDB(site_source_db_ffp) as distance_store:
        fault_df, n_stations, site_df, work = common.get_work(
            distance_store, vs30_ffp, z_ffp, rank, size
        )

        rupture_df = fault_df.copy(deep=True)
        rupture_df.columns = ["rupture_name"]

        for site_index, site in work.iterrows():
            max_dist = common.get_max_dist_zfac_scaled(site)
            if distance_store.has_station_data(site.name):
                print(
                    f"Processing site {(site_df.index.get_loc(site_index) + 1)} / {n_stations} - Rank: {rank}"
                )
                common.calculate_emp_site(
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
                    tect_type_model_dict_ffp,
                    max_dist,
                    keep_sigma_components=keep_sigma,
                    use_directivity=distance_store.has_station_directivity_data(site.name)
                )
            else:
                print(
                    f"Skipping site {(site_df.index.get_loc(site_index) + 1)} / {n_stations} - Rank: {rank}"
                )
    if is_master:
        common.write_data_and_close(
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


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("nhm_ffp", help="full file path to the nhm file")
    parser.add_argument("site_source_db")
    parser.add_argument("vs30_file")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--z-file",
        help="File name of the Z data",
    )
    parser.add_argument(
        "--periods",
        default=common.PERIOD,
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
        "--suffix",
        "-s",
        help="suffix for the end of the imdb files",
        default=None,
    )
    parser.add_argument(
        "--rupture_lookup",
        "-rl",
        help="flag to run rupture lookup function when creating the db",
        default=False,
    )

    return parser.parse_args()


def calculate_emp_flt():
    args = None
    if is_master:
        args = parse_args()
    args = comm.bcast(args, root=master)
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
    )


if __name__ == "__main__":
    calculate_emp_flt()
