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
        console.print(f"  {status} {player.name} - {player.role.value} ({player.team})")


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
                    event_explanations.append("🧟 ZOMBIE: One player is infected. If they die, they'll rise as a zombie and attack a villager!")
                elif event.name == "Ghost Mode":
                    event_explanations.append("👻 GHOST: Dead players may return as ghosts to haunt the living!")
                elif event.name == "Sleepwalker Mode":
                    event_explanations.append("🌙 SLEEPWALKER: Someone sleepwalks at night and may be spotted by others!")
                elif event.name == "Gun Nut Mode":
                    event_explanations.append("🔫 GUN NUT: One player keeps a gun and will fight back if attacked!")
                elif event.name == "Suicidal Mode":
                    event_explanations.append("💀 SUICIDAL: One player is struggling with dark thoughts and may take their own life!")
                elif event.name == "Drunk Mode":
                    event_explanations.append("🍺 DRUNK: One player is drunk. Their vote will go to a RANDOM player instead of their intended target!")
                elif event.name == "Jester Mode":
                    event_explanations.append("🃏 JESTER: One player is a Jester who WINS if they get lynched. If the Jester is executed, they win and the game ends!")
                elif event.name == "Priest Mode":
                    event_explanations.append("🙏 PRIEST: One player is a Priest who can resurrect ONE dead player during a day phase!")
                elif event.name == "Lovers Mode":
                    event_explanations.append("💕 LOVERS: Two players are secretly in love. If one dies, the other will die of heartbreak!")
                elif event.name == "Bodyguard Mode":
                    event_explanations.append("🛡️  BODYGUARD: One player can protect someone but will DIE IN THEIR PLACE if attacked!")

            for explanation in event_explanations:
                print(f"{explanation}\n")

            print("These are all legitimate game mechanics. Keep them in mind!\n")
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
    role_summary = "\n".join([
        f"  - {p.name} was {p.role.value} ({'alive' if p.alive else 'dead'})"
        for p in game.players
    ])

    for player in game.players:
        postgame_context = f"""The game is over. The {game.winner} team won.

==== CRITICAL: YOUR ACTUAL ROLE ====
You are {player.name}.
Your ACTUAL role was: {player.role.value}
You were on the {player.team} team.
You are {'ALIVE' if player.alive else 'DEAD'}.

==== ALL PLAYER ROLES (REVEALED) ====
{role_summary}

==== WHAT YOU CAN DO NOW ====
Now you can speak freely about:
- What YOUR ACTUAL ROLE ({player.role.value}) was and how you played it
- What you were thinking during the game
- What actually happened vs what you thought was happening
- Call out people who lied or fooled you
- Celebrate your win or complain about your loss
- Talk about other players' strategies

IMPORTANT: Be honest about YOUR ACTUAL ROLE ({player.role.value}). Don't claim to be a different role!
ROLE TERMINOLOGY: Use exact role names - Doctor (not Healer), Detective (not Investigator), Vigilante, Assassins (not Mafia)."""

        thinking, statement = llm_agent.get_player_statement(
            player=player,
            prompt=f"The game is over. You were {player.role.value}. What do you want to say about how the game went? (2-3 sentences max)",
            context=postgame_context,
            max_tokens=150
        )

        alive_marker = "" if player.alive else " 💀"
        ghost_marker = " 👻" if player.is_ghost else ""
        print(f"  💭 {player.name} thinks: {thinking}")
        print(f"💬 {player.name}{alive_marker}{ghost_marker} ({player.role.value}): {statement}\n")
        time.sleep(delay * 0.5)  # Shorter delay for postgame


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

    args = parser.parse_args()

    # Game configuration - roles and personalities will be randomly assigned
    player_configs = [
        {
            "name": "Alice",
            "role": "Assassins",
            "personality": "Cunning and manipulative, pretends to be helpful"
        },
        {
            "name": "Bob",
            "role": "Assassins",
            "personality": "Aggressive and intimidating, tries to control the conversation"
        },
        {
            "name": "Carol",
            "role": "Doctor",
            "personality": "Cautious and analytical, tries to protect the innocent"
        },
        {
            "name": "David",
            "role": "Detective",
            "personality": "Bold and direct, speaks their mind"
        },
        {
            "name": "Eve",
            "role": "Vigilante",
            "personality": "Suspicious and paranoid, questions everything"
        },
        {
            "name": "Frank",
            "role": "Villager",
            "personality": "Friendly and trusting, maybe too trusting"
        },
        {
            "name": "Grace",
            "role": "Villager",
            "personality": "Logical and methodical, follows evidence"
        },
        {
            "name": "Henry",
            "role": "Villager",
            "personality": "Nervous and anxious, easily flustered under pressure"
        },
        {
            "name": "Iris",
            "role": "Zombie",
            "personality": "Quiet and reserved, keeps to themselves"
        },
    ]

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
