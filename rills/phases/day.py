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
            night_deaths: List of player names who died during the night
        """
        from ..formatting import h4

        print(f"\n### ☀️  Day {game.day_number}\n")

        alive_players = game.get_alive_players()

        if len(alive_players) <= 1:
            return

        # ==== REVELATIONS ====
        print(h4("Revelations"))
        self._display_game_summary(night_deaths)

        # ==== DISCUSSION ROUNDS ====
        print(h4("Discussion"))
        day_result = DayResult()
        day_result.discussion_rounds = self._conduct_discussion_rounds(
            game, alive_players, num_rounds=2
        )

        # ==== VOTING ====
        print(h4("Voting"))
        # _conduct_lynch_vote returns dict[str, str] for backwards compatibility
        vote_result = self._conduct_lynch_vote(game, alive_players)

        # ==== EVENTS ====
        print(h4("Events"))
        day_result.eliminated = self._process_lynch_result(game, vote_result)

        # ==== SUMMARY ====
        print(h4("Summary"))
        self._display_night_summary(game)

        game.check_win_condition()

    def _display_game_summary(self, night_deaths: list[str]) -> None:
        """Display revelations about who died during the night.

        Args:
            night_deaths: List of player names who died
        """
        if night_deaths:
            for name in night_deaths:
                print(f"{name} has been found dead.")
            print()
        else:
            print("No one died during the night.\n")

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

    def _conduct_discussion_rounds(
        self, game: GameState, alive_players: list[Player], num_rounds: int
    ) -> list:
        """Run discussion rounds and return the conversation rounds."""
        from ..formatting import h5

        discussion_rounds: list = []

        for round_num in range(1, num_rounds + 1):
            print(h5(f"Round {round_num}"))

            def get_statement_for_player(player, context, round_number):
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

            # Check for ties
            most_common = vote_counts.most_common()
            if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                print(h5("Lynch"))
                print("⚖️  The vote ended in a tie! No one was lynched.")
                print(
                    "ℹ️  When votes tie, no one is eliminated - the town must reach a clear majority.\n"
                )
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
        self, player: Player, game: GameState, round_num: int = 1
    ) -> tuple[str, str]:
        """Get a player's statement during discussion."""
        alive_names = [p.name for p in game.get_alive_players() if p != player]

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

        prompt = f"""It's daytime. Share your thoughts about who might be an Assassin.

Consider:
- Who has been acting suspiciously?
- What have people said during discussions?
- Who should the town vote to eliminate?

Other alive players: {", ".join(alive_names)}

{context_str}

Share your thoughts (1-2 sentences)."""

        system_context = game.context_builder.build_system_context(player, "day")

        return self.llm.get_player_statement(
            player=player, prompt=prompt, context=system_context, max_tokens=100
        )

    def _get_ghost_statement(
        self, ghost: Player, haunted_player: Player, game: GameState
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
            player=ghost, prompt=prompt, context=system_context, max_tokens=100
        )

    def _conduct_vote(self, game: GameState, alive_players: list[Player]) -> dict[str, str]:
        """Conduct voting to eliminate someone."""

        def get_vote_from_player(player, candidates):
            other_names = [p.name for p in candidates if p.name != player.name]

            if not other_names:
                return "ABSTAIN", ""

            choices = ["ABSTAIN"] + other_names

            prompt = game.context_builder.build_for_vote(
                player, candidates=other_names, discussion_summary="Based on the discussion..."
            )
            system_context = game.context_builder.build_system_context(player, "day")

            guidance = """\nConsider:
- Who seems most suspicious?
- Who might be an Assassin?
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
