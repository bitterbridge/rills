"""Player class representing a character in the game."""

from dataclasses import dataclass, field
from typing import Optional
from .roles import Role, get_role_info


@dataclass
class Player:
    """Represents a player in the Mafia game."""

    name: str
    role: Role
    personality: str
    alive: bool = True
    protected: bool = False
    memories: list[str] = field(default_factory=list)
    vigilante_has_killed: bool = False
    suicidal: bool = False
    is_zombie: bool = False
    pending_zombification: bool = False
    is_ghost: bool = False
    haunting_target: Optional[str] = None
    is_sleepwalker: bool = False
    is_insomniac: bool = False
    is_gun_nut: bool = False
    is_drunk: bool = False
    is_jester: bool = False
    is_priest: bool = False
    resurrection_available: bool = False
    is_lover: bool = False
    lover_name: Optional[str] = None
    is_bodyguard: bool = False
    bodyguard_active: bool = False
    insomniac_sighting: Optional[str] = None
    last_protected: Optional[str] = None  # Doctor can't save same person twice in a row

    def __post_init__(self):
        """Initialize player with role information."""
        role_info = get_role_info(self.role)
        self.team = role_info["team"]
        self.role_description = role_info["description"]
        self.has_night_action = role_info["night_action"]
        if self.role == Role.ZOMBIE:
            self.is_zombie = True

    def add_memory(self, memory: str) -> None:
        """Add a memory/observation to the player's history."""
        self.memories.append(memory)

    def get_context(self, phase: str, visible_info: dict) -> str:
        """Generate context string for LLM prompting."""
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
            special_status.append("You have been struggling with dark thoughts and feel an overwhelming despair.")
        if self.is_zombie and self.alive:
            special_status.append("You're not feeling well - you were bitten on the ankle by a rather ugly passerby a few days ago, and the wound has been bothering you. Probably nothing serious.")
        elif self.is_zombie and not self.alive:
            special_status.append("You are a ZOMBIE - you have risen from the dead with an insatiable hunger for brains!")
        if self.is_ghost:
            special_status.append(f"You are a GHOST haunting {self.haunting_target}. You cannot speak or act, only observe.")
        if self.is_sleepwalker:
            special_status.append("You are a sleepwalker - you wander around at night and might be seen by others.")
        if self.is_insomniac:
            special_status.append("You have insomnia - you stay awake and sometimes see people moving around at night.")
        if self.is_gun_nut:
            special_status.append("You keep a gun under your pillow - if Assassins attack you, you'll fight back!")
        if self.is_drunk:
            special_status.append("You've had too much to drink - you're feeling a bit confused and disoriented.")
        if self.vigilante_has_killed:
            special_status.append("You already used your ONE vigilante shot - you cannot kill again.")

        if special_status:
            context_parts.append("\nSpecial Status:")
            context_parts.extend([f"- {status}" for status in special_status])

        context_parts.append(f"\nCurrent phase: {phase}")

        if self.memories:
            context_parts.append("\nWhat you remember:")
            context_parts.extend([f"- {memory}" for memory in self.memories[-10:]])  # Last 10 memories

        if visible_info:
            context_parts.append("\nCurrent situation:")
            for key, value in visible_info.items():
                context_parts.append(f"- {key}: {value}")

        return "\n".join(context_parts)

    def is_assassin(self) -> bool:
        """Check if player is on the assassins team."""
        return self.team == "assassins"

    def __str__(self) -> str:
        status = "alive" if self.alive else "dead"
        return f"{self.name} ({self.role.value}, {status})"
