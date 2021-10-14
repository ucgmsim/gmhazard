"""Script for collection of event based map data at IMDB level

Note: If ratio map data is ever required at IMDB level,
then this script should be modified to support this.
"""
import os
import argparse

import gmhazard_calc as sc
import shared


def main(
    imdb_ffp: str, output_dir: str, n_procs: int = 4, lat_max_filter: float = None
):
    # Get the stations
    with sc.dbs.IMDB.get_imdb(imdb_ffp) as db:
        station_df = db.sites()
        rupture_names = db.rupture_names()
        ims = db.ims

    for ix, cur_rup in enumerate(rupture_names):
        print(f"Processing rupture {cur_rup}, {ix + 1}/{rupture_names.size}")
        cur_dir = os.path.join(output_dir, cur_rup)

        if os.path.isdir(cur_dir):
            print(f"Output dir for fault {cur_rup} already exists, skipping")
            continue

        os.mkdir(cur_dir)
        for cur_im in ims:
            shared.gen_event_data(
                cur_im,
                cur_rup,
                imdb_ffp,
                station_df,
                cur_dir,
                n_procs=n_procs,
                lat_max_filter=lat_max_filter,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("imdb_ffp", type=str, help="The file path to the imdb")
    parser.add_argument("output_dir", type=str)
    parser.add_argument("--n_procs", type=int, default=4)
    parser.add_argument(
        "--lat_max_filter",
        type=float,
        help="All station with lat > lat_max_filter are ignored",
    )

    args = parser.parse_args()

    main(
        args.imdb_ffp,
        args.output_dir,
        n_procs=args.n_procs,
        lat_max_filter=args.lat_max_filter,
    )
