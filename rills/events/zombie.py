"""Zombie event - dead zombies rise again."""

from typing import TYPE_CHECKING, Optional
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from ..roles import Role
    from ..llm import LLMAgent


class ZombieEvent(EventModifier):
    """Zombie infection event.

    One player starts infected. When they die, they rise as a zombie
    and attack each night. Victims also become zombies, creating
    exponential spread.
    """

    def __init__(self, probability: float = 0.10):
        super().__init__(probability)
        self._active_zombies: list["Player"] = []  # Currently undead zombies
        self._pending_rise: list["Player"] = []  # Will rise next night

    @property
    def name(self) -> str:
        return "Zombie Mode"

    @property
    def description(self) -> str:
        return "Dead zombies will rise again..."

    def setup_game(self, game: "GameState") -> None:
        """No special setup needed for zombie mode."""
        pass

    def on_player_eliminated(
        self,
        game: "GameState",
        player: "Player",
        reason: str
    ) -> None:
        """When an infected player dies, they will rise as a zombie."""
        if not player.is_zombie:
            return

        # Mark them to rise as a zombie
        self._pending_rise.append(player)

        # Different timing based on how they died
        if "lynched" in reason:
            print(f"🧟 {player.name} was infected! Their corpse will rise tonight...")
        else:
            print(f"🧟 {player.name} was infected! They will rise tomorrow night...")

    def on_night_start(self, game: "GameState") -> None:
        """Rise pending zombies at night start."""
        for zombie in self._pending_rise:
            self._active_zombies.append(zombie)
            print(f"🧟 {zombie.name}'s corpse rises from the grave!")

        self._pending_rise.clear()

    def handle_zombie_attacks(
        self,
        game: "GameState",
        llm: "LLMAgent"
    ) -> None:
        """Let all active zombies attack (mostly random)."""
        for zombie in self._active_zombies:
            # Find potential victims (anyone alive who isn't already undead)
            potential_victims = [
                p for p in game.get_alive_players()
                if p not in self._active_zombies and p != zombie
            ]

            if potential_victims:
                # Zombies attack somewhat randomly - pick from available targets
                victim = random.choice(potential_victims)

                print(f"🧟 Zombie {zombie.name} attacks {victim.name}!")

                # Mark victim as infected (they'll rise when they die)
                victim.is_zombie = True

                # Kill the victim
                game.eliminate_player(
                    victim,
                    f"They were killed by zombie {zombie.name}.",
                    f"{victim.name} was found dead."
                )
