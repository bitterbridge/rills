"""Suicidal event - a player may take their own life."""

from typing import TYPE_CHECKING
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class SuicidalEvent(EventModifier):
    """Suicidal villager event.

    One random villager has suicidal tendencies and has a 20%
    chance each night of taking their own life.
    """

    @property
    def name(self) -> str:
        return "Suicidal Mode"

    @property
    def description(self) -> str:
        return "Someone struggles with dark thoughts..."

    def setup_game(self, game: "GameState") -> None:
        """Assign suicidal flag to a random villager."""
        villagers = [p for p in game.players if p.team == "village"]
        if villagers:
            suicidal = random.choice(villagers)
            suicidal.suicidal = True

    def on_player_eliminated(
        self, game: "GameState", player: "Player", reason: str
    ) -> None:
        """No special behavior on elimination."""
        pass

    def on_night_end(self, game: "GameState") -> None:
        """Check if suicidal player commits suicide (20% chance)."""
        suicidal_players = [p for p in game.get_alive_players() if p.suicidal]

        if not suicidal_players:
            return

        suicidal = suicidal_players[0]

        # 20% chance each night
        if random.random() < 0.2:
            # Don't reveal it's a suicide - just another mysterious death
            print(f"☠️  {suicidal.name} was found dead!")
            game.eliminate_player(
                suicidal, "They took their own life.", f"{suicidal.name} was found dead."
            )
