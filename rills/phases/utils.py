"""Utility functions for game phases."""

import random

from ..player import Player


def get_speaking_order(players: list[Player]) -> list[Player]:
    """
    Determine speaking order with personality-weighted randomization.

    Players with assertive personalities are more likely to speak first,
    while quiet/reserved personalities are more likely to speak later.

    Args:
        players: List of players

    Returns:
        List of players in speaking order
    """
    # Personality keywords that indicate high initiative (speak early)
    assertive_keywords = [
        "aggressive",
        "intimidating",
        "bold",
        "direct",
        "charismatic",
        "persuasive",
        "blunt",
        "honest",
        "impulsive",
        "reckless",
        "cunning",
        "manipulative",
    ]

    # Personality keywords that indicate low initiative (speak late)
    reserved_keywords = [
        "quiet",
        "reserved",
        "timid",
        "hesitant",
        "cautious",
        "analytical",
        "nervous",
        "anxious",
        "shy",
        "passive",
    ]

    # Calculate initiative score for each player
    player_scores = []
    for player in players:
        personality_lower = player.personality.lower()

        # Base score is random
        score = random.random()

        # Bonus for assertive traits (speak earlier)
        for keyword in assertive_keywords:
            if keyword in personality_lower:
                score += 0.3
                break

        # Penalty for reserved traits (speak later)
        for keyword in reserved_keywords:
            if keyword in personality_lower:
                score -= 0.3
                break

        player_scores.append((player, score))

    # Sort by score (highest first)
    player_scores.sort(key=lambda x: x[1], reverse=True)

    return [player for player, score in player_scores]
