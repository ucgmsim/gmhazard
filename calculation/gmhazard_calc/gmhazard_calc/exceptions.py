class GMHazardError(BaseException):
    """Base GMHazard error"""

    def __init__(self, message: str):
        self.message = message


class ExceedanceOutOfRangeError(GMHazardError):
    """Raised when the specified exceedance value is out of range when
    going from exceedance to IM on the hazard curve"""

    def __init__(self, im: str, exceedance: float, message: str):
        super().__init__(message)

        self.exceedance = exceedance
        self.im = im
