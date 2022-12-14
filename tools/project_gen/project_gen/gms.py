"""Script for generating the ground motion selection results"""
import multiprocessing as mp
from pathlib import Path
from typing import List, Tuple

import yaml
import numpy as np

import gmhazard_calc as gc
from . import utils


def process_station_gms_config_comb(
    ensemble: gc.gm_data.Ensemble,
    station_name: str,
    gms_id: str,
    IMj: gc.im.IM,
    IMs: np.ndarray,
    n_gms: int,
    output_dir: Path,
    gm_dataset_id: str,
    im_j: float = None,
    exceedance: float = None,
    n_replica: int = 10,
    sf_bounds: Tuple[float, float] = None,
):
    """Processes to a single station and GMS-config"""
    # Get the site
    if (gms_out_dir := output_dir / gc.gms.GMSResult.get_save_dir(gms_id)).exists():
        print(
            f"Skipping GMS computation for station {station_name} and "
            f"id {gms_id} as it already exists"
        )
        return

    print(f"Computing GMS for station {station_name} and id {gms_id}")

    # Get site and create the current output directory (if required)
    site_info = gc.site.get_site_from_name(ensemble, station_name)
    output_dir.mkdir(exist_ok=True, parents=False)

    cs_param_bounds = None
    if ensemble.flt_im_data_type is gc.IMDataType.parametric:
        # Calculates Disagg
        try:
            disagg_data = gc.disagg.run_ensemble_disagg(
                ensemble,
                site_info,
                IMj,
                exceedance=exceedance,
                im_value=im_j,
                calc_mean_values=True,
            )
        except gc.exceptions.ExceedanceOutOfRangeError as ex:
            print(
                f"\tFailed to compute disagg for gms id {gms_id}, site {site_info.station_name}, IM {ex.im} "
                f"and exceedance {ex.exceedance} as the exceedance is outside of the computed "
                f"hazard range for this site, skipping!"
            )
            return

        # Save the Disagg Data
        disagg_output_dir = output_dir / f"gms_{gms_id}" / "disagg_data"
        disagg_output_dir.mkdir(exist_ok=True, parents=True)
        disagg_data.save(disagg_output_dir)

        # Retrieve the default causal filter parameters
        cs_param_bounds = gc.gms.default_causal_params(
            ensemble,
            site_info,
            IMj,
            exceedance=exceedance,
            im_value=im_j,
            disagg_data=disagg_data,
            sf_bounds=sf_bounds,
        )

    # Get the GM dataset
    gm_dataset = gc.gms.GMDataset.get_GMDataset(gm_dataset_id)

    # Can only use IMs that are supported by the GM dataset
    IMs = IMs[np.isin(IMs, gm_dataset.ims)]

    # Run the GM selection
    try:
        gc.gms.run_ensemble_gms(
            ensemble,
            site_info,
            n_gms,
            IMj,
            gm_dataset,
            IMs,
            cs_param_bounds=cs_param_bounds,
            im_j=im_j,
            exceedance=exceedance,
            n_replica=n_replica,
            gms_id=gms_id,
        ).save(output_dir, gms_id)
    # Require additional exceedance error handling here, as it is possible to run
    # fine for disagg, but get an exceedance error here.
    # This is due to the fact that disagg uses mean hazard,
    # whereas GMS uses branch hazard.
    except gc.exceptions.ExceedanceOutOfRangeError as ex:
        print(
            f"\tFailed to compute GMS for gms id {gms_id}, site {site_info.station_name}, IM {ex.im} and "
            f"exceedance {exceedance} as the exceedance is outside of the computed hazard \
            range for this site, skipping!"
        )
        return
    except gc.exceptions.NotSufficientNumberOfSimulationsError as ex:
        print(f"Failed to compute GMS for gms id {gms_id}, site {site_info.station_name}, "
              f"IMj {ex.IMj}, and exceedance {exceedance} as there are "
              f"not enough simulations available to compute IMi|IMj")
    except AssertionError as ex:
        print(
            f"\tFailed to compute GMS for gms id {gms_id}, site {site_info.station_name}, "
            f"IM {IMj} and exceedance {exceedance} due an assert error:\n{ex}"
        )
        return


def _get_gms_ims(IMj: str, im_strings: List[str], ensemble: gc.gm_data.Ensemble):
    """
    Generates a list of IMs that does not contain IMj.
    Allows for a shortcut "pSA" to be set to generate all pSA IM's that are available for the given Ensemble.

    Parameters
    -----------
    IMj: str
        The IM to not add to list of IMs
    im_strings: List[str]
        The list of strings from the gms config file
    ensemble: Ensemble
        The ensemble to grab pSA periods from if "pSA" is specified in the config
    """
    IMj = gc.im.IM.from_str(IMj)
    ims = []
    for im_string in im_strings:
        if im_string == "pSA":
            ims.extend(
                [
                    gc.im.IM(gc.im.IMType.pSA, period=cur_im.period)
                    for cur_im in ensemble.ims
                    if cur_im.period != IMj.period
                    and cur_im.is_pSA()
                    and cur_im.component is gc.im.IMComponent.RotD50
                ]
            )
        else:
            im = gc.im.IM.from_str(im_string)
            if im != IMj:
                ims.append(im)
    return np.asarray(ims)


def gen_gms_project_data(project_dir: Path, n_procs: int = 1):
    project_name = project_dir.name

    # Load the project definition config
    with open(project_dir / f"{project_name}.yaml", "r") as f:
        project_dict = yaml.safe_load(f)

    # Load the project parameters
    project_params = project_dict["project_parameters"]

    if "gms" not in project_params.keys():
        print("No GMS parameters specified. Skipping GMS!")
        return

    # Load GMS parameters
    gms_params = project_params["gms"]
    gms_ids = list(gms_params.keys())

    # Load the ensemble
    ensemble_ffp = project_dict["ensemble_ffp"]
    ensemble = gc.gm_data.Ensemble(
        project_name, config_ffp=ensemble_ffp, use_im_data_cache=True
    )

    # Generate the station -  combinations
    # Breaking calculations down into "smallest" chunks
    station_ids = ids if (ids:= project_params.get("location_ids")) is not None else utils.get_station_ids(project_params)
    station_id_comb = [
        (cur_station, cur_id) for cur_station in station_ids for cur_id in gms_ids
    ]

    results_dir = project_dir / "results"
    if n_procs == 1:
        for cur_station, cur_id in station_id_comb:
            process_station_gms_config_comb(
                ensemble,
                cur_station,
                cur_id,
                gc.im.IM.from_str(gms_params[cur_id]["IMj"]),
                _get_gms_ims(
                    gms_params[cur_id]["IMj"], gms_params[cur_id]["IMs"], ensemble
                ),
                gms_params[cur_id]["n_gms"],
                results_dir / cur_station,
                gms_params[cur_id]["dataset_id"],
                im_j=gms_params[cur_id].get("im_j"),
                exceedance=gms_params[cur_id].get("exceedance"),
                n_replica=gms_params[cur_id].get("n_replica"),
                sf_bounds=gms_params[cur_id].get("sf_bounds"),
            )
    else:
        with mp.Pool(processes=n_procs) as p:
            p.starmap(
                process_station_gms_config_comb,
                [
                    (
                        ensemble,
                        cur_station,
                        cur_id,
                        gc.im.IM.from_str(gms_params[cur_id]["IMj"]),
                        _get_gms_ims(
                            gms_params[cur_id]["IMj"],
                            gms_params[cur_id]["IMs"],
                            ensemble,
                        ),
                        gms_params[cur_id]["n_gms"],
                        results_dir / cur_station,
                        gms_params[cur_id]["dataset_id"],
                        gms_params[cur_id].get("im_j"),
                        gms_params[cur_id].get("exceedance"),
                        gms_params[cur_id].get("n_replica"),
                        gms_params[cur_id].get("sf_bounds")
                    )
                    for cur_station, cur_id in station_id_comb
                ],
            )
