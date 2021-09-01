from flask_sqlalchemy import SQLAlchemy


class CustomSQLALchemy(SQLAlchemy):
    """Customize the SQLAlchemy class to override isolation level"""

    def apply_driver_hacks(self, app, info, options):
        options.update(
            {"isolation_level": "READ COMMITTED",}
        )
        super(CustomSQLALchemy, self).apply_driver_hacks(app, info, options)
