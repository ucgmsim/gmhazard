from pathlib import Path
from typing import Dict, Sequence, Any, Tuple

import pygmt
import yaml
import numpy as np
import pandas as pd

from pygmt_helper import plotting
from qcore import geo

TEMPLATE_OPTIONS_DICT = {"flags": [], "options": {}}

DEFAULT_STANDARD_GMT_PLOT_OPTIONS = {
    "flags": ["xyz-grid", "xyz-landmask", "xyz-grid-contours", "xyz-cpt-invert"],
    "options": {
        "xyz-grid-search": "12m",
        "xyz-grid-automask": "12k",
        "xyz-cpt": "hot",
        "xyz-transparency": "30",
        "xyz-size": "1k",
        "xyz-cpt-min": "0",
        "xyz-cpt-max": "0.125",
    },
}


def _get_region(
    hypocentre_loc: Tuple[float, float],
    hypocentre_dist: Tuple[float, float],
):
    min_lon = geo.ll_shift(
        hypocentre_loc[1], hypocentre_loc[0], hypocentre_dist[0], 270
    )[1]
    max_lon = geo.ll_shift(
        hypocentre_loc[1], hypocentre_loc[0], hypocentre_dist[0], 90
    )[1]
    min_lat = geo.ll_shift(
        hypocentre_loc[1], hypocentre_loc[0], hypocentre_dist[1], 180
    )[0]
    max_lat = geo.ll_shift(hypocentre_loc[1], hypocentre_loc[0], hypocentre_dist[1], 0)[
        0
    ]

    return (min_lon, max_lon, min_lat, max_lat)


def _plot_stations(fig: pygmt.Figure, data_df: pd.DataFrame):
    for cur_station, cur_row in data_df.iterrows():
        # Plot observation stations
        if "observation" in cur_row.index and cur_row.observation:
            fig.plot(
                x=cur_row.lon,
                y=cur_row.lat,
                style="d0.05c",
                fill="green",
                pen="green",
            )
        # Plot sites of interest
        else:
            fig.plot(
                x=cur_row.lon,
                y=cur_row.lat,
                style="x0.02c",
                fill="black",
                pen="black",
            )


def gen_spatial_plot(
    data_df: pd.DataFrame,
    data_key: str,
    hypocentre_loc: Tuple[float, float],
    hypocentre_dist: Tuple[float, float],
    output_ffp: Path,
    title: str = None,
    map_data_ffp: Path = None,
    map_data: plotting.NZMapData = None,
    plot_stations: bool = True,
    cb_max: float = None
):
    # Load the map data
    if map_data is None and map_data_ffp is not None:
        map_data = plotting.NZMapData.load(map_data_ffp, high_res_topo=False)

    # Use max value from data if not specified
    cb_max = cb_max if cb_max is not None else np.around(data_df[data_key].max(), 1)

    # Create the figure
    region = _get_region(hypocentre_loc, hypocentre_dist)
    fig = plotting.gen_region_fig(title, region, map_data=map_data)

    # Create & Plot the grid
    grid = plotting.create_grid(
        data_df, data_key=data_key, region=region, grid_spacing="50e/50e"
    )
    plotting.plot_grid(
        fig,
        grid,
        "hot",
        (0, cb_max, cb_max / 20),
        ("white", "black"),
        reverse_cmap=True,
        transparency=35,
    )

    # Plot stations
    if plot_stations:
        _plot_stations(fig, data_df)

    # Plot the hypocentre
    fig.plot(
        x=hypocentre_loc[0],
        y=hypocentre_loc[1],
        style="a0.1c",
        fill="pink",
        pen="pink",
    )

    fig.savefig(
        output_ffp,
        dpi=900,
        anti_alias=True,
    )


def plot_realisations(
    rel_df: pd.DataFrame,
    station_df: pd.DataFrame,
    output_dir: Path,
    out_name_prefix: str,
    label: str = "",
    n_procs: int = 4,
    cpt_max: float = 0.125,
):
    """
    Plots realisations and stations on a map
    using a plot items wrapper from the visualisation package
    """
    from visualization.plot_items_wrapper import plot_multiple

    data_df = pd.merge(rel_df, station_df, left_index=True, right_index=True)

    csv_files = []
    for rel_ix, cur_col in enumerate(rel_df.columns):
        cur_out_name = f"{out_name_prefix}_{rel_ix}"

        cur_df = data_df.loc[:, ["lon", "lat", cur_col]]
        cur_df.rename(columns={cur_col: "value"}, inplace=True)

        cur_csv_ffp = output_dir / f"{cur_out_name}.csv"
        cur_df.to_csv(cur_csv_ffp, index=False)
        csv_files.append(str(cur_csv_ffp))

        gmt_options = get_gmt_options_dict(
            options={
                **{
                    "title": cur_out_name,
                    "xyz-cpt-labels": label,
                },
            }
        )
        with open(output_dir / f"{cur_out_name}.yaml", "w") as f:
            yaml.safe_dump(gmt_options, f)

    PLOT_OPTIONS = DEFAULT_STANDARD_GMT_PLOT_OPTIONS.copy()
    PLOT_OPTIONS["options"]["xyz-cpt-max"] = cpt_max

    plot_multiple(
        "plot_items.py",
        PLOT_OPTIONS,
        in_ffps=csv_files,
        n_procs=n_procs,
    )


def get_gmt_options_dict(flags: Sequence[str] = None, options: Dict[str, Any] = None):
    """Generates the GMT plot options dict"""
    cur_dict = TEMPLATE_OPTIONS_DICT.copy()

    if flags is not None:
        cur_dict["flags"] = flags

    if options is not None:
        cur_dict["options"] = options

    return cur_dict
