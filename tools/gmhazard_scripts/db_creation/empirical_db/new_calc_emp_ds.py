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
    rupture_df[["hypo_depth", "ztor"]] = rupture_df[["dbot", "dtop"]]

    # Distance Parameter - OQ uses ry0 term
    rupture_df[["rx", "ry0"]] = rupture_df[["rx", "ry"]].fillna(0)

    return rupture_df.loc[rupture_df["tect_type"] == tect_type.name]


def calculate_emp_ds(
    background_sources_ffp: str,
    site_source_db_ffp: str,
    vs30_ffp: str,
    output_dir: str,
    z_ffp: Optional[str],
    ims: Optional[List[gc.im.IMType]],
    psa_periods: Optional[List[float]],
    model_dict_ffp: Optional[str],
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
        sites = [
            site for site in site_df.index if distance_store.has_station_data(site)
        ]
        tect_types = nhm_data["tect_type"].unique()

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
                    # TODO: Check those models
                    if GMM.name in ("K_20", "K_20_NZ", "ZA_06", "CB_14", "ASK_14"):
                        print(f"{GMM.name} is currently not supported.")
                        continue

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
                    print(
                        f"Processing Model: {GMM.name} for {tect_type}, {GMM_idx + 1} / {len(GMMs)}"
                    )
                    with imdb as imdb:
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
                                classdef.TectType[tect_type],
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
                            # PGA_std_Total -> PGA_sigma
                            gmm_calculated_df.columns = [
                                f"{'_'.join(col.split('_')[:2]) if im is gc.im.IMType.pSA else im}"
                                if col.endswith("mean")
                                else col
                                for col in gmm_calculated_df
                            ]
                            gmm_calculated_df.columns = [
                                f"{'_'.join(col.split('_')[:2]) if im is gc.im.IMType.pSA else im}_sigma"
                                if col.endswith("std_Total")
                                else col
                                for col in gmm_calculated_df
                            ]

                            # Write an im_df to the given station/site
                            imdb.add_im_data(
                                site,
                                gmm_calculated_df.loc[
                                    :,
                                    # Only mean and std_Total are needed
                                    ~gmm_calculated_df.columns.str.endswith(
                                        ("std_Inter", "std_Intra")
                                    ),
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
        suffix=args.suffix,
    )
    print(f"Finished in {(time.time() - start) / 60}")
