"""Tests for Player class."""

from rills.player import Player
from rills.roles import Role


class TestPlayer:
    """Test suite for Player class."""

    def test_player_creation(self):
        """Test basic player creation."""
        player = Player(name="Alice", role=Role.ASSASSINS, personality="Cunning")
        assert player.name == "Alice"
        assert player.role == Role.ASSASSINS
        assert player.personality == "Cunning"
        assert player.alive is True
        assert player.team == "assassins"

    def test_player_is_assassin(self):
        """Test is_assassin method."""
        assassin = Player(name="Alice", role=Role.ASSASSINS, personality="Cunning")
        villager = Player(name="Bob", role=Role.VILLAGER, personality="Trusting")

        assert assassin.is_assassin() is True
        assert villager.is_assassin() is False

    def test_zombie_player_initialization(self):
        """Test that zombie players are marked correctly."""
        zombie = Player(name="Zed", role=Role.ZOMBIE, personality="Quiet")
        assert zombie.is_zombie is True
        assert zombie.team == "village"

    def test_special_role_flags(self):
        """Test special role flags."""
        player = Player(name="Carol", role=Role.VILLAGER, personality="Normal")

        # Initially false
        assert player.is_sleepwalker is False
        assert player.is_insomniac is False
        assert player.is_gun_nut is False
        assert player.suicidal is False

        # Can be set
        player.is_sleepwalker = True
        player.is_gun_nut = True
        assert player.is_sleepwalker is True
        assert player.is_gun_nut is True

    def test_vigilante_flag(self):
        """Test vigilante has_killed flag."""
        vigilante = Player(name="Eve", role=Role.VIGILANTE, personality="Suspicious")
        assert vigilante.vigilante_has_killed is False

        vigilante.vigilante_has_killed = True
        assert vigilante.vigilante_has_killed is True

    def test_ghost_haunting(self):
        """Test ghost haunting mechanics."""
        player = Player(name="Frank", role=Role.VILLAGER, personality="Normal")
        assert player.is_ghost is False
        assert player.haunting_target is None

        player.is_ghost = True
        player.haunting_target = "Bob"
        assert player.is_ghost is True
        assert player.haunting_target == "Bob"
