from typing import Sequence

import numpy as np
import copy
from scipy import stats

from gmhazard_calc.constants import EventType


class WeibullTruncatedStrikeSlip(stats.rv_continuous):
    """Truncates the weibull distribution to between 0 and 1 for strike slip events"""

    weibull = stats.weibull_min(scale=0.626, c=3.921)
    divide = weibull.cdf(1)

    def _pdf(self, x, *args):
        return self.weibull.pdf(x, *args) / self.divide


class WeibullTruncatedOblique(stats.rv_continuous):
    """Truncates the weibull distribution to between 0 and 1 for oblique events"""

    weibull = stats.weibull_min(scale=0.612, c=3.353)
    divide = weibull.cdf(1)

    def _pdf(self, x, *args):
        return self.weibull.pdf(x, *args) / self.divide


class GammaTruncated(stats.rv_continuous):
    """Truncates the gamma distribution to between 0 and 1 for dip slip events"""

    gamma = stats.gamma(a=7.364, scale=0.072)
    divide = gamma.cdf(1)

    def _pdf(self, x, *args):
        return self.gamma.pdf(x, *args) / self.divide


def mc_sampling(
    nhypo: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
    seed: int = None,
):
    """
    Straight Monte Carlo using distributions along strike and dip
    to determine the placement

    Parameters
    ----------
    nhypo: int
        Number of hypocentres to use
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type strike_slip, dip_slip or oblique
        for determining the down dip distribution function
    total_length: float
        The total length of the fault
    seed: int
        The seed to use to get reproducible results
    """
    # Setting seed to fix results unless None then will be random
    np.random.seed(seed)

    # Define strike distribution and truncate
    mean, std = 0.5, 0.23
    strike_distribution = stats.norm(mean, std)
    strike_upper, strike_lower = strike_distribution.cdf((1, 0))
    strike_dist_range = strike_upper - strike_lower

    # Define down dip distribution
    down_dip_distribution = _get_down_dip_distribution(event_type)

    # Truncate between 0 and 1 for hypocentre depth to ensure none exceed the boundaries
    dip_upper, dip_lower = down_dip_distribution.cdf((1, 0))
    dip_dist_range = dip_upper - dip_lower

    hypo_planes, plane_ind = [], []
    plane_lengths = np.cumsum(np.asarray([plane["length"] for plane in planes]))
    # Assuming all widths in the planes are the same
    assert all([x["width"] == planes[0]["width"] for x in planes])

    # Creates a planes list each with a different hypocentre location drawn from the strike and dip distributions
    for i in range(nhypo):
        # Draw strike location based on distribution
        truncated_points = np.random.uniform(0, 1) * strike_dist_range + strike_lower
        truncated_dist = strike_distribution.ppf(truncated_points)
        strike_location = truncated_dist * total_length

        # Draw depth based on distribution
        truncated_points = np.random.uniform(0, 1) * dip_dist_range + dip_lower
        depth = down_dip_distribution.ppf(truncated_points)

        # Get the plane index of the hypocentre location
        plane_ix = np.flatnonzero(strike_location < plane_lengths)[0]
        # Copies the planes without any hypocentres and sets the shyp and dhyp values
        # in the hypocentre plane to the strike location and depth values
        planes_copy = copy.deepcopy(planes)
        planes_copy[plane_ix]["shyp"] = strike_location - (total_length / 2)
        planes_copy[plane_ix]["dhyp"] = planes[0]["width"] * depth
        plane_ind.append(plane_ix)
        hypo_planes.append(planes_copy)

    return hypo_planes, plane_ind, []


def uniform_grid(
    hypo_along_strike: int,
    hypo_down_dip: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
):
    """
    Uses a uniformly spaced grid across strike and dip
    Based on the amount of hypocentres specified across both lengths

    Parameters
    ----------
    hypo_along_strike: int
        Number of hypocentres across strike
    hypo_down_dip: int
        Number of hypocentres down dip
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all
        for determining the down dip distribution function
    total_length: float
        The total length of the fault
    """
    strike_gap = total_length / (hypo_along_strike + 1)
    strike_locations = np.arange(1, hypo_along_strike + 1) * strike_gap

    down_gap = planes[0]["width"] / (hypo_down_dip + 1)
    down_dip_locations = np.arange(1, hypo_down_dip + 1) * down_gap

    # Works out the distances across strike of the fault for each hypocentre
    # Based on a normal distribution and truncated between 0 and 1
    mu, sigma = 0.5, 0.23
    lower, upper = 0, 1
    strike_distribution = stats.truncnorm(
        (lower - mu) / sigma, (upper - mu) / sigma, loc=mu, scale=sigma
    )
    strike_weights = strike_distribution.pdf(strike_locations / total_length) * (
        1 / hypo_along_strike
    )

    down_dip_distribution = _get_down_dip_distribution(event_type)
    # Assuming all widths in the planes are the same
    assert all([x["width"] == planes[0]["width"] for x in planes])
    dip_weights = down_dip_distribution.pdf(down_dip_locations / planes[0]["width"]) * (
        1 / hypo_down_dip
    )
    combo_weights = (strike_weights[:, np.newaxis] * dip_weights).ravel()
    combo_weights = combo_weights / combo_weights.sum()

    hypo_planes, plane_ind = [], []
    plane_lengths = np.cumsum(np.asarray([plane["length"] for plane in planes]))

    # Creates a planes list each with a different hypocentre location based on the strike and dip locations
    for strike_location in strike_locations:
        # Get the plane index of the hypocentre location
        plane_ix = np.flatnonzero(strike_location < plane_lengths)[0]
        for depth in down_dip_locations:
            # Copies the planes without any hypocentres and sets the shyp and dhyp values
            # in the hypocentre plane to the strike location and depth values
            planes_copy = copy.deepcopy(planes)
            planes_copy[plane_ix]["shyp"] = strike_location - (total_length / 2)
            planes_copy[plane_ix]["dhyp"] = depth
            plane_ind.append(plane_ix)
            hypo_planes.append(planes_copy)

    return hypo_planes, plane_ind, combo_weights


def latin_hypercube_sampling(
    nhypo: int,
    planes: Sequence,
    event_type: EventType,
    total_length: float,
    seed: int = None,
):
    """
    Using Latin Hypercube to place hypocentres by taking a grid of nhypo length
    across both strike and dip which is defined by the strike and dip distribution
    methods but is sectioned to ensure lower probability hypocentre
    locations are chosen as part of the set

    Parameters
    ----------
    nhypo: int
        Number of hypocentres to use
    planes: list
        The planes to adjust and set the hypocentre on
    event_type: EventType
        The event type Strike_slip, dip_slip or all
        for determining the down dip distribution function
    total_length: float
        The total length of the fault
    seed: int
        The seed to use to get reproducible results
    """
    # Define strike and down dip distributions
    mu, sigma = 0.5, 0.23
    strike_distribution = stats.truncnorm(
        (0.0 - mu) / sigma, (1.0 - mu) / sigma, loc=mu, scale=sigma
    )
    down_dip_distribution = _get_down_dip_distribution(event_type)

    # Setup Latin-HyperCube
    lhd = stats.qmc.LatinHypercube(2, seed=seed)
    lhd = lhd.random(nhypo)
    lhd[:, 0] = strike_distribution.ppf(lhd[:, 0])
    lhd[:, 1] = down_dip_distribution.ppf(lhd[:, 1])

    hypo_planes, plane_ind = [], []
    plane_lengths = np.cumsum(np.asarray([plane["length"] for plane in planes]))
    # Assuming all widths in the planes are the same
    assert all([x["width"] == planes[0]["width"] for x in planes])

    # Creates a planes list each with a different hypocentre location based on the strike and depth values
    # from the latin hypercube distribution
    for strike, depth in lhd:
        strike_location = strike * total_length
        # Get the plane index of the hypocentre location
        plane_ix = np.flatnonzero(strike_location < plane_lengths)[0]
        # Copies the planes without any hypocentres and sets the shyp and dhyp values
        # in the hypocentre plane to the strike location and depth values
        planes_copy = copy.deepcopy(planes)
        planes_copy[plane_ix]["shyp"] = strike_location - (total_length / 2)
        planes_copy[plane_ix]["dhyp"] = planes[0]["width"] * depth
        plane_ind.append(plane_ix)
        hypo_planes.append(planes_copy)

    return hypo_planes, plane_ind, []


def _get_down_dip_distribution(event_type: EventType):
    """
    Works out the depth method for down dip placement of hypocentres
    Based on Weilbull or Gamma distributions depending on the EventType
    """
    if event_type == EventType.DIP_SLIP:
        down_dip_distribution = GammaTruncated(a=0, b=1)
    elif event_type == EventType.STRIKE_SLIP:
        down_dip_distribution = WeibullTruncatedStrikeSlip(a=0, b=1)
    else:
        down_dip_distribution = WeibullTruncatedOblique(a=0, b=1)
    return down_dip_distribution
