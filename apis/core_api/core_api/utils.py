from typing import Dict, Sequence

import numpy as np
from werkzeug.contrib.cache import BaseCache

import gmhazard_calc as sc
import seistech_utils as su
from core_api import server


class NZTACachedData(su.api.BaseCacheData):
    """Wrapper for caching NZTA hazard data"""

    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        nzta_hazard: sc.nz_code.nzta_2018.NZTAResult,
    ):
        super().__init__(ensemble, site_info)
        self.nzta_hazard = nzta_hazard

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzta_hazard))


class NZS1170p5CachedHazardData(su.api.BaseCacheData):
    """Wrapper for caching NZS1170.5 hazard data"""

    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        nzs1170p5_hazard: sc.nz_code.nzs1170p5.NZS1170p5Result,
    ):
        super().__init__(ensemble, site_info)
        self.nzs1170p5_hazard = nzs1170p5_hazard

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzs1170p5_hazard))


class NZS1170p5CachedUHSData(su.api.BaseCacheData):
    """Wrapper for caching NZS1170.5 uhs data"""

    def __init__(
        self,
        ensemble: sc.gm_data.Ensemble,
        site_info: sc.site.SiteInfo,
        nzs1170p5_uhs: Sequence[sc.nz_code.nzs1170p5.NZS1170p5Result],
    ):
        super().__init__(ensemble, site_info)
        self.nzs1170p5_uhs = nzs1170p5_uhs

    def __iter__(self):
        return iter((self.ensemble, self.site_info, self.nzs1170p5_uhs))


def get_nzs1170p5_hazard(
    ensemble_id: str,
    station: str,
    im: sc.im.IM,
    optional_params: Dict,
    cache,
    user_vs30: float = None,
):
    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzs1170p5_hazard",
        ensemble_id=ensemble_id,
        station=station,
        im=str(im),
        **{cur_key: str(cur_val) for cur_key, cur_val in optional_params.items()},
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        server.app.logger.debug(
            f"Computing NZS1170p5 - Hazard - version {su.api.get_repo_version()}"
        )
        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)
        nzs1170p5_hazard = sc.nz_code.nzs1170p5.run_ensemble_nzs1170p5(
            ensemble,
            site_info,
            im,
            soil_class=optional_params.get("soil_class"),
            distance=optional_params.get("distance"),
            z_factor=optional_params.get("z_factor"),
            z_factor_radius=optional_params.get("z_factor_radius")
            if "z_factor_radius" in optional_params.keys()
            else sc.nz_code.nzs1170p5.CITY_RADIUS_SEARCH,
        )

        cache.set(
            cache_key, NZS1170p5CachedHazardData(ensemble, site_info, nzs1170p5_hazard)
        )
    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzs1170p5_hazard = cached_data

    return ensemble, site_info, nzs1170p5_hazard


def get_nzs1170p5_uhs(
    ensemble_id: str,
    station: str,
    exceedances: str,
    optional_args: Dict,
    cache: BaseCache,
    user_vs30: float = None,
):
    exceedances = np.asarray(list(map(float, exceedances.split(","))))

    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzs1170p5_uhs",
        ensemble_id=ensemble_id,
        station=station,
        **{
            f"exceedance_{ix}": str(exceedance)
            for ix, exceedance in enumerate(exceedances)
        },
        **{cur_key: str(cur_val) for cur_key, cur_val in optional_args.items()},
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        server.app.logger.debug(
            f"No cached result for {cache_key}, computing NZS1170p5 - UHS - version {su.api.get_repo_version()}"
        )

        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        nzs1170p5_results = sc.uhs.run_nzs1170p5_uhs(
            ensemble, site_info, exceedances, opt_nzs1170p5_args=optional_args
        )

        cache.set(
            cache_key, NZS1170p5CachedUHSData(ensemble, site_info, nzs1170p5_results)
        )
    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzs1170p5_results = cached_data

    return ensemble, site_info, nzs1170p5_results


def get_nzta_result(
    ensemble_id: str,
    station: str,
    soil_class: sc.NZTASoilClass,
    cache: BaseCache,
    user_vs30: float = None,
    im_component: sc.im.IMComponent = sc.im.IMComponent.RotD50,
):
    # Get the cached result, if there is one
    cache_key = su.api.get_cache_key(
        "nzta_hazard",
        ensemble_id=ensemble_id,
        station=station,
        soil_class=soil_class.value,
        im_component=str(im_component),
    )
    cached_data = cache.get(cache_key)

    if cached_data is None:
        server.app.logger.debug(
            f"Computing NZTA - Hazard - version {su.api.get_repo_version()}"
        )
        ensemble = sc.gm_data.Ensemble(ensemble_id)
        site_info = sc.site.get_site_from_name(ensemble, station, user_vs30=user_vs30)

        nzta_hazard = sc.nz_code.nzta_2018.run_ensemble_nzta(
            ensemble, site_info, soil_class=soil_class, im_component=im_component
        )

        cache.set(cache_key, NZTACachedData(ensemble, site_info, nzta_hazard))
    else:
        server.app.logger.debug(f"Using cached result with key {cache_key}")
        ensemble, site_info, nzta_hazard = cached_data

    return ensemble, site_info, nzta_hazard
