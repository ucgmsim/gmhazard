from enum import Enum


class HypoMethod(Enum):
    """Hypocentre placement methods"""

    LATIN_HYPERCUBE = "LATIN_HYPERCUBE"
    MONTE_CARLO = "MONTE_CARLO"
    UNIFORM_GRID = "UNIFORM_GRID"
