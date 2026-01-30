"""Conversation service for managing discussion rounds and speaking order."""

import random
from collections.abc import Callable
from typing import Any

from rills.models import ConversationHistory, ConversationRound, Statement, Visibility


class ConversationService:
    """Manages conversation rounds and speaking order."""

    def __init__(self):
        self.history = ConversationHistory()

    def get_speaking_order(self, players: list[Any]) -> list[Any]:
        """Get personality-weighted speaking order.

        Players with assertive personalities speak earlier,
        reserved personalities speak later, with randomization.
        """
        assertive_keywords = {
            "aggressive",
            "bold",
            "charismatic",
            "cunning",
            "manipulative",
            "assertive",
            "confident",
            "dominant",
            "outspoken",
            "brash",
            "fearless",
            "daring",
            "provocative",
            "confrontational",
        }

        reserved_keywords = {
            "quiet",
            "timid",
            "cautious",
            "nervous",
            "anxious",
            "reserved",
            "shy",
            "hesitant",
            "withdrawn",
            "meek",
            "passive",
            "introverted",
            "subtle",
            "humble",
        }

        def calculate_initiative(player) -> float:
            """Calculate initiative score for speaking order."""
            personality = getattr(player, "personality", "").lower()

            # Start with random base
            score = random.random()

            # Adjust based on personality keywords
            for keyword in assertive_keywords:
                if keyword in personality:
                    score += 0.3
                    break

            for keyword in reserved_keywords:
                if keyword in personality:
                    score -= 0.3
                    break

            return score

        # Sort by initiative score (high to low)
        sorted_players = sorted(players, key=calculate_initiative, reverse=True)
        return sorted_players

    def conduct_round(
        self,
        participants: list[Any],
        phase: str,
        round_number: int,
        day_number: int,
        get_statement_func: Callable,
        visibility: Visibility | None = None,
    ) -> ConversationRound:
        """Conduct a round of conversation.

        Args:
        ----
            participants: List of player objects
            phase: Phase name (e.g., "day_discussion", "assassin_discussion")
            round_number: Round number within this phase
            day_number: Current day number
            get_statement_func: Function to get statement from a player
                                Should accept (player, context) and return (thinking, content)
            visibility: Visibility for statements (defaults to public)

        Returns:
        -------
            ConversationRound object with all statements

        """
        if visibility is None:
            visibility = Visibility("public", [])

        speaking_order = self.get_speaking_order(participants)
        round_obj = ConversationRound(
            round_number=round_number,
            phase=phase,
            day_number=day_number,
            speaking_order=[p.name for p in speaking_order],
        )

        for player in speaking_order:
            # Build context from prior statements in this round
            context = round_obj.get_context_for(player.name)

            # Get statement from player
            thinking, content = get_statement_func(player, context, round_number)

            # Create statement
            stmt = Statement.create(
                speaker=player.name,
                content=content,
                thinking=thinking,
                round_number=round_number,
                phase=phase,
                visibility=visibility,
            )

            round_obj.add_statement(stmt)

        # Add to history
        self.history.add_round(round_obj)

        return round_obj

    def get_recent_statements(self, player_name: str, count: int = 5) -> list[Statement]:
        """Get the most recent statements by a player."""
        statements = self.history.get_statements_by(player_name)
        return statements[-count:] if statements else []

    def get_visible_statements_in_phase(
        self,
        player_name: str,
        phase: str,
        player_team: str | None = None,
        day_number: int | None = None,
        exclude_self: bool = True,
    ) -> list[Statement]:
        """Get statements visible to a player in a specific phase.

        Args:
        ----
            player_name: Name of the player viewing the statements
            phase: Phase to get statements from (e.g., "day_discussion")
            player_team: Player's team (needed for team visibility)
            day_number: Optional day number filter
            exclude_self: Whether to exclude the player's own statements

        Returns:
        -------
            List of statements the player can see

        """
        statements = self.get_statements_in_phase(phase, day_number)

        visible_statements = []
        for stmt in statements:
            # Skip own statements if requested
            if exclude_self and stmt.speaker == player_name:
                continue

            # Check visibility
            if stmt.visibility.is_visible_to(player_name, player_team=player_team):
                visible_statements.append(stmt)

        return visible_statements

    def get_statements_in_phase(self, phase: str, day_number: int | None = None) -> list[Statement]:
        """Get all statements from a specific phase."""
        statements = self.history.get_statements_in_phase(phase)
        if day_number is not None:
            statements = [s for s in statements if s.metadata.get("day_number") == day_number]
        return statements

    def search_mentions(self, keyword: str) -> list[Statement]:
        """Search for statements mentioning a keyword."""
        return self.history.search_content(keyword)

    def format_round_for_display(
        self,
        round_obj: ConversationRound,
        show_thinking: bool = False,
    ) -> str:
        """Format a conversation round for display."""
        lines = []
        lines.append(f"\n=== {round_obj.phase.upper()} - Round {round_obj.round_number} ===\n")

        for stmt in round_obj.statements:
            lines.append(f"{stmt.speaker}: {stmt.content}")
            if show_thinking:
                lines.append(f"  [Thinking: {stmt.thinking}]")
            lines.append("")

        return "\n".join(lines)

    def clear(self):
        """Clear conversation history (for testing)."""
        self.history.clear()
