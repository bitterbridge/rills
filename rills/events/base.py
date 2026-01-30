"""Base classes for event system."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional
import random

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class EventModifier(ABC):
    """Base class for game event modifiers.

    Events are special conditions that modify game behavior.
    Each event has a probability of occurring and can affect
    players, game state, or both.
    """

    def __init__(self, probability: float = 0.10):
        """Initialize event modifier.

        Args:
            probability: Chance this event is active in a game (0.0 to 1.0)
        """
        self.probability = probability
        self.active = False

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the event."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this event does."""
        pass

    def should_activate(self) -> bool:
        """Determine if this event should be active this game."""
        return random.random() < self.probability

    def activate(self) -> None:
        """Mark this event as active for the current game."""
        self.active = True

    @abstractmethod
    def setup_game(self, game: "GameState") -> None:
        """Called when game is created if event is active.

        Use this to assign event-specific roles to players.
        """
        pass

    @abstractmethod
    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """Called when a player is eliminated.

        Use this to trigger event-specific effects.
        """
        pass

    def on_night_start(self, game: "GameState") -> None:
        """Called at the start of night phase.

        Override to add night-specific behavior.
        """
        pass

    def on_night_end(self, game: "GameState") -> None:
        """Called at the end of night phase.

        Override to add night-end behavior.
        """
        pass


class EventRegistry:
    """Registry for managing game events."""

    def __init__(self):
        """Initialize empty event registry."""
        self._events: list[EventModifier] = []

    def register(self, event: EventModifier) -> None:
        """Register an event modifier."""
        self._events.append(event)

    def activate_random_events(self) -> list[EventModifier]:
        """Randomly activate events based on their probabilities.

        Returns:
            List of activated events
        """
        activated = []
        for event in self._events:
            if event.should_activate():
                event.activate()
                activated.append(event)
        return activated

    def get_active_events(self) -> list[EventModifier]:
        """Get all currently active events."""
        return [e for e in self._events if e.active]

    def setup_game(self, game: "GameState") -> None:
        """Setup all active events for a new game."""
        for event in self.get_active_events():
            event.setup_game(game)

    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """Notify all active events of player elimination."""
        for event in self.get_active_events():
            event.on_player_eliminated(game, player, reason)

    def on_night_start(self, game: "GameState") -> None:
        """Notify all active events of night start."""
        for event in self.get_active_events():
            event.on_night_start(game)

    def on_night_end(self, game: "GameState") -> None:
        """Notify all active events of night end."""
        for event in self.get_active_events():
            event.on_night_end(game)
