import argparse
import math
import time
import threading

import pandas as pd


import common
import gmhazard_calc as gc
from empirical.util import empirical_factory


def calculate_ds(
    background_sources_ffp,
    site_source_db_ffp,
    vs30_ffp,
    z_ffp,
    ims,
    psa_periods,
    output_dir,
    model_dict_ffp,
    suffix=None,
):
    """
    Calculate Empirical values for every site-fault pairing in the provided site_source_db.

    Pairs the station name with the vs30 value in the provided vs30 file. Only sites that have vs30 values will be calculated.

    Saves all IM values (median and sigma) for all ims specified to the imdb_path in pandas h5 format

    :return: None
    """
    wait_time = 0.0
    # Setting up some data
    nhm_data = gc.utils.ds_nhm_to_rup_df(background_sources_ffp)
    rupture_df = pd.DataFrame(nhm_data["rupture_name"])
    imdb_dict, stations_calculated = common.open_imdbs(
        model_dict_ffp, output_dir, gc.constants.SourceType.distributed, suffix=suffix,
    )
    model_dict = empirical_factory.read_model_dict(model_dict_ffp)
    count = 0
    with gc.dbs.SiteSourceDB(site_source_db_ffp) as distance_store:
        fault_df, n_stations, site_df, _ = common.get_work(
            distance_store, vs30_ffp, z_ffp, None, 1, stations_calculated
        )
        for _, site in site_df.iterrows():
            print(f"{count + 1} / {n_stations} started")
            max_dist = common.get_max_dist_zfac_scaled(site)

            value = (
                common.new_calculate_emp_site(
                    ims,
                    psa_periods,
                    imdb_dict,
                    fault_df,
                    distance_store,
                    nhm_data,
                    site.vs30,
                    site.vs30measured if hasattr(site, "vs30measured") else None,
                    site.z1p0 if hasattr(site, "z1p0") else None,
                    site.z2p5 if hasattr(site, "z2p5") else None,
                    site.name,
                    model_dict,
                    max_dist,
                    dist_filter_by_mag=True,
                    return_vals=False,
                    use_directivity=False,
                ),
                site.name,
            )
            count += 1

    common.write_metadata_and_close(
        imdb_dict,
        background_sources_ffp,
        rupture_df,
        site_df,
        vs30_ffp,
        psa_periods,
        ims,
        model_dict_ffp,
    )


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("background_txt", help="background txt file")
    parser.add_argument("site_source_db")
    parser.add_argument("vs30_file")
    parser.add_argument("output_dir")
    parser.add_argument(
        "--z-file", help="File name of the Z data",
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
        type=gc.im.IMType,
    )
    parser.add_argument(
        "--model-dict",
        help="model dictionary to specify which model to use for each tect-type",
    )
    parser.add_argument(
        "--suffix", "-s", help="suffix for the end of the imdb files", default=None,
    )

    return parser.parse_args()


def calculate_emp_ds():
    args = parse_args()
    calculate_ds(
        args.background_txt,
        args.site_source_db,
        args.vs30_file,
        args.z_file,
        args.im,
        args.periods,
        args.output_dir,
        args.model_dict,
        suffix=args.suffix,
    )


if __name__ == "__main__":
    calculate_emp_ds()
