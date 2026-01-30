"""Game roles and their behaviors."""

from enum import Enum
from typing import Protocol


class Role(str, Enum):
    """Available roles in the game."""

    ASSASSINS = "Assassins"
    DOCTOR = "Doctor"
    DETECTIVE = "Detective"
    VIGILANTE = "Vigilante"
    ZOMBIE = "Zombie"
    VILLAGER = "Villager"

    def display_name(self) -> str:
        """Get the singular display name for this role."""
        if self == Role.ASSASSINS:
            return "an Assassin"
        # All other roles start with consonants, so use "a"
        return f"a {self.value}"


class RoleInfo(Protocol):
    """Information about a role."""

    name: str
    team: str
    description: str
    night_action: bool


ROLE_DESCRIPTIONS = {
    Role.ASSASSINS: {
        "name": "Assassins",
        "team": "assassins",
        "description": "You are part of the Assassins. Work with your fellow Assassins to eliminate villagers at night. Win by outnumbering the villagers.",
        "night_action": True,
    },
    Role.DOCTOR: {
        "name": "Doctor",
        "team": "village",
        "description": "You are the Doctor. Each night, you can protect one person from being eliminated by the Assassins.",
        "night_action": True,
    },
    Role.DETECTIVE: {
        "name": "Detective",
        "team": "village",
        "description": "You are the Detective. Each night, you can investigate one person to learn if they are an Assassin or not.",
        "night_action": True,
    },
    Role.VIGILANTE: {
        "name": "Vigilante",
        "team": "village",
        "description": "You are the Vigilante. ONCE per game, you can choose to eliminate one person at night. You only get ONE shot - use it wisely! Be careful - you could accidentally kill a villager.",
        "night_action": True,
    },
    Role.ZOMBIE: {
        "name": "Zombie",
        "team": "village",
        "description": "You are infected with a zombie virus, but you don't know it yet. You believe you're a normal Villager trying to survive and help the village win. You have no special powers. IMPORTANT: You want to SURVIVE like everyone else - you don't know what will happen if you die.",
        "night_action": False,
    },
    Role.VILLAGER: {
        "name": "Villager",
        "team": "village",
        "description": "You are a Villager. You have no special powers, but use your voice during the day to help identify the Assassins.",
        "night_action": False,
    },
}


def get_role_info(role: Role) -> dict:
    """Get information about a role."""
    return ROLE_DESCRIPTIONS[role]
