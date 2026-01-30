"""Pytest configuration and fixtures."""

import pytest
from rills.roles import Role
from rills.player import Player
from rills.game import GameState


@pytest.fixture
def basic_players():
    """Create a basic set of players for testing."""
    return [
        Player(name="Alice", role=Role.ASSASSINS, personality="Cunning"),
        Player(name="Bob", role=Role.ASSASSINS, personality="Aggressive"),
        Player(name="Carol", role=Role.DOCTOR, personality="Cautious"),
        Player(name="David", role=Role.DETECTIVE, personality="Bold"),
        Player(name="Eve", role=Role.VIGILANTE, personality="Suspicious"),
        Player(name="Frank", role=Role.VILLAGER, personality="Trusting"),
        Player(name="Grace", role=Role.VILLAGER, personality="Logical"),
        Player(name="Henry", role=Role.ZOMBIE, personality="Quiet"),
    ]


@pytest.fixture
def game_state(basic_players):
    """Create a basic game state for testing."""
    return GameState(players=basic_players)


@pytest.fixture
def game_with_events():
    """Create a game state with all event modes enabled."""
    players = [
        Player(name="Alice", role=Role.ASSASSINS, personality="Cunning"),
        Player(name="Bob", role=Role.DOCTOR, personality="Cautious"),
        Player(name="Carol", role=Role.VILLAGER, personality="Normal", is_sleepwalker=True),
        Player(name="David", role=Role.VILLAGER, personality="Anxious", is_insomniac=True),
        Player(name="Eve", role=Role.VILLAGER, personality="Armed", is_gun_nut=True),
    ]
    return GameState(
        players=players,
        zombie_mode_active=True,
        ghost_mode_active=True,
        sleepwalker_mode_active=True,
        insomniac_mode_active=True,
        gun_nut_mode_active=True,
    )
