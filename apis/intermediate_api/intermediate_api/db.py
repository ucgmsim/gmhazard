from typing import Dict, List
from collections import defaultdict

from intermediate_api import db
import intermediate_api.models as models


def _is_user_in_db(user_id: str):
    """To check whether the given user_id is in the DB

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    """
    return bool(models.User.query.filter_by(user_id=user_id).first())


def _insert_user(user_id: str):
    """Insert an user to the MariaDB if not exist

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    """
    if not _is_user_in_db(user_id):
        db.session.add(models.User(user_id))
        db.session.commit()
        db.session.flush()
    else:
        print(f"User {user_id} already exists")


def is_project_in_db(project_id: str):
    """To check whether the given project is in the DB

    Parameters
    ----------
    project_id: str
        A project code we use internally.
        E.g., gnzl, mac_raes, nzgs_pga, soffitel_qtwn...
    """
    return bool(models.Project.query.filter_by(project_id=project_id).first())


def add_project_to_db(project_id: str, project_name: str, access_level: str):
    """Add a new project to the MariaDB if not exist

    Parameters
    ----------
    project_id: str
        A project code we use internally.
        E.g., gnzl, mac_raes, nzgs_pga, soffitel_qtwn...
    project_name: str
        A readable name for projects
    access_level: str
        private or public
    """
    if not is_project_in_db(project_id):
        db.session.add(models.Project(project_id, project_name, access_level))
        db.session.commit()
        db.session.flush()
    else:
        print(f"Project {project_id} already exists")


def _is_permission_in_db(permission_name: str):
    """To check whether the given permission is in the DB

    Parameters
    ----------
    permission_name: str
        A permission name we use internally.
        E.g., hazard, hazard:hazard, project...
    """
    return bool(
        models.Auth0Permission.query.filter_by(permission_name=permission_name).first()
    )


def _insert_permission(permission_name: str):
    """Insert new permission to the MariaDB if not exist

    Parameters
    ----------
    permission_name: str
        A permission name we use internally.
        E.g., hazard, hazard:hazard, project...
    """
    if not _is_permission_in_db(permission_name):
        db.session.add(models.Auth0Permission(permission_name))
        db.session.commit()
        db.session.flush()
    else:
        print(f"Project {permission_name} already exists")


def _is_user_access_permission_in_db(user_id: str, permission: str):
    """Check whether there is a row with given user_id & permission
    
    Parameters
    ----------
    user_id: str
        Auth0's unique ID
    permission: str
        Access permission
        E.g., Hazard, hazard:hazard, project...
    """
    return bool(
        models.UserPermission.query.filter_by(user_id=user_id)
        .filter_by(permission_name=permission)
        .first()
    )


def _insert_user_access_permission(user_id: str, permission: str):
    """Insert data(page access permission) to the bridging table,
    users_permissions

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    permission: str
        Selected user's permission
        E.g., hazard, hazard:hazard, project...
    """
    print(
        f"Check whether the permission is in the DB, if not, add the permission to the DB"
    )
    if not _is_permission_in_db(permission):
        print(f"{permission} is not in the DB so updating it.")
        _insert_permission(permission)
        db.session.flush()

    if not _is_user_access_permission_in_db(user_id, permission):
        db.session.add(models.UserPermission(user_id, permission))
        db.session.commit()
        db.session.flush()
    else:
        print(f"{user_id} already has a permission with ${permission}")


def update_user_access_permission(user_id: str, permission_list: List):
    """Update/Insert user's assigned permission to a table,
    Users_Permissions

    Parameters
    ----------
    user_id: str
        Auth0's unique user id
    permission_list: list
        List of permission that the user has. (From Auth0, trusted source)
    """
    # Sync the users_permissions table to token's permission (trusted source)
    # first before we check/update
    _sync_permissions(user_id, permission_list)

    print(f"Check whether the user is in the DB, if not, add the person to the DB")
    if not _is_user_in_db(user_id):
        print(f"{user_id} is not in the DB so updating it.")
        _insert_user(user_id)
        db.session.flush()

    for permission in permission_list:
        _insert_user_access_permission(user_id, permission)


def _remove_user_access_permission(user_id: str, permission: str):
    """users_permissions table is outdated, remove illegal permission to update the dashboard
    
    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    permission: str
        Selected user's permission
        E.g., hazard, hazard:hazard, project...
    """
    illegal_permission_row = (
        models.UserPermission.query.filter_by(user_id=user_id)
        .filter_by(permission_name=permission)
        .first()
    )

    db.session.delete(illegal_permission_row)
    db.session.commit()
    db.session.flush()


def _insert_user_project_permission(user_id: str, project_id: str):
    """Insert data(assigned projects) to the bridging table,
    users_projects

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    project_id: str
        Selected project's project code.
        E.g., gnzl, mac_raes, nzgs_pga, soffitel_qtwn...
    """
    # Find a project object with a given project_id to get its project id
    project_obj = models.Project.query.filter_by(project_id=project_id).first()

    db.session.add(models.UserProject(user_id, project_obj.project_id))
    db.session.commit()
    db.session.flush()


def _remove_user_project_permission(user_id: str, project_id: str):
    """Remove data(project) from the bridging table,
    users_projects

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    project_id: str
        Selected project's project code.
        E.g., gnzl, mac_raes, nzgs_pga, soffitel_qtwn...
    """
    try:
        # Get the project id with the given project name
        certain_project_id = (
            models.Project.query.filter_by(project_id=project_id).first().project_id
        )

        users_projects_row = (
            models.UserProject.query.filter_by(user_id=user_id)
            .filter_by(project_id=certain_project_id)
            .first()
        )

        db.session.delete(users_projects_row)
        db.session.commit()
        db.session.flush()
    except:
        print("Something went wrong.")


def _get_user_access_permission(requested_user_id: str):
    """Retrieve all permissions for the specified user

    Parameters
    ----------
    requested_user_id: str

    Returns
    -------
    A list of permission names
    """
    all_users_permissions_for_a_user_list = models.UserPermission.query.filter_by(
        user_id=requested_user_id
    ).all()

    return [
        permission.permission_name
        for permission in all_users_permissions_for_a_user_list
    ]


def get_user_project_permission(user_id: str):
    """Retrieves all projects ids for the specified user from Users_Permissions table

    Parameters
    ----------
    user_id: str
        user_id from Auth0 to identify the user

    Returns
    -------
    list of Project IDs from DB (Assigned Projects from Users_Projects table)
    """
    # Get all projects that are assigned to this user.
    assigned_project_objs = (
        models.Project.query.join(models.UserProject)
        .filter((models.UserProject.user_id == user_id))
        .all()
    )

    return {
        project.project_id: project.project_name for project in assigned_project_objs
    }


def get_all_users_project_permissions(auth0_users: Dict):
    """Retrieve all assigned projects from Users_Projects table for each user

    Parameters
    ----------
    auth0_users: Dict
        All the users who are signed up for PSHA app

    Returns
    -------
    users_projects_dict: dictionary
        In the form of:
        {
           userA: [ProjectA, ProjectB, ProjectC],
           userB: [ProjectA, ProjectB]
        }
    """
    # Sync the users_projects table to Auth0's user_id
    _sync_users_table_with_auth0(auth0_users)
    # Get all assigned projects from the UserDB
    users_projects = models.UserProject.query.all()

    users_projects_dict = defaultdict(list)

    for project in users_projects:
        users_projects_dict[project.user_id].append(project.project_id)

    return users_projects_dict


def get_all_users_permissions(auth0_users: Dict):
    """Retrieve permissions for all users
    Retrieve all permissions from Users_Permissions table

    Parameters
    ----------
    auth0_users: Dict
        All the users who are signed up for PSHA app

    Returns
    -------
    Dictionary
        return a list of a dictionary in the form of
            {
              user_id: user_id,
              permission_name: [permission_name]
            }
    """
    # Sync the users_permissions table to Auth0's user_id
    _sync_users_table_with_auth0(auth0_users)
    # Get all assigned permission from the DB.
    all_users_permissions_list = models.UserPermission.query.all()

    users_permissions_dict = defaultdict(list)

    for permission in all_users_permissions_list:
        users_permissions_dict[permission.user_id].append(permission.permission_name)

    return users_permissions_dict


def _sync_users_table_with_auth0(auth0_users: Dict):
    """Sync Users_Permission and Users_Projects tables
    with Auth0 user data
    remove any rows from tables
    with Users who are no longer on board

    Parameters
    ----------
    auth0_users: Dict
        All the users who are signed up for PSHA app
    """
    current_user_ids = auth0_users.keys()
    # Sync Users_Projects table
    all_users_in_users_projects_table = list(
        {user.user_id for user in models.UserProject.query.all()}
    )
    for user_id in all_users_in_users_projects_table:
        if user_id not in current_user_ids:
            models.UserProject.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            db.session.flush()

    # Sync Users_Permissions table
    all_users_in_users_permissions_table = list(
        {user.user_id for user in models.UserPermission.query.all()}
    )
    for user_id in all_users_in_users_permissions_table:
        if user_id not in current_user_ids:
            models.UserPermission.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            db.session.flush()


def allocate_projects_to_user(user_id: str, project_list: List):
    """Give user a permission of the chosen projects

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    project_list: list of dictionaries
        List of projects(dictionary) to allocate in the form of
        [{label: project_name, value: project_id}]
    """
    print(f"Check whether the user is in the DB, if not, add the person to the DB")
    if not _is_user_in_db(user_id):
        print(f"{user_id} is not in the DB so updating it.")
        _insert_user(user_id)
        db.session.flush()

    for project in project_list:
        _insert_user_project_permission(user_id, project["value"])


def remove_projects_from_user(user_id: str, project_list: List):
    """Remove projects from the chosen user

    Parameters
    ----------
    user_id: str
        Selected user's Auth0 id
    project_list: list
        List of projects to remove from the DB
    """
    for project in project_list:
        _remove_user_project_permission(user_id, project["value"])


def get_all_permissions_for_dashboard():
    """Retrieve all permissions from Auth0_Permission table

    Returns
    -------
    A list of permission names
    """
    # Get all assigned permission from the DB.
    all_permission_list = models.Auth0Permission.query.all()

    return [permission.permission_name for permission in all_permission_list]


def _sync_permissions(user_id: str, trusted_permission_list: List):
    """Syncs the user access permissions with the ones from
    the token (the one source of truth)
    Filter the users_permissions table to remove outdated permission

    If the access token has the permission of A, B, C but users_permissions table
    has the permission of A, B, C, D. Then remove the permission D from the
    users_permissions table as the token is the trusted source of permission.

    Parameters
    ----------
    user_id: str
        It will be used to find a list of permission with the function,
        _get_all_users_permissions_for_a_user(user_id)
    trusted_permission_list: list
        The list to be compared with the list of permission from users_permissions
        table
    """
    # Get a list of permission that are assigned to this user
    unfiltered_assigned_permission_list = _get_user_access_permission(user_id)

    for permission in unfiltered_assigned_permission_list:
        if permission not in trusted_permission_list:
            _remove_user_access_permission(user_id, permission)


def write_request_details(user_id: str, action: str, query_dict: Dict):
    """Record users' interaction into the DB

    Parameters
    ----------
    user_id: str
        Determining the user
    action: str
        What users chose to do
        E.g., Hazard Curve Compute, UHS Compute, Disaggregation Compute...
    query_dict: Dict
        It is basically a query dictionary that contains attribute and value
        E.g., Attribute -> Station
              value -> CCCC
    """
    # Insert to History table
    new_history = models.History(user_id, action)
    db.session.add(new_history)
    db.session.commit()

    # Get a current user's history id key which would be the last row in a table
    latest_history_id = (
        models.History.query.filter_by(user_id=user_id)
        .order_by(models.History.history_id.desc())
        .first()
        .history_id
    )

    # For History_Request with attribute and value
    for attribute, value in query_dict.items():
        if attribute == "exceedances":
            # 'exceedances' value is comma-separated
            exceedances_list = value.split(",")
            for exceedance in exceedances_list:
                new_history = models.HistoryRequest(
                    latest_history_id, attribute, exceedance
                )
                db.session.add(new_history)
        else:
            new_history = models.HistoryRequest(latest_history_id, attribute, value)
            db.session.add(new_history)

    db.session.commit()


def get_projects(access_level: str = None):
    """Get all projects that have a given access_level from the Project table

    Parameters
    ----------
    access_level: str
        Determining the access level

    Returns
    -------
    Dictionary in the form of
    {
        project_id: project_name
    }
    """
    projects = (
        models.Project.query.filter_by(access_level=access_level).all()
        if access_level is not None
        else models.Project.query.all()
    )

    return {project.project_id: project.project_name for project in projects}
