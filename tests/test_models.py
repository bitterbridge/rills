"""Tests for data models."""

from datetime import datetime

from rills.models import (
    ConversationHistory,
    ConversationRound,
    InfoCategory,
    Information,
    InformationStore,
    KnowledgeState,
    PlayerModifier,
    PlayerState,
    Statement,
    Visibility,
    Vote,
    VoteResult,
)


class TestVisibility:
    """Test Visibility model."""

    def test_public_visibility(self):
        vis = Visibility("public", [])
        assert vis.is_visible_to("Alice") is True
        assert vis.is_visible_to("Bob") is True

    def test_private_visibility(self):
        vis = Visibility("private", ["Alice", "Bob"])
        assert vis.is_visible_to("Alice") is True
        assert vis.is_visible_to("Bob") is True
        assert vis.is_visible_to("Charlie") is False

    def test_team_visibility(self):
        vis = Visibility("team", ["Assassins"])
        assert vis.is_visible_to("Alice", player_team="Assassins") is True
        assert vis.is_visible_to("Bob", player_team="Village") is False

    def test_role_visibility(self):
        vis = Visibility("role", ["Vigilante"])
        assert vis.is_visible_to("Alice", player_role="Vigilante") is True
        assert vis.is_visible_to("Bob", player_role="Villager") is False


class TestInformation:
    """Test Information model."""

    def test_create_information(self):
        info = Information.create(
            content="Alice died. They were a Villager.",
            source="game",
            category=InfoCategory.DEATH,
            visibility=Visibility("public", []),
            day_number=1,
        )

        assert info.content == "Alice died. They were a Villager."
        assert info.source == "game"
        assert info.category == InfoCategory.DEATH
        assert info.day_number == 1
        assert info.id is not None
        assert isinstance(info.timestamp, datetime)


class TestInformationStore:
    """Test InformationStore."""

    def test_add_and_get(self):
        store = InformationStore()
        info = Information.create(
            content="Test info",
            source="game",
            category=InfoCategory.GAME_STATE,
            visibility=Visibility("public", []),
        )

        info_id = store.add(info)
        retrieved = store.get(info_id)

        assert retrieved is not None
        assert retrieved.content == "Test info"

    def test_get_visible_to(self):
        store = InformationStore()

        # Public info
        pub_info = Information.create(
            content="Public announcement",
            source="game",
            category=InfoCategory.GAME_STATE,
            visibility=Visibility("public", []),
        )
        store.add(pub_info)

        # Private info for Alice
        priv_info = Information.create(
            content="Secret for Alice",
            source="game",
            category=InfoCategory.ACTION,
            visibility=Visibility("private", ["Alice"]),
        )
        store.add(priv_info)

        # Alice sees both
        alice_visible = store.get_visible_to("Alice")
        assert len(alice_visible) == 2

        # Bob only sees public
        bob_visible = store.get_visible_to("Bob")
        assert len(bob_visible) == 1
        assert bob_visible[0].content == "Public announcement"

    def test_query_by_category(self):
        store = InformationStore()

        death_info = Information.create(
            content="Death occurred",
            source="game",
            category=InfoCategory.DEATH,
            visibility=Visibility("public", []),
        )
        store.add(death_info)

        vote_info = Information.create(
            content="Vote occurred",
            source="game",
            category=InfoCategory.VOTE,
            visibility=Visibility("public", []),
        )
        store.add(vote_info)

        deaths = store.query(category=InfoCategory.DEATH)
        assert len(deaths) == 1
        assert deaths[0].content == "Death occurred"

    def test_query_by_day(self):
        store = InformationStore()

        day1_info = Information.create(
            content="Day 1 event",
            source="game",
            category=InfoCategory.GAME_STATE,
            visibility=Visibility("public", []),
            day_number=1,
        )
        store.add(day1_info)

        day2_info = Information.create(
            content="Day 2 event",
            source="game",
            category=InfoCategory.GAME_STATE,
            visibility=Visibility("public", []),
            day_number=2,
        )
        store.add(day2_info)

        day1_results = store.query(day_number=1)
        assert len(day1_results) == 1
        assert day1_results[0].content == "Day 1 event"


class TestPlayerModifier:
    """Test PlayerModifier model."""

    def test_create_modifier(self):
        mod = PlayerModifier(type="zombie", source="event:zombie", applied_on=1, expires_on=None)

        assert mod.type == "zombie"
        assert mod.active is True
        assert mod.is_expired(5) is False

    def test_expiration(self):
        mod = PlayerModifier(type="drunk", source="event:drunk", applied_on=1, expires_on=2)

        assert mod.is_expired(1) is False
        assert mod.is_expired(2) is False
        assert mod.is_expired(3) is True

    def test_deactivate(self):
        mod = PlayerModifier(type="test", source="test")
        assert mod.active is True

        mod.deactivate()
        assert mod.active is False


class TestPlayerState:
    """Test PlayerState model."""

    def test_create_player_state(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        assert state.name == "Alice"
        assert state.alive is True
        assert len(state.modifiers) == 0

    def test_add_and_check_modifier(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        modifier = PlayerModifier(type="drunk", source="event:drunk")
        state.add_modifier(modifier)

        assert state.has_modifier("drunk") is True
        assert state.has_modifier("zombie") is False

    def test_get_modifier(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        modifier = PlayerModifier(type="drunk", source="event:drunk", data={"rounds": 2})
        state.add_modifier(modifier)

        retrieved = state.get_modifier("drunk")
        assert retrieved is not None
        assert retrieved.data["rounds"] == 2

    def test_remove_modifier(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        modifier = PlayerModifier(type="drunk", source="event:drunk")
        state.add_modifier(modifier)

        assert state.has_modifier("drunk") is True
        state.remove_modifier("drunk")
        assert state.has_modifier("drunk") is False

    def test_update_modifiers_expiration(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        modifier = PlayerModifier(type="drunk", source="event:drunk", applied_on=1, expires_on=2)
        state.add_modifier(modifier)

        state.update_modifiers(current_day=1)
        assert state.has_modifier("drunk") is True

        state.update_modifiers(current_day=3)
        assert state.has_modifier("drunk") is False

    def test_get_display_role_infected(self):
        state = PlayerState(name="Alice", role="Villager", team="Village")

        # Normal villager
        assert state.get_display_role() == "Villager"

        # Infected but alive
        state.add_modifier(PlayerModifier(type="infected", source="event:zombie"))
        assert state.get_display_role() == "Villager (Infected)"

        # Infected and dead becomes Zombie
        state.alive = False
        assert state.get_display_role() == "Zombie"


class TestKnowledgeState:
    """Test KnowledgeState model."""

    def test_add_information(self):
        knowledge = KnowledgeState(player_name="Alice")

        knowledge.add_information("info-123")
        assert knowledge.knows_about("info-123") is True
        assert knowledge.knows_about("info-456") is False

    def test_add_multiple(self):
        knowledge = KnowledgeState(player_name="Alice")

        knowledge.add_multiple(["info-1", "info-2", "info-3"])
        assert len(knowledge.information_ids) == 3

    def test_get_knowledge_summary(self):
        store = InformationStore()
        knowledge = KnowledgeState(player_name="Alice")

        # Add some information
        info1 = Information.create(
            content="Bob died",
            source="game",
            category=InfoCategory.DEATH,
            visibility=Visibility("public", []),
        )
        id1 = store.add(info1)
        knowledge.add_information(id1)

        summary = knowledge.get_knowledge_summary(store)
        assert "Bob died" in summary


class TestStatement:
    """Test Statement model."""

    def test_create_statement(self):
        stmt = Statement.create(
            speaker="Alice",
            content="I think Bob is suspicious",
            thinking="Bob voted for me yesterday",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )

        assert stmt.speaker == "Alice"
        assert stmt.content == "I think Bob is suspicious"
        assert stmt.id is not None


class TestConversationRound:
    """Test ConversationRound model."""

    def test_add_statement(self):
        round_obj = ConversationRound(round_number=1, phase="day_discussion", day_number=1)

        stmt = Statement.create(
            speaker="Alice",
            content="Test",
            thinking="Test thinking",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )

        round_obj.add_statement(stmt)
        assert len(round_obj.statements) == 1

    def test_get_context_for(self):
        round_obj = ConversationRound(round_number=1, phase="day_discussion")

        stmt1 = Statement.create(
            speaker="Alice",
            content="Alice statement",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )
        stmt2 = Statement.create(
            speaker="Bob",
            content="Bob statement",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )

        round_obj.add_statement(stmt1)
        round_obj.add_statement(stmt2)

        # Charlie sees both Alice and Bob
        context = round_obj.get_context_for("Charlie")
        assert "Alice statement" in context
        assert "Bob statement" in context

        # Alice doesn't see her own statement
        alice_context = round_obj.get_context_for("Alice")
        assert "Alice statement" not in alice_context
        assert "Bob statement" in alice_context


class TestConversationHistory:
    """Test ConversationHistory model."""

    def test_add_round(self):
        history = ConversationHistory()
        round_obj = ConversationRound(round_number=1, phase="day_discussion", day_number=1)

        history.add_round(round_obj)
        assert len(history.rounds) == 1

    def test_get_statements_by(self):
        history = ConversationHistory()
        round_obj = ConversationRound(round_number=1, phase="day_discussion")

        stmt1 = Statement.create(
            speaker="Alice",
            content="Alice 1",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )
        stmt2 = Statement.create(
            speaker="Bob",
            content="Bob 1",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )
        stmt3 = Statement.create(
            speaker="Alice",
            content="Alice 2",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )

        round_obj.add_statement(stmt1)
        round_obj.add_statement(stmt2)
        round_obj.add_statement(stmt3)
        history.add_round(round_obj)

        alice_stmts = history.get_statements_by("Alice")
        assert len(alice_stmts) == 2
        assert all(s.speaker == "Alice" for s in alice_stmts)

    def test_search_content(self):
        history = ConversationHistory()
        round_obj = ConversationRound(round_number=1, phase="day_discussion")

        stmt1 = Statement.create(
            speaker="Alice",
            content="I suspect Bob",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )
        stmt2 = Statement.create(
            speaker="Charlie",
            content="I agree about Bob",
            thinking="",
            round_number=1,
            phase="day_discussion",
            visibility=Visibility("public", []),
        )

        round_obj.add_statement(stmt1)
        round_obj.add_statement(stmt2)
        history.add_round(round_obj)

        results = history.search_content("Bob")
        assert len(results) == 2


class TestVote:
    """Test Vote model."""

    def test_create_vote(self):
        vote = Vote(voter="Alice", target="Bob", round_number=1, day_number=1)

        assert vote.voter == "Alice"
        assert vote.target == "Bob"
        assert vote.is_abstain() is False

    def test_abstain_vote(self):
        vote = Vote(voter="Alice", target="ABSTAIN", round_number=1, day_number=1)

        assert vote.is_abstain() is True

    def test_redirected_vote(self):
        vote = Vote(
            voter="Alice",
            target="Charlie",
            round_number=1,
            day_number=1,
            original_target="Bob",
        )

        assert vote.was_redirected() is True


class TestVoteResult:
    """Test VoteResult model."""

    def test_clear_winner(self):
        votes = [
            Vote(voter="Alice", target="Bob", round_number=1, day_number=1),
            Vote(voter="Charlie", target="Bob", round_number=1, day_number=1),
            Vote(voter="Dave", target="Eve", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)

        assert result.eliminated == "Bob"
        assert result.tied is False
        assert result.vote_counts["Bob"] == 2
        assert result.vote_counts["Eve"] == 1

    def test_tie(self):
        votes = [
            Vote(voter="Alice", target="Bob", round_number=1, day_number=1),
            Vote(voter="Charlie", target="Dave", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)

        assert result.eliminated is None
        assert result.tied is True
        assert set(result.tied_players) == {"Bob", "Dave"}

    def test_all_abstain(self):
        votes = [
            Vote(voter="Alice", target="ABSTAIN", round_number=1, day_number=1),
            Vote(voter="Bob", target="ABSTAIN", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)

        assert result.eliminated is None
        assert result.tied is False

    def test_get_votes_for(self):
        votes = [
            Vote(voter="Alice", target="Bob", round_number=1, day_number=1),
            Vote(voter="Charlie", target="Bob", round_number=1, day_number=1),
            Vote(voter="Dave", target="Eve", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)

        bob_votes = result.get_votes_for("Bob")
        assert len(bob_votes) == 2
        assert all(v.target == "Bob" for v in bob_votes)

    def test_get_voters_for(self):
        votes = [
            Vote(voter="Alice", target="Bob", round_number=1, day_number=1),
            Vote(voter="Charlie", target="Bob", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)

        voters = result.get_voters_for("Bob")
        assert set(voters) == {"Alice", "Charlie"}

    def test_format_breakdown(self):
        votes = [
            Vote(voter="Alice", target="Bob", round_number=1, day_number=1),
            Vote(voter="Charlie", target="Bob", round_number=1, day_number=1),
            Vote(voter="Dave", target="ABSTAIN", round_number=1, day_number=1),
        ]

        result = VoteResult(day_number=1, round_number=1, votes=votes)
        breakdown = result.format_breakdown()

        assert "Bob: 2 vote(s)" in breakdown
        assert "Alice, Charlie" in breakdown
        assert "Abstained: Dave" in breakdown
        assert "Bob is eliminated" in breakdown
