# Seistech

Note: This toolset is still under development, and is therefore not stable and changing frequently 
with no guarantee of backwards compatability

The Seistech toolset consists of 4 components:

- Calculation
- Tools
- APIs
- Frontend

each of the components is briefly discussed below

Installation instructions for each package can be found in their respective READMEs

### Calculation

The core component that contains the calculation code, everything else builds on this. Is made up of two 
packages: `sha_calc` contains the low level PHSA functions and `seistech_calc` which supports more complex PSHA 
calculation. Such as hazard, disaggregation and UHS for logic trees (referred to as Ensembles).

Note: `seistech_calc` can be used directly, see its README for details

## Tools

This component consist of three packages: `seistech_utils` which contains utility functions that are shared 
across all other packages, `project_gen` which allows generation of (static) PSHA results for a specific set of locations
and `project_gen_service` which is a service for generating projects (not fully functional at this stage).

### APIs

Consists of 2 APIs, the `coreAPI` which computes PHSA results on the fly (using `seistech_calc`) and `project_gen` which returns 
static PSHA results (generated via `project_gen`)

IntermediateAPI to be added

### Frontend 

To be added


## Overview diagram

![SeistechDiagram](seistech_diagram.png)