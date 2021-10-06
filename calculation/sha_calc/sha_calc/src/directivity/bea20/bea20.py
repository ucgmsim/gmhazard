import h5py
import numpy as np
import numpy.matlib
import math
import matplotlib.pyplot as plt
from typing import List, Union, Tuple


# WIP
# def get_directivity_effects():
#     """Calculates directivity effects at the given site"""
#
#     # srf_file = "/isilon/cybershake/v20p4/Sources/scale_wlg_ nobackup/filesets/nobackup/nesi00213/RunFolder/jpa198/cybershake_sources/Data/Sources/AlpineK2T/Srf/AlpineK2T_REL01.srf"
#     srf_file = "/home/joel/local/AlpineK2T_REL01.srf"
#
#     planes = srf.read_header(srf_file, idx=True)
#     planes_list, planes_index = set_hypocenters(10, planes, [0.5])
#
#     points, Rake = get_srf_values(srf_file)
#
#     lon_lat_depth = np.asarray([[x["lat"], x["lon"], x["depth"]] for x in points])
#     site_loc = np.asarray([[-41.713595, 173.090279], [-41.613595, 173.090279]])
#
#     fdi_list = []
#
#     for index, planes in planes_list:
#
#         rx, ry = src_site_dist.calc_rx_ry_GC2(
#             lon_lat_depth, planes, site_loc, hypocentre_origin=True
#         )
#
#         nominal_strike, nominal_strike2 = calc_nominal_strike(lon_lat_depth)
#
#         rx_end, _ = src_site_dist.calc_rx_ry_GC2(
#             lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
#         )
#         rx_end2, _ = src_site_dist.calc_rx_ry_GC2(
#             lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
#         )
#
#         Smax = [min(rx_end, rx_end2)[0], max(rx_end, rx_end2)[0]]
#
#         z_tor = planes[index]["dtop"]
#
#         Dip = planes[index]["dip"]
#         Dbot = z_tor + planes[index]["width"] * math.sin(Dip)
#         Tbot = z_tor / math.tan(Dip) + planes[index]["width"] * math.cos(Dip)
#         D = (planes[index]["dhyp"] - z_tor) / math.sin(Dip)
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             M, rx, ry, Smax, D, Tbot, Dbot, Rake, Dip, force_type, period
#         )
#
#         fdi_list.append(fdi)
#
#     return fdi_list


def bea20(M: float, U: List, T: List, Smax: List, D: float, Tbot: float, Dbot: float, Rake: float, Dip: float, type: int, Period: float):
    """
    Calculates the directivity effects at given locations based on fault information.
    Algorithm has been taken from the Bayless 2020 model found in the paper.
    "A Rupture Directivity Adjustment Model Applicable to the NGA-West2 Ground Motion Models and Complex Fault Geometries
    (Bayless 2020)".
    This functionality was compared to the matlab code taken from the paper.

    Parameters
    ----------
    M: float
        Moment magnitude, 5<=M<=8
    U: list
        The GC2 coordinates in km. Equivalent to ry.
        Must be nX1 number where n is the number of locations at which the model provides a prediction.
    T: list
        The GC2 coordinates in km. Equivalent to rx.
        Must be nX1 number where n is the number of locations at which the model provides a prediction.
    Smax: List
        List of 2x1 number where first is the lowest max value and the second is the largest max value for s.
        Computed from GC2 using nominal strike of the fault.
    D: float
        The effective rupture travel width, measured from the hypocenter to the shallowest depth of the rupture plane.
    Tbot: float
        The length of the bottom of the rupture plane (projected to the surface) in km.
    Dbot: float
        The vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km.
    Rake: float
        The Rake of the fault
    Dip: float
        The Dip of the fault at the hypocenter
    type: float
        1 for a strike slip
        2 for a oblique, reverse or normal
    Period: float
        Used for specifying the period for a pSA IM
    """

    # If not specified, determine rupture category from Rake angle
    if type == 0:
        if (-30 <= Rake <= 30) or (-180 <= Rake <= -150) or (150 <= Rake <= 180):
            type = 1
        else:
            type = 2

    # Convert U to S
    # Limit S to the Smax values for positive and negative numbers
    Smax1, Smax2 = Smax
    U, S = np.asarray(U).copy(), np.asarray(U).copy()
    S[U < Smax1] = Smax1
    S[U > Smax2] = Smax2

    # Convert U to Ry
    # Reduce each positive and negative side by absolute value of Smax and remove negative numbers inbetween
    upos, uneg = U >= 0, U < 0
    Ry = np.zeros(U.size)
    Ry[upos] = U[upos] - Smax2
    Ry[uneg] = abs(U[uneg]) - abs(Smax1)
    Ry[Ry < 0] = 0

    # Calculate S2
    if type == 2 and Rake < 0:
        S = -S
    Srake = S * math.cos(math.radians(Rake))
    D = max(D, 3)  # Gets the max value for D, 3 is the minimum
    S2 = np.sqrt(Srake ** 2 + D ** 2)

    # Predictor variable fs2
    if type == 1:
        fs2 = np.log(S2)
        fsCap = math.log(465)
        fs2[fs2 > fsCap] = fsCap
    else:
        fs2 = np.zeros(U.size)
        spos, sneg = Srake >= 0, Srake < 0
        fs2[spos] = np.log(S2[spos])
        fs2[sneg] = np.log(D)
        fsCap = math.log(188)
        fs2[fs2 > fsCap] = fsCap

    # Angular predictor variables
    T = np.asarray(T).copy()
    if type == 1:
        theta = np.nan_to_num(np.arctan(np.divide(T, U)))
        ftheta = abs(np.cos(2 * theta))
        fphi = np.ones(U.size)
    else:
        tpos, tneg = T > 0, T <= 0
        phi = np.zeros(U.size)

        phi[tneg] = (
            np.degrees(np.arctan(np.divide(abs(T[tneg]) + Tbot, Dbot))) + Dip - 90
        )

        t1 = np.logical_and(tpos, T < Tbot)
        phi[t1] = 90 - Dip - np.degrees(np.arctan(np.divide(Tbot - T[t1], Dbot)))

        t2 = np.logical_and(tpos, T >= Tbot)
        phi[t2] = 90 - Dip + np.degrees(np.arctan(np.divide(T[t2] - Tbot, Dbot)))

        phi[phi > 45] = 45
        fphi = np.cos(2 * phi * np.pi / 180)

        Tmin = 10 * (abs(math.cos(math.radians(Rake))) + 1)
        T2 = abs(T)
        T2[T2 < Tmin] = Tmin
        T2[tpos] = Tmin

        omega = np.arctan(np.divide(T2, Ry))
        ftheta = np.nan_to_num(np.sin(omega), nan=1)

    # Distance taper
    R = np.sqrt(T ** 2 + Ry ** 2) # Distance from surface trace
    if M < 5:
        Rmax = 40
    elif M > 7:
        Rmax = 80
    else:
        Rmax = -60 + 20 * M

    if type == 2:
        Rmax = Rmax - 20

    AR = -4 * Rmax
    Footprint = R <= Rmax
    fdist = np.zeros(R.size)
    fdist[Footprint] = 1 - np.exp(np.divide(AR, R[Footprint]) - np.divide(AR, Rmax))
    fG = fs2 * ftheta * fphi

    # Calculate fD

    # Constants
    Per = np.logspace(-2, 1, 1000)
    coefb = [-0.0336, 0.5469]  # mag dependence of bmax
    coefc = [0.2858, -1.2090]  # mag scaling of Tpeak
    coefd1 = [0.9928, -4.8300]  # mag dependence of fG0 for SOF=1
    coefd2 = [0.3946, -1.5415]  # mag dependence of fG0 for SOF=2
    SigG = 0.4653

    # Impose the limits on M, Table 4-3
    if M > 8:
        M = 8
    elif M < 5.5:
        M = 5.5

    # Determine magnitude dependent parameters
    if type == 1:
        fG0 = coefd1[1] + coefd1[0] * M
    else:
        fG0 = coefd2[1] + coefd2[0] * M
    bmax = coefb[1] + coefb[0] * M
    Tpeak = 10 ** (coefc[1] + coefc[0] * M)

    # Period dependent coefficients: a and b
    x = np.log10(np.divide(Per, Tpeak))
    b = bmax * np.exp(np.divide(-(x ** 2), 2 * SigG ** 2))
    a = -b * fG0

    # fd and fdi
    fD = (a + fG[:, np.newaxis] * b) * fdist[:, np.newaxis]
    ti = np.argmin(np.abs(Per - Period))
    fDi = fD[:, ti]

    PhiPer = [0.01, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7.5, 10]
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
    e1interp = np.interp(np.log(Per), np.log(PhiPer), e1)

    # phired and phiredi
    PhiRed = np.matlib.repmat(e1interp, len(fD), 1)
    PhiRed[np.invert(Footprint), :] = 0
    PhiRedi = PhiRed[:, ti]

    predictor_functions = {
        "fG": fG,
        "fdist": fdist,
        "ftheta": ftheta,
        "fphi": fphi,
        "fs2": fs2,
    }
    other = {
        "Per": Per,
        "Rmax": Rmax,
        "Footprint": Footprint,
        "Tpeak": Tpeak,
        "fG0": fG0,
        "bmax": bmax,
        "S2": S2,
    }

    return fD, fDi, PhiRed, PhiRedi, predictor_functions, other


# WIP (May not need)
# def directivity_plots():
#     t_base = -80
#     plot_s2 = None
#     for i in range(0, 461):
#         T = [t_base + i * 0.5] * 461
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             M, U, T, Smax, D, Tbot, Dbot, Rake, Dip, force_type, Period
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
#     lon_lat_depth = np.asarray([[x["lat"], x["lon"], x["depth"]] for x in points])
#
#     lon_values = np.linspace(
#         lon_lat_depth[:, 0].min() - 1, lon_lat_depth[:, 0].max() + 1, 100
#     )
#     lat_values = np.linspace(
#         lon_lat_depth[:, 1].min() - 1, lon_lat_depth[:, 1].max() + 1, 100
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
#             lon_lat_depth, planes, site_coords, hypocentre_origin=True
#         )
#
#         fig3, (ax3, ax4) = plt.subplots(1, 2, figsize=(21, 13.5), dpi=144)
#
#         ry_plot = np.asarray(Ry).reshape(100, 100)
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
#             lon_lat_depth[:, 1][::2],
#             lon_lat_depth[:, 0][::2],
#             c=lon_lat_depth[:, 2][::2],
#             label="srf points",
#             s=1.0,
#         )
#         ax4.scatter(
#             lon_lat_depth[:, 1][::2],
#             lon_lat_depth[:, 0][::2],
#             c=lon_lat_depth[:, 2][::2],
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
#         nominal_strike, nominal_strike2 = calc_nominal_strike(lon_lat_depth)
#
#         rx_end, _ = src_site_dist.calc_rx_ry_GC2(
#             lon_lat_depth, planes, nominal_strike, hypocentre_origin=True
#         )
#         rx_end2, _ = src_site_dist.calc_rx_ry_GC2(
#             lon_lat_depth, planes, nominal_strike2, hypocentre_origin=True
#         )
#
#         Smax = [min(rx_end, rx_end2)[0], max(rx_end, rx_end2)[0]]
#
#         z_tor = planes[plane_index]["dtop"]
#
#         Dip = planes[plane_index]["dip"]
#         Dbot = z_tor + planes[plane_index]["width"] * math.sin(Dip)
#         Tbot = z_tor / math.tan(Dip) + planes[plane_index]["width"] * math.cos(Dip)
#         D = (planes[plane_index]["dhyp"] - z_tor) / math.sin(Dip)
#         hypo_lon, hypo_lat = srf.get_hypo(srf_file, custom_planes=remove_plane_idx(planes))
#         Rake = get_rake_value(srf_file, hypo_lat, hypo_lon)
#         fd, fdi, phi_red, phi_redi, predictor_functions, other = bea20(
#             M, rx, ry, Smax, D, Tbot, Dbot, Rake, Dip, force_type, Period
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
#             lon_lat_depth[:, 1][::2],
#             lon_lat_depth[:, 0][::2],
#             c=lon_lat_depth[:, 2][::2],
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
#         lon_lat_depth[:, 1][::2],
#         lon_lat_depth[:, 0][::2],
#         c=lon_lat_depth[:, 2][::2],
#         label="srf points",
#         s=1.0,
#     )
#     ax1.legend()
#
#     fig.savefig("/home/joel/local/directivity_hossack_full.png")
#
#     return fdi_average

# output = bea20(M,U,T,Smax,D,Tbot,Dbot,Rake,dip,force_type,Period)
# directivity_plots()
# get_directivity_effects()
# directivity_srf_plot()
