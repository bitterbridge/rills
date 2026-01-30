"""Drunk event - a player's vote gets redirected randomly."""

from typing import TYPE_CHECKING, Optional
import random
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class DrunkEvent(EventModifier):
    """Drunk villager event.

    One random villager is drunk. During voting, their vote
    goes to a random player instead of their intended target.
    """

    def __init__(self):
        super().__init__()
        self._vote_redirect: dict[str, str] = {}  # {voter_name: actual_target}

    @property
    def name(self) -> str:
        return "Drunk Mode"

    @property
    def description(self) -> str:
        return "Someone's had too much to drink..."

    def setup_game(self, game: "GameState") -> None:
        """Assign drunk flag to a random villager."""
        available = [
            p for p in game.players
            if p.team == "village"
            and not p.suicidal
            and not p.is_sleepwalker
            and not p.is_insomniac
            and not p.is_gun_nut
            and not p.is_jester
            and not p.is_priest
            and not p.is_bodyguard
        ]

        if available:
            drunk = random.choice(available)
            drunk.is_drunk = True

    def on_player_eliminated(
        self, game: "GameState", player: "Player", reason: str
    ) -> None:
        """No special behavior on elimination."""
        pass

    def redirect_vote(
        self, voter: "Player", intended_target: str, all_players: list["Player"]
    ) -> str:
        """Redirect a drunk player's vote to a random target.

        Args:
            voter: The player voting
            intended_target: Who they tried to vote for
            all_players: All alive players to choose from

        Returns:
            The actual target (random if drunk, original otherwise)
        """
        if not hasattr(voter, 'is_drunk') or not voter.is_drunk:
            return intended_target

        # Choose a random alive player (could be the same as intended)
        alive = [p for p in all_players if p.alive]
        if not alive:
            return intended_target

        actual_target = random.choice(alive).name
        self._vote_redirect[voter.name] = actual_target

        return actual_target

    def get_redirect_message(self, voter_name: str) -> Optional[str]:
        """Get message if a vote was redirected.

        Args:
            voter_name: Name of the voter

        Returns:
            Message if vote was redirected, None otherwise
        """
        if voter_name in self._vote_redirect:
            return f"🍺 {voter_name}'s vote went astray..."

        return None

    def clear_redirects(self) -> None:
        """Clear redirect tracking (call after each vote)."""
        self._vote_redirect.clear()
