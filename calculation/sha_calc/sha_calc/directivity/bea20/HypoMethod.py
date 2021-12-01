from enum import Enum


class HypoMethod(Enum):
    """Hypocentre placement methods"""

    LATIN_HYPERCUBE = "LATIN_HYPERCUBE"
    MONTE_CARLO = "MONTE_CARLO"
    GRID = "GRID"
    MONTE_CARLO_GRID = "MONTE_CARLO_GRID"
