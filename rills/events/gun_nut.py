"""Gun Nut event - a player can fight back."""

from typing import TYPE_CHECKING, Optional
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class GunNutEvent(EventModifier):
    """Gun Nut event.

    One random villager is armed. If assassins target them,
    there's a 50% chance a random assassin dies instead.
    """

    def __init__(self):
        super().__init__()
        self._pending_counter_attack: Optional["Player"] = None

    @property
    def name(self) -> str:
        return "Gun Nut Mode"

    @property
    def description(self) -> str:
        return "Someone is armed and dangerous..."

    def setup_game(self, game: "GameState") -> None:
        """Assign gun nut to a random non-suicidal villager."""
        available = [
            p for p in game.players
            if p.team == "village"
            and not p.suicidal
            and not p.is_sleepwalker
            and not p.is_insomniac
            and not p.is_drunk
            and not p.is_jester
            and not p.is_priest
            and not p.is_bodyguard
        ]

        if available:
            gun_nut = random.choice(available)
            gun_nut.is_gun_nut = True

    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """No special behavior - counter attack is handled in phases."""
        pass

    def check_counter_attack(
        self,
        game: "GameState",
        target: "Player"
    ) -> Optional["Player"]:
        """Check if gun nut fights back when targeted.

        Returns the assassin who dies, if any.
        """
        from ..roles import Role

        if not target.is_gun_nut:
            return None

        if random.random() < 0.50:
            assassins = [p for p in game.get_alive_players() if p.role == Role.ASSASSINS]
            if assassins:
                return random.choice(assassins)

        return None
