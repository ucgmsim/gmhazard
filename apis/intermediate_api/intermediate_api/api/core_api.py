import os

from jose import jwt
from flask import request

from intermediate_api import app
import intermediate_api.utils as utils
import intermediate_api.auth0 as auth0
import intermediate_api.decorators as decorators
import intermediate_api.constants as const


# For DEV/EA/PROD with ENV
CORE_API_BASE = os.environ["CORE_API_BASE"]

# Generate the coreAPI token
CORE_API_TOKEN = "Bearer {}".format(
    jwt.encode(
        {"env": os.environ["ENV"]}, os.environ["CORE_API_SECRET"], algorithm="HS256"
    )
)


# Site Selection
@app.route(const.CORE_API_ENSEMBLE_IDS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_ensemble_ids(auth):
    print(auth)
    return utils.proxy_to_api(
        request, const.ENSEMBLE_IDS_ENDPOINT, "GET", CORE_API_BASE, CORE_API_TOKEN, auth
    )


@app.route(const.CORE_API_IMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_im_ids(auth):
    return utils.proxy_to_api(
        request, const.ENSEMBLE_IMS_ENDPOINT, "GET", CORE_API_BASE, CORE_API_TOKEN, auth
    )


@app.route(const.CORE_API_CONTEXT_MAP_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_context_map(auth):
    return utils.proxy_to_api(
        request,
        const.SITE_CONTEXT_MAP_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


@app.route(const.CORE_API_VS30_MAP_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_vs30_map(auth):
    return utils.proxy_to_api(
        request,
        const.SITE_VS30_MAP_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


@app.route(const.CORE_API_VS30_SOIL_CLASS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_soil_class_from_vs30(auth):
    return utils.proxy_to_api(
        request,
        const.SITE_VS30_SOIL_CLASS_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


@app.route(const.CORE_API_STATION_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_station(auth):
    return utils.proxy_to_api(
        request,
        const.SITE_LOCATION_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - Set Station",
    )


# Seismic Hazard
@app.route(const.CORE_API_HAZARD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_hazard(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.ENSEMBLE_HAZARD_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - Hazard Curve Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZS1170P5_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_hazard_nzs1170p5(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZS1170p5_HAZARD_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - Hazard NZS1170p5 Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZS1170P5_SOIL_CLASS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_nzs1170p5_soil_class(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZS1170p5_SOIL_CLASS,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZS1170P5_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_nzs1170p5_default_params(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZS1170p5_DEFAULT_PARAMS_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZTA_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_hazard_nzta(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZTA_HAZARD_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - Hazard NZTA Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZTA_SOIL_CLASS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_nzta_soil_class(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request, const.NZTA_SOIL_CLASS, "GET", CORE_API_BASE, CORE_API_TOKEN, auth,
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_NZTA_DEFAULT_PARAMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_nzta_default_params(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZTA_DEFAULT_PARAMS_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_DISAGG_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_disagg(auth):
    if auth0.requires_permission("hazard:disagg"):
        return utils.proxy_to_api(
            request,
            const.ENSEMBLE_DISAGG_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - Disaggregation Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_UHS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_uhs(auth):
    if auth0.requires_permission("hazard:uhs"):
        return utils.proxy_to_api(
            request,
            const.ENSEMBLE_UHS_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - UHS Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


@app.route(const.CORE_API_HAZARD_UHS_NZS1170P5_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_uhs_nzs1170p5(auth):
    if auth0.requires_permission("hazard:hazard"):
        return utils.proxy_to_api(
            request,
            const.NZS1170p5_UHS_ENDPOINT,
            "GET",
            CORE_API_BASE,
            CORE_API_TOKEN,
            auth,
            user_id=auth0.get_user_id(),
            action="Hazard Analysis - UHS NZS1170p5 Compute",
        )
    raise auth0.AuthError(
        {
            "code": "Unauthorized",
            "description": "You don't have access to this resource",
        },
        const.NO_ACCESS_RIGHT_CODE,
    )


# GMS
@app.route(const.CORE_API_GMS_ENDPOINT, methods=["POST"])
@decorators.requires_auth
def compute_ensemble_gms(auth):
    return utils.proxy_to_api(
        request,
        const.ENSEMBLE_GMS_COMPUTE_ENDPOINT,
        "POST",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        data=request.data.decode(),
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - GMS Compute",
    )


@app.route(const.CORE_API_GMS_DEFAULT_IM_WEIGHTS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_default_im_weights(auth):
    return utils.proxy_to_api(
        request,
        const.GMS_DEFAULT_IM_WEIGHTS_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


@app.route(const.CORE_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_default_causal_params(auth):
    return utils.proxy_to_api(
        request,
        const.GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


# GMS
@app.route(const.CORE_API_GMS_DATASETS_ENDPOINT, methods=["GET"])
def get_gm_datasets(auth):
    return utils.proxy_to_api(
        request,
        const.GMS_GM_DATASETS_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
    )


@app.route(const.CORE_API_GMS_IMS_ENDPOINT_ENDPOINT, methods=["GET"])
def get_gms_available_ims(auth):
    return utils.proxy_to_api(
        request, const.GMS_IMS_ENDPOINT, "GET", CORE_API_BASE, CORE_API_TOKEN, auth
    )


# Scenarios
@app.route(const.CORE_API_SCENARIOS_ENDPOINT, methods=["GET"])
def get_scenario(auth):
    return utils.proxy_to_api(
        request,
        const.ENSEMBLE_SCENARIO_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - Scenarios Get",
    )


# Download
# CORE API
@app.route(const.CORE_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def core_api_download_hazard(auth):
    core_response = utils.proxy_to_api(
        request,
        const.ENSEMBLE_HAZARD_DOWNLOAD_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - Hazard Download",
        content_type="application/zip",
    )

    return core_response


@app.route(const.CORE_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def core_api_download_disagg(auth):
    core_response = utils.proxy_to_api(
        request,
        const.ENSEMBLE_DISAGG_DOWNLOAD_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - Disaggregation Download",
        content_type="application/zip",
    )

    return core_response


@app.route(const.CORE_API_HAZARD_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def core_api_download_uhs(auth):
    core_response = utils.proxy_to_api(
        request,
        const.ENSEMBLE_UHS_DOWNLOAD_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - UHS Download",
        content_type="application/zip",
    )

    return core_response


@app.route(f"{const.CORE_API_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@decorators.requires_auth
def core_api_download_gms(token):
    core_response = utils.proxy_to_api(
        request,
        const.ENSEMBLE_GMS_DOWNLOAD_ENDPOINT + "/" + token,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - GMS Download",
        content_type="application/zip",
    )

    return core_response


@app.route(f"{const.CORE_API_SCENARIOS_DOWNLOAD_ENDPOINT}", methods=["GET"])
@decorators.requires_auth
def core_api_download_scenario(auth):
    core_response = utils.proxy_to_api(
        request,
        const.ENSEMBLE_SCENARIO_DOWNLOAD_ENDPOINT,
        "GET",
        CORE_API_BASE,
        CORE_API_TOKEN,
        auth,
        user_id=auth0.get_user_id(),
        action="Hazard Analysis - Scenarios Download",
        content_type="application/zip",
    )

    return core_response
