import math
from typing import List, Union, Iterable, Tuple, Sequence

import numpy as np
import pandas as pd

import sha_calc as sha_calc
from seistech_calc.im import IM, IMType, IMComponent, IM_COMPONENT_MAPPING
from seistech_calc import site
from seistech_calc import gm_data
from seistech_calc import dbs
from seistech_calc import constants
from seistech_calc import rupture
from seistech_calc import utils
from seistech_calc import hazard


def get_IM_params(
    im: IM,
    imdb_ffps: Sequence[str],
    site_info: site.SiteInfo,
    ensemble: gm_data.Ensemble = None,
):
    """Retrieves the IM parameters (i.e. mean and sigma) for the
    specified IM and returns it as dataframe with columns mu & sigma"""
    im_df = get_IM_values(imdb_ffps, site_info, ensemble=ensemble)

    sigma_key = f"{im}_sigma"
    if str(im) not in im_df.columns:
        raise ValueError("No data found for the specified IM")
    if sigma_key not in im_df.columns:
        raise ValueError("The data appears to be non-parametric")

    im_params = im_df.loc[:, [str(im), f"{im}_sigma"]]
    im_params.columns = ["mu", "sigma"]

    return im_params


def get_IM_values(
    imdb_ffps: Sequence[str],
    site_info: site.SiteInfo,
    ensemble: gm_data.Ensemble = None,
) -> Union[pd.DataFrame, None]:
    """Load the IM values/parameters from the specified
    IMDBs or the IM data cache if an Ensemble that has
    caching enabled is provided

    Note: The IMDBs have to be mutually exclusive,
    i.e. a rupture/simulation can only be defined in one of the
    specified IMDBs

    Parameters
    ----------
    leafs: list of Leaf
        The leaves from which to retrieve the IM data
        Note: All leaves have to have the same
        IM data type (i.e. either parametric or non-parametric)
    site_info: SiteInfo
        Station of interest
    ensemble: Ensemble, optional
        If specified and the Ensemble has IM data
        caching enabled then IM data is retrieved from
        the cache if possible

    Returns
    -------
    im_df: pandas dataframe
        The combined IM dataframe
    """
    use_cache = ensemble is not None and ensemble.use_im_data_cache

    im_dfs, db_type = [], None
    for cur_imdb_ffp in imdb_ffps:
        # Try the IM data cache
        if use_cache:
            cur_im_data = ensemble.get_cache_value(site_info, cur_imdb_ffp)
            # Can't check for None since that is a valid value
            if cur_im_data is not False:
                im_dfs.append(cur_im_data)
                continue
        # Otherwise load from IMDB
        with dbs.IMDB.get_imdb(cur_imdb_ffp) as imdb:
            if db_type is None:
                db_type = imdb.imdb_type

            # All dbs have to be either parametric or non-parametric
            assert imdb.imdb_type == db_type

            # Parametric
            if isinstance(imdb, dbs.IMDBParametric):
                cur_im_params = imdb.im_data(site_info.station_name)

                if cur_im_params is not None:
                    ims = [
                        IM.from_str(col)
                        for col in cur_im_params.columns.values
                        if "sigma" not in col
                    ]
                    if site_info.user_vs30 is not None:
                        # TODO: Can we maybe vectorize this? Or even just support multiple IM types at once?
                        for im in ims:
                            if (
                                im.im_type == IMType.PGA
                                or im.im_type == IMType.PGV
                                or im.is_pSA()
                            ):
                                cur_im_params.loc[:, [str(im), f"{im}_sigma"]] = (
                                    apply_vs30_mod_parametric(
                                        cur_im_params, site_info, im
                                    )
                                    .loc[:, ["mu", "sigma"]]
                                    .values
                                )

                    im_dfs.append(cur_im_params)

                # Update the IM data cache
                if use_cache:
                    ensemble.update_cache(site_info, cur_imdb_ffp, cur_im_params)

            # Non-parametric
            else:
                cur_im_values = imdb.im_data(site_info.station_name)

                if site_info.user_vs30 is not None:
                    # TODO: Can we maybe vectorize this? Or even just support multiple IM types at once?
                    for im in cur_im_values.columns.values:
                        im = IM.from_str(im)
                        if (
                            im.im_type == IMType.PGA
                            or im.im_type == IMType.PGV
                            or im.is_pSA()
                        ):
                            cur_im_values[im] = apply_vs30_mod_non_parametric(
                                cur_im_values, site_info, im
                            )

                if use_cache:
                    ensemble.update_cache(site_info, cur_imdb_ffp, cur_im_values)

                if cur_im_values is not None:
                    im_dfs.append(cur_im_values)

    if len(im_dfs) == 0:
        return None

    im_df = pd.concat(im_dfs) if len(im_dfs) > 1 else im_dfs[0]
    return im_df


def get_gm_prob(
    branch: gm_data.Branch,
    site_info: site.SiteInfo,
    im: IM,
    im_level: float,
    source_type: constants.SourceType,
    ensemble: gm_data.Ensemble = None,
) -> pd.Series:
    """Retrieves the ground motion exceedance probabilities
    for the specified branch

    Returns
    -------
    pd.Series
        index = rupture_name, values = ground motion exceedance probabilities
    """
    # Convert to series
    gm_prob_df = get_gm_prob_df(
        branch, site_info, im, np.array([im_level]), source_type, ensemble=ensemble
    )

    return gm_prob_df.iloc[:, 0] if gm_prob_df is not None else None


def get_gm_prob_df(
    branch: gm_data.Branch,
    site_info: site.SiteInfo,
    im: IM,
    im_levels: np.ndarray,
    source_type: constants.SourceType,
    ensemble: gm_data.Ensemble = None,
):
    """Calculates the GM exceedance probabilities
    for the given branch & IM levels

    Parameters
    ----------
    branch: Branch
        The branch for which to calculate the GM
        exceedance probabilities
    site_info: SiteInfo
        Site of interest
    im: IM
        IM Object
    im_levels: np.ndarray
        IM levels at which to calculate the
        GM exceedance probabilites
    source_type: SourceType
        The source type, either fault or
        distributed seismicity
    ensemble: Ensemble, optional
        If specified and the Ensemble has IM data
        caching enabled then IM data is retrieved from
        the cache if possible

    Returns
    -------
    pd.DataFrame
        The ground motion probabilities for every rupture
        for every IM level.
        format: index = rupture_name, columns = IM_levels
    """
    im_data, im_data_type = get_im_data(
        branch, ensemble, site_info, source_type, im_component=im.component
    )

    # No IM data for the specified branch and source type
    if im_data is None:
        return None

    # Compute the ground motion probabilites and combine
    # Parametric
    if im_data_type is constants.IMDataType.parametric:
        # Raise error if component not in the mapping so is not supported
        if im.component not in IM_COMPONENT_MAPPING[im.im_type]:
            raise ValueError(
                f"{im}'s component {im.component} is not currently supported, only pSA and PGA IM's"
            )

        # Selecting the given im from the im_data
        im_data = im_data.loc[:, [str(im), f"{im}_sigma"]].rename(
            columns={str(im): "mu", f"{im}_sigma": "sigma"}
        )

        result_df = sha_calc.parametric_gm_excd_prob(
            im_levels,
            im_data,
        )
    # Non-parametric
    else:
        result_df = pd.concat(
            [
                sha_calc.non_parametric_gm_excd_prob(im_level, im_data[str(im)])
                for im_level in im_levels
            ],
            axis=1,
            join="inner",
        )
        result_df.columns = im_levels

    # Convert rupture names to rupture ids
    result_df.index = rupture.rupture_name_to_id(
        result_df.index.values,
        branch.flt_erf_ffp
        if source_type is constants.SourceType.fault
        else branch.ds_erf_ffp,
    )

    return result_df


def _apply_mu_im_component(value, component):
    mu_ratio = sha_calc.get_computed_component_ratio(
        str(IMComponent.RotD50),
        str(component),
        # Using period of 0.01 for PGA IM
        0.01 if value.name.startswith("PGA") else IM.from_str(value.name).period,
    )
    return value + math.log(mu_ratio)


def get_im_data(
    branch, ensemble, site_info, source_type, im_component=IMComponent.RotD50
):
    # Load the IM data
    im_data_type = (
        branch.ds_im_data_type
        if source_type is constants.SourceType.distributed
        else branch.flt_im_data_type
    )
    assert im_data_type is not None
    imdb_ffps = branch.get_imdb_ffps(source_type)
    im_data = get_IM_values(imdb_ffps, site_info, ensemble=ensemble)

    # No IM data for the specified branch and source type
    if im_data is None:
        return None

    if im_component != IMComponent.RotD50:
        if im_data_type is constants.IMDataType.parametric:
            # Ensure we only perform component conversion on PGA or pSA IM's
            sa_im_data = im_data.filter(regex="PGA|pSA")
            sigma_im_data = sa_im_data.filter(regex="sigma")
            mu_im_data = sa_im_data[
                sa_im_data.columns.difference(sigma_im_data.columns)
            ]

            # Compute the apply the ratios which are using the paper
            # Relations between Some Horizontal-Component Ground-Motion Intensity Measures Used in Practice (Boore 2017)
            # Sigma ratios were taken from Table 3 and the mu ratio is calculated using equation 2
            # Sigma is dominated by the sigma of the original component and the variation
            # in the sigma of the ratio is minimal, hence constant values where determined from a ratio vs period plot
            mu_im_data = mu_im_data.apply(
                lambda value: _apply_mu_im_component(value, im_component)
            )
            sigma_ratio = 0.095 if im_component == IMComponent.Larger else 0.085
            sigma_im_data = sigma_im_data.apply(
                lambda sigma: np.sqrt((sigma * sigma + sigma_ratio * sigma_ratio))
            )

            # Ensures we have other IM's such as PGV
            im_data = im_data[im_data.columns.difference(sa_im_data.columns)]
            # Join back together
            im_data = pd.concat([im_data, mu_im_data, sigma_im_data], axis=1)

        # Non-parametric
        else:
            raise NotImplementedError(
                "IM Components other than RotD50 are not currently supported for Non-parametric calculations"
            )
    return im_data, im_data_type


def compute_adj_branch_weights(
    ensemble: gm_data.Ensemble,
    im: IM,
    im_value: float,
    site_info: site.SiteInfo,
) -> Tuple[pd.Series, float]:
    """
    Computes hazard adjusted branch weights using equations (9) and (10) from
    "Consideration and Propagation of Ground Motion Selection Epistemic Uncertainties
    to Seismic Performance Metrics (Karim Tarbali, 2018)"

    Used for computing disagg mean and aggregating GCIM results

    Parameters
    ----------
    ensemble: Ensemble
        The ensemble to use
    im: IM
        The IM Object of interest
    im_value: float
        The IM value at which to compute the adjusted
        branch weights
    site_info: SiteInfo
        The site of interest

    Returns
    -------
    series:
        The adjusted weights for each branch
    float:
        The ensemble hazard mean for the specified IM value
    """
    # Get the hazard for branches and ensemble
    im_values = np.asarray([im_value])
    branches_hazard = hazard.run_branches_hazard(
        ensemble, site_info, im, im_values=im_values
    )
    ensemble_hazard = hazard.run_ensemble_hazard(
        ensemble, site_info, im, branch_hazard=branches_hazard, im_values=im_values
    )
    hazard_mean = ensemble_hazard.total_hazard.iloc[0]

    # Convert to Series
    hazard_series = pd.Series(
        {
            branch_name: cur_hazard.total_hazard.values[0]
            for branch_name, cur_hazard in branches_hazard.items()
        }
    )

    # Branch weights
    branch_weights = pd.Series(
        {
            branch.name: branch.weight
            for name, branch in ensemble.get_im_ensemble(
                im.im_type
            ).branches_dict.items()
        }
    )

    return (
        sha_calc.disagg_mean_weights(hazard_mean, hazard_series, branch_weights),
        hazard_mean,
    )


def apply_vs30_mod_non_parametric(
    im_values: pd.DataFrame, site_info: site.SiteInfo, im: IM
) -> pd.Series:
    """Applies the user vs30 modification for non-parametric data"""
    assert "PGA" in im_values.columns
    pga = im_values["PGA"].copy()

    return im_values[str(im)] * __get_site_amp_ratio(
        pga, site_info.db_vs30, site_info.user_vs30, im
    )


def apply_vs30_mod_parametric(
    im_params: pd.DataFrame, site_info: site.SiteInfo, im: IM
) -> pd.DataFrame:
    pga = np.exp(im_params["PGA"])

    #  The below line gets the empirical IM out of log-space,
    #  applies the correction and then transforms it back into log-space
    im_params["mu"] = np.log(
        np.exp(im_params[str(im)])
        * __get_site_amp_ratio(pga, site_info.db_vs30, site_info.user_vs30, im)
    )

    im_params["sigma"] = im_params[str(im) + "_sigma"]
    return im_params[["mu", "sigma"]]


def get_SA_ims(
    ims: Iterable[IM], component: IMComponent = IMComponent.RotD50
) -> List[IM]:
    """Gets all SA ims from the provided list of IMs"""
    sa_ims = [
        im
        for im in ims
        if im.component == component and (im.is_pSA() or im.im_type == IMType.PGA)
    ]
    return sorted(sa_ims, key=lambda im: 0 if im.period is None else im.period)


def compute_contr_mean(data_series: pd.Series, contribution_df: pd.DataFrame) -> float:
    """Computes the weighted sum of the provided values using the
    contribution from disaggregation for the IM values in contributions (columns)

    Parameters
    ----------
    data_series: pd.Series
        The values of the quantity to average
        format: index = rupture_id, values = values
    contributions: pd.DataFrame
        The contribution of the ruptures
        format: index = rupture_id, columns = IM values

    Returns
    -------
    pd.Series
        The contribution mean values at each IM value
        format: index = IM value, values = contribution mean
    """
    # Sanity check
    ruptures = contribution_df.index.values
    assert np.all(utils.pandas_isin(ruptures, data_series.index.values))

    return (
        contribution_df.loc[ruptures]
        .multiply(data_series.loc[ruptures], axis=0)
        .sum(axis=0, skipna=True)
    )


def compute_contr_16_84(
    data_series: pd.Series, contribution_df: pd.DataFrame
) -> Tuple[float, float]:
    """Computes the 16th and 84th percentile values for
    the provided data using the contributions weights
    from disaggregation

    Parameters
    ----------
    data_series: pd.Series
        The values of the quantity to average
        format: index = rupture_id, values = values
    contributions: pd.DataFrame
        The contribution of the ruptures
        format: index = rupture_id, columns = IM values

    Returns
    -------
    tuple:
        16th percentile value, 84th percentile value
    """
    # Sanity check
    ruptures = contribution_df.index.values
    assert np.all(utils.pandas_isin(ruptures, data_series.index.values))

    df = pd.merge(
        contribution_df,
        data_series.to_frame("data"),
        how="inner",
        right_index=True,
        left_index=True,
    )
    df.sort_values("data", ascending=True, inplace=True)

    quantiles = sha_calc.query_non_parametric_cdf_invs(
        np.asarray([0.16, 0.84]), df["data"].values, np.cumsum(df.contribution.values)
    )
    return quantiles[0], quantiles[1]


###
# VS30 modification code below
###
def __fs_auto(i: int, vs30: float, a1100: float = None):
    """
    Python implementation of the Campbell Bozorgina 2014 site amplification (aka vs30 adjustments) from the GMM model
    :param i: index of pSA period
    :param vs30: vs30 that is being amplified to
    :param a1100: PGA value at 1100 m/s vs30 for a given site source combination
    :return: IM factor of site_amplification
    """
    # fmt: off
    k1 = np.array([400, 865.0, 865.0, 865.0, 865.0, 908.0, 1054.0, 1086.0, 1032.0,
                   878.0, 748.0, 654.0, 587.0, 503.0, 457.0, 410.0,
                   400.0, 400.0, 400.0, 400.0, 400.0, 400.0, 400.0, 400.0])
    k2 = np.array([-1.955, -1.186, -1.186, -1.186, -1.219, -1.273, -1.346, -1.471, -1.624,
                   -1.931, -2.188, -2.381, -2.518, -2.657, -2.669, -2.401,
                   -1.955, -1.025, -0.299, 0.0, 0.0, 0.0, 0.0, 0.0])
    c10 = np.array([1.713, 1.090, 1.090, 1.094, 1.149, 1.290, 1.449, 1.535, 1.615,
                    1.877, 2.069, 2.205, 2.306, 2.398, 2.355, 1.995,
                    1.447, 0.330, -0.514, -0.848, -0.793, -0.748, -0.664,
                    -0.576])
    # fmt: on

    scon_c = 1.88
    scon_n = 1.18

    if vs30 < k1[i]:  # Low vs30
        return c10[i] * np.log(vs30 / k1[i]) + k2[i] * np.log(
            (a1100 + scon_c * np.exp(scon_n * np.log(vs30 / k1[i]))) / (a1100 + scon_c)
        )
    elif vs30 < 1100.0:  # medium
        return (c10[i] + k2[i] * scon_n) * np.log(vs30 / k1[i])
    else:  # high
        return (c10[i] + k2[i] * scon_n) * np.log(1100.0 / k1[i])


def __get_site_amp_ratio(pga: float, db_vs30: float, user_vs30: float, im: IM):
    """
    Calculates a PGA_1100 estimate; uses it to calculate a site amplification ratio for the difference in vs30
    between the user and the modelled vs30

    Scaling is only defined for pSA and PGA otherwise no scaling is applied - aka a ratio of 1.

    :param pga: PGA value at given site/rupture for the original vs30 value
    :param db_vs30: vs30 of the initial calculation
    :param user_vs30: vs30 of the site that the intesity measures are to be scaled to
    :param im: IM of intensity measure to scale
    :return: a ratio to be applied to intensity measure values to scale them based on the user_vs30
    """
    pga1100 = pga * np.exp(__fs_auto(0, 1100) - __fs_auto(0, db_vs30, pga))

    periods = np.array(
        [
            -1,
            0,
            0.001,
            0.01,
            0.02,
            0.03,
            0.05,
            0.075,
            0.10,
            0.15,
            0.20,
            0.25,
            0.30,
            0.40,
            0.50,
            0.75,
            1.00,
            1.50,
            2.00,
            3.00,
            4.00,
            5.00,
            7.50,
            10.0,
        ]
    )

    if im.is_pSA():
        T = np.argmin(np.abs(periods - im.period))
    elif im.im_type == IMType.PGV:
        T = 0
    elif im.im_type == IMType.PGA:
        T = 1
    else:
        return 1

    result = np.exp(__fs_auto(T, user_vs30, pga1100) - __fs_auto(T, db_vs30, pga1100))

    return result
