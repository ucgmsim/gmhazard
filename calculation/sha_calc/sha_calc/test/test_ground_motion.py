import numpy as np
import pandas as pd

from sha_calc import non_parametric_gm_excd_prob, parametric_gm_excd_prob


def test_non_parametric_gm_prob():
    im_level = 2
    index_tuples = [
        ("rupture_1", "rel_1"),
        ("rupture_1", "rel_2"),
        ("rupture_2", "rel_1"),
        ("rupture_2", "rel_2"),
        ("rupture_2", "rel_3"),
    ]
    index = pd.MultiIndex.from_tuples(index_tuples)
    values = [1, 3, 1, 3, 4]

    im_values = pd.Series(index=index, data=values)
    result = non_parametric_gm_excd_prob(im_level, im_values)

    assert result.loc["rupture_1"] == 0.5
    assert result.loc["rupture_2"] == 2 / 3


def test_parametric_gm_prob():
    im_level = np.exp(1)
    im_params = pd.DataFrame(
        index=["rupture_1", "rupture_2"],
        columns=["mu", "sigma"],
        data=[[1, 1], [0.25, 0.1]],
    )

    results = parametric_gm_excd_prob(im_level, im_params)

    # The IM values of the first rupture have a mean and standard deviation of 1, 1
    # which means that for a IM level of exp(1) (since lognormal distribution is used)
    # should always give an exceedance probability of 0.5 (since it
    # corresponds to the mean)
    assert float(results.loc["rupture_1"]) == 0.5

    # The IM values of the second rupture have a mean of 0.25 and standard deviation
    # of 0.1, which means that the exceedance probability for np.exp(1) should always
    # be pretty much zero
    assert np.isclose(float(results.loc["rupture_2"]), 0)
