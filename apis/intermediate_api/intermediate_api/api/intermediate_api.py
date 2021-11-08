import json

from flask import jsonify, request, Response
from jose import jwt

from intermediate_api import app, PROJECT_API_BASE, PROJECT_API_TOKEN
import intermediate_api.db as db
import intermediate_api.utils as utils
import intermediate_api.auth0 as auth0
import intermediate_api.decorators as decorators
import intermediate_api.constants as const


@app.route(const.INTERMEDIATE_API_AUTH0_USER_INFO_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_auth0_user_key_info(auth):
    """Getting users permission on their first launch

    At the same time, also update the users_permissions table
    as we want to keep the users_permissions table up to date
    for the dashboards.
    """
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_AUTH0_USER_INFO_ENDPOINT}"
    )

    token = auth0.get_token_auth_header()
    unverified_claims = jwt.get_unverified_claims(token)

    user_id = unverified_claims["sub"].split("|")[1]
    permission_list = unverified_claims["permissions"]

    # Update the Users_Permissions table
    db.update_user_access_permission(user_id, permission_list)

    return jsonify({"permissions": permission_list, "id": user_id})


# Edit User
@app.route(const.INTERMEDIATE_API_AUTH0_USERS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
def get_auth0_users(auth):
    """Fetching all the existing users from the Auth0
    These will be used for User dropdown in the Permission Config

    Have to use Auth0 as source for users, to allow
    setting user permission to users that don't
    exist in the DB yet
    """
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_AUTH0_USERS_ENDPOINT}"
    )
    response, status_code = auth0.get_users()
    return jsonify(response), status_code


@app.route(const.INTERMEDIATE_API_ALL_PRIVATE_PROJECTS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_private_projects(auth):
    """Fetching all private projects from the Project table"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_ALL_PRIVATE_PROJECTS_ENDPOINT}"
    )
    return jsonify(db.get_projects("private"))


@app.route(const.INTERMEDIATE_API_ALL_PUBLIC_PROJECTS_ENDPOINT, methods=["GET"])
@decorators.endpoint_exception_handler
def get_public_projects():
    """Fetching all public projects from the Project table"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_ALL_PUBLIC_PROJECTS_ENDPOINT}"
    )
    return jsonify(db.get_projects("public"))


@app.route(const.INTERMEDIATE_API_USER_PROJECTS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_user_allowed_projects(auth):
    """Fetching all the projects that are already allowed to a user
    Will be used for allowed Private Projects dropdown
    """
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_USER_PROJECTS_ENDPOINT}"
    )

    user_id = request.args.to_dict()["user_id"]

    return jsonify(db.get_user_project_permission(user_id))


@app.route(const.INTERMEDIATE_API_USER_ALLOCATE_PROJECTS_ENDPOINT, methods=["POST"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def allocate_projects_to_user(auth):
    """Allocate the chosen project(s) to the chosen user."""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_USER_ALLOCATE_PROJECTS_ENDPOINT}"
    )

    data = json.loads(request.data.decode())

    user_id = data["user_info"]["value"]
    project_list = data["project_info"]

    db.allocate_projects_to_user(user_id, project_list)

    return Response(status=const.OK_CODE)


@app.route(const.INTERMEDIATE_API_USER_REMOVE_PROJECTS_ENDPOINT, methods=["POST"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def remove_projects_from_user(auth):
    """Remove the chosen project(s) from the chosen user."""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_USER_REMOVE_PROJECTS_ENDPOINT}"
    )

    data = json.loads(request.data.decode())

    user_id = data["user_info"]["value"]
    project_list = data["project_info"]

    db.remove_projects_from_user(user_id, project_list)

    return Response(status=const.OK_CODE)


@app.route(const.INTERMEDIATE_API_ALL_USERS_PROJECTS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_all_users_projects(auth):
    """Pull every assigned project for all users from Users_Projects table"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_ALL_USERS_PROJECTS_ENDPOINT}"
    )
    auth0_users, _ = auth0.get_users()
    return db.get_all_users_project_permissions(auth0_users)


@app.route(const.INTERMEDIATE_API_ALL_PERMISSIONS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_all_permissions(auth):
    """Pull all possible access permission (Auth0_Permission table)"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_ALL_PERMISSIONS_ENDPOINT}"
    )
    return jsonify({"all_permissions": db.get_all_permissions_for_dashboard()})


@app.route(const.INTERMEDIATE_API_ALL_USERS_PERMISSIONS_ENDPOINT, methods=["GET"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def get_all_users_permissions(auth):
    """Pull every assigned access permission for all uesrs from Users_Permissions table"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_ALL_USERS_PERMISSIONS_ENDPOINT}"
    )
    auth0_users, _ = auth0.get_users()
    return db.get_all_users_permissions(auth0_users)


@app.route(const.INTERMEDIATE_API_CREATE_PROJECT_ENDPOINT, methods=["POST"])
@decorators.requires_auth
@decorators.endpoint_exception_handler
def create_project(auth):
    """Create new project(s)"""
    app.logger.info(
        f"Received request at {const.INTERMEDIATE_API_CREATE_PROJECT_ENDPOINT}"
    )
    data = json.loads(request.data.decode())

    # Use Display Name as Project ID
    # If Project ID is not provided
    if data.get("id") is None or len(data["id"].strip()) == 0:
        data["id"] = data["name"].lower().strip().replace(" ", "_")

    if db.is_project_in_db(data["id"]):
        return (
            jsonify({"project_created": False, "reason": "Already exists"}),
            const.CONFLICT_CODE,
        )
    else:
        response_code = utils.proxy_to_core_api(
            request,
            const.PROJECT_CREATE_NEW_ENDPOINT,
            "POST",
            PROJECT_API_BASE,
            PROJECT_API_TOKEN,
            auth,
            data=json.dumps(data),
            user_id=auth0.get_user_id(),
            action="Project Creation - Triggering project generation",
        ).status_code

        if response_code == const.OK_CODE:
            db.add_project_to_db(data["id"], data["name"], data["access_level"])
            return jsonify({"project_created": True}), const.OK_CODE
        else:
            return (
                jsonify({"project_created": False}),
                response_code,
            )
