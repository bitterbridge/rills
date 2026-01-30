"""Action result models for phase execution."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..models import ConversationRound, VoteResult
    from ..player import Player


@dataclass
class NightResult:
    """Results of a night phase."""

    assassin_target: Optional["Player"] = None
    doctor_target: Optional["Player"] = None
    vigilante_target: Optional["Player"] = None
    detective_result: str | None = None
    deaths: list["Player"] = field(default_factory=list)
    counter_kills: list["Player"] = field(default_factory=list)


@dataclass
class DayResult:
    """Results of a day phase."""

    discussion_rounds: list["ConversationRound"] = field(default_factory=list)
    vote_result: Optional["VoteResult"] = None
    eliminated: Optional["Player"] = None
