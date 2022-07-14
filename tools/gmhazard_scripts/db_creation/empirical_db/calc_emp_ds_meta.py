import multiprocessing as mp
import argparse
import time
from typing import List, Optional
from enum import Enum
from pathlib import Path

import pandas as pd
import numpy as np

import common
import gmhazard_calc as gc
from empirical.util import classdef
from empirical.util import empirical_factory
from empirical.util import openquake_wrapper_vectorized
from empirical.GMM_models import meta_model

MAG = [
    5.25,
    5.75,
    6.25,
    6.75,
    7.25,
    8.0,
]  # Definitions for the maximum magnitude / rjb relation
DIST = [125, 150, 175, 200, 250, 300]


def create_rupture_context_df(
    distance_df: pd.DataFrame,
    site_data: pd.Series,
    nhm_data: pd.DataFrame,
    tect_type: Enum,
):
    """Creating the form of dataframe for the vectorized OQ Wrapper
    By combining site, distance and rupture information
    """
    rupture_df = nhm_data.merge(
        distance_df, left_on="fault_name", right_on="fault_name"
    )
    max_dist = np.minimum(
        np.interp(rupture_df.mag, MAG, DIST),
        common.get_max_dist_zfac_scaled(site_data),
    )
    rupture_df = rupture_df[rupture_df["rjb"] < max_dist]

    # Adding missing columns
    # Site Parameters
    rupture_df["vs30"] = site_data.vs30
    rupture_df["vs30measured"] = site_data.get("vs30measured", default=False)
    rupture_df["z1pt0"] = site_data.z1p0
    rupture_df["z2pt5"] = site_data.z2p5

    # Rupture Parameter
    # hypo_depth is not dbot but can be used as a proxy for point source
    # if there is only a single point then the dtop, dbot and hypo_depth
    # are at the same point
    # Commented on 19/05/22 to use an average of dbot and dtop for hypo_depth
    # to be more robust when supporting more models in the future.
    rupture_df["hypo_depth"] = np.mean([rupture_df["dbot"], rupture_df["dtop"]], axis=0)
    # zbot is not dbot but can be used as a proxy for point source, same reason above
    rupture_df[["ztor", "zbot"]] = rupture_df[["dtop", "dbot"]]

    # Distance Parameter - OQ uses ry0 term
    rupture_df[["rx", "ry0"]] = rupture_df[["rx", "ry"]].fillna(0)

    return rupture_df.loc[rupture_df["tect_type"] == tect_type.name]


def something(model, tect_type, rupture_context_df, im, psa_periods, rupture_df):
    # results = []
    GMM = classdef.GMM[model]
    gmm_calculated_df = openquake_wrapper_vectorized.oq_run(
        GMM,
        classdef.TectType["ACTIVE_SHALLOW"]
        if tect_type != "ACTIVE_SHALLOW"
        and GMM.name in ("CB_10", "CB_12", "AS_16",)
        else classdef.TectType[tect_type],
        rupture_context_df,
        str(im),
        psa_periods if im is gc.im.IMType.pSA else None,
    )
    # Matching the index with rupture_df
    # to have a right rupture label
    gmm_calculated_df.set_index(
        rupture_df[
            rupture_df["rupture_name"].isin(rupture_context_df["rupture_name"])
        ].index,
        inplace=True,
    )

    # Relabel the columns
    # PGA_mean -> PGA
    gmm_calculated_df.columns = np.char.rstrip(
        gmm_calculated_df.columns.values.astype(str), "_mean",
    )
    # PGA_std_Total -> PGA_sigma
    gmm_calculated_df.columns = np.char.replace(
        gmm_calculated_df.columns.values.astype(str), "_std_Total", "_sigma",
    )
    # results.append(gmm_calculated_df)
    return gmm_calculated_df


def calculate_emp_ds(
    background_sources_ffp: str,
    site_source_db_ffp: str,
    vs30_ffp: str,
    output_dir: str,
    z_ffp: Optional[str],
    ims: Optional[List[gc.im.IMType]],
    psa_periods: Optional[List[float]],
    model_dict_ffp: Optional[str],
    model_weights_ffp: Optional[str],
    suffix: Optional[str] = None,
):
    nhm_data = gc.utils.ds_nhm_to_rup_df(background_sources_ffp)
    rupture_df = pd.DataFrame(nhm_data["rupture_name"])
    model_dict = empirical_factory.read_model_dict(model_dict_ffp)

    with gc.dbs.SiteSourceDB(site_source_db_ffp) as distance_store:
        # TODO: simplify the get_work() - removing MPI
        fault_df, _, site_df, _ = common.get_work(
            distance_store, vs30_ffp, z_ffp, None, None
        )

        # Check to see if any site's Z1.0 or Z2.5 is NaN
        if np.any(np.isnan(site_df.z1p0.values)):
            raise ValueError("Z1.0 cannot be NaN")
        if np.any(np.isnan(site_df.z2p5.values)):
            raise ValueError("Z2.5 cannot be NaN")

        # Filter the site/station that the distance_store actually has
        sites = site_df.index[np.isin(site_df.index, distance_store.stored_stations())]

        tect_types = list(model_dict.keys())

        for im_idx, im in enumerate(ims):
            print(f"Processing IM: {im}, {im_idx + 1} / {len(ims)}")
            for tect_idx, tect_type in enumerate(tect_types):
                print(
                    f"Processing Tectonic Type: {tect_type}, {tect_idx + 1} / {len(tect_types)}"
                )
                GMMs = empirical_factory.determine_all_gmm(
                    classdef.Fault(tect_type=classdef.TectType[tect_type]),
                    str(im),
                    model_dict,
                )
                for GMM_idx, (GMM, _) in enumerate(GMMs):
                    db_type = f"{GMM.name}_{tect_type}"
                    # Create a DB if not exists
                    imdb = gc.dbs.IMDBParametric(
                        str(
                            Path(output_dir)
                            / gc.utils.create_parametric_db_name(
                                db_type, gc.constants.SourceType.distributed, suffix
                            )
                        ),
                        writeable=True,
                        source_type=gc.constants.SourceType.distributed,
                    )
                    if tect_type in ("SUBDUCTION_INTERFACE", "VOLCANIC"):
                        continue
                    print(
                        f"Processing Model: {GMM.name} for {tect_type}, {GMM_idx + 1} / {len(GMMs)}"
                    )
                    with imdb as imdb:
                        if model_weights_ffp:
                            meta_GMMs = meta_model.load_weights(
                                model_weights_ffp,
                                str(im),
                                classdef.TectType[tect_type],
                            )
                            for site in sites:
                                rupture_context_df = create_rupture_context_df(
                                    fault_df.merge(
                                        distance_store.station_data(site),
                                        left_on="fault_name",
                                        right_index=True,
                                    ),
                                    site_df.loc[site],
                                    nhm_data,
                                    classdef.TectType[tect_type],
                                )

                                with mp.Pool(processes=2) as p:
                                    results = p.starmap(
                                        something,
                                        [
                                            (
                                                model,
                                                tect_type,
                                                rupture_context_df,
                                                im,
                                                psa_periods
                                                if im is gc.im.IMType.pSA
                                                else None,
                                                rupture_df,
                                            )
                                            for model in meta_GMMs.keys()
                                        ],
                                    )
                                # for model in meta_GMMs.keys():
                                # GMM = classdef.GMM[model]
                                # gmm_calculated_df = openquake_wrapper_vectorized.oq_run(
                                #     GMM,
                                #     classdef.TectType["ACTIVE_SHALLOW"]
                                #     if tect_type != "ACTIVE_SHALLOW"
                                #     and GMM.name in ("CB_10", "CB_12", "AS_16",)
                                #     else classdef.TectType[tect_type],
                                #     rupture_context_df,
                                #     str(im),
                                #     psa_periods if im is gc.im.IMType.pSA else None,
                                # )
                                # # Matching the index with rupture_df
                                # # to have a right rupture label
                                # gmm_calculated_df.set_index(
                                #     rupture_df[
                                #         rupture_df["rupture_name"].isin(
                                #             rupture_context_df["rupture_name"]
                                #         )
                                #     ].index,
                                #     inplace=True,
                                # )
                                #
                                # # Relabel the columns
                                # # PGA_mean -> PGA
                                # gmm_calculated_df.columns = np.char.rstrip(
                                #     gmm_calculated_df.columns.values.astype(str),
                                #     "_mean",
                                # )
                                # # PGA_std_Total -> PGA_sigma
                                # gmm_calculated_df.columns = np.char.replace(
                                #     gmm_calculated_df.columns.values.astype(str),
                                #     "_std_Total",
                                #     "_sigma",
                                # )
                                # results.append(gmm_calculated_df)

                                # Dot products
                                meta_df = results[0].copy()
                                for column in meta_df.columns:
                                    col_df = pd.DataFrame(
                                        [result[column].values for result in results]
                                    ).T
                                    meta_df[column] = col_df.dot(
                                        pd.Series(meta_GMMs.values())
                                    ).values

                                # Write an im_df to the given station/site
                                imdb.add_im_data(
                                    site,
                                    meta_df.loc[
                                        :,
                                        # Only mean and sigma(std_Total) are needed
                                        ~meta_df.columns.str.contains("_std"),
                                    ],
                                )
                        else:
                            for site in sites:
                                rupture_context_df = create_rupture_context_df(
                                    fault_df.merge(
                                        distance_store.station_data(site),
                                        left_on="fault_name",
                                        right_index=True,
                                    ),
                                    site_df.loc[site],
                                    nhm_data,
                                    classdef.TectType[tect_type],
                                )
                                gmm_calculated_df = openquake_wrapper_vectorized.oq_run(
                                    GMM,
                                    classdef.TectType["ACTIVE_SHALLOW"]
                                    if tect_type != "ACTIVE_SHALLOW"
                                    and GMM.name in ("CB_10", "CB_12", "AS_16",)
                                    else classdef.TectType[tect_type],
                                    rupture_context_df,
                                    str(im),
                                    psa_periods if im is gc.im.IMType.pSA else None,
                                )
                                # Matching the index with rupture_df
                                # to have a right rupture label
                                gmm_calculated_df.set_index(
                                    rupture_df[
                                        rupture_df["rupture_name"].isin(
                                            rupture_context_df["rupture_name"]
                                        )
                                    ].index,
                                    inplace=True,
                                )

                                # Relabel the columns
                                # PGA_mean -> PGA
                                gmm_calculated_df.columns = np.char.rstrip(
                                    gmm_calculated_df.columns.values.astype(str),
                                    "_mean",
                                )
                                # PGA_std_Total -> PGA_sigma
                                gmm_calculated_df.columns = np.char.replace(
                                    gmm_calculated_df.columns.values.astype(str),
                                    "_std_Total",
                                    "_sigma",
                                )

                                # Write an im_df to the given station/site
                                imdb.add_im_data(
                                    site,
                                    gmm_calculated_df.loc[
                                        :,
                                        # Only mean and sigma(std_Total) are needed
                                        ~gmm_calculated_df.columns.str.contains("_std"),
                                    ],
                                )

                    print(f"Writing metadata for Model: {GMM.name}")
                    common.write_metadata(
                        imdb,
                        site_df,
                        background_sources_ffp,
                        vs30_ffp,
                        rupture_df,
                        common.curate_im_list(model_dict, db_type, psa_periods),
                    )
                    print(f"Writing metadata for Model: {GMM.name} is done.")


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
        "--model-weights",
        help="model weights dictionary to specify which model to use for each tect-type",
    )
    parser.add_argument(
        "--suffix", "-s", help="suffix for the end of the imdb files", default=None,
    )

    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    start = time.time()
    calculate_emp_ds(
        args.background_txt,
        args.site_source_db,
        args.vs30_file,
        args.output_dir,
        z_ffp=args.z_file,
        ims=args.im,
        psa_periods=args.periods,
        model_dict_ffp=args.model_dict,
        model_weights_ffp=args.model_weights,
        suffix=args.suffix,
    )
    print(f"Finished in {((time.time() - start) / 60):.2f} minutes")
