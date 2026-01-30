"""Voting models and vote result tracking."""

from dataclasses import dataclass, field
from typing import Optional
from collections import Counter


@dataclass
class Vote:
    """A single vote cast by a player."""

    voter: str
    target: str  # Player name or "ABSTAIN"
    round_number: int  # Usually 1, could support multiple vote rounds
    day_number: int
    original_target: Optional[str] = None  # For drunk modifier tracking
    thinking: str = ""  # Voter's reasoning

    def is_abstain(self) -> bool:
        """Check if this is an abstain vote."""
        return self.target == "ABSTAIN"

    def was_redirected(self) -> bool:
        """Check if this vote was redirected (e.g., by drunk modifier)."""
        return self.original_target is not None and self.original_target != self.target

    def __repr__(self) -> str:
        if self.was_redirected():
            return f"Vote({self.voter} → {self.target} [redirected from {self.original_target}])"
        return f"Vote({self.voter} → {self.target})"


@dataclass
class VoteResult:
    """Result of a voting round."""

    day_number: int
    round_number: int
    votes: list[Vote] = field(default_factory=list)
    eliminated: Optional[str] = None
    tied: bool = False
    tied_players: list[str] = field(default_factory=list)
    vote_counts: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate vote counts and determine result."""
        if not self.vote_counts:  # Only calculate if not already provided
            self._calculate_result()

    def _calculate_result(self):
        """Calculate vote counts and determine elimination."""
        # Count votes (excluding abstentions)
        valid_votes = [v for v in self.votes if not v.is_abstain()]
        self.vote_counts = Counter(v.target for v in valid_votes)

        if not self.vote_counts:
            # Everyone abstained
            self.eliminated = None
            self.tied = False
            return

        # Find maximum vote count
        max_votes = max(self.vote_counts.values())
        players_with_max = [p for p, c in self.vote_counts.items() if c == max_votes]

        if len(players_with_max) > 1:
            # Tie
            self.tied = True
            self.tied_players = players_with_max
            self.eliminated = None
        else:
            # Clear winner
            self.tied = False
            self.eliminated = players_with_max[0]

    def get_votes_by(self, player: str) -> list[Vote]:
        """Get all votes cast by a specific player."""
        return [v for v in self.votes if v.voter == player]

    def get_votes_for(self, player: str) -> list[Vote]:
        """Get all votes targeting a specific player."""
        return [v for v in self.votes if v.target == player]

    def get_voters_for(self, player: str) -> list[str]:
        """Get names of players who voted for a specific player."""
        return [v.voter for v in self.votes if v.target == player]

    def get_abstainers(self) -> list[str]:
        """Get names of players who abstained."""
        return [v.voter for v in self.votes if v.is_abstain()]

    def get_redirected_votes(self) -> list[Vote]:
        """Get all votes that were redirected (e.g., by drunk modifier)."""
        return [v for v in self.votes if v.was_redirected()]

    def format_breakdown(self) -> str:
        """Format a human-readable breakdown of the vote."""
        lines = []

        # Vote counts
        lines.append("Vote breakdown:")
        for target, count in sorted(self.vote_counts.items(), key=lambda x: x[1], reverse=True):
            voters = self.get_voters_for(target)
            voters_str = ", ".join(voters)
            lines.append(f"  {target}: {count} vote(s) ({voters_str})")

        # Abstentions
        abstainers = self.get_abstainers()
        if abstainers:
            lines.append(f"  Abstained: {', '.join(abstainers)}")

        # Result
        if self.tied:
            lines.append(f"\nResult: TIE between {', '.join(self.tied_players)}")
            lines.append("No one is eliminated.")
        elif self.eliminated:
            lines.append(f"\nResult: {self.eliminated} is eliminated with {self.vote_counts[self.eliminated]} vote(s)")
        else:
            lines.append("\nResult: No one is eliminated (no votes cast)")

        return "\n".join(lines)

    def __repr__(self) -> str:
        if self.tied:
            return f"VoteResult(Day {self.day_number}, TIE: {self.tied_players})"
        elif self.eliminated:
            return f"VoteResult(Day {self.day_number}, Eliminated: {self.eliminated})"
        return f"VoteResult(Day {self.day_number}, No elimination)"


class VotingHistory:
    """Track voting history across all days."""

    def __init__(self):
        self.results: list[VoteResult] = []
        self._by_day: dict[int, list[VoteResult]] = {}

    def add_result(self, result: VoteResult):
        """Add a vote result to the history."""
        self.results.append(result)

        if result.day_number not in self._by_day:
            self._by_day[result.day_number] = []
        self._by_day[result.day_number].append(result)

    def get_by_day(self, day_number: int) -> list[VoteResult]:
        """Get all vote results from a specific day."""
        return self._by_day.get(day_number, [])

    def get_voting_pattern(self, voter: str) -> list[str]:
        """Get history of who a player voted for across all days."""
        pattern = []
        for result in self.results:
            votes = result.get_votes_by(voter)
            if votes:
                pattern.append(votes[0].target)  # Should only be one vote per player per round
        return pattern

    def get_targeting_pattern(self, target: str) -> list[str]:
        """Get history of who voted for a specific player across all days."""
        pattern = []
        for result in self.results:
            voters = result.get_voters_for(target)
            pattern.extend(voters)
        return pattern

    def count_votes_by(self, voter: str) -> int:
        """Count total number of non-abstain votes by a player."""
        count = 0
        for result in self.results:
            votes = result.get_votes_by(voter)
            count += sum(1 for v in votes if not v.is_abstain())
        return count

    def count_votes_for(self, target: str) -> int:
        """Count total number of votes targeting a player across all days."""
        count = 0
        for result in self.results:
            count += len(result.get_votes_for(target))
        return count

    def clear(self):
        """Clear all voting history (for testing)."""
        self.results.clear()
        self._by_day.clear()
