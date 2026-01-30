# Architecture Documentation

## Overview

Rills is a social deduction game (inspired by Mafia/Werewolf) with AI-powered players. The architecture follows a **service-oriented design** with clear separation of concerns and structured data flow.

**Last Updated**: January 30, 2026
**Version**: 2.0 (After Refactoring Wave 2)

---

## Core Architecture Principles

### 1. Service-Oriented Design
Game logic is decomposed into specialized services, each handling a specific domain:
- **InformationService**: Manages what players know
- **ConversationService**: Handles discussions and statements
- **VoteService**: Manages voting logic
- **EffectService**: Applies game state changes
- **ContextBuilder**: Builds LLM prompts from game state

### 2. Immutable Event History
All game events are recorded in append-only structures:
- Conversations stored in `ConversationHistory`
- Votes stored in `VotingHistory`
- Information stored in `InformationStore`

### 3. Centralized State Management
Player state is managed through:
- **PlayerState**: Tracks active modifiers
- **PlayerModifier**: Represents temporary or permanent status effects
- **GameState**: Central game state with services

### 4. Effect-Based Mutations
State changes flow through the EffectService:
- Events return `Effect` objects
- Effects are batched and applied atomically
- No direct state mutations outside the service layer

---

## Project Structure

```
rills/
├── game.py                 # GameState - central game state
├── player.py               # Player dataclass
├── roles.py                # Role definitions
├── phases.py               # PhaseManager - orchestrates game flow
├── llm.py                  # LLM interface (Claude)
├── main.py                 # Game creation and display
├── protocols.py            # Type protocols (LLMAgentProtocol)
├── types.py                # Type definitions (PlayerConfig, GameConfig)
│
├── models/                 # Data models
│   ├── information.py      # Information, Visibility, InfoCategory
│   ├── player_state.py     # PlayerState, PlayerModifier
│   ├── knowledge.py        # KnowledgeState
│   ├── conversation.py     # Statement, ConversationRound, ConversationHistory
│   ├── voting.py           # Vote, VoteResult
│   └── actions.py          # NightResult, DayResult
│
├── services/               # Service layer
│   ├── information_service.py    # Manages what players know
│   ├── conversation_service.py   # Manages discussions
│   ├── vote_service.py           # Manages voting
│   ├── effect_service.py         # Applies state changes
│   ├── context_service.py        # Builds LLM context (ContextBuilder)
│   ├── prompt_templates.py       # LLM prompt templates
│   └── player_state_service.py   # DEPRECATED - use models/player_state.py
│
└── events/                 # Event modifiers (game modes)
    ├── base.py             # EventModifier base class
    ├── drunk.py            # Drunk modifier (random speech)
    ├── zombie.py           # Zombie infection (rises after death)
    ├── ghost.py            # Ghost haunting (speaks after death)
    ├── jester.py           # Jester win condition (win if lynched)
    ├── priest.py           # Resurrection ability
    ├── lovers.py           # Lover connection (die together)
    ├── bodyguard.py        # Protection ability (self-sacrifice)
    ├── sleepwalker.py      # Sleepwalker modifier (wanders at night)
    ├── insomniac.py        # Insomniac sighting (sees activity)
    ├── gun_nut.py          # Counter-attack ability (shoot attacker)
    └── suicidal.py         # Suicidal villager (commits suicide)
```

---

## Key Components

### GameState

Central game state that holds all game data:

```python
@dataclass
class GameState:
    players: list[Player]
    day_number: int
    phase: str

    # Services
    info_service: InformationService
    conversation_service: ConversationService
    vote_service: VoteService
    effect_service: EffectService
    context_builder: ContextBuilder

    # State tracking
    player_states: dict[str, PlayerState]
    event_registry: Optional[EventRegistry]

# Note: RoleInfo is defined as TypedDict in roles.py for better type safety
class RoleInfo(TypedDict):
    name: str
    team: str
    description: str
    night_action: bool
```

**Key Methods**:
- `get_alive_players()` - Filter to living players
- `eliminate_player()` - Handle player death
- `check_win_condition()` - Determine if game is over
- `advance_phase()` - Move to next phase

### PlayerState & PlayerModifier

Centralized player state management:

```python
@dataclass
class PlayerModifier:
    type: str                           # e.g., "drunk", "zombie", "protected"
    source: str                         # What created this (e.g., "mad_scientist", "event:zombie")
    active: bool = True                 # Whether modifier is active
    data: dict[str, Any] = {}           # Optional modifier data
    expires_on: Optional[int] = None    # Day number when expires, None = permanent
    applied_on: int = 0                 # Day number when applied

    def is_expired(self, current_day: int) -> bool
    def deactivate()

@dataclass
class PlayerState:
    modifiers: list[PlayerModifier]

    def has_modifier(self, type: str) -> bool
    def add_modifier(self, modifier: PlayerModifier)
    def remove_modifier(self, type: str)
    def get_modifier(self, type: str) -> Optional[PlayerModifier]
    def cleanup_expired_modifiers(self, current_day: int)
```

**Common Modifiers**:
- **Temporary**: `drunk` (expires day+1), `protected` (expires day+1), `insomniac` (expires day+1), `sleepwalker` (expires day+1)
- **Permanent**: `zombie`, `ghost`, `jester`, `priest`, `lover`, `bodyguard`, `gun_nut`, `suicidal`, `vigilante_used`
- **With Data**: `priest` (resurrections), `lover` (partner), `bodyguard` (active state)
- **Mad Scientist Effects**: Can create any of the above modifiers randomly

### PhaseManager

Orchestrates game flow through phases:

```python
class PhaseManager:
    def run_night_phase(game: GameState) -> None
    def run_day_phase(game: GameState) -> None

    # Night actions (extracted methods)
    def _assassins_action(game) -> Optional[Player]
    def _doctor_action(game) -> Optional[Player]
    def _detective_action(game) -> Optional[str]
    def _vigilante_action(game) -> Optional[Player]
    def _mad_scientist_action(game) -> None
    def _apply_night_results(game, result: NightResult)

    # Day actions (extracted methods)
    def _display_game_summary(game, alive_players)
    def _conduct_discussion_rounds(game, alive_players, num_rounds)
    def _conduct_lynch_vote(game, alive_players)
    def _process_lynch_result(game, vote_result)
```

**Phase Flow**:
1. **Night Phase**: Assassins → Doctor → Detective → Vigilante → Resolution
2. **Day Phase**: Summary → Discussion → Voting → Lynch

### Services

#### InformationService

Manages what players know:

```python
class InformationService:
    def reveal_to_player(player_name, info: Information)
    def reveal_to_team(team, info: Information)
    def reveal_to_all(info: Information)
    def reveal_death(player_name, role, reason)
    def build_context_for(player_name, categories) -> str
```

**Information Types** (InfoCategory):
- `DEATH` - Player eliminations
- `ROLE` - Role reveals
- `INVESTIGATION` - Detective results
- `OBSERVATION` - Night observations
- `ACTION` - Player actions
- `GENERAL` - General game info

#### ConversationService

Manages discussions:

```python
class ConversationService:
    def conduct_round(participants, phase, round_number, day_number, get_statement_func)
    def get_recent_statements(player_name, count=5) -> list[Statement]
    def get_statements_in_phase(phase, day_number=None) -> list[Statement]
    def get_statements_by(player_name) -> list[Statement]
    def format_round_for_display(round: ConversationRound) -> str
```

**Statement Structure**:
```python
@dataclass
class Statement:
    speaker: str
    content: str
    thinking: str          # Internal reasoning
    round_number: int
    day_number: int
    phase: str
```

#### VoteService

Manages voting:

```python
class VoteService:
    def conduct_vote(voters, candidates, context_func) -> VoteResult
    def get_voting_pattern(player_name) -> list[str]
    def analyze_voting_alignment(player1, player2) -> float
```

**Vote Result**:
```python
@dataclass
class VoteResult:
    votes: list[Vote]
    winner: Optional[str]
    is_tie: bool

    def get_votes_for(candidate) -> int
    def get_voters_for(candidate) -> list[str]
    def format_breakdown() -> str
```

#### ContextBuilder

Builds LLM context from game state:

```python
class ContextBuilder:
    def build_for_night_kill(player, game, targets) -> str
    def build_for_protection(player, game, targets, last_protected) -> str
    def build_for_investigation(player, game, targets) -> str
    def build_for_discussion(player, game, round_num, recent_statements) -> str
    def build_for_vote(player, game, candidates) -> str
    def build_system_context(player, game) -> str
```

**Template-Based**: Uses `prompt_templates.py` for consistent, tunable prompts.

---

## Data Flow

### Night Phase Flow

```
┌─────────────────┐
│  Night Start    │
│  - Reset flags  │
│  - Events fire  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│ Collect Actions │────▶│ NightResult  │
│  - Assassins    │     │  - targets   │
│  - Doctor       │     │  - deaths    │
│  - Detective    │     │  - counters  │
│  - Vigilante    │     │  - mad sci   │
│  - Mad Scientist│     └──────────────┘
└────────┬────────┘              │
         │                       │
         ▼                       ▼
┌─────────────────────────────────┐
│   Apply Night Results           │
│   - Check Gun Nut counters      │
│   - Check Doctor protection     │
│   - Process eliminations        │
│   - Update InformationService   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Night End     │
│  - Events fire  │
│  - Win check    │
└─────────────────┘
```

### Day Phase Flow

```
┌─────────────────┐
│  Day Start      │
│  - Display      │
│    summary      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────┐
│   Discussion    │────▶│  DayResult   │
│   (2 rounds)    │     │  - rounds    │
│  - Statements   │     │  - votes     │
│  - Ghost posts  │     │  - eliminated│
└────────┬────────┘     └──────────────┘
         │                       │
         ▼                       │
┌─────────────────┐             │
│     Voting      │             │
│  - Collect      │             │
│  - Tally        │─────────────┘
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Lynch Result   │
│  - Eliminate    │
│  - Win check    │
└─────────────────┘
```

### Event System Flow

```
┌─────────────┐
│   Event     │
│  Trigger    │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│  Event Handler      │
│  on_night_start()   │
│  on_night_end()     │
│  on_player_elim()   │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Return Effects     │
│  [Effect(...),      │
│   Effect(...)]      │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  EffectService      │
│  apply_batch()      │
│  - Modify state     │
│  - Update modifiers │
└─────────────────────┘
```

---

## Common Patterns

### Adding a New Event Modifier

1. **Create event file**: `rills/events/my_event.py`

```python
from .base import EventModifier
from ..models.player_state import PlayerModifier

class MyEvent(EventModifier):
    def setup_game(self, game: "GameState") -> None:
        """Initialize event state."""
        # Select affected players
        player = random.choice(available_players)

        # Dual-write pattern (backward compatibility)
        player.my_flag = True
        player.add_modifier(game, PlayerModifier(type="my_modifier"))

    def on_night_start(self, game: "GameState") -> None:
        """Handle night start."""
        pass

    def on_night_end(self, game: "GameState") -> None:
        """Handle night end."""
        pass
```

2. **Register event**: `rills/events/__init__.py`

```python
from .my_event import MyEvent

__all__ = [..., "MyEvent"]
```

3. **Add to game setup**: Check in `main.py` or game config

### Adding a New Modifier

```python
# In event setup or role action
player.add_modifier(
    game,
    PlayerModifier(
        type="my_modifier",
        source="my_event",                  # Required: what created this
        data={"key": "value"},              # Optional data
        expires_on=game.day_number + 1,     # None = permanent
        applied_on=game.day_number          # When it was applied
    )
)

# Checking modifier
if player.has_modifier(game, "my_modifier"):
    modifier = player.get_modifier(game, "my_modifier")
    value = modifier.data.get("key")

# Cleanup expired modifiers
state = player.get_state(game)
state.cleanup_expired_modifiers(game.day_number)
```

### Accessing Game State

**DO** ✅:
```python
# Use services
info = game.info_service.build_context_for(player.name)

# Use PlayerState
if player.has_modifier(game, "drunk"):
    # ...

# Use structured data
statements = game.conversation_service.get_recent_statements(player.name)
```

**DON'T** ❌:
```python
# Don't directly access deprecated fields
if player.memories:  # DEPRECATED

# Don't mutate state directly outside services
player.alive = False  # Use game.eliminate_player()

# Don't bypass modifiers
player.is_drunk = True  # Use player.add_modifier()
```

---

## Migration from Old Code

### Player Memories → InformationService

**Before**:
```python
player.add_memory("Bob was eliminated")
context = "\n".join(player.memories)
```

**After**:
```python
# Information is automatically added via game.eliminate_player()
context = game.context_builder.build_for_vote(player, game, candidates)
```

### Boolean Flags → PlayerModifier

**Before**:
```python
player.is_drunk = True
if player.is_drunk:
    # ...
```

**After**:
```python
player.add_modifier(game, PlayerModifier(type="drunk", expires_on_day=game.day_number + 1))
if player.has_modifier(game, "drunk"):
    # ...
```

### Direct State Changes → Effects

**Before**:
```python
player.role = Role.ZOMBIE
player.alive = False
```

**After**:
```python
effects = [
    Effect.change_role(player.name, Role.ZOMBIE),
    Effect.kill_player(player.name)
]
game.effect_service.apply_batch(effects, game.player_states)
```

---

## Performance Considerations

### Memory Usage
- **InformationStore**: O(n×m) where n=players, m=information items
- **ConversationHistory**: O(r×p) where r=rounds, p=players
- **PlayerState**: O(p×m) where p=players, m=modifiers per player

### Time Complexity
- **LLM calls**: Dominant factor (seconds per call)
- **Game logic**: O(n) for most operations
- **Information retrieval**: O(m) with category filtering

### Optimization Tips
1. Use category filters in `build_context_for()`
2. Limit `get_recent_statements()` with `limit` parameter
3. Clean up expired modifiers via `cleanup_expired_modifiers()`
4. Batch LLM calls when possible (not implemented yet)

---

## Testing Strategy

### Unit Tests
- **Models**: Test data structures (`test_models.py`)
- **Services**: Test service logic (`test_services.py`)
- **Events**: Test event behavior (`test_events.py`)

### Integration Tests
- **Game flow**: Test complete games (`test_integration.py`)
- **Phase transitions**: Test night/day cycles
- **Win conditions**: Test all victory paths

### Test Utilities
```python
# Create test game
game = create_game(...)

# Create test player
player = Player(name="Test", role=Role.VILLAGER, ...)

# Mock LLM
class MockLLM:
    def get_player_choice(self, ...):
        return "Test", "Because..."
```

---

## Development Tools

### Linting and Type Checking

The project uses a comprehensive linting setup:

```bash
# Format code with black
black rills/ tests/

# Check linting with ruff
ruff check rills/ tests/

# Auto-fix linting issues
ruff check --fix rills/ tests/

# Type checking with mypy
mypy rills/
```

**Configuration** (in `pyproject.toml`):
- **black**: Line length 100, Python 3.11+ target
- **ruff**: Import sorting, style checks, bug detection (E/W/F/I/B/C4/UP rules)
- **mypy**: Basic type safety with lenient settings for gradual adoption

**Pre-commit Workflow**:
```bash
# Run all checks
ruff check rills/ tests/ && mypy rills/ && pytest tests/
```

### Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=rills

# Run specific test file
pytest tests/test_roles.py

# Run in quiet mode
pytest tests/ -q
```

**Test Structure**:
- `tests/test_roles.py` - Role definitions and info
- `tests/test_game.py` - GameState and core mechanics
- `tests/test_events.py` - Event modifier behaviors
- `tests/test_services.py` - Service layer logic

---

## Future Enhancements

### Potential Improvements
1. **Async LLM calls**: Parallel LLM requests for better performance
2. **Event effect system**: All events return Effects (partially done)
3. **Replay system**: Serialize and replay games
4. **Web interface**: Move from CLI to web UI
5. **Multiple LLM support**: Support different LLM providers
6. **Advanced analytics**: Track player behavior patterns

### Extension Points
- **New roles**: Add to `roles.py` ROLE_DESCRIPTIONS and Role enum
  - Current roles: Assassins, Doctor, Detective, Vigilante, Mad Scientist, Zombie, Villager
- **New events**: Add to `events/` directory
  - Current events: Drunk, Zombie, Ghost, Jester, Priest, Lovers, Bodyguard, Sleepwalker, Insomniac, Gun Nut, Suicidal
- **New services**: Add to `services/` directory
- **Custom LLM agents**: Implement `LLMAgentProtocol` in `protocols.py`

---

## Troubleshooting

### Common Issues

**"Player has no modifier"**
- Check if modifier was added: `player.add_modifier(game, ...)`
- Verify modifier type string matches exactly
- Ensure game parameter is passed to `has_modifier()`

**"Deprecated memories warning"**
- Use `InformationService` instead of `player.memories`
- Use `ContextBuilder` to build LLM context

**"Information not visible to player"**
- Check `Visibility` setting on Information
- Verify player team/role matches visibility criteria

**"LLM context too long"**
- Use category filters in `build_context_for()`
- Limit recent statements with `limit` parameter
- Review prompt templates for excessive length

---

## References

- **Refactoring Plan**: See `REFACTORING_WAVE_2.md`
- **Migration Guide**: See `MIGRATION_GUIDE.md` (TODO)
- **Test Suite**: See `tests/` directory
- **Type Definitions**: See `protocols.py` and `types.py`
