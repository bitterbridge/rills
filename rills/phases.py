"""Game phases - night actions and day discussions."""

from collections import Counter
from typing import Optional

from .game import GameState
from .player import Player
from .llm import LLMAgent
from .roles import Role


class PhaseManager:
    """Manages the different phases of the game."""

    def __init__(self, llm_agent: LLMAgent):
        """Initialize the phase manager."""
        self.llm = llm_agent

    def run_night_phase(self, game: GameState) -> None:
        """Execute the night phase where special roles take actions."""
        print(f"\n{'='*60}")
        print(f"🌙 {game.get_phase_description()}")
        print(f"{'='*60}\n")

        # Notify events of night start (marks pending zombies, handles sleepwalker, insomniac)
        if game.event_registry:
            game.event_registry.on_night_start(game)

            # Handle zombie attacks with LLM deliberation
            from .events import ZombieEvent
            for event in game.event_registry.get_active_events():
                if isinstance(event, ZombieEvent):
                    event.handle_zombie_attacks(game, self.llm)

        # Reset protection status
        for player in game.get_alive_players():
            player.protected = False
            player.insomniac_sighting = None  # Reset insomniac sightings

        assassins_target: Optional[Player] = None
        doctor_target: Optional[Player] = None
        detective_target: Optional[Player] = None
        vigilante_target: Optional[Player] = None

        # Assassins choose victim
        assassins_target = self._assassins_action(game)

        # Doctor chooses who to protect
        doctor_target = self._doctor_action(game)

        # Detective investigates
        detective_result = self._detective_action(game)

        # Vigilante chooses target
        vigilante_target = self._vigilante_action(game)

        # Resolve night actions
        print("\n--- Night Resolution ---")

        if assassins_target:
            # Gun Nut mechanic: check event for counter attack
            counter_killed = None
            if game.event_registry:
                from .events import GunNutEvent
                for event in game.event_registry.get_active_events():
                    if isinstance(event, GunNutEvent):
                        counter_killed = event.check_counter_attack(game, assassins_target)
                        break

            if counter_killed:
                print(f"💥 {assassins_target.name} fought back! {counter_killed.name} was killed instead!")
                game.eliminate_player(
                    counter_killed,
                    f"{assassins_target.name} (Gun Nut) killed them in self-defense.",
                    f"{counter_killed.name} was found dead."
                )
                for player in game.get_alive_players():
                    player.add_memory(f"There was a struggle at night. {counter_killed.name} died.")
            elif doctor_target and doctor_target == assassins_target:
                print(f"💊 The Doctor saved {assassins_target.name}!")
                game.events.append(f"Someone was attacked but saved by the Doctor.")
                for player in game.get_alive_players():
                    player.add_memory("Someone was attacked but saved by the Doctor last night.")
            else:
                print(f"☠️  {assassins_target.name} was eliminated by the Assassins!")
                game.eliminate_player(
                    assassins_target,
                    "They were killed by the Assassins.",
                    f"{assassins_target.name} was found dead."
                )

        if vigilante_target:
            if doctor_target and doctor_target == vigilante_target:
                print(f"💊 The Doctor saved {vigilante_target.name} from the Vigilante!")
                game.events.append(f"The Vigilante tried to kill someone but they were saved.")
                for player in game.get_alive_players():
                    player.add_memory("Someone was attacked at night (possibly by Vigilante) but saved.")
            else:
                print(f"⚔️  {vigilante_target.name} was eliminated by the Vigilante!")
                game.eliminate_player(
                    vigilante_target,
                    "They were killed by the Vigilante.",
                    f"{vigilante_target.name} was found dead."
                )

        if detective_result:
            print(f"🔍 {detective_result}")

        # Notify events of night end (handles suicide, insomniac reveals)
        if game.event_registry:
            game.event_registry.on_night_end(game)

            # Handle ghost choices (needs LLM access)
            from .events import GhostEvent
            for event in game.event_registry.get_active_events():
                if isinstance(event, GhostEvent):
                    event.handle_ghost_choice(game, self.llm)

        game.check_win_condition()

    def run_day_phase(self, game: GameState) -> None:
        """Execute the day phase where players discuss and vote."""
        print(f"\n{'='*60}")
        print(f"☀️  {game.get_phase_description()}")
        print(f"{'='*60}\n")

        alive_players = game.get_alive_players()

        if len(alive_players) <= 1:
            return

        # Discussion phase
        print("--- Discussion Phase ---\n")
        for player in alive_players:
            thinking, statement = self._get_discussion_statement(player, game)
            print(f"  💭 {player.name} thinks: {thinking}")
            print(f"💬 {player.name}: {statement}\n")

            # All other players remember this (not the thinking)
            for other in alive_players:
                if other != player:
                    other.add_memory(f"{player.name} said: {statement}")

            # Check if any ghost is haunting this player
            for ghost in [p for p in game.players if p.is_ghost and p.haunting_target == player.name]:
                ghost_thinking, ghost_statement = self._get_ghost_statement(ghost, player, game)
                print(f"  💭 {ghost.name}'s ghost thinks: {ghost_thinking}")
                print(f"👻 {ghost.name}'s ghost: {ghost_statement}\n")
                # Other players remember the ghost's outburst (not the thinking)
                for other in alive_players:
                    other.add_memory(f"A ghostly voice (claiming to be {ghost.name}) yelled: {ghost_statement}")

        # Voting phase
        print("\n--- Voting Phase ---\n")
        votes = self._conduct_vote(game, alive_players)

        # Determine who gets eliminated
        if votes:
            vote_counts = Counter(votes.values())
            if vote_counts:
                print(f"\n📊 Vote Results:")
                for name, count in vote_counts.most_common():
                    print(f"  {name}: {count} votes")

                # Check for ties
                most_common = vote_counts.most_common()
                if len(most_common) > 1 and most_common[0][1] == most_common[1][1]:
                    print(f"\n⚖️  The vote ended in a tie! No one was lynched.")
                    for player in alive_players:
                        player.add_memory(f"Day {game.day_number}: The town couldn't agree on who to eliminate - the vote was tied.")
                else:
                    eliminated_name, vote_count = most_common[0]
                    eliminated = game.get_player_by_name(eliminated_name)
                    if eliminated:
                        print(f"\n⚖️  {eliminated.name} was lynched by the town!")
                        game.eliminate_player(
                            eliminated,
                            f"They received {vote_count} votes.",
                            f"{eliminated.name} was lynched by the town."
                        )

                        # Handle ghost choice if they became a ghost
                        if game.event_registry:
                            from .events import GhostEvent
                            for event in game.event_registry.get_active_events():
                                if isinstance(event, GhostEvent):
                                    event.handle_ghost_choice(game, self.llm)

        game.check_win_condition()

    def _assassins_action(self, game: GameState) -> Optional[Player]:
        """Assassins choose who to eliminate."""
        assassins_members = [p for p in game.get_alive_players() if p.role == Role.ASSASSINS]

        if not assassins_members:
            return None

        non_assassins = [p for p in game.get_alive_players() if p.role != Role.ASSASSINS]

        if not non_assassins:
            return None

        print("🔪 The Assassins are deciding who to eliminate...")

        # Each assassin member votes
        votes = {}
        for assassin in assassins_members:
            target_names = [p.name for p in non_assassins]
            context = f"Night {game.day_number} - Assassins Decision"

            # Let assassins know who their teammates are
            teammates = [m.name for m in assassins_members if m != assassin]
            teammate_info = f"Your fellow Assassins: {', '.join(teammates)}" if teammates else "You are the only Assassin."

            choice, reasoning = self.llm.get_player_choice_with_reasoning(
                player=assassin,
                prompt=f"{teammate_info}\n\nWho should the Assassins eliminate tonight?",
                valid_choices=target_names,
                context=context
            )

            votes[assassin.name] = choice
            print(f"  💭 {assassin.name} thinks: {reasoning}")
            print(f"  🔪 {assassin.name} votes for {choice}")

        # Majority vote
        if votes:
            vote_counts = Counter(votes.values())
            target_name = vote_counts.most_common(1)[0][0]
            return game.get_player_by_name(target_name)

        return None

    def _doctor_action(self, game: GameState) -> Optional[Player]:
        """Doctor chooses who to protect."""
        doctors = [p for p in game.get_alive_players() if p.role == Role.DOCTOR]

        if not doctors:
            return None

        doctor = doctors[0]
        alive_players = game.get_alive_players()

        print("💊 The Doctor is choosing who to protect...")

        # Doctor can't protect the same person two nights in a row
        available_targets = [
            p for p in alive_players
            if p.name != doctor.last_protected
        ]

        target_names = [p.name for p in available_targets]
        context = f"Night {game.day_number} - Doctor Decision"

        prompt = "Who would you like to protect tonight?"
        if doctor.last_protected:
            prompt += f" (You cannot protect {doctor.last_protected} again - they were your last patient.)"

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=doctor,
            prompt=prompt,
            valid_choices=target_names,
            context=context
        )

        target = game.get_player_by_name(choice)
        if target:
            target.protected = True
            doctor.last_protected = choice
            print(f"  💭 {doctor.name} thinks: {reasoning}")
            print(f"  💊 {doctor.name} protects {choice}")
            doctor.add_memory(f"I protected {choice} on Night {game.day_number}")

        return target

    def _detective_action(self, game: GameState) -> Optional[str]:
        """Detective investigates a player."""
        detectives = [p for p in game.get_alive_players() if p.role == Role.DETECTIVE]

        if not detectives:
            return None

        detective = detectives[0]
        other_players = [p for p in game.get_alive_players() if p != detective]

        if not other_players:
            return None

        print("🔍 The Detective is investigating...")

        target_names = [p.name for p in other_players]
        context = f"Night {game.day_number} - Detective Investigation"

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=detective,
            prompt="Who would you like to investigate tonight?",
            valid_choices=target_names,
            context=context
        )

        target = game.get_player_by_name(choice)
        if target:
            is_assassin = target.is_assassin()
            result = "IS an Assassin" if is_assassin else "is NOT an Assassin"
            memory = f"I investigated {choice} on Night {game.day_number}. They {result}."
            detective.add_memory(memory)
            print(f"  💭 {detective.name} thinks: {reasoning}")
            print(f"  🔍 {detective.name} investigates {choice}")
            return f"{detective.name} learned that {choice} {result}"

        return None

    def _get_discussion_statement(self, player: Player, game: GameState) -> tuple[str, str]:
        """Get a player's statement during discussion.

        Returns:
            Tuple of (thinking, statement)
        """
        alive_names = [p.name for p in game.get_alive_players() if p != player]

        context = f"Day {game.day_number} - Discussion"
        prompt = f"""It's the day discussion phase. Think carefully, then make a statement to the group.

STRATEGIC GUIDANCE:
- DON'T reveal information that makes you a target (being "logical," "analytical," "perceptive")
- DO try to blend in and appear average/unremarkable
- Consider what a villager vs. Assassin would say
- Be careful not to reveal your role unnecessarily
- You can share suspicions, defend yourself, or try to appear innocent

ROLE TERMINOLOGY: Use exact role names - Doctor (not Healer), Detective (not Investigator), Vigilante, Assassins (not Mafia).

Other alive players: {', '.join(alive_names)}

Keep your statement concise (2-3 sentences max)."""

        return self.llm.get_player_statement(
            player=player,
            prompt=prompt,
            context=context,
            max_tokens=150
        )

    def _get_ghost_statement(self, ghost: Player, haunted: Player, game: GameState) -> tuple[str, str]:
        """Get a ghost's statement while haunting someone.

        Returns:
            Tuple of (thinking, statement)
        """
        context = f"Day {game.day_number} - Ghost Haunting"
        prompt = f"""You are a GHOST haunting {haunted.name}. You died but don't know who killed you.
You can only yell at {haunted.name} publicly during discussions.

You should:
- Be angry, confused, or accusatory
- Yell at {haunted.name} specifically
- Maybe accuse them (wrongly or rightly)
- Be dramatic and unhinged

You do NOT know who killed you. Keep it brief (1-2 sentences max)."""

        return self.llm.get_player_statement(
            player=ghost,
            prompt=prompt,
            context=context,
            max_tokens=100
        )

    def _conduct_vote(self, game: GameState, alive_players: list[Player]) -> dict[str, str]:
        """Conduct voting to eliminate someone."""
        votes = {}

        # Everyone votes
        for player in alive_players:
            other_names = [p.name for p in alive_players if p != player]

            if not other_names:
                continue

            context = f"Day {game.day_number} - Voting"
            prompt = """Based on the discussion, who do you vote to eliminate?
Consider:
- Who seems most suspicious?
- Who might be an Assassin?
- What strategy helps your team win?

Choose carefully."""

            choice = self.llm.get_player_choice(
                player=player,
                prompt=prompt,
                valid_choices=other_names,
                context=context
            )

            votes[player.name] = choice
            print(f"  {player.name} votes for {choice}")

            # Players remember how they voted
            player.add_memory(f"I voted for {choice} on Day {game.day_number}")

        return votes

    def _vigilante_action(self, game: GameState) -> Optional[Player]:
        """Vigilante chooses who to eliminate."""
        vigilantes = [p for p in game.get_alive_players() if p.role == Role.VIGILANTE]

        if not vigilantes:
            return None

        vigilante = vigilantes[0]

        # Vigilante can only kill once
        if vigilante.vigilante_has_killed:
            return None

        other_players = [p for p in game.get_alive_players() if p != vigilante]

        if not other_players:
            return None

        print("⚔️  The Vigilante is choosing a target...")

        # Vigilante can choose to skip
        target_names = ["Skip (don't kill anyone tonight)"] + [p.name for p in other_players]
        context = f"Night {game.day_number} - Vigilante Decision"

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=vigilante,
            prompt="Who would you like to eliminate tonight? Choose someone you believe is an Assassin, or skip if you're not confident. Be careful - if you're wrong, you'll kill an innocent villager! (You can only do this ONCE per game.)",
            valid_choices=target_names,
            context=context
        )

        print(f"  💭 {vigilante.name} thinks: {reasoning}")

        # Check if vigilante chose to skip
        if choice.startswith("Skip"):
            print(f"  ⚔️  {vigilante.name} decides not to act tonight")
            vigilante.add_memory(f"I chose not to use my vigilante shot on Night {game.day_number}")
            return None

        print(f"  ⚔️  {vigilante.name} targets {choice}")

        target = game.get_player_by_name(choice)
        if target:
            vigilante.add_memory(f"I targeted {choice} on Night {game.day_number}")
            vigilante.vigilante_has_killed = True

        return target

    def _check_suicide(self, game: GameState) -> None:
        """Check if the suicidal villager commits suicide."""
        import random

        suicidal_players = [p for p in game.get_alive_players() if p.suicidal]

        if not suicidal_players:
            return

        suicidal = suicidal_players[0]

        # 20% chance each night
        if random.random() < 0.2:
            print(f"💀 {suicidal.name} has committed suicide!")
            game.eliminate_player(
                suicidal,
                "They took their own life.",
                f"{suicidal.name} was found dead."
            )

    def _zombie_attack(self, game: GameState) -> None:
        """Handle zombie attacks from previously killed zombies."""
        import random

        # Find anyone marked for zombification
        pending_zombies = [p for p in game.get_alive_players() if p.pending_zombification]

        for zombie in pending_zombies:
            zombie.pending_zombification = False

            # The newly zombified person kills a random villager
            alive_villagers = [p for p in game.get_alive_players()
                             if p.team == "village" and not p.is_zombie and p != zombie]

            if alive_villagers:
                victim = random.choice(alive_villagers)
                print(f"🧟 {zombie.name} has risen as a zombie and attacks {victim.name}!")
                zombie.is_zombie = True
                zombie.role = Role.ZOMBIE
                game.eliminate_player(
                    victim,
                    f"They were killed by zombie {zombie.name}.",
                    f"{victim.name} was found dead."
                )

    def _sleepwalker_action(self, game: GameState) -> None:
        """Sleepwalker moves around at night but doesn't do anything."""
        sleepwalkers = [p for p in game.get_alive_players() if p.is_sleepwalker]

        if sleepwalkers:
            for sleepwalker in sleepwalkers:
                print(f"🌙 {sleepwalker.name} is sleepwalking...")

    def _insomniac_action(self, game: GameState) -> list[tuple[str, str]]:
        """Insomniac sees someone moving around but not what they're doing."""
        insomniacs = [p for p in game.get_alive_players() if p.is_insomniac]
        sightings = []

        if not insomniacs:
            return sightings

        for insomniac in insomniacs:
            # Insomniac sees a random other alive player moving around
            other_players = [p for p in game.get_alive_players() if p != insomniac]
            if other_players:
                seen = random.choice(other_players)
                insomniac.insomniac_sighting = seen.name
                memory = f"I saw {seen.name} moving around on Night {game.day_number}, but I don't know what they were doing."
                insomniac.add_memory(memory)
                sightings.append((insomniac.name, seen.name))

        return sightings
