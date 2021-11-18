import base64
import tempfile
from pathlib import Path
from typing import Tuple, Union

import flask
import pandas as pd
from flask_cors import cross_origin
from flask_caching import Cache

import gmhazard_calc as sc
import gmhazard_utils as su
from core_api import server
from core_api import constants as const


class DisaggCachedData:
    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        disagg_data: sc.disagg.EnsembleDisaggResult,
        merged_df: pd.DataFrame,
        src_plot_data: bytes,
        eps_plot_data: bytes,
    ):
        self.ensemble = ensemble
        self.site_info = site_info
        self.disagg_data = disagg_data
        self.merged_df = merged_df

        self.src_plot_data = src_plot_data
        self.eps_plot_data = eps_plot_data

    def __iter__(self):
        return iter(
            (
                self.ensemble,
                self.site_info,
                self.disagg_data,
                self.merged_df,
                self.src_plot_data,
                self.eps_plot_data,
            )
        )


@server.app.route(const.ENSEMBLE_DISAGG_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_ensemble_disagg():
    """Retrieves the contribution of each rupture for the
    specified exceedance.

    Valid request has to contain the following
    URL parameters: ensemble_id, station, im, exceedance
    """
    server.app.logger.info(f"Received request at {const.ENSEMBLE_DISAGG_ENDPOINT}")
    cache = server.cache

    (
        (ensemble_id, station, im, exceedance,),
        optional_params_dict,
    ) = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "im", "exceedance"),
        (("gmt_plot", bool, False), ("vs30", float), ("im_component", str, "RotD50"),),
    )

    gmt_plots = optional_params_dict["gmt_plot"]
    user_vs30 = optional_params_dict.get("vs30")
    im = sc.im.IM.from_str(im, im_component=optional_params_dict.get("im_component"))

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im}, {im.component}, {exceedance}"
    )

    # Compute or retrieve from cache
    (
        ensemble,
        site_info,
        disagg_data,
        extra_info_df,
        src_png_data,
        eps_png_data,
    ) = _get_disagg(
        ensemble_id,
        station,
        im,
        exceedance,
        cache,
        gmt_plots=gmt_plots,
        user_vs30=user_vs30,
    )

    return flask.jsonify(
        su.api.get_ensemble_disagg(
            disagg_data,
            extra_info_df,
            base64.b64encode(src_png_data).decode()
            if src_png_data is not None
            else None,
            base64.b64encode(eps_png_data).decode()
            if eps_png_data is not None
            else None,
            su.api.get_download_token(
                {
                    "type": "ensemble_disagg",
                    "ensemble_id": ensemble_id,
                    "station": station,
                    "im": str(im),
                    "im_component": str(im.component),
                    "exceedance": exceedance,
                    "gmt_plots": gmt_plots,
                    "user_vs30": user_vs30,
                },
                server.DOWNLOAD_URL_SECRET_KEY,
            ),
        )
    )


@server.app.route(f"{const.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT}", methods=["Get"])
@su.api.endpoint_exception_handling(server.app)
def download_ens_disagg():
    """Handles downloading of disagg contribution data"""
    server.app.logger.info(
        f"Received request at {const.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT}"
    )
    cache = server.cache

    # Retrieve parameters from the token
    disagg_token, *_ = su.api.get_check_keys(flask.request.args, ("disagg_token",))
    disagg_payload = su.api.get_token_payload(
        disagg_token[0], server.DOWNLOAD_URL_SECRET_KEY
    )
    ensemble_id, station, user_vs30, im, exceedance, gmt_plots = (
        disagg_payload["ensemble_id"],
        disagg_payload["station"],
        disagg_payload["user_vs30"],
        sc.im.IM.from_str(
            disagg_payload["im"], im_component=disagg_payload["im_component"]
        ),
        disagg_payload["exceedance"],
        disagg_payload["gmt_plots"],
    )

    # Compute or retrieve from cache
    (
        ensemble,
        site_info,
        disagg_data,
        merged_df,
        src_plot_data,
        eps_plot_data,
    ) = _get_disagg(
        ensemble_id,
        station,
        im,
        exceedance,
        cache,
        gmt_plots=gmt_plots,
        user_vs30=user_vs30,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_disagg_download_zip(
            disagg_data,
            merged_df,
            tmp_dir,
            src_plot_data=src_plot_data,
            eps_plot_data=eps_plot_data,
            prefix=f"{ensemble.name}",
        )

        return flask.send_file(
            zip_ffp, as_attachment=True, attachment_filename=Path(zip_ffp).name
        )


@server.app.route(const.ENSEMBLE_FULL_DISAGG_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@server.requires_auth
@su.api.endpoint_exception_handling(server.app)
def get_full_disagg():
    """
    Valid request has to contain the following
    URL parameters: ensemble_id, station, im, exceedance
    """
    server.app.logger.info(f"Received request at {const.ENSEMBLE_FULL_DISAGG_ENDPOINT}")

    (
        (ensemble_id, station, im, exceedance,),
        optional_values_dict,
    ) = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", "im", "exceedance"),
        (
            ("mag_min", float),
            ("mag_n_bins", float),
            ("mag_bin_size", float),
            ("rrup_min", float),
            ("rrup_n_bins", float),
            ("rrup_bin_size", float),
            ("im_component", str, "RotD50"),
        ),
    )

    user_vs30 = optional_values_dict.get("vs30")
    im = sc.im.IM.from_str(im, im_component=optional_values_dict.get("im_component"))

    server.app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im}, {exceedance}, "
        f"optional parameters {optional_values_dict}"
    )

    server.app.logger.debug(f"Loading ensemble and retrieving site information")
    ensemble = sc.gm_data.Ensemble(ensemble_id)
    site = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

    server.app.logger.debug(f"Computing disagg")
    disagg_data = sc.disagg.run_ensemble_disagg(
        ensemble, site, im, exceedance=float(exceedance), calc_mean_values=True
    )

    server.app.logger.debug("Computing disagg gridding")
    disagg_grid_data = sc.disagg.run_disagg_gridding(
        disagg_data, **optional_values_dict
    )

    return flask.jsonify({"disagg_grid_data": disagg_grid_data.to_dict()})


def _get_disagg(
    ensemble_id: str,
    station: str,
    im: sc.im.IM,
    exceedance: str,
    cache: Cache,
    gmt_plots: bool = False,
    user_vs30: float = None,
) -> Tuple[
    sc.gm_data.Ensemble,
    sc.site.SiteInfo,
    sc.disagg.EnsembleDisaggResult,
    pd.DataFrame,
    Union[None, bytes],
    Union[None, bytes],
]:
    # Get the cache key
    cache_key = su.api.get_cache_key(
        "disagg",
        ensemble_id=ensemble_id,
        station=station,
        user_vs30=str(user_vs30),
        im=str(im),
        im_component=str(im.component),
        exceedance=exceedance,
        gmt_plots=str(gmt_plots),
    )

    # Get the cached result, if there is one
    cached_data = cache.get(cache_key)

    src_plot_data, eps_plot_data = None, None
    if cached_data is None:
        server.app.logger.debug(f"No cached result for {cache_key}, computing disagg")
        server.app.logger.debug(f"Loading ensemble and retrieving site information")
        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        server.app.logger.debug(
            f"Computing disagg - version {su.api.get_repo_version()}"
        )
        disagg_data = sc.disagg.run_ensemble_disagg(
            ensemble, site_info, im, exceedance=float(exceedance), calc_mean_values=True
        )

        # Also include annual rec prob, magnitude and rrup (for disagg table)
        ruptures_df = ensemble.get_im_ensemble(im.im_type).rupture_df_id.loc[
            disagg_data.fault_disagg_id.index.values
        ]
        flt_dist_df = sc.site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info)
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

        # Additional plots if requested
        if gmt_plots:
            disagg_grid_data = sc.disagg.run_disagg_gridding(disagg_data)

            with tempfile.TemporaryDirectory() as tmp_dir:
                sc.plots.gmt_disagg(
                    str(Path(tmp_dir) / "disagg_src"),
                    disagg_grid_data.to_dict(),
                    bin_type="src",
                )
                sc.plots.gmt_disagg(
                    str(Path(tmp_dir) / "disagg_eps"),
                    disagg_grid_data.to_dict(),
                    bin_type="eps",
                )

                p = Path(tmp_dir) / "disagg_src.png"
                with p.open(mode="rb") as f:
                    src_plot_data = f.read()

                p = Path(tmp_dir) / "disagg_eps.png"
                with p.open(mode="rb") as f:
                    eps_plot_data = f.read()

        if not cache.get(cache_key):
            server.app.logger.debug(
                f"Adding disagg result to cache using key - {cache_key}"
            )
            cache.set(
                cache_key,
                DisaggCachedData(
                    ensemble,
                    site_info,
                    disagg_data,
                    merged_df,
                    src_plot_data,
                    eps_plot_data,
                ),
            )

    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        (
            ensemble,
            site_info,
            disagg_data,
            merged_df,
            src_plot_data,
            eps_plot_data,
        ) = cached_data

    return ensemble, site_info, disagg_data, merged_df, src_plot_data, eps_plot_data
