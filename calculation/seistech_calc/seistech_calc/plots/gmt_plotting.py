import math
from io import BytesIO
from shutil import copyfile, rmtree
from tempfile import mkdtemp
from typing import Dict
from pathlib import Path

import numpy as np

from qcore import geo


def plot_site_vs30(
    out_ffp: str,
    site_lon: float,
    site_lat: float,
    station_lon: float,
    station_lat: float,
    station_vs30: float,
    station_ll_ffp: str,
    vs30_grid_ffp: str,
    site_vs30: float = None,
    distance: float = 8,
):
    from qcore import gmt

    max_lat = geo.ll_shift(site_lat, site_lon, distance, 0)[0]
    min_lon = geo.ll_shift(site_lat, site_lon, distance, -90)[1]
    min_lat = site_lat - (max_lat - site_lat)
    max_lon = site_lon + (site_lon - min_lon)
    region = (min_lon, max_lon, min_lat, max_lat)

    # automatic label positioning, doesn't work over geographic quadrants
    if abs(site_lat - station_lat) > abs(site_lon - station_lon):
        # labels above/below
        dx = 0
        if site_lat > station_lat:
            # site label above, closest site label below
            site_align = "CB"
            closest_align = "CT"
            dy = 0.12
        else:
            # opposite
            site_align = "CT"
            closest_align = "CB"
            dy = -0.12
    else:
        # labels to the side
        dy = 0
        if site_lon > station_lon:
            # site label to right, closest site label to left
            site_align = "LM"
            closest_align = "RM"
            dx = -0.12
        else:
            # opposite
            site_align = "RM"
            closest_align = "LM"
            dx = 0.12

    wd = mkdtemp()
    img = Path(wd) / "snapped_station"
    cpt = Path(wd) / "vs30.cpt"
    p = gmt.GMTPlot(str(img) + ".ps")
    p.spacial("M", region, sizing=9, x_shift=1, y_shift=2)
    gmt.makecpt("rainbow", str(cpt), 100, 800, continuing=True)
    p.overlay(vs30_grid_ffp, cpt=str(cpt))
    p.points(station_ll_ffp, shape="s", size=0.2, line_thickness="2p", line="black")

    p.points(
        f"{site_lon} {site_lat}\n",
        is_file=False,
        shape="c",
        fill="black",
        size=0.1,
        line="white",
        line_thickness="1p",
    )
    p.points(
        f"{station_lon} {station_lat}\n",
        is_file=False,
        shape="c",
        size=0.2,
        line_thickness="2p",
        line="white",
    )
    p.text(
        site_lon,
        site_lat,
        "site",
        dx=-dx,
        dy=dy,
        align=site_align,
        size="14p",
        box_fill="white@40",
    )
    p.text(
        station_lon,
        station_lat,
        "closest station",
        dx=dx * 1.5,
        dy=-dy * 1.5,
        align=closest_align,
        size="14p",
        box_fill="white@40",
    )
    p.text(
        min_lon,
        min_lat,
        f"Site Vs30: {site_vs30} {'m/s' * (site_vs30 is not None)}",
        size="20p",
        align="LB",
        dx=0.2,
        dy=0.8,
        box_fill="white@40",
    )
    p.text(
        min_lon,
        min_lat,
        f"Closest Site Vs30: {station_vs30} m/s",
        size="20p",
        align="LB",
        dx=0.2,
        dy=0.5,
        box_fill="white@40",
    )
    p.text(
        min_lon,
        min_lat,
        f"Distance: {geo.ll_dist(station_lon, station_lat, site_lon, site_lat):.2f} km",
        size="20p",
        align="LB",
        dx=0.2,
        dy=0.2,
        box_fill="white@40",
    )

    p.ticks(major="0.05d", minor="0.01d")
    p.cpt_scale(
        "R",
        "M",
        cpt,
        pos="rel_out",
        dx=0.2,
        label="Vs30 (m/s)",
        major=100,
        minor=10,
        horiz=False,
    )
    p.finalise()
    p.png(background="white")

    copyfile(str(img) + ".png", out_ffp)
    rmtree(wd)


def plot_context(
    lon: float,
    lat: float,
    out_ffp_no_ext: str,
    fault_corners_ffp: str = None,
    bballs_ffp: str = None,
):
    """Creates a gmt context map

    Parameters
    ----------
    lon: float
    lat: float
    out_ffp_no_ext: str
        Output file path, no extension...
    fault_corners_ffp: str, optional
        Path to the fault corners csv file
    bballs_ffp: str, optional
        Path to the beach ball csv file
    """
    from qcore import gmt

    script_dir = Path(__file__).resolve().parent
    if fault_corners_ffp is None:
        fault_corners_ffp = Path(script_dir).parent / "resources" / "SimAtlasFaults.csv"
    if bballs_ffp is None:
        bballs_ffp = Path(script_dir).parent / "resources" / "gmt.bb"

    mom2mag = lambda mom: (2 / 3.0 * math.log(mom) / math.log(10.0)) - 10.7

    wd = mkdtemp()
    p = gmt.GMTPlot(str(Path(wd) / f"{Path(out_ffp_no_ext).name}.ps"))
    # in a future release of GMT, this might be possible
    # p.spacial("M" + str(args.lon) + "/" + str(args.lat) + "/", ("-200", "200", "-200", "200+uk"), sizing=8, x_shift=2, y_shift=2)
    p.spacial(
        "M", (lon - 1.3, lon + 1.3, lat - 1, lat + 1), sizing=8, x_shift=1, y_shift=1
    )
    p.basemap()
    p.water()

    paths = []
    with fault_corners_ffp.open(mode="r") as c:
        c.readline()
        for l in c:
            paths.append(
                l.split(",")[9]
                .replace("]|", "\n")
                .replace("|", " ")
                .replace("[[", ">\n")
                .replace("[", "")
                .replace("]", "")
                .replace("\n ", "\n")
            )
    paths = "".join(paths)
    p.path(
        paths,
        is_file=False,
        close=True,
        colour="black",
        width="1.0p",
        cols="1,0",
        split="-",
    )
    paths = "\n".join([">\n" + "\n".join(x.split("\n")[1:3]) for x in paths.split(">")])
    p.path(paths, is_file=False, colour="black", width="1.5p", cols="1,0")

    p.ticks()

    # beachballs by magnitude
    b5 = []
    b56 = []
    b6 = []
    with bballs_ffp.open(mode="r") as b:
        for l in b:
            man, exp = map(float, l.split()[9:11])
            mag = mom2mag(man * 10 ** exp)
            if mag < 5:
                b5.append(l)
            elif mag < 6:
                b56.append(l)
            else:
                b6.append(l)
    if len(b5) > 0:
        p.beachballs("\n".join(b5), scale=0.2, colour="blue")
    if len(b56) > 0:
        p.beachballs("\n".join(b56), scale=0.2, colour="orange")
    if len(b6) > 0:
        p.beachballs("\n".join(b6), scale=0.2, colour="red")

    p.points(
        f"{lon} {lat}\n",
        is_file=False,
        shape="c",
        fill="black",
        size=0.1,
        line="white",
        line_thickness="1p",
    )
    p.text(lon, lat, "site", dy=-0.12, align="CT", size="14p", box_fill="white@40")
    p.dist_scale("R", "B", "25", pos="rel", dx=0.5, dy=0.5)

    p.finalise()
    p.png(out_dir=str(Path(out_ffp_no_ext).parent), clip=True)
    rmtree(wd)


def plot_disagg(
    out_ffp_no_ext: str, disagg_data: Dict, dpi: int = 300, bin_type: str = "src"
) -> None:
    """
    Creates a gmt based disagg plot

    Parameters
    ----------
    out_ffp_no_ext: string
        Output file path, don't include the file extension...
    disagg_data: Dictionary
        The disagg grid data as dictionary
    dpi: int
    bin_type: str
        The type of binning to use for the disagg plot,
        either "src" (i.e. Fault and DS) or "eps"
    """
    from qcore import gmt

    # Constants
    X_LEN = 4.5
    Y_LEN = 4.0
    Z_LEN = 2.5
    ROT = 30
    TILT = 60
    LEGEND_SPACE = 0.7
    EPSILON_LEGEND_EXPAND = 1.0
    EPSILON_COLOURS = [
        "215/38/3",
        "252/94/62",
        "252/180/158",
        "254/220/210",
        "217/217/255",
        "151/151/255",
        "0/0/255",
        "0/0/170",
    ]
    EPSILON_LABELS = [
        "@~e@~<-2",
        "-2<@~e@~<-1",
        "-1<@~e@~<-0.5",
        "-0.5<@~e@~<0",
        "0<@~e@~<0.5",
        "0.5<@~e@~<1",
        "1<@~e@~<2",
        "2<@~e@~",
    ]
    TYPE_LEGEND_EXPAND = 0.35
    TYPE_COLOURS = ["blue", "green"]
    TYPE_LABELS = ["Fault", "DS"]

    out_dir = Path(out_ffp_no_ext).parent
    out_name = Path(out_ffp_no_ext).name

    rrup_edges = np.asarray(disagg_data["rrup_edges"])
    mag_edges = np.asarray(disagg_data["mag_edges"])

    # modifications based on plot type selection
    if bin_type == "src":
        colours = TYPE_COLOURS
        labels = TYPE_LABELS
        legend_expand = TYPE_LEGEND_EXPAND
    else:
        colours = EPSILON_COLOURS
        labels = EPSILON_LABELS
        legend_expand = EPSILON_LEGEND_EXPAND

    ###
    ### PROCESS DATA
    ###
    # x axis
    x_axis_max = max(rrup_edges)
    if x_axis_max < 115:
        x_tick_inc = 10
    elif x_axis_max < 225:
        x_tick_inc = 20
    elif x_axis_max < 335:
        x_tick_inc = 30
    elif x_axis_max < 445:
        x_tick_inc = 40
    else:
        x_tick_inc = 50
    x_axis_max = math.ceil(x_axis_max / float(x_tick_inc)) * x_tick_inc

    # y axis
    y_min, y_max = mag_edges[0], mag_edges[-1]
    if y_max - y_min < 5:
        y_tick_inc = 0.5
    else:
        y_tick_inc = 1.0

    # bins to put data in
    # TODO: set bottom limit on x and y (not e)
    bin_centres_rrup = rrup_edges[:-1] + (np.diff(rrup_edges) / 2.0)
    bin_centre_mag = mag_edges[:-1] + (np.diff(mag_edges) / 2.0)
    bins_e = np.array([-2, -1, -0.5, 0, 0.5, 1, 2, np.inf])

    # build gmt input lines from block data
    gmt_in = BytesIO()
    if bin_type == "src":
        blocks_flt = np.array(disagg_data["flt_bin_contr"])
        blocks_ds = np.array(disagg_data["ds_bin_contr"])
        # sum to 100
        factor = 100 / (np.sum(blocks_flt) + np.sum(blocks_ds))
        blocks_flt *= factor
        blocks_ds *= factor
        for y in range(len(bin_centre_mag)):
            for x in range(len(bin_centres_rrup)):
                if blocks_flt[y, x] > 0:
                    base = blocks_flt[y, x]
                    gmt_in.write(
                        f"{bin_centres_rrup[x]} {bin_centre_mag[y]} {base} {0} {0}\n".encode()
                    )
                else:
                    base = 0
                if blocks_ds[y, x] > 0:
                    gmt_in.write(
                        f"{bin_centres_rrup[x]} {bin_centre_mag[y]} {base + blocks_ds[y, x]} {2} {base}\n".encode()
                    )
        # z axis depends on max contribution tower
        z_tick_inc = int(math.ceil(np.max(blocks_flt + blocks_ds) / 5.0))
        z_max = z_tick_inc * 5
        del blocks_flt, blocks_ds
    else:
        blocks = np.array(disagg_data["eps_bin_contr"])
        # sum to 100
        blocks *= 100 / np.sum(blocks)
        for z in range(len(bins_e)):
            for y in range(len(bin_centre_mag)):
                for x in range(len(bin_centres_rrup)):
                    if blocks[z, y, x] > 0:
                        base = sum(blocks[:z, y, x])
                        gmt_in.write(
                            f"{bin_centres_rrup[x]} {bin_centre_mag[y]} {base + blocks[z, y, x]} {z} {base}\n".encode()
                        )
        # z axis depends on max contribution tower
        z_tick_inc = int(math.ceil(np.max(np.add.reduce(blocks, axis=0)) / 5.0))
        z_max = z_tick_inc * 5
        del blocks

    ###
    ### PLOT AXES
    ###
    wd = mkdtemp()
    p = gmt.GMTPlot("%s.ps" % str(Path(wd) / out_name))
    f = Path(wd) / "gmt.conf"
    f.unlink(missing_ok=True)

    # setup axes
    p.spacial(
        "X",
        (0, x_axis_max, y_min, y_max, 0, z_max),
        sizing="%si/%si" % (X_LEN, Y_LEN),
        z="Z%si" % (Z_LEN),
        p="%s/%s" % (180 - ROT, 90 - TILT),
        x_shift="5",
        y_shift=5,
    )
    p.ticks_multi(
        [
            "xa%s+lRupture Distance (km)" % (x_tick_inc),
            "ya%s+lMagnitude" % (y_tick_inc),
            "za%sg%s+l%%Contribution" % (z_tick_inc, z_tick_inc),
            "wESnZ",
        ]
    )
    # GMT will not plot gridlines without box, manually add gridlines
    gridlines = []
    for z in range(z_tick_inc, z_max + z_tick_inc, z_tick_inc):
        gridlines.append(
            "0 %s %s\n0 %s %s\n%s %s %s" % (y_min, z, y_max, z, x_axis_max, y_max, z)
        )
    gridlines.append("0 %s 0\n0 %s %s" % (y_max, y_max, z_max))
    gridlines.append(
        "%s %s 0\n%s %s %s" % (x_axis_max, y_max, x_axis_max, y_max, z_max)
    )
    p.path("\n>\n".join(gridlines), is_file=False, width="0.5p", z=True)

    ###
    ### PLOT CONTENTS
    ###
    cpt = Path(wd) / "z.cpt"
    gmt.makecpt(",".join(colours), str(cpt), 0, len(colours), inc=1, wd=wd)
    p.points(
        gmt_in.getvalue().decode(),
        is_file=False,
        z=True,
        line="black",
        shape="o",
        size=f"{float(X_LEN) / len(bin_centres_rrup) - 0.05}i/{float(Y_LEN) / len(bin_centres_rrup) - 0.05}ib",
        line_thickness="0.5p",
        cpt=str(cpt),
    )

    ###
    ### PLOT LEGEND
    ###
    # x y diffs from start to end, alternatively run multiple GMT commands with -X
    angle = math.radians(ROT)
    map_width = math.cos(angle) * X_LEN + math.sin(angle) * Y_LEN
    x_end = (
        (X_LEN + math.cos(angle) * math.sin(angle) * (Y_LEN - math.tan(angle) * X_LEN))
        / X_LEN
        * x_axis_max
        * legend_expand
    )
    y_end = math.tan(angle) * x_end / x_axis_max * X_LEN * (y_max - y_min) / Y_LEN
    # x y diffs at start, alternatively set -D(dz)
    x_shift = map_width * (legend_expand - 1) * -0.5
    y_shift = (LEGEND_SPACE) / math.cos(math.radians(TILT)) + X_LEN * math.sin(angle)
    x0 = (y_shift * math.sin(angle) + x_shift * math.cos(angle)) * (x_axis_max / X_LEN)
    y0 = y_min + (-y_shift * math.cos(angle) + x_shift * math.sin(angle)) * (
        (y_max - y_min) / Y_LEN
    )
    # legend definitions
    legend_boxes = []
    legend_labels = []
    for i, x in enumerate(np.arange(0, 1.01, 1.0 / (len(colours) - 1.0))):
        legend_boxes.append(
            "%s %s %s %s" % (x0 + x * x_end, y0 + x * y_end, z_tick_inc / 2.0, i)
        )
        legend_labels.append("%s 0 %s" % (x, labels[i]))
    # cubes and labels of legend
    p.points(
        "\n".join(legend_boxes),
        is_file=False,
        z=True,
        line="black",
        shape="o",
        size="%si/%sib0" % (Z_LEN / 10.0, Z_LEN / 10.0),
        line_thickness="0.5p",
        cpt=str(cpt),
        clip=False,
    )
    p.spacial(
        "X",
        (0, 1, 0, 1),
        sizing="%si/1i" % (map_width * legend_expand),
        x_shift="%si" % (x_shift),
        y_shift="-%si" % (LEGEND_SPACE + 0.2),
    )
    p.text_multi("\n".join(legend_labels), is_file=False, justify="CT")

    ###
    ### SAVE
    ###
    p.finalise()
    p.png(
        portrait=True,
        background="white",
        dpi=dpi,
        out_dir=str(out_dir),
        margin=[0.618, 1],
    )
    rmtree(wd)
