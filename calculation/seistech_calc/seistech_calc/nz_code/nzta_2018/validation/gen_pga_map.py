import pandas as pd
import os, sys

from c01000 import get_pga_and_meff, get_c_01000
from subprocess import PIPE, Popen
from qcore.shared import exe

try:
    from visualization import gmt
except ModuleNotFoundError:
    print("visualization.gmt is missing..generating command instead")
    PLOT_ITEMS_PATH = None
else:
    PLOT_ITEMS_PATH = os.path.join(gmt.__path__._path[0], "plot_items.py")
    print(
        "visualization.gmt is found at {}..can plot".format(
            os.path.dirname(PLOT_ITEMS_PATH)
        )
    )

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
GRID_FILE = "400m_land1500k.ll"
if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("return_period", type=int)
    parser.add_argument(
        "vs30", type=float
    )  # we assume we have a constant vs30 for all locations
    parser.add_argument(
        "--c01000", help="Generate C_0,1000 Map instead of PGA", action="store_true"
    )
    parser.add_argument("--grid-file", default=os.path.join(DATA, GRID_FILE))
    parser.add_argument(
        "--plot-items-path",
        help="Give a full path to plot_items.py",
        default=PLOT_ITEMS_PATH,
    )
    args = parser.parse_args()

    if args.plot_items_path is not None and not os.path.exists(args.plot_items_path):
        print(
            "Warning: plot_items.py is not available at the specified path..generating command instead"
        )
        args.plot_items_path = None

    if args.grid_file != os.path.join(DATA, GRID_FILE):
        args.grid_file = os.path.abspath(os.path.join(os.path.curdir, args.grid_file))
        if not os.path.exists(args.grid_file):
            print("Error: Grid file does not exists: {}".format(args.grid_file))
            sys.exit()

    stations_df = pd.read_csv(
        os.path.join(DATA, args.grid_file),
        sep=" ",
        names=["lon", "lat", "station"],
        header=None,
        index_col=2,
    )

    result = []

    if args.c01000:
        result = [
            get_c_01000(station.lat, station.lon, args.vs30)[0]
            for _, station in stations_df.iterrows()
        ]
        name = "C01000"
        label = "C0,1000 for vs30={}".format(args.vs30)
    else:
        result = [
            get_pga_and_meff(station.lat, station.lon, args.vs30, args.return_period)[0]
            for _, station in stations_df.iterrows()
        ]
        name = "PGA"
        label = "PGA (RP={}yrs vs30={})".format(args.return_period, args.vs30)

    xyz_df = pd.DataFrame(
        data={
            "lon": stations_df.lon.values,
            "lat": stations_df.lat.values,
            "{}".format(name): result,
        }
    )

    output_file = "NZTA_{}_{}".format(
        name, os.path.basename(args.grid_file).split(".ll")[0]
    )  # take the grid file name (ie. no dirname, no extname)
    xyz_df.to_csv("{}.xyz".format(output_file), sep=" ", header=None, index=None)

    cmd = [
        "--xyz",
        output_file + ".xyz",
        "-t",
        '"{}"'.format(label),
        "--xyz-cpt-labels",
        "{}".format(name),
        "-f",
        output_file,
        "--xyz-landmask",
        "--xyz-cpt",
        "hot",
        "--xyz-transparency",
        "10",
        "--xyz-size",
        "0.02",
        "--xyz-shape",
        "s",
        "--xyz-cpt-invert",
        "-n",
        "16",
    ]

    if args.plot_items_path is not None:
        cmd = ["python", args.plot_items_path] + cmd
        exe(cmd, debug=True)
    else:
        print(
            "copy {}.xyz and following command to where plot_items(+gmt) is available".format(
                output_file
            )
        )
        print("--------------------------------------------------------")
        print("plot_items.py {}".format(" ".join(cmd)))
