from intermediate_api import db
import intermediate_api.auth0 as auth0

# Because models need to be imported after db gets imported
from intermediate_api.models import *

# Create tables - It only creates when tables don't exist
db.create_all()
db.session.commit()

print(auth0.get_users())

# Need to be manually done as we cannot pull permission data from Auth0
# PERMISSION may vary on their Auth0 setting
PERMISSION_LIST = [
    "create-project",
    "edit-user",
    "hazard",
    "hazard:hazard",
    "hazard:disagg",
    "hazard:uhs",
    "hazard:gms",
    "project",
    "admin",
]

# Adding all users from Auth0 to the User table
user_info, _ = auth0.get_users()
for user_id in user_info.keys():
    db.session.add(User(user_id))
    db.session.commit()

# Adding all permission to the Auth0Permission table
for permission in PERMISSION_LIST:
    db.session.add(Auth0Permission(permission))
    db.session.commit()
