"""Formatting utilities for game output."""


def h1(text: str) -> str:
    """Format a level 1 header."""
    return f"\n# {text}\n"


def h2(text: str) -> str:
    """Format a level 2 header."""
    return f"\n## {text}\n"


def h3(text: str) -> str:
    """Format a level 3 header."""
    return f"\n### {text}\n"


def h4(text: str) -> str:
    """Format a level 4 header."""
    return f"\n#### {text}\n"


def h5(text: str) -> str:
    """Format a level 5 header."""
    return f"\n##### {text}\n"


def separator(width: int = 60) -> str:
    """Create a visual separator line."""
    return f"{'=' * width}"


def night_header(night_num: int) -> str:
    """Format a night phase header."""
    return f"{separator()}\n🌙 Night {night_num}\n{separator()}"


def day_header(day_num: int) -> str:
    """Format a day phase header."""
    return f"{separator()}\n☀️  Day {day_num}\n{separator()}"
