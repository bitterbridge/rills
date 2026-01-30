"""Information and visibility models for tracking game knowledge."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import uuid4


class InfoCategory(Enum):
    """Categories of information in the game."""

    DEATH = "death"
    ROLE_REVEAL = "role_reveal"
    VOTE = "vote"
    STATEMENT = "statement"
    ACTION = "action"
    NIGHT_RESULT = "night_result"
    TEAM_INFO = "team_info"
    GAME_STATE = "game_state"


@dataclass
class Visibility:
    """Defines who can see a piece of information."""

    scope: Literal["public", "private", "team", "role"]
    targets: list[str] = field(
        default_factory=list,
    )  # Player names for private/team, empty for public

    def is_visible_to(
        self,
        player_name: str,
        player_team: str | None = None,
        player_role: str | None = None,
    ) -> bool:
        """Check if information is visible to a specific player."""
        if self.scope == "public":
            return True
        elif self.scope == "private":
            return player_name in self.targets
        elif self.scope == "team":
            return player_team in self.targets if player_team else False
        else:  # self.scope == "role"
            return player_role in self.targets if player_role else False


@dataclass
class Information:
    """A piece of information in the game."""

    id: str
    content: str
    timestamp: datetime
    source: str  # Who/what generated this (player name, "game", "event:zombie", etc.)
    visibility: Visibility
    category: InfoCategory
    day_number: int = 0
    revealed_to: set[str] = field(default_factory=set)  # Player names who have access
    metadata: dict = field(default_factory=dict)  # Additional contextual data

    @classmethod
    def create(
        cls,
        content: str,
        source: str,
        category: InfoCategory,
        visibility: Visibility,
        day_number: int = 0,
        **metadata,
    ) -> "Information":
        """Factory method to create Information with auto-generated ID."""
        return cls(
            id=str(uuid4()),
            content=content,
            timestamp=datetime.now(),
            source=source,
            visibility=visibility,
            category=category,
            day_number=day_number,
            revealed_to=set(),
            metadata=metadata,
        )


class InformationStore:
    """Central store of all information in the game."""

    def __init__(self):
        self._info: dict[str, Information] = {}
        self._by_category: dict[InfoCategory, list[str]] = {cat: [] for cat in InfoCategory}
        self._by_day: dict[int, list[str]] = {}

    def add(self, info: Information) -> str:
        """Add information to the store and return its ID."""
        self._info[info.id] = info
        self._by_category[info.category].append(info.id)

        if info.day_number not in self._by_day:
            self._by_day[info.day_number] = []
        self._by_day[info.day_number].append(info.id)

        return info.id

    def get(self, info_id: str) -> Information | None:
        """Get information by ID."""
        return self._info.get(info_id)

    def get_visible_to(
        self,
        player_name: str,
        player_team: str | None = None,
        player_role: str | None = None,
    ) -> list[Information]:
        """Get all information visible to a player."""
        visible = []
        for info in self._info.values():
            if info.visibility.is_visible_to(player_name, player_team, player_role):
                visible.append(info)
        return sorted(visible, key=lambda i: i.timestamp)

    def query(
        self,
        category: InfoCategory | None = None,
        after: datetime | None = None,
        before: datetime | None = None,
        day_number: int | None = None,
        visible_to: str | None = None,
        player_team: str | None = None,
        player_role: str | None = None,
        source: str | None = None,
    ) -> list[Information]:
        """Query information store with filters."""
        results = []

        # Start with category filter for efficiency
        if category:
            info_ids = self._by_category[category]
            candidates = [self._info[iid] for iid in info_ids]
        elif day_number is not None:
            info_ids = self._by_day.get(day_number, [])
            candidates = [self._info[iid] for iid in info_ids]
        else:
            candidates = list(self._info.values())

        # Apply filters
        for info in candidates:
            if after and info.timestamp < after:
                continue
            if before and info.timestamp > before:
                continue
            if day_number is not None and info.day_number != day_number:
                continue
            if source and info.source != source:
                continue
            if visible_to and not info.visibility.is_visible_to(
                visible_to,
                player_team,
                player_role,
            ):
                continue

            results.append(info)

        return sorted(results, key=lambda i: i.timestamp)

    def get_by_category(self, category: InfoCategory) -> list[Information]:
        """Get all information of a specific category."""
        return [self._info[iid] for iid in self._by_category[category]]

    def get_by_day(self, day_number: int) -> list[Information]:
        """Get all information from a specific day."""
        return [self._info[iid] for iid in self._by_day.get(day_number, [])]

    def count(self) -> int:
        """Get total count of information items."""
        return len(self._info)

    def clear(self):
        """Clear all information (for testing)."""
        self._info.clear()
        self._by_category = {cat: [] for cat in InfoCategory}
        self._by_day.clear()
