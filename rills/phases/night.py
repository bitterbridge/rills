"""Night phase logic - actions and resolutions."""

import random
from collections import Counter
from typing import TYPE_CHECKING

from ..game import GameState
from ..models import PlayerModifier
from ..models.actions import NightResult
from ..player import Player
from ..roles import Role

if TYPE_CHECKING:
    from ..llm import LLMAgent


class NightPhaseHandler:
    """Handles all night phase logic."""

    def __init__(self, llm_agent: "LLMAgent"):
        """Initialize the night phase handler."""
        self.llm = llm_agent

    def run_night_phase(self, game: GameState) -> list[str]:
        """Execute the night phase where special roles take actions.

        Returns:
            List of player names who died during the night
        """
        from ..formatting import h4

        print(f"\n### 🌙 Night {game.day_number}\n")

        # Notify events of night start
        if game.event_registry:
            effects = game.event_registry.on_night_start(game)
            game._apply_event_effects(effects)

            # Handle zombie attacks
            from ..events import ZombieEvent

            for event in game.event_registry.get_active_events():
                if isinstance(event, ZombieEvent):
                    event.handle_zombie_attacks(game, self.llm)

        # Reset protection status
        for player in game.get_alive_players():
            player.protected = False
            player.remove_modifier(game, "protected")
            player.insomniac_sighting = None

        # ==== COLLECT ALL NIGHT ACTIONS ====
        night_result = NightResult()

        # Assassins section
        print(h4("Assassins"))
        night_result.assassin_target = self._assassins_action(game)

        # Villagers section
        print(h4("Villagers"))
        night_result.doctor_target = self._doctor_action(game)
        night_result.detective_result = self._detective_action(game)
        night_result.vigilante_target = self._vigilante_action(game)
        self._mad_scientist_action(game)

        # ==== APPLY AND RESOLVE NIGHT ACTIONS ====
        print(h4("Events"))

        # Apply night results and collect deaths
        deaths = self._apply_night_results(game, night_result)

        # Notify events of night end
        if game.event_registry:
            effects = game.event_registry.on_night_end(game)
            game._apply_event_effects(effects)

            # Handle ghost choices
            from ..events import GhostEvent

            for event in game.event_registry.get_active_events():
                if isinstance(event, GhostEvent):
                    event.handle_ghost_choice(game, self.llm)

        # ==== SUMMARY ====
        print(h4("Summary"))
        self._display_night_summary(game)

        game.check_win_condition()

        return deaths

    def _apply_night_results(self, game: GameState, result: NightResult) -> list[str]:
        """Apply the results of night actions.

        Returns:
            List of player names who died
        """
        deaths = []

        # Detective investigates BEFORE deaths
        if result.detective_result:
            print(f"🔍 {result.detective_result}")

        # Resolve assassin kill
        if result.assassin_target:
            counter_killed = None
            if game.event_registry:
                from ..events import GunNutEvent

                for event in game.event_registry.get_active_events():
                    if isinstance(event, GunNutEvent):
                        counter_killed = event.check_counter_attack(game, result.assassin_target)
                        break

            if counter_killed:
                print(
                    f"💥 {result.assassin_target.name} fought back. {counter_killed.name} was killed instead."
                )
                game.eliminate_player(
                    counter_killed,
                    f"{result.assassin_target.name} (Gun Nut) killed them in self-defense.",
                    f"{counter_killed.name} was found dead.",
                )
                result.counter_kills.append(counter_killed)
                deaths.append(counter_killed.name)
            elif result.doctor_target and result.doctor_target == result.assassin_target:
                print(f"💊 The Doctor saved {result.assassin_target.name}.")
                game.events.append("Someone was attacked but saved by the Doctor.")
            else:
                print(f"☠️  {result.assassin_target.name} was eliminated by the Assassins.")
                print(
                    f"💀 {result.assassin_target.name} was a {result.assassin_target.role.value}."
                )
                game.eliminate_player(
                    result.assassin_target,
                    "They were killed by the Assassins.",
                    f"{result.assassin_target.name} was found dead. They were {result.assassin_target.role.display_name()}.",
                )
                result.deaths.append(result.assassin_target)
                deaths.append(result.assassin_target.name)

        # Resolve vigilante kill
        if result.vigilante_target:
            vigilantes = [p for p in game.get_alive_players() if p.role == Role.VIGILANTE]
            vigilante = vigilantes[0] if vigilantes else None

            counter_killed = None
            if game.event_registry and vigilante:
                from ..events import GunNutEvent

                for event in game.event_registry.get_active_events():
                    if isinstance(event, GunNutEvent):
                        counter_killed = event.check_counter_attack(
                            game, result.vigilante_target, vigilante
                        )
                        break

            if counter_killed:
                print(
                    f"💥 {result.vigilante_target.name} fought back. {counter_killed.name} was killed instead."
                )
                print(f"💀 {counter_killed.name} was a {counter_killed.role.value}.")
                game.eliminate_player(
                    counter_killed,
                    f"{result.vigilante_target.name} (Gun Nut) killed them in self-defense.",
                    f"{counter_killed.name} was found dead. They were {counter_killed.role.display_name()}.",
                )
                result.counter_kills.append(counter_killed)
                deaths.append(counter_killed.name)
            elif result.doctor_target and result.doctor_target == result.vigilante_target:
                pass  # Blocked by doctor
            else:
                print(f"☠️  {result.vigilante_target.name} was found dead.")
                print(
                    f"💀 {result.vigilante_target.name} was a {result.vigilante_target.role.value}."
                )
                game.eliminate_player(
                    result.vigilante_target,
                    "They were killed by the Vigilante.",
                    f"{result.vigilante_target.name} was found dead. They were {result.vigilante_target.role.display_name()}.",
                )
                result.deaths.append(result.vigilante_target)
                deaths.append(result.vigilante_target.name)

        return deaths

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

    def _assassins_action(self, game: GameState) -> Player | None:
        """Assassins choose who to eliminate."""
        from ..formatting import h5
        from ..models import Visibility

        assassins_members = [p for p in game.get_alive_players() if p.role == Role.ASSASSINS]

        if not assassins_members:
            return None

        non_assassins = [p for p in game.get_alive_players() if p.role != Role.ASSASSINS]

        if not non_assassins:
            return None

        # Assassin discussion phase
        if len(assassins_members) > 1:
            print(h5("Discussion"))

            def get_assassin_statement(assassin, context, round_num):
                teammates = [m.name for m in assassins_members if m.name != assassin.name]
                teammate_info = f"Your fellow Assassins: {', '.join(teammates)}"

                prompt = f"""{teammate_info}

It's nighttime. Discuss with your team who you think should be eliminated tonight.
Consider:
- Who is the biggest threat to the Assassins?
- Who might be the Doctor, Detective, or Vigilante?
- What's your team's strategy?

Share your thoughts with your fellow Assassins (1-2 sentences)."""

                if context:
                    prompt += f"\n\nWhat your teammates have said:\n{context}"

                thinking, statement = self.llm.get_player_statement(
                    player=assassin,
                    prompt=prompt,
                    context=f"Night {game.day_number} - Assassin Discussion",
                    max_tokens=100,
                )
                return thinking, statement

            round_obj = game.conversation_service.conduct_round(
                participants=assassins_members,
                phase="assassin_discussion",
                round_number=1,
                day_number=game.day_number,
                get_statement_func=get_assassin_statement,
                visibility=Visibility("team", ["Assassins"]),
            )

            # Display statements
            for stmt in round_obj.statements:
                print(f"  💭 {stmt.speaker} thinks: {stmt.thinking}")
                print(f"  🔪 {stmt.speaker}: {stmt.content}\n")

                # Backwards compatibility
                assassin = next(a for a in assassins_members if a.name == stmt.speaker)
                assassin._last_assassin_statement = stmt.content

        # Voting
        print(h5("Voting"))
        votes = {}
        for assassin in assassins_members:
            target_names = [p.name for p in non_assassins]
            teammates = [m.name for m in assassins_members if m != assassin]

            prompt = game.context_builder.build_for_night_kill(
                assassin, targets=target_names, team_members=teammates
            )
            system_context = game.context_builder.build_system_context(assassin, "night")

            choice, reasoning = self.llm.get_player_choice_with_reasoning(
                player=assassin,
                prompt=f"Who should the Assassins eliminate tonight?\n\n{prompt}",
                valid_choices=target_names,
                context=system_context,
            )

            votes[assassin.name] = choice
            print(f"  💭 {assassin.name} thinks: {reasoning}")
            print(f"  🔪 {assassin.name} votes for {choice}")

        print()

        if votes:
            vote_counts = Counter(votes.values())
            target_name = vote_counts.most_common(1)[0][0]
            return game.get_player_by_name(target_name)

        return None

    def _doctor_action(self, game: GameState) -> Player | None:
        """Doctor chooses who to protect."""
        from ..formatting import h5

        doctors = [p for p in game.get_alive_players() if p.role == Role.DOCTOR]

        if not doctors:
            return None

        doctor = doctors[0]
        alive_players = game.get_alive_players()

        print(h5("Doctor"))

        available_targets = [p for p in alive_players if p.name != doctor.last_protected]
        target_names = [p.name for p in available_targets]

        prompt = game.context_builder.build_for_protection(
            doctor, targets=target_names, last_protected=doctor.last_protected
        )
        system_context = game.context_builder.build_system_context(doctor, "night")

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=doctor, prompt=prompt, valid_choices=target_names, context=system_context
        )

        target = game.get_player_by_name(choice)
        if target:
            target.protected = True
            target.add_modifier(
                game,
                PlayerModifier(type="protected", source="doctor", expires_on=game.day_number + 1),
            )
            doctor.last_protected = choice
            print(f"  💭 {doctor.name} thinks: {reasoning}")
            print(f"  💊 {doctor.name} protects {choice}")

        return target

    def _detective_action(self, game: GameState) -> str | None:
        """Detective investigates a player."""
        from ..formatting import h5

        detectives = [p for p in game.get_alive_players() if p.role == Role.DETECTIVE]

        if not detectives:
            return None

        detective = detectives[0]
        other_players = [p for p in game.get_alive_players() if p != detective]

        if not other_players:
            return None

        print(h5("Detective"))

        target_names = [p.name for p in other_players]

        prompt = game.context_builder.build_for_investigation(detective, targets=target_names)
        system_context = game.context_builder.build_system_context(detective, "night")

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=detective, prompt=prompt, valid_choices=target_names, context=system_context
        )

        target = game.get_player_by_name(choice)
        if target:
            is_assassin = target.is_assassin()
            result = "IS an Assassin" if is_assassin else "is NOT an Assassin"
            print(f"  💭 {detective.name} thinks: {reasoning}")
            print(f"  🔍 {detective.name} investigates {choice}")
            return f"{detective.name} learned that {choice} {result}"

        return None

    def _vigilante_action(self, game: GameState) -> Player | None:
        """Vigilante chooses who to eliminate."""
        from ..formatting import h5

        vigilantes = [p for p in game.get_alive_players() if p.role == Role.VIGILANTE]

        if not vigilantes:
            return None

        vigilante = vigilantes[0]

        if vigilante.vigilante_has_killed or vigilante.has_modifier(game, "vigilante_used"):
            return None

        other_players = [p for p in game.get_alive_players() if p != vigilante]

        if not other_players:
            return None

        print(h5("Vigilante"))

        target_names = ["Skip (don't kill anyone tonight)"] + [p.name for p in other_players]

        prompt = game.context_builder.build_for_vigilante_action(vigilante, choices=target_names)
        system_context = game.context_builder.build_system_context(vigilante, "night")

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=vigilante, prompt=prompt, valid_choices=target_names, context=system_context
        )

        print(f"  💭 {vigilante.name} thinks: {reasoning}")

        if choice.startswith("Skip"):
            print(f"  ⚔️  {vigilante.name} decides not to act tonight")
            return None

        print(f"  ⚔️  {vigilante.name} targets {choice}")

        target = game.get_player_by_name(choice)
        if target:
            vigilante.vigilante_has_killed = True
            vigilante.add_modifier(game, PlayerModifier(type="vigilante_used", source="vigilante"))

        return target

    def _mad_scientist_action(self, game: GameState) -> None:
        """Mad Scientist chooses a target and injects them with a random effect."""
        from ..formatting import h5

        scientists = [p for p in game.get_alive_players() if p.role == Role.MAD_SCIENTIST]

        if not scientists:
            return

        scientist = scientists[0]
        other_players = [p for p in game.get_alive_players() if p != scientist]

        if not other_players:
            return

        print(h5("Mad Scientist"))

        target_names = [p.name for p in other_players]
        recent_events = game.info_service.build_context_for(scientist.name)

        prompt = f"""You are conducting a scientific experiment. Choose ONE person to inject with your experimental serum.

You DON'T know what effect it will have - it could help them, harm them, or cause bizarre side effects!

Available test subjects: {", ".join(target_names)}

{recent_events if recent_events else "No recent events."}

Choose your test subject and explain your reasoning (be eccentric and scientific!)."""

        mad_guidance = """

⚗️ IMPORTANT - MAD SCIENTIST MINDSET:
You are ECCENTRIC and your reasoning should reflect this! Your thought process can be:
- Based on pseudoscience ("Their aura is too orange...")
- Obsessed with the SCIENCE of it ("For the advancement of knowledge!")
- Bizarrely logical ("They sneezed twice, clearly a perfect test subject")
- Pattern-seeking in chaos ("Their name has 5 letters, the golden ratio!")
- Enthusiastically manic about experimentation
- Completely ignoring social consequences in favor of "data collection"

Be weird, be enthusiastic, be MAD. Science waits for no one!
"""

        system_context = (
            game.context_builder.build_system_context(scientist, "night") + mad_guidance
        )

        choice, reasoning = self.llm.get_player_choice_with_reasoning(
            player=scientist, prompt=prompt, valid_choices=target_names, context=system_context
        )

        target = game.get_player_by_name(choice)
        if not target:
            target = random.choice(other_players)

        print(f"  💭 {scientist.name} thinks: {reasoning}")
        print(f"  🎯 {scientist.name} chooses to inject: {target.name}")

        # Random effect
        effects = [
            ("zombie", "💉 Zombie Infection", "infected with the zombie virus"),
            ("love", "💘 Love Potion", "injected with a love potion"),
            ("drunk", "🍺 Confusion Serum", "injected with a confusion serum"),
            ("insomniac", "☕ Insomnia Inducer", "injected with an insomnia-inducing serum"),
            ("sleepwalker", "🌙 Sleepwalker Serum", "injected with a sleepwalking serum"),
            ("suicidal", "💀 Depression Serum", "injected with a serum causing dark thoughts"),
        ]

        effect_type, effect_name, description = random.choice(effects)

        print(f"  🎲 Random effect selected: {effect_name}")
        print(f"  💉 {scientist.name} injects {target.name}!")

        # Apply the effect
        if effect_type == "zombie":
            target.pending_zombification = True
            target.add_modifier(
                game,
                PlayerModifier(
                    type="infected", source="mad_scientist", data={"infector": scientist.name}
                ),
            )
            print(f"  🧟 {target.name} has been infected with the zombie virus...")

        elif effect_type == "love":
            possible_loves = [p for p in game.get_alive_players() if p != target]
            if possible_loves:
                beloved = random.choice(possible_loves)
                target.is_lover = True
                target.lover_name = beloved.name
                target.add_modifier(
                    game,
                    PlayerModifier(
                        type="lover",
                        source="mad_scientist",
                        data={"partner": beloved.name, "reciprocated": False},
                    ),
                )
                print(
                    f"  💘 {target.name} has fallen in love with {beloved.name}! (unidirectional)"
                )

        elif effect_type == "drunk":
            target.is_drunk = True
            target.add_modifier(
                game,
                PlayerModifier(
                    type="drunk", source="mad_scientist", expires_on=game.day_number + 1
                ),
            )
            print(f"  🍺 {target.name} is now confused and disoriented...")

        elif effect_type == "insomniac":
            target.is_insomniac = True
            target.add_modifier(game, PlayerModifier(type="insomniac", source="mad_scientist"))
            print(f"  ☕ {target.name} can no longer sleep at night...")

        elif effect_type == "sleepwalker":
            target.is_sleepwalker = True
            target.add_modifier(game, PlayerModifier(type="sleepwalker", source="mad_scientist"))
            print(f"  🌙 {target.name} will now sleepwalk at night...")

        elif effect_type == "suicidal":
            target.suicidal = True
            target.add_modifier(game, PlayerModifier(type="suicidal", source="mad_scientist"))
            print(f"  💀 {target.name} has been afflicted with dark thoughts...")
