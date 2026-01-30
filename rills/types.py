"""Type definitions for game configuration and data structures."""

from typing import Literal, NotRequired, TypedDict


class PlayerConfig(TypedDict):
    """Configuration for a single player."""

    name: str
    role: str
    personality: str


class GameConfig(TypedDict, total=False):
    """Configuration options for game setup."""

    # Event toggles
    enable_zombie: NotRequired[bool]
    enable_ghost: NotRequired[bool]
    enable_drunk: NotRequired[bool]
    enable_sleepwalker: NotRequired[bool]
    enable_insomniac: NotRequired[bool]
    enable_gun_nut: NotRequired[bool]
    enable_jester: NotRequired[bool]
    enable_priest: NotRequired[bool]
    enable_lovers: NotRequired[bool]
    enable_bodyguard: NotRequired[bool]
    enable_suicidal: NotRequired[bool]

    # Game parameters
    num_players: NotRequired[int]
    num_assassins: NotRequired[int]
    num_detectives: NotRequired[int]
    num_doctors: NotRequired[int]
    num_vigilantes: NotRequired[int]

    # LLM settings
    llm_model: NotRequired[str]
    llm_temperature: NotRequired[float]


PhaseType = Literal["night", "day", "game_start", "game_end"]
"""Valid game phases."""

TeamType = Literal["villagers", "assassins"]
"""Valid team names."""

ActionType = Literal[
    "vote",
    "kill",
    "protect",
    "investigate",
    "vigilante_kill",
    "resurrect",
    "bodyguard_protect",
    "haunt",
]
"""Valid action types that players can take."""


class ActionContext(TypedDict, total=False):
    """Context data for player actions."""

    phase: NotRequired[PhaseType]
    day_number: NotRequired[int]
    available_targets: NotRequired[list[str]]
    team_info: NotRequired[str]
    recent_events: NotRequired[str]
    discussion_summary: NotRequired[str]
