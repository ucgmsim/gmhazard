"""Script that generates a bash script that allows generation
of hazard map data for all the specified combinations (ensemble, IMs, excd prob)
"""
import os
import argparse
from collections import namedtuple
from typing import Iterable

import yaml

import gmhazard_calc as sc

RunCombination = namedtuple(
    "RunCombination", "ensemble_id, im, excd_prob, excd_percentage, excd_years, n_procs"
)


def gen_script(
    run_hazard_script_ffp: str,
    out_script_ffp: str,
    output_dir: str,
    combinations: Iterable[RunCombination],
    nz_code: bool = False,
    maui: bool = False,
):
    with open(out_script_ffp, "w") as f:
        for cur_comb in combinations:
            file_prefix = 'nz_code' if nz_code else cur_comb.ensemble_id
            cur_ffp = os.path.join(
                output_dir,
                f"{file_prefix}_{cur_comb.im.replace('.', 'p')}_"
                f"{str(cur_comb.excd_percentage).replace('.', 'p')}_{cur_comb.excd_years}",
            )

            if maui:
                cur_line = (
                    "HDF5_USE_FILE_LOCKING=FALSE srun -t 06:00:00 -o {} "
                    "python3 {} {} {} {} {} --n_procs {} "
                    "--exceedance_title '{}' {} &\n".format(
                        f"{cur_ffp}.log",
                        run_hazard_script_ffp,
                        cur_comb.ensemble_id,
                        cur_comb.im,
                        cur_comb.excd_prob,
                        f"{cur_ffp}.csv",
                        cur_comb.n_procs,
                        f"{cur_comb.excd_percentage}% in {cur_comb.excd_years} years",
                        "--nz_code" if nz_code else ""
                    )
                )
            else:
                cur_line = (
                    "python3 {} {} {} {} {} --n_procs {} "
                    "--exceedance_title '{}' {} 1>{} 2>{} &\n".format(
                        run_hazard_script_ffp,
                        cur_comb.ensemble_id,
                        cur_comb.im,
                        cur_comb.excd_prob,
                        f"{cur_ffp}.csv",
                        cur_comb.n_procs,
                        f"{cur_comb.excd_percentage}% in {cur_comb.excd_years} years",
                        "--nz_code" if nz_code else "",
                        f"{cur_ffp}.log",
                        f"{cur_ffp}.log",
                    )
                )

            f.write(cur_line)


def get_combinations(config_ffp: str):
    with open(config_ffp, "r") as f:
        config = yaml.safe_load(f)["combinations"]

    combinations = []
    for cur_ens_id, cur_ens_config in config.items():
        for im in cur_ens_config["ims"]:
            for excd_prob_dict in cur_ens_config["excd_prob"]:
                excd_perct = excd_prob_dict["percentage"]
                excd_years = excd_prob_dict["years"]

                combinations.append(
                    RunCombination(
                        cur_ens_id,
                        im,
                        sc.hazard.get_exceedance_rate(excd_perct, excd_years),
                        excd_perct,
                        excd_years,
                        cur_ens_config["n_procs"],
                    )
                )
    return combinations


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "run_hazard_map_calc_ffp",
        type=str,
        help="File path to the run_hazard_map_calc.py script",
    )
    parser.add_argument(
        "out_script_ffp", type=str, help="The file path of the output bash script"
    )
    parser.add_argument(
        "output_dir", type=str, help="The output directory for the hazard map data"
    )
    parser.add_argument(
        "config_ffp",
        type=str,
        help="The yaml config file that specifies which combinations to run",
    )

    parser.add_argument("--maui", action="store_true", default=False)
    parser.add_argument(
        "--nz_code",
        action="store_true",
        default=False,
        help="If set then the hazard is generated using the NZ code",
    )

    args = parser.parse_args()

    combs = get_combinations(args.config_ffp)
    gen_script(
        args.run_hazard_map_calc_ffp,
        args.out_script_ffp,
        args.output_dir,
        combs,
        args.nz_code,
        args.maui,
    )
