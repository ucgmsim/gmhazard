from flask import jsonify, request, Response

from intermediate_api import app, PROJECT_API_BASE, PROJECT_API_TOKEN
import intermediate_api.db as db
import intermediate_api.utils as utils
import intermediate_api.decorators as decorators
import intermediate_api.auth0 as auth0
import intermediate_api.constants as const
import intermediate_api.api.intermediate_api as intermediate_api


# Site Selection
def get_available_projects():
    return utils.proxy_to_api(
        request, const.PROJECT_IDS_ENDPOINT, "GET", PROJECT_API_BASE, PROJECT_API_TOKEN,
    ).get_json()


@app.route(const.PROJECT_API_PROJECT_IDS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
@decorators.endpoint_exception_handler
def get_available_project_ids(is_authenticated):
    if is_authenticated:
        user_id = auth0.get_user_id()
        return utils.run_project_crosscheck(
            db.get_user_project_permission(user_id),
            intermediate_api.get_public_projects().get_json(),
            get_available_projects()["ids"],
        )
    else:
        return utils.run_project_crosscheck(
            {}, db.get_projects("public"), get_available_projects()["ids"],
        )


@app.route(const.PROJECT_API_SITES_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_sites(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_SITES_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_IMS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_ims(is_authenticated):
    return utils.proxy_to_api(
        request, const.PROJECT_IMS_ENDPOINT, "GET", PROJECT_API_BASE, PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_MAPS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_maps(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_CONTEXT_MAPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Site Selection Get" if is_authenticated else None,
    )


# Seismic Hazard
@app.route(const.PROJECT_API_HAZARD_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_hazard(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_HAZARD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Hazard Compute" if is_authenticated else None,
    )


@app.route(const.PROJECT_API_HAZARD_DISAGG_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_disagg(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Disaggregation Compute" if is_authenticated else None,
    )


@app.route(const.PROJECT_API_HAZARD_DISAGG_RPS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_disagg_rps(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_RPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_HAZARD_UHS_RPS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_uhs_rps(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_UHS_RPS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_HAZARD_UHS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_project_uhs(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_UHS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - UHS Compute" if is_authenticated else None,
    )


@app.route(const.PROJECT_API_GMS_RUNS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_gms_runs(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_GMS_RUNS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
    )


@app.route(const.PROJECT_API_GMS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_ensemble_gms(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_GMS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - GMS Compute" if is_authenticated else None,
    )


@app.route(const.PROJECT_API_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def get_gms_default_causal_params(is_authenticated):
    response = utils.proxy_to_api(
        request,
        const.PROJECT_GMS_DEFAULT_CAUSAL_PARAMS_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - GMS Get Default Causal Params" if is_authenticated else None,
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
@decorators.get_authentication
def get_ensemble_scenarios(is_authenticated):
    return utils.proxy_to_api(
        request,
        const.PROJECT_SCENARIO_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Scenarios Get" if is_authenticated else None,
    )


# PROJECT DOWNLOAD
@app.route(const.PROJECT_API_HAZARD_CURVE_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def project_api_download_hazard(is_authenticated):
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_HAZARD_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Hazard Download" if is_authenticated else None,
        content_type="application/zip",
    )

    return project_response


@app.route(const.PROJECT_API_HAZARD_DISAGG_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def project_api_download_disagg(is_authenticated):
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_DISAGG_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - Disaggregation Download" if is_authenticated else None,
        content_type="application/zip",
    )

    return project_response


@app.route(const.PROJECT_API_HAZARD_UHS_DOWNLOAD_ENDPOINT, methods=["GET"])
@decorators.get_authentication
def project_api_download_uhs(is_authenticated):
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_UHS_DOWNLOAD_ENDPOINT,
        "GET",
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - UHS Download" if is_authenticated else None,
        content_type="application/zip",
    )

    return project_response


@app.route(f"{const.PROJECT_API_GMS_DOWNLOAD_ENDPOINT}/<token>", methods=["GET"])
@decorators.get_authentication
def project_api_download_gms(is_authenticated, token):
    project_response = utils.proxy_to_api(
        request,
        const.PROJECT_GMS_DOWNLOAD_ENDPOINT + "/" + token,
        PROJECT_API_BASE,
        PROJECT_API_TOKEN,
        user_id=auth0.get_user_id() if is_authenticated else None,
        action="Project - GMS Download" if is_authenticated else None,
        content_type="application/zip",
    )

    return project_response


@app.route(f"{const.PROJECT_API_SCENARIOS_DOWNLOAD_ENDPOINT}", methods=["GET"])
@decorators.get_authentication
def project_api_download_scenario(is_authenticated):
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
