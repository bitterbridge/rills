"""Bodyguard event - can protect someone by sacrificing themselves."""

from typing import TYPE_CHECKING
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class BodyguardEvent(EventModifier):
    """Bodyguard event.

    One random villager is a Bodyguard. If they successfully
    protect someone from an Assassin attack, they die in their
    place. This is a one-time protection that removes the
    Bodyguard from the game.
    """

    def __init__(self):
        super().__init__()
        self._protected_player: str | None = None
        self._bodyguard_name: str | None = None

    @property
    def name(self) -> str:
        return "Bodyguard Mode"

    @property
    def description(self) -> str:
        return "Someone is willing to die for others..."

    def setup_game(self, game: "GameState") -> None:
        """Assign bodyguard flag to a random villager."""
        available = [
            p for p in game.players
            if p.team == "village"
            and not p.suicidal
            and not p.is_sleepwalker
            and not p.is_insomniac
            and not p.is_gun_nut
            and not p.is_drunk
            and not p.is_jester
            and not p.is_priest
        ]

        if available:
            bodyguard = random.choice(available)
            bodyguard.is_bodyguard = True
            bodyguard.bodyguard_active = True
            self._bodyguard_name = bodyguard.name

    def on_player_eliminated(
        self, game: "GameState", player: "Player", reason: str
    ) -> None:
        """No special behavior on elimination."""
        pass

    def set_protection(self, target_name: str) -> None:
        """Set who the bodyguard is protecting tonight.

        Args:
            target_name: Name of player to protect
        """
        self._protected_player = target_name

    def check_protection(
        self, game: "GameState", target_name: str
    ) -> tuple[bool, str | None]:
        """Check if bodyguard protects and sacrifices themselves.

        Args:
            game: The game state
            target_name: Name of player being attacked

        Returns:
            (protected, bodyguard_name) - True if protected and bodyguard dies
        """
        if target_name != self._protected_player:
            return False, None

        # Find the bodyguard
        bodyguard = next(
            (p for p in game.players if p.name == self._bodyguard_name and p.alive),
            None
        )

        if not bodyguard:
            return False, None

        if not hasattr(bodyguard, 'bodyguard_active') or not bodyguard.bodyguard_active:
            return False, None

        # Bodyguard sacrifices themselves!
        bodyguard.alive = False
        bodyguard.bodyguard_active = False

        return True, bodyguard.name

    def get_bodyguard_context(self, player: "Player") -> str:
        """Get bodyguard-specific context.

        Args:
            player: The player to get context for

        Returns:
            Context string if player is active bodyguard
        """
        if not hasattr(player, 'is_bodyguard') or not player.is_bodyguard:
            return ""

        if not hasattr(player, 'bodyguard_active') or not player.bodyguard_active:
            return ""

        return (
            "\n🛡️  SECRET ROLE: You are the BODYGUARD!\n"
            "Each night you can protect one player.\n"
            "If they are attacked by Assassins, you will DIE IN THEIR PLACE.\n"
            "This is a ONE-TIME protection - choose wisely!\n"
            "After you sacrifice yourself, your power is gone.\n"
        )
