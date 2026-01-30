"""Main game loop and CLI."""

import argparse
import time
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .game import GameState, create_game
from .llm import LLMAgent
from .phases import PhaseManager
from .roles import Role


console = Console()


def display_game_start(game: GameState) -> None:
    """Display game start information."""
    console.print("\n[bold cyan]🎭 ASSASSINS - LLM Edition 🎭[/bold cyan]\n")

    # Display active random events
    if game.event_registry:
        active_events = game.event_registry.get_active_events()
        if active_events:
            console.print("[yellow]⚠️  Special Event Modes Active:[/yellow]")
            for event in active_events:
                console.print(f"  {event.name}: {event.description}")
            console.print()

    table = Table(title="Players")
    table.add_column("Name", style="cyan")
    table.add_column("Role", style="magenta")
    table.add_column("Personality", style="yellow")

    for player in game.players:
        # Build role info string with modifiers
        role_info = [player.role.value]
        if player.suicidal:
            role_info.append("Suicidal")
        if player.is_sleepwalker:
            role_info.append("Sleepwalker")
        if player.is_insomniac:
            role_info.append("Insomniac")
        if player.is_gun_nut:
            role_info.append("Gun Nut")
        if player.is_drunk:
            role_info.append("Drunk")
        if player.is_jester:
            role_info.append("Jester")
        if player.is_priest and player.resurrection_available:
            role_info.append("Priest")
        if player.is_lover:
            role_info.append(f"Lover({player.lover_name})")
        if player.is_bodyguard and player.bodyguard_active:
            role_info.append("Bodyguard")
        if player.is_zombie and player.role != Role.ZOMBIE:
            role_info.append("Infected")

        role_str = " + ".join(role_info)
        table.add_row(player.name, role_str, player.personality)

    console.print(table)
    console.print("\n[italic]The game begins...[/italic]\n")
    time.sleep(2)


def display_game_status(game: GameState) -> None:
    """Display current game status."""
    alive = game.get_alive_players()

    console.print(f"\n[bold]Alive Players ({len(alive)}):[/bold]")
    for player in alive:
        # Build role info string for human viewing
        role_info = [player.role.value]
        if player.suicidal:
            role_info.append("Suicidal")
        if player.is_sleepwalker:
            role_info.append("Sleepwalker")
        if player.is_insomniac:
            role_info.append("Insomniac")
        if player.is_gun_nut:
            role_info.append("Gun Nut")
        if player.is_drunk:
            role_info.append("Drunk")
        if player.is_jester:
            role_info.append("Jester")
        if player.is_priest and player.resurrection_available:
            role_info.append("Priest")
        if player.is_lover:
            role_info.append(f"Lover({player.lover_name})")
        if player.is_bodyguard and player.bodyguard_active:
            role_info.append("Bodyguard")
        # Show "Infected" for living zombies, they become "Zombie" after death
        if player.is_zombie and player.role != Role.ZOMBIE:
            role_info.append("Infected")
        if player.pending_zombification:
            role_info.append("Becoming Infected")
        if player.vigilante_has_killed:
            role_info.append("Vig Used")

        role_str = " + ".join(role_info)
        console.print(f"  • {player.name} ({role_str})")


def display_game_end(game: GameState) -> None:
    """Display game end information."""
    console.print("\n" + "="*60)
    console.print(f"[bold green]🎉 GAME OVER 🎉[/bold green]")
    console.print("="*60 + "\n")

    if game.winner == "village":
        console.print("[bold green]The Village has won![/bold green]")
    else:
        console.print("[bold red]The Assassins have won![/bold red]")

    console.print("\n[bold]Final Player Roles:[/bold]")
    for player in game.players:
        status = "✓" if player.alive else "✗"
        # Show Villager (Infected) for zombie role
        if player.role == Role.ZOMBIE:
            role_display = "Villager (Infected)"
        else:
            role_display = player.role.value
        console.print(f"  {status} {player.name} - {role_display} ({player.team})")


def generate_player_configs(num_players: int) -> list[dict]:
    """Generate player configurations dynamically.

    Args:
        num_players: Number of players (5-20)

    Returns:
        List of player configuration dicts
    """
    # Extended pool of names
    names = [
        "Alice", "Bob", "Carol", "David", "Eve", "Frank", "Grace", "Henry", "Iris",
        "Jack", "Kate", "Liam", "Mia", "Noah", "Olivia", "Paul", "Quinn", "Ruby",
        "Sam", "Tina"
    ]

    # Pool of personalities
    personalities = [
        "Cunning and manipulative, pretends to be helpful",
        "Aggressive and intimidating, tries to control the conversation",
        "Cautious and analytical, tries to protect the innocent",
        "Bold and direct, speaks their mind",
        "Suspicious and paranoid, questions everything",
        "Friendly and trusting, maybe too trusting",
        "Logical and methodical, follows evidence",
        "Nervous and anxious, easily flustered under pressure",
        "Quiet and reserved, keeps to themselves",
        "Charismatic and persuasive, natural leader",
        "Sarcastic and witty, makes jokes to deflect",
        "Timid and hesitant, avoids confrontation",
        "Observant and calculating, notices small details",
        "Emotional and reactive, wears heart on sleeve",
        "Strategic and patient, plays the long game",
        "Impulsive and reckless, acts without thinking",
        "Diplomatic and fair, seeks compromise",
        "Mysterious and cryptic, speaks in riddles",
        "Blunt and honest, no filter",
        "Optimistic and cheerful, sees the best in everyone"
    ]

    # Role distribution: roughly 1/3 Assassins, rest divided among power roles and villagers
    num_assassins = max(2, num_players // 3)
    num_power_roles = min(3, num_players - num_assassins - 2)  # Doctor, Detective, Vigilante
    num_villagers = num_players - num_assassins - num_power_roles - 1  # -1 for Zombie

    roles = (
        ["Assassins"] * num_assassins +
        ["Doctor", "Detective", "Vigilante"][:num_power_roles] +
        ["Villager"] * num_villagers +
        ["Zombie"]
    )

    return [
        {
            "name": names[i],
            "role": roles[i],
            "personality": personalities[i % len(personalities)]
        }
        for i in range(num_players)
    ]


def run_game(game: GameState, llm_agent: LLMAgent, delay: float = 1.0) -> None:
    """
    Run the main game loop.

    Args:
        game: The game state
        llm_agent: LLM agent for decision making
        delay: Delay between phases in seconds
    """
    phase_manager = PhaseManager(llm_agent)

    display_game_start(game)

    # Explain basic game rules
    print(f"\n{'='*60}")
    print("📖 GAME RULES")
    print(f"{'='*60}\n")
    print("🎯 WIN CONDITIONS:")
    print("   • Village team wins if all Assassins are eliminated")
    print("   • Assassins win if they equal or outnumber the village\n")
    print("🗳️  VOTING RULES:")
    print("   • During day phase, everyone votes to eliminate someone")
    print("   • You can vote for anyone or choose to ABSTAIN")
    print("   • The person with the MOST votes is eliminated")
    print("   • ⚠️  TIE RULE: If votes tie, NO ONE is eliminated that day")
    print("   • Vote breakdowns are shown - you'll see who voted for whom\n")
    print("🌙 NIGHT ACTIONS:")
    print("   • Power roles act at night (Doctor, Detective, Vigilante)")
    print("   • Assassins choose someone to eliminate")
    print("   • Roles are revealed when players die\n")
    print("Press Ctrl+C at any time to end the game.\n")
    time.sleep(3)

    # Explain active events to all players
    if game.event_registry:
        active_events = game.event_registry.get_active_events()
        if active_events:
            print(f"\n{'='*60}")
            print("⚠️  SPECIAL EVENTS IN THIS GAME")
            print(f"{'='*60}\n")

            event_explanations = []
            for event in active_events:
                if event.name == "Insomniac Mode":
                    event_explanations.append(
                        "🔍 INSOMNIAC: One player has insomnia and stays awake at night.\n"
                        "   They can see WHO moves around at night (but not what they're doing).\n"
                        "   \n"
                        "   ⚠️  IMPORTANT: If someone says they saw you moving at night, THIS IS A REAL GAME MECHANIC!\n"
                        "   The Insomniac player can genuinely see movement. Don't automatically assume they're lying.\n"
                        "   Power roles (Doctor, Detective, Vigilante, Assassins) DO move at night to use their abilities.\n"
                        "   Being seen moving does NOT prove someone is an Assassin - it could be any power role!"
                    )
                elif event.name == "Zombie Mode":
                    event_explanations.append(
                        "🧟 ZOMBIE: One player is secretly infected with a zombie virus.\n"
                        "   The infected player DOES NOT KNOW they are infected - they play as a normal villager.\n"
                        "   If/when they die (by lynch or assassination), they will RISE AS A ZOMBIE the next night.\n"
                        "   Zombies attack and infect villagers each night - victims become new zombies when killed.\n"
                        "   This can create exponential zombie spread if not stopped!"
                    )
                elif event.name == "Ghost Mode":
                    event_explanations.append(
                        "👻 GHOST: This is a REAL GAME MECHANIC - not role-playing!\n"
                        "   When players die, they may return as ghosts who can haunt one living player.\n"
                        "   Ghosts can speak and make accusations through their haunted target.\n"
                        "   Ghost statements will appear in the format: 'A ghostly voice (claiming to be [Name]) says...'\n"
                        "   Ghosts are trying to help their team from beyond the grave!"
                    )
                elif event.name == "Sleepwalker Mode":
                    event_explanations.append(
                        "🌙 SLEEPWALKER: One player sleepwalks at night and wanders around unconsciously.\n"
                        "   The sleepwalker does NOT know they are sleepwalking.\n"
                        "   They may be spotted by Insomniacs or others who can see nighttime movement.\n"
                        "   Being a sleepwalker does NOT make someone evil - it's just a quirk!"
                    )
                elif event.name == "Gun Nut Mode":
                    event_explanations.append(
                        "🔫 GUN NUT: One player keeps a gun under their pillow for protection.\n"
                        "   If Assassins try to kill them at night, there's a 50% chance the Gun Nut will SHOOT BACK!\n"
                        "   When successful, a random attacker dies and the Gun Nut survives.\n"
                        "   The Gun Nut will know privately that they killed someone, but others won't know how the person died.\n"
                        "   This can happen multiple times - each attack has a 50% chance of backfiring!"
                    )
                elif event.name == "Suicidal Mode":
                    event_explanations.append("💀 SUICIDAL: One player is struggling with dark thoughts and may take their own life during the night!")
                elif event.name == "Drunk Mode":
                    event_explanations.append(
                        "🍺 DRUNK: One player is drunk and confused.\n"
                        "   When they vote during the day, their vote will go to a RANDOM player instead of their intended target!\n"
                        "   The drunk player won't know their vote was redirected.\n"
                        "   This can lead to unexpected vote outcomes!"
                    )
                elif event.name == "Jester Mode":
                    event_explanations.append(
                        "🃏 JESTER: One player is a Jester who WANTS to be executed!\n"
                        "   If the Jester is lynched by the town, the Jester WINS and the game ends immediately.\n"
                        "   The Jester doesn't know who the Assassins are - they're just trying to seem suspicious.\n"
                        "   Be careful who you vote for - they might be trying to get lynched!"
                    )
                elif event.name == "Priest Mode":
                    event_explanations.append(
                        "🙏 PRIEST: One player is a Priest with the power to resurrect the dead!\n"
                        "   During any day phase, the Priest can bring ONE dead player back to life.\n"
                        "   This is a one-time ability - use it wisely!\n"
                        "   The Priest must choose carefully who to resurrect."
                    )
                elif event.name == "Lovers Mode":
                    event_explanations.append(
                        "💕 LOVERS: Two players are secretly bound by true love.\n"
                        "   The lovers know each other's identities, but others don't know who they are.\n"
                        "   If one lover dies (by any means), the other will die of heartbreak the next night.\n"
                        "   Lovers can be on different teams - love transcends allegiances!"
                    )
                elif event.name == "Bodyguard Mode":
                    event_explanations.append(
                        "🛡️  BODYGUARD: One player is a loyal bodyguard willing to sacrifice themselves.\n"
                        "   During a night phase, the Bodyguard can choose someone to protect.\n"
                        "   If Assassins attack the protected person, the Bodyguard DIES IN THEIR PLACE!\n"
                        "   This is a one-time ability - the Bodyguard can only sacrifice themselves once."
                    )

            for explanation in event_explanations:
                print(f"{explanation}\n")

            print("These are all legitimate game mechanics. Keep them in mind!\n")
            time.sleep(3)

    # Tell Assassins who their teammates are
    assassins = [p for p in game.players if p.role == Role.ASSASSINS]
    if len(assassins) > 1:
        print(f"\n{'='*60}")
        print("🔪 ASSASSIN TEAM BRIEFING")
        print(f"{'='*60}\n")
        assassin_names = [a.name for a in assassins]
        print(f"The Assassins are: {', '.join(assassin_names)}\n")
        print("You work together to eliminate villagers at night.")
        print("Coordinate your strategy, but be careful during the day - don't reveal yourselves!\n")

        # Use InformationService to track team information
        game.info_service.reveal_to_team(
            team="Assassins",
            content=f"Your Assassin teammates are: {', '.join(assassin_names)}",
            category=InfoCategory.TEAM_INFO,
            day=0,
            team_members=assassin_names
        )

        # Backwards compatibility: Keep old memory system
        for assassin in assassins:
            teammate_names = [a.name for a in assassins if a != assassin]
            if teammate_names:
                assassin.add_memory(f"My fellow Assassins are: {', '.join(teammate_names)}")

        time.sleep(3)

    # Day 0 - Introduction phase
    print(f"\n{'='*60}")
    print("☀️  Day 0 - Introductions")
    print(f"{'='*60}\n")
    print("The players gather to introduce themselves...\n")

    for player in game.get_alive_players():
        thinking, intro = llm_agent.get_player_statement(
            player=player,
            prompt="""Introduce yourself to the group.

STRATEGIC GUIDANCE: Be careful what you reveal! If you describe yourself as "logical" or "analytical," the Assassins may target you. If you seem too clever or perceptive, you become a threat. Consider being vague, humble, or even slightly misleading about your capabilities while still being friendly.
ROLE TERMINOLOGY: Use exact role names - Doctor (not Healer), Detective (not Investigator), Vigilante, Assassins (not Mafia).
Keep your introduction brief (1-2 sentences).""",
            context="Day 0 - Introductions",
            max_tokens=150
        )
        print(f"  💭 {player.name} thinks: {thinking}")
        print(f"💬 {player.name}: {intro}\n")

        # Players remember introductions
        for other in game.get_alive_players():
            if other != player:
                other.add_memory(f"{player.name} introduced themselves: {intro}")

    time.sleep(delay)

    # Main game loop
    while not game.game_over:
        if game.phase == "night":
            phase_manager.run_night_phase(game)
        else:
            phase_manager.run_day_phase(game)

        if not game.game_over:
            display_game_status(game)
            game.advance_phase()
            time.sleep(delay)

    display_game_end(game)

    # Postgame chat - players talk shit
    print(f"\n{'='*60}")
    print("💀 POSTGAME - THE TRUTH COMES OUT")
    print(f"{'='*60}\n")
    print("Now that the game is over, the players can speak freely...\n")

    # Build comprehensive game summary
    role_summary_lines = []
    for p in game.players:
        # Show role appropriately
        if p.role == Role.ZOMBIE:
            role_display = "Villager (Infected)"
        else:
            role_display = p.role.value
        role_summary_lines.append(f"  - {p.name} was {role_display} ({'alive' if p.alive else 'dead'})")
    role_summary = "\n".join(role_summary_lines)

    # Use personality-weighted speaking order for postgame
    from .phases import get_speaking_order
    speaking_order = get_speaking_order(game.players)

    for player in speaking_order:
        # Special explanation for infected/zombie role
        if player.role == Role.ZOMBIE:
            role_explanation = (
                "Your ACTUAL role was: Villager (Infected)\n"
                "You were infected with a zombie virus but didn't know it.\n"
                "You played as a normal Villager throughout the game.\n"
                "If you had died, you would have risen as a zombie and attacked villagers."
            )
            role_display = "Villager (Infected)"
        else:
            role_explanation = f"Your ACTUAL role was: {player.role.value}"
            role_display = player.role.value

        # Build context of what others have said
        prior_statements = ""
        for other in game.players:
            if other != player and hasattr(other, '_postgame_statement'):
                prior_statements += f"\n{other.name} said: {other._postgame_statement}"

        postgame_context = f"""The game is over. The {game.winner} team won.

==== CRITICAL: YOUR ACTUAL ROLE ====
You are {player.name}.
{role_explanation}
You were on the {player.team} team.
You are {'ALIVE' if player.alive else 'DEAD'}.

==== ALL PLAYER ROLES (REVEALED) ====
{role_summary}

==== WHAT OTHERS HAVE SAID ====
You can respond to or comment on what others said:{prior_statements}

==== WHAT YOU CAN DO NOW ====
Now you can speak freely about:
- What YOUR ACTUAL ROLE ({role_display}) was and how you played it
- What you were thinking during the game
- What actually happened vs what you thought was happening
- RESPOND to what others said if relevant
- Call out people who lied or fooled you
- Celebrate your win or complain about your loss
- Talk about other players' strategies

IMPORTANT: Be honest about YOUR ACTUAL ROLE ({player.role.value}). Don't claim to be a different role!
ROLE TERMINOLOGY: Use exact role names - Doctor (not Healer), Detective (not Investigator), Vigilante, Assassins (not Mafia)."""

        thinking, statement = llm_agent.get_player_statement(
            player=player,
            prompt=f"The game is over. You were {role_display}. What do you want to say about how the game went? (2-3 sentences max)",
            context=postgame_context,
            max_tokens=150
        )

        alive_marker = "" if player.alive else " 💀"
        ghost_marker = " 👻" if player.is_ghost else ""
        print(f"  💭 {player.name} thinks: {thinking}")
        print(f"💬 {player.name}{alive_marker}{ghost_marker} ({role_display}): {statement}\n")

        # Store for others to read
        player._postgame_statement = statement

        time.sleep(delay * 0.5)  # Shorter delay for postgame

    # Post-game suggestions and discussion
    print(f"\n{'='*60}")
    print("🎯 SUGGESTIONS FOR IMPROVEMENT")
    print(f"{'='*60}\n")
    print("The players discuss how to improve the game...\n")

    for round_num in range(2):  # Two rounds of discussion
        print(f"--- Round {round_num + 1} ---\n")

        # Use personality-weighted speaking order
        from .phases import get_speaking_order
        speaking_order = get_speaking_order(game.players)

        for player in speaking_order:
            # Get role display for this player
            if player.role == Role.ZOMBIE:
                player_role_display = "Villager (Infected)"
            else:
                player_role_display = player.role.value

            # Build context of what others have said in this round
            prior_discussion = ""
            for other in game.players:
                if other != player and hasattr(other, f'_suggestion_round_{round_num}'):
                    prior_discussion += f"\n{other.name} said: {getattr(other, f'_suggestion_round_{round_num}')}"

            if round_num == 0:
                suggestion_context = f"""The game is over. Now the players are discussing how to improve the game.

You are {player.name}. You were {player_role_display} on the {player.team} team.

Think about:
- How could the prompts be improved?
- What information was missing that would have helped you?
- Were there any confusing mechanics or unclear instructions?
- What would make the game more fun or strategic?

Give constructive feedback about the game design and prompts."""
            else:
                suggestion_context = f"""Round 2 of feedback discussion.

You are {player.name}. You were {player_role_display} on the {player.team} team.

Others have shared their feedback. You can:
- RESPOND to specific points others made
- Agree or disagree with their suggestions
- Build on their ideas
- Add new suggestions you thought of

What others said in this round:{prior_discussion}

Respond to the discussion (1-2 sentences)."""

            thinking, statement = llm_agent.get_player_statement(
                player=player,
                prompt="What suggestions do you have for improving the game, prompts, or mechanics? (1-2 sentences)" if round_num == 0 else "Respond to others' feedback or add new thoughts (1-2 sentences)",
                context=suggestion_context,
                max_tokens=120
            )

            print(f"  💭 {player.name} thinks: {thinking}")
            print(f"💬 {player.name}: {statement}\n")

            # Store statement for others to read
            setattr(player, f'_suggestion_round_{round_num}', statement)

            time.sleep(delay * 0.5)

        if round_num == 0:
            print()  # Extra spacing between rounds


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="ASSASSINS - LLM-powered Mafia game",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Play with default random events:
    python play.py

  Play with specific events:
    python play.py --zombie --ghost

  Play in CHAOS MODE (all events):
    python play.py --chaos
"""
    )

    parser.add_argument(
        "--zombie",
        action="store_true",
        help="Enable Zombie event (infected players rise from the dead)"
    )
    parser.add_argument(
        "--ghost",
        action="store_true",
        help="Enable Ghost event (dead players haunt the living)"
    )
    parser.add_argument(
        "--sleepwalker",
        action="store_true",
        help="Enable Sleepwalker event (players wander at night)"
    )
    parser.add_argument(
        "--insomniac",
        action="store_true",
        help="Enable Insomniac event (player sees others moving at night)"
    )
    parser.add_argument(
        "--gun-nut",
        action="store_true",
        help="Enable Gun Nut event (player fights back when attacked)"
    )
    parser.add_argument(
        "--suicidal",
        action="store_true",
        help="Enable Suicidal event (player may take their own life)"
    )
    parser.add_argument(
        "--drunk",
        action="store_true",
        help="Enable Drunk event (player's vote goes to random target)"
    )
    parser.add_argument(
        "--jester",
        action="store_true",
        help="Enable Jester event (player wins by getting lynched)"
    )
    parser.add_argument(
        "--priest",
        action="store_true",
        help="Enable Priest event (can resurrect one dead player)"
    )
    parser.add_argument(
        "--lovers",
        action="store_true",
        help="Enable Lovers event (two players die if one dies)"
    )
    parser.add_argument(
        "--bodyguard",
        action="store_true",
        help="Enable Bodyguard event (dies protecting someone)"
    )
    parser.add_argument(
        "--chaos",
        action="store_true",
        help="CHAOS MODE - enable ALL events at once!"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between game phases in seconds (default: 2.0)"
    )
    parser.add_argument(
        "--players",
        type=int,
        default=9,
        choices=range(5, 21),
        metavar="[5-20]",
        help="Number of players in the game (default: 9)"
    )

    args = parser.parse_args()

    # Generate player configurations based on number of players
    player_configs = generate_player_configs(args.players)

    try:
        # Initialize LLM agent
        console.print("[yellow]Initializing LLM agent...[/yellow]")
        llm_agent = LLMAgent()

        # Create game with event flags
        game = create_game(
            player_configs,
            enable_zombie=args.zombie,
            enable_ghost=args.ghost,
            enable_sleepwalker=args.sleepwalker,
            enable_insomniac=args.insomniac,
            enable_gun_nut=args.gun_nut,
            enable_suicidal=args.suicidal,
            enable_drunk=args.drunk,
            enable_jester=args.jester,
            enable_priest=args.priest,
            enable_lovers=args.lovers,
            enable_bodyguard=args.bodyguard,
            chaos_mode=args.chaos
        )

        # Run the game
        run_game(game, llm_agent, delay=args.delay)

    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        console.print("[yellow]Make sure to set ANTHROPIC_API_KEY in your .env file[/yellow]")
        return 1
    except KeyboardInterrupt:
        console.print("\n[yellow]Game interrupted by user[/yellow]")
        return 0
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
