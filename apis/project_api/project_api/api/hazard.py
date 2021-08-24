import tempfile

import flask
from flask_cors import cross_origin

import seistech_utils as su
from seistech_calc.im import IM, IMComponent
from ..server import (
    app,
    requires_auth,
    DOWNLOAD_URL_SECRET_KEY,
    DOWNLOAD_URL_VALID_FOR,
    BASE_PROJECTS_DIR,
)
from .. import constants as const
from ..utils import load_hazard_data


@app.route(const.PROJECT_HAZARD_ENDPOINT, methods=["GET"])
@cross_origin(expose_headers=["Content-Type", "Authorization"])
@requires_auth
@su.api.endpoint_exception_handling(app)
def get_ensemble_hazard():
    app.logger.info(f"Received request at {const.PROJECT_HAZARD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (project_id, station_id, im), optional_kwargs = su.api.get_check_keys(
        flask.request.args,
        ("project_id", "station_id", ("im", IM.from_str)),
        (("im_component", str),),
    )
    im.component = (
        IMComponent.RotD50
        if optional_kwargs.get("im_component") is None
        else IMComponent[optional_kwargs.get("im_component")]
    )
    app.logger.debug(f"Request parameters {project_id}, {station_id}, {im}")

    # Load the data
    ensemble_hazard, nzs1170p5_hazard, nzta_hazard = load_hazard_data(
        BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / str(im.component),
        im,
    )

    result = su.api.get_ensemble_hazard_response(
        ensemble_hazard,
        su.api.get_download_token(
            {
                "project_id": project_id,
                "station_id": ensemble_hazard.site.station_name,
                "im": str(ensemble_hazard.im),
                "im_component": str(ensemble_hazard.im.component),
            },
            DOWNLOAD_URL_SECRET_KEY,
            DOWNLOAD_URL_VALID_FOR,
        ),
    )
    result = {**result, "nzs1170p5_hazard": nzs1170p5_hazard.to_dict()}

    if ensemble_hazard.percentiles is not None:
        result = {
            **result,
            "percentiles": {
                key: {
                    im_value: exceedance for im_value, exceedance in value.iteritems()
                }
                for key, value in ensemble_hazard.percentiles.items()
            },
        }

    if nzta_hazard is not None:
        result = {**result, "nzta_hazard": nzta_hazard.to_dict(nan_to_string=True)}
    return flask.jsonify(result)


@app.route(const.PROJECT_HAZARD_DOWNLOAD_ENDPOINT, methods=["GET"])
@su.api.endpoint_exception_handling(app)
def download_ens_hazard():
    """Handles downloading of the hazard data,
    specified by the given token"""
    app.logger.info(f"Received request at {const.PROJECT_HAZARD_DOWNLOAD_ENDPOINT}")

    _, version_str = su.utils.get_package_version(const.PACKAGE_NAME)
    app.logger.debug(f"API - version {version_str}")

    (token,), _ = su.api.get_check_keys(flask.request.args, ("hazard_token",))

    payload = su.api.get_token_payload(token, DOWNLOAD_URL_SECRET_KEY)

    project_id, station_id, im, im_component = (
        payload["project_id"],
        payload["station_id"],
        IM.from_str(payload["im"]),
        payload["im_component"],
    )

    app.logger.debug(
        f"Token parameters {project_id}, {station_id}, {im}, {im_component}"
    )

    # Load the data
    ensemble_hazard, nzs1170p5_hazard, nzta_hazard = load_hazard_data(
        BASE_PROJECTS_DIR
        / version_str
        / project_id
        / "results"
        / station_id
        / im_component,
        im,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        zip_ffp = su.api.create_hazard_download_zip(
            ensemble_hazard, nzs1170p5_hazard, tmp_dir, nzta_hazard=nzta_hazard,
        )

        return flask.send_file(
            zip_ffp,
            as_attachment=True,
            attachment_filename=f"{ensemble_hazard.ensemble.name}_{ensemble_hazard.site.station_name}_hazard.zip",
        )
