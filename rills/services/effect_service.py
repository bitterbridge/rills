"""Effect service for applying game state changes."""

from copy import deepcopy
from dataclasses import dataclass
from typing import Any

from rills.models import PlayerModifier, PlayerState


@dataclass
class Effect:
    """An effect to be applied to game state."""

    type: str  # "add_modifier", "kill_player", "change_role", "heal", etc.
    target: str  # Player name or "game"
    data: dict[str, Any]
    source: str = "unknown"  # What created this effect

    def __repr__(self) -> str:
        return f"Effect({self.type} on {self.target} from {self.source})"


class EffectService:
    """Applies effects to game state."""

    def apply(
        self,
        effect: Effect,
        player_states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Apply an effect to player states.

        Args:
        ----
            effect: The effect to apply
            player_states: Dictionary of player_name -> PlayerState

        Returns:
        -------
            Updated player_states dictionary

        """
        # Create a copy to avoid mutating original
        new_states = deepcopy(player_states)

        if effect.type == "add_modifier":
            return self._add_modifier(effect, new_states)
        elif effect.type == "remove_modifier":
            return self._remove_modifier(effect, new_states)
        elif effect.type == "kill_player":
            return self._kill_player(effect, new_states)
        elif effect.type == "revive_player":
            return self._revive_player(effect, new_states)
        elif effect.type == "change_role":
            return self._change_role(effect, new_states)
        elif effect.type == "change_team":
            return self._change_team(effect, new_states)
        else:
            raise ValueError(f"Unknown effect type: {effect.type}")

    def apply_batch(
        self,
        effects: list[Effect],
        player_states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Apply multiple effects in sequence."""
        current_states = player_states
        for effect in effects:
            current_states = self.apply(effect, current_states)
        return current_states

    def _add_modifier(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Add a modifier to a player."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        modifier = PlayerModifier(
            type=effect.data.get("modifier_type", "unknown"),
            source=effect.source,
            active=True,
            data=effect.data.get("modifier_data", {}),
            expires_on=effect.data.get("expires_on"),
            applied_on=effect.data.get("applied_on", 0),
        )
        player.add_modifier(modifier)

        return states

    def _remove_modifier(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Remove a modifier from a player."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        modifier_type = effect.data.get("modifier_type")
        if modifier_type:
            player.remove_modifier(modifier_type)

        return states

    def _kill_player(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Kill a player."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        player.alive = False

        # Add death modifier for tracking
        death_modifier = PlayerModifier(
            type="dead",
            source=effect.source,
            active=True,
            data={"cause": effect.data.get("cause", "unknown")},
            applied_on=effect.data.get("day", 0),
        )
        player.add_modifier(death_modifier)

        return states

    def _revive_player(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Revive a player."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        player.alive = True
        player.remove_modifier("dead")

        return states

    def _change_role(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Change a player's role."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        new_role = effect.data.get("new_role")
        if new_role:
            player.role = new_role

        return states

    def _change_team(
        self,
        effect: Effect,
        states: dict[str, PlayerState],
    ) -> dict[str, PlayerState]:
        """Change a player's team."""
        if effect.target not in states:
            return states

        player = states[effect.target]
        new_team = effect.data.get("new_team")
        if new_team:
            player.team = new_team

        return states

    @staticmethod
    def create_modifier_effect(
        target: str,
        modifier_type: str,
        source: str,
        expires_on: int | None = None,
        applied_on: int = 0,
        modifier_data: dict | None = None,
    ) -> Effect:
        """Factory method to create a modifier effect."""
        return Effect(
            type="add_modifier",
            target=target,
            source=source,
            data={
                "modifier_type": modifier_type,
                "expires_on": expires_on,
                "applied_on": applied_on,
                "modifier_data": modifier_data or {},
            },
        )

    @staticmethod
    def create_death_effect(target: str, source: str, cause: str, day: int) -> Effect:
        """Factory method to create a death effect."""
        return Effect(
            type="kill_player",
            target=target,
            source=source,
            data={"cause": cause, "day": day},
        )

    @staticmethod
    def create_role_change_effect(target: str, new_role: str, source: str) -> Effect:
        """Factory method to create a role change effect."""
        return Effect(type="change_role", target=target, source=source, data={"new_role": new_role})
