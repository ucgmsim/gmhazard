from typing import Sequence, Union

import numpy as np


def nzs1170p5_spectra(
    periods: Sequence[float], Z: float, RP: Union[float, int], D: float, soil_class: str
):
    """
    Provides the NZ code uniform hazard spectra ”

    Input variables:
    periods - the output periods for which the spectra is to be provided
    Z - factor defining the Z-factor for the region in question
    RP - return period for which the spectra is desired (20 < RP < 2500)
    D  - closest distance to a active fault in km
    SoilClass - soil class as defined by NZS1170.5 (options rock (A); weak
    rock (B); intermediate soil (C); soft or deep soil (D)); very soft (E)

    output variables:
    C - the value of the response spectra for the required periods
    Ch - the spectral shape
    R - R-factor for the given return period
    N - the near fault factor for the required periods
    """
    # Nmax(T) (T, Nmax)
    Nmax = np.array(
        (
            (0.0, 1.0),
            (1.5, 1.0),
            (2.0, 1.12),
            (3.0, 1.36),
            (4.0, 1.60),
            (5.0, 1.72),
            (10.0, 1.72),
        )
    )

    # compute return period factor
    R = get_return_period_factor(RP)

    # compute near fault factor N(D, T)
    if RP <= 250 or D > 20 or D is None:
        N = np.ones(len(periods), dtype=np.float32)
    elif D < 2:
        N = np.interp(periods, Nmax[:, 0], Nmax[:, 1])
    else:
        N = 1 + (np.interp(periods, Nmax[:, 0], Nmax[:, 1]) - 1) * (20 - D) / 18.0

    # get spectral shapes
    Ch = np.zeros(len(periods), dtype=np.float32)
    for i in range(len(periods)):
        if soil_class in ("A", "B"):
            if periods[i] < 0.1:
                Ch[i] = 1 + 1.35 * (periods[i] / 0.1)
            elif periods[i] < 0.3:
                Ch[i] = 2.35
            elif periods[i] < 1.5:
                Ch[i] = 1.6 * (0.5 / periods[i]) ** 0.75
            elif periods[i] < 3:
                Ch[i] = 1.05 / periods[i]
            else:
                Ch[i] = 3.15 / periods[i] ** 2
        elif soil_class in ("C", "U"):
            if periods[i] < 0.1:
                Ch[i] = 1.33 + 1.6 * periods[i] / 0.1
            elif periods[i] < 0.3:
                Ch[i] = 2.93
            elif periods[i] < 1.5:
                Ch[i] = 2 * (0.5 / periods[i]) ** 0.75
            elif periods[i] < 3:
                Ch[i] = 1.32 / periods[i]
            else:
                Ch[i] = 3.96 / periods[i] ** 2
        elif soil_class == "D":
            if periods[i] < 0.1:
                Ch[i] = 1.12 + 1.88 * periods[i] / 0.1
            elif periods[i] < 0.56:
                Ch[i] = 3.0
            elif periods[i] < 1.5:
                Ch[i] = 2.4 * (0.75 / periods[i]) ** 0.75
            elif periods[i] < 3:
                Ch[i] = 2.14 / periods[i]
            else:
                Ch[i] = 6.42 / periods[i] ** 2
        elif soil_class == "E":
            if periods[i] < 0.1:
                Ch[i] = 1.12 + 1.88 * periods[i] / 0.1
            elif periods[i] < 1:
                Ch[i] = 3.0
            elif periods[i] < 1.5:
                Ch[i] = 3 * (1.0 / periods[i]) ** 0.75
            elif periods[i] < 3:
                Ch[i] = 3.32 / periods[i]
            else:
                Ch[i] = 9.66 / periods[i] ** 2

    # get spectra
    C = Ch * Z * R * N

    return C, Ch, R, N


def get_return_period_factor(RP: int):
    """
    Parameters
    ----------
    return_period (years)

    Returns
    -------
    Return period factor
    """
    r_data = np.array(
        (
            (20, 0.20),
            (25, 0.25),
            (50, 0.35),
            (100, 0.50),
            (250, 0.75),
            (500, 1.0),
            (1000, 1.3),
            (2000, 1.7),
            (2500, 1.8),
        )
    )

    if RP < 20:
        raise ValueError("return_period must be at least 20 years")
    elif RP > 2500:
        raise ValueError("return_period must be at most 2500 years")
    r = np.interp(RP, r_data[:, 0], r_data[:, 1])
    return r
