import math
from typing import Tuple

import numpy as np
import numpy.matlib


def bea20(
    M: float,
    U: np.ndarray,
    T: np.ndarray,
    Smax: Tuple[float, float],
    D: float,
    Tbot: float,
    Dbot: float,
    rake: float,
    dip: float,
    periods: np.ndarray,
    rupture_type: int = 0,
):
    """
    Calculates the directivity effects at given locations based on fault information.
    Algorithm has been taken from the Bayless 2020 model found in the paper.
    "A Rupture Directivity Adjustment Model Applicable to the NGA-West2 Ground Motion Models
    and Complex Fault Geometries (Bayless 2020)".
    This functionality was compared to the matlab code taken from the paper.

    Parameters
    ----------
    M: float
        Moment magnitude, 5<=M<=8
    U: np.ndarray
        The GC2 coordinates in km. Equivalent to ry.
        A 1d array of length n where n is the number of locations at which the model provides a prediction.
    T: np.ndarray
        The GC2 coordinates in km. Equivalent to rx.
        A 1d array of length n where n is the number of locations at which the model provides a prediction.
    Smax: Tuple[float, float]
        Tuple of 2x1 float where the first value is the lowest max value and the second is the largest max value for s.
        Computed from GC2 using nominal strike of the fault.
    D: float
        The effective rupture travel width, measured from the hypocentre to the shallowest depth of the rupture plane.
    Tbot: float
        The length of the bottom of the rupture plane (projected to the surface) in km.
    Dbot: float
        The vertical depth of the bottom of the rupture plane from the ground surface, including Ztor, in km.
    rake: float
        The rake of the fault
    dip: float
        The dip of the fault at the hypocentre
    periods: np.ndarray
        Numpy array of periods to calculate fD for
    rupture_type: int, optional
        0 for rupture_type based on rake (auto)
        1 for a strike slip
        2 for a oblique, reverse or normal
    """
    # If not specified, determine rupture category from rake angle
    if rupture_type == 0:
        if (-30 <= rake <= 30) or (-180 <= rake <= -150) or (150 <= rake <= 180):
            rupture_type = 1
        else:
            rupture_type = 2

    # Convert U to S
    # Limit S to the Smax values for positive and negative numbers
    Smax1, Smax2 = Smax
    U, S = np.asarray(U).copy(), np.asarray(U).copy()
    S[U < Smax1] = Smax1
    S[U > Smax2] = Smax2

    # Convert U to Ry
    # Reduce each positive and negative side by absolute value of Smax
    # Also remove negative numbers inbetween
    Ry = np.where(U >= 0, U - Smax2, np.abs(U) - abs(Smax1))
    Ry[Ry < 0] = 0

    # Calculate S2
    S = -S if rupture_type == 2 and rake < 0 else S
    Srake = S * math.cos(math.radians(rake))
    D = max(D, 3)  # Gets the max value for D, 3 is the minimum
    S2 = np.sqrt(Srake ** 2 + D ** 2)

    # Predictor variable fs2
    if rupture_type == 1:
        fs2 = np.log(S2)
        fsCap = math.log(465)
    else:
        fs2 = np.where(Srake >= 0, np.log(S2), math.log(D))
        fsCap = math.log(188)
    fs2[fs2 > fsCap] = fsCap

    # Angular predictor variables
    if rupture_type == 1:
        theta = np.nan_to_num(np.arctan(T / U))
        ftheta = abs(np.cos(2 * theta))
        fphi = np.ones(U.size)
    else:
        tpos, tneg = T > 0, T <= 0
        phi = np.zeros(U.size)

        phi[tneg] = np.degrees(np.arctan((np.abs(T[tneg]) + Tbot) / Dbot)) + dip - 90

        t1 = tpos & (T < Tbot)
        phi[t1] = 90 - dip - np.degrees(np.arctan((Tbot - T[t1]) / Dbot))

        t2 = tpos & (T >= Tbot)
        phi[t2] = 90 - dip + np.degrees(np.arctan((T[t2] - Tbot) / Dbot))

        phi[phi > 45] = 45
        fphi = np.cos(2 * phi * np.pi / 180)

        Tmin = 10 * (abs(math.cos(math.radians(rake))) + 1)
        T2 = abs(T)
        T2[T2 < Tmin] = Tmin
        T2[tpos] = Tmin

        omega = np.arctan(T2 / Ry)
        ftheta = np.nan_to_num(np.sin(omega), nan=1)

    # Distance taper
    R = np.sqrt(T ** 2 + Ry ** 2)  # Distance from surface trace
    if M < 5:
        Rmax = 40
    elif M > 7:
        Rmax = 80
    else:
        Rmax = -60 + 20 * M

    if rupture_type == 2:
        Rmax = Rmax - 20

    AR = -4 * Rmax
    Footprint = R <= Rmax
    fdist = np.zeros(R.size)
    fdist[Footprint] = 1 - np.exp(AR / R[Footprint] - AR / Rmax)
    fG = fs2 * ftheta * fphi

    # Calculate fD

    # Constants
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
    if rupture_type == 1:
        fG0 = coefd1[1] + coefd1[0] * M
    else:
        fG0 = coefd2[1] + coefd2[0] * M
    bmax = coefb[1] + coefb[0] * M
    Tpeak = 10 ** (coefc[1] + coefc[0] * M)

    # Period dependent coefficients: a and b
    x = np.log10(periods / Tpeak)
    b = bmax * np.exp((-(x ** 2)) / (2 * SigG ** 2))
    a = -b * fG0

    # No longer calculating fdi, instead compute for all periods listed
    fD = (a + fG[:, np.newaxis] * b) * fdist[:, np.newaxis]

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
    e1interp = np.interp(np.log(periods), np.log(PhiPer), e1)

    # Computing phi_red for all periods
    # Note: In the original matlab implementation this was only done for the period of interest
    PhiRed = np.matlib.repmat(e1interp, len(fD), 1)
    PhiRed[np.invert(Footprint), :] = 0

    predictor_functions = {
        "fG": fG,
        "fdist": fdist,
        "ftheta": ftheta,
        "fphi": fphi,
        "fs2": fs2,
    }
    other = {
        "periods": periods,
        "Rmax": Rmax,
        "Footprint": Footprint,
        "Tpeak": Tpeak,
        "fG0": fG0,
        "bmax": bmax,
        "S2": S2,
    }

    return fD, PhiRed, predictor_functions, other
