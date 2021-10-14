import pytest
import numpy as np
import pandas as pd

from sha_calc.hazard import hazard_single, hazard_curve


def test_single_rupture():
    """Based on the 'One Rupture Scenario' example,
    using a single IM level of 0.2
    """
    gm_prob = pd.Series(index=["rupture_1"], data=[0.378])
    rec_prob = pd.Series(index=["rupture_1"], data=[0.01])

    result = hazard_single(gm_prob, rec_prob)

    assert result == 0.00378


def test_single_rupture_multi_IM():
    """Based on the 'One Rupture Scenario' example,
    with the IM levels of 0.2 and 0.5
    """
    im_levels = [0.2, 0.5]
    gm_prob_df = pd.DataFrame(
        index=["rupture_1"],
        columns=im_levels,
        data=np.asarray([0.378, 0.0191]).reshape(1, -1),
    )
    rec_prob = pd.Series(index=["rupture_1"], data=0.01)

    result = hazard_curve(gm_prob_df, rec_prob)

    assert np.all(np.isclose(result.values, np.asarray([0.00378, 0.000191])))


def test_two_rupture():
    """Based on the 'Two Rupture Scenarios' example using
    two ruptures at an IM level of 0.2
    """
    gm_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.378, 0.940])
    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    result = hazard_single(gm_prob, rec_prob)

    assert result == 0.00566


def test_two_rupture_multi_IM():
    """Based on the 'Two Rupture Scenarios' example using
    two ruptures at an IM level of 0.2 and 0.5
    """
    im_levels = [0.2, 0.5]
    gm_prob_df = pd.DataFrame(
        index=["rupture_1", "rupture_2"],
        columns=im_levels,
        data=[[0.378, 0.0191], [0.940, 0.419]],
    )
    rec_prob = pd.Series(index=["rupture_1", "rupture_2"], data=[0.01, 0.002])

    result = hazard_curve(gm_prob_df, rec_prob)

    assert np.all(np.isclose(result.values, np.asarray([0.00566, 0.001029])))
