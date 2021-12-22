from enum import Enum


class EventType(Enum):
    """Event types for hypocentre distributions"""
    STRIKE_SLIP = "STRIKE_SLIP"
    DIP_SLIP = "DIP_SLIP"
    ALL = "ALL"

    @classmethod
    def from_rake(cls, rake: float):
        """Converts a rake value to an event type"""
        if -30 <= rake <= 30 or 150 <= rake <= 210:
            return EventType.STRIKE_SLIP
        elif 60 <= rake <= 120 or -120 <= rake <= -60:
            return EventType.DIP_SLIP
        else:
            return EventType.ALL
