"""Priest event - can resurrect a dead player once per game."""

import random
from typing import TYPE_CHECKING, Optional

from ..models import PlayerModifier
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class PriestEvent(EventModifier):
    """Priest event.

    One random villager is a Priest who can resurrect one dead
    player during a day phase. They don't know they have this
    power until they attempt to use it.
    """

    def __init__(self) -> None:
        super().__init__()
        self._resurrection_used = False

    @property
    def name(self) -> str:
        return "Priest Mode"

    @property
    def description(self) -> str:
        return "Someone has the power to bring back the dead..."

    def setup_game(self, game: "GameState") -> None:
        """Assign priest flag to a random villager."""
        available = [
            p
            for p in game.players
            if p.team == "village"
            and not p.suicidal
            and not p.is_sleepwalker
            and not p.is_insomniac
            and not p.is_gun_nut
            and not p.is_drunk
            and not p.is_jester
            and not p.is_bodyguard
        ]

        if available:
            priest = random.choice(available)
            priest.is_priest = True  # Old flag (backward compatibility)
            priest.resurrection_available = True
            priest.add_modifier(
                game,
                PlayerModifier(
                    type="priest", source="event:priest", data={"resurrections_available": 1}
                ),
            )  # NEW: permanent modifier with resurrection count

    def on_player_eliminated(self, game: "GameState", player: "Player", reason: str) -> None:
        """No special behavior on elimination."""
        pass

    def attempt_resurrection(
        self, priest: "Player", target_name: str, game: "GameState"
    ) -> Optional["Player"]:
        """Attempt to resurrect a dead player.

        Args:
            priest: The priest attempting resurrection
            target_name: Name of the dead player to resurrect
            game: The game state

        Returns:
            The resurrected player if successful, None otherwise
        """
        # Dual-check: old flag or new modifier
        is_priest = (hasattr(priest, "is_priest") and priest.is_priest) or priest.has_modifier(
            game, "priest"
        )
        if not is_priest:
            return None

        if not hasattr(priest, "resurrection_available") or not priest.resurrection_available:
            return None

        if self._resurrection_used:
            return None

        # Find the dead player
        target = next((p for p in game.players if p.name == target_name and not p.alive), None)
        if not target:
            return None

        # Resurrect them!
        target.alive = True
        priest.resurrection_available = False
        self._resurrection_used = True

        print(f"\n✨ {priest.name} reveals themselves as the PRIEST!")
        print(f"🙏 {priest.name} has resurrected {target.name} from the dead!\n")

        return target

    def can_resurrect(self, priest: "Player") -> bool:
        """Check if priest can still resurrect.

        Args:
            priest: The player to check

        Returns:
            True if they can resurrect, False otherwise
        """
        return (
            hasattr(priest, "is_priest")
            and priest.is_priest
            and hasattr(priest, "resurrection_available")
            and priest.resurrection_available
            and not self._resurrection_used
        )

    def get_priest_context(self, player: "Player", game: "GameState") -> str:
        """Get priest-specific context.

        Args:
            player: The player to get context for
            game: The game state

        Returns:
            Context string if player is priest with power available
        """
        if not self.can_resurrect(player):
            return ""

        dead_players = [p for p in game.players if not p.alive]
        if not dead_players:
            return ""

        dead_names = ", ".join(p.name for p in dead_players)
        return (
            f"\n⚠️  SECRET POWER: You are the PRIEST!\n"
            f"You can resurrect ONE dead player during a day phase.\n"
            f"Dead players: {dead_names}\n"
            f"Use this power wisely - you only get one resurrection!\n"
        )
