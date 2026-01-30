"""Tests for event system."""

import pytest
from rills.events import (
    EventRegistry,
    ZombieEvent,
    GhostEvent,
    SleepwalkerEvent,
    InsomniacEvent,
    GunNutEvent,
)
from rills.game import GameState
from rills.player import Player
from rills.roles import Role


class TestEventRegistry:
    """Test suite for EventRegistry."""

    def test_registry_creation(self):
        """Test creating an event registry."""
        registry = EventRegistry()
        assert len(registry.get_active_events()) == 0

    def test_register_event(self):
        """Test registering an event."""
        registry = EventRegistry()
        event = ZombieEvent()

        registry.register(event)
        assert event in registry._events

    def test_activate_events(self):
        """Test activating events."""
        registry = EventRegistry()

        # Create events with 100% probability for testing
        zombie = ZombieEvent(probability=1.0)
        ghost = GhostEvent(probability=1.0)

        registry.register(zombie)
        registry.register(ghost)

        activated = registry.activate_random_events()
        assert len(activated) == 2
        assert zombie.active
        assert ghost.active


class TestZombieEvent:
    """Test suite for ZombieEvent."""

    def test_zombie_event_creation(self):
        """Test creating a zombie event."""
        event = ZombieEvent()
        assert event.name == "Zombie Mode"
        assert "zombie" in event.description.lower()

    def test_zombie_chain_reaction(self):
        """Test zombie resurrection after elimination."""
        zombie = Player(name="Zed", role=Role.ZOMBIE, personality="Quiet")
        zombie.is_zombie = True
        villager = Player(name="Frank", role=Role.VILLAGER, personality="Normal")

        game = GameState(players=[zombie, villager])
        event = ZombieEvent()
        event.activate()

        # Eliminate the zombie
        event.on_player_eliminated(game, zombie, "Killed")

        # Zombie should be pending rise (internal to the event)
        assert zombie in event._pending_rise

        # After night start, zombie should become active
        event.on_night_start(game)
        assert zombie in event._active_zombies
        assert zombie not in event._pending_rise


class TestGhostEvent:
    """Test suite for GhostEvent."""

    def test_ghost_event_creation(self):
        """Test creating a ghost event."""
        event = GhostEvent()
        assert event.name == "Ghost Mode"
        assert "dead" in event.description.lower()

    def test_ghost_haunting_probability(self):
        """Test that ghost haunting has correct probability."""
        player = Player(name="Frank", role=Role.VILLAGER, personality="Normal")
        other = Player(name="Bob", role=Role.VILLAGER, personality="Normal")

        game = GameState(players=[player, other])
        event = GhostEvent()
        event.activate()

        # Run multiple times to check probability (not deterministic)
        ghost_count = 0
        for _ in range(100):
            test_player = Player(name="Test", role=Role.VILLAGER, personality="Normal")
            test_game = GameState(players=[test_player, other])
            event.on_player_eliminated(test_game, test_player, "Killed")
            if test_player.is_ghost:
                ghost_count += 1

        # Should be around 10% (with some variance)
        assert 0 < ghost_count < 30  # Reasonable range for 100 trials


class TestSleepwalkerEvent:
    """Test suite for SleepwalkerEvent."""

    def test_sleepwalker_event_creation(self):
        """Test creating a sleepwalker event."""
        event = SleepwalkerEvent()
        assert event.name == "Sleepwalker Mode"
        assert "wander" in event.description.lower()

    def test_sleepwalker_assignment(self):
        """Test that sleepwalker is assigned to a villager."""
        players = [
            Player(name="Frank", role=Role.VILLAGER, personality="Normal"),
            Player(name="Grace", role=Role.VILLAGER, personality="Normal"),
        ]

        game = GameState(players=players)
        event = SleepwalkerEvent()
        event.activate()
        event.setup_game(game)

        # One villager should be a sleepwalker
        sleepwalkers = [p for p in game.players if p.is_sleepwalker]
        assert len(sleepwalkers) == 1


class TestInsomniacEvent:
    """Test suite for InsomniacEvent."""

    def test_insomniac_event_creation(self):
        """Test creating an insomniac event."""
        event = InsomniacEvent()
        assert event.name == "Insomniac Mode"
        assert "watch" in event.description.lower()

    def test_insomniac_assignment(self):
        """Test that insomniac is assigned to a villager."""
        players = [
            Player(name="Frank", role=Role.VILLAGER, personality="Normal"),
            Player(name="Grace", role=Role.VILLAGER, personality="Normal"),
        ]

        game = GameState(players=players)
        event = InsomniacEvent()
        event.activate()
        event.setup_game(game)

        # One villager should be an insomniac
        insomniacs = [p for p in game.players if p.is_insomniac]
        assert len(insomniacs) == 1

    def test_insomniac_sees_someone(self):
        """Test that insomniac sees someone at night."""
        insomniac = Player(name="Frank", role=Role.VILLAGER, personality="Normal")
        insomniac.is_insomniac = True
        # Insomniac needs to see someone who moves (doctor, detective, assassins, sleepwalker)
        doctor = Player(name="Bob", role=Role.DOCTOR, personality="Normal")

        game = GameState(players=[insomniac, doctor])
        event = InsomniacEvent()
        event.activate()

        event.on_night_start(game)

        # Insomniac should have seen the doctor (who moves at night)
        assert insomniac.insomniac_sighting == "Bob"
        assert len(insomniac.memories) > 0


class TestGunNutEvent:
    """Test suite for GunNutEvent."""

    def test_gun_nut_event_creation(self):
        """Test creating a gun nut event."""
        event = GunNutEvent()
        assert event.name == "Gun Nut Mode"
        assert "armed" in event.description.lower()

    def test_gun_nut_assignment(self):
        """Test that gun nut is assigned to a villager."""
        players = [
            Player(name="Frank", role=Role.VILLAGER, personality="Normal"),
            Player(name="Grace", role=Role.VILLAGER, personality="Normal"),
        ]

        game = GameState(players=players)
        event = GunNutEvent()
        event.activate()
        event.setup_game(game)

        # One villager should be a gun nut
        gun_nuts = [p for p in game.players if p.is_gun_nut]
        assert len(gun_nuts) == 1

    def test_gun_nut_counter_attack(self):
        """Test gun nut counter attack mechanism."""
        gun_nut = Player(name="Frank", role=Role.VILLAGER, personality="Normal")
        gun_nut.is_gun_nut = True
        assassin = Player(name="Alice", role=Role.ASSASSINS, personality="Evil")

        game = GameState(players=[gun_nut, assassin])
        event = GunNutEvent()
        event.activate()

        # Check counter attack (probabilistic, so run multiple times)
        counter_attacks = 0
        for _ in range(100):
            result = event.check_counter_attack(game, gun_nut)
            if result is not None:
                counter_attacks += 1

        # Should be around 50%
        assert 30 < counter_attacks < 70  # Reasonable range
