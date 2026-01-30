"""Day phase logic - discussions and voting."""

from collections import Counter
from typing import TYPE_CHECKING

from ..game import GameState
from ..models.actions import DayResult
from ..player import Player

if TYPE_CHECKING:
    from ..llm import LLMAgent


class DayPhaseHandler:
    """Handles all day phase logic."""

    def __init__(self, llm_agent: "LLMAgent"):
        """Initialize the day phase handler."""
        self.llm = llm_agent

    def run_day_phase(self, game: GameState, night_deaths: list[str]) -> None:
        """Execute the day phase where players discuss and vote.

        Args:
        ----
            night_deaths: List of player names who died during the night

        """
        from ..formatting import h4

        print(f"\n### ☀️  Day {game.day_number}\n")

        alive_players = game.get_alive_players()

        if len(alive_players) <= 1:
            return

        # ==== REVELATIONS ====
        print(h4("Revelations"))
        self._display_game_summary(game, night_deaths)

        # ==== DISCUSSION ROUNDS ====
        print(h4("Discussion"))
        day_result = DayResult()
        day_result.discussion_rounds = self._conduct_discussion_rounds(
            game,
            alive_players,
            num_rounds=2,
        )

        # ==== VOTING ====
        print(h4("Voting"))
        # _conduct_lynch_vote returns dict[str, str] for backwards compatibility
        vote_result = self._conduct_lynch_vote(game, alive_players)

        # ==== EVENTS ====
        print(h4("Events"))
        day_result.eliminated = self._process_lynch_result(game, vote_result)

        # ==== UPDATE NOTES ====
        # Allow players to update their strategic notes after observing the day's events
        self._update_player_notes(game, alive_players, day_result)

        # ==== SUMMARY ====
        print(h4("Summary"))
        self._display_night_summary(game)

        game.check_win_condition()

    def _display_game_summary(self, game: GameState, night_deaths: list[str]) -> None:
        """Display revelations about who died during the night.

        Args:
        ----
            game: Current game state
            night_deaths: List of player names who died

        """
        # Display game progress
        alive_players = game.get_alive_players()
        alive_count = len(alive_players)
        print(f"📊 Day {game.day_number} | {alive_count} players remaining\n")

        # Display town blackboard if there are messages
        if game.blackboard_messages:
            print("📋 Town Blackboard (anonymous messages):")
            for msg in game.blackboard_messages[-5:]:  # Show last 5 messages
                print(f"  📝 {msg['content']}")
            print()

        # Display structured recent history
        if game.day_number > 1:
            print("📜 Recent Events Summary:")
            # Get eliminated players in reverse order (most recent first)
            dead_players = [p for p in game.players if not p.alive]
            recent_deaths = dead_players[-4:] if len(dead_players) > 4 else dead_players

            if recent_deaths:
                for dead in reversed(recent_deaths):
                    elimination_reason = "unknown"
                    # Try to determine how they died from game events
                    if any(
                        "lynched" in str(e).lower() or "voted" in str(e).lower()
                        for e in game.events
                    ):
                        if dead.role.value in ["Assassins"]:
                            elimination_reason = "eliminated by village vote"
                        else:
                            elimination_reason = "eliminated by village vote"
                    elif any("assassin" in str(e).lower() for e in game.events):
                        elimination_reason = "killed during the night"
                    print(f"  • {dead.name} ({dead.role.display_name()}) - {elimination_reason}")
                print()

        # Display deaths
        if night_deaths:
            print("☠️  Night Deaths:")
            for name in night_deaths:
                print(f"  • {name} has been found dead.")
            print()
        else:
            print("✅ No one died during the night.\n")

        # Display action feedback for each player
        has_feedback = False
        for player in alive_players:
            if player.action_feedback:
                print(f"📢 {player.name}: {player.action_feedback}")
                has_feedback = True
                # Clear the feedback after displaying it
                player.action_feedback = None

        if has_feedback:
            print()

        # Display truth serum effects
        truth_serum_victims = [p for p in alive_players if p.has_modifier(game, "truth_serum")]
        if truth_serum_victims:
            for victim in truth_serum_victims:
                print(
                    f"🧪 {victim.name} is under the effect of the TRUTH SERUM! They must reveal their true role during discussion.",
                )
            print()

        # Display strategic guidance

        print("ℹ️  Strategic Information:")
        print(
            f"  • Started with: {len([p for p in game.players if p.team == 'village'])} villagers, {len([p for p in game.players if p.team == 'assassins'])} assassins",
        )
        print(f"  • Currently alive: {alive_count} players total")
        print("  • Remember: Eliminating quiet players without evidence is often a mistake!")
        print("  • Look for: Voting patterns, defensive behavior, claims that contradict events")
        print()

    def _display_night_summary(self, game: GameState) -> None:
        """Display summary of alive players and their roles/statuses."""
        alive_players = game.get_alive_players()

        print(f"Alive Players ({len(alive_players)}):")
        for player in alive_players:
            role_info = [player.role.value]
            if player.has_modifier(game, "suicidal"):
                role_info.append("Suicidal")
            if player.has_modifier(game, "insomniac"):
                role_info.append("Insomniac")
            if player.has_modifier(game, "sleepwalker"):
                role_info.append("Sleepwalker")
            if player.has_modifier(game, "priest") and player.resurrection_available:
                role_info.append("Priest")
            if player.has_modifier(game, "lover"):
                role_info.append("Lover")
            if player.has_modifier(game, "bodyguard") and player.bodyguard_active:
                role_info.append("Bodyguard")
            if player.has_modifier(game, "infected"):
                role_info.append("Infected")
            if player.has_modifier(game, "pending_zombification"):
                role_info.append("Becoming Infected")

            role_str = " + ".join(role_info)
            print(f"  • {player.name} ({role_str})")
        print()

    def _update_player_notes(
        self,
        game: GameState,
        alive_players: list[Player],
        day_result,
    ) -> None:
        """Allow players to update their strategic notes after the day's events."""
        for player in alive_players:
            # Build context about what happened today
            discussion_summary = ""
            if day_result.discussion_rounds:
                recent_round = day_result.discussion_rounds[-1]
                statements = [f"- {s.speaker}: {s.content}" for s in recent_round.statements[-5:]]
                discussion_summary = "\n".join(statements)

            eliminated_info = ""
            if day_result.eliminated:
                eliminated_info = f"\n{day_result.eliminated.name} ({day_result.eliminated.role.display_name()}) was eliminated."

            prompt = f"""Update your strategic notes based on today's events.

Today's discussion highlights:
{discussion_summary}
{eliminated_info}

Your current notes:
{player.notes if player.notes else "(No notes yet)"}

Update your notes to track:
- Suspicious behavior or voting patterns you noticed
- Role claims (who claimed what, does it match events?)
- Predictions (who might be Assassin, who to trust)
- Contradictions or defensive behavior
- Plans for tomorrow (who to investigate, protect, or vote for)

Keep notes concise but useful for future reference. Write updated notes (or "KEEP" to keep current notes unchanged):"""

            system_context = game.context_builder.build_system_context(player, "day")

            # Get updated notes from player
            try:
                response = self.llm.client.messages.create(
                    model=self.llm.model,
                    max_tokens=200,
                    temperature=0.7,
                    system=system_context,
                    messages=[{"role": "user", "content": prompt}],
                )

                # Extract text from response, handling different content types
                content = response.content[0]
                new_notes = content.text if hasattr(content, "text") else ""
                new_notes = new_notes.strip()

                # Update notes if they provided new ones
                if new_notes and new_notes.upper() != "KEEP":
                    player.notes = new_notes

            except Exception:
                # If note-taking fails, just skip it - not critical
                print(f"  (Note update skipped for {player.name})")

    def _conduct_discussion_rounds(
        self,
        game: GameState,
        alive_players: list[Player],
        num_rounds: int,
    ) -> list:
        """Run discussion rounds and return the conversation rounds."""
        from ..formatting import h5

        discussion_rounds: list = []

        for round_num in range(1, num_rounds + 1):
            print(h5(f"Round {round_num}"))

            def get_statement_for_player(player, _context, round_number):
                return self._get_discussion_statement(player, game, round_number)

            round_obj = game.conversation_service.conduct_round(
                participants=alive_players,
                phase="day_discussion",
                round_number=round_num,
                day_number=game.day_number,
                get_statement_func=get_statement_for_player,
            )

            discussion_rounds.append(round_obj)

            # Display statements
            for stmt in round_obj.statements:
                print(f"  💭 {stmt.speaker} thinks: {stmt.thinking}")
                print(f"💬 {stmt.speaker}: {stmt.content}\n")

                # Check for ghost haunting
                player = next(p for p in alive_players if p.name == stmt.speaker)
                ghosts = [
                    p
                    for p in game.players
                    if (p.is_ghost or p.has_modifier(game, "ghost"))
                    and p.haunting_target == player.name
                ]
                for ghost in ghosts:
                    ghost_thinking, ghost_statement = self._get_ghost_statement(ghost, player, game)
                    print(f"  💭 {ghost.name}'s ghost thinks: {ghost_thinking}")
                    print(f"👻 {ghost.name}'s ghost: {ghost_statement}\n")

        return discussion_rounds

    def _conduct_lynch_vote(self, game: GameState, alive_players: list[Player]):
        """Conduct voting phase and return vote result."""
        from ..formatting import h5

        print(h5("Votes"))
        print("📋 VOTING PROCESS:")
        print("   • Each player votes for ONE person to eliminate (or can ABSTAIN)")
        print("   • The player with the MOST votes is eliminated")
        print("   • In case of a TIE, NO ONE is eliminated")
        print("   • Think carefully - vote based on EVIDENCE, not suspicion alone\n")
        votes = self._conduct_vote(game, alive_players)

        if not votes:
            return None

        return votes

    def _process_lynch_result(self, game: GameState, vote_result) -> Player | None:
        """Process the lynch vote result and eliminate player if needed."""
        from ..formatting import h5

        if not vote_result:
            return None

        # Filter out abstentions
        actual_votes = {
            k: v for k, v in vote_result.items() if v != "ABSTAIN (don't vote for anyone)"
        }
        abstain_count = len(vote_result) - len(actual_votes)

        vote_counts = Counter(actual_votes.values())
        if vote_counts:
            # Show detailed vote breakdown
            print(h5("Breakdown"))
            for voter, target in sorted(actual_votes.items()):
                print(f"  {voter} → {target}")
            if abstain_count > 0:
                abstainers = [
                    k for k, v in vote_result.items() if v == "ABSTAIN (don't vote for anyone)"
                ]
                print(f"  Abstained: {', '.join(abstainers)}")

            print()
            print(h5("Totals"))
            for name, count in vote_counts.most_common():
                print(f"  {name}: {count} votes")
            if abstain_count > 0:
                print(f"  Abstentions: {abstain_count}")

            print()

            # Check for ties with explicit tie-breaking rules
            most_common = vote_counts.most_common()
            if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                print(h5("Lynch"))
                tied_players = [name for name, count in most_common if count == most_common[0][1]]
                print(f"⚖️  TIE: {', '.join(tied_players)} all received {most_common[0][1]} votes")
                print("\n🔔 TIE-BREAKING RULE: When there's a tie, NO ONE is eliminated.")
                print("   The village must reach consensus or risk another night.")
                print("   Ties protect the uncertain but allow Assassins to strike again.\n")
                return None
            else:
                eliminated_name, vote_count = most_common[0]
                eliminated = game.get_player_by_name(eliminated_name)
                if eliminated:
                    print(h5("Lynch"))
                    print(f"⚖️  {eliminated.name} was lynched by the town!")
                    print(f"💀 {eliminated.name} was a {eliminated.role.value}!\n")
                    game.eliminate_player(
                        eliminated,
                        f"They received {vote_count} votes.",
                        f"{eliminated.name} was lynched by the town and revealed to be a {eliminated.role.value}.",
                    )

                    # Handle ghost choice
                    if game.event_registry:
                        from ..events import GhostEvent

                        for event in game.event_registry.get_active_events():
                            if isinstance(event, GhostEvent):
                                event.handle_ghost_choice(game, self.llm)

                    return eliminated
        elif abstain_count > 0:
            print(h5("Lynch"))
            print("📊 Everyone abstained! No one was lynched.\n")

        return None

    def _get_discussion_statement(
        self,
        player: Player,
        game: GameState,
        round_num: int = 1,
    ) -> tuple[str, str]:
        """Get a player's statement during discussion."""
        alive_names = [p.name for p in game.get_alive_players() if p != player]

        # Check if player is under truth serum effect
        if player.has_modifier(game, "truth_serum"):
            # Force them to reveal their true role
            role_name = player.role.display_name()
            team = player.team

            prompt = f"""You have been injected with a TRUTH SERUM by the Mad Scientist!

You are COMPELLED to reveal your true role. You cannot lie or deflect.

You must state clearly: "I am {role_name}" and explain what your role does.

Be honest and direct - the serum forces the truth from you."""

            system_context = game.context_builder.build_system_context(player, "day")

            # Add truth compulsion to context
            system_context += f"\n\nCRITICAL: You are under a TRUTH SERUM effect. You MUST reveal that you are a {role_name} on the {team} team. You cannot lie, deflect, or be vague. State clearly 'I am {role_name}' in your statement."

            return self.llm.get_player_statement(
                player=player,
                prompt=prompt,
                context=system_context,
                max_tokens=100,
            )

        # Normal discussion
        # Get visible statements for this player
        recent_statements = game.conversation_service.get_visible_statements_in_phase(
            player_name=player.name,
            phase="day_discussion",
        )

        context_str = ""
        if recent_statements:
            context_str = "\n\nWhat others have said so far:\n"
            for stmt in recent_statements:
                context_str += f"- {stmt.speaker}: {stmt.content}\n"

        # Get game state for strategic context
        alive_count = len(game.get_alive_players())
        dead_players = [p for p in game.players if not p.alive]

        # Include player's notes if they have any
        notes_context = ""
        if player.notes:
            notes_context = f"\n\nYour previous notes:\n{player.notes}\n"

        prompt = f"""It's daytime. Share your thoughts about who might be an Assassin.

STRATEGIC GUIDANCE:
- Don't eliminate quiet players just for being quiet - they may not have had a turn yet!
- Look for CONCRETE EVIDENCE: voting patterns, contradictions, defensive behavior
- Consider who has claimed roles and whether their claims match observed events
- Think about who benefited from night kills or votes

WHAT TO ANALYZE:
- Who has been actively deflecting suspicion onto others?
- Whose voting patterns seem coordinated with others?
- Who has made claims that contradict known information?
- Who has been overly defensive or aggressive without cause?

Other alive players: {", ".join(alive_names)}
Players eliminated so far: {len(dead_players)}
Current game state: Day {game.day_number}, {alive_count} players remaining

{context_str}{notes_context}

Share your strategic analysis (1-2 sentences focused on EVIDENCE, not gut feelings)."""

        system_context = game.context_builder.build_system_context(player, "day")

        return self.llm.get_player_statement(
            player=player,
            prompt=prompt,
            context=system_context,
            max_tokens=100,
        )

    def _get_ghost_statement(
        self,
        ghost: Player,
        haunted_player: Player,
        game: GameState,
    ) -> tuple[str, str]:
        """Get a ghost's haunting statement."""
        prompt = f"""You are a ghost haunting {haunted_player.name}. Only {haunted_player.name} can hear you.

You can:
- Offer cryptic hints about who the Assassins might be
- Reference your own death
- Try to guide {haunted_player.name} to help your former team

What do you whisper to {haunted_player.name}? (1 sentence, be eerie and cryptic)"""

        system_context = game.context_builder.build_system_context(ghost, "day")

        return self.llm.get_player_statement(
            player=ghost,
            prompt=prompt,
            context=system_context,
            max_tokens=100,
        )

    def _conduct_vote(self, game: GameState, alive_players: list[Player]) -> dict[str, str]:
        """Conduct voting to eliminate someone."""

        def get_vote_from_player(player, candidates):
            other_names = [p.name for p in candidates if p.name != player.name]

            if not other_names:
                return "ABSTAIN", ""

            choices = ["ABSTAIN"] + other_names

            prompt = game.context_builder.build_for_vote(
                player,
                candidates=other_names,
                discussion_summary="Based on the discussion...",
            )
            system_context = game.context_builder.build_system_context(player, "day")

            # Include player's notes in voting context
            notes_reminder = ""
            if player.notes:
                notes_reminder = f"\n\nYour notes:\n{player.notes}\n"

            guidance = f"""{notes_reminder}
Consider:
- Who seems most suspicious based on EVIDENCE?
- Who might be an Assassin based on your observations?
- What strategy helps your team win?
- You can choose to ABSTAIN if you're uncertain

Choose carefully."""

            choice = self.llm.get_player_choice(
                player=player,
                prompt=f"{prompt}\n{guidance}",
                valid_choices=choices,
                context=system_context,
            )

            # Normalize ABSTAIN choice
            if choice == "ABSTAIN (don't vote for anyone)":
                choice = "ABSTAIN"

            return choice, ""

        # Conduct vote through service
        result = game.vote_service.conduct_vote(
            voters=alive_players,
            candidates=alive_players,
            day=game.day_number,
            round_number=1,
            get_vote_func=get_vote_from_player,
        )

        # Display votes
        for vote in result.votes:
            if vote.is_abstain():
                print(f"  {vote.voter} abstains")
            else:
                print(f"  {vote.voter} votes for {vote.target}")

        # Return votes in old format for backwards compatibility
        votes = {
            v.voter: v.target if not v.is_abstain() else "ABSTAIN (don't vote for anyone)"
            for v in result.votes
        }

        return votes
