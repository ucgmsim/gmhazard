import os
import json
import multiprocessing as mp

import pandas as pd
import numpy as np

import seistech_utils as su
import seistech_calc as si


def gen_event_data(
    im: str,
    rupture: str,
    imdb_ffp: str,
    station_df: pd.DataFrame,
    output_dir: str,
    n_procs: int = 4,
    lat_max_filter: float = None,
):
    """Generates median and std output for the specified rupture and IMDB"""
    # Get the stations
    if lat_max_filter is not None:
        station_df = station_df.loc[station_df.lat <= lat_max_filter]

    # Get the median values
    with mp.Pool(n_procs) as p:
        results = p.starmap(
            _get_median_value,
            [
                (imdb_ffp, cur_station, im, rupture)
                for cur_station in station_df.index.values
            ],
        )

    assert len(results) == station_df.shape[0]
    result_df = pd.DataFrame.from_dict(
        {
            cur_station: {"median": median, "std": std}
            for cur_station, (median, std) in zip(station_df.index.values, results)
        },
        orient="index",
    )

    # Drop entries with median & std equal to zero
    result_df = result_df.loc[
        (result_df["median"].values != 0) & (result_df["std"].values != 0)
    ]

    id = os.path.basename(imdb_ffp).split(".")[0].replace("_", "")
    base_out_fname = f"{id}_{rupture}_{im.replace('.', 'p')}"

    # Write the dataframe
    result_df = result_df.join(station_df)
    result_df.to_csv(
        os.path.join(output_dir, f"{base_out_fname}_df.csv"), index_label="station_name"
    )

    # Write the data for plotting purposes
    median_map_data_ffp = os.path.join(output_dir, f"{base_out_fname}_median.csv")
    with open(su.utils.change_file_ext(median_map_data_ffp, "json"), "w") as f:
        json.dump(
            {"id": f"{id}", "im": im, "plot_title": f"{rupture} - {im} - Median"}, f
        )

    result_df.to_csv(
        median_map_data_ffp,
        index=True,
        columns=["lon", "lat", "median"],
        header=["lon", "lat", "value"],
        index_label="station_name",
    )

    std_map_data_ffp = os.path.join(output_dir, f"{base_out_fname}_std.csv")
    with open(su.utils.change_file_ext(std_map_data_ffp, "json"), "w") as f:
        json.dump({"id": f"{id}", "im": im, "plot_title": f"{rupture} - Std"}, f)

    result_df.to_csv(
        std_map_data_ffp,
        index=True,
        columns=["lon", "lat", "std"],
        header=["lon", "lat", "value"],
        index_label="station_name",
    )


def gen_event_ratio_data(
    im: str,
    rupture: str,
    imdb_1_ffp: str,
    imdb_2_ffp: str,
    output_dir: str,
    station_list_ffp: str,
    n_procs: int = 4,
    verbose: bool = False,
    lat_max_filter: float = None,
):
    """Computes the median and std ratio for the given rupture and pair of imdbs

    Saves the result as csv file along with metadata json file
    """
    stations = pd.DataFrame.from_records(
        np.loadtxt(station_list_ffp, dtype=[("lon", "f"), ("lat", "f"), ("name", "U7")])
    ).set_index("name")

    if lat_max_filter is not None:
        stations = stations.loc[stations.lat <= lat_max_filter]

    # Get the median values
    with mp.Pool(n_procs) as p:
        results = p.starmap(
            _process_station,
            [
                (imdb_1_ffp, imdb_2_ffp, im, station, rupture, ix if verbose else None)
                for ix, station in enumerate(stations.index.values)
            ],
        )

    result_df = pd.DataFrame.from_dict(
        {
            station: {
                "median_1": median_1,
                "std_1": std_1,
                "median_2": median_2,
                "std_2": std_2,
            }
            for station, median_1, median_2, std_1, std_2 in results
        },
        orient="index",
    )
    pd.set_option("use_inf_as_na", True)
    result_df["median_ratio"] = np.log(result_df.median_1 / result_df.median_2)
    result_df["std_ratio"] = np.log(result_df.std_1 / result_df.std_2)
    result_df.dropna(inplace=True)

    id_1 = os.path.basename(imdb_1_ffp).split(".")[0].replace("_", "")
    id_2 = os.path.basename(imdb_2_ffp).split(".")[0].replace("_", "")

    base_out_fname = f"{id_1}_vs_{id_2}_{rupture}_{im.replace('.', 'p')}"

    # Write the dataframe
    result_df = result_df.join(stations)
    result_df.to_csv(
        os.path.join(output_dir, f"{base_out_fname}_df.csv"), index_label="station_name"
    )

    # Write the differences data for plotting purposes
    median_map_data_ffp = os.path.join(output_dir, f"{base_out_fname}_median.csv")
    with open(su.utils.change_file_ext(median_map_data_ffp, "json"), "w") as f:
        json.dump(
            {
                "ensemble_id": f"{id_1}/{id_2}",
                "im": im,
                "plot_title": f"{rupture} - {im} - Median ratio",
            },
            f,
        )

    result_df.to_csv(
        median_map_data_ffp,
        index=True,
        columns=["lon", "lat", "median_ratio"],
        header=["lon", "lat", "value"],
        index_label="station_name",
    )

    std_map_data_ffp = os.path.join(output_dir, f"{base_out_fname}_std.csv")
    with open(su.utils.change_file_ext(std_map_data_ffp, "json"), "w") as f:
        json.dump(
            {
                "ensemble_id": f"{id_1}/{id_2}",
                "im": im,
                "plot_title": f"{rupture} - Std ratio",
            },
            f,
        )

    result_df.to_csv(
        std_map_data_ffp,
        index=True,
        columns=["lon", "lat", "std_ratio"],
        header=["lon", "lat", "value"],
        index_label="station_name",
    )


def _get_median_value(imdb_ffp: str, station: str, im: str, rupture: str):
    """Gets the median and std for the given
    imdb, station, IM and rupture combination"""
    with si.dbs.IMDB.get_imdb(imdb_ffp) as db:
        if isinstance(db, si.dbs.IMDBNonParametric):
            im_values = db.im_data(station, im)
            if im_values is not None and rupture in np.unique(
                im_values.index.get_level_values(0)
            ).astype(str):
                median = np.median(im_values.loc[rupture].values)
                sigma = np.std(im_values.loc[rupture].values)
            else:
                median, sigma = 0, 0
            return median, sigma
        elif isinstance(db, si.dbs.IMDBParametric):
            im_params = db.im_data(station, im)
            if im_params is not None and rupture in im_params.index.values:
                mu, sigma = (
                    im_params.loc[rupture, "mu"],
                    im_params.loc[rupture, "sigma"],
                )

                median = np.exp(mu)
                std = np.sqrt(np.exp(sigma ** 2 - 1) * np.exp(2 * mu + sigma ** 2))
            else:
                median, std = 0, 0
            return median, std

    raise NotImplementedError


def _process_station(
    imdb_1_ffp: str,
    imdb_2_ffp: str,
    im: str,
    station: str,
    rupture: str,
    station_ix: int = None,
):
    """Gets the median & std for the given station for both imdbs"""
    median_1, std_1 = _get_median_value(imdb_1_ffp, station, im, rupture)
    median_2, std_2 = _get_median_value(imdb_2_ffp, station, im, rupture)

    if station_ix is not None:
        print(f"Completed - {station}, index {station_ix}")
    return station, median_1, median_2, std_1, std_2
