from dataclasses import dataclass

from .HypoMethod import HypoMethod


@dataclass
class NHypoData:
    """
    Class for keeping track of the
    correct number of hypocentre parameters
    for their method of placement
    """
    method: HypoMethod
    nhypo: int = None
    hypo_along_strike: int = None
    hypo_down_dip: int = None
    seed: int = None

    def __post_init__(self):
        """
        Checks to ensure that the given parameters are correct for the method specified
        """
        if self.method == HypoMethod.UNIFORM_GRID:
            if self.hypo_along_strike is None or self.hypo_down_dip is None:
                raise ValueError(
                    f"hypo_along_strike and hypo_down_dip need to be defined for {str(self.method)}"
                )
            else:
                self.nhypo = self.hypo_along_strike * self.hypo_down_dip
        elif (
            self.method == HypoMethod.LATIN_HYPERCUBE
            or self.method == HypoMethod.MONTE_CARLO
        ):
            if self.nhypo is None:
                raise ValueError(f"nhypo needs to be defined for {str(self.method)}")
