import json
from pathlib import Path

import numpy as np


class SiteInfo:
    """Contains information for a single site

    Note: SiteInfo objects should only every
    be created for station locations
    and by the Site module

    Parameters
    ----------
    station_name: str
    lat: float
    lon: float
    db_vs30: float
    user_vs30: float, optional
    z1p0: float, optional
    z2p5: float, optional

    Attributes
    ----------
    station_name : str
        Station name
    lat: float
    lon: float
    vs30: float
        The vs30 value to be used at this site
    user_vs30: float
        A user specified vs30, which potentially differs from the one used
    db_vs30: float
        A vs30 value specified by the db for this sites location
    z1p0: float
        A specified depth for vs30=1000 in Km's
    z2p5: float
        A specified depth for vs30=2500 in Km's
    """

    def __init__(
        self,
        station_name: str,
        lat: float,
        lon: float,
        db_vs30: float,
        user_vs30: float = None,
        z1p0: float = None,
        z2p5: float = None,
    ):
        self._station_name = station_name
        self._lat, self._lon = lat, lon
        self._vs30 = db_vs30 if user_vs30 is None else user_vs30
        self._user_vs30 = user_vs30
        self._db_vs30 = db_vs30
        self._z1p0 = z1p0
        self._z2p5 = z2p5

    @property
    def station_name(self):
        return self._station_name

    @property
    def lat(self):
        return self._lat

    @property
    def lon(self):
        return self._lon

    @property
    def vs30(self):
        return self._vs30

    @property
    def user_vs30(self):
        return self._user_vs30

    @property
    def db_vs30(self):
        return self._db_vs30

    @property
    def z1p0(self):
        return self._z1p0

    @property
    def z2p5(self):
        return self._z2p5

    def __str__(self):
        return f"{self.lon}_{self.lat}_{self.vs30}_{self._user_vs30}_{self._db_vs30}_{self._z1p0}_{self._z2p5}"

    def save(self, save_dir: Path):
        with open(save_dir / "site.json", "w") as f:
            json.dump(
                {
                    "station_name": self._station_name,
                    "lat": float(self._lat),
                    "lon": float(self._lon),
                    "vs30": float(self._vs30),
                    "user_vs30": float(self._user_vs30)
                    if self._user_vs30 is not None
                    else None,
                    "z1p0": None
                    if self._z1p0 is None or np.isnan(self._z1p0)
                    else float(self._z1p0),
                    "z2p5": None
                    if self._z2p5 is None or np.isnan(self._z2p5)
                    else float(self._z2p5),
                    "db_vs30": float(self._db_vs30),
                },
                f,
            )

    @classmethod
    def load(cls, data_dir: Path):
        with open(data_dir / "site.json", "r") as f:
            data = json.load(f)

        return cls(
            data["station_name"],
            data["lat"],
            data["lon"],
            data["vs30"],
            data["user_vs30"],
            data["z1p0"],
            data["z2p5"],
        )
