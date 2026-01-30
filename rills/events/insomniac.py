"""Insomniac event - a player witnesses night activity."""

import random
from typing import TYPE_CHECKING

from ..models import PlayerModifier
from .base import EventModifier

if TYPE_CHECKING:
    from ..game import GameState
    from ..player import Player


class InsomniacEvent(EventModifier):
    """Insomniac event.

    One random villager is an insomniac who sees someone
    moving around at night but can't tell what they're doing.
    """

    def __init__(self) -> None:
        super().__init__()
        self._sightings: list[tuple[str, str, bool]] = []  # (insomniac, seen, was_dead)

    @property
    def name(self) -> str:
        return "Insomniac Mode"

    @property
    def description(self) -> str:
        return "Someone can't sleep and watches..."

    def setup_game(self, game: "GameState") -> None:
        """Assign insomniac to a random non-suicidal villager."""
        available = [
            p
            for p in game.players
            if p.team == "village" and not p.suicidal and not p.is_sleepwalker
        ]

        if available:
            insomniac = random.choice(available)
            insomniac.is_insomniac = True  # Old flag (backward compatibility)
            insomniac.add_modifier(
                game,
                PlayerModifier(type="insomniac", source="event:insomniac"),
            )  # NEW: permanent modifier

    def on_player_eliminated(self, game: "GameState", player: "Player", reason: str) -> None:
        """No special behavior on elimination."""

    def on_night_start(self, game: "GameState") -> None:
        """Insomniac sees someone moving around."""
        from ..roles import Role

        self._sightings = []

        insomniacs = [p for p in game.get_alive_players() if p.is_insomniac]

        for insomniac in insomniacs:
            # Reset sighting
            insomniac.insomniac_sighting = None

            # See only players who move at night:
            # - Assassins (killing)
            # - Doctor (protecting)
            # - Detective (investigating)
            # - Sleepwalkers (wandering)
            # - Zombies (even if dead - very amusing!)
            movers = [
                p
                for p in game.get_alive_players()
                if p != insomniac
                and (p.role in [Role.ASSASSINS, Role.DOCTOR, Role.DETECTIVE] or p.is_sleepwalker)
            ]

            # Also include zombies (even dead ones!)
            # Dual-check: old flag or new modifier
            zombies = [
                p
                for p in game.players
                if (p.is_zombie or p.has_modifier(game, "zombie")) and not p.alive
            ]
            all_visible = movers + zombies

            if all_visible:
                seen = random.choice(all_visible)
                insomniac.insomniac_sighting = seen.name

                # Note: Sighting will be revealed at night end and tracked by InformationService
                self._sightings.append((insomniac.name, seen.name, not seen.alive))

    def on_night_end(self, game: "GameState") -> None:
        """Reveal insomniac sightings."""
        if self._sightings:
            print("\n--- Insomniac Report ---")
            for insomniac_name, seen_name, was_dead in self._sightings:
                if was_dead:
                    print(
                        f"👁️  {insomniac_name} saw {seen_name} moving around at night... but isn't {seen_name} dead?!",
                    )
                    # Note: Anomaly information could be tracked by InformationService
                else:
                    print(f"👁️  {insomniac_name} saw {seen_name} moving around at night...")
                    # Note: Sighting information tracked by InformationService
            print()
        self._sightings = []
