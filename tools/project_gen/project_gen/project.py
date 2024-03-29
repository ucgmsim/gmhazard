import shutil
import subprocess
import traceback
import os
from typing import Dict, List, Union, Sequence
from pathlib import Path

import git
import pandas as pd
import numpy as np
import yaml

import gmhazard_utils as su
import gmhazard_calc as gc

from . import utils
from . import psha
from . import gms

EMPIRICAL_VERSION = "v22p5emp"
FLT_SITE_SOURCE_DB_FILENAME = "flt_site_source.db"
DS_SITE_SOURCE_DB_FILENAME = "ds_site_source.db"

ERF_DIR = Path(os.getenv("ERF_DIR")) if "ERF_DIR" in os.environ else None

FLT_ERF_MAPPING = {
    "NHM_v21p8p1": "NZ_FLTmodel_2010",
    "CFM_v21p8p1": "CFM_v0_9_Akatore_mod_21p8p1",
}

SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent / "gmhazard_scripts"
MODEL_CONFIG_PATH = (
    SCRIPTS_DIR
    / "db_creation"
    / "empirical_db"
    / "empirical_model_configs"
    / "22p5.yaml"
)
EMPIRICAL_WEIGHT_CONFIG_PATH = (
    SCRIPTS_DIR / "ensemble_creation" / "gmm_weights_22p5.yaml"
)


def create_project(
    project_specs: Dict,
    projects_base_dir: Union[Path, str],
    scripts_dir: Union[Path, str],
    n_procs: int = 6,
    new_project: bool = True,
    use_mp: bool = True,
    erf_dir: Path = None,
    erf_pert_dir: Path = None,
    flt_erf_version: str = "NHM",
    setup_only: bool = False,
    model_config_ffp: Path = MODEL_CONFIG_PATH,
    empirical_weight_config_ffp: Path = EMPIRICAL_WEIGHT_CONFIG_PATH,
    ensemble_ffp: Path = None,
    no_gms: bool = False,
):
    """
    Creates a new project, generates the required DBs,
    and computes the hazard analysis results

    This function uses multiprocessing to for the
    result generation

    Parameters
    ----------
    project_specs: dictionary
        The project specifications
    projects_base_dir: Path or string
        The base directory of the projects, above the
        version directories
    scripts_dir: Path or string
        The path to the directory that contains the
        subdirectories for DB and Ensemble generation scripts
    n_procs: int
        Number of processes to use
    new_project: bool
        If True then a completely new project is setup,
        If False then only the results are computed (the results
            directory has to be empty though)
    erf_dir: Path, optional
        Path to the ERF base directory, expected to contain
         - NZBCK2015_Chch50yearsAftershock_OpenSHA_modType4.txt
         - NZ_DSmodel_2015.txt
         - NZ_FLTmodel_2010.txt
    erf_pert_dir: Path, optional
        Directory of the fault perturbed ERF files
        Ignored unless n_perturbations > 1 (in project_specs)
    use_mp: bool, optional
        If true then standard python multiprocessing will be
        used for PSHA result generation, otherwise celery
        will be used.
    setup_only: bool, optional
        If true, then only the config and DBs are generated, but
        no results are computed
    model_config_ffp: path, optional
        Path to the model config file.
    empirical_weight_config_ffp: path, optional
        Path to the weights config file.
        model_config_ffp and weights_config_ffp
        can be specified in certain cases(E.g., test case)
    ensemble_ffp: path, optional
        If given, then this ensemble is used for
        the project. The ensemble has to support
        the sites of interest

        If this option is set, then the following
        parameters are ignored:
            - erf_dir
            - erf_pert_dir
            - model_config_ffp and
            - empirical_weight_config_ffp
    """
    erf_dir = ERF_DIR if erf_dir is None else erf_dir

    try:
        projects_base_dir, scripts_dir = (Path(projects_base_dir), Path(scripts_dir))
        project_id = project_specs["id"]

        n_perturbations = project_specs.get("n_perturbations", 1)

        _, version_str = su.utils.get_package_version("project_api")
        project_dir = projects_base_dir / version_str / project_id

        if new_project:
            # Setup the project structure
            setup_project(projects_base_dir, project_id, ensemble_ffp=ensemble_ffp)

            if "im_components" not in project_specs:
                project_specs["im_components"] = ["RotD50"]

            # Write the config
            project_config = write_project_config(project_dir, project_specs)

            # Get the site info

            if ensemble_ffp is None:
                dbs_dir = project_dir / "dbs"

                # Write the station location and vs30 file
                site_infos = utils.get_site_infos(project_config)
                ll_ffp, vs30_ffp, z_ffp = write_station_details(
                    site_infos, dbs_dir, project_id
                )

                # Generate the DBs
                generate_dbs(
                    dbs_dir,
                    ll_ffp,
                    vs30_ffp,
                    model_config_ffp,
                    scripts_dir,
                    erf_dir,
                    erf_pert_dir,
                    flt_erf_version,
                    list(
                        {
                            str(im.im_type)
                            for im in gc.im.to_im_list(project_config["ims"])
                        }
                    ),
                    n_procs=n_procs,
                    z_ffp=z_ffp,
                    n_perturbations=n_perturbations,
                )

                # Create the ensemble config file
                create_ensemble_config(
                    EMPIRICAL_VERSION,
                    project_dir,
                    project_id,
                    dbs_dir,
                    erf_dir,
                    erf_pert_dir,
                    flt_erf_version,
                    n_perturbations=n_perturbations,
                    empirical_weight_config_ffp=empirical_weight_config_ffp,
                )
            else:
                print(
                    f"An existing ensemble has been specified, "
                    f"no dbs will be generated."
                )

                ens = gc.gm_data.Ensemble(project_id, str(ensemble_ffp))

                # Check that the specified location ids exist
                if (
                    project_loc_ids := project_config.get("location_ids")
                ) is None or np.any(
                    ~np.isin(project_loc_ids, ens.stations.index.values.astype(str))
                ):
                    raise ValueError(
                        "Either no location ids are specified, or one of the "
                        "specified locations is not supported by the ensemble"
                    )

                # Check that the specified IMs are supported
                project_ims = np.asarray(project_config["ims"])
                if not np.all(
                    im_mask := np.isin(project_ims, gc.im.to_string_list(ens.ims))
                ):
                    raise ValueError(
                        f"The ims {project_ims[~im_mask]} are not "
                        f"supported by the ensemble"
                    )

        if setup_only:
            return

        # Generate the PSHA project data and GMS
        psha.gen_psha_project_data(project_dir, n_procs=n_procs, use_mp=use_mp)

        if not no_gms:
            gms.gen_gms_project_data(project_dir, n_procs=n_procs)
    except NotImplementedError as ex:
        print(f"Failed to create new project, due to an exception:\n{ex}")
        print(f"Traceback:\n{traceback.format_exc()}")

        # TODO: Add slack integration here??
        return

    return


def setup_project(base_dir: Path, project_id: str, ensemble_ffp: Path = None):
    """Sets up the required directories and files for a project"""
    # Get the current projectAPI version
    _, version_str = su.utils.get_package_version("project_api")

    # Create the version folder
    (base_dir / version_str).mkdir(exist_ok=True, parents=False)

    # Create the project folder
    project_dir = base_dir / version_str / project_id
    if project_dir.exists():
        print("Project dir already exists, skipping setup")
        return
    project_dir.mkdir(exist_ok=False, parents=False)

    # Copy the specified ensemble into the project directory
    if ensemble_ffp is not None:
        ensemble_ffp = shutil.copy(ensemble_ffp, project_dir)

    try:
        commit_hash = git.Repo(search_parent_directories=True).head.object.hexsha
    except git.exc.InvalidGitRepositoryError as ex:
        commit_hash = ""

    # Create empty project definition file
    project_def = {
        "ensemble_ffp": str(ensemble_ffp) if ensemble_ffp is not None else None,
        "commit_hash": commit_hash,
        "project_parameters": None,
    }
    with open(project_dir / f"{project_id}.yaml", "w") as f:
        yaml.safe_dump(project_def, f)

    # Create the database folder
    if ensemble_ffp is None:
        (project_dir / "dbs").mkdir()

    # Create the results folder
    (project_dir / "results").mkdir()

    return project_dir


def write_project_config(project_dir: Path, project_specs: Dict):
    """Writes the project config"""
    project_config_ffp = project_dir / f"{project_specs['id']}.yaml"
    with open(project_config_ffp, "r") as f:
        project_config = yaml.safe_load(f)

        if project_specs.get("project_parameters") is not None:
            print("Project parameters are already set, skipping package type mapping")
            project_config["project_parameters"] = project_specs["project_parameters"]
        else:
            project_config["project_parameters"] = {
                "locations": {
                    cur_id: {
                        "names": cur_config["names"],
                        "lat": cur_config["lat"],
                        "lon": cur_config["lon"],
                        "vs30": cur_config["vs30"],
                        "z1.0": cur_config.get(
                            "z1p0", [None] * len(cur_config["vs30"])
                        ),
                        "z2.5": cur_config.get(
                            "z2p5", [None] * len(cur_config["vs30"])
                        ),
                    }
                    for cur_id, cur_config in project_specs["locations"].items()
                }
            }

            # Get & apply the package mapping
            with open(Path(__file__).parent / "package_mapping.yaml", "r") as f:
                package_mapping = yaml.safe_load(f)

            project_config["project_parameters"] = {
                **project_config["project_parameters"],
                **package_mapping[project_specs["package_type"]],
                "im_components": project_specs["im_components"],
            }

    with open(project_dir / f"{project_specs['id']}.yaml", "w") as f:
        yaml.safe_dump(project_config, f)

    return project_config["project_parameters"]


def write_station_details(
    site_infos: Sequence[gc.site.SiteInfo], dbs_dir: Path, project_id: str
):
    """Writes the station location, vs30 and Z file"""
    ll_ffp = dbs_dir / f"{project_id}.ll"
    if not ll_ffp.exists():
        lines = [
            f"{cur_site.lon} {cur_site.lat} {cur_site.station_name}\n"
            for cur_site in site_infos
        ]
        with ll_ffp.open("w") as f:
            f.writelines(lines)

    vs30_ffp = dbs_dir / f"{project_id}.vs30"
    if not vs30_ffp.exists():
        lines = [
            f"{cur_site.station_name} {cur_site.db_vs30}\n" for cur_site in site_infos
        ]
        with vs30_ffp.open("w") as f:
            f.writelines(lines)

    z_ffp = dbs_dir / f"{project_id}.z"
    if not z_ffp.exists():
        header = "Station_Name,Z_1.0(km),Z_2.5(km),sigma\n"
        lines = [
            f"{cur_site.station_name},{cur_site.z1p0},{cur_site.z2p5},0\n"
            for cur_site in site_infos
        ]
        with z_ffp.open("w") as f:
            f.write(header)
            f.writelines(lines)

    return ll_ffp, vs30_ffp, z_ffp


def generate_dbs(
    dbs_dir: Path,
    ll_ffp: Path,
    vs30_ffp: Path,
    model_config_ffp: Path,
    scripts_dir: Path,
    erf_dir: Path,
    erf_pert_dir: Path,
    flt_erf_version: str,
    im_types: Sequence[str],
    n_procs: int,
    z_ffp: Path = None,
    n_perturbations: int = 1,
):
    """Generates the distance DBs and empirical fault and
    distributed seismicity IMDBs"""
    n_stations = pd.read_csv(ll_ffp, header=None, sep="\s+").shape[0]

    print("Generating DS distance db")
    ds_site_source_db_ffp = dbs_dir / DS_SITE_SOURCE_DB_FILENAME
    empirical_db_scripts_dir = scripts_dir / "db_creation" / "empirical_db"
    if ds_site_source_db_ffp.exists():
        print("DS distance DB already exists, skipping")
    else:
        calc_ds_distances_cmd = [
            "python",
            str(empirical_db_scripts_dir / "calc_distances_ds.py"),
            str(erf_dir / "NZBCK2015_Chch50yearsAftershock_OpenSHA_modType4.txt"),
            str(ll_ffp),
            str(ds_site_source_db_ffp),
        ]
        print(f"Running command:\n\t{' '.join(calc_ds_distances_cmd)}")
        ds_distance_result = subprocess.run(calc_ds_distances_cmd, capture_output=True)
        print("STDOUT:\n" + ds_distance_result.stdout.decode())
        print("STDERR:\n" + ds_distance_result.stderr.decode() + "\n")
        assert (
            ds_distance_result.returncode == 0
        ), "Distributed Seismicity site-source DB generation failed"

    print("Generating DS IMDBs")
    ds_db_dir = dbs_dir / "ds"
    if ds_db_dir.exists():
        print("DS IMDB folder already exists, skipping")
    else:
        ds_db_dir.mkdir(exist_ok=True)

        # Temporary case with AI
        AI_to_gen = "AI" in im_types
        if AI_to_gen:
            ds_imdbs_cmd = [
                "mpirun",
                "--use-hwthread-cpus",
                "python",
                str(empirical_db_scripts_dir / "calc_emp_ds.py"),
                str(erf_dir / "NZBCK2015_Chch50yearsAftershock_OpenSHA_modType4.txt"),
                str(ds_site_source_db_ffp),
                str(vs30_ffp),
                str(ds_db_dir),
                "--model-dict",
                str(model_config_ffp),
                "--z-file",
                str(z_ffp),
                "--im",
                "AI",
            ]
            ds_timeout = (n_stations * (60 * 60 * 5)) / (min(n_procs - 1, n_stations))
            print(f"Using a timeout of {ds_timeout} seconds")
            print(f"Running command for AI:\n\t{' '.join(ds_imdbs_cmd)}")
            ds_imdbs_result = subprocess.run(
                ds_imdbs_cmd, capture_output=True, timeout=ds_timeout
            )
            print("STDOUT:\n" + ds_imdbs_result.stdout.decode())
            print("STDERR:\n" + ds_imdbs_result.stderr.decode())
            assert (
                ds_imdbs_result.returncode == 0
            ), "Distributed Seismicity IMDB generation failed"

            im_types.remove("AI")

        ds_imdbs_cmd = [
            "python",
            str(empirical_db_scripts_dir / "new_calc_emp_ds.py"),
            str(erf_dir / "NZBCK2015_Chch50yearsAftershock_OpenSHA_modType4.txt"),
            str(ds_site_source_db_ffp),
            str(vs30_ffp),
            str(ds_db_dir),
            "--model-dict",
            str(model_config_ffp),
            "--z-file",
            str(z_ffp),
            "--im",
            *im_types,
        ]
        ds_timeout = (n_stations * (60 * 60 * 5)) / (min(n_procs - 1, n_stations))
        print(f"Using a timeout of {ds_timeout} seconds")
        print(f"Running command:\n\t{' '.join(ds_imdbs_cmd)}")
        ds_imdbs_result = subprocess.run(
            ds_imdbs_cmd, capture_output=True, timeout=ds_timeout
        )
        print("STDOUT:\n" + ds_imdbs_result.stdout.decode())
        print("STDERR:\n" + ds_imdbs_result.stderr.decode())
        assert (
            ds_imdbs_result.returncode == 0
        ), "Distributed Seismicity IMDB generation failed"

    # We had to temporarily remove, so it works with OQ wrapper which does not support AI
    if AI_to_gen:
        im_types.append("AI")

    flt_erf_base_fn = FLT_ERF_MAPPING[flt_erf_version]

    print("Generating fault distance db")
    flt_site_source_db_ffp = dbs_dir / FLT_SITE_SOURCE_DB_FILENAME
    if flt_site_source_db_ffp.exists():
        print("Fault distance DB already exists, skipping")
    else:
        calc_fault_distances_cmd = [
            "python",
            str(empirical_db_scripts_dir / "calc_distances_flt.py"),
            str(flt_site_source_db_ffp),
            "--nhm_file",
            str(erf_dir / f"{flt_erf_base_fn}.txt"),
            str(ll_ffp),
        ]
        print(f"Running command:\n\t{' '.join(calc_fault_distances_cmd)}")
        flt_distance_result = subprocess.run(
            calc_fault_distances_cmd, capture_output=True
        )
        print("STDOUT:\n" + flt_distance_result.stdout.decode())
        print("STDERR:\n" + flt_distance_result.stderr.decode())
        assert (
            flt_distance_result.returncode == 0
        ), "Fault site-source DB generation failed"

    if n_perturbations > 1:
        if erf_pert_dir is None or not (erf_pert_dir).exists():
            raise Exception(
                f"A valid directory with the perturbed ERF files has to be specified."
            )

    print("Generating fault IMDBs")
    flt_db_dir = dbs_dir / "flt"
    if flt_db_dir.exists():
        print("Fault IMDB folder already exists, skipping")
    else:
        flt_db_dir.mkdir(exist_ok=True)
        for i in range(n_perturbations):
            if n_perturbations > 1:
                erf_file = str(erf_pert_dir / f"{flt_erf_base_fn}_pert{i:02}.txt")
            else:
                erf_file = str(erf_dir / f"{flt_erf_base_fn}.txt")
            flt_imdbs_cmd = [
                "python",
                str(empirical_db_scripts_dir / "calc_emp_flt.py"),
                erf_file,
                str(flt_site_source_db_ffp),
                str(vs30_ffp),
                str(flt_db_dir),
                "--model-dict",
                str(model_config_ffp),
                "--z-file",
                str(z_ffp),
                "--im",
                *im_types,
            ]
            if n_perturbations > 1:
                flt_imdbs_cmd.extend(["-s", f"pert_{i:02}"])
            print(
                f"Running command, {i + 1}/{n_perturbations}:\n\t{' '.join(flt_imdbs_cmd)}"
            )
            flt_imdbs_result = subprocess.run(flt_imdbs_cmd, capture_output=True)
            print("STDOUT:\n" + flt_imdbs_result.stdout.decode())
            print("STDERR:\n" + flt_imdbs_result.stderr.decode())
            assert flt_imdbs_result.returncode == 0, "Fault IMDB generation failed"


def create_ensemble_config(
    empirical_version: str,
    project_dir: Path,
    project_id: str,
    dbs_dir: Path,
    erf_dir: Path,
    erf_pert_dir: Path,
    flt_erf_version: str,
    n_perturbations: int = 1,
    empirical_weight_config_ffp: Path = EMPIRICAL_WEIGHT_CONFIG_PATH,
):
    """Creates the ensemble config for the project"""
    ens_filename = f"{empirical_version}_{project_id}"
    ens_ffp = project_dir / f"{ens_filename}.yaml"

    flt_erf_base_fn = FLT_ERF_MAPPING[flt_erf_version]

    if n_perturbations > 1:
        erf_ffps = [
            str(erf_ffp)
            for erf_ffp in sorted(erf_pert_dir.glob(f"{flt_erf_base_fn}_pert*.txt"))
        ]
    else:
        erf_ffps = [str(erf_dir / f"{flt_erf_base_fn}.txt")]

    su.ensemble_creation.create_ensemble(
        ens_filename,
        str(project_dir),
        str(empirical_weight_config_ffp),
        str(dbs_dir / DS_SITE_SOURCE_DB_FILENAME),
        str(dbs_dir / FLT_SITE_SOURCE_DB_FILENAME),
        str(dbs_dir / f"{project_id}.ll"),
        str(dbs_dir / f"{project_id}.vs30"),
        erf_ffps,
        str(erf_dir / "NZ_DSmodel_2015.txt"),
        [str(db) for db in dbs_dir.glob("*/*.db")],
        n_perts=n_perturbations,
    )

    # Update the ensemble config path in the project config
    project_config_ffp = project_dir / f"{project_id}.yaml"
    with open(project_config_ffp, "r") as f:
        project_config = yaml.safe_load(f)

    project_config["ensemble_ffp"] = str(ens_ffp)

    with open(project_config_ffp, "w") as f:
        yaml.dump(project_config, f)

    return ens_ffp
