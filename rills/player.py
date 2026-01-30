"""Player class representing a character in the game."""

import warnings
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from .roles import Role, get_role_info

if TYPE_CHECKING:
    from .game import GameState
    from .models.player_state import PlayerModifier, PlayerState


@dataclass
class Player:
    """Represents a player in the Mafia game."""

    name: str
    role: Role
    personality: str
    alive: bool = True
    protected: bool = False

    # DEPRECATED: Use InformationService and ContextBuilder instead
    # This field is kept for backwards compatibility only
    _memories_deprecated: list[str] = field(default_factory=list, repr=False)

    vigilante_has_killed: bool = False
    suicidal: bool = False
    is_zombie: bool = False
    pending_zombification: bool = False
    is_ghost: bool = False
    haunting_target: str | None = None
    is_sleepwalker: bool = False
    is_insomniac: bool = False
    is_gun_nut: bool = False
    is_drunk: bool = False
    is_jester: bool = False
    is_priest: bool = False
    resurrection_available: bool = False
    is_lover: bool = False
    lover_name: str | None = None
    is_bodyguard: bool = False
    bodyguard_active: bool = False
    insomniac_sighting: str | None = None
    last_protected: str | None = None  # Doctor can't save same person twice in a row
    _last_assassin_statement: str | None = None  # Backwards compatibility
    _postgame_statement: str | None = None  # Backwards compatibility

    def __post_init__(self):
        """Initialize player with role information."""
        role_info = get_role_info(self.role)
        self.team = role_info["team"]
        self.role_description = role_info["description"]
        self.has_night_action = role_info["night_action"]
        if self.role == Role.ZOMBIE:
            self.is_zombie = True

    # ============================================================================
    # PlayerState/Modifier Helper Methods - NEW in Phase 5
    # ============================================================================

    def get_state(self, game: "GameState") -> "PlayerState":
        """Get the PlayerState for this player.

        Args:
            game: The game state containing player states

        Returns:
            The PlayerState for this player
        """
        return game.player_states[self.name]

    def has_modifier(self, game: "GameState", modifier_type: str) -> bool:
        """Check if player has a specific modifier.

        Args:
            game: The game state containing player states
            modifier_type: The type of modifier to check for

        Returns:
            True if the player has this modifier, False otherwise
        """
        return self.get_state(game).has_modifier(modifier_type)

    def add_modifier(self, game: "GameState", modifier: "PlayerModifier") -> None:
        """Add a modifier to this player.

        Args:
            game: The game state containing player states
            modifier: The modifier to add
        """
        self.get_state(game).add_modifier(modifier)

    def remove_modifier(self, game: "GameState", modifier_type: str) -> bool:
        """Remove a modifier from this player.

        Args:
            game: The game state containing player states
            modifier_type: The type of modifier to remove

        Returns:
            True if a modifier was removed, False otherwise
        """
        return self.get_state(game).remove_modifier(modifier_type)

    def get_modifier(self, game: "GameState", modifier_type: str) -> Optional["PlayerModifier"]:
        """Get a specific modifier if it exists.

        Args:
            game: The game state containing player states
            modifier_type: The type of modifier to get

        Returns:
            The modifier if found, None otherwise
        """
        return self.get_state(game).get_modifier(modifier_type)

    # ============================================================================
    # End PlayerState/Modifier Helper Methods
    # ============================================================================

    @property
    def memories(self) -> list[str]:
        """DEPRECATED: Use InformationService.build_context_for() instead.

        This property is maintained for backwards compatibility but will be removed
        in a future version. Use the structured InformationService for accessing
        game state information.
        """
        warnings.warn(
            "Player.memories is deprecated. Use InformationService and ContextBuilder instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._memories_deprecated

    def add_memory(self, memory: str) -> None:
        """DEPRECATED: Use InformationService to track information instead.

        This method is maintained for backwards compatibility but will be removed
        in a future version. Use InformationService methods like reveal_death(),
        reveal_to_player(), etc. to track game information.

        Args:
            memory: Memory string to add (deprecated)
        """
        warnings.warn(
            "Player.add_memory() is deprecated. Use InformationService instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._memories_deprecated.append(memory)

    def get_context(self, phase: str, visible_info: dict) -> str:
        """Generate context string for LLM prompting.

        DEPRECATED: Use ContextBuilder.build_system_context() instead.
        This method is kept for backward compatibility but should not be used.
        """
        import warnings

        warnings.warn(
            "Player.get_context() is deprecated. Use ContextBuilder.build_system_context() instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        context_parts = [
            f"You are {self.name}.",
            f"Your personality: {self.personality}",
            f"Your role: {self.role_description}",
            "",
            "IMPORTANT - Use these exact role names:",
            "- Assassins (not Mafia, killers, etc.)",
            "- Doctor (not Healer, medic, etc.)",
            "- Detective (not Investigator, cop, etc.)",
            "- Vigilante (not Hunter, killer, etc.)",
            "- Villager (not Townsfolk, citizen, etc.)",
        ]

        # Add special status information
        special_status = []
        if self.suicidal:
            special_status.append(
                "You have been struggling with dark thoughts and feel an overwhelming despair."
            )
        if self.is_zombie and self.alive:
            special_status.append(
                "You're not feeling well - you were bitten on the ankle by a rather ugly passerby a few days ago, and the wound has been bothering you. Probably nothing serious."
            )
        elif self.is_zombie and not self.alive:
            special_status.append(
                "You are a ZOMBIE - you have risen from the dead with an insatiable hunger for brains!"
            )
        if self.is_ghost:
            special_status.append(
                f"You are a GHOST haunting {self.haunting_target}. You cannot speak or act, only observe."
            )
        if self.is_sleepwalker:
            special_status.append(
                "You are a sleepwalker - you wander around at night and might be seen by others."
            )
        if self.is_insomniac:
            special_status.append(
                "You have insomnia - you stay awake and sometimes see people moving around at night."
            )
        if self.is_gun_nut:
            special_status.append(
                "You keep a gun under your pillow - if Assassins attack you, you'll fight back!"
            )
        if self.is_drunk:
            special_status.append(
                "You've had too much to drink - you're feeling a bit confused and disoriented."
            )
        if self.vigilante_has_killed:
            special_status.append(
                "You already used your ONE vigilante shot - you cannot kill again."
            )

        if special_status:
            context_parts.append("\nSpecial Status:")
            context_parts.extend([f"- {status}" for status in special_status])

        context_parts.append(f"\nCurrent phase: {phase}")

        # Note: Memory functionality removed - use InformationService and ContextBuilder instead

        if visible_info:
            context_parts.append("\nCurrent situation:")
            for key, value in visible_info.items():
                context_parts.append(f"- {key}: {value}")

        return "\n".join(context_parts)

    def is_assassin(self) -> bool:
        """Check if player is on the assassins team."""
        role_info = get_role_info(self.role)
        return role_info["team"] == "assassins"

    def __str__(self) -> str:
        status = "alive" if self.alive else "dead"
        return f"{self.name} ({self.role.value}, {status})"
