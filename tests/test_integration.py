"""Integration tests for the game flow."""

import pytest
from rills.game import create_game
from rills.roles import Role


class TestGameIntegration:
    """Integration tests for full game scenarios."""

    def test_full_game_creation(self):
        """Test creating a complete game."""
        configs = [
            {"name": "Alice", "role": "Assassins", "personality": "Cunning"},
            {"name": "Bob", "role": "Assassins", "personality": "Aggressive"},
            {"name": "Carol", "role": "Doctor", "personality": "Cautious"},
            {"name": "David", "role": "Detective", "personality": "Bold"},
            {"name": "Eve", "role": "Vigilante", "personality": "Suspicious"},
            {"name": "Frank", "role": "Villager", "personality": "Trusting"},
            {"name": "Grace", "role": "Villager", "personality": "Logical"},
            {"name": "Henry", "role": "Villager", "personality": "Nervous"},
        ]

        game = create_game(configs)

        assert len(game.players) == 8
        assert len(game.get_alive_players()) == 8
        assert len(game.get_alive_by_team("assassins")) >= 1
        assert len(game.get_alive_by_team("village")) >= 1

    def test_game_progression_scenario(self):
        """Test a basic game progression scenario."""
        configs = [
            {"name": "Assassin1", "role": "Assassins", "personality": "Evil"},
            {"name": "Assassin2", "role": "Assassins", "personality": "Evil"},
            {"name": "Villager1", "role": "Villager", "personality": "Good"},
            {"name": "Villager2", "role": "Villager", "personality": "Good"},
            {"name": "Doctor", "role": "Doctor", "personality": "Healer"},
        ]

        game = create_game(configs)

        # Initial state
        assert game.phase == "night"
        assert game.day_number == 1
        assert not game.game_over

        # Simulate night
        game.advance_phase()
        assert game.phase == "day"
        assert game.day_number == 1

        # Simulate day
        game.advance_phase()
        assert game.phase == "night"
        assert game.day_number == 2

    def test_elimination_sequence(self):
        """Test a sequence of eliminations."""
        configs = [
            {"name": "Assassin", "role": "Assassins", "personality": "Evil"},
            {"name": "V1", "role": "Villager", "personality": "Good"},
            {"name": "V2", "role": "Villager", "personality": "Good"},
            {"name": "V3", "role": "Villager", "personality": "Good"},
        ]

        game = create_game(configs)

        # Eliminate one villager
        v1 = game.get_player_by_name("V1")
        game.eliminate_player(v1, "Night kill", "V1 died")
        assert len(game.get_alive_players()) == 3

        # Eliminate another villager
        v2 = game.get_player_by_name("V2")
        game.eliminate_player(v2, "Lynch", "V2 lynched")
        assert len(game.get_alive_players()) == 2

        # Check events were recorded
        assert len(game.events) == 2

    def test_win_condition_triggers(self):
        """Test that win conditions trigger correctly."""
        configs = [
            {"name": "Assassin", "role": "Assassins", "personality": "Evil"},
            {"name": "Villager", "role": "Villager", "personality": "Good"},
        ]

        game = create_game(configs)

        # Equal numbers - assassins should win
        game.check_win_condition()
        assert game.game_over is True
        assert game.winner == "assassins"

    def test_memory_persistence(self):
        """Test that player memories persist across events."""
        configs = [
            {"name": "Alice", "role": "Assassins", "personality": "Cunning"},
            {"name": "Bob", "role": "Villager", "personality": "Trusting"},
        ]

        game = create_game(configs)
        alice = game.get_player_by_name("Alice")
        bob = game.get_player_by_name("Bob")

        # Add some memories
        alice.add_memory("I targeted Bob")
        alice.add_memory("Bob seems suspicious of me")

        assert len(alice.memories) == 2

        # Bob gets eliminated, Alice should remember
        game.eliminate_player(bob, "Killed", "Bob was eliminated")
        # Check for new death message format
        assert "Bob died. They were a Villager" in alice.memories[-1]
        assert len(alice.memories) == 3

    def test_special_mode_flags(self):
        """Test that special event modes can be enabled."""
        configs = [
            {"name": "Player", "role": "Villager", "personality": "Normal"},
        ]

        # Test with specific events enabled
        game = create_game(configs, enable_zombie=True, enable_ghost=True)

        # Game should have event registry
        assert hasattr(game, 'event_registry')
        assert game.event_registry is not None

        # Registry should have registered events
        assert len(game.event_registry._events) == 2

        # Test chaos mode
        chaos_game = create_game(configs, chaos_mode=True)
        assert len(chaos_game.event_registry._events) == 11  # All 11 events
