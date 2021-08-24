## [21.5.5] - 2021-07-14 -- IM Components
### Changed
    - Support for different IM Components with file structure change

## [21.5.5] - 2021-06-23 -- NHM perturbations
### Changed
    - Support for NHM perturbations

## [21.5.4] - 2021-06-14 -- UHS/Disagg bug fix 
### Changed
    - Added handling for UHS/Disagg out of range exceedance issue

## [21.5.3] - 2021-05-19 -- Extra GMS metadata 
### Changed
    - Added extra GMS metadata

## [21.5.2] - 2021-05-17 -- Download format updates 
### Changed
    - Minor download format updates

## [21.5.1] - 2021-05-04 -- New Ensemble Format Support 
### Changed
    - Added support for the new ensemble format

## [21.1.5] - 2021-03-08 -- NZTA data included 
### Changed
    - Added support for saving/returning NZTA code data

## [21.1.4] - 2021-02-17 -- Automated Project Data Generation
### Changed
    - Added service and API endpoint for automated new project creation & result generation

## [21.1.3] - 2021-01-14 -- Download full project
### Changed
    - Add endpoint for downloading all data for a single project as .zip file
    - Include lat/lon to site retrieval endpoint

## [21.1.2] - 2021-01-14 -- Return Project Name
### Changed
    - Also return project names with the project ids

## [21.1.1] - 2021-01-13 -- New Data Format
### Changed
    - Now uses csv + json files for saving of the project data instead of pickle files, 
        reduces store requirement by a factor of 10+

## [20.11.2] - 2021-01-06 -- NZCode fix
### Changed
    - Return nan values as "nan" to be json compatible
    - CH is now a dictionary/series (entries per exceedance) instead of just a single value across all exceedances

## [20.11.1] - 2020-11-26 -- Initial Version
### Changed
	- Initial version of projectAPI
