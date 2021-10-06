import pytest
import numpy as np
import pandas as pd

from sha_calc.hazard import hazard_single
from sha_calc.disagg import (
    disagg_exceedance,
    disagg_mean_weights,
    epsilon_non_para_single,
    epsilon_para,
)


def test_two_rupture_0p2():
    """Based on the disagg example with two ruptures
    at an IM level of 0.2
    """
    gm_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.378, 0.940])
    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    contributions = disagg_exceedance(gm_prob, rec_prob)

    assert round(contributions.loc["rupture_1"], 3) == 0.668
    assert round(contributions.loc["rupture_2"], 3) == 0.332


def test_two_rupture_0p5():
    """Based on the disagg example with two ruptures
    at an IM level of 0.5
    """
    gm_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.0191, 0.419])
    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    contributions = disagg_exceedance(gm_prob, rec_prob)

    assert round(contributions.loc["rupture_1"], 3) == 0.186
    assert round(contributions.loc["rupture_2"], 3) == 0.814


def test_mean_same_branches():
    """Tests the disagg mean, by using two branches
    with the same data and checking that the result
    matches the disagg from a single branch
    """
    weights = [0.4, 0.6]
    gm_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.378, 0.940])
    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    contributions_1 = disagg_exceedance(gm_prob, rec_prob)
    contributions_2 = disagg_exceedance(gm_prob, rec_prob)
    disagg_models = pd.concat([contributions_1, contributions_2], axis=1)

    hazard_1 = hazard_single(gm_prob, rec_prob)
    hazard_2 = hazard_single(gm_prob, rec_prob)
    hazard_mean = np.average([hazard_1, hazard_2], weights=weights)
    hazard_models = pd.Series(data=[hazard_1, hazard_2], index=[0, 1])

    adj_weights = disagg_mean_weights(
        hazard_mean, hazard_models, pd.Series(data=weights, index=[0, 1])
    )
    result = (disagg_models * adj_weights).sum(axis=1)
    assert np.all(np.isclose(result.values, contributions_1.values))


def test_mean_diff_branches():
    """Tests the disagg mean, using two branches with different
    gm_prob and compares it to results calculated by hand"""
    weights = [0.5, 0.5]
    gm_prob_1 = pd.Series(index=["rupture_1", "rupture_2"], data=[0.378, 0.940])
    gm_prob_2 = pd.Series(index=["rupture_1", "rupture_2"], data=[0.325, 0.845])

    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    contributions_1 = round(disagg_exceedance(gm_prob_1, rec_prob), 3)
    contributions_2 = round(disagg_exceedance(gm_prob_2, rec_prob), 5)
    disagg_models = pd.concat([contributions_1, contributions_2], axis=1)

    hazard_1 = hazard_single(gm_prob_1, rec_prob)
    hazard_2 = hazard_single(gm_prob_2, rec_prob)
    hazard_mean = np.average([hazard_1, hazard_2], weights=weights)
    hazard_models = pd.Series(data=[hazard_1, hazard_2], index=[0, 1])

    adj_weights = disagg_mean_weights(
        hazard_mean, hazard_models, pd.Series(data=weights, index=[0, 1])
    )
    result = (disagg_models * adj_weights).sum(axis=1)
    assert np.all(np.isclose(result.values, [0.66329, 0.33671]))


@pytest.mark.parametrize(
    ["mu", "sigma", "gm_prob", "expected"],
    [
        (0.0, 1.0, 0.5, 0.0),
        # High exceedance probability, small (wrt. mean) IM value (i.e. smaller epsilon)
        (0.0, 1.0, 0.5 + (0.682689492137086 / 2), -1.0),
        # Low exceedance probability, large (wrt. mean) IM value (i.e. larger epsilon)
        (0.0, 1.0, 0.5 - (0.682689492137086 / 2), 1.0),
    ],
)
def test_epsilon_para(mu: float, sigma: float, gm_prob: float, expected: float):
    """Tests the epsilon calculation for a parametric distribution,
    i.e. lognormally distributed IM values, in terms of
    the normal distribution parameters (mean and std)
    """
    params_df = pd.DataFrame(
        index=["test_rupture"],
        data=np.asarray([mu, sigma]).reshape(1, 2),
        columns=["mu", "sigma"],
    )
    gm_prob = pd.Series(index=["test_rupture"], data=[gm_prob])

    result = epsilon_para(params_df, gm_prob)

    assert np.isclose(result["test_rupture"], expected)


@pytest.mark.parametrize(
    ["im_values", "gm_prob", "expected"],
    [
        (np.random.normal(0.0, 1.0, int(1e7)), 0.5, 0.0),
        # High exceedance probability, small (wrt. mean) IM value (i.e. smaller epsilon)
        (np.random.normal(0.0, 1.0, int(1e7)), 0.5 + (0.682689492137086 / 2), -1.0),
        # Low exceedance probability, large (wrt. mean) IM value (i.e. larger epsilon)
        (np.random.normal(0.0, 1.0, int(1e7)), 0.5 - (0.682689492137086 / 2), 1.0),
    ],
)
def test_epsilon_non_para(im_values: np.ndarray, gm_prob: float, expected: float):
    """Tests the epsilon calculation for a non-parametric
    distribution (i.e. from IM values)
    """
    result = epsilon_non_para_single(im_values, gm_prob)

    assert np.isclose(result, expected, atol=1e-3)
