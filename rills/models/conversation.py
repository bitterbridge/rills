"""Conversation and statement models."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4

from .information import Visibility


@dataclass
class Statement:
    """A statement made by a player during a conversation."""

    id: str
    speaker: str
    content: str
    thinking: str  # Internal reasoning/thoughts (not visible to others)
    timestamp: datetime
    round_number: int
    phase: str  # "day_discussion", "assassin_discussion", "postgame", "feedback", etc.
    visibility: Visibility
    in_response_to: Optional[str] = None  # Statement ID this is responding to
    metadata: dict = field(default_factory=dict)  # Additional context

    @classmethod
    def create(cls, speaker: str, content: str, thinking: str,
               round_number: int, phase: str, visibility: Visibility,
               in_response_to: Optional[str] = None, **metadata) -> "Statement":
        """Factory method to create Statement with auto-generated ID."""
        return cls(
            id=str(uuid4()),
            speaker=speaker,
            content=content,
            thinking=thinking,
            timestamp=datetime.now(),
            round_number=round_number,
            phase=phase,
            visibility=visibility,
            in_response_to=in_response_to,
            metadata=metadata
        )

    def __repr__(self) -> str:
        preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"Statement({self.speaker}: {preview})"


@dataclass
class ConversationRound:
    """A round of conversation in a specific phase."""

    round_number: int
    phase: str  # "day_discussion", "assassin_discussion", etc.
    statements: list[Statement] = field(default_factory=list)
    speaking_order: list[str] = field(default_factory=list)  # Player names in order
    day_number: int = 0

    def add_statement(self, statement: Statement):
        """Add a statement to this round."""
        self.statements.append(statement)

    def get_context_for(self, player_name: str, include_thinking: bool = False) -> str:
        """Get conversation context for a player (what others have said before them)."""
        prior_statements = [s for s in self.statements if s.speaker != player_name]

        if not prior_statements:
            return ""

        lines = []
        for stmt in prior_statements:
            lines.append(f"{stmt.speaker} said: {stmt.content}")
            if include_thinking:
                lines.append(f"  (thinking: {stmt.thinking})")

        return "\n".join(lines)

    def get_statements_by(self, player_name: str) -> list[Statement]:
        """Get all statements by a specific player in this round."""
        return [s for s in self.statements if s.speaker == player_name]

    def __repr__(self) -> str:
        return f"ConversationRound({self.phase}, round {self.round_number}, {len(self.statements)} statements)"


class ConversationHistory:
    """Complete conversation history across all phases and rounds."""

    def __init__(self):
        self.rounds: list[ConversationRound] = []
        self._by_phase: dict[str, list[ConversationRound]] = {}
        self._by_day: dict[int, list[ConversationRound]] = {}

    def add_round(self, round_obj: ConversationRound):
        """Add a conversation round to the history."""
        self.rounds.append(round_obj)

        # Index by phase
        if round_obj.phase not in self._by_phase:
            self._by_phase[round_obj.phase] = []
        self._by_phase[round_obj.phase].append(round_obj)

        # Index by day
        if round_obj.day_number not in self._by_day:
            self._by_day[round_obj.day_number] = []
        self._by_day[round_obj.day_number].append(round_obj)

    def get_statements_by(self, player: str) -> list[Statement]:
        """Get all statements by a specific player across all rounds."""
        statements = []
        for round_obj in self.rounds:
            statements.extend(round_obj.get_statements_by(player))
        return sorted(statements, key=lambda s: s.timestamp)

    def get_statements_in_phase(self, phase: str) -> list[Statement]:
        """Get all statements in a specific phase."""
        rounds = self._by_phase.get(phase, [])
        statements = []
        for round_obj in rounds:
            statements.extend(round_obj.statements)
        return sorted(statements, key=lambda s: s.timestamp)

    def get_rounds_by_phase(self, phase: str) -> list[ConversationRound]:
        """Get all conversation rounds for a specific phase."""
        return self._by_phase.get(phase, [])

    def get_rounds_by_day(self, day_number: int) -> list[ConversationRound]:
        """Get all conversation rounds for a specific day."""
        return self._by_day.get(day_number, [])

    def search_content(self, keyword: str, case_sensitive: bool = False) -> list[Statement]:
        """Search for statements containing a keyword."""
        results = []
        search_term = keyword if case_sensitive else keyword.lower()

        for round_obj in self.rounds:
            for statement in round_obj.statements:
                content = statement.content if case_sensitive else statement.content.lower()
                if search_term in content:
                    results.append(statement)

        return sorted(results, key=lambda s: s.timestamp)

    def get_conversation_between(self, player1: str, player2: str) -> list[Statement]:
        """Get all statements exchanged between two players."""
        statements = []
        for round_obj in self.rounds:
            for stmt in round_obj.statements:
                if stmt.speaker in [player1, player2]:
                    statements.append(stmt)
        return sorted(statements, key=lambda s: s.timestamp)

    def count_statements(self) -> int:
        """Get total count of statements."""
        return sum(len(r.statements) for r in self.rounds)

    def clear(self):
        """Clear all conversation history (for testing)."""
        self.rounds.clear()
        self._by_phase.clear()
        self._by_day.clear()
