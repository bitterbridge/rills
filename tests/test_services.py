"""Tests for service layer."""

from rills.models import InfoCategory, PlayerModifier, PlayerState
from rills.services import (
    ConversationService,
    Effect,
    EffectService,
    InformationService,
    VoteService,
)


class MockPlayer:
    """Mock player for testing."""

    def __init__(self, name: str, personality: str = ""):
        self.name = name
        self.personality = personality


class TestInformationService:
    """Test InformationService."""

    def test_register_player(self):
        service = InformationService()
        service.register_player("Alice")

        assert "Alice" in service.knowledge
        assert service.knowledge["Alice"].player_name == "Alice"

    def test_reveal_death(self):
        service = InformationService()
        service.register_player("Alice")
        service.register_player("Bob")

        info_id = service.reveal_death("Charlie", "Villager", "lynch", day=1)

        # Both players should know about the death
        assert service.knowledge["Alice"].knows_about(info_id)
        assert service.knowledge["Bob"].knows_about(info_id)

        # Check content
        info = service.store.get(info_id)
        assert "Charlie died" in info.content
        assert "Villager" in info.content

    def test_reveal_to_player(self):
        service = InformationService()
        service.register_player("Alice")
        service.register_player("Bob")

        info_id = service.reveal_to_player(
            "Alice", "You killed someone", InfoCategory.ACTION, day=1
        )

        # Only Alice should know
        assert service.knowledge["Alice"].knows_about(info_id)
        assert not service.knowledge["Bob"].knows_about(info_id)

    def test_reveal_to_team(self):
        service = InformationService()
        service.register_player("Alice")
        service.register_player("Bob")
        service.register_player("Charlie")

        info_id = service.reveal_to_team(
            team="Assassins",
            content="You are all assassins",
            category=InfoCategory.TEAM_INFO,
            day=0,
            team_members=["Alice", "Bob"],
        )

        # Alice and Bob should know, Charlie shouldn't
        assert service.knowledge["Alice"].knows_about(info_id)
        assert service.knowledge["Bob"].knows_about(info_id)
        assert not service.knowledge["Charlie"].knows_about(info_id)

    def test_reveal_to_all(self):
        service = InformationService()
        service.register_player("Alice")
        service.register_player("Bob")

        info_id = service.reveal_to_all("Game starts!", InfoCategory.GAME_STATE, day=0)

        # Everyone should know
        assert service.knowledge["Alice"].knows_about(info_id)
        assert service.knowledge["Bob"].knows_about(info_id)

    def test_build_context_for(self):
        service = InformationService()
        service.register_player("Alice")

        service.reveal_to_player("Alice", "Info 1", InfoCategory.ACTION, day=1)
        service.reveal_to_player("Alice", "Info 2", InfoCategory.ACTION, day=1)

        context = service.build_context_for("Alice")
        assert "Info 1" in context
        assert "Info 2" in context

    def test_build_context_with_category_filter(self):
        service = InformationService()
        service.register_player("Alice")

        service.reveal_to_player("Alice", "Action info", InfoCategory.ACTION, day=1)
        service.reveal_to_player("Alice", "Death info", InfoCategory.DEATH, day=1)

        context = service.build_context_for("Alice", category=InfoCategory.ACTION)
        assert "Action info" in context
        assert "Death info" not in context


class TestConversationService:
    """Test ConversationService."""

    def test_get_speaking_order(self):
        service = ConversationService()

        players = [
            MockPlayer("Alice", "aggressive and bold"),
            MockPlayer("Bob", "quiet and timid"),
            MockPlayer("Charlie", "neutral person"),
        ]

        # Run multiple times to verify it's deterministic enough
        orders = []
        for _ in range(10):
            order = service.get_speaking_order(players)
            orders.append([p.name for p in order])

        # Alice (aggressive) should tend to be earlier than Bob (timid)
        alice_positions = [order.index("Alice") for order in orders]
        bob_positions = [order.index("Bob") for order in orders]

        avg_alice = sum(alice_positions) / len(alice_positions)
        avg_bob = sum(bob_positions) / len(bob_positions)

        assert avg_alice < avg_bob  # Alice speaks earlier on average

    def test_conduct_round(self):
        service = ConversationService()

        players = [MockPlayer("Alice"), MockPlayer("Bob")]

        def get_statement(player, context, round_num):
            return (f"{player.name} thinking", f"{player.name} says hello")

        round_obj = service.conduct_round(
            participants=players,
            phase="test_phase",
            round_number=1,
            day_number=1,
            get_statement_func=get_statement,
        )

        assert len(round_obj.statements) == 2
        assert round_obj.phase == "test_phase"
        assert round_obj.round_number == 1

    def test_conduct_round_with_context(self):
        service = ConversationService()

        players = [MockPlayer("Alice"), MockPlayer("Bob")]

        contexts_seen = []

        def get_statement(player, context, round_num):
            contexts_seen.append((player.name, context))
            return ("thinking", f"{player.name} speaks")

        service.conduct_round(
            participants=players,
            phase="test",
            round_number=1,
            day_number=1,
            get_statement_func=get_statement,
        )

        # First speaker sees no context
        assert contexts_seen[0][1] == ""
        # Second speaker sees first speaker's statement
        assert "speaks" in contexts_seen[1][1]

    def test_get_recent_statements(self):
        service = ConversationService()

        players = [MockPlayer("Alice")]

        def get_statement(player, context, round_num):
            return ("thinking", f"Statement {round_num}")

        # Create multiple rounds
        for i in range(5):
            service.conduct_round(
                participants=players,
                phase="test",
                round_number=i,
                day_number=1,
                get_statement_func=get_statement,
            )

        recent = service.get_recent_statements("Alice", count=3)
        assert len(recent) == 3

    def test_format_round_for_display(self):
        service = ConversationService()

        players = [MockPlayer("Alice"), MockPlayer("Bob")]

        def get_statement(player, context, round_num):
            return ("secret thoughts", f"{player.name} message")

        round_obj = service.conduct_round(
            participants=players,
            phase="discussion",
            round_number=1,
            day_number=1,
            get_statement_func=get_statement,
        )

        # Without thinking
        display = service.format_round_for_display(round_obj, show_thinking=False)
        assert "Alice: Alice message" in display
        assert "secret thoughts" not in display

        # With thinking
        display_with = service.format_round_for_display(round_obj, show_thinking=True)
        assert "secret thoughts" in display_with


class TestVoteService:
    """Test VoteService."""

    def test_conduct_vote_simple(self):
        service = VoteService()

        voters = [MockPlayer("Alice"), MockPlayer("Bob"), MockPlayer("Charlie")]
        candidates = voters

        def get_vote(player, candidates):
            # Alice and Bob vote for Charlie, Charlie abstains
            if player.name == "Charlie":
                return ("ABSTAIN", "I abstain")
            return ("Charlie", f"I vote {player.name}")

        result = service.conduct_vote(
            voters=voters, candidates=candidates, day=1, round_number=1, get_vote_func=get_vote
        )

        assert result.eliminated == "Charlie"
        assert result.vote_counts["Charlie"] == 2
        assert not result.tied

    def test_conduct_vote_tie(self):
        service = VoteService()

        voters = [MockPlayer("Alice"), MockPlayer("Bob")]
        candidates = voters

        def get_vote(player, candidates):
            # Each votes for the other
            if player.name == "Alice":
                return ("Bob", "Vote Bob")
            return ("Alice", "Vote Alice")

        result = service.conduct_vote(
            voters=voters, candidates=candidates, day=1, round_number=1, get_vote_func=get_vote
        )

        assert result.eliminated is None
        assert result.tied is True
        assert set(result.tied_players) == {"Alice", "Bob"}

    def test_get_voting_pattern(self):
        service = VoteService()

        voters = [MockPlayer("Alice"), MockPlayer("Bob")]
        candidates = voters

        def get_vote(player, candidates):
            return ("Bob", "Vote Bob")

        # Conduct multiple votes
        for day in range(1, 4):
            service.conduct_vote(
                voters=voters,
                candidates=candidates,
                day=day,
                round_number=1,
                get_vote_func=get_vote,
            )

        pattern = service.get_voting_pattern("Alice")
        assert pattern == ["Bob", "Bob", "Bob"]

    def test_analyze_voting_alignment(self):
        service = VoteService()

        voters = [MockPlayer("Alice"), MockPlayer("Bob"), MockPlayer("Charlie")]
        candidates = voters

        vote_choices = {
            1: {"Alice": "Charlie", "Bob": "Charlie"},  # Aligned
            2: {"Alice": "Bob", "Bob": "Alice"},  # Not aligned
            3: {"Alice": "Charlie", "Bob": "Charlie"},  # Aligned
        }

        def get_vote(player, candidates):
            day = len(service.history.results) + 1
            return (vote_choices[day].get(player.name, "ABSTAIN"), "vote")

        for day in range(1, 4):
            service.conduct_vote(
                voters=voters,
                candidates=candidates,
                day=day,
                round_number=1,
                get_vote_func=get_vote,
            )

        alignment = service.analyze_voting_alignment("Alice", "Bob")
        assert alignment == 2 / 3  # Aligned 2 out of 3 times


class TestEffectService:
    """Test EffectService."""

    def test_add_modifier(self):
        service = EffectService()

        states = {"Alice": PlayerState(name="Alice", role="Villager", team="Village")}

        effect = Effect(
            type="add_modifier",
            target="Alice",
            source="event:drunk",
            data={"modifier_type": "drunk", "applied_on": 1, "expires_on": 2},
        )

        new_states = service.apply(effect, states)

        assert new_states["Alice"].has_modifier("drunk")

    def test_remove_modifier(self):
        service = EffectService()

        states = {"Alice": PlayerState(name="Alice", role="Villager", team="Village")}
        states["Alice"].add_modifier(PlayerModifier(type="drunk", source="test"))

        effect = Effect(
            type="remove_modifier", target="Alice", source="game", data={"modifier_type": "drunk"}
        )

        new_states = service.apply(effect, states)

        assert not new_states["Alice"].has_modifier("drunk")

    def test_kill_player(self):
        service = EffectService()

        states = {"Alice": PlayerState(name="Alice", role="Villager", team="Village")}

        effect = Effect(
            type="kill_player",
            target="Alice",
            source="event:assassin",
            data={"cause": "assassination", "day": 1},
        )

        new_states = service.apply(effect, states)

        assert not new_states["Alice"].alive
        assert new_states["Alice"].has_modifier("dead")

    def test_change_role(self):
        service = EffectService()

        states = {"Alice": PlayerState(name="Alice", role="Villager", team="Village")}

        effect = Effect(
            type="change_role",
            target="Alice",
            source="event:shapeshifter",
            data={"new_role": "Assassin"},
        )

        new_states = service.apply(effect, states)

        assert new_states["Alice"].role == "Assassin"

    def test_apply_batch(self):
        service = EffectService()

        states = {"Alice": PlayerState(name="Alice", role="Villager", team="Village")}

        effects = [
            Effect(
                type="add_modifier",
                target="Alice",
                source="test",
                data={"modifier_type": "drunk", "applied_on": 1},
            ),
            Effect(type="change_role", target="Alice", source="test", data={"new_role": "Zombie"}),
        ]

        new_states = service.apply_batch(effects, states)

        assert new_states["Alice"].has_modifier("drunk")
        assert new_states["Alice"].role == "Zombie"

    def test_create_modifier_effect_factory(self):
        effect = EffectService.create_modifier_effect(
            target="Alice", modifier_type="drunk", source="event:drunk", expires_on=2, applied_on=1
        )

        assert effect.type == "add_modifier"
        assert effect.target == "Alice"
        assert effect.data["modifier_type"] == "drunk"

    def test_create_death_effect_factory(self):
        effect = EffectService.create_death_effect(
            target="Alice", source="assassin", cause="assassination", day=1
        )

        assert effect.type == "kill_player"
        assert effect.data["cause"] == "assassination"
