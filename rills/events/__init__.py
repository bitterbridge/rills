"""Event system for random game modifiers."""

from .base import EventModifier, EventRegistry
from .zombie import ZombieEvent
from .ghost import GhostEvent
from .sleepwalker import SleepwalkerEvent
from .insomniac import InsomniacEvent
from .gun_nut import GunNutEvent
from .suicidal import SuicidalEvent
from .drunk import DrunkEvent
from .jester import JesterEvent
from .priest import PriestEvent
from .lovers import LoversEvent
from .bodyguard import BodyguardEvent

__all__ = [
    "EventModifier",
    "EventRegistry",
    "ZombieEvent",
    "GhostEvent",
    "SleepwalkerEvent",
    "InsomniacEvent",
    "GunNutEvent",
    "SuicidalEvent",
    "DrunkEvent",
    "JesterEvent",
    "PriestEvent",
    "LoversEvent",
    "BodyguardEvent",
]
