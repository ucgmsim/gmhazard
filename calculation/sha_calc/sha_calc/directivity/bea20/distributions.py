from typing import List

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from sha_calc.directivity.bea20.EventType import EventType


class weibull_truncated_strike_slip(stats.rv_continuous):
    weibull = stats.weibull_min(scale=0.626, c=3.921)
    divide = weibull.cdf(1)

    def _pdf(self, x):
        return self.weibull.pdf(x) / self.divide


class weibull_truncated_oblique(stats.rv_continuous):
    weibull = stats.weibull_min(scale=0.612, c=3.353)
    divide = weibull.cdf(1)

    def _pdf(self, x):
        return self.weibull.pdf(x) / self.divide


class gamma_truncated(stats.rv_continuous):
    gamma = stats.gamma(a=7.364, scale=0.072)
    divide = gamma.cdf(1)

    def _pdf(self, x):
        return self.gamma.pdf(x) / self.divide


def monte_carlo_distribution(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    total_length: float,
):
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
    planes_index = []

    # Do 2 style of hypo placement
    for i in range(0, hypo_down_dip * hypo_along_strike):
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
                planes_index.append(index)
                planes_list.append(planes_copy)
            current_length += plane["length"]

    return planes_list, planes_index, []


def monte_carlo_grid(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    total_length: float,
):
    # Works out the distances across strike of the fault for each hypocentre
    # Based on a normal distribution and truncated between 0 and 1
    mean, std = 0.5, 0.23
    strike_distribution = stats.norm(mean, std)
    upper, lower = strike_distribution.cdf((1, 0))
    dist_range = upper - lower
    truncated_points = (np.random.uniform(0, 1, hypo_along_strike)) * dist_range + lower
    truncated_distribution = strike_distribution.ppf(truncated_points)
    distances = truncated_distribution * total_length

    # Works out the depth method for down dip placement of hypocentres
    # Based on Weilbull or Gamma distributions depending on the EventType
    if event_type == EventType.DIP_SLIP:
        distribution = stats.gamma(a=7.364, scale=0.072)
    elif event_type == EventType.STRIKE_SLIP:
        distribution = stats.weibull_min(scale=0.626, c=3.921)
    else:
        distribution = stats.weibull_min(scale=0.612, c=3.353)
    # Truncate between 0 and 1 for hypocentre depth to ensure none exceed the boundaries
    upper, lower = distribution.cdf((1, 0))
    dist_range = upper - lower
    truncated_points = (np.random.uniform(0, 1, hypo_down_dip)) * dist_range + lower
    down_dip_distribution = distribution.ppf(truncated_points)

    planes_list = []
    planes_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                for depth in down_dip_distribution:
                    planes_depth_copy = [plane.copy() for plane in planes]
                    planes_depth_copy[index]["shyp"] = distance - (total_length / 2)
                    planes_depth_copy[index]["dhyp"] = plane["width"] * depth
                    planes_index.append(index)
                    planes_list.append(planes_depth_copy)
            current_length += plane["length"]

    return planes_list, planes_index, []


def even_grid(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    total_length: float):

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
    strike_weight_dist = strike_distribution.pdf([x / total_length for x in distances]) * (1 / hypo_along_strike)

    # Works out the depth method for down dip placement of hypocentres
    # Based on Weilbull or Gamma distributions depending on the EventType
    if event_type == EventType.DIP_SLIP:
        down_dip_distribution = gamma_truncated(a=0, b=1)
    elif event_type == EventType.STRIKE_SLIP:
        down_dip_distribution = weibull_truncated_strike_slip(a=0, b=1)
    else:
        down_dip_distribution = weibull_truncated_oblique(a=0, b=1)
    dip_weight_dist = down_dip_distribution.pdf([x / planes[0]["width"] for x in down_dip_values]) * (1 / hypo_down_dip)

    combo_weight_dist = [strike * dip for strike in strike_weight_dist for dip in dip_weight_dist]
    sum_dist = sum(combo_weight_dist)
    weights = [x / sum_dist for x in combo_weight_dist]

    planes_list = []
    planes_index = []

    for distance in distances:
        current_length = 0
        planes_copy = [plane.copy() for plane in planes]
        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                for depth in down_dip_values:
                    planes_depth_copy = [plane.copy() for plane in planes]
                    planes_depth_copy[index]["shyp"] = distance - (total_length / 2)
                    planes_depth_copy[index]["dhyp"] = depth
                    planes_index.append(index)
                    planes_list.append(planes_depth_copy)
            current_length += plane["length"]

    return planes_list, planes_index, weights


def plot_searchspace(x, title, name):
    fig, ax = plt.subplots()
    plt.plot(np.array(x)[:, 0], np.array(x)[:, 1], "bo", label="samples")
    ax.set_xlabel("Strike Distribution")
    ax.set_xlim([0, 1])
    ax.set_ylabel("Down Dip Distribution")
    ax.set_ylim([0, 1])
    plt.title(title)
    plt.savefig(f"/home/joel/local/directivity/test/{name}.png")


def latin_hypercube(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    total_length: float,
):

    n_hypo = hypo_along_strike * hypo_down_dip

    lhd = stats.qmc.LatinHypercube(2)
    lhd = lhd.random(n_hypo)

    lower, upper = 0, 1
    mu, sigma = 0.5, 0.23
    strike_distribution = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma
    )

    lhd[:, 0] = strike_distribution.ppf(lhd[:, 0])

    # Works out the depth method for down dip placement of hypocentres
    # Based on Weilbull or Gamma distributions depending on the EventType
    if event_type == EventType.DIP_SLIP:
        down_dip_distribution = gamma_truncated(a=0, b=1)
    elif event_type == EventType.STRIKE_SLIP:
        down_dip_distribution = weibull_truncated_strike_slip(a=0, b=1)
    else:
        down_dip_distribution = weibull_truncated_oblique(a=0, b=1)

    lhd[:, 1] = down_dip_distribution.ppf(lhd[:, 1])

    planes_list = []
    planes_index = []

    for strike, down_dip in lhd:

        distance = strike * total_length

        current_length = 0
        planes_copy = [plane.copy() for plane in planes]

        for index, plane in enumerate(planes_copy):
            if current_length < distance < (current_length + plane["length"]):
                planes_copy[index]["shyp"] = distance - (total_length / 2)
                planes_copy[index]["dhyp"] = plane["width"] * down_dip
                planes_index.append(index)
                planes_list.append(planes_copy)
            current_length += plane["length"]

    return planes_list, planes_index, []
