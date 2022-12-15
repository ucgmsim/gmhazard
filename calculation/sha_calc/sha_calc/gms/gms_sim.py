"""Ground motion selection functionality for simulations based on the following papers:
- Bradley, Brendon A. "A generalized conditional intensity measure approach and holistic ground‐motion selection."
Earthquake Engineering & Structural Dynamics 39.12 (2010): 1321-1342.
- Bradley, Brendon A. "A ground motion selection algorithm based on the generalized conditional intensity measure approach."
Soil Dynamics and Earthquake Engineering 40 (2012): 48-61.
- Bradley, Brendon A., Lynne S. Burks, and Jack W. Baker. "Ground motion selection for simulation‐based seismic hazard and structural reliability assessment."
Earthquake Engineering & Structural Dynamics 44.13 (2015): 2321-2340.
"""

import numpy as np
import pandas as pd

from . import shared





