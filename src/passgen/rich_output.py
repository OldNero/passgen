"""
src/passgen/rich_output.py
Rich-styled display helpers for non-interactive passgen output.
"""

import string
import time

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich import box

console = Console()

# ── Colour palette ────────────────────────────────────────────────────────────
ACCENT   = "bold cyan"
DIM      = "dim white"
SUCCESS  = "bold green"
WARNING  = "bold yellow"
ERROR_C  = "bold red"
HIST_HDR = "bold magenta"

# Strength thresholds (0-4 character classes)
_STRENGTH_COLORS = ["red", "dark_orange", "yellow", "green", "bright_green"]
_STRENGTH_LABELS = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _format_time_ago(timestamp: float) -> str:
    if not timestamp:
        return "unknown"
    diff = max(0, int(time.time() - timestamp))
    if diff < 60:
        return "just now"
    elif diff < 120:
        return "1 min ago"
    elif diff < 3600:
        return f"{diff // 60} min ago"
    elif diff < 7200:
        return "1 hour ago"
    elif diff < 86400:
        return f"{diff // 3600} hr ago"
    elif diff < 172800:
        return "yesterday"
    else:
        return f"{diff // 86400} days ago"


def _strength_score(password: str) -> int:
    """Return 0-4 based on character class diversity + length bonus."""
    classes = 0
    if any(c in string.ascii_lowercase for c in password):
        classes += 1
    if any(c in string.ascii_uppercase for c in password):
        classes += 1
    if any(c in string.digits for c in password):
        classes += 1
    if any(c in string.punctuation for c in password):
        classes += 1
    # Penalise very short passwords
    if len(password) < 8:
        classes = max(0, classes - 1)
    return classes


def _strength_bar(password: str) -> str:
    score = _strength_score(password)
    color = _STRENGTH_COLORS[score]
    label = _STRENGTH_LABELS[score]
    bar_filled = "█" * (score + 1) * 2
    bar_empty  = "░" * (4 - score) * 2
    return f"[{color}]{bar_filled}{bar_empty} {label}[/{color}]"


# ── Public display functions ──────────────────────────────────────────────────

def print_passwords(passwords: list[str]) -> None:
    """Display a rich panel of generated passwords with strength bars."""
    if not passwords:
        return

    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold white", justify="right")   # index
    grid.add_column(style="bold bright_cyan", no_wrap=True) # password
    grid.add_column()                                       # strength

    for i, pwd in enumerate(passwords, 1):
        grid.add_row(
            f"[dim]{i}[/dim]",
            pwd,
            _strength_bar(pwd),
        )

    count = len(passwords)
    title_text = (
        f"[bold cyan]⚿  Generated {'Password' if count == 1 else f'{count} Passwords'}[/bold cyan]"
    )
    panel = Panel(
        grid,
        title=title_text,
        border_style="cyan",
        padding=(1, 2),
        expand=False,
    )
    console.print()
    console.print(panel)
    console.print()


def print_history_table(history: list[dict]) -> None:
    """Display a rich-styled history table."""
    if not history:
        console.print(
            Panel(
                Align.center("[dim]No password history found.[/dim]"),
                border_style="dim",
                title="[bold magenta]⌚  History[/bold magenta]",
            )
        )
        return

    table = Table(
        box=box.ROUNDED,
        border_style="bright_black",
        header_style="bold magenta",
        show_lines=False,
        expand=False,
        title=f"[bold magenta]⌚  Stored Passwords[/bold magenta]  [dim]({len(history)} entries)[/dim]",
        title_justify="left",
    )
    table.add_column("#",        style="dim",               width=4,  justify="right")
    table.add_column("Password", style="bold bright_cyan",  min_width=16)
    table.add_column("Strength", min_width=20)
    table.add_column("Created",  style="yellow",            min_width=12)
    table.add_column("Comment",  style="italic green",      min_width=10)

    for i, item in enumerate(history, 1):
        pwd     = item.get("password", "")
        ts      = item.get("timestamp", 0)
        comment = item.get("comment") or "-"
        t_str   = _format_time_ago(ts)
        table.add_row(str(i), pwd, _strength_bar(pwd), t_str, comment)

    console.print()
    console.print(table)
    console.print()


def print_success(message: str) -> None:
    console.print(f"[{SUCCESS}]✓[/] {message}")


def print_error(message: str) -> None:
    console.print(f"[{ERROR_C}]✗ {message}[/]")


def print_info(message: str) -> None:
    console.print(f"[{DIM}]{message}[/]")


def print_cleared() -> None:
    console.print(
        Panel(
            Align.center("[bold green]✓  Password history cleared.[/bold green]"),
            border_style="green",
            padding=(0, 4),
        )
    )
