"""Script for the collection of event based ratio map data

Note: If non-ratio maps are ever required for a single ensemble,
then this script should be modified this,
similarly to imdb_event_map_runner
"""
import os
import argparse

import seistech_calc as sc
import shared


def get_imdb(ens: sc.gm_data.Ensemble, rupture_id: str):
    """Gets the relevant imdb for the given rupture in the
    specifed ensemble
    """
    branch = ens.branches[list(ens.branches.keys())[0]]

    for imdb_ffp in branch.fault_imdbs:
        with sc.dbs.IMDB.get_imdb(imdb_ffp) as db:
            if rupture_id in sc.rupture.rupture_name_to_id(
                db.rupture_names(), branch.flt_erf_ffp
            ):
                return imdb_ffp


def main(
    ensemble_id_1: str,
    ensemble_id_2: str,
    output_dir: str,
    station_list_ffp: str,
    n_procs: int = 8,
    lat_max_filter: float = None,
):
    ens_1 = sc.gm_data.Ensemble(ensemble_id_1)
    ens_2 = sc.gm_data.Ensemble(ensemble_id_2)

    # Only support ensembles with a single branch
    if len(ens_1.branches) > 1 or len(ens_2.branches) > 1:
        raise NotImplementedError()

    # Get all ruptures & IMs that are in both ensembles
    flt_ruptures_1 = ens_1.rupture_df_id.loc[
        ens_1.rupture_df_id.rupture_type == sc.SourceType.fault.value
        ].index.values.astype(str)
    flt_ruptures_2 = ens_2.rupture_df_id.loc[
        ens_2.rupture_df_id.rupture_type == sc.SourceType.fault.value
        ].index.values.astype(str)
    flt_ruptures = set(flt_ruptures_1) & set(flt_ruptures_2)
    ims = set(ens_1.ims) & set(ens_2.ims)

    for ix, cur_rup in enumerate(list(flt_ruptures)):
        print(f"Processing rupture {cur_rup}, {ix + 1}/{len(flt_ruptures)}")
        cur_dir = os.path.join(output_dir, ens_1.rupture_df_id.loc[cur_rup].rupture_name)
        if os.path.isdir(cur_dir):
            print(f"Output dir for fault {cur_rup} already exists, skipping")
            continue

        imdb_1_ffp = get_imdb(ens_1, cur_rup)
        imdb_2_ffp = get_imdb(ens_2, cur_rup)

        if imdb_1_ffp is None or imdb_2_ffp is None:
            print(
                f"Rupture {cur_rup} does not exist in any of the IMDBs of ensemble "
                f"{ens_1.name if imdb_1_ffp is None else ens_2.name}, "
                f"skipping"
            )
            continue

        os.mkdir(cur_dir)
        for cur_im in ims:
            r = shared.gen_event_ratio_data(
                cur_im,
                cur_rup.split("_")[0],
                imdb_1_ffp,
                imdb_2_ffp,
                cur_dir,
                station_list_ffp,
                n_procs=n_procs,
                lat_max_filter=lat_max_filter,
            )
            continue


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "ensemble_id_1",
        type=str,
        help="The ensemble id of the first ensemble, "
             "note the ratio is computed as ln(ensemble_id/ensemble_id)",
    )
    parser.add_argument("ensemble_id_2", type=str)
    parser.add_argument("station_list_ffp", type=str, help="Station list file")
    parser.add_argument("output_dir", type=str)
    parser.add_argument("--n_procs", type=int, default=8)
    parser.add_argument(
        "--lat_max_filter",
        type=float,
        help="All station with lat > lat_max_filter are ignored",
    )

    args = parser.parse_args()

    main(
        args.ensemble_id_1,
        args.ensemble_id_2,
        args.output_dir,
        args.station_list_ffp,
        n_procs=args.n_procs,
        lat_max_filter=args.lat_max_filter,
    )
