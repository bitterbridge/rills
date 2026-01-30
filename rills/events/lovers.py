"""Lovers event - two players are linked and die together."""

from typing import TYPE_CHECKING, Optional
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class LoversEvent(EventModifier):
    """Lovers event.

    Two random players (any role) are secretly in love. If one
    dies, the other dies of heartbreak the following night.
    They don't know who their lover is at first.
    """

    def __init__(self):
        super().__init__()
        self._pending_heartbreak: Optional[str] = None  # Name of lover who will die
        self._heartbreak_ready: bool = False  # Whether to execute heartbreak this night

    @property
    def name(self) -> str:
        return "Lovers Mode"

    @property
    def description(self) -> str:
        return "Two souls are bound together..."

    def setup_game(self, game: "GameState") -> None:
        """Assign lover flags to two random players."""
        if len(game.players) < 2:
            return

        # Choose two random players (any role)
        lover1, lover2 = random.sample(game.players, 2)

        lover1.is_lover = True
        lover1.lover_name = lover2.name

        lover2.is_lover = True
        lover2.lover_name = lover1.name

    def on_player_eliminated(
        self, game: "GameState", player: "Player", reason: str
    ) -> None:
        """Mark the other lover for death if one dies."""
        if not hasattr(player, 'is_lover') or not player.is_lover:
            return

        if not hasattr(player, 'lover_name'):
            return

        # Find the other lover
        lover = next(
            (p for p in game.players if p.name == player.lover_name and p.alive),
            None
        )

        if lover:
            self._pending_heartbreak = lover.name
            print(f"\n💔 {player.name}'s death will break someone's heart...\n")

    def on_night_start(self, game: "GameState") -> None:
        """Mark heartbreak as ready at the start of each new night."""
        if self._pending_heartbreak:
            self._heartbreak_ready = True

    def on_night_end(self, game: "GameState") -> None:
        """Kill the other lover from heartbreak (delayed one night)."""
        if not self._pending_heartbreak or not self._heartbreak_ready:
            return

        lover = next(
            (p for p in game.players if p.name == self._pending_heartbreak and p.alive),
            None
        )

        if lover:
            lover.alive = False
            print(f"\n💔 {lover.name} died of a broken heart after losing their beloved!\n")

        self._pending_heartbreak = None
        self._heartbreak_ready = False

    def get_lover_context(self, player: "Player") -> str:
        """Get lover-specific context.

        Args:
            player: The player to get context for

        Returns:
            Context string if player is a lover
        """
        if not hasattr(player, 'is_lover') or not player.is_lover:
            return ""

        lover_name = getattr(player, 'lover_name', 'unknown')
        return (
            f"\n💕 SECRET: You are in love with {lover_name}!\n"
            f"If {lover_name} dies, you will die of heartbreak the following night.\n"
            f"Try to keep {lover_name} alive - your fates are linked!\n"
        )
