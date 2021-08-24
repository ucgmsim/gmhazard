#!/bin/env python3
"""Script for computing the difference in median values
of a parametric and non-parametric ensemble for a specific
rupture and IM, at each station for plotting on a hazard like map

This is debugging/analysis script.
"""
import argparse

import seistech_calc as si
import shared


def main(args):
    if args.imdb_2_ffp is None:
        with si.dbs.IMDB.get_imdb(args.imdb_1_ffp) as db:
            station_df = db.sites()

        shared.gen_event_data(
            args.im,
            args.rupture,
            args.imdb_1_ffp,
            station_df,
            args.output_dir,
            n_procs=args.n_procs,
            lat_max_filter=args.lat_max_filter,
        )
    else:
        shared.gen_event_ratio_data(
            args.im,
            args.rupture,
            args.imdb_1_ffp,
            args.imdb_2_ffp,
            args.output_dir,
            args.station_list_ffp,
            n_procs=args.n_procs,
            lat_max_filter=args.lat_max_filter,
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("im", type=str, help="The im of interest")
    parser.add_argument("rupture", type=str, help="The rupture name")
    parser.add_argument(
        "imdb_1_ffp",
        type=str,
        help="Path for the 1st IMDB, if no 2nd IMDB is specified "
        "then the event based data for this IMDB is calculated,"
        "otherwise the ratio is calculated",
    )
    parser.add_argument(
        "--imdb_2_ffp",
        type=str,
        help="Path for the 2nd IMDB, if specified then the ratio is computed",
        default=None,
    )
    parser.add_argument("output_dir", type=str, help="Output directory")
    parser.add_argument(
        "--station_list_ffp",
        type=str,
        help="Station list file path, required if imdb_2_ffp is specified",
        default=None,
    )
    parser.add_argument(
        "--n_procs", type=int, help="Number of processes to use", default=4
    )
    parser.add_argument(
        "--lat_max_filter",
        type=float,
        help="All stations with lat > lat_max_filter are ignored",
    )

    args = parser.parse_args()

    main(args)
