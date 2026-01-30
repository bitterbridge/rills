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
                # Zombies attack somewhat randomly but with LLM deliberation
                prompt = (
                    f"You are {zombie.name}, a mindless zombie seeking fresh brains! 🧟\n\n"
                    f"You shamble through the night. Who do you attack?\n\n"
                    f"Potential victims: {', '.join(p.name for p in potential_victims)}\n\n"
                    f"Pick mostly randomly - you're driven by hunger, not strategy."
                )

                victim_name, reasoning = llm.get_player_choice_with_reasoning(
                    zombie,
                    prompt,
                    [p.name for p in potential_victims],
                    f"{zombie.name} choosing victim"
                )

                victim = game.get_player_by_name(victim_name)
                if victim:
                    print(f"🧟 Zombie {zombie.name} attacks {victim.name}!")
                    print(f"  💭 {zombie.name} thinks: {reasoning}")

                    # Gun Nut mechanic: check if victim fights back
                    counter_killed = None
                    if game.event_registry:
                        from . import GunNutEvent
                        for event in game.event_registry.get_active_events():
                            if isinstance(event, GunNutEvent):
                                counter_killed = event.check_counter_attack(game, victim, zombie)
                                break

                    if counter_killed:
                        print(f"💥 {victim.name} fought back! Zombie {counter_killed.name} was killed!")
                        print(f"💀 {counter_killed.name} was a {counter_killed.role.value} (now a zombie)!")
                        # Remove zombie from active zombies
                        if counter_killed in self._active_zombies:
                            self._active_zombies.remove(counter_killed)
                        game.eliminate_player(
                            counter_killed,
                            f"{victim.name} (Gun Nut) killed them in self-defense.",
                            f"Zombie {counter_killed.name} was destroyed. They were {counter_killed.role.display_name()}."
                        )
                        # Gun Nut knows they killed a zombie
                        victim.add_memory(f"You shot and killed zombie {counter_killed.name} who attacked you last night!")
                        # Others know the zombie was destroyed
                        for player in game.get_alive_players():
                            if player != victim:
                                player.add_memory(f"Zombie {counter_killed.name} was destroyed. They were {counter_killed.role.display_name()}.")
                    else:
                        # Mark victim as infected (they'll rise when they die)
                        victim.is_zombie = True

                        # Kill the victim
                        print(f"💀 {victim.name} was {victim.role.display_name()}!")
                        game.eliminate_player(
                            victim,
                            f"They were killed by zombie {zombie.name}.",
                            f"{victim.name} was found dead. They were {victim.role.display_name()}."
                        )
