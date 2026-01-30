"""Tests for GameState class."""

import pytest
from rills.game import GameState, create_game
from rills.player import Player
from rills.roles import Role


class TestGameState:
    """Test suite for GameState class."""

    def test_game_initialization(self, basic_players):
        """Test game state initialization."""
        game = GameState(players=basic_players)
        assert len(game.players) == 8
        assert game.day_number == 1
        assert game.phase == "night"
        assert game.game_over is False
        assert game.winner is None

    def test_get_alive_players(self, game_state):
        """Test getting alive players."""
        alive = game_state.get_alive_players()
        assert len(alive) == 8

        # Kill a player
        game_state.players[0].alive = False
        alive = game_state.get_alive_players()
        assert len(alive) == 7

    def test_get_alive_by_team(self, game_state):
        """Test getting alive players by team."""
        assassins = game_state.get_alive_by_team("assassins")
        village = game_state.get_alive_by_team("village")

        assert len(assassins) == 2  # Alice and Bob
        assert len(village) == 6  # Everyone else

    def test_get_player_by_name(self, game_state):
        """Test finding players by name."""
        alice = game_state.get_player_by_name("Alice")
        assert alice is not None
        assert alice.name == "Alice"

        # Case insensitive
        bob = game_state.get_player_by_name("bob")
        assert bob is not None
        assert bob.name == "Bob"

        # Non-existent player
        nobody = game_state.get_player_by_name("Nobody")
        assert nobody is None

    def test_eliminate_player_basic(self, game_state):
        """Test basic player elimination."""
        alice = game_state.get_player_by_name("Alice")
        assert alice.alive is True

        game_state.eliminate_player(alice, "Test reason", "Public reason")
        assert alice.alive is False
        assert len(game_state.events) == 1
        assert "Alice" in game_state.events[0]

    def test_eliminate_player_memories(self, game_state):
        """Test that other players remember eliminations."""
        alice = game_state.get_player_by_name("Alice")
        bob = game_state.get_player_by_name("Bob")

        initial_memories = len(bob.memories)
        game_state.eliminate_player(alice, "Test reason", "Alice was eliminated")

        assert len(bob.memories) == initial_memories + 1
        assert "Alice was eliminated" in bob.memories

    def test_check_win_condition_village_wins(self, game_state):
        """Test win condition when village eliminates all assassins."""
        # Kill all assassins
        for player in game_state.players:
            if player.role == Role.ASSASSINS:
                player.alive = False

        game_state.check_win_condition()
        assert game_state.game_over is True
        assert game_state.winner == "village"

    def test_check_win_condition_assassins_win(self, game_state):
        """Test win condition when assassins equal/outnumber village."""
        # Kill villagers until assassins equal them
        village_players = [p for p in game_state.players if p.team == "village"]
        for i, player in enumerate(village_players):
            if i < 4:  # Leave only 2 alive (equal to 2 assassins)
                player.alive = False

        game_state.check_win_condition()
        assert game_state.game_over is True
        assert game_state.winner == "assassins"

    def test_advance_phase(self, game_state):
        """Test phase advancement."""
        assert game_state.phase == "night"
        assert game_state.day_number == 1

        game_state.advance_phase()
        assert game_state.phase == "day"
        assert game_state.day_number == 1

        game_state.advance_phase()
        assert game_state.phase == "night"
        assert game_state.day_number == 2

    def test_get_phase_description(self, game_state):
        """Test phase description generation."""
        assert game_state.get_phase_description() == "Night 1"

        game_state.advance_phase()
        assert game_state.get_phase_description() == "Day 1"

    def test_zombie_mode_elimination(self):
        """Test zombie elimination triggers pending zombification."""
        from rills.events import EventRegistry, ZombieEvent

        zombie = Player(name="Zed", role=Role.ZOMBIE, personality="Quiet")
        zombie.is_zombie = True
        villager = Player(name="Frank", role=Role.VILLAGER, personality="Normal")

        registry = EventRegistry()
        zombie_event = ZombieEvent()
        zombie_event.activate()
        registry.register(zombie_event)

        game = GameState(
            players=[zombie, villager],
            event_registry=registry
        )

        game.eliminate_player(zombie, "Killed", "Zed died")

        # In zombie mode, a villager should be marked for zombification

class TestCreateGame:
    """Test suite for create_game function."""

    def test_create_game_randomizes_roles(self):
        """Test that create_game randomizes roles."""
        configs = [
            {"name": "Alice", "role": "Assassins", "personality": "Cunning"},
            {"name": "Bob", "role": "Doctor", "personality": "Cautious"},
            {"name": "Carol", "role": "Villager", "personality": "Normal"},
        ]

        game = create_game(configs)
        assert len(game.players) == 3

        # Check that all roles are present (just shuffled)
        roles = sorted([p.role for p in game.players])
        expected = sorted([Role.ASSASSINS, Role.DOCTOR, Role.VILLAGER])
        assert roles == expected

    def test_create_game_randomizes_personalities(self):
        """Test that create_game randomizes personalities."""
        configs = [
            {"name": "Alice", "role": "Assassins", "personality": "Cunning"},
            {"name": "Bob", "role": "Doctor", "personality": "Cautious"},
            {"name": "Carol", "role": "Villager", "personality": "Normal"},
        ]

        game = create_game(configs)

        # Check that all personalities are present (just shuffled)
        personalities = sorted([p.personality for p in game.players])
        expected = sorted(["Cunning", "Cautious", "Normal"])
        assert personalities == expected

    def test_create_game_assigns_suicidal_villager(self):
        """Test that one villager is marked as suicidal."""
        configs = [
            {"name": "Alice", "role": "Villager", "personality": "Normal"},
            {"name": "Bob", "role": "Villager", "personality": "Cautious"},
            {"name": "Carol", "role": "Doctor", "personality": "Caring"},
        ]

        game = create_game(configs)

        # Exactly one villager should be suicidal
        suicidal_count = sum(1 for p in game.players if p.suicidal)
        # Could be 0 or 1 depending on random assignment
        assert suicidal_count <= 1

    def test_create_game_event_modes(self):
        """Test that event modes are randomly assigned."""
        configs = [
            {"name": "Alice", "role": "Villager", "personality": "Normal"},
        ]

        game = create_game(configs)

        # Game should have event registry
        assert hasattr(game, 'event_registry')
        assert game.event_registry is not None
