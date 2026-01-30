"""Information service for managing information flow and revelation."""

from datetime import datetime

from rills.models import InfoCategory, Information, InformationStore, KnowledgeState, Visibility


class InformationService:
    """Manages information flow and revelation to players."""

    def __init__(self, store: InformationStore | None = None):
        self.store = store or InformationStore()
        self.knowledge: dict[str, KnowledgeState] = {}

    def register_player(self, player_name: str):
        """Register a player to track their knowledge."""
        if player_name not in self.knowledge:
            self.knowledge[player_name] = KnowledgeState(player_name=player_name)

    def reveal_death(self, player_name: str, role: str, cause: str, day: int) -> str:
        """Create and distribute death information to all players.

        Args:
            player_name: Name of the player who died
            role: Display name of the role (use Role.display_name() for proper grammar)
            cause: Cause of death
            day: Day number when death occurred
        """
        info = Information.create(
            content=f"{player_name} died. They were {role}.",
            source="game",
            category=InfoCategory.DEATH,
            visibility=Visibility("public", []),
            day_number=day,
            cause=cause,
        )
        info_id = self.store.add(info)

        # Reveal to all registered players
        for knowledge_state in self.knowledge.values():
            knowledge_state.add_information(info_id)

        return info_id

    def reveal_role(self, player_name: str, role: str, to_players: list[str], day: int) -> str:
        """Reveal a player's role to specific players."""
        info = Information.create(
            content=f"{player_name} is a {role}.",
            source="game",
            category=InfoCategory.ROLE_REVEAL,
            visibility=Visibility("private", to_players),
            day_number=day,
        )
        info_id = self.store.add(info)

        # Reveal to specified players
        for player in to_players:
            if player in self.knowledge:
                self.knowledge[player].add_information(info_id)

        return info_id

    def reveal_to_player(
        self, player_name: str, content: str, category: InfoCategory, day: int, **metadata
    ) -> str:
        """Reveal private information to a specific player."""
        info = Information.create(
            content=content,
            source="game",
            category=category,
            visibility=Visibility("private", [player_name]),
            day_number=day,
            **metadata,
        )
        info_id = self.store.add(info)

        if player_name in self.knowledge:
            self.knowledge[player_name].add_information(info_id)

        return info_id

    def reveal_to_team(
        self,
        team: str,
        content: str,
        category: InfoCategory,
        day: int,
        team_members: list[str],
        **metadata,
    ) -> str:
        """Reveal information to all members of a team."""
        info = Information.create(
            content=content,
            source="game",
            category=category,
            visibility=Visibility("team", [team]),
            day_number=day,
            **metadata,
        )
        info_id = self.store.add(info)

        # Reveal to all team members
        for member in team_members:
            if member in self.knowledge:
                self.knowledge[member].add_information(info_id)

        return info_id

    def reveal_to_all(
        self, content: str, category: InfoCategory, day: int, source: str = "game", **metadata
    ) -> str:
        """Reveal public information to all players."""
        info = Information.create(
            content=content,
            source=source,
            category=category,
            visibility=Visibility("public", []),
            day_number=day,
            **metadata,
        )
        info_id = self.store.add(info)

        # Reveal to all registered players
        for knowledge_state in self.knowledge.values():
            knowledge_state.add_information(info_id)

        return info_id

    def build_context_for(
        self,
        player_name: str,
        category: InfoCategory | None = None,
        day_number: int | None = None,
        since: datetime | None = None,
    ) -> str:
        """Build context string for LLM prompt from player's knowledge."""
        if player_name not in self.knowledge:
            return ""

        knowledge_state = self.knowledge[player_name]

        # Get all information this player knows
        all_info = []
        for info_id in knowledge_state.information_ids:
            info = self.store.get(info_id)
            if info is None:
                continue

            # Apply filters
            if category and info.category != category:
                continue
            if day_number is not None and info.day_number != day_number:
                continue
            if since and info.timestamp < since:
                continue

            all_info.append(info)

        if not all_info:
            return ""

        # Sort by timestamp
        all_info.sort(key=lambda i: i.timestamp)

        # Format as context
        return "\n".join(info.content for info in all_info)

    def get_knowledge_summary(self, player_name: str, category: InfoCategory | None = None) -> str:
        """Get formatted knowledge summary for a player."""
        if player_name not in self.knowledge:
            return "No information available."

        return self.knowledge[player_name].get_knowledge_summary(self.store, category=category)

    def get_public_info(self, day_number: int | None = None) -> list[Information]:
        """Get all public information, optionally filtered by day."""
        return self.store.query(
            visible_to="anyone",
            day_number=day_number,  # Will match public visibility
        )

    def clear(self):
        """Clear all information (for testing)."""
        self.store.clear()
        self.knowledge.clear()
