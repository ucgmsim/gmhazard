import h5py
import numpy as np
import numpy.matlib
import math
import matplotlib.pyplot as plt
from typing import List, Union, Tuple

from IM_calculation.source_site_dist import src_site_dist
from qcore import srf, geo

m = 7.2  # Moment magnitude, 5<=m<=8. 1x1 double.
u = np.arange(-90, 140.5, 0.5).tolist()
t = [
    -80
] * 461  # The GC2 coordinates in km. Must both be nX1 doubles where n is the number of locations at which the model provides a prediction. Must be columnar.
s_max = [
    -10,
    70,
]  # The maximum possible values of s for the scenario in km. 1x2 double with the first element corresponding to the maximum s in the antistrike direction (defined to be a negative value) and the second element the maximum in the strike direction (positive value).
d = 10  # The effective rupture travel width, measured from the hypocenter to the shallowest depth of the rupture plane, up-dip (km). 1x1 double.
t_bot = 0  # The t ordinate of the bottom of the rupture plane (projected to the surface) in km. 1x1 double.
# The vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km. 1x1 double.
d_bot = 15
rake = 0

dip = 90  # The characteristic rupture rake and dip angles, in degrees. 1x1 doubles. -180<=rake<=180 and dip<=90
force_type = 0  # A flag for determining the SOF category. 0->select SOF based on rake angle. 1->force SOF=1. 2->force SOF=2. 1x1 double.
period = 3  # The spectral period for which fD is requested, in sec. 0.01<period<10. 1x1 double.

# WIP
# def get_directivity_effects():
#     """Calcualtes directivity effects at the given site"""
#
#     # srf_file = "/isilon/cybershake/v20p4/Sources/scale_wlg_ nobackup/filesets/nobackup/nesi00213/RunFolder/jpa198/cybershake_sources/Data/Sources/AlpineK2T/Srf/AlpineK2T_REL01.srf"
#     srf_file = "/home/joel/local/AlpineK2T_REL01.srf"
#
#     planes = srf.read_header(srf_file, idx=True)
#     planes_list, planes_index = set_hypocenters(10, planes, [0.5])
#
#     points, rake = get_srf_values(srf_file)
#
#     lat_lon_depth = np.asarray([[x["lat"], x["lon"], x["depth"]] for x in points])
#     site_loc = np.asarray([[-41.713595, 173.090279], [-41.613595, 173.090279]])
#
#     fdi_list = []
#
#     for index, planes in planes_list:
#
#         rx, ry = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, site_loc, hypocentre_origin=True
#         )
#
#         nominal_strike, nominal_strike2 = calc_nominal_strike(lat_lon_depth)
#
#         rx_end, _ = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, nominal_strike, hypocentre_origin=True
#         )
#         rx_end2, _ = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, nominal_strike2, hypocentre_origin=True
#         )
#
#         s_max = [min(rx_end, rx_end2)[0], max(rx_end, rx_end2)[0]]
#
#         z_tor = planes[index]["dtop"]
#
#         dip = planes[index]["dip"]
#         d_bot = z_tor + planes[index]["width"] * math.sin(dip)
#         t_bot = z_tor / math.tan(dip) + planes[index]["width"] * math.cos(dip)
#         d = (planes[index]["dhyp"] - z_tor) / math.sin(dip)
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             m, rx, ry, s_max, d, t_bot, d_bot, rake, dip, force_type, period
#         )
#
#         fdi_list.append(fdi)
#
#     return fdi_list


def set_hypocenters(n_hypo: int, planes: List, depth_method: List):
    """
    Creates a List of planes each with a different set hypocenter for directivity calculations
    Sets n_hypo amount of hypocenters across the planes evenly

    Parameters
    ----------
    n_hypo: int
        Number of hypocenters across strike to set
    planes: list
        The planes to adjust and set the hypocenter on
    depth_method: List
        How deep the hypocenter is to be placed e.g. [0.5] would be every hypocenter at 50% depth
        where as [0.33, 0.66] would be every 2nd hypocenter would have a depth of 66% and every other would have 33%
    """

    # Gets the total length and removes any previous hypocenters
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    # Works out the distances across the length of the fault for each hypocenter
    distances = [(total_length/n_hypo * x) - ((total_length/n_hypo)/2) for x in range(1, n_hypo+1)]

    depth_index = 0
    planes_list = []
    planes_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if current_length < distance and (current_length + plane["length"]) > distance:
                plane["shyp"] = distance - (current_length + plane["length"] / 2)
                plane["dhyp"] = plane["width"] * depth_method[depth_index]
                depth_index = (depth_index + 1) % len(depth_method)
                planes_index.append(index)
            current_length += plane["length"]
        planes_list.append(planes_copy)
    return planes_list, planes_index


def calc_nominal_strike(traces):
    """Gets the start and ending trace of the fault and ensures order for largest lat value first"""
    depth = traces[0][2]
    trace_end_index = 0
    for index, trace in enumerate(traces):
        if depth != trace[2]:
            trace_end_index = index -1
            break
    trace_start, trace_end = [traces[0][0], traces[0][1]], [
        traces[trace_end_index][0],
        traces[trace_end_index][1],
    ]
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])


def get_rake_value(srf_file: str, lat: float, lon: float):
    """
    Gets the rake value at a given lat lon for a hypocenter
    Used for a more accurate representation of rake for the bea20 model

    Parameters
    ----------
    srf_file: str
        Fault srf file to read from
    lat: float
        The latitude value to extract rake from
    lon: float
        The Longitude value to extract rake from
    """
    with open(srf_file, "r") as sf:
        sf.readline()
        n_seg = int(sf.readline().split()[1])
        for _ in range(n_seg):
            sf.readline()
            sf.readline()
        n_point = int(sf.readline().split()[1])
        rake = 0  # If not found
        for _ in range(n_point):
            values = srf.get_lonlat(sf, "rake", True)
            if lat == values[1] and lon == values[0]:
                rake = values[3]
    return rake


def bea20(m: float, u: List, t: List, s_max: List, d: float, t_bot: float, d_bot: float, rake: float, dip: float, type: int, period: float):
    """
    Calculates the directivity effects at given locations based on fault information.
    Algorithm has been taken from the Bayless 2020 model found in the paper.
    "A Rupture Directivity Adjustment Model Applicable to the NGA-West2 Ground Motion Models and Complex Fault Geometries
    (Bayless 2020)".
    This functionality was compared to the matlab code taken from the paper.

    Parameters
    ----------
    m: float
        Moment magnitude, 5<=m<=8
    u: list
        The GC2 coordinates in km. Equivalent to ry.
        Must be nX1 number where n is the number of locations at which the model provides a prediction.
    t: list
        The GC2 coordinates in km. Equivalent to rx.
        Must be nX1 number where n is the number of locations at which the model provides a prediction.
    s_max: List
        List of 2x1 number where first is the lowest max value and the second is the largest max value for s.
        Computed from GC2 using nominal strike of the fault.
    d: float
        The effective rupture travel width, measured from the hypocenter to the shallowest depth of the rupture plane.
    t_bot: float
        The length of the bottom of the rupture plane (projected to the surface) in km.
    d_bot: float
        The vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km.
    rake: float
        The rake of the fault
    dip: float
        The dip of the fault at the hypocenter
    type: float
        1 for a strike slip
        2 for a oblique, reverse or normal
    period: float
        Used for specifying the period for a pSA IM
    """

    # If not specified, determine rupture category from rake angle
    if type == 0:
        if (-30 <= rake <= 30) or (-180 <= rake <= -150) or (150 <= rake <= 180):
            type = 1
        else:
            type = 2

    # Convert u to s
    # Limit s to the s_max values for positive and negative numbers
    s_max1, s_max2 = s_max
    u, s = np.asarray(u).copy(), np.asarray(u).copy()
    s[u < s_max1] = s_max1
    s[u > s_max2] = s_max2

    # Convert u to ry
    # Reduce each positive and negative side by absolute value of s_max and remove negative numbers inbetween
    pos, neg = u >= 0, u < 0
    ry = np.zeros(u.size)
    ry[pos] = u[pos] - s_max2
    ry[neg] = abs(u[neg]) - abs(s_max1)
    ry[ry < 0] = 0

    # Calculate S2
    if type == 2 and rake < 0:
        s = -s
    s_rake = s * math.cos(rake)
    d = max(d, 3)  # Gets the max value for d, 3 is the minimum
    s2 = s_rake ** 2 + d ** 2
    s2 = np.sqrt(s2)

    # Predictor variable fs2
    if type == 1:
        fs2 = np.log(s2)
        fs_cap = math.log(465)
        fs2[fs2 > fs_cap] = fs_cap
    else:
        fs2 = np.zeros(u.size)
        s_pos, s_neg = s_rake >= 0, s_rake < 0
        fs2[s_pos] = np.log(s2[s_pos])
        fs2[s_neg] = np.log(d)
        fs_cap = math.log(188)
        fs2[fs2 > fs_cap] = fs_cap

    # Angular predictor variables
    t = np.asarray(t)
    if type == 1:
        theta = np.nan_to_num(np.arctan(np.divide(t, u)))
        f_theta = abs(np.cos(2 * theta))
        fphi = np.ones(u.size)
    else:
        t_pos, t_neg = t > 0, t <= 0
        phi = np.zeros(u.size)

        phi[t_neg] = (
            np.degrees(np.arctan(np.divide(abs(t[t_neg]) + t_bot, d_bot))) + dip - 90
        )

        t1 = np.logical_and(t_pos, t < t_bot)
        phi[t1] = 90 - dip - np.degrees(np.arctan(np.divide(t_bot - t[t1], d_bot)))

        t2 = np.logical_and(t_pos, t >= t_bot)
        phi[t2] = 90 - dip + np.degrees(np.arctan(np.divide(t[t2] - t_bot, d_bot)))

        phi[phi > 45] = 45
        fphi = np.cos(2 * phi)

        t_min = 10 * (abs(math.cos(rake)) + 1)
        t2 = abs(t)
        t2[t2 < t_min] = t_min
        t2[t_pos] = t_min

        omega = np.arctan(np.divide(t2, ry))
        f_theta = np.nan_to_num(np.sin(omega), nan=1)

    # Distance taper
    r = np.sqrt(t ** 2 + ry ** 2)
    if m < 5:
        r_max = 40
    elif m > 7:
        r_max = 80
    else:
        r_max = -60 + 20 * m

    if type == 2:
        r_max = r_max - 20

    ar = -4 * r_max
    footprint = r <= r_max
    f_dist = np.zeros(r.size)
    f_dist[footprint] = 1 - np.exp(np.divide(ar, r[footprint]) - np.divide(ar, r_max))
    fg = fs2 * f_theta * fphi

    # Calculate fd

    # Constants
    per = np.logspace(-2, 1, 1000)
    coefb = [-0.0336, 0.5469]  # mag dependence of bmax
    coefc = [0.2858, -1.2090]  # mag scaling of Tpeak
    coefd1 = [0.9928, -4.8300]  # mag dependence of fG0 for SOF=1
    coefd2 = [0.3946, -1.5415]  # mag dependence of fG0 for SOF=2
    sigg = 0.4653

    # Impose the limits on m, Table 4-3
    if m > 8:
        m = 8
    elif m < 5.5:
        m = 5.5

    # Determine magnitude dependent parameters
    if type == 1:
        fg0 = coefd1[1] + coefd1[0] * m
    else:
        fg0 = coefd2[1] + coefd2[0] * m
    b_max = coefb[1] + coefb[0] * m
    t_peak = 10 ** (coefc[1] + coefc[0] * m)

    # Period dependent coefficients: a and b
    x = np.log10(np.divide(per, t_peak))
    b = b_max * np.exp(np.divide(-(x ** 2), 2 * sigg ** 2))
    a = -b * fg0

    # fd and fdi
    fd = (a + fg[:, np.newaxis] * b) * f_dist[:, np.newaxis]
    ti_array = abs(per - period)
    ti = np.where(ti_array == np.amin(ti_array))[0][0]
    fdi = fd[:, ti]

    phi_per = [0.01, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7.5, 10]
    e1 = [
        0.000,
        0.000,
        0.008,
        0.020,
        0.035,
        0.051,
        0.067,
        0.080,
        0.084,
        0.093,
        0.110,
        0.139,
        0.166,
        0.188,
        0.199,
    ]
    e1interp = np.interp(np.log(per), np.log(phi_per), e1)

    # phired and phiredi
    phi_red = np.matlib.repmat(e1interp, len(fd), 1)
    phi_red[np.invert(footprint), :] = 0
    phi_redi = phi_red[:, ti]

    predictor_functions = {
        "fg": fg,
        "fdist": f_dist,
        "ftheta": f_theta,
        "fphi": fphi,
        "fs2": fs2,
    }
    other = {
        "per": per,
        "rmax": r_max,
        "footprint": footprint,
        "tpeak": t_peak,
        "fg0": fg0,
        "bmax": b_max,
        "s2": s2,
    }

    return fd, fdi, phi_red, phi_redi, predictor_functions, other


# WIP (May not need)
# def directivity_plots():
#     t_base = -80
#     plot_s2 = None
#     for i in range(0, 461):
#         t = [t_base + i * 0.5] * 461
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             m, u, t, s_max, d, t_bot, d_bot, rake, dip, force_type, period
#         )
#
#         # If first run set all plotting variables
#         if plot_s2 is None:
#             plot_s2 = other["s2"][:, np.newaxis]
#             plot_fs2 = predictor_functions["fs2"][:, np.newaxis]
#             plot_ftheta = predictor_functions["ftheta"][:, np.newaxis]
#             plot_fg = predictor_functions["fg"][:, np.newaxis]
#             plot_fdist = predictor_functions["fdist"][:, np.newaxis]
#             plot_fdi = np.exp(fdi[:, np.newaxis])
#         else:
#             plot_s2 = np.append(plot_s2, other["s2"][:, np.newaxis], axis=1)
#             plot_fs2 = np.append(
#                 plot_fs2, predictor_functions["fs2"][:, np.newaxis], axis=1
#             )
#             plot_ftheta = np.append(
#                 plot_ftheta, predictor_functions["ftheta"][:, np.newaxis], axis=1
#             )
#             plot_fg = np.append(
#                 plot_fg, predictor_functions["fg"][:, np.newaxis], axis=1
#             )
#             plot_fdist = np.append(
#                 plot_fdist, predictor_functions["fdist"][:, np.newaxis], axis=1
#             )
#             plot_fdi = np.append(plot_fdi, np.exp(fdi[:, np.newaxis]), axis=1)
#
#     fig = plt.figure(figsize=(18, 12))
#
#     ax = fig.add_subplot(231)
#     ax2 = fig.add_subplot(232)
#     ax3 = fig.add_subplot(233)
#     ax4 = fig.add_subplot(234)
#     ax5 = fig.add_subplot(235)
#     ax6 = fig.add_subplot(236)
#
#     ax.set_title("S2")
#     ax.set_xlim(0, 320)
#     ax.matshow(plot_s2)
#
#     ax2.set_title("FS2")
#     ax2.set_xlim(0, 320)
#     ax2.matshow(plot_fs2)
#
#     ax3.set_title("F Theta")
#     ax3.set_xlim(0, 320)
#     ax3.matshow(plot_ftheta)
#
#     ax4.set_title("FG")
#     ax4.set_xlim(0, 320)
#     ax4.matshow(plot_fg)
#
#     ax5.set_title("F Dist")
#     ax5.set_xlim(0, 320)
#     ax5.matshow(plot_fdist)
#
#     ax6.set_title("FDI")
#     ax6.set_xlim(0, 320)
#     ax6.matshow(plot_fdi)

    # fig.savefig("/home/joel/local/fig_test.png")

# WIP
# def directivity_srf_plot():
#     # srf_file = "/home/joel/local/AlpineK2T_REL01.srf"
#     srf_file = "/home/joel/local/Hossack_REL01.srf"
#
#     planes = srf.read_header(srf_file, idx=True)
#     planes_list, planes_index = set_hypocenters(10, planes, [0.5])
#
#     points = srf.read_latlondepth(srf_file)
#
#     lat_lon_depth = np.asarray([[x["lat"], x["lon"], x["depth"]] for x in points])
#
#     lon_values = np.linspace(
#         lat_lon_depth[:, 0].min() - 1, lat_lon_depth[:, 0].max() + 1, 100
#     )
#     lat_values = np.linspace(
#         lat_lon_depth[:, 1].min() - 1, lat_lon_depth[:, 1].max() + 1, 100
#     )
#
#     x, y = np.meshgrid(lon_values, lat_values)
#     site_coords = np.stack((x, y), axis=2).reshape(-1, 2)
#
#     fdi_average = np.asarray([])
#
#     fig, (ax1) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
#
#     for index, planes in enumerate(planes_list):
#
#         plane_index = planes_index[index]
#
#         rx, ry = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, site_coords, hypocentre_origin=True
#         )
#
#         fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(21, 13.5), dpi=144)
#
#         ry_plot = np.asarray(ry).reshape(100, 100)
#         rx_plot = np.asarray(rx).reshape(100, 100)
#
#         levels = 20
#         ct = ax3.contourf(y, x, ry_plot, cmap="Reds_r", levels=levels)
#         ct2 = ax4.contourf(y, x, rx_plot, cmap="Reds_r", levels=levels)
#         ax3.set_title("GC2 ry")
#         ax4.set_title("GC2 rx")
#         fig.colorbar(ct, ax=ax3, pad=0.01)
#         fig.colorbar(ct2, ax=ax4, pad=0.01)
#         ax3.scatter(
#             lat_lon_depth[:, 1][::2],
#             lat_lon_depth[:, 0][::2],
#             c=lat_lon_depth[:, 2][::2],
#             label="srf points",
#             s=1.0,
#         )
#         ax4.scatter(
#             lat_lon_depth[:, 1][::2],
#             lat_lon_depth[:, 0][::2],
#             c=lat_lon_depth[:, 2][::2],
#             label="srf points",
#             s=1.0,
#         )
#
#         ax3.legend()
#         ax4.legend()
#
#         ax3.set_aspect('equal')
#         ax4.set_aspect('equal')
#
#         fig3.savefig(f"/home/joel/local/gc2_{index}.png")
#
#         nominal_strike, nominal_strike2 = calc_nominal_strike(lat_lon_depth)
#
#         rx_end, _ = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, nominal_strike, hypocentre_origin=True
#         )
#         rx_end2, _ = src_site_dist.calc_rx_ry_GC2(
#             lat_lon_depth, planes, nominal_strike2, hypocentre_origin=True
#         )
#
#         s_max = [min(rx_end, rx_end2)[0], max(rx_end, rx_end2)[0]]
#
#         z_tor = planes[plane_index]["dtop"]
#
#         dip = planes[plane_index]["dip"]
#         d_bot = z_tor + planes[plane_index]["width"] * math.sin(dip)
#         t_bot = z_tor / math.tan(dip) + planes[plane_index]["width"] * math.cos(dip)
#         d = (planes[plane_index]["dhyp"] - z_tor) / math.sin(dip)
#         hypo_lon, hypo_lat = srf.get_hypo(srf_file, custom_planes=remove_plane_idx(planes))
#         rake = get_rake_value(srf_file, hypo_lat, hypo_lon)
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             m, rx, ry, s_max, d, t_bot, d_bot, rake, dip, force_type, period
#         )
#
#         if fdi_average.size == 0:
#             fdi_average = fdi
#         else:
#             fdi_average = np.add(fdi_average, fdi)
#
#         fdi_values = np.asarray(fdi).reshape(100, 100)
#
#         fig2, (ax2) = plt.subplots(1, 1, figsize=(21, 13.5), dpi=144)
#
#         levels = 20
#         ct = ax2.contourf(y, x, fdi_values, cmap="Reds_r", levels=levels)
#         ax2.set_title("Fdi pSA_3.0")
#         fig.colorbar(ct, ax=ax2, pad=0.01)
#         ax2.scatter(
#             lat_lon_depth[:, 1][::2],
#             lat_lon_depth[:, 0][::2],
#             c=lat_lon_depth[:, 2][::2],
#             label="srf points",
#             s=1.0,
#         )
#         ax2.scatter(
#             hypo_lon,
#             hypo_lat,
#             label="Hypocentre",
#             marker="x",
#             c="k",
#             s=50.0,
#         )
#         ax2.legend()
#
#         fig2.savefig(f"/home/joel/local/directivity_hossack_hyp{index}.png")
#         ax1.scatter(
#             hypo_lon,
#             hypo_lat,
#             label="Hypocentre",
#             marker="x",
#             c="k",
#             s=50.0,
#         )
#
#     fdi_values = np.divide(np.asarray(fdi_average).reshape(100, 100), 10)
#
#     levels = 20
#     ct = ax1.contourf(y, x, fdi_values, cmap="Reds_r", levels=levels)
#     ax1.set_title("Fdi pSA_3.0")
#     fig.colorbar(ct, ax=ax1, pad=0.01)
#     ax1.scatter(
#         lat_lon_depth[:, 1][::2],
#         lat_lon_depth[:, 0][::2],
#         c=lat_lon_depth[:, 2][::2],
#         label="srf points",
#         s=1.0,
#     )
#     ax1.legend()
#
#     fig.savefig("/home/joel/local/directivity_hossack_full.png")
#
#     return fdi_average


def remove_plane_idx(planes: List):
    """
    Removes the idx from the plane

    Parameters
    ----------
    planes: List
        List of planes to remove the idx dict format from
    """
    new_planes = []
    for plane in planes:
        new_planes.append((
                    float(plane["centre"][0]),
                    float(plane["centre"][1]),
                    int(plane["nstrike"]),
                    int(plane["ndip"]),
                    float(plane["length"]),
                    float(plane["width"]),
                    plane["strike"],
                    plane["dip"],
                    plane["dtop"],
                    plane["shyp"],
                    plane["dhyp"],
                ))
    return new_planes

# output = bea20(m,u,t,s_max,d,t_bot,d_bot,rake,dip,force_type,period)
# directivity_plots()
# get_directivity_effects()
# directivity_srf_plot()
