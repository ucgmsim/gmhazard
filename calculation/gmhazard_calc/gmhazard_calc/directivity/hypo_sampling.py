from typing import Sequence

import numpy as np
from scipy import stats

from .EventType import EventType


class WeibullTruncatedStrikeSlip(stats.rv_continuous):
    """Truncates the weibull distribution to between 0 and 1 for strike slip events"""

    weibull = stats.weibull_min(scale=0.626, c=3.921)
    divide = weibull.cdf(1)

    def _pdf(self, x):
        return self.weibull.pdf(x) / self.divide


class WeibullTruncatedOblique(stats.rv_continuous):
    """Truncates the weibull distribution to between 0 and 1 for oblique events"""

    weibull = stats.weibull_min(scale=0.612, c=3.353)
    divide = weibull.cdf(1)

    def _pdf(self, x):
        return self.weibull.pdf(x) / self.divide


class GammaTruncated(stats.rv_continuous):
    """Truncates the gamma distribution to between 0 and 1 for dip slip events"""

    gamma = stats.gamma(a=7.364, scale=0.072)
    divide = gamma.cdf(1)

    def _pdf(self, x):
        return self.gamma.pdf(x) / self.divide


def mc_sampling(
    nhypo: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
):
    """
    Straight Monte Carlo using distributions along strike and dip to determine the placement

    Parameters
    ----------
    nhypo: int
        Number of hypocentres to use
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    total_length: float
        The total length of the fault
    """
    mean, std = 0.5, 0.23
    strike_distribution = stats.norm(mean, std)
    upper, strike_lower = strike_distribution.cdf((1, 0))
    strike_dist_range = upper - strike_lower

    if event_type == EventType.DIP_SLIP:
        distribution = stats.gamma(a=7.364, scale=0.072)
    elif event_type == EventType.STRIKE_SLIP:
        distribution = stats.weibull_min(scale=0.626, c=3.921)
    else:
        distribution = stats.weibull_min(scale=0.612, c=3.353)
    # Truncate between 0 and 1 for hypocentre depth to ensure none exceed the boundaries
    upper, lower = distribution.cdf((1, 0))
    dist_range = upper - lower

    truncated_strike = []
    truncated_down_dip = []

    planes_list = []
    plane_index = []

    for i in range(0, nhypo):
        truncated_points = np.random.uniform(0, 1) * strike_dist_range + strike_lower
        truncated_dist = strike_distribution.ppf(truncated_points)
        distance = truncated_dist * total_length
        truncated_strike.append(truncated_dist)

        truncated_points = np.random.uniform(0, 1) * dist_range + lower
        down_dip = distribution.ppf(truncated_points)

        truncated_down_dip.append(down_dip)

        current_length = 0
        planes_copy = [plane.copy() for plane in planes]

        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                planes_copy[index]["shyp"] = distance - (total_length / 2)
                planes_copy[index]["dhyp"] = plane["width"] * down_dip
                plane_index.append(index)
                planes_list.append(planes_copy)
            current_length += plane["length"]

    return planes_list, plane_index, []


def even_grid(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
):
    """
    Uses an evenly spaced grid across strike and dip based on the amount of hypocentres specified across both lengths

    Parameters
    ----------
    hypo_along_strike: int
        Number of hypocentres across strike
    hypo_down_dip: int
        Number of hypocentres down dip
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    total_length: float
        The total length of the fault
    """

    gap = total_length / (hypo_along_strike + 1)
    distances = [gap * (x + 1) for x in range(hypo_along_strike)]

    down_gap = planes[0]["width"] / (hypo_down_dip + 1)
    down_dip_values = [down_gap * (x + 1) for x in range(hypo_down_dip)]

    # Works out the distances across strike of the fault for each hypocentre
    # Based on a normal distribution and truncated between 0 and 1
    mu, sigma = 0.5, 0.23
    lower, upper = 0, 1
    strike_distribution = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma
    )
    strike_weight_dist = strike_distribution.pdf(
        [x / total_length for x in distances]
    ) * (1 / hypo_along_strike)

    # Works out the depth method for down dip placement of hypocentres
    # Based on Weilbull or Gamma distributions depending on the EventType
    if event_type == EventType.DIP_SLIP:
        down_dip_distribution = GammaTruncated(a=0, b=1)
    elif event_type == EventType.STRIKE_SLIP:
        down_dip_distribution = WeibullTruncatedStrikeSlip(a=0, b=1)
    else:
        down_dip_distribution = WeibullTruncatedOblique(a=0, b=1)
    dip_weight_dist = down_dip_distribution.pdf(
        [x / planes[0]["width"] for x in down_dip_values]
    ) * (1 / hypo_down_dip)

    combo_weight_dist = [
        strike * dip for strike in strike_weight_dist for dip in dip_weight_dist
    ]
    sum_dist = sum(combo_weight_dist)
    weights = np.asarray(combo_weight_dist) / sum_dist

    planes_list = []
    plane_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                for depth in down_dip_values:
                    planes_depth_copy = [plane.copy() for plane in planes]
                    planes_depth_copy[index]["shyp"] = distance - (total_length / 2)
                    planes_depth_copy[index]["dhyp"] = depth
                    plane_index.append(index)
                    planes_list.append(planes_depth_copy)
            current_length += plane["length"]

    return planes_list, plane_index, weights


def latin_hypercube(
    nhypo: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
):
    """
    Using Latin Hypercube to place hypocentres by taking a grid of nhypo length across both strike and dip
    which is defined by the strike and dip distribution methods but is sectioned to ensure lower probability hypocentre
    locations are chosen as part of the set

    Parameters
    ----------
    nhypo: int
        Number of hypocentres to use
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    total_length: float
        The total length of the fault
    """

    lhd = stats.qmc.LatinHypercube(2)
    lhd = lhd.random(nhypo)

    lower, upper = 0, 1
    mu, sigma = 0.5, 0.23
    strike_distribution = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma
    )

    lhd[:, 0] = strike_distribution.ppf(lhd[:, 0])

    # Works out the depth method for down dip placement of hypocentres
    # Based on Weilbull or Gamma distributions depending on the EventType
    if event_type == EventType.DIP_SLIP:
        down_dip_distribution = GammaTruncated(a=0, b=1)
    elif event_type == EventType.STRIKE_SLIP:
        down_dip_distribution = WeibullTruncatedStrikeSlip(a=0, b=1)
    else:
        down_dip_distribution = WeibullTruncatedOblique(a=0, b=1)

    lhd[:, 1] = down_dip_distribution.ppf(lhd[:, 1])

    planes_list = []
    plane_index = []

    for strike, down_dip in lhd:

        distance = strike * total_length

        current_length = 0
        planes_copy = [plane.copy() for plane in planes]

        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                planes_copy[index]["shyp"] = distance - (total_length / 2)
                planes_copy[index]["dhyp"] = plane["width"] * down_dip
                plane_index.append(index)
                planes_list.append(planes_copy)
            current_length += plane["length"]

    return planes_list, plane_index, []
