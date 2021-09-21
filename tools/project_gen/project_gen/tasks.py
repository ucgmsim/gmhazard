from pathlib import Path
from typing import Dict, Sequence

import seistech_calc as sc
from . import project
from . import psha
from .celery import app


@app.task(name="Create project", queue="project_gen")
def create_project_task(
    project_params: Dict,
    projects_base_dir: str,
    scripts_dir: str,
    n_procs: int = 6,
    new_project: bool = True,
):
    """See create_project function in projects.py for docstring"""
    project.create_project(
        project_params,
        projects_base_dir,
        scripts_dir,
        n_procs=n_procs,
        new_project=new_project,
        use_mp=False,
    )
    pass


@app.task(name="Generate maps", queue="project_gen")
def generate_maps_task(
    ensemble_id: str, ensemble_ffp: str, station_name: str, results_dir: str
):
    ensemble = sc.gm_data.Ensemble(ensemble_id, config_ffp=ensemble_ffp)
    psha.generate_maps(ensemble, station_name, results_dir)


@app.task(name="Process station im", queue="project_gen")
def process_station_im_task(
    ensemble_id: str,
    ensemble_ffp: str,
    station_name: str,
    im: sc.im.IM,
    disagg_exceedances: Sequence[float],
    output_dir: str,
):
    ensemble = sc.gm_data.Ensemble(ensemble_id, config_ffp=ensemble_ffp)
    psha.process_station_im(ensemble, station_name, im, disagg_exceedances, output_dir)


@app.task(name="Process station component", queue="project_gen")
def process_station_component_task(
    ensemble: sc.gm_data.Ensemble,
    station_name: str,
    im_component: sc.im.IMComponent,
    output_dir: Path,
):
    psha.process_station_scenarios(ensemble, station_name, im_component, output_dir)
