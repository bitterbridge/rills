"""Player state and modifier models."""

from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class PlayerModifier:
    """A modifier affecting a player's state or abilities."""

    type: str  # "zombie", "drunk", "lover", "protected", etc.
    source: str  # What created this modifier (e.g., "event:zombie", "event:cupid")
    active: bool = True
    data: dict[str, Any] = field(default_factory=dict)  # Modifier-specific data
    expires_on: Optional[int] = None  # Day number when this expires, None = permanent
    applied_on: int = 0  # Day number when this was applied

    def is_expired(self, current_day: int) -> bool:
        """Check if this modifier has expired."""
        if self.expires_on is None:
            return False
        return current_day > self.expires_on

    def deactivate(self):
        """Deactivate this modifier."""
        self.active = False

    def __repr__(self) -> str:
        status = "active" if self.active else "inactive"
        expiry = f"expires day {self.expires_on}" if self.expires_on else "permanent"
        return f"PlayerModifier({self.type}, {status}, {expiry})"


@dataclass
class PlayerState:
    """Complete state of a player at a point in time."""

    name: str
    role: str  # Role as string for now, can be Role enum later
    team: str
    alive: bool = True
    modifiers: list[PlayerModifier] = field(default_factory=list)

    def has_modifier(self, modifier_type: str) -> bool:
        """Check if player has an active modifier of a specific type."""
        return any(m.type == modifier_type and m.active for m in self.modifiers)

    def get_modifier(self, modifier_type: str) -> Optional[PlayerModifier]:
        """Get an active modifier of a specific type."""
        return next((m for m in self.modifiers if m.type == modifier_type and m.active), None)

    def get_all_modifiers(self, modifier_type: str) -> list[PlayerModifier]:
        """Get all active modifiers of a specific type."""
        return [m for m in self.modifiers if m.type == modifier_type and m.active]

    def add_modifier(self, modifier: PlayerModifier):
        """Add a modifier to this player."""
        self.modifiers.append(modifier)

    def remove_modifier(self, modifier_type: str) -> bool:
        """Remove (deactivate) all modifiers of a specific type. Returns True if any were removed."""
        found = False
        for modifier in self.modifiers:
            if modifier.type == modifier_type and modifier.active:
                modifier.deactivate()
                found = True
        return found

    def update_modifiers(self, current_day: int):
        """Update modifiers, deactivating any that have expired."""
        for modifier in self.modifiers:
            if modifier.active and modifier.is_expired(current_day):
                modifier.deactivate()

    def get_active_modifiers(self) -> list[PlayerModifier]:
        """Get all currently active modifiers."""
        return [m for m in self.modifiers if m.active]

    def get_display_role(self) -> str:
        """Get the role as it should be displayed (accounting for modifiers like zombie infection)."""
        # Check for zombie infection
        if self.has_modifier("infected") and self.alive:
            return "Villager (Infected)"
        elif self.has_modifier("zombie") or (self.has_modifier("infected") and not self.alive):
            return "Zombie"

        return self.role

    def __repr__(self) -> str:
        status = "alive" if self.alive else "dead"
        mod_count = len(self.get_active_modifiers())
        return f"PlayerState({self.name}, {self.role}, {status}, {mod_count} modifiers)"
