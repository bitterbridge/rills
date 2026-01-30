# Rills - LLM-Powered Mafia Game 🎭

A Python implementation of the classic social deduction game Mafia (also known as Werewolf) where all players are controlled by Large Language Models (LLMs). Watch as AI characters with different personalities and roles interact, deceive, and deduce their way to victory!

## Features

- 🤖 **LLM-Powered Characters**: Each player is an AI agent powered by Claude with unique personalities
- 🎮 **Classic Mafia Gameplay**: Includes Mafia, Doctor, Detective, and Villager roles
- 🌙 **Day/Night Cycles**: Night actions (kills, protections, investigations) and day discussions/voting
- 💭 **Memory System**: Players remember events and use them to make decisions
- 🎨 **Rich CLI Interface**: Colorful terminal output using Rich library

## Roles

- **Mafia**: Eliminates villagers at night. Wins by outnumbering villagers.
- **Doctor**: Protects one person each night from elimination.
- **Detective**: Investigates one person each night to learn if they're Mafia.
- **Villager**: No special powers, but votes during the day to eliminate suspects.

## Installation

1. **Clone or navigate to the repository**:
   ```bash
   cd rills
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -e .
   ```

4. **Set up your API key**:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Anthropic API key:
     ```
     ANTHROPIC_API_KEY=your_actual_api_key_here
     ```
   - Get an API key from: https://console.anthropic.com/

## Usage

Run the game with:

```bash
python play.py
```

The game will:
1. Initialize 5 players with different roles and personalities
2. Run through night and day phases
3. Display each player's statements and votes
4. Continue until either the Mafia or Village wins

## Customizing the Game

Edit `rills/main.py` to customize the game:

```python
player_configs = [
    {
        "name": "Alice",
        "role": "Mafia",
        "personality": "Cunning and manipulative, pretends to be helpful"
    },
    # Add more players...
]
```

You can:
- Change player names and personalities
- Add more players (minimum 3 recommended)
- Adjust the role distribution
- Modify the delay between phases

## Game Flow

### Night Phase
1. **Mafia** votes on who to eliminate
2. **Doctor** chooses someone to protect
3. **Detective** investigates someone
4. Night actions are resolved

### Day Phase
1. All living players make statements about their suspicions
2. Players vote on who to eliminate
3. The player with the most votes is eliminated
4. Win conditions are checked

## Example Output

```
🎭 MAFIA - LLM Edition 🎭

┏━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Name   ┃ Personality                           ┃
┡━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Alice  │ Cunning and manipulative              │
│ Bob    │ Cautious and analytical               │
│ Carol  │ Bold and direct                       │
│ David  │ Friendly and trusting                 │
│ Eve    │ Suspicious and paranoid               │
└────────┴───────────────────────────────────────┘

============================================================
🌙 Night 1
============================================================

🔪 The Mafia is deciding who to eliminate...
💊 The Doctor is choosing who to protect...
🔍 The Detective is investigating...

--- Night Resolution ---
☠️  David was eliminated by the Mafia!
```

## Project Structure

```
rills/
├── rills/
│   ├── __init__.py
│   ├── game.py          # Game state and logic
│   ├── player.py        # Player class with memory
│   ├── roles.py         # Role definitions
│   ├── llm.py          # LLM integration (Anthropic Claude)
│   ├── phases.py       # Night and day phase logic
│   └── main.py         # Main game loop and CLI
├── play.py             # Entry point script
├── pyproject.toml      # Project dependencies
├── .env.example        # Example environment file
└── README.md           # This file
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## How It Works

Each player is an LLM agent with:
- **Role context**: Knowledge of their role and abilities
- **Personality**: A unique personality trait that influences behavior
- **Memory**: Remembers game events and uses them for decisions
- **Decision-making**: Makes choices based on context using Claude API

The LLM receives prompts like:
```
You are Alice.
Your personality: Cunning and manipulative
Your role: You are part of the Mafia...

Current phase: Day 2

What you remember:
- Bob was eliminated by the town on Day 1
- Someone was attacked but saved last night

Make a statement about what you think is happening...
```

## Notes

- The game uses the Claude 3.5 Sonnet model by default
- API costs depend on game length (typically a few cents per game)
- Players sometimes make surprising or irrational decisions - that's part of the fun!
- The game can be interrupted with Ctrl+C

## Future Ideas

- [ ] Add more roles (Sheriff, Godfather, Serial Killer, etc.)
- [ ] Web interface for easier observation
- [ ] Game replay/analysis tools
- [ ] Tournament mode with multiple games
- [ ] Configurable LLM parameters (temperature, model, etc.)
- [ ] Save game transcripts
- [ ] Support for other LLM providers

## License

MIT License
