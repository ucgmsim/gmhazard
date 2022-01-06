from pathlib import Path
from typing import Dict, Sequence, Any

import yaml
import pandas as pd

from visualization.plot_items_wrapper import plot_multiple

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


def plot_realisations(
    rel_df: pd.DataFrame,
    station_df: pd.DataFrame,
    output_dir: Path,
    out_name_prefix: str,
    label: str = "",
    n_procs: int = 4,
    cpt_max: float = 0.125,
):
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
            options={**{"title": cur_out_name, "xyz-cpt-labels": label,},}
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