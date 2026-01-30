"""Tests for roles module."""

import pytest
from rills.roles import Role, get_role_info, ROLE_DESCRIPTIONS


class TestRoles:
    """Test suite for roles module."""

    def test_all_roles_exist(self):
        """Test that all expected roles are defined."""
        expected_roles = [
            Role.ASSASSINS,
            Role.DOCTOR,
            Role.DETECTIVE,
            Role.VIGILANTE,
            Role.ZOMBIE,
            Role.VILLAGER,
        ]
        assert len(expected_roles) == 6

    def test_role_values(self):
        """Test role string values."""
        assert Role.ASSASSINS.value == "Assassins"
        assert Role.DOCTOR.value == "Doctor"
        assert Role.DETECTIVE.value == "Detective"
        assert Role.VIGILANTE.value == "Vigilante"
        assert Role.ZOMBIE.value == "Zombie"
        assert Role.VILLAGER.value == "Villager"

    def test_get_role_info_assassins(self):
        """Test getting Assassins role info."""
        info = get_role_info(Role.ASSASSINS)
        assert info["name"] == "Assassins"
        assert info["team"] == "assassins"
        assert info["night_action"] is True
        assert "Assassins" in info["description"]

    def test_get_role_info_doctor(self):
        """Test getting Doctor role info."""
        info = get_role_info(Role.DOCTOR)
        assert info["name"] == "Doctor"
        assert info["team"] == "village"
        assert info["night_action"] is True
        assert "protect" in info["description"]

    def test_get_role_info_detective(self):
        """Test getting Detective role info."""
        info = get_role_info(Role.DETECTIVE)
        assert info["name"] == "Detective"
        assert info["team"] == "village"
        assert info["night_action"] is True
        assert "investigate" in info["description"]

    def test_get_role_info_vigilante(self):
        """Test getting Vigilante role info."""
        info = get_role_info(Role.VIGILANTE)
        assert info["name"] == "Vigilante"
        assert info["team"] == "village"
        assert info["night_action"] is True

    def test_get_role_info_zombie(self):
        """Test getting Zombie role info."""
        info = get_role_info(Role.ZOMBIE)
        assert info["name"] == "Zombie"
        assert info["team"] == "village"
        assert info["night_action"] is False
        assert "zombie" in info["description"].lower()

    def test_get_role_info_villager(self):
        """Test getting Villager role info."""
        info = get_role_info(Role.VILLAGER)
        assert info["name"] == "Villager"
        assert info["team"] == "village"
        assert info["night_action"] is False

    def test_all_roles_have_descriptions(self):
        """Test that all roles have complete descriptions."""
        for role in Role:
            info = get_role_info(role)
            assert "name" in info
            assert "team" in info
            assert "description" in info
            assert "night_action" in info
            assert len(info["description"]) > 0

    def test_team_assignments(self):
        """Test that teams are correctly assigned."""
        assassins_info = get_role_info(Role.ASSASSINS)
        assert assassins_info["team"] == "assassins"

        village_roles = [Role.DOCTOR, Role.DETECTIVE, Role.VIGILANTE, Role.ZOMBIE, Role.VILLAGER]
        for role in village_roles:
            info = get_role_info(role)
            assert info["team"] == "village"

    def test_night_action_roles(self):
        """Test which roles have night actions."""
        night_action_roles = [Role.ASSASSINS, Role.DOCTOR, Role.DETECTIVE, Role.VIGILANTE]
        no_night_action_roles = [Role.ZOMBIE, Role.VILLAGER]

        for role in night_action_roles:
            info = get_role_info(role)
            assert info["night_action"] is True

        for role in no_night_action_roles:
            info = get_role_info(role)
            assert info["night_action"] is False
