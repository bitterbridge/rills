"""Prompt templates for LLM context building."""

from typing import Final

# Action-specific prompts
NIGHT_KILL_PROMPT: Final[
    str
] = """
You are {player_name}, an Assassin. Choose who to eliminate tonight.

{team_info}

{recent_events}

Available targets: {targets}
"""

DOCTOR_PROTECT_PROMPT: Final[
    str
] = """
You are {player_name}, the Doctor. Choose who to protect tonight.
Note: You cannot protect the same person two nights in a row.

{recent_events}

Available targets: {targets}
"""

DETECTIVE_INVESTIGATE_PROMPT: Final[
    str
] = """
You are {player_name}, the Detective. Choose who to investigate tonight.

{recent_events}

Available targets: {targets}
"""

VIGILANTE_KILL_PROMPT: Final[
    str
] = """
You are {player_name}, the Vigilante. You have ONE shot to eliminate someone you suspect is an Assassin.
WARNING: If you kill a villager, you will die from guilt!

{recent_events}

Available choices: {choices}
"""

PRIEST_RESURRECT_PROMPT: Final[
    str
] = """
You are {player_name}, a Priest with the power to resurrect ONE dead player.
This is your only resurrection - use it wisely!

{recent_events}

Dead players: {dead_players}

Available choices: {choices}
"""

BODYGUARD_PROTECT_PROMPT: Final[
    str
] = """
You are {player_name}, a Bodyguard. Choose someone to protect tonight.
If they are attacked by Assassins, you will die in their place.

{recent_events}

Available targets: {targets}
"""

GHOST_HAUNT_PROMPT: Final[
    str
] = """
You are {player_name}, and you have died! You may have a chance to become a ghost.

{death_info}

Choose who to haunt (they will know something supernatural is happening):

Available targets: {targets}
"""

# Discussion prompts
DISCUSSION_PROMPT: Final[
    str
] = """
It's time for discussion. Share your thoughts, suspicions, or information.

{context}

What do you say?
"""

DISCUSSION_WITH_STATEMENTS: Final[
    str
] = """
Discussion round {round_num}. Other players have been speaking:

{recent_statements}

{context}

What do you say?
"""

# Voting prompts
LYNCH_VOTE_PROMPT: Final[
    str
] = """
It's time to vote for who to eliminate today.

⚠️  CRITICAL VOTING GUIDANCE:
- DO NOT vote for someone just because they're "quiet" or "haven't spoken yet"
- Look for CONCRETE EVIDENCE: contradictions, suspicious voting patterns, defensive behavior
- Consider: Who has claimed roles? Do their claims match observed events?
- Think strategically: Who benefits from recent deaths and votes?
- Remember: Eliminating innocent villagers helps the Assassins win!

WHAT MAKES SOMEONE SUSPICIOUS:
✓ Contradicting known facts or previous statements
✓ Coordinated voting patterns with others
✓ Overly defensive or deflecting when questioned
✓ Role claims that don't match observed events

WHAT DOES NOT MAKE SOMEONE SUSPICIOUS:
✗ Being quiet (they may not have had a turn to speak yet!)
✗ Asking questions or being confused
✗ Not having a power role to claim

{discussion_summary}

{context}

Who do you vote to eliminate? Base your decision on EVIDENCE, not assumptions.
"""

# System context templates
ROLE_CONTEXT: Final[
    str
] = """You are {player_name}.
Your personality: {personality}
Your role: {role_description}

IMPORTANT - Use these exact role names:
- Assassins (not Mafia, killers, etc.)
- Doctor (not Healer, medic, etc.)
- Detective (not Investigator, cop, etc.)
- Vigilante (not Hunter, killer, etc.)
- Villager (not Townsfolk, citizen, etc.)
"""

SPECIAL_STATUS_TEMPLATES: Final[dict[str, str]] = {
    "suicidal": "You have been struggling with dark thoughts and feel an overwhelming despair.",
    "zombie_alive": "You're not feeling well - you were bitten on the ankle by a rather ugly passerby a few days ago, and the wound has been bothering you. Probably nothing serious.",
    "zombie_undead": "You are a ZOMBIE - you have risen from the dead with an insatiable hunger for brains!",
    "ghost": "You are a GHOST haunting {target}. You cannot speak or act, only observe.",
    "sleepwalker": "You are a sleepwalker - you wander around at night and might be seen by others.",
    "insomniac": "You have insomnia - you stay awake and sometimes see people moving around at night.",
    "gun_nut": "You keep a gun under your pillow - if Assassins attack you, you'll fight back!",
    "drunk": "You've had too much to drink - you're feeling a bit confused and disoriented.",
    "vigilante_used": "You already used your ONE vigilante shot - you cannot kill again.",
    "jester": "You are secretly a Jester - your goal is to GET YOURSELF LYNCHED to win!",
    "priest": "You have the power to resurrect ONE dead player - this is your only resurrection!",
    "lover": "You are in love with {partner} - if they die, you will die of heartbreak.",
    "bodyguard": "You are a Bodyguard - you can die protecting others from Assassin attacks.",
}

PHASE_DESCRIPTIONS: Final[dict[str, str]] = {
    "night": "Night Phase - Special roles are taking their actions",
    "day": "Day Phase - Discussion and voting",
    "game_start": "Game Start",
    "game_end": "Game Over",
}
