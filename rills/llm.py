"""LLM integration for character decision-making."""

import os
from typing import Optional, Literal
from anthropic import Anthropic
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from .player import Player


class PlayerChoice(BaseModel):
    """Schema for player choice with reasoning."""
    reasoning: str = Field(description="1-2 sentence explanation of the reasoning")
    choice: str = Field(description="The exact choice from the available options")


class PlayerStatement(BaseModel):
    """Schema for player free-form statement with internal thinking."""
    thinking: str = Field(description="Internal deliberation/reasoning (1-2 sentences) - visible only in transcript")
    statement: str = Field(description="The public statement to other players")


class LLMAgent:
    """Handles LLM API calls for character decisions."""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-5-20250929"):
        """Initialize the LLM agent."""
        load_dotenv()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def get_player_choice(
        self,
        player: Player,
        prompt: str,
        valid_choices: list[str],
        context: str = ""
    ) -> str:
        """
        Get a decision from a player using the LLM with structured output.

        Args:
            player: The player making the decision
            prompt: The specific question/prompt
            valid_choices: List of valid choice strings
            context: Additional context about the game state

        Returns:
            The player's choice (one of valid_choices)
        """
        system_message = player.get_context(
            phase=context or "game",
            visible_info={}
        )

        choices_str = "\n".join([f"- {choice}" for choice in valid_choices])

        user_message = f"""{prompt}

Available choices:
{choices_str}

Choose exactly one option from the list above."""

        # Create tool schema for structured output
        tool_schema = {
            "name": "make_choice",
            "description": "Make a choice from the available options",
            "input_schema": {
                "type": "object",
                "properties": {
                    "choice": {
                        "type": "string",
                        "description": "The exact choice from the available options",
                        "enum": valid_choices
                    }
                },
                "required": ["choice"]
            }
        }

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=100,
                temperature=0.7,
                system=system_message,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "make_choice"},
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract choice from tool use
            for block in response.content:
                if block.type == "tool_use" and block.name == "make_choice":
                    choice = block.input["choice"]

                    # Validate choice (should always be valid due to enum, but just in case)
                    if choice in valid_choices:
                        return choice

                    # Fallback for case-insensitive match
                    choice_lower = choice.lower()
                    for valid_choice in valid_choices:
                        if valid_choice.lower() == choice_lower:
                            return valid_choice

            # Fallback if no tool use found
            print(f"Warning: {player.name} did not use tool, using first option")
            return valid_choices[0]

        except Exception as e:
            print(f"Error getting choice from LLM for {player.name}: {e}")
            return valid_choices[0]

    def get_player_choice_with_reasoning(
        self,
        player: Player,
        prompt: str,
        valid_choices: list[str],
        context: str = ""
    ) -> tuple[str, str]:
        """Get a decision with reasoning from a player using structured output.

        Returns:
            Tuple of (choice, reasoning)
        """
        system_message = player.get_context(
            phase=context or "game",
            visible_info={}
        )

        choices_str = "\n".join([f"- {choice}" for choice in valid_choices])

        user_message = f"""{prompt}

Available choices:
{choices_str}

Explain your reasoning (1-2 sentences) and make your choice."""

        # Create tool schema for structured output with reasoning
        tool_schema = {
            "name": "make_choice_with_reasoning",
            "description": "Make a choice with reasoning explanation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "reasoning": {
                        "type": "string",
                        "description": "1-2 sentence explanation of the reasoning behind the choice"
                    },
                    "choice": {
                        "type": "string",
                        "description": "The exact choice from the available options",
                        "enum": valid_choices
                    }
                },
                "required": ["reasoning", "choice"]
            }
        }

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.7,
                system=system_message,
                tools=[tool_schema],
                tool_choice={"type": "tool", "name": "make_choice_with_reasoning"},
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )

            # Extract choice and reasoning from tool use
            for block in response.content:
                if block.type == "tool_use" and block.name == "make_choice_with_reasoning":
                    choice = block.input["choice"]
                    reasoning = block.input["reasoning"]

                    # Validate choice
                    if choice in valid_choices:
                        return choice, reasoning

                    # Fallback for case-insensitive match
                    choice_lower = choice.lower()
                    for valid_choice in valid_choices:
                        if valid_choice.lower() == choice_lower:
                            return valid_choice, reasoning

                    # Special handling for skip variations
                    skip_keywords = ["skip", "pass", "none", "no one", "wait", "hold", "don't"]
                    if any(keyword in choice_lower for keyword in skip_keywords):
                        for valid_choice in valid_choices:
                            if valid_choice.lower().startswith("skip"):
                                return valid_choice, reasoning

                    # If no match, use first choice
                    if valid_choices[0].lower().startswith("skip"):
                        return valid_choices[0], reasoning
                    else:
                        return valid_choices[0], f"[Invalid choice, used fallback] {reasoning}"

            # Fallback if no tool use found
            return valid_choices[0], "No reasoning provided"

        except Exception as e:
            return valid_choices[0], f"Error: {e}"

    def get_player_statement(
        self,
        player: Player,
        prompt: str,
        context: str = "",
        max_tokens: int = 300
    ) -> tuple[str, str]:
        """
        Get a free-form statement from a player using two-step structured output.
        First gets thinking, then generates statement based on that thinking.

        Args:
            player: The player making the statement
            prompt: The prompt for what to say
            context: Additional context
            max_tokens: Maximum length of response

        Returns:
            Tuple of (thinking, statement) where thinking is internal deliberation
            and statement is the public message
        """
        system_message = player.get_context(
            phase=context or "game",
            visible_info={}
        )

        # Step 1: Get thinking/reasoning
        thinking_schema = {
            "name": "internal_thinking",
            "description": "Your private internal thoughts and reasoning about the situation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "thinking": {
                        "type": "string",
                        "description": "Your internal deliberation and reasoning (1-2 sentences) - what you're actually thinking privately"
                    }
                },
                "required": ["thinking"]
            }
        }

        try:
            # First call: Get thinking
            thinking_response = self.client.messages.create(
                model=self.model,
                max_tokens=150,
                temperature=0.8,
                system=system_message,
                tools=[thinking_schema],
                tool_choice={"type": "tool", "name": "internal_thinking"},
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nFirst, what are you thinking privately about this situation?"}
                ]
            )

            thinking = "No thoughts"
            for block in thinking_response.content:
                if block.type == "tool_use" and block.name == "internal_thinking":
                    thinking = block.input.get("thinking", "No thoughts")
                    break

            # Step 2: Get public statement based on thinking
            statement_schema = {
                "name": "public_statement",
                "description": "Your public statement to other players based on your thinking",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "statement": {
                            "type": "string",
                            "description": "Your public statement to other players - what you actually say out loud (1-3 sentences)"
                        }
                    },
                    "required": ["statement"]
                }
            }

            statement_response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                temperature=0.8,
                system=system_message,
                tools=[statement_schema],
                tool_choice={"type": "tool", "name": "public_statement"},
                messages=[
                    {"role": "user", "content": f"{prompt}\n\nYou were thinking: {thinking}\n\nNow, what do you say out loud to the other players?"}
                ]
            )

            statement = f"{player.name} remains silent."
            for block in statement_response.content:
                if block.type == "tool_use" and block.name == "public_statement":
                    statement = block.input.get("statement", f"{player.name} remains silent.")
                    break

            return thinking, statement

        except Exception as e:
            print(f"Error getting statement from LLM for {player.name}: {e}")
            import traceback
            traceback.print_exc()
            return "Error occurred", f"{player.name} remains silent."
