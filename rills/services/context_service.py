"""Context building service for LLM prompts."""

from typing import TYPE_CHECKING, Optional

from ..models import InfoCategory, Statement
from . import prompt_templates as templates

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player
    from .information_service import InformationService


class ContextBuilder:
    """Builds LLM context from structured game state.

    This service centralizes prompt building and uses InformationService
    to access structured information instead of raw player.memories.
    """

    def __init__(self, info_service: "InformationService") -> None:
        """Initialize the context builder.

        Args:
        ----
            info_service: Information service for accessing game state

        """
        self.info_service = info_service

    def build_system_context(
        self,
        player: "Player",
        phase: str = "game",
        game: Optional["GameState"] = None,
    ) -> str:
        """Build the system context for a player (personality, role, status).

        Args:
        ----
            player: The player to build context for
            phase: Current game phase
            game: Optional game state for modifier checks

        Returns:
        -------
            Formatted system context string

        """
        # Base role context
        context_parts = [
            templates.ROLE_CONTEXT.format(
                player_name=player.name,
                personality=player.personality,
                role_description=player.role_description,
            ),
        ]

        # Add special status information
        special_status = self._build_special_status(player, game)
        if special_status:
            context_parts.append("\nSpecial Status:")
            context_parts.extend([f"- {status}" for status in special_status])

        # Add phase information
        phase_desc = templates.PHASE_DESCRIPTIONS.get(phase, phase)
        context_parts.append(f"\nCurrent phase: {phase_desc}")

        return "\n".join(context_parts)

    def _build_special_status(
        self,
        player: "Player",
        game: Optional["GameState"] = None,
    ) -> list[str]:
        """Build list of special status messages for a player.

        Args:
        ----
            player: The player to check status for
            game: Optional game state for modifier checks

        Returns:
        -------
            List of status strings

        """
        status = []

        # Dual-check: old flag or new modifier (if game is available)
        if player.suicidal or (game and player.has_modifier(game, "suicidal")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["suicidal"])

        # Dual-check: old flag or new modifier (if game is available)
        is_zombie = player.is_zombie or (game and player.has_modifier(game, "zombie"))
        if is_zombie and player.alive:
            status.append(templates.SPECIAL_STATUS_TEMPLATES["zombie_alive"])
        elif is_zombie and not player.alive:
            status.append(templates.SPECIAL_STATUS_TEMPLATES["zombie_undead"])

        # Dual-check: old flag or new modifier (if game is available)
        is_ghost = player.is_ghost or (game and player.has_modifier(game, "ghost"))
        if is_ghost and player.haunting_target:
            status.append(
                templates.SPECIAL_STATUS_TEMPLATES["ghost"].format(target=player.haunting_target),
            )

        # Dual-check: old flag or new modifier (if game is available)
        if player.is_sleepwalker or (game and player.has_modifier(game, "sleepwalker")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["sleepwalker"])

        # Dual-check: old flag or new modifier (if game is available)
        if player.is_insomniac or (game and player.has_modifier(game, "insomniac")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["insomniac"])

        if player.is_gun_nut:
            status.append(templates.SPECIAL_STATUS_TEMPLATES["gun_nut"])

        # Dual-check: old flag or new modifier (if game is available)
        if player.is_drunk or (game and player.has_modifier(game, "drunk")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["drunk"])

        # Dual-check: old flag or new modifier (if game is available)
        if player.vigilante_has_killed or (game and player.has_modifier(game, "vigilante_used")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["vigilante_used"])

        # Dual-check: old flag or new modifier (if game is available)
        if player.is_jester or (game and player.has_modifier(game, "jester")):
            status.append(templates.SPECIAL_STATUS_TEMPLATES["jester"])

        # Dual-check: old flag or new modifier (if game is available)
        is_priest = player.is_priest or (game and player.has_modifier(game, "priest"))
        if is_priest and player.resurrection_available:
            status.append(templates.SPECIAL_STATUS_TEMPLATES["priest"])

        # Dual-check: old flag or new modifier (if game is available)
        is_lover = player.is_lover or (game and player.has_modifier(game, "lover"))
        if is_lover and player.lover_name:
            status.append(
                templates.SPECIAL_STATUS_TEMPLATES["lover"].format(partner=player.lover_name),
            )

        # Dual-check: old flag or new modifier (if game is available)
        is_bodyguard = player.is_bodyguard or (game and player.has_modifier(game, "bodyguard"))
        if is_bodyguard and player.bodyguard_active:
            status.append(templates.SPECIAL_STATUS_TEMPLATES["bodyguard"])

        return status

    def build_information_context(
        self,
        player_name: str,
        categories: list[InfoCategory] | None = None,
        max_items: int = 10,
    ) -> str:
        """Build context from information visible to a player.

        Args:
        ----
            player_name: Name of the player
            categories: Optional list of categories to filter by
            max_items: Maximum number of information items to include

        Returns:
        -------
            Formatted information context string

        """
        if categories:
            # Build context for each category and combine
            contexts = []
            for category in categories:
                ctx = self.info_service.build_context_for(player_name, category=category)
                if ctx:
                    contexts.append(ctx)
            context = "\n".join(contexts)
        else:
            # No category filter
            context = self.info_service.build_context_for(player_name)

        if context:
            return f"\nWhat you know:\n{context}"
        return ""

    def build_for_night_kill(
        self,
        player: "Player",
        targets: list[str],
        team_members: list[str],
    ) -> str:
        """Build context for assassin kill decision.

        Args:
        ----
            player: The assassin making the decision
            targets: Available targets
            team_members: Other assassins

        Returns:
        -------
            Formatted prompt for kill decision

        """
        team_info = f"Your fellow Assassins: {', '.join(team_members)}"
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.VOTE, InfoCategory.STATEMENT],
        )

        return templates.NIGHT_KILL_PROMPT.format(
            player_name=player.name,
            team_info=team_info,
            recent_events=recent_events or "\nNo recent events.",
            targets=", ".join(targets),
        )

    def build_for_protection(
        self,
        player: "Player",
        targets: list[str],
        last_protected: str | None = None,
    ) -> str:
        """Build context for doctor protection decision.

        Args:
        ----
            player: The doctor making the decision
            targets: Available targets
            last_protected: Last person protected (can't repeat)

        Returns:
        -------
            Formatted prompt for protection decision

        """
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.ACTION],
        )

        prompt = templates.DOCTOR_PROTECT_PROMPT.format(
            player_name=player.name,
            recent_events=recent_events or "\nNo recent events.",
            targets=", ".join(targets),
        )

        if last_protected:
            prompt += f"\n\nNote: You protected {last_protected} last night and cannot protect them again."

        return prompt

    def build_for_investigation(self, player: "Player", targets: list[str]) -> str:
        """Build context for detective investigation.

        Args:
        ----
            player: The detective investigating
            targets: Available targets

        Returns:
        -------
            Formatted prompt for investigation

        """
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.VOTE, InfoCategory.STATEMENT],
        )

        return templates.DETECTIVE_INVESTIGATE_PROMPT.format(
            player_name=player.name,
            recent_events=recent_events or "\nNo recent events.",
            targets=", ".join(targets),
        )

    def build_for_vigilante_action(self, player: "Player", choices: list[str]) -> str:
        """Build context for vigilante kill decision.

        Args:
        ----
            player: The vigilante deciding
            choices: Available choices (including "Skip")

        Returns:
        -------
            Formatted prompt for vigilante action

        """
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.VOTE, InfoCategory.STATEMENT],
        )

        return templates.VIGILANTE_KILL_PROMPT.format(
            player_name=player.name,
            recent_events=recent_events or "\nNo recent events.",
            choices=", ".join(choices),
        )

    def build_for_resurrection(
        self,
        player: "Player",
        dead_players: list[str],
        choices: list[str],
    ) -> str:
        """Build context for priest resurrection decision.

        Args:
        ----
            player: The priest deciding
            dead_players: List of dead player names
            choices: Available choices (including "Skip")

        Returns:
        -------
            Formatted prompt for resurrection

        """
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.STATEMENT],
        )

        return templates.PRIEST_RESURRECT_PROMPT.format(
            player_name=player.name,
            recent_events=recent_events or "\nNo recent events.",
            dead_players=", ".join(dead_players),
            choices=", ".join(choices),
        )

    def build_for_bodyguard_protection(self, player: "Player", targets: list[str]) -> str:
        """Build context for bodyguard protection decision.

        Args:
        ----
            player: The bodyguard deciding
            targets: Available targets

        Returns:
        -------
            Formatted prompt for bodyguard protection

        """
        recent_events = self.build_information_context(
            player.name,
            categories=[InfoCategory.DEATH, InfoCategory.ACTION],
        )

        return templates.BODYGUARD_PROTECT_PROMPT.format(
            player_name=player.name,
            recent_events=recent_events or "\nNo recent events.",
            targets=", ".join(targets),
        )

    def build_for_ghost_haunt(self, player: "Player", targets: list[str], death_reason: str) -> str:
        """Build context for ghost haunting decision.

        Args:
        ----
            player: The deceased player
            targets: Available targets to haunt
            death_reason: How they died

        Returns:
        -------
            Formatted prompt for haunting decision

        """
        return templates.GHOST_HAUNT_PROMPT.format(
            player_name=player.name,
            death_info=f"You died: {death_reason}",
            targets=", ".join(targets),
        )

    def build_for_discussion(
        self,
        player: "Player",
        round_num: int,
        recent_statements: list[Statement] | None = None,
    ) -> str:
        """Build context for discussion phase.

        Args:
        ----
            player: The player speaking
            round_num: Current discussion round number
            recent_statements: Recent statements from other players

        Returns:
        -------
            Formatted prompt for discussion

        """
        context = self.build_information_context(player.name, max_items=15)

        if recent_statements:
            statements_text = "\n".join(
                [
                    f"- {s.speaker}: {s.content}" for s in recent_statements[-5:]
                ],  # Last 5 statements
            )

            return templates.DISCUSSION_WITH_STATEMENTS.format(
                round_num=round_num,
                recent_statements=statements_text,
                context=context or "No additional context.",
            )
        else:
            return templates.DISCUSSION_PROMPT.format(context=context or "The game has just begun.")

    def build_for_vote(
        self,
        player: "Player",
        candidates: list[str],
        discussion_summary: str | None = None,
    ) -> str:
        """Build context for voting decision.

        Args:
        ----
            player: The player voting
            candidates: Available candidates to vote for
            discussion_summary: Summary of discussion

        Returns:
        -------
            Formatted prompt for voting

        """
        context = self.build_information_context(player.name, max_items=15)

        return templates.LYNCH_VOTE_PROMPT.format(
            discussion_summary=discussion_summary or "No discussion occurred.",
            context=context or "No additional context.",
        )
