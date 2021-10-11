import argparse

import gmhazard_utils as utils


def create_ensemble_main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ensemble_name")
    parser.add_argument(
        "-o",
        "--output_dir",
        default=".",
        help="directory to write the ensemble config file",
    )
    parser.add_argument("--empirical_weight_config")
    parser.add_argument("--ds_ssdb")
    parser.add_argument("--ds_erf")
    parser.add_argument("--flt_ssdb")
    parser.add_argument("--flt_erfs", nargs="+")
    parser.add_argument("--station_list")
    parser.add_argument("--station_vs30")
    parser.add_argument(
        "--version", default=utils.ensemble_creation.DEFAULT_VERSION_NUMBER
    )
    parser.add_argument("--dbs", nargs="+")
    parser.add_argument("--n_perts", default=1, type=int)
    args = parser.parse_args()

    utils.ensemble_creation.create_ensemble(
        args.ensemble_name,
        args.output_dir,
        args.empirical_weight_config,
        stat_list_ffp=args.station_list,
        stat_vs30_ffp=args.station_vs30,
        flt_erf_ffps=args.flt_erfs,
        ds_erf_ffp=args.ds_erf,
        flt_ssdb_ffp=args.flt_ssdb,
        ds_ssdb_ffp=args.ds_ssdb,
        db_list=args.dbs,
        version=args.version,
        n_perts=args.n_perts,
    )


if __name__ == "__main__":
    create_ensemble_main()
