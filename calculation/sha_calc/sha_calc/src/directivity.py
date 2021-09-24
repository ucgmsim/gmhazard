import numpy as np
import numpy.matlib
import math
import matplotlib.pyplot as plt

from IM_calculation.source_site_dist import src_site_dist
from qcore import srf

m = 7.2 # Moment magnitude, 5<=m<=8. 1x1 double.
u = np.arange(-90, 140.5, 0.5).tolist()
t = [-80] * 461 # The GC2 coordinates in km. Must both be nX1 doubles where n is the number of locations at which the model provides a prediction. Must be columnar.
s_max = [-10, 70] # The maximum possible values of s for the scenario in km. 1x2 double with the first element corresponding to the maximum s in the antistrike direction (defined to be a negative value) and the second element the maximum in the strike direction (positive value).
d = 10 # The effective rupture travel width, measured from the hypocenter to the shallowest depth of the rupture plane, up-dip (km). 1x1 double.
t_bot = 0 # The t ordinate of the bottom of the rupture plane (projected to the surface) in km. 1x1 double.
# The vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km. 1x1 double.
d_bot = 15
rake = 0

dip = 90  # The characteristic rupture rake and dip angles, in degrees. 1x1 doubles. -180<=rake<=180 and dip<=90
force_type = 0   # A flag for determining the SOF category. 0->select SOF based on rake angle. 1->force SOF=1. 2->force SOF=2. 1x1 double.
period = 3      # The spectral period for which fD is requested, in sec. 0.01<period<10. 1x1 double.

def get_directivity_effects():
    """ Calcualtes directivity effects at the given site"""

    # srf_file = "/isilon/cybershake/v20p4/Sources/scale_wlg_ nobackup/filesets/nobackup/nesi00213/RunFolder/jpa198/cybershake_sources/Data/Sources/AlpineK2T/Srf/AlpineK2T_REL01.srf"
    srf_file = "/home/joel/local/AlpineK2T_REL01.srf"

    planes = srf.read_header(srf_file, idx=True)

    points, rake = get_srf_values(srf_file)

    lat_lon_depth = np.asarray([[x["lat"], x["lon"], x["depth"]] for x in points])
    site_loc = np.asarray([[-41.713595, 173.090279], [-41.613595, 173.090279]])

    rx, ry = src_site_dist.calc_rx_ry_GC2(lat_lon_depth, planes, site_loc, hypocentre_origin=True)

    nominal_strike, nominal_strike2 = calc_nominal_strike(lat_lon_depth)

    rx_end, _ = src_site_dist.calc_rx_ry_GC2(lat_lon_depth, planes, nominal_strike, hypocentre_origin=True)
    rx_end2, _ = src_site_dist.calc_rx_ry_GC2(lat_lon_depth, planes, nominal_strike2, hypocentre_origin=True)

    s_max = [min(rx_end, rx_end2)[0], max(rx_end, rx_end2)[0]]

    # TODO Add ZTOR value if applicable
    z_tor = 0

    dip = planes[0]["dip"]
    d_bot = z_tor + planes[0]["width"] * math.sin(dip)
    t_bot = z_tor / math.tan(dip) + planes[0]["width"] * math.cos(dip)
    d = (planes[0]["dhyp"] - z_tor) / math.sin(dip)
    fd, fdi, phi_red, phi_redi, predictor_functions, other = Bea20(m, rx, ry, s_max, d, t_bot, d_bot, rake, dip,
                                                                   force_type, period)
    print("YES")

def calc_nominal_strike(traces):
    """ Gets the start and ending trace of the fault and ensures order for largest lat value first"""
    trace_start, trace_end = [traces[0][0], traces[0][1]], [traces[-1][0], traces[-1][1]]
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])


def get_srf_values(srf_file):
    with open(srf_file, "r") as sf:
        sf.readline()
        n_seg = int(sf.readline().split()[1])
        for _ in range(n_seg):
            sf.readline()
            sf.readline()
        n_point = int(sf.readline().split()[1])
        points = []
        average_rake = 0
        for _ in range(n_point):
            values = srf.get_lonlat(sf, "rake", True)
            point = {}
            point["lat"] = values[1]
            point["lon"] = values[0]
            average_rake += values[3]
            point["depth"] = values[2]
            points.append(point)
        average_rake = average_rake / n_point
    return points, average_rake

def Bea20(m,u,t,s_max,d,t_bot,d_bot,rake,dip,force_type,period):
    """ Bayless 2020 model function from matlab code"""

    # If not specified, determine rupture category from rake angle
    if force_type == 0:
        if (-30 <= rake <= 30) or (-180 <= rake <= -150) or (150 <= rake <= 180):
            type = 1
        else:
            type = 2
    elif force_type == 1:
        type = 1
    elif force_type == 2:
        type = 2

    # Convert u to s
    # Limit s to the s_max values for positive and negative numbers
    s_max1, s_max2 = s_max
    u, s = np.asarray(u), np.asarray(u)
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
    s_rake = s*math.cos(rake)
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

        phi[t_neg] = np.degrees(np.arctan(np.divide(abs(t[t_neg]) + t_bot, d_bot))) + dip - 90

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
    coefb = [-0.0336, 0.5469] # mag dependence of bmax
    coefc = [0.2858, -1.2090] # mag scaling of Tpeak
    coefd1 = [0.9928, -4.8300] # mag dependence of fG0 for SOF=1
    coefd2 = [0.3946, -1.5415] # mag dependence of fG0 for SOF=2
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
    b = b_max * np.exp(np.divide(-x ** 2, 2 * sigg ** 2))
    a = -b * fg0

    # fd and fdi
    fd = (a + fg[:, np.newaxis] * b) * f_dist[:, np.newaxis]
    ti_array = abs(per - period)
    ti = np.where(ti_array == np.amin(ti_array))[0][0]
    fdi = fd[:, ti]

    phi_per = [0.01, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1, 1.5, 2, 3, 4, 5, 7.5, 10]
    e1 = [0.000, 0.000, 0.008, 0.020, 0.035, 0.051, 0.067, 0.080, 0.084, 0.093, 0.110, 0.139, 0.166, 0.188, 0.199]
    e1interp = np.interp(np.log(per), np.log(phi_per), e1)

    # phired and phiredi
    phi_red = np.matlib.repmat(e1interp, len(fd), 1)
    phi_red[np.invert(footprint), :] = 0
    phi_redi = phi_red[:, ti]

    predictor_functions = {"fg": fg, "fdist": f_dist, "ftheta": f_theta, "fphi": fphi, "fs2": fs2}
    other = {"per": per, "rmax": r_max, "footprint": footprint, "tpeak": t_peak, "fg0": fg0, "bmax": b_max, "s2": s2}

    return fd, fdi, phi_red, phi_redi, predictor_functions, other


def directivity_plots():
    t_base = -80
    plot_s2 = None
    for i in range(0, 461):
        t = [t_base + i * 0.5] * 461
        fd, fdi, phi_red, phi_redi, predictor_functions, other = Bea20(m, u, t, s_max, d, t_bot, d_bot, rake, dip, force_type, period)

        # If first run set all plotting variables
        if plot_s2 is None:
            plot_s2 = other["s2"][:, np.newaxis]
            plot_fs2 = predictor_functions["fs2"][:, np.newaxis]
            plot_ftheta = predictor_functions["ftheta"][:, np.newaxis]
            plot_fg = predictor_functions["fg"][:, np.newaxis]
            plot_fdist = predictor_functions["fdist"][:, np.newaxis]
            plot_fdi = np.exp(fdi[:, np.newaxis])
        else:
            plot_s2 = np.append(plot_s2, other["s2"][:, np.newaxis], axis=1)
            plot_fs2 = np.append(plot_fs2, predictor_functions["fs2"][:, np.newaxis], axis=1)
            plot_ftheta = np.append(plot_ftheta, predictor_functions["ftheta"][:, np.newaxis], axis=1)
            plot_fg = np.append(plot_fg, predictor_functions["fg"][:, np.newaxis], axis=1)
            plot_fdist = np.append(plot_fdist, predictor_functions["fdist"][:, np.newaxis], axis=1)
            plot_fdi = np.append(plot_fdi, np.exp(fdi[:, np.newaxis]), axis=1)

    fig = plt.figure(figsize=(18, 12))

    ax = fig.add_subplot(231)
    ax2 = fig.add_subplot(232)
    ax3 = fig.add_subplot(233)
    ax4 = fig.add_subplot(234)
    ax5 = fig.add_subplot(235)
    ax6 = fig.add_subplot(236)

    ax.set_title('S2')
    ax.set_xlim(0, 320)
    ax.matshow(plot_s2)

    ax2.set_title('FS2')
    ax2.set_xlim(0, 320)
    ax2.matshow(plot_fs2)

    ax3.set_title('F Theta')
    ax3.set_xlim(0, 320)
    ax3.matshow(plot_ftheta)

    ax4.set_title('FG')
    ax4.set_xlim(0, 320)
    ax4.matshow(plot_fg)

    ax5.set_title('F Dist')
    ax5.set_xlim(0, 320)
    ax5.matshow(plot_fdist)

    ax6.set_title('FDI')
    ax6.set_xlim(0, 320)
    ax6.matshow(plot_fdi)


    fig.savefig("/home/joel/local/fig_test.png")

    print("Done")

# output = Bea20(m,u,t,s_max,d,t_bot,d_bot,rake,dip,force_type,period)
# directivity_plots()
get_directivity_effects()
