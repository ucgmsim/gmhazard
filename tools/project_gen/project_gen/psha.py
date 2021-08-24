import multiprocessing as mp
from pathlib import Path
from typing import Sequence, Union

import yaml
import pandas as pd
import numpy as np
import celery

import seistech_calc as si
from . import tasks
from . import utils

# Solve this a bit better in the future...
VS30_GRID_FFP = "/mnt/mantle_data/seistech/vs30/19p1/nz_vs30_nz-specific-v19p1_100m.grd"


def gen_psha_project_data(project_dir: Path, n_procs: int = 1, use_mp: bool = True):
    """Computes the PSHA project data for the specified project directory"""
    project_id = project_dir.name
    results_dir = project_dir / "results"

    # Load the project definition config
    with open(project_dir / f"{project_id}.yaml", "r") as f:
        project_dict = yaml.safe_load(f)

    # Load the project parameters
    project_params = project_dict["project_parameters"]
    ims = si.im.to_im_list(project_params["ims"])
    im_components = [
        si.im.IMComponent[component] for component in project_params["im_components"]
    ]
    for im_component in im_components:
        if im_component != si.im.IMComponent.RotD50:
            ims.extend(
                [
                    si.im.IM(im.im_type, im.period, im_component)
                    for im in ims
                    if im.is_pSA() or im.im_type == si.im.IMType.PGA
                ]
            )

    # Exceedances
    disagg_exceedances = [
        1 / cur_rp for cur_rp in project_params["disagg_return_periods"]
    ]
    uhs_exceedances = [1 / cur_rp for cur_rp in project_params["uhs_return_periods"]]

    # Load the ensemble
    ensemble_ffp = project_dict["ensemble_ffp"]
    ensemble = si.gm_data.Ensemble(
        project_id, config_ffp=ensemble_ffp, use_im_data_cache=False
    )

    # Get the full list of station ids
    station_ids = utils.get_station_ids(project_params)

    # Create the context & vs30 maps
    if use_mp:
        with mp.Pool(processes=n_procs) as p:
            p.starmap(
                generate_maps,
                [(ensemble, cur_station, results_dir) for cur_station in station_ids],
            )
    else:
        celery.group(
            tasks.generate_maps_task.s(
                project_id, ensemble_ffp, cur_station, str(results_dir)
            )
            for cur_station in station_ids
        )()

    # Generate the station - IM combinations
    # Breaking calculations down into "smallest" chunks
    station_im_comb = [
        (cur_station, cur_im) for cur_station in station_ids for cur_im in ims
    ]

    # Run the hazard and disagg calculation
    if use_mp:
        with mp.Pool(processes=n_procs) as p:
            p.starmap(
                process_station_im,
                [
                    (
                        ensemble,
                        cur_station,
                        cur_im,
                        disagg_exceedances,
                        str(results_dir / cur_station / str(cur_im.component)),
                    )
                    for cur_station, cur_im in station_im_comb
                ],
            )
    else:
        celery.group(
            tasks.process_station_im_task.s(
                project_id,
                ensemble_ffp,
                cur_station,
                cur_im,
                disagg_exceedances,
                str(results_dir / cur_station / str(cur_im.component)),
            )
            for cur_station, cur_im in station_im_comb
        )()

    if len(uhs_exceedances) > 0:
        for cur_station in station_ids:
            cur_site_info = si.site.get_site_from_name(ensemble, cur_station)

            # Computing UHS for each of the IM Components
            for im_component in im_components:
                cur_output_dir = results_dir / cur_station / str(im_component)
                print(
                    f"Computing UHS for station {cur_station} - Component {im_component}"
                )

                # Compute & write UHS
                uhs_results = si.uhs.run_ensemble_uhs(
                    ensemble,
                    cur_site_info,
                    np.asarray(uhs_exceedances),
                    n_procs=n_procs,
                    calc_percentiles=True,
                    im_component=im_component,
                )
                for cur_uhs_result in uhs_results:
                    cur_uhs_result.save(cur_output_dir)

                # Compute & write UHS NZS1170.5
                cur_uhs_nzs1170p5_dir = cur_output_dir / "uhs_nz11750"
                cur_uhs_nzs1170p5_dir.mkdir(exist_ok=False, parents=False)
                uhs_nzs1170p5 = si.uhs.run_nzs1170p5_uhs(
                    ensemble,
                    cur_site_info,
                    np.asarray(uhs_exceedances),
                    opt_nzs1170p5_args={"im_component": str(im_component)},
                )
                for cur_uhs_nzs1170p5 in uhs_nzs1170p5:
                    cur_uhs_nzs1170p5.save(cur_uhs_nzs1170p5, uhs=True)


def generate_maps(
    ensemble: si.gm_data.Ensemble, station_name: str, results_dir: Union[str, Path]
):
    """Generates the context and vs30 map for the specified station"""
    results_dir = Path(results_dir)

    site_info = si.site.get_site_from_name(ensemble, station_name)
    output_dir = results_dir / station_name

    # Create the current output directory (if required)
    output_dir.mkdir(exist_ok=False, parents=False)

    # Generate the context maps
    print(f"Generating context maps for station {site_info.station_name}")
    si.plots.gmt_context(
        site_info.lon, site_info.lat, str(output_dir / "context_map_plot"),
    )

    # Generate the vs30 map
    si.plots.gmt_vs30(
        str(output_dir / "vs30_map_plot.png"),
        site_info.lon,
        site_info.lat,
        site_info.lon,
        site_info.lat,
        site_info.vs30,
        ensemble.station_ffp,
        VS30_GRID_FFP,
    )


def process_station_im(
    ensemble: si.gm_data.Ensemble,
    station_name: str,
    im: si.im.IM,
    disagg_exceedances: Sequence[float],
    output_dir: Union[str, Path],
):
    """Computes hazard, NZS1170.5 and disagg for the
    specified station and IM (and exceedances for disagg)

    If a exceedance is out of the supported range
    for the specified station it is skipped (i.e. no results
    are generated and saved)
    """
    output_dir = Path(output_dir)

    # Get the site
    site_info = si.site.get_site_from_name(ensemble, station_name)

    # Compute & write hazard
    print(
        f"Computing hazard for station {site_info.station_name} - IM {im} - Component {im.component}"
    )
    si.hazard.run_ensemble_hazard(ensemble, site_info, im, calc_percentiles=True).save(
        output_dir
    )

    # Compute & write NZS1170.5
    print(
        f"Computing NZS1170.5 for station {site_info.station_name} - IM {im} - Component {im.component}"
    )
    si.nz_code.nzs1170p5.run_ensemble_nzs1170p5(ensemble, site_info, im).save(
        output_dir
    )

    # Compute & write NZTA hazard
    if im.im_type == si.im.IMType.PGA:
        si.nz_code.nzta_2018.run_ensemble_nzta(ensemble, site_info).save(output_dir)

    # Compute & write disagg for the different exceedances
    for cur_excd in disagg_exceedances:
        cur_rp = int(1.0 / cur_excd)
        print(
            f"Computing disagg for station {site_info.station_name} - "
            f"IM {im} - Component {im.component} - Return period {cur_rp}"
        )
        try:
            cur_disagg_data = si.disagg.run_ensemble_disagg(
                ensemble, site_info, im, exceedance=cur_excd, calc_mean_values=True
            )
        except si.exceptions.ExceedanceOutOfRangeError as ex:
            print(
                f"Failed to compute disagg for IM {ex.im} and exceedance {ex.exceedance} as the"
                f"exceedance is outside of the computed hazard range for this site, skipping!"
            )
        else:
            cur_disagg_grid_data = si.disagg.run_disagg_gridding(cur_disagg_data)

            # Save
            cur_disagg_data_dir = cur_disagg_data.save(output_dir)
            cur_disagg_grid_data.save(cur_disagg_data_dir, save_disagg_data=False)

            # Additional info for the table
            # Annual rec prob, magnitude and rrup (for disagg table)
            ruptures_df = ensemble.rupture_df.loc[
                cur_disagg_data.fault_disagg.index.values
            ]
            flt_dist_df = si.site_source.get_distance_df(
                ensemble.flt_ssddb_ffp, site_info
            )
            merged_df = pd.merge(
                ruptures_df,
                flt_dist_df,
                how="left",
                left_on="rupture_name",
                right_index=True,
            )
            merged_df = merged_df.loc[
                :, ["annual_rec_prob", "magnitude", "rupture_name", "rrup"]
            ]
            merged_df.to_csv(
                cur_disagg_data_dir
                / f"disagg_{im.file_format()}_{cur_rp}_metadata.csv",
                index_label="record_id",
            )

            # Generate the disagg plots
            si.plots.gmt_disagg(
                str(cur_disagg_data_dir / f"disagg_{im.file_format()}_{cur_rp}_src"),
                cur_disagg_grid_data.to_dict(),
                bin_type="src",
            )
            si.plots.gmt_disagg(
                str(cur_disagg_data_dir / f"disagg_{im.file_format()}_{cur_rp}_eps"),
                cur_disagg_grid_data.to_dict(),
                bin_type="eps",
            )
