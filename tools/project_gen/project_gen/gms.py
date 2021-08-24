"""Script for generating the ground motion selection results"""
import multiprocessing as mp
from pathlib import Path
from typing import List

import yaml
import numpy as np

import seistech_calc as si
from . import utils


def process_station_gms_config_comb(
    ensemble: si.gm_data.Ensemble,
    station_name: str,
    gms_id: str,
    IMj: si.im.IM,
    IMs: np.ndarray,
    n_gms: int,
    output_dir: Path,
    gm_dataset_id: str,
    im_j: float = None,
    exceedance: float = None,
):
    """Processes to a single station and GMS-config"""
    # Get the site
    site_info = si.site.get_site_from_name(ensemble, station_name)

    # Create the current output directory (if required)
    output_dir.mkdir(exist_ok=True, parents=False)

    # Retrieve the default causal filter parameters
    cs_param_bounds = si.gms.default_causal_params(
        ensemble, site_info, IMj, exceedance=exceedance, im_value=im_j
    )

    # Get the GM dataset
    gm_dataset = si.gms.GMDataset.get_GMDataset(gm_dataset_id)

    # Can only use IMs that are supported by the GM dataset
    IMs = IMs[np.isin(IMs, gm_dataset.ims)]

    # Run the GM selection
    gms_result = si.gms.run_ensemble_gms(
        ensemble,
        site_info,
        n_gms,
        IMj,
        gm_dataset,
        IMs,
        cs_param_bounds=cs_param_bounds,
        im_j=im_j,
        exceedance=exceedance,
    )

    # Save
    save_dir = gms_result.save(output_dir, gms_id)


def _get_gms_ims(IMj: str, im_strings: List[str], ensemble: si.gm_data.Ensemble):
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
    IMj = si.im.IM.from_str(IMj)
    ims = []
    for im_string in im_strings:
        if im_string == "pSA":
            ims.extend(
                [
                    si.im.IM(si.im.IMType.pSA, period=cur_im.period)
                    for cur_im in ensemble.ims
                    if cur_im.period != IMj.period and cur_im.is_pSA() and cur_im.component is si.im.IMComponent.RotD50
                ]
            )
        else:
            im = si.im.IM.from_str(im_string)
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
    gms_params = project_params["gms"]
    gms_ids = list(gms_params.keys())

    # Load the ensemble
    ensemble_ffp = project_dict["ensemble_ffp"]
    ensemble = si.gm_data.Ensemble(
        project_name, config_ffp=ensemble_ffp, use_im_data_cache=True
    )

    # Generate the station -  combinations
    # Breaking calculations down into "smallest" chunks
    station_ids = utils.get_station_ids(project_params)
    station_id_comb = [
        (cur_station, cur_id) for cur_station in station_ids for cur_id in gms_ids
    ]

    results_dir = project_dir / "results"
    with mp.Pool(processes=n_procs) as p:
        p.starmap(
            process_station_gms_config_comb,
            [
                (
                    ensemble,
                    cur_station,
                    cur_id,
                    si.im.IM.from_str(gms_params[cur_id]["IMj"]),
                    _get_gms_ims(gms_params[cur_id]["IMj"], gms_params[cur_id]["IMs"], ensemble),
                    gms_params[cur_id]["n_gms"],
                    results_dir / cur_station,
                    gms_params[cur_id]["dataset_id"],
                    gms_params[cur_id].get("im_j"),
                    gms_params[cur_id].get("exceedance"),
                )
                for cur_station, cur_id in station_id_comb
            ],
        )
