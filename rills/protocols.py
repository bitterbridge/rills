"""Protocol definitions for type checking."""

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from .player import Player


class LLMAgentProtocol(Protocol):
    """Protocol for LLM agent implementations."""

    def get_player_choice(
        self,
        player: "Player",
        prompt: str,
        valid_choices: list[str],
        context: str = "",
    ) -> str:
        """Get a single choice from the player.

        Args:
        ----
            player: The player making the decision
            prompt: The specific question/prompt
            valid_choices: List of valid choice strings
            context: Additional context about the game state

        Returns:
        -------
            The player's choice (one of valid_choices)

        """
        ...

    def get_player_choice_with_reasoning(
        self,
        player: "Player",
        prompt: str,
        valid_choices: list[str],
        context: str = "",
    ) -> tuple[str, str]:
        """Get a decision with reasoning from the player.

        Args:
        ----
            player: The player making the decision
            prompt: The specific question/prompt
            valid_choices: List of valid choice strings
            context: Additional context about the game state

        Returns:
        -------
            Tuple of (choice, reasoning)

        """
        ...

    def get_player_statement(
        self,
        player: "Player",
        prompt: str,
        context: str = "",
    ) -> tuple[str, str]:
        """Get a free-form statement from the player.

        Args:
        ----
            player: The player making the statement
            prompt: The specific question/prompt
            context: Additional context about the game state

        Returns:
        -------
            Tuple of (thinking, statement) where thinking is internal reasoning
            and statement is the public message

        """
        ...
