"""PlayerState service for managing player modifiers and state.

This service provides a centralized way to manage player state through modifiers,
replacing the previous boolean flag approach with a more flexible and extensible system.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PlayerModifier:
    """Represents a modifier applied to a player.

    Modifiers represent temporary or permanent state changes, such as:
    - drunk: Player's vote is redirected
    - zombie: Player continues playing after death
    - ghost: Player can haunt others
    - lover: Player is linked to another player
    - protected: Player is protected from night kills

    Attributes
    ----------
        type: The type of modifier (e.g., "drunk", "zombie", "protected")
        data: Additional data specific to this modifier type
        expires_on_day: Day number when this modifier expires (None = permanent)

    """

    type: str
    data: dict[str, Any] = field(default_factory=dict)
    expires_on_day: int | None = None

    def is_expired(self, current_day: int) -> bool:
        """Check if this modifier has expired."""
        if self.expires_on_day is None:
            return False
        return current_day > self.expires_on_day


@dataclass
class PlayerState:
    """Centralized state for a single player.

    This replaces the scattered boolean flags on the Player class with a
    unified state management system using modifiers.

    Attributes
    ----------
        name: Player name
        role: Player's role type
        team: Player's team alignment
        alive: Whether the player is alive
        modifiers: List of active modifiers on this player

    """

    name: str
    role: str
    team: str
    alive: bool = True
    modifiers: list[PlayerModifier] = field(default_factory=list)

    def add_modifier(self, modifier: PlayerModifier) -> None:
        """Add a modifier to this player.

        Args:
        ----
            modifier: The modifier to add

        """
        # Don't add duplicates of the same type (remove old one first)
        self.modifiers = [m for m in self.modifiers if m.type != modifier.type]
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier_type: str) -> bool:
        """Remove a modifier from this player.

        Args:
        ----
            modifier_type: The type of modifier to remove

        Returns:
        -------
            True if a modifier was removed, False otherwise

        """
        original_length = len(self.modifiers)
        self.modifiers = [m for m in self.modifiers if m.type != modifier_type]
        return len(self.modifiers) < original_length

    def has_modifier(self, modifier_type: str) -> bool:
        """Check if player has a specific modifier type.

        Args:
        ----
            modifier_type: The type of modifier to check for

        Returns:
        -------
            True if the player has this modifier, False otherwise

        """
        return any(m.type == modifier_type for m in self.modifiers)

    def get_modifier(self, modifier_type: str) -> PlayerModifier | None:
        """Get a specific modifier if it exists.

        Args:
        ----
            modifier_type: The type of modifier to get

        Returns:
        -------
            The modifier if found, None otherwise

        """
        for modifier in self.modifiers:
            if modifier.type == modifier_type:
                return modifier
        return None

    def cleanup_expired_modifiers(self, current_day: int) -> list[str]:
        """Remove expired modifiers.

        Args:
        ----
            current_day: Current day number

        Returns:
        -------
            List of modifier types that were removed

        """
        expired = [m.type for m in self.modifiers if m.is_expired(current_day)]
        self.modifiers = [m for m in self.modifiers if not m.is_expired(current_day)]
        return expired

    def get_all_modifiers(self) -> list[PlayerModifier]:
        """Get all active modifiers.

        Returns
        -------
            List of all modifiers on this player

        """
        return self.modifiers.copy()
