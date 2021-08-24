from typing import Tuple, Dict

import numpy as np


def get_im_correlations(IMi: str, IMj: str):
    """Gets the correlation coefficients for the
    specified IMs"""
    if IMi == IMj:
        return 1.0

    models = [bradley_correlations_2011, baker_correlations_2008, bradley_correlations_2015]
    for cur_model in models:
        cur_result = cur_model(IMi, IMj)
        if cur_result is not None:
            return cur_result

    raise NotImplementedError(
        f"Correlation coefficient for "
        f"IMs {IMi} and {IMj} is currently not supported"
    )


def bradley_correlations_2015(IMi: str, IMj: str):
    """
    Computes the empirical correlation coefficients
    based on the Bradley 2015 paper

    Parameters
    ----------
    IMi: str
    IMj: str
        IM types for which to compute the correlations.
        Spectral acceleration IM has to have the format 'pSA_X.XX'

    Returns
    -------
    float:
        Correlation coefficient
    """
    correlation_dict = {
        ("ai", "pga"): 0.83,
        ("ai", "pgv"): 0.73,
        ("ai", "asi"): 0.81,
        ("ai", "si"): 0.68,
        ("ai", "dsi"): 0.51,
        ("ai", "ds575"): -0.19,
        ("ai", "ds595"): -0.20,
        ("ai", "cav"): 0.89,
    }

    IMi, IMj = IMi.lower(), IMj.lower()

    lookup_value = _get_IM_comb_value(IMi, IMj, correlation_dict)
    if lookup_value is not None:
        return lookup_value

    # pSA
    if IMi.startswith("psa") or IMj.startswith("psa"):
        other_IM = IMi if IMj.startswith("psa") else IMj
        T = _get_psa_period(IMi if IMi.startswith("psa") else IMj)

        if T <= 0.01 or T > 10.0:
            raise ValueError("Only supports pSA periods in the range [0.01,10.0]")

        if other_IM == "ai":
            # Period segments
            e = np.asarray([0.01, 0.20, 4.0, 10.0])

            # Coefficients
            a = np.asarray([0.83, 0.74, 0.46])
            b = np.asarray([0.74, 0.46, 0.35])
            c = np.asarray([0.05, 1.0, 5.5])
            d = np.asarray([2.5, 1.5, 6.0])

            # Get index into the coefficients array
            i = max(np.flatnonzero(e >= T)[0] - 1, 0)

            return ((a[i] + b[i]) / 2) - (
                (a[i] - b[i]) / 2 * np.tanh(d[i] * np.log(T / c[i]))
            )

    return None


def bradley_correlations_2011(IMi: str, IMj: str):
    """Computes the empirical correlation coefficents
    as per the 2011 Bradley papers

    Parameters
    ----------
    IMi: str
    IMj: str
        IM types for which to compute the correlations.
        Spectral acceleration IM has to have the format 'pSA_X.XX'

    Returns
    -------
    float:
        Correlation coefficient
    """
    correlation_dict = {
        ("pga", "si"): 0.599,
        ("pga", "asi"): 0.928,
        ("si", "asi"): 0.641,
        ("pgv", "pga"): 0.733,
        ("pgv", "si"): 0.89,
        ("pgv", "asi"): 0.729,
        ("dsi", "pga"): 0.395,
        ("dsi", "pgv"): 0.800,
        ("dsi", "asi"): 0.376,
        ("dsi", "si"): 0.782,
        ("cav", "pga"): 0.700,
        ("cav", "pgv"): 0.691,
        ("cav", "asi"): 0.703,
        ("cav", "si"): 0.681,
        ("cav", "dsi"): 0.565,
        ("ds575", "pga"): -0.442,
        ("ds575", "pgv"): -0.259,
        ("ds575", "asi"): -0.411,
        ("ds575", "si"): -0.131,
        ("ds575", "dsi"): 0.074,
        ("ds575", "cav"): 0.077,
        ("ds595", "pga"): -0.405,
        ("ds595", "pgv"): -0.211,
        ("ds595", "asi"): -0.370,
        ("ds595", "si"): -0.079,
        ("ds595", "dsi"): 0.163,
        ("ds595", "cav"): 0.122,
        ("ds595", "cav"): 0.122,
        ("ds595", "ds575"): 0.843,
    }

    IMi, IMj = IMi.lower(), IMj.lower()

    # Simple look-up correlations
    lookup_value = _get_IM_comb_value(IMi, IMj, correlation_dict)
    if lookup_value is not None:
        return lookup_value

    # pSA
    if IMi.startswith("psa") or IMj.startswith("psa"):
        other_IM = IMi if IMj.startswith("psa") else IMj
        T = _get_psa_period(IMi if IMi.startswith("psa") else IMj)

        if T < 0.01 or T > 10.0:
            raise ValueError("Only supports pSA periods in the range [0.01,10.0]")

        if other_IM in ["pga", "pgv", "si", "asi", "dsi", "cav"]:
            # PGA
            if other_IM == "pga":
                a = np.array([1, 0.97])
                b = np.array([0.895, 0.25])
                c = np.array([0.06, 0.80])
                d = np.array([1.6, 0.8])
                e = np.array([0.20, 10.0])
            # PGV
            elif other_IM == "pgv":
                a = np.array([0.73, 0.54, 0.80, 0.76])
                b = np.array([0.54, 0.81, 0.76, 0.7])
                c = np.array([0.045, 0.28, 1.1, 5.0])
                d = np.array([1.8, 1.5, 3.0, 3.2])
                e = np.array([0.1, 0.75, 2.5, 10.0])
            # SI
            elif other_IM == "si":
                a = np.asarray([0.60, 0.38, 0.95])
                b = np.asarray([0.38, 0.94, 0.68])
                c = np.asarray([0.045, 0.33, 3.10])
                d = np.asarray([1.5, 1.4, 1.6])
                e = np.asarray([0.1, 1.4, 10])
            # ASI
            elif other_IM == "asi":
                a = np.asarray([0.927, 0.823, 1.05])
                b = np.asarray([0.823, 0.962, 0.29])
                c = np.asarray([0.04, 0.14, 0.80])
                d = np.asarray([1.8, 2.2, 1.0])
                e = np.asarray([0.075, 0.3, 10])
            # DSI
            elif other_IM == "dsi":
                a = np.asarray([0.39, 0.19, 0.98])
                b = np.asarray([0.265, 1.2, 0.82])
                c = np.asarray([0.04, 1.2, 6.1])
                d = np.asarray([1.8, 0.6, 3.0])
                e = np.asarray([0.15, 3.4, 10.0])
            # CAV
            elif other_IM == "cav":
                a = np.asarray([0.7, 0.635, 0.525])
                b = np.asarray([0.635, 0.525, 0.39])
                c = np.asarray([0.043, 0.95, 6.2])
                d = np.asarray([2.5, 3.0, 4.0])
                e = np.asarray([0.20, 3.0, 10.0])
            else:
                return None

            idx = np.flatnonzero(e >= T)[0]
            return (a[idx] + b[idx]) / 2.0 - (a[idx] - b[idx]) / 2 * np.tanh(
                d[idx] * np.log(T / c[idx])
            )

        if other_IM in ["ds575", "ds595"]:
            if other_IM == "ds595":
                a = np.asarray([-0.41, -0.41, -0.38, -0.35, -0.02, 0.23, 0.02])
                b = np.asarray([0.01, 0.04, 0.08, 0.26, 1.40, 6.0, 10.0])
            elif other_IM == "ds575":
                a = np.asarray([-0.45, -0.39, -0.39, -0.06, 0.16, 0.0])
                b = np.asarray([0.01, 0.09, 0.30, 1.40, 6.5, 10.0])
            else:
                return None

            i = np.flatnonzero(b >= T)[0]
            return a[i - 1] + np.log(T / b[i - 1]) / np.log(b[i] / b[i - 1]) * (
                a[i] - a[i - 1]
            )

    return None


def _check_IM_comb(IMi: str, IMj: str, im_comb: Tuple[str, str]):
    """Checks if the given IMs match the specified combination"""
    return (IMi == im_comb[0] and IMj == im_comb[1]) or (
        IMj == im_comb[0] and IMi == im_comb[1]
    )


def _get_IM_comb_value(IMi: str, IMj: str, lookup: Dict[Tuple[str, str], float]):
    """Retrieves the value corresponding to
    the specified IM combination"""
    r_1, r_2 = lookup.get((IMi, IMj)), lookup.get((IMj, IMi))
    return r_2 if r_1 is None else r_1


def baker_correlations_2008(IMi: str, IMj: str):
    """Computes the spectral acceleration correlation
    coefficients based on Baker 2008 implementation on OpenSHA

    Parameters
    ----------
    IMi: str
    IMj: str
        IM types for which to compute the correlations.
        Spectral acceleration IM has to have the format 'pSA_X.XX'

    Returns
    -------
    float:
        Correlation coefficient
    """
    IMi, IMj = IMi.lower(), IMj.lower()
    if not (IMi.startswith("psa") and IMj.startswith("psa")):
        return None

    period_i, period_j = _get_psa_period(IMi), _get_psa_period(IMj)
    t_min = min(period_i, period_j)
    t_max = max(period_i, period_j)
    c2 = np.nan

    c1 = 1.0 - np.cos(np.pi / 2.0 - np.log(t_max / max(t_min, 0.109)) * 0.366)
    if t_max < 0.2:
        c2 = 1.0 - 0.105 * (1.0 - 1.0 / (1.0 + np.exp(100.0 * t_max - 5.0))) * (
            t_max - t_min
        ) / (t_max - 0.0099)
    if t_max < 0.109:
        c3 = c2
    else:
        c3 = c1
    c4 = c1 + 0.5 * (np.sqrt(c3) - c3) * (1.0 + np.cos(np.pi * t_min / 0.109))
    if t_max <= 0.109:
        return c2
    elif t_min > 0.109:
        return c1
    elif t_max < 0.2:
        return min(c2, c4)
    else:
        return c4


def _get_psa_period(IM: str):
    assert IM.lower().startswith("psa")

    return float(IM.split("_")[-1])
