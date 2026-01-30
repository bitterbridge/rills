"""Game state and logic."""

from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from collections import Counter
import random

from .player import Player
from .roles import Role

if TYPE_CHECKING:
    from .events import EventRegistry


@dataclass
class GameState:
    """Represents the current state of the game."""

    players: list[Player]
    day_number: int = 1
    phase: str = "night"  # "night" or "day"
    game_over: bool = False
    winner: Optional[str] = None
    events: list[str] = field(default_factory=list)
    event_registry: Optional["EventRegistry"] = None

    def get_alive_players(self) -> list[Player]:
        """Get all players who are still alive."""
        return [p for p in self.players if p.alive]

    def get_alive_by_team(self, team: str) -> list[Player]:
        """Get all alive players on a specific team."""
        return [p for p in self.get_alive_players() if p.team == team]

    def get_player_by_name(self, name: str) -> Optional[Player]:
        """Find a player by name."""
        for player in self.players:
            if player.name.lower() == name.lower():
                return player
        return None

    def eliminate_player(self, player: Player, reason: str, public_reason: Optional[str] = None) -> None:
        """Eliminate a player from the game.

        Args:
            player: The player to eliminate
            reason: Full reason shown to humans
            public_reason: What players are told (defaults to vague message)
        """
        player.alive = False
        # Human-visible event with full details
        event = f"{player.name} ({player.role.value}) has been eliminated. {reason}"
        self.events.append(event)

        # Notify events of elimination
        if self.event_registry:
            self.event_registry.on_player_eliminated(self, player, reason)

        # Players only get vague information (not role or method)
        if public_reason is None:
            public_reason = f"{player.name} has been eliminated."

        for p in self.players:
            if p != player:
                p.add_memory(public_reason)

    def check_win_condition(self) -> bool:
        """Check if the game has been won."""
        alive_assassins = len(self.get_alive_by_team("assassins"))
        alive_village = len(self.get_alive_by_team("village"))

        if alive_assassins == 0:
            self.game_over = True
            self.winner = "village"
            self.events.append("The village has won! All Assassins have been eliminated.")
            return True

        if alive_assassins >= alive_village:
            self.game_over = True
            self.winner = "assassins"
            self.events.append("The Assassins have won! They equal or outnumber the villagers.")
            return True

        return False

    def advance_phase(self) -> None:
        """Move to the next phase of the game."""
        if self.phase == "night":
            self.phase = "day"
        else:
            self.phase = "night"
            self.day_number += 1

    def get_phase_description(self) -> str:
        """Get a description of the current phase."""
        if self.phase == "night":
            return f"Night {self.day_number}"
        else:
            return f"Day {self.day_number}"


def create_game(
    player_configs: list[dict],
    enable_zombie: bool = False,
    enable_ghost: bool = False,
    enable_sleepwalker: bool = False,
    enable_insomniac: bool = False,
    enable_gun_nut: bool = False,
    enable_suicidal: bool = False,
    enable_drunk: bool = False,
    enable_jester: bool = False,
    enable_priest: bool = False,
    enable_lovers: bool = False,
    enable_bodyguard: bool = False,
    chaos_mode: bool = False
) -> GameState:
    """
    Create a new game with the specified players.

    Args:
        player_configs: List of dicts with 'name', 'role', and 'personality' keys
        enable_zombie: Enable zombie event
        enable_ghost: Enable ghost event
        enable_sleepwalker: Enable sleepwalker event
        enable_insomniac: Enable insomniac event
        enable_gun_nut: Enable gun nut event
        enable_suicidal: Enable suicidal event
        enable_drunk: Enable drunk event
        enable_jester: Enable jester event
        enable_priest: Enable priest event
        enable_lovers: Enable lovers event
        enable_bodyguard: Enable bodyguard event
        chaos_mode: Enable all events (overrides individual flags)

    Returns:
        GameState instance
    """
    from .events import (
        EventRegistry,
        ZombieEvent,
        GhostEvent,
        SleepwalkerEvent,
        InsomniacEvent,
        GunNutEvent,
        SuicidalEvent,
        DrunkEvent,
        JesterEvent,
        PriestEvent,
        LoversEvent,
        BodyguardEvent,
    )

    # Randomly assign roles
    roles = [Role(config["role"]) for config in player_configs]
    random.shuffle(roles)

    # Randomly assign personalities
    personalities = [config["personality"] for config in player_configs]
    random.shuffle(personalities)

    # Create players with randomized roles and personalities
    players = [
        Player(
            name=config["name"],
            role=roles[i],
            personality=personalities[i]
        )
        for i, config in enumerate(player_configs)
    ]

    # Create event registry and register enabled events
    registry = EventRegistry()

    # In chaos mode, enable everything
    if chaos_mode:
        enable_zombie = True
        enable_ghost = True
        enable_sleepwalker = True
        enable_insomniac = True
        enable_gun_nut = True
        enable_suicidal = True
        enable_drunk = True
        enable_jester = True
        enable_priest = True
        enable_lovers = True
        enable_bodyguard = True

    if enable_zombie:
        registry.register(ZombieEvent())
    if enable_ghost:
        registry.register(GhostEvent())
    if enable_sleepwalker:
        registry.register(SleepwalkerEvent())
    if enable_insomniac:
        registry.register(InsomniacEvent())
    if enable_gun_nut:
        registry.register(GunNutEvent())
    if enable_suicidal:
        registry.register(SuicidalEvent())
    if enable_drunk:
        registry.register(DrunkEvent())
    if enable_jester:
        registry.register(JesterEvent())
    if enable_priest:
        registry.register(PriestEvent())
    if enable_lovers:
        registry.register(LoversEvent())
    if enable_bodyguard:
        registry.register(BodyguardEvent())

    # Activate all registered events (no random selection when manually specified)
    for event in registry._events:
        event.active = True

    # Create game state
    game = GameState(players=players, event_registry=registry)

    # Setup active events
    registry.setup_game(game)

    return game
