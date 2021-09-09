from flask import jsonify, request, Response

from intermediate_api import app, PROJECT_API_BASE, PROJECT_API_TOKEN
import intermediate_api.db as db
import intermediate_api.utils as utils
import intermediate_api.decorators as decorators
import intermediate_api.auth0 as auth0
import intermediate_api.constants as const
import intermediate_api.api.intermediate_api as intermediate_api


# Site Selection
def _get_available_projects():
    return utils.proxy_to_api(
        request, const.PROJECT_IDS_ENDPOINT, "GET", PROJECT_API_BASE, PROJECT_API_TOKEN
    ).get_json()


@app.route(const.PROJECT_API_PROJECT_IDS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_available_project_ids():
    user_id = auth0.get_user_id()

    return utils.run_project_crosscheck(
        db.get_user_project_permission(user_id),
        intermediate_api.get_public_projects().get_json(),
        _get_available_projects()["ids"],
    )


@app.route(const.PROJECT_API_SITES_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_sites():
    return utils.proxy_to_api(
        request,
        const.PROJECT_SITES_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_IMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_ims():
    return utils.proxy_to_api(
        request, const.PROJECT_IMS_ENDPOINT, "GET", PROJECT_API_BASE, PROJECT_API_TOKEN
    )


@app.route(const.PROJECT_API_MAPS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_maps():
    return utils.proxy_to_api(
        request,
        const.PROJECT_CONTEXT_MAPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Site Selection Get",
    )


# Seismic Hazard
@app.route(const.PROJECT_API_HAZARD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_hazard():
    return utils.proxy_to_api(
        request,
        const.PROJECT_HAZARD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Hazard Compute",
    )


@app.route(const.PROJECT_API_HAZARD_DISAGG_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_disagg():
    return utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Disaggregation Compute",
    )


@app.route(const.PROJECT_API_HAZARD_DISAGG_RPS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_disagg_rps():
    return utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_RPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_HAZARD_UHS_RPS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_uhs_rps():
    return utils.proxy_to_api(
        request,
        const.PROJECT_UHS_RPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_HAZARD_UHS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_project_uhs():
    return utils.proxy_to_api(
        request,
        const.PROJECT_UHS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - UHS Compute",
    )


@app.route(const.PROJECT_API_GMS_RUNS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_gms_runs():
    return utils.proxy_to_api(
        request,
        const.PROJECT_GMS_RUNS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_GMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_ensemble_gms():
    return utils.proxy_to_api(
        request,
        const.PROJECT_GMS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - GMS Compute",
    )


@app.route(const.PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_gms_default_causal_params():
    response = utils.proxy_to_api(
        request,
        const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - GMS Get Default Causal Params",
    )

    if response.status_code is const.OK_CODE:
        data_dict = response.get_json()

        contribution_df_data = data_dict["contribution_df"]

        sorted_rrup, rrup_cdf = utils.calc_cdf(
            contribution_df_data["contribution"][:], contribution_df_data["rrup"]
        )
        sorted_mag, mag_cdf = utils.calc_cdf(
            contribution_df_data["contribution"][:], contribution_df_data["magnitude"]
        )
        data_dict["contribution_df"] = {
            "magnitude": sorted_mag.tolist(),
            "mag_contribution": mag_cdf.tolist(),
            "rrup": sorted_rrup.tolist(),
            "rrup_contribution": rrup_cdf.tolist(),
        }

        return jsonify(data_dict)

    return Response(status=response.status_code)


@app.route(const.PROJECT_API_SCENARIOS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_ensemble_scenarios():
    return utils.proxy_to_api(
        request,
        const.PROJECT_SCENARIO_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Scenarios Get",
    )


# PROJECT DOWNLOAD
@app.route(const.PROJECT_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def project_api_download_hazard():
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_HAZARD_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Hazard Download",
        content_type="application/zip",
    )

    return project_response


@app.route(const.PROJECT_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def project_api_download_disagg():
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Disaggregation Download",
        content_type="application/zip",
    )

    return project_response


@app.route(const.PROJECT_API_HAZARD_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def project_api_download_uhs():
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_UHS_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - UHS Download",
        content_type="application/zip",
    )

    return project_response


@app.route(f"{const.PROJECT_API_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@decorators.requires_auth
def project_api_download_gms(token):
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_GMS_DOWNLOAD_ENDPOINT + "/" + token,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - GMS Download",
        content_type="application/zip",
    )

    return project_response


@app.route(f"{const.PROJECT_API_SCENARIOS_DOWNLOAD_ENDPOINT}", methods=["GET"])
@decorators.requires_auth
def project_api_download_scenario():
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_SCENARIO_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id(),
        action="Project - Scenario Download",
        content_type="application/zip",
    )

    return project_response
