"""Base classes for event system."""

import random
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from ..services.effect_service import Effect


class EventModifier(ABC):
    """Base class for game event modifiers.

    Events are special conditions that modify game behavior.
    Each event has a probability of occurring and can affect
    players, game state, or both.
    """

    def __init__(self, probability: float = 0.10) -> None:
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
    def on_player_eliminated(self, game: "GameState", player: "Player", reason: str) -> None:
        """Called when a player is eliminated.

        Use this to trigger event-specific effects.

        NOTE: This method is being phased out in favor of
        on_player_eliminated_effects(). For now, both are called.
        """
        pass

    def on_night_start(self, game: "GameState") -> None:
        """Called at the start of night phase.

        Override to add night-specific behavior.

        NOTE: This method is being phased out in favor of
        on_night_start_effects(). For now, both are called.
        """
        pass

    def on_night_end(self, game: "GameState") -> None:
        """Called at the end of night phase.

        Override to add night-end behavior.

        NOTE: This method is being phased out in favor of
        on_night_end_effects(). For now, both are called.
        """
        pass

    # New effect-based methods (override these for new events)

    def on_player_eliminated_effects(
        self, game: "GameState", player: "Player", reason: str
    ) -> list["Effect"]:
        """Return effects to apply when a player is eliminated.

        This is the new effect-based approach that will replace
        on_player_eliminated() over time.

        Returns:
            List of Effect objects to apply
        """
        return []

    def on_night_start_effects(self, game: "GameState") -> list["Effect"]:
        """Return effects to apply at night start.

        This is the new effect-based approach that will replace
        on_night_start() over time.

        Returns:
            List of Effect objects to apply
        """
        return []

    def on_night_end_effects(self, game: "GameState") -> list["Effect"]:
        """Return effects to apply at night end.

        This is the new effect-based approach that will replace
        on_night_end() over time.

        Returns:
            List of Effect objects to apply
        """
        return []


class EventRegistry:
    """Registry for managing game events."""

    def __init__(self) -> None:
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
        self, game: "GameState", player: "Player", reason: str
    ) -> list["Effect"]:
        """Notify all active events of player elimination.

        Returns:
            List of Effect objects to apply from all events
        """
        effects = []
        for event in self.get_active_events():
            # Call old method for backward compatibility
            event.on_player_eliminated(game, player, reason)
            # Collect effects from new method
            effects.extend(event.on_player_eliminated_effects(game, player, reason))
        return effects

    def on_night_start(self, game: "GameState") -> list["Effect"]:
        """Notify all active events of night start.

        Returns:
            List of Effect objects to apply from all events
        """
        effects = []
        for event in self.get_active_events():
            # Call old method for backward compatibility
            event.on_night_start(game)
            # Collect effects from new method
            effects.extend(event.on_night_start_effects(game))
        return effects

    def on_night_end(self, game: "GameState") -> list["Effect"]:
        """Notify all active events of night end.

        Returns:
            List of Effect objects to apply from all events
        """
        effects = []
        for event in self.get_active_events():
            # Call old method for backward compatibility
            event.on_night_end(game)
            # Collect effects from new method
            effects.extend(event.on_night_end_effects(game))
        return effects
