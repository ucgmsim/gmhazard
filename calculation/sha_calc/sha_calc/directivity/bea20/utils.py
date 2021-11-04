from typing import List
from enum import Enum

import numpy as np
from scipy import stats
import pandas as pd
import time
import matplotlib.pyplot as plt


class EventType(Enum):
    """Event types for hypocentre distributions"""

    STRIKE_SLIP = "STRIKE_SLIP"
    DIP_SLIP = "DIP_SLIP"
    ALL = "ALL"

    @classmethod
    def from_rake(cls, rake: float):
        """Converts a rake value to an event type"""
        if -30 <= rake <= 30 or 150 <= rake <= 210:
            return EventType.STRIKE_SLIP
        elif 60 <= rake <= 120 or -120 <= rake <= -60:
            return EventType.DIP_SLIP
        else:
            return EventType.ALL


def set_hypocentres(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    fault_name: str = "Nothing",
):
    """
    Creates a List of planes each with a different set hypocentre for directivity calculations
    Sets a given amount of hypocentres along strike and down dip based on different distributions and the event type.

    Parameters
    ----------
    hypo_along_strike: int
        Number of hypocentres across strike to set
    hypo_down_dip: int
        Number of hypocentres down dip to set
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all for determining the down dip distribution function
    """

    # Gets the total length and removes any previous hypocentres
    total_length = 0
    for plane in planes:
        total_length += plane["length"]
        plane["shyp"] = -999.9
        plane["dhyp"] = -999.9

    # return monte_carlo_distribution(hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length)

    # return monte_carlo_grid(
    #     hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length
    # )

    return latin_hypercube(
        hypo_along_strike, hypo_down_dip, planes, event_type, fault_name, total_length
    )


def calc_nominal_strike(traces: np.ndarray):
    """
    Gets the start and ending trace of the fault and ensures order for largest lon value first

    Parameters
    ----------
    traces: np.ndarray
        Array of traces of points across a fault with the format [[lon, lat, depth],...]
    """

    # Extract just lat and lon for the start and end of the traces
    trace_start, trace_end = [traces[0][0], traces[0][1]], [
        traces[-1][0],
        traces[-1][1],
    ]

    # Ensures correct order
    if trace_start[0] < trace_end[0]:
        return np.asarray([trace_end]), np.asarray([trace_start])
    else:
        return np.asarray([trace_start]), np.asarray([trace_end])


def monte_carlo_distribution(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    fault_name: str,
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

    pd.DataFrame(truncated_strike).to_csv(
        f"/home/joel/local/directivity/monte_carlo/dist/Strike_Distribution_{fault_name}_{hypo_along_strike}.csv"
    )

    pd.DataFrame(truncated_down_dip).to_csv(
        f"/home/joel/local/directivity/monte_carlo/dist/Down_Dip_Distribution_{fault_name}_{event_type}_{hypo_down_dip}.csv"
    )

    return planes_list, planes_index


def monte_carlo_grid(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: List,
    event_type: EventType,
    fault_name: str,
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

    # Save the distribution TODO remove this
    truncated_df = pd.DataFrame(truncated_distribution)
    truncated_df.to_csv(
        f"/home/joel/local/directivity/distributions2/Strike_Distribution_{fault_name}_{hypo_along_strike}.csv"
    )

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

    # Save the distribution TODO remove this
    truncated_df = pd.DataFrame(down_dip_distribution)
    truncated_df.to_csv(
        f"/home/joel/local/directivity/distributions2/Down_Dip_Distribution_{fault_name}_{event_type}_{hypo_down_dip}.csv"
    )

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

    return planes_list, planes_index


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
    fault_name: str,
    total_length: float,
):
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

    # Save the distribution
    lhd_df = pd.DataFrame(lhd)
    lhd_df.to_csv(f"/home/joel/local/directivity/test/{fault_name}_{n_hypo}.csv")
    plot_searchspace(
        lhd,
        f"Latin Hypercube Distribution {n_hypo} Hypocentres",
        f"{fault_name}_{n_hypo}_distribution",
    )

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

    return planes_list, planes_index
