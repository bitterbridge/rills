"""Vote service for managing voting and vote tracking."""

from collections.abc import Callable
from typing import Any

from rills.models import Vote, VoteResult
from rills.models.voting import VotingHistory


class VoteService:
    """Manages voting and vote tracking."""

    def __init__(self):
        self.history = VotingHistory()

    def conduct_vote(
        self,
        voters: list[Any],
        candidates: list[Any],
        day: int,
        round_number: int,
        get_vote_func: Callable,
        modifiers: dict[str, list] | None = None,
    ) -> VoteResult:
        """Conduct a voting round.

        Args:
        ----
            voters: List of player objects who can vote
            candidates: List of player objects who can be voted for
            day: Current day number
            round_number: Vote round number (usually 1)
            get_vote_func: Function to get vote from a player
                          Should accept (player, candidates, context) and return (choice, thinking)
            modifiers: Optional dict of player_name -> [PlayerModifier] for vote redirects

        Returns:
        -------
            VoteResult object

        """
        votes = []
        candidate_names = [c.name for c in candidates]
        modifiers = modifiers or {}

        for voter in voters:
            # Get vote choice
            choice, thinking = get_vote_func(voter, candidates)

            original_choice = choice

            # Apply modifiers (e.g., drunk redirects vote)
            if voter.name in modifiers:
                player_modifiers = modifiers[voter.name]
                for modifier in player_modifiers:
                    if modifier.type == "drunk" and modifier.active:
                        # Redirect to random other candidate
                        if choice != "ABSTAIN" and candidate_names:
                            other_candidates = [c for c in candidate_names if c != choice]
                            if other_candidates:
                                choice = random.choice(other_candidates)

            # Create vote
            vote = Vote(
                voter=voter.name,
                target=choice,
                round_number=round_number,
                day_number=day,
                original_target=original_choice if original_choice != choice else None,
                thinking=thinking,
            )
            votes.append(vote)

        # Create result
        result = VoteResult(day_number=day, round_number=round_number, votes=votes)

        # Add to history
        self.history.add_result(result)

        return result

    def get_vote_breakdown(self, result: VoteResult) -> str:
        """Get formatted vote breakdown."""
        return result.format_breakdown()

    def get_voting_pattern(self, voter: str) -> list[str]:
        """Get history of who a player voted for."""
        return self.history.get_voting_pattern(voter)

    def get_targeting_pattern(self, target: str) -> list[str]:
        """Get history of who voted for a specific player."""
        return self.history.get_targeting_pattern(target)

    def analyze_voting_alignment(self, player1: str, player2: str) -> float:
        """Analyze voting alignment between two players.

        Returns a score from 0.0 (never aligned) to 1.0 (always aligned).
        """
        pattern1 = self.history.get_voting_pattern(player1)
        pattern2 = self.history.get_voting_pattern(player2)

        if not pattern1 or not pattern2:
            return 0.0

        # Count how many times they voted for the same person
        aligned = sum(1 for v1, v2 in zip(pattern1, pattern2, strict=False) if v1 == v2)
        total = min(len(pattern1), len(pattern2))

        return aligned / total if total > 0 else 0.0

    def get_vote_leaders(self, result: VoteResult, min_votes: int = 1) -> list[tuple[str, int]]:
        """Get players with at least min_votes, sorted by vote count."""
        leaders = [
            (name, count) for name, count in result.vote_counts.items() if count >= min_votes
        ]
        return sorted(leaders, key=lambda x: x[1], reverse=True)

    def clear(self):
        """Clear voting history (for testing)."""
        self.history.clear()


# Need to import random for drunk modifier
import random
