from enum import Enum, auto
from typing import Optional, List


class IMType(Enum):
    """Available IMs to use"""

    PGA = "PGA"
    PGV = "PGV"
    pSA = "pSA"
    CAV = "CAV"
    AI = "AI"
    ASI = "ASI"
    DSI = "DSI"
    SI = "SI"
    Ds575 = "Ds575"
    Ds595 = "Ds595"

    def __str__(self):
        """Ensures that we return PGA not IMType.PGA"""
        return self.name

    @classmethod
    def has_value(cls, value: str):
        """Checks if the value is in the IMType set"""
        available_names = set(im.name for im in IMType)
        if value.startswith("pSA"):
            value = "pSA"
        return value in available_names


class IMComponent(Enum):
    """Available components to use"""

    RotD50 = "RotD50"
    RotD100 = "RotD100"
    Larger = "Larger"

    def __str__(self):
        """Ensures that we return RotD50 not IMComponent.RotD50"""
        return self.name


class IM:
    """
    Represents an IM to use for calculations
    """

    def __init__(
        self,
        im_type: IMType,
        period: Optional[float] = None,
        component: Optional[IMComponent] = IMComponent.RotD50,
    ):
        self.im_type = im_type
        self.period = period
        self.component = component

        if im_type == IMType.pSA and period is None:
            raise ValueError("Creation of pSA IM does not have a specified period")

    @classmethod
    def from_str(cls, im_string: str):
        """Converts a given string to an IM object"""
        period = None
        if im_string.startswith("pSA") and "_" in im_string:
            im_string, period = im_string.split("_")
            period = float(period.replace("p", "."))
        return cls(IMType[im_string], period)

    def __str__(self):
        """Overrides the string method by just returning the name instead of the object"""
        if self.period:
            return f"{self.im_type}_{self.period}"
        else:
            return f"{self.im_type}"

    def __hash__(self):
        return hash((self.im_type, self.period, self.component))

    def __eq__(self, other):
        return (self.im_type, self.period, self.component) == (other.im_type, other.period, other.component,)

    def __ne__(self, other):
        return not self.__eq__(other)

    def file_format(self):
        """
        Outputs the normal str version of the IM
        Except does a replace on the period for p instead of . for saving in file formats
        """
        return str(self).replace(".", "p")

    def is_pSA(self):
        """Returns True if IM is of type pSA otherwise False"""
        return self.im_type == IMType.pSA


def to_string_list(IMs: List[IM]):
    """Converts a list of IM Objects to their string form"""
    return [str(im) for im in IMs]


def to_im_list(IMs: List[str]):
    """Converts a list of string to IM Objects"""
    return [IM.from_str(im) for im in IMs]


# Available IM Components per IMType
IM_COMPONENT_MAPPING = {
    IMType.PGA: [IMComponent.RotD50, IMComponent.RotD100, IMComponent.Larger],
    IMType.pSA: [IMComponent.RotD50, IMComponent.RotD100, IMComponent.Larger],
    IMType.PGV: [IMComponent.RotD50],
    IMType.AI: [IMComponent.RotD50],
    IMType.ASI: [IMComponent.RotD50],
    IMType.CAV: [IMComponent.RotD50],
    IMType.Ds575: [IMComponent.RotD50],
    IMType.Ds595: [IMComponent.RotD50],
    IMType.DSI: [IMComponent.RotD50],
    IMType.SI: [IMComponent.RotD50],
}
