"""Knowledge state models for tracking what players know."""

from dataclasses import dataclass, field

from .information import InfoCategory, InformationStore


@dataclass
class KnowledgeState:
    """Tracks what information a player has access to."""

    player_name: str
    information_ids: set[str] = field(default_factory=set)

    def add_information(self, info_id: str):
        """Grant access to a piece of information."""
        self.information_ids.add(info_id)

    def add_multiple(self, info_ids: list[str]):
        """Grant access to multiple pieces of information."""
        self.information_ids.update(info_ids)

    def knows_about(self, info_id: str) -> bool:
        """Check if player has access to specific information."""
        return info_id in self.information_ids

    def get_knowledge_summary(
        self,
        info_store: InformationStore,
        category: InfoCategory | None = None,
        day_number: int | None = None,
    ) -> str:
        """Get formatted summary of what this player knows."""
        # Get all information this player has access to
        all_info = []
        for info_id in self.information_ids:
            info = info_store.get(info_id)
            if info:
                # Apply filters if provided
                if category and info.category != category:
                    continue
                if day_number is not None and info.day_number != day_number:
                    continue
                all_info.append(info)

        if not all_info:
            return "No information available."

        # Sort by timestamp
        all_info.sort(key=lambda i: i.timestamp)

        # Group by category if no category filter
        if category is None:
            by_category: dict[InfoCategory, list[str]] = {}
            for info in all_info:
                if info.category not in by_category:
                    by_category[info.category] = []
                by_category[info.category].append(info.content)

            sections = []
            for cat, items in by_category.items():
                sections.append(f"\n{cat.value.upper()}:")
                for item in items:
                    sections.append(f"  - {item}")

            return "\n".join(sections)
        else:
            # Single category, just list items
            items = [f"  - {info.content}" for info in all_info]
            return "\n".join(items)

    def get_info_count(self, category: InfoCategory | None = None) -> int:
        """Count how many pieces of information this player knows."""
        if category is None:
            return len(self.information_ids)
        # Would need info_store to filter by category - leave simple for now
        return len(self.information_ids)

    def clear(self):
        """Clear all knowledge (for testing)."""
        self.information_ids.clear()
