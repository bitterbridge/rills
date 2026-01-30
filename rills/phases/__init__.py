"""Phase management - orchestrates night and day phases.

This package consolidates phase-related logic that was previously in a single phases.py file:
- night.py: Night phase actions (assassins, doctor, detective, vigilante, mad scientist)
- day.py: Day phase discussions and voting
- utils.py: Shared utilities like speaking order
"""

from typing import TYPE_CHECKING

from ..game import GameState
from .day import DayPhaseHandler
from .night import NightPhaseHandler

if TYPE_CHECKING:
    from ..llm import LLMAgent


class PhaseManager:
    """Manages the different phases of the game.

    This class delegates to specialized handlers for night and day phases,
    improving code organization and maintainability.
    """

    def __init__(self, llm_agent: "LLMAgent") -> None:
        """Initialize the phase manager."""
        self.llm = llm_agent
        self.night_handler = NightPhaseHandler(llm_agent)
        self.day_handler = DayPhaseHandler(llm_agent)
        self._last_night_deaths: list[str] = []  # Track deaths between phases

    def run_night_phase(self, game: GameState) -> None:
        """Execute the night phase where special roles take actions."""
        # Run night phase and capture who died
        deaths = self.night_handler.run_night_phase(game)
        # Store deaths for day phase revelations
        self._last_night_deaths = deaths

    def run_day_phase(self, game: GameState) -> None:
        """Execute the day phase where players discuss and vote."""
        # Pass night deaths to day phase for revelations
        self.day_handler.run_day_phase(game, self._last_night_deaths)
        # Clear deaths after they've been revealed
        self._last_night_deaths = []


# Export public interface
__all__ = ["PhaseManager"]
