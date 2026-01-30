"""Suicidal event - a player may take their own life."""

import random
from typing import TYPE_CHECKING

from ..models import PlayerModifier
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from ..services.effect_service import Effect


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
            suicidal.suicidal = True  # Old flag (backward compatibility)
            suicidal.add_modifier(
                game, PlayerModifier(type="suicidal", source="event:suicidal")
            )  # NEW: permanent modifier

    def on_player_eliminated(self, game: "GameState", player: "Player", reason: str) -> None:
        """No special behavior on elimination."""
        pass

    def on_night_end(self, game: "GameState") -> None:
        """Check if suicidal player commits suicide (20% chance)."""
        # Dual-check: old flag or new modifier
        suicidal_players = [
            p for p in game.get_alive_players() if p.suicidal or p.has_modifier(game, "suicidal")
        ]

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

    def on_night_end_effects(self, game: "GameState") -> list["Effect"]:
        """Return suicide effect if it occurs (20% chance)."""
        from ..services.effect_service import Effect

        # Dual-check: old flag or new modifier
        suicidal_players = [
            p for p in game.get_alive_players() if p.suicidal or p.has_modifier(game, "suicidal")
        ]

        if not suicidal_players:
            return []

        suicidal = suicidal_players[0]

        # 20% chance each night
        if random.random() < 0.2:
            return [
                Effect(
                    type="suicide_death",
                    target=suicidal.name,
                    source="suicidal_event",
                    data={
                        "cause": "They took their own life.",
                        "public_reason": f"{suicidal.name} was found dead.",
                        "day": game.day_number,
                        "print_message": f"☠️  {suicidal.name} was found dead!",
                    },
                )
            ]

        return []
