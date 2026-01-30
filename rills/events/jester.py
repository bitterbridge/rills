"""Jester event - a player wins if they get lynched."""

import random
from typing import TYPE_CHECKING

from ..models import PlayerModifier
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from ..services.effect_service import Effect


class JesterEvent(EventModifier):
    """Jester event.

    One random villager is secretly a Jester. Their goal is to
    get themselves lynched. If they succeed, they win and the
    game ends (everyone else loses).
    """

    def __init__(self) -> None:
        super().__init__()
        self._jester_won = False

    @property
    def name(self) -> str:
        return "Jester Mode"

    @property
    def description(self) -> str:
        return "Someone wants to be executed..."

    def setup_game(self, game: "GameState") -> None:
        """Assign jester flag to a random villager."""
        available = [
            p
            for p in game.players
            if p.team == "village"
            and not p.suicidal
            and not p.is_sleepwalker
            and not p.is_insomniac
            and not p.is_gun_nut
            and not p.is_drunk
            and not p.is_priest
            and not p.is_bodyguard
        ]

        if available:
            jester = random.choice(available)
            jester.is_jester = True  # Old flag (backward compatibility)
            jester.add_modifier(
                game,
                PlayerModifier(type="jester", source="event:jester"),
            )  # NEW: permanent modifier

    def on_player_eliminated(self, game: "GameState", player: "Player", reason: str) -> None:
        """Check if jester was lynched (backward compatibility)."""
        # Keep old behavior for now
        if reason == "lynched" and hasattr(player, "is_jester") and player.is_jester:
            self._jester_won = True
            print(f"\n🃏 {player.name} was the Jester and has WON by being lynched!")
            print("🎭 JESTER VICTORY! The game ends. Everyone else loses.\n")

    def on_player_eliminated_effects(
        self,
        game: "GameState",
        player: "Player",
        reason: str,
    ) -> list["Effect"]:
        """Return jester victory effect if jester was lynched."""
        from ..services.effect_service import Effect

        # Dual-check: old flag or new modifier
        is_jester = (hasattr(player, "is_jester") and player.is_jester) or player.has_modifier(
            game,
            "jester",
        )
        if reason == "lynched" and is_jester:
            # Return a game-ending effect
            return [
                Effect(
                    type="jester_victory",
                    target="game",
                    source="jester_event",
                    data={"winner": player.name},
                ),
            ]
        return []

    def check_jester_victory(self) -> bool:
        """Check if jester has won.

        Returns
        -------
            True if jester won, False otherwise

        """
        return self._jester_won

    def get_jester_context(self, player: "Player") -> str:
        """Get jester-specific context for the player.

        Args:
        ----
            player: The player to get context for

        Returns:
        -------
            Context string if player is jester, empty otherwise

        """
        if hasattr(player, "is_jester") and player.is_jester:
            return (
                "\n⚠️  SECRET ROLE: You are the JESTER!\n"
                "Your goal is to get yourself LYNCHED by the town during a day vote.\n"
                "If you succeed, YOU WIN and everyone else loses!\n"
                "Be suspicious, but not TOO obvious - you need them to vote for you.\n"
                "The Assassins and other roles don't matter to you - only getting lynched!\n"
            )
        return ""
