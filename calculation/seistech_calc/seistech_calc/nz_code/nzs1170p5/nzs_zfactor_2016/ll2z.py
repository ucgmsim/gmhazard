#!/usr/bin/env python

import os

from matplotlib.path import Path
import numpy as np
import pandas as pd
from scipy.interpolate import griddata

from qcore import geo

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zdata")

# constant regions and max bounds for faster processing
POLYGONS = [
    (os.path.join(DATA, "AucklandPolgonOutline_Points_WGS84.txt"), 0.13),
    (os.path.join(DATA, "ChristchurchPolgonOutline_Points_WGS84.txt"), 0.3),
    (os.path.join(DATA, "NorthlandPolgonOutline_Points_WGS84.txt"), 0.1),
]

CITY_RADIUS_SEARCH = 2

# contours
Z_VALS = [0.13, 0.15, 0.175, 0.188, 0.20, 0.25, 0.275, 0.30, 0.325, 0.35, 0.375, 0.40, 0.415, 0.425, 0.45, 0.475, 0.50, 0.525, 0.55, 0.575, 0.60]
Z_FORMAT = os.path.join(DATA, "Z_%.3f_points_WGS84.txt")


def ll2z(locations, radius_search=CITY_RADIUS_SEARCH):
    """Computes the z-value for the given lon, lat tuple or
     list of lon, lat tuples
    :param locations:
    :param radius_search: Checks to see if a city is within X km from the given location,
                          removes the search if value is set to 0
    :return: Array of z-values, one for each location specified
    """
    try:
        multi = bool(len(locations[0]))
    except TypeError:
        multi = False
        locations = [locations]
    out = np.zeros(len(locations))

    # check if in polygon
    for p in POLYGONS:
        c = Path(
            geo.path_from_corners(
                corners=np.loadtxt(p[0]).tolist(), output=None, min_edge_points=4
            )
        ).contains_points(locations)
        out = np.where(c, p[1], out)

    # check if within specified radius from city
    if radius_search > 0:
        cities = pd.read_csv(os.path.join(DATA, 'cities_z.csv'), header=None, names=['lon', 'lat', 'city', 'z_value'])

        cities_ll = cities[['lon', 'lat']].values
        for i, location in enumerate(locations):
            dists = geo.get_distances(cities_ll, location[0], location[1])

            if np.any(dists < radius_search):
                cities['dist'] = dists
                city_idx = cities.dist.idxmin()
                out[i] = cities.loc[city_idx].z_value

    # interpolate contours
    nz = []
    points_all = []
    for z in Z_VALS:
        points = np.atleast_2d(np.loadtxt(Z_FORMAT % z))
        nz.append(len(points))
        points_all.append(points)
    points = np.concatenate(points_all)
    del points_all
    z = griddata(points, np.repeat(Z_VALS, nz), locations, method="linear")

    return np.where(out == 0, np.where(np.isnan(z), 0.13, z), out)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("lon", type=float)
    parser.add_argument("lat", type=float)
    a = parser.parse_args()
    print(ll2z((a.lon, a.lat)))
