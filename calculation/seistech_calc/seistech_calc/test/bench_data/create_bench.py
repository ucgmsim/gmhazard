"""Script to create hazard benchmark data used to unit testing"""
import yaml
import argparse
import pathlib
import os
from typing import List, Dict

import numpy as np
import pandas as pd

import seistech_calc as sc

BENCH_ENSEMBLE_DIR = (
            pathlib.Path(os.getenv("ENSEMBLE_CONFIG_PATH"))
            / "benchmark_tests"
        )


def create_hazard_bench_data(
    ensemble_id: str,
    station_names: List[str],
    ims: List[sc.im.IM],
    output_dir: pathlib.PosixPath,
):
    """Creates hazard benchmark data for the specified stations and ims
    directory layers
    [ensemble_id -> im -> station -> branch_name.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for im in ims:
        im_dir = pathlib.Path(output_dir / f"{im.file_format()}_{im.component}")
        im_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(
                f"Computing hazard for {ensemble_id} - {im} - {station_name} - {im.component}"
            )
            site_info = sc.site.get_site_from_name(ens, station_name)
            station_dir = pathlib.Path(im_dir / station_name)
            station_dir.mkdir(parents=True, exist_ok=True)

            branch_hazards = sc.hazard.run_branches_hazard(ens, site_info, im)
            for cur_branch_name, cur_hazard in branch_hazards.items():
                csv_file_name = f"{cur_branch_name.replace('.', 'p')}.csv"
                cur_hazard.as_dataframe().to_csv(station_dir / csv_file_name)

            # Get the ensemble hazard
            ensemble_hazard = sc.hazard.run_ensemble_hazard(
                ens, site_info, im, branch_hazards
            )
            ensemble_hazard.as_dataframe().to_csv(station_dir / f"ensemble.csv")


def create_uhs_bench_data(
    ensemble_id: str,
    station_names: List[str],
    components: List[sc.im.IMComponent],
    exceedance_values: np.ndarray,
    output_dir: pathlib.PosixPath,
):
    """Creates uhs benchmark data for the specified stations and ims
    directory layers
    [ensemble_id -> station.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for component in components:
        component_dir = pathlib.Path(output_dir / str(component))
        component_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(f"Computing UHS for {ensemble_id} - {station_name} - {component}")
            site_info = sc.site.get_site_from_name(ens, station_name)

            uhs_results = sc.uhs.run_ensemble_uhs(
                ens, site_info, exceedance_values, im_component=component
            )
            df = sc.uhs.EnsembleUHSResult.combine_results(uhs_results)

            csv_file_name = f"{station_name.replace('.', 'p')}.csv"
            df.to_csv(component_dir / csv_file_name)


def create_disagg_grid_bench_data(
    ensemble_id: str,
    station_names: List[str],
    ims: List[sc.im.IM],
    exceedance: float,
    output_dir: pathlib.PosixPath,
):
    """Creates disagg gridded benchmark data for the specified stations
    and ims
    directory layers
    [ensemble_id -> im -> station -> branch_name -> __contr.csv]
    """

    def create_bench_dict(grid_disagg_data: sc.disagg.DisaggGridData):
        cur_bench_dict = {
            "flt_bin_contr": grid_disagg_data.flt_bin_contr,
            "ds_bin_contr": grid_disagg_data.ds_bin_contr,
            "eps_bin_contr": grid_disagg_data.eps_bin_contr,
        }

        return cur_bench_dict

    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for im in ims:
        im_dir = pathlib.Path(output_dir / f"{im.file_format()}_{im.component}")
        im_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(
                f"Computing disagg gridding for {ensemble_id} - {im} - {station_name}"
            )
            site_info = sc.site.get_site_from_name(ens, station_name)
            station_dir = pathlib.Path(im_dir / station_name)
            station_dir.mkdir(parents=True, exist_ok=True)

            # Disagg grid result per branch
            branches_disagg = sc.disagg.run_branches_disagg(
                ens.get_im_ensemble(im.im_type), site_info, im, exceedance=exceedance
            )
            for cur_branch_name, cur_disagg in branches_disagg.items():
                station_dict = create_bench_dict(
                    sc.disagg.run_disagg_gridding(cur_disagg)
                )
                for cur_branch_dir, cur_branch_data in station_dict.items():
                    contr_dir = pathlib.Path(station_dir / cur_branch_name)
                    contr_dir.mkdir(parents=True, exist_ok=True)

                    # https://numpy.org/doc/stable/reference/generated/numpy.set_printoptions.html
                    # Default number of digits of precision for floating point is 8
                    # Hence, storing 8 decimal points
                    if cur_branch_dir != "eps_bin_contr":
                        np.savetxt(
                            contr_dir / f"{cur_branch_dir}.csv",
                            cur_branch_data,
                            delimiter=",",
                            fmt="%1.8f",
                        )
                    else:
                        # eps_bin_contr is 3-dimensional, cannot store to csv
                        # by using one savetxt method
                        with open(contr_dir / f"{cur_branch_dir}.csv", "w") as outfile:
                            for slide_2d in cur_branch_data:
                                np.savetxt(
                                    outfile, slide_2d, delimiter=",", fmt="%1.8f"
                                )

            # Ensemble disagg grid result
            ens_disagg = sc.disagg.run_ensemble_disagg(
                ens, site_info, im, exceedance=exceedance
            )
            station_dict = create_bench_dict(sc.disagg.run_disagg_gridding(ens_disagg))
            for cur_branch_dir, cur_branch_data in station_dict.items():
                contr_dir = pathlib.Path(station_dir / "ensemble")
                contr_dir.mkdir(parents=True, exist_ok=True)
                if cur_branch_dir != "eps_bin_contr":
                    np.savetxt(
                        contr_dir / f"{cur_branch_dir}.csv",
                        cur_branch_data,
                        delimiter=",",
                        fmt="%1.8f",
                    )
                else:
                    with open(contr_dir / f"{cur_branch_dir}.csv", "w") as outfile:
                        for slide_2d in cur_branch_data:
                            np.savetxt(outfile, slide_2d, delimiter=",", fmt="%1.8f")


def create_disagg_bench_data(
    ensemble_id: str,
    station_names: List[str],
    ims: List[sc.im.IM],
    exceedance: float,
    output_dir: pathlib.PosixPath,
):
    """Creates disagg top contributors benchmark data
    for the specified stations and ims
    directory layers
    [ensemble_id -> IM -> station -> branch_name.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for im in ims:
        im_dir = pathlib.Path(output_dir / f"{im.file_format()}_{im.component}")
        im_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(f"Computing disagg for {ensemble_id} - {im} - {station_name}")
            site_info = sc.site.get_site_from_name(ens, station_name)
            station_dir = pathlib.Path(im_dir / station_name)
            station_dir.mkdir(parents=True, exist_ok=True)

            # Disagg result per dataset
            branches_disagg = sc.disagg.run_branches_disagg(
                ens.get_im_ensemble(im.im_type), site_info, im, exceedance=exceedance
            )
            for cur_branch_name, cur_disagg in branches_disagg.items():
                cur_disagg.total_contributions.to_csv(
                    station_dir / f"{cur_branch_name.replace('.', 'p')}.csv"
                )

            ens_disagg = sc.disagg.run_ensemble_disagg(
                ens, site_info, im, exceedance=exceedance
            )
            ens_disagg.total_contributions.to_csv(station_dir / "ensemble.csv")


def create_nzs1170p5_bench_data(
    ensemble_id: str,
    station_names: List[str],
    ims: List[sc.im.IM],
    z_factor_radii: List[float],
    output_dir: pathlib.PosixPath,
):
    """Creates NZS1170.5 benchmark data for the specified stations and ims
    directory layers
    [ensemble_id -> station -> IM.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for im in ims:
        for station_name in station_names:
            site_info = sc.site.get_site_from_name(ens, station_name)
            station_dir = pathlib.Path(output_dir / station_name)
            station_dir.mkdir(parents=True, exist_ok=True)
            radius_dict = {}
            for radius in z_factor_radii:
                print(
                    f"Computing NZ code - NZS1170.5 for {ensemble_id} - {im} - {station_name} - {im.component} - {radius}"
                )

                nz_code_result = sc.nz_code.nzs1170p5.run_ensemble_nzs1170p5(
                    ens, site_info, im, z_factor_radius=radius
                )
                radius_dict[radius] = nz_code_result.im_values

            csv_file_name = f"{im.file_format()}_{im.component}.csv"
            pd.DataFrame.from_dict(radius_dict).to_csv(station_dir / csv_file_name)


def create_nzta_bench_data(
    ensemble_id: str,
    station_names: List[str],
    components: List[sc.im.IMComponent],
    output_dir: pathlib.PosixPath,
):
    """Creates NZTA benchmark data for the specified stations and ims
    directory layers
    [ensemble_id -> station.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, config_ffp=ens_config_ffp)

    for component in components:
        component_dir = pathlib.Path(output_dir / str(component))
        component_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(f"Computing NZ code - NZTA for {ensemble_id} - {station_name}")
            site_info = sc.site.get_site_from_name(ens, station_name)

            result = sc.nz_code.nzta_2018.run_ensemble_nzta(
                ens, site_info, im_component=component
            )

            result_dict = {
                "pga_values": result.pga_values,
                "M_eff": result.M_eff,
                "C0_1000": result.C0_1000,
            }

            csv_file_name = f"{station_name.replace('.', 'p')}.csv"
            pd.DataFrame.from_dict(result_dict).to_csv(component_dir / csv_file_name)


def create_gms_bench_data(
    ensemble_id: str,
    station_names: List[str],
    gms_parameters: List[Dict],
    output_dir: pathlib.PosixPath,
):
    """Creates NZTA benchmark data for the specified stations and ims
    directory layers
    [ensemble_id -> station.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, config_ffp=ens_config_ffp)

    for gms_run in gms_parameters:
        parameters = gms_parameters[gms_run]
        for station_name in station_names:
            print(f"Computing GMS - GMS for {ensemble_id} - {station_name}")
            site_info = sc.site.get_site_from_name(ens, station_name)
            gm_dataset = sc.gms.GMDataset.get_GMDataset(parameters["dataset_id"])

            gms_result = sc.gms.run_ensemble_gms(
                ens,
                site_info,
                parameters["n_gms"],
                parameters["IMj"],
                gm_dataset,
                IMs=parameters["IMs"],
                exceedance=parameters["exceedance"],
                im_j=parameters["im_j"],
                n_replica=parameters["n_replica"],
            )

            for gcim, gcim_values in gms_result.IMi_gcims.items():
                gcim_dir = pathlib.Path(output_dir / gcim.replace(".", "p"))
                gcim_dir.mkdir(parents=True, exist_ok=True)
                csv_file_name = f"{station_name.replace('.', 'p')}_cdf.csv"
                gcim_values.lnIMi_IMj.cdf.to_frame().to_csv(gcim_dir / csv_file_name)

                for branch, branch_values in gcim_values.branch_uni_gcims.items():
                    branch_dir = pathlib.Path(gcim_dir / branch)
                    branch_dir.mkdir(parents=True, exist_ok=True)
                    csv_file_name = f"{station_name.replace('.', 'p')}_cdf.csv"
                    branch_values.lnIMi_IMj.cdf.to_frame().to_csv(
                        branch_dir / csv_file_name
                    )

                    csv_file_name = f"{station_name.replace('.', 'p')}_mu.csv"
                    branch_values.lnIMi_IMj_Rup.mu.to_frame().to_csv(
                        branch_dir / csv_file_name
                    )

                    csv_file_name = f"{station_name.replace('.', 'p')}_sigma.csv"
                    branch_values.lnIMi_IMj_Rup.sigma.to_frame().to_csv(
                        branch_dir / csv_file_name
                    )


def create_scenarios_bench_data(
    ensemble_id: str,
    station_names: List[str],
    components: List[sc.im.IMComponent],
    output_dir: pathlib.PosixPath,
):
    """Creates scenarios benchmark data for the specified stations and component
    directory layers
    [ensemble_id -> component -> station.csv]
    """
    ens_config_ffp = BENCH_ENSEMBLE_DIR / f"{ensemble_id}.yaml"
    ens = sc.gm_data.Ensemble(ensemble_id, ens_config_ffp)

    for component in components:
        component_dir = pathlib.Path(output_dir / str(component))
        component_dir.mkdir(parents=True, exist_ok=True)
        for station_name in station_names:
            print(
                f"Computing Scenarios for {ensemble_id} - {station_name} - {component}"
            )
            site_info = sc.site.get_site_from_name(ens, station_name)

            ensemble_scenario = sc.scenario.run_ensemble_scenario(
                ens, site_info, im_component=component
            )

            csv_file_name = f"{station_name.replace('.', 'p')}.csv"
            ensemble_scenario.percentiles.to_csv(component_dir / csv_file_name)


def _get_ims(
    string_ims: List[str],
    components: bool,
    default_component: sc.im.IMComponent = sc.im.IMComponent.RotD50,
):
    ims = []
    for im_string in string_ims:
        im = sc.im.IM.from_str(im_string)
        if components:
            ims.extend(
                [
                    sc.im.IM(im.im_type, im.period, component)
                    for component in sc.im.IM_COMPONENT_MAPPING[im.im_type]
                ]
            )
        else:
            im.component = default_component
            ims.append(im)
    return ims


def main(args):
    bench_dir = args.bench_data_dir
    config_file = args.config

    # Check if the specified config_file is a full path or just a filename
    if not pathlib.Path(config_file).is_file():
        config_file = bench_dir / config_file

    # Read config
    with open(config_file, "r") as f:
        config = yaml.safe_load(f)

    # Benchmark data type (i.e. either hazard, disagg, uhs or gms)
    type = config["type"]

    ensembles = config["ensembles"]
    for ensemble_id in ensembles:
        output_dir = pathlib.Path(bench_dir).resolve() / type / f"{ensemble_id}"
        # Create directory if not exists
        output_dir.mkdir(parents=True, exist_ok=True)

        if type == "hazard":
            create_hazard_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                _get_ims(
                    ensembles[ensemble_id]["ims"], config[ensemble_id]["components"]
                ),
                output_dir,
            )
        elif type == "disagg_grid":
            create_disagg_grid_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                _get_ims(
                    ensembles[ensemble_id]["ims"], ensembles[ensemble_id]["components"]
                ),
                ensembles[ensemble_id]["exceedance"],
                output_dir,
            )
        elif type == "disagg":
            create_disagg_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                _get_ims(
                    ensembles[ensemble_id]["ims"], ensembles[ensemble_id]["components"]
                ),
                ensembles[ensemble_id]["exceedance"],
                output_dir,
            )
        elif type == "uhs":
            create_uhs_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                [component for component in sc.im.IMComponent]
                if ensembles[ensemble_id]["components"]
                else [sc.im.IMComponent.RotD50],
                np.asanyarray(ensembles[ensemble_id]["exceedance_levels"]),
                output_dir,
            )
        elif type == "nzs1170p5":
            create_nzs1170p5_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                _get_ims(
                    ensembles[ensemble_id]["ims"],
                    ensembles[ensemble_id]["components"],
                    sc.im.IMComponent.Larger,
                ),
                ensembles[ensemble_id]["z_factor_radius"],
                output_dir,
            )
        elif type == "nzta":
            create_nzta_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                [component for component in sc.im.IMComponent]
                if ensembles[ensemble_id]["components"]
                else [sc.im.IMComponent.Larger],
                output_dir,
            )
        elif type == "gms":
            create_gms_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                ensembles[ensemble_id]["gms_parameters"],
                output_dir,
            )
        elif type == "scenarios":
            create_scenarios_bench_data(
                ensemble_id,
                ensembles[ensemble_id]["station_names"],
                [component for component in sc.im.IMComponent]
                if ensembles[ensemble_id]["components"]
                else [sc.im.IMComponent.RotD50],
                output_dir,
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "bench_data_dir", type=str, help="Path of the bench_data directory"
    )
    parser.add_argument(
        "config",
        type=str,
        help="Path of the testing config, can just be a filename, "
        "if the file is located in the bench_data data_dir",
    )

    args = parser.parse_args()

    main(args)
