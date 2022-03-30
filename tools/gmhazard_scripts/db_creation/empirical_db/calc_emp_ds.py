import argparse
import time

import pandas as pd
import numpy as np

import common
import gmhazard_calc as gc
from empirical.util import empirical_factory, classdef, openquake_wrapper_vectorized

# fmt: off
PERIOD = [0.01, 0.02, 0.03, 0.04, 0.05, 0.075, 0.1, 0.12, 0.15, 0.17, 0.2, 0.25, 0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8,
          0.9, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.5, 10.0]
# fmt: on

IM_TYPE_LIST = [
    gc.im.IMType.PGA,
    gc.im.IMType.pSA,
    gc.im.IMType.Ds595,
    gc.im.IMType.Ds575,
    gc.im.IMType.AI,
    gc.im.IMType.CAV,
    gc.im.IMType.PGV,
]

MAG = [
    5.25,
    5.75,
    6.25,
    6.75,
    7.25,
    8.0,
]  # Definitions for the maximum magnitude / rjb relation
DIST = [125, 150, 175, 200, 250, 300]


def get_rupture_context_df(
    distance_store: gc.dbs.SiteSourceDB,
    fault_df: pd.DataFrame,
    site: str,
    site_data: pd.Series,
    nhm_data: pd.DataFrame,
    tect_type: str,
):
    """Creating the form of dataframe for the vectorized OQ Wrapper
    By combining site, distance and rupture information
    """
    distance_df = fault_df.merge(
        distance_store.station_data(site), left_on="fault_name", right_index=True,
    )
    rupture_df = nhm_data.merge(
        distance_df, left_on="fault_name", right_on="fault_name"
    )
    max_dist = np.minimum(
        np.interp(rupture_df.mag, MAG, DIST),
        common.get_max_dist_zfac_scaled(site_data),
    )
    rupture_df = rupture_df[rupture_df["rjb"] < max_dist]

    return polish_rupture_context_df(rupture_df, site_data, tect_type)


def polish_rupture_context_df(
    rupture_context_df: pd.DataFrame, site_data: pd.Series, tect_type: str,
):
    """
    Combining the given rupture_context_df(Distance and Rupture) with Site information
    to create a OQ's RuptureContext like DF to be used with OQ's Vectorized Wrapper
    """
    # Adding missing columns
    rupture_context_df["vs30"] = site_data.vs30
    rupture_context_df["vs30measured"] = (
        site_data.vs30measured if site_data.get("vs30measured") is not None else False
    )
    rupture_context_df["z1pt0"] = (
        None
        if site_data.z1p0 is None or np.isnan(float(site_data.z1p0))
        else site_data.z1p0
    )
    rupture_context_df["z2pt5"] = (
        None
        if site_data.z1p0 is None or np.isnan(float(site_data.z2p5))
        else site_data.z2p5
    )
    rupture_context_df[["hypo_depth", "ztor"]] = rupture_context_df[["dbot", "dtop"]]
    # OQ uses ry0 term
    rupture_context_df[["rx", "ry0"]] = rupture_context_df[["rx", "ry"]].fillna(0)
    # rtvz for Br_10 model
    if rupture_context_df.get("rtvz") is None:
        rupture_context_df["rtvz"] = 0
    else:
        # OQ's Br_10 does not support Volcanic, hence rtvz will always be 0
        # unless it is already specified
        rupture_context_df["rtvz"] = rupture_context_df["rtvz"].fillna(0)
        rupture_context_df.loc[rupture_context_df["rtvz"] <= 0, "rtvz"] = 0

    return rupture_context_df.loc[rupture_context_df["tect_type"] == tect_type]


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
    nhm_data = gc.utils.ds_nhm_to_rup_df(background_sources_ffp)
    rupture_df = pd.DataFrame(nhm_data["rupture_name"])
    imdb_dict, _ = common.open_imdbs(
        model_dict_ffp, output_dir, gc.constants.SourceType.distributed, suffix=suffix,
    )
    model_dict = empirical_factory.read_model_dict(model_dict_ffp)

    with gc.dbs.SiteSourceDB(site_source_db_ffp) as distance_store:
        fault_df, n_stations, site_df, _ = common.get_work(
            distance_store, vs30_ffp, z_ffp, None, None
        )
        sites = [
            site for site in site_df.index if distance_store.has_station_data(site)
        ]

        for im_idx, im in enumerate(ims):
            print(f"Processing IM {im}, {im_idx + 1} / {len(ims)}")
            for tect_idx, tect_type in enumerate(nhm_data["tect_type"].unique()):
                print(
                    f"Processing Tectonic Type {tect_type}, {tect_idx + 1} / {len(nhm_data['tect_type'].unique())}"
                )
                GMMs = empirical_factory.determine_all_gmm(
                    classdef.Fault(tect_type=classdef.TectType[tect_type]),
                    str(im),
                    model_dict,
                )
                for GMM_idx, (GMM, _) in enumerate(GMMs):
                    db_type = f"{GMM.name}_{tect_type}"
                    if GMM.name in ("K_20", "K_20_NZ", "ZA_06", "ASK_14", "CB_14",):
                        continue
                    print(f"Processing DB Type {db_type}, {GMM_idx + 1} / {len(GMMs)}")

                    for site in sites:
                        rupture_context_df = get_rupture_context_df(
                            distance_store,
                            fault_df,
                            site,
                            site_df.loc[site],
                            nhm_data,
                            tect_type,
                        )
                        gmm_calculated_df = openquake_wrapper_vectorized.oq_run(
                            GMM,
                            classdef.TectType[tect_type],
                            rupture_context_df,
                            str(im),
                            psa_periods if im is gc.im.IMType.pSA else None,
                        )

                        gmm_calculated_df.set_index(
                            rupture_df[
                                rupture_df["rupture_name"].isin(
                                    rupture_context_df["rupture_name"]
                                )
                            ].index,
                            inplace=True,
                        )
                        gmm_calculated_df.columns = [
                            f"{'_'.join(col.split('_')[:2]) if im is gc.im.IMType.pSA else im}_sigma"
                            if col.endswith("std_Total")
                            else col
                            for col in gmm_calculated_df
                        ]

                        imdb_dict[db_type].open()
                        imdb_dict[db_type].add_im_data(
                            site,
                            gmm_calculated_df.loc[
                                :,
                                gmm_calculated_df.columns.str.endswith(
                                    ("mean", "sigma")
                                ),
                            ],
                        )
                        imdb_dict[db_type].close()

    print("Writing metadata")
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
    print("Done")


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
    start = time.time()
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
    print(f"Finished in {(time.time() - start) / 60}")


if __name__ == "__main__":
    calculate_emp_ds()
