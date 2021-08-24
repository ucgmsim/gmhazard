import base64
import tempfile
from pathlib import Path
from typing import Tuple, Union

import flask
import pandas as pd
from flask_cors import cross_origin
from werkzeug.contrib.cache import BaseCache

import seistech_calc as si
import seistech_utils as su
from ..server import app, requires_auth, DOWNLOAD_URL_VALID_FOR, DOWNLOAD_URL_SECRET_KEY
from .. import constants as const


class DisaggCachedData:
    def __init__(
        self,
        ensemble: si.gm_data.Ensemble,
        site_info: si.site.SiteInfo,
        disagg_data: si.disagg.EnsembleDisaggData,
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


@app.route(const.ENSEMBLE_DISAGG_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app=app)
def get_ensemble_disagg():
    """Retrieves the contribution of each rupture for the
    specified exceedance.

    Valid request has to contain the following
    URL parameters: ensemble_id, station, im, exceedance
    """
    app.logger.info(f"Received request at {const.ENSEMBLE_DISAGG_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    (
        (ensemble_id, station, im, exceedance,),
        optional_params_dict,
    ) = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", ("im", si.im.IM.from_str), "exceedance"),
        (
            ("gmt_plot", bool, False),
            ("vs30", float),
            ("im_component", si.im.IMComponent, si.im.IMComponent.RotD50),
        ),
    )
    gmt_plots = optional_params_dict["gmt_plot"]
    user_vs30 = optional_params_dict.get("vs30")
    im.component = optional_params_dict.get("im_component")

    app.logger.debug(f"Request parameters {ensemble_id}, {station}, {im}, {exceedance}")

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
                DOWNLOAD_URL_SECRET_KEY,
                DOWNLOAD_URL_VALID_FOR,
            ),
        )
    )


@app.route(f"{const.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT}", methods=["Get"])
@su.api.endpoint_exception_handling(app)
def download_ens_disagg():
    """Handles downloading of disagg contribution data"""
    app.logger.info(f"Received request at {const.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT}")
    cache = flask.current_app.extensions["cache"]

    # Retrieve parameters from the token
    disagg_token, *_ = su.api.get_check_keys(flask.request.args, ("disagg_token",))
    disagg_payload = su.api.get_token_payload(disagg_token[0], DOWNLOAD_URL_SECRET_KEY)
    ensemble_id, station, user_vs30, im, exceedance, gmt_plots = (
        disagg_payload["ensemble_id"],
        disagg_payload["station"],
        disagg_payload["user_vs30"],
        si.im.IM.from_str(disagg_payload["im"]),
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


@app.route(const.ENSEMBLE_FULL_DISAGG_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_full_disagg():
    """
    Valid request has to contain the following
    URL parameters: ensemble_id, station, im, exceedance
    """
    app.logger.info(f"Received request at {const.ENSEMBLE_FULL_DISAGG_ENDPOINT}")

    (
        (ensemble_id, station, im, exceedance,),
        optional_values_dict,
    ) = su.api.get_check_keys(
        flask.request.args,
        ("ensemble_id", "station", ("im", si.im.IM.from_str), "exceedance"),
        (
            ("mag_min", float),
            ("mag_n_bins", float),
            ("mag_bin_size", float),
            ("rrup_min", float),
            ("rrup_n_bins", float),
            ("rrup_bin_size", float),
            ("im_component", si.im.IMComponent, si.im.IMComponent.RotD50),
        ),
    )

    app.logger.debug(
        f"Request parameters {ensemble_id}, {station}, {im}, {exceedance}, "
        f"optional parameters {optional_values_dict}"
    )

    user_vs30 = optional_values_dict.get("vs30")
    im.component = optional_values_dict.get("im_component")

    app.logger.debug(f"Loading ensemble and retrieving site information")
    ensemble = si.gm_data.Ensemble(ensemble_id)
    site = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

    app.logger.debug(f"Computing disagg")
    disagg_data = si.disagg.run_ensemble_disagg(
        ensemble, site, im, exceedance=float(exceedance), calc_mean_values=True
    )

    app.logger.debug("Computing disagg gridding")
    disagg_grid_data = si.disagg.run_disagg_gridding(
        disagg_data, **optional_values_dict
    )

    return flask.jsonify({"disagg_grid_data": disagg_grid_data.to_dict()})


def _get_disagg(
    ensemble_id: str,
    station: str,
    im: si.im.IM,
    exceedance: str,
    cache: BaseCache,
    gmt_plots: bool = False,
    user_vs30: float = None,
) -> Tuple[
    si.gm_data.Ensemble,
    si.site.SiteInfo,
    si.disagg.EnsembleDisaggData,
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
        app.logger.debug(f"No cached result for {cache_key}, computing disagg")
        app.logger.debug(f"Loading ensemble and retrieving site information")
        ensemble = si.gm_data.Ensemble(ensemble_id)
        site_info = si.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        app.logger.debug(f"Computing disagg - version {su.api.get_repo_version()}")
        disagg_data = si.disagg.run_ensemble_disagg(
            ensemble, site_info, im, exceedance=float(exceedance), calc_mean_values=True
        )

        # Also include annual rec prob, magnitude and rrup (for disagg table)
        ruptures_df = ensemble.rupture_df.loc[disagg_data.fault_disagg.index.values]
        flt_dist_df = si.site_source.get_distance_df(ensemble.flt_ssddb_ffp, site_info)
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
            disagg_grid_data = si.disagg.run_disagg_gridding(disagg_data)

            with tempfile.TemporaryDirectory() as tmp_dir:
                si.plots.gmt_disagg(
                    str(Path(tmp_dir) / "disagg_src"),
                    disagg_grid_data.to_dict(),
                    bin_type="src",
                )
                si.plots.gmt_disagg(
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

        if not cache.has(cache_key):
            app.logger.debug(f"Adding disagg result to cache using key - {cache_key}")
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
        app.logger.debug(f"Using cached result with key {cache_key}")
        (
            ensemble,
            site_info,
            disagg_data,
            merged_df,
            src_plot_data,
            eps_plot_data,
        ) = cached_data

    return ensemble, site_info, disagg_data, merged_df, src_plot_data, eps_plot_data
