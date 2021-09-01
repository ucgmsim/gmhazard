from intermediate_api import db
import intermediate_api.auth0 as auth0

# Because models need to be imported after db gets imported
from intermediate_api.models import *

# Create tables - It only creates when tables don't exist
db.create_all()
db.session.commit()

print(auth0.get_users())

# Need to be manually done as we cannot pull permission data from Auth0
PERMISSION_LIST = [
    "create-project",
    "edit-user",
    "hazard",
    "hazard:hazard",
    "hazard:disagg",
    "hazard:uhs",
    "hazard:gms",
    "project",
    "psha-admin",
]

PROJECT_DICT = {
    "gnzl": "Generic New Zealand Locations",
    "mac_raes": "MacRaes Oceania Gold",
    "nzgs_pga": "NZGS",
    "soffitel_qtwn": "Soffitel, Queenstown",
    "wel_par_accom": "Wellington Parliament Accomodation",
}

PUBLIC_PROJECT_IDS = {"gnzl", "nzgs_pga"}

# Adding all users from Auth0 to the User table
for key in auth0.get_users():
    db.session.add(User(key))
    db.session.commit()

# Adding all permission to the Auth0Permission table
for permission in PERMISSION_LIST:
    db.session.add(Auth0Permission(permission))
    db.session.commit()

# Adding initial five project ids to the Project table
for code, name in PROJECT_DICT.items():
    if code in PUBLIC_PROJECT_IDS:
        db.session.add(Project(code, name, "public"))
        db.session.commit()
    else:
        db.session.add(Project(code, name))
        db.session.commit()
