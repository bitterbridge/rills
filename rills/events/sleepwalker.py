"""Sleepwalker event - a player wanders at night."""

from typing import TYPE_CHECKING
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class SleepwalkerEvent(EventModifier):
    """Sleepwalker event.

    One random villager is a sleepwalker who moves around
    at night but doesn't do anything. Creates noise/distraction.
    """

    @property
    def name(self) -> str:
        return "Sleepwalker Mode"

    @property
    def description(self) -> str:
        return "Someone wanders at night..."

    def setup_game(self, game: "GameState") -> None:
        """Assign sleepwalker to a random non-suicidal villager."""
        available = [
            p for p in game.players
            if p.team == "village" and not p.suicidal
        ]

        if available:
            sleepwalker = random.choice(available)
            sleepwalker.is_sleepwalker = True

    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """No special behavior on elimination."""
        pass

    def on_night_start(self, game: "GameState") -> None:
        """Announce sleepwalker movement."""
        sleepwalkers = [p for p in game.get_alive_players() if p.is_sleepwalker]

        if sleepwalkers:
            for sleepwalker in sleepwalkers:
                print(f"🌙 {sleepwalker.name} is sleepwalking...")
