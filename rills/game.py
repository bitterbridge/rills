"""Game state and logic."""

import random
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .models.player_state import PlayerModifier, PlayerState
from .player import Player
from .roles import Role
from .services import ContextBuilder, ConversationService, InformationService, VoteService
from .services.effect_service import Effect

if TYPE_CHECKING:
    from .events import EventRegistry


@dataclass
class GameState:
    """Represents the current state of the game."""

    players: list[Player]
    day_number: int = 1
    phase: str = "night"  # "night" or "day"
    game_over: bool = False
    winner: str | None = None
    events: list[str] = field(default_factory=list)
    event_registry: Optional["EventRegistry"] = None

    # Player state management - NEW in Phase 5
    player_states: dict[str, PlayerState] = field(default_factory=dict)

    # Service layer - initialized in __post_init__
    info_service: InformationService = field(default_factory=InformationService, init=False)
    conversation_service: ConversationService = field(
        default_factory=ConversationService,
        init=False,
    )
    vote_service: VoteService = field(default_factory=VoteService, init=False)
    context_builder: ContextBuilder = field(init=False)

    def __post_init__(self) -> None:
        """Initialize services and register players."""
        # Initialize context builder with info service
        self.context_builder = ContextBuilder(self.info_service)

        # Register all players with information service
        for player in self.players:
            self.info_service.register_player(player.name)

        # Initialize PlayerState for each player - NEW in Phase 5
        for player in self.players:
            self.player_states[player.name] = PlayerState(
                name=player.name,
                role=player.role.value,
                team=player.team,
                alive=player.alive,
            )

    def get_alive_players(self) -> list[Player]:
        """Get all players who are still alive."""
        return [p for p in self.players if p.alive]

    def get_alive_by_team(self, team: str) -> list[Player]:
        """Get all alive players on a specific team."""
        return [p for p in self.get_alive_players() if p.team == team]

    def get_player_by_name(self, name: str) -> Player | None:
        """Find a player by name."""
        for player in self.players:
            if player.name.lower() == name.lower():
                return player
        return None

    def eliminate_player(
        self,
        player: Player,
        reason: str,
        public_reason: str | None = None,
    ) -> None:
        """Eliminate a player from the game.

        Args:
        ----
            player: The player to eliminate
            reason: Full reason shown to humans
            public_reason: What players are told (defaults to role reveal)

        """
        player.alive = False
        # Human-visible event with full details
        event = f"{player.name} ({player.role.value}) has been eliminated. {reason}"
        self.events.append(event)

        # Notify events of elimination and collect effects
        if self.event_registry:
            effects = self.event_registry.on_player_eliminated(self, player, reason)
            # Apply effects from events
            self.apply_event_effects(effects)

        # Use InformationService to reveal death with role
        self.info_service.reveal_death(
            player_name=player.name,
            role=player.role.display_name(),
            cause=reason,
            day=self.day_number,
        )
        # Note: Death information automatically tracked by InformationService

    def check_win_condition(self) -> bool:
        """Check if the game is over and set winner.

        Returns True if game is over, False otherwise.
        """
        alive_assassins = len([p for p in self.players if p.alive and p.team == "assassins"])
        alive_village = len([p for p in self.players if p.alive and p.team == "village"])

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

    def apply_event_effects(self, effects: list[Effect]) -> None:
        """Apply effects from events to game state.

        Args:
        ----
            effects: List of Effect objects to apply

        """
        for effect in effects:
            if effect.type == "jester_victory":
                # Handle jester victory
                winner = effect.data.get("winner")
                self.game_over = True
                self.winner = "jester"
                print(f"\n🃏 {winner} was the Jester and has WON by being lynched!")
                print("🎭 JESTER VICTORY! The game ends. Everyone else loses.\n")
                self.events.append(f"JESTER VICTORY! {winner} wins!")
            elif effect.type == "heartbreak_death":
                # Handle lover dying of heartbreak
                target = self.get_player_by_name(effect.target)
                if target and target.alive:
                    self.eliminate_player(
                        target,
                        effect.data.get("cause", "Died of heartbreak"),
                        effect.data.get("public_reason"),
                    )
            elif effect.type == "suicide_death":
                # Handle suicidal player death
                target = self.get_player_by_name(effect.target)
                if target and target.alive:
                    print_msg = effect.data.get("print_message")
                    if print_msg:
                        print(print_msg)
                    self.eliminate_player(
                        target,
                        effect.data.get("cause", "Suicide"),
                        effect.data.get("public_reason"),
                    )
            elif effect.type == "bodyguard_sacrifice":
                # Handle bodyguard sacrificing themselves
                target = self.get_player_by_name(effect.target)
                if target and target.alive:
                    # Deactivate bodyguard ability
                    if hasattr(target, "bodyguard_active"):
                        target.bodyguard_active = False
                    # Kill the bodyguard
                    protected = effect.data.get("protected_player")
                    print(f"\n🛡️  {target.name} sacrifices themselves to protect {protected}!")
                    self.eliminate_player(
                        target,
                        effect.data.get("cause", "Died protecting another"),
                        effect.data.get("public_reason"),
                    )
            elif effect.type == "become_ghost":
                # Handle ghost transformation
                target = self.get_player_by_name(effect.target)
                if target:
                    target.is_ghost = True  # Old flag (backward compatibility)
                    target.add_modifier(
                        self,
                        PlayerModifier(type="ghost", source="ghost_event"),
                    )  # NEW: permanent modifier
                    print(f"\n👻 {target.name}'s spirit rises as a ghost...")
                    # Store pending ghost in the event
                    if self.event_registry:
                        from .events import GhostEvent

                        for event in self.event_registry.get_active_events():
                            if isinstance(event, GhostEvent):
                                event.pending_ghost = target
                                break
            # Add more effect types as we migrate events
            # For now, other effects will be handled by effect_service for player states

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
    player_configs: list[dict[str, str]],
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
    chaos_mode: bool = False,
) -> GameState:
    """Create a new game with the specified players.

    Args:
    ----
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
    -------
        GameState instance

    """
    from .events import (
        BodyguardEvent,
        DrunkEvent,
        EventRegistry,
        GhostEvent,
        GunNutEvent,
        InsomniacEvent,
        JesterEvent,
        LoversEvent,
        PriestEvent,
        SleepwalkerEvent,
        SuicidalEvent,
        ZombieEvent,
    )

    # Randomly assign roles
    roles = [Role(config["role"]) for config in player_configs]
    random.shuffle(roles)

    # Randomly assign personalities
    personalities = [config["personality"] for config in player_configs]
    random.shuffle(personalities)

    # Create players with randomized roles and personalities
    players = [
        Player(name=config["name"], role=roles[i], personality=personalities[i])
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
    for event in registry.get_all_events():
        event.active = True

    # Create game state
    game = GameState(players=players, event_registry=registry)

    # Setup active events
    registry.setup_game(game)

    return game
