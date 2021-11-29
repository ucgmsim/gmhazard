## [20.11.4] - 2021-11-26 -- Download GMS no longer needs a token as a parameter
### Changed
    - Non-projects GMS download endpoint no longer needs a token as a parameter
        - To keep the consistency with other download endpoints. (E.g., Hazard Curve, Disagg, UHS...)
## [20.11.3] - 2021-11-18 -- Update Flask and itsdangerous packages
### Changed
    - Support Flask 2.x.x
        - werkzeug cache is no longer supported, changed to flask-caching
    - Support itsdangerous 2.x.x
        - TimedJSONWebSignatureSerializer is deprecated
        - Replaced with URLSafeTimedSerializer
## [20.11.2] - 2021-01-06 -- NaN fix
### Changed
	- For NZCode return nan values as "nan" to make results json compatible
    - CH is now a dictionary/series (entries per exceedance) instead of just a single value across all exceedances

## [20.11.1] - 2020-11-26 -- Renaming
### Changed
    - Renamed to coreAPI 
	- Some refactoring of its util functions into the `gmhazard_utils` repo

## [19.11.1] - 2019-11-20 -- Initial Version
### Changed
    - Added README and CHANGELOG
    - Added host and port number to API app
