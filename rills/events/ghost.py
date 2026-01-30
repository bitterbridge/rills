"""Ghost event - dead players may haunt the living."""

from typing import TYPE_CHECKING, Optional
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from ..llm import LLMAgent


class GhostEvent(EventModifier):
    """Ghost haunting event.

    When a player dies, they have a 10% chance to become
    a ghost that can haunt a living player of their choice.
    """

    def __init__(self, probability: float = 0.10):
        super().__init__(probability)
        self._pending_ghost: Optional["Player"] = None

    @property
    def name(self) -> str:
        return "Ghost Mode"

    @property
    def description(self) -> str:
        return "The dead may linger..."

    def setup_game(self, game: "GameState") -> None:
        """No special setup needed for ghost mode."""
        pass

    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """10% chance for eliminated player to become a ghost."""
        if random.random() < 0.10:
            player.is_ghost = True
            self._pending_ghost = player
            print(f"\n👻 {player.name}'s spirit rises as a ghost...")

    def handle_ghost_choice(
        self,
        game: "GameState",
        llm: "LLMAgent"
    ) -> None:
        """Let pending ghost choose who to haunt."""
        if not self._pending_ghost:
            return

        player = self._pending_ghost
        alive = game.get_alive_players()

        if alive:
            prompt = (
                f"You are {player.name}, and you have just died. However, your spirit lingers as a ghost.\n\n"
                f"You must choose one living player to haunt. You cannot speak or provide any information, "
                f"but your presence will be felt.\n\n"
                f"Living players: {', '.join(p.name for p in alive)}\n\n"
                f"Who do you choose to haunt?"
            )

            haunted_name = llm.get_player_choice(
                player,
                prompt,
                [p.name for p in alive],
                f"{player.name} choosing who to haunt"
            )

            player.haunting_target = haunted_name
            print(f"👻 {player.name} chooses to haunt {haunted_name}...")

        self._pending_ghost = None
