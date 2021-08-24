import datetime
import functools
from typing import Callable
from contextlib import contextmanager

import tables
import numpy as np
import pandas as pd


def check_open(f: Callable = None, *, writeable: bool = False):
    """Decorator that can be wrapped around methods/properties
    of the BaseDb (and subclasses) that require the database to be open
    See https://realpython.com/primer-on-python-decorators/#decorators-with-arguments
    """

    def decorator(f: Callable):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            instance = args[0]
            if not isinstance(instance, BaseDB):
                raise Exception(
                    "This decorator can only be used " "on subclasses of BaseDb"
                )
            if not instance.is_open:
                raise Exception(
                    "The database has not been opened. Please open the "
                    "database before accessing this method/property."
                )
            if writeable and not instance.writeable:
                raise Exception(
                    "This method requires the database "
                    "to have been opened in write mode."
                )
            return f(*args, **kwargs)

        return wrapper

    if f is None:
        return decorator
    else:
        return decorator(f)


class BaseDB:
    """Base class for all h5 dbs that
    read/write data using the pd.HDFStore
    """

    def __init__(self, db_ffp: str, writeable: bool = False):
        self._db = None
        self._attrs = None

        self.db_ffp = db_ffp
        self.writeable = writeable

    @property
    def is_open(self):
        return self._db is not None

    @property
    @check_open
    def attributes(self):
        if self._attrs is None:
            self._attrs = self.get_attributes()
        return self._attrs

    def __enter__(self) -> "BaseDB":
        """Defining __enter__ and __exit__ allows
        the class to be used as a with statement, i.e.

        with IMDB(file) as db:
            pass
        """
        self.open()
        return self

    def __exit__(self, *args) -> None:
        """Defining __enter__ and __exit__ allows
        the class to be used as a with statement, i.e.

        with IMDB(file) as db:
            pass
        """
        self.close()

    @check_open(writeable=True)
    def write_attributes(self, **kwargs) -> None:
        """Stores attributes in the root of the h5 db

        Note: string values have to be encoded using np.string_
        """
        # Custom attributes
        for key, value in kwargs.items():
            if value is not None:
                self._db.root._v_attrs[key] = (
                    np.string_(value) if isinstance(value, str) else value
                )

        # Generic attributes
        if not "date_created" in self._db.root._v_attrs._f_list():
            self._db.root._v_attrs.date_created = np.datetime64("now")
            self._db.root._v_attrs.numpy_version = np.string_(np.__version__)
            self._db.root._v_attrs.pandas_version = np.string_(pd.__version__)
            self._db.root._v_attrs.pytables_version = np.string_(tables.__version__)
        else:
            self._db.root._v_attrs[
                f"date_modified_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ] = np.datetime64("now")

    @check_open
    def get_attributes(self):
        """Gets the root attributes of the h5 db"""
        result = {}
        for key in self._db.root._v_attrs._f_list():
            value = self._db.root._v_attrs[key]
            result[key] = value.decode() if isinstance(value, np.bytes_) else value
        return result

    def open(self) -> None:
        """Opens the database"""
        mode = "a" if self.writeable else "r"
        self._db = pd.HDFStore(self.db_ffp, mode=mode)

    def close(self) -> None:
        """Close opened database"""
        self._db.close()
        self._db = None

    @contextmanager
    def use_db(self) -> "BaseDB":
        yield self._db.open()
        self.close()
