## December 13, 2021

### Reset the Hazard Curve data before sending a new request - ([PR #45](https://github.com/ucgmsim/gmhazard/pull/45))

- Reset any existing Hazard Curve data to plot with the correct data.

## December 1, 2021

### Deploying GMHazard web app to subdirectory - ([PR #39](https://github.com/ucgmsim/gmhazard/pull/39))

- Deploy the GMHazard web application to subdirectory.
- Only Dockerize the following components
  - Intermediate API
  - MariaDB
- Frontend is now deployed with production build.
  - It makes it easier to be deployed to subdirectories.

## November 26, 2021

### Download GMS no longer needs a token as a parameter - ([PR #36](https://github.com/ucgmsim/gmhazard/pull/36))

- To keep the consistency with other download endpoints.

## October 27, 2021

### Remove Authentication for the Projects tab - ([PR #23](https://github.com/ucgmsim/gmhazard/pull/23))

- Removed authentication requirements for the Project tab
  - Any private projects will still require authentication to access.

## October 26, 2021

### Refactor API calls - ([PR #22](https://github.com/ucgmsim/gmhazard/pull/22))

- Create API call modules for Projects.
  - Private access
  - Public access

## September 22, 2021

### Mw and Rrup distribution plot with error bounds - ([PR #14](https://github.com/ucgmsim/gmhazard/pull/14))

- Mw and Rrup distribution plot now comes with error bounds.
- Fixed the GMS download data issue with Core API.

## September 2, 2021

### Tidy up Frontend and ReadMEs - ([PR #7](https://github.com/ucgmsim/gmhazard/pull/7))

- Upload `.env.example`.
- Update ReadME to provide better information.
