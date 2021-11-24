## November 16, 2021

### Permission check - ([PR #30](https://github.com/ucgmsim/gmhazard/pull/30))

- Adding permission check before forwarding requests to Core/Project API.

## October 27, 2021

### Remove Authentication for the Projects tab - ([PR #23](https://github.com/ucgmsim/gmhazard/pull/23))

- Removed authentication requirements for the Project tab
  - Any private projects will still require authentication to access.
  - PublicAPI proxy is created to hit the ProjectAPI with no Auth0 authentication required.

## September 2, 2021

### Tidy up Intermediate API and ReadMEs - ([PR #7](https://github.com/ucgmsim/gmhazard/pull/7))

- Rename Middleware to IntermediateAPI.
- Upload `.env.example`.
- Update ReadME to provide better information.~~
