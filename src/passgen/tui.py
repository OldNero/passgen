"""
src/passgen/tui.py
Single-pane dashboard TUI for passgen.
"""

import secrets
import string
import time
from typing import ClassVar

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Input,
    Label,
    Static,
)

try:
    from passgen.core import (
        HISTORY_FILE,
        MAX_HISTORY,
        build_pool,
        format_time_ago,
        generate_passwords,
        load_history,
        save_to_history,
    )
except ModuleNotFoundError:
    from core import (  # type: ignore
        HISTORY_FILE,
        MAX_HISTORY,
        build_pool,
        format_time_ago,
        generate_passwords,
        load_history,
        save_to_history,
    )

try:
    from passgen.picker import copy_to_clipboard
except ModuleNotFoundError:
    from picker import copy_to_clipboard  # type: ignore


# ── Strength helpers ──────────────────────────────────────────────────────────

_STRENGTH_COLORS = ["red", "dark_orange", "yellow", "green", "bright_green"]
_STRENGTH_LABELS = ["Very Weak", "Weak",    "Fair",   "Strong", "Very Strong"]


def _strength_score(pwd: str) -> int:
    classes = sum([
        any(c in string.ascii_lowercase for c in pwd),
        any(c in string.ascii_uppercase for c in pwd),
        any(c in string.digits          for c in pwd),
        any(c in string.punctuation     for c in pwd),
    ])
    if len(pwd) < 8:
        classes = max(0, classes - 1)
    return classes


def _strength_markup(pwd: str) -> str:
    score  = _strength_score(pwd)
    color  = _STRENGTH_COLORS[score]
    label  = _STRENGTH_LABELS[score]
    filled = "█" * (score + 1) * 2
    empty  = "░" * (4 - score) * 2
    return f"[{color}]{filled}{empty}[/{color}] [{color} bold]{label}[/{color} bold]"


# ── CSS ───────────────────────────────────────────────────────────────────────

CSS = """
/* ── Root ─────────────────────────────────────────────── */
Screen {
    background: #0b0b12;
    layers: base overlay;
}

/* ── Dashboard wrapper ────────────────────────────────── */
#dashboard {
    height: 1fr;
    padding: 0 2 1 2;
}

/* ── Branded header bar ────────────────────────────────── */
#brand-bar {
    height: 3;
    background: #0b0b12;
    padding: 0 1;
    dock: top;
}

#brand-title {
    width: 1fr;
    color: #7ee8fa;
    text-style: bold;
    padding: 1 0;
    content-align: left middle;
}

#brand-subtitle {
    width: auto;
    color: #2a2a45;
    padding: 1 0;
    content-align: right middle;
}

/* ── Section panels ───────────────────────────────────── */
.section {
    border: solid #1e1e35;
    background: #10101c;
    padding: 0 1 1 1;
    margin-bottom: 1;
}

.section-title {
    color: #5a5a80;
    text-style: bold;
    padding: 0;
    margin-bottom: 1;
    border-bottom: solid #1e1e35;
    width: 1fr;
    padding-bottom: 0;
}

/* ── Controls section ─────────────────────────────────── */
#controls-section {
    height: auto;
}

#controls-row-1 {
    height: 3;
    margin-bottom: 1;
}

#controls-row-2 {
    height: 3;
}

.ctrl-label {
    width: auto;
    color: #4a4a70;
    text-style: bold;
    padding: 1 1 0 0;
    content-align: left middle;
}

#length-input {
    width: 6;
    border: solid #1e1e35;
    background: #0b0b12;
    color: #e2e8ff;
    margin-right: 2;
}

#length-input:focus {
    border: solid #7ee8fa;
}

#count-input {
    width: 5;
    border: solid #1e1e35;
    background: #0b0b12;
    color: #e2e8ff;
    margin-right: 2;
}

#count-input:focus {
    border: solid #7ee8fa;
}

#comment-input {
    width: 1fr;
    border: solid #1e1e35;
    background: #0b0b12;
    color: #e2e8ff;
}

#comment-input:focus {
    border: solid #7ee8fa;
}

Checkbox {
    background: transparent;
    border: none;
    padding: 0 1 0 0;
    margin: 0;
    color: #3a3a58;
    height: 3;
}

Checkbox:hover { color: #7ee8fa; }
Checkbox.-on   { color: #a78bfa; }

#generate-btn {
    width: 20;
    background: #7ee8fa;
    color: #0b0b12;
    border: none;
    text-style: bold;
    margin-right: 1;
}

#generate-btn:hover  { background: #a78bfa; }
#generate-btn:focus  { background: #a78bfa; }

#copy-all-btn {
    width: 18;
    background: #1e1e35;
    color: #7ee8fa;
    border: solid #2a2a50;
    text-style: bold;
    margin-right: 1;
}

#copy-all-btn:hover  { background: #2a2a50; }

#clear-hist-btn {
    width: 18;
    background: #1e1e35;
    color: #ff6b6b;
    border: solid #2a2a35;
    text-style: bold;
}

#clear-hist-btn:hover { background: #ff6b6b; color: #0b0b12; }

/* ── Results section ──────────────────────────────────── */
#results-section {
    height: 1fr;
    min-height: 8;
}

#results-scroll {
    height: 1fr;
    background: transparent;
}

#results-empty {
    height: 1fr;
    color: #2a2a45;
    text-style: italic;
    content-align: center middle;
}

/* ── Password row ─────────────────────────────────────── */
.pwd-row {
    height: 3;
    padding: 0 1;
    margin-bottom: 0;
    background: #13131f;
    border-left: tall #2a2a45;
}

.pwd-row:hover {
    background: #1a1a2e;
    border-left: tall #7ee8fa;
}

.pwd-row.-copied {
    background: #0d2010;
    border-left: tall #22c55e;
}

.pwd-num {
    width: 4;
    color: #2a2a45;
    text-style: bold;
    content-align: left middle;
    padding: 1 0;
}

.pwd-text {
    width: 1fr;
    color: #e2e8ff;
    text-style: bold;
    content-align: left middle;
    padding: 1 0;
}

.pwd-strength {
    width: 22;
    content-align: right middle;
    padding: 1 1;
}

.pwd-hint {
    width: 14;
    color: #2a2a45;
    content-align: right middle;
    padding: 1 0;
}

/* ── History section ──────────────────────────────────── */
#history-section {
    height: 10;
}

#history-table {
    height: 1fr;
    background: transparent;
}

DataTable {
    background: transparent;
    border: none;
}

DataTable > .datatable--header {
    background: #10101c;
    color: #5a5a80;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #1e1e35;
    color: #7ee8fa;
}

DataTable > .datatable--hover {
    background: #16162a;
}

/* ── Action row ───────────────────────────────────────── */
#action-row {
    height: 3;
    margin-top: 0;
    padding: 0;
}

/* ── Status strip ─────────────────────────────────────── */
#status-strip {
    height: 1;
    background: #0b0b12;
    padding: 0 2;
    color: #3a3a58;
    dock: bottom;
    offset-y: -1;
}

/* ── Footer ───────────────────────────────────────────── */
Footer {
    background: #0d0d18;
    color: #3a3a58;
}
"""


# ── Password row widget ───────────────────────────────────────────────────────

class PasswordRow(Horizontal):
    """Clickable password row with strength indicator."""

    def __init__(self, index: int, password: str, **kwargs):
        super().__init__(**kwargs, classes="pwd-row")
        self.index    = index
        self.password = password

    def compose(self) -> ComposeResult:
        yield Label(f"{self.index}", classes="pwd-num")
        yield Label(self.password,   classes="pwd-text")
        yield Static(_strength_markup(self.password), classes="pwd-strength", markup=True)
        yield Label("↵ copy", classes="pwd-hint")

    def on_click(self) -> None:
        copy_to_clipboard(self.password)
        self.add_class("-copied")
        hint = self.query_one(".pwd-hint", Label)
        hint.update("✓ Copied!")
        hint.styles.color = "#22c55e"
        app = self.app
        if hasattr(app, "set_status"):
            app.set_status(f"✓  Copied to clipboard: {self.password}")
        self.set_timer(2.0, self._reset)

    def _reset(self) -> None:
        self.remove_class("-copied")
        hint = self.query_one(".pwd-hint", Label)
        hint.update("↵ copy")
        hint.styles.color = None


# ── Main app ──────────────────────────────────────────────────────────────────

class PassgenApp(App):
    """Passgen — single-pane dashboard."""

    CSS   = CSS
    TITLE = "Passgen"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("g",      "generate",  "Generate",  show=True),
        Binding("ctrl+c", "copy_top",  "Copy Top",  show=True),
        Binding("r",      "regenerate","Regenerate", show=True),
        Binding("q",      "quit",      "Quit",       show=True),
    ]

    def __init__(
        self,
        length:       int  = 16,
        count:        int  = 1,
        no_numbers:   bool = False,
        no_letters:   bool = False,
        no_specials:  bool = False,
        no_ambiguous: bool = False,
        comment:      str  = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._init_length       = length
        self._init_count        = count
        self._init_no_numbers   = no_numbers
        self._init_no_letters   = no_letters
        self._init_no_specials  = no_specials
        self._init_no_ambiguous = no_ambiguous
        self._init_comment      = comment
        self._last_passwords: list[str] = []

    # ── Layout ─────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:

        # ── Top brand bar ────────────────────────────────────────────────
        with Horizontal(id="brand-bar"):
            yield Label("⚿  PASSGEN", id="brand-title")
            yield Label("secure · fast · open source", id="brand-subtitle")

        # ── Main scrollable dashboard ────────────────────────────────────
        with ScrollableContainer(id="dashboard"):

            # Controls ────────────────────────────────────────────────────
            with Vertical(id="controls-section", classes="section"):
                yield Label(" SETTINGS", classes="section-title")

                # Row 1: Length / Count / Comment
                with Horizontal(id="controls-row-1"):
                    yield Label("Length", classes="ctrl-label")
                    yield Input(
                        value=str(self._init_length),
                        id="length-input",
                        restrict=r"[0-9]*",
                    )
                    yield Label("Count", classes="ctrl-label")
                    yield Input(
                        value=str(self._init_count),
                        id="count-input",
                        restrict=r"[0-9]*",
                    )
                    yield Label("Label", classes="ctrl-label")
                    yield Input(
                        value=self._init_comment,
                        placeholder="optional comment…",
                        id="comment-input",
                    )

                # Row 2: Exclusion toggles
                with Horizontal(id="controls-row-2"):
                    yield Checkbox("No Numbers",   value=self._init_no_numbers,   id="cb-nn")
                    yield Checkbox("No Letters",   value=self._init_no_letters,   id="cb-nl")
                    yield Checkbox("No Specials",  value=self._init_no_specials,  id="cb-ns")
                    yield Checkbox("No Ambiguous", value=self._init_no_ambiguous, id="cb-na")

            # Results ─────────────────────────────────────────────────────
            with Vertical(id="results-section", classes="section"):
                yield Label(" PASSWORDS", classes="section-title")
                with ScrollableContainer(id="results-scroll"):
                    yield Static(
                        "Press [bold cyan]G[/bold cyan] to generate passwords.",
                        id="results-empty",
                        markup=True,
                    )

            # History ─────────────────────────────────────────────────────
            with Vertical(id="history-section", classes="section"):
                yield Label(" RECENT HISTORY", classes="section-title")
                yield DataTable(id="history-table", cursor_type="row", show_cursor=True)

            # Action row ──────────────────────────────────────────────────
            with Horizontal(id="action-row"):
                yield Button("⚿  Generate",      id="generate-btn",  variant="primary")
                yield Button("⎘  Copy All",       id="copy-all-btn")
                yield Button("🗑  Clear History",  id="clear-hist-btn")

        yield Static("", id="status-strip")
        yield Footer()

    def on_mount(self) -> None:
        self._refresh_history()
        self.query_one("#length-input").focus()

    # ── Actions ────────────────────────────────────────────────────────────

    def action_generate(self) -> None:
        self._do_generate()

    def action_copy_top(self) -> None:
        if self._last_passwords:
            copy_to_clipboard(self._last_passwords[0])
            self.set_status(f"✓  Copied: {self._last_passwords[0]}")

    def action_regenerate(self) -> None:
        self._do_generate()

    # ── Status helper ──────────────────────────────────────────────────────

    def set_status(self, msg: str) -> None:
        try:
            self.query_one("#status-strip", Static).update(msg)
        except NoMatches:
            pass

    # ── Event handlers ─────────────────────────────────────────────────────

    @on(Button.Pressed, "#generate-btn")
    def on_generate(self) -> None:
        self._do_generate()

    @on(Button.Pressed, "#copy-all-btn")
    def on_copy_all(self) -> None:
        if not self._last_passwords:
            self.set_status("Nothing to copy — generate some passwords first.")
            return
        combined = "\n".join(self._last_passwords)
        copy_to_clipboard(combined)
        self.set_status(f"✓  Copied all {len(self._last_passwords)} passwords to clipboard.")

    @on(Button.Pressed, "#clear-hist-btn")
    def on_clear_history(self) -> None:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        self._refresh_history()
        self.set_status("History cleared.")

    @on(DataTable.RowSelected, "#history-table")
    def on_history_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#history-table", DataTable)
        row   = table.get_row(event.row_key)
        if row:
            pwd = str(row[1])
            copy_to_clipboard(pwd)
            self.set_status(f"✓  Copied from history: {pwd}")

    # ── Core logic ─────────────────────────────────────────────────────────

    def _do_generate(self) -> None:
        length_val  = self.query_one("#length-input",  Input).value.strip()
        count_val   = self.query_one("#count-input",   Input).value.strip()
        comment_val = self.query_one("#comment-input", Input).value.strip()

        try:
            length = max(1, int(length_val or "16"))
        except ValueError:
            length = 16

        try:
            count = max(1, min(50, int(count_val or "1")))
        except ValueError:
            count = 1

        no_numbers   = self.query_one("#cb-nn", Checkbox).value
        no_letters   = self.query_one("#cb-nl", Checkbox).value
        no_specials  = self.query_one("#cb-ns", Checkbox).value
        no_ambiguous = self.query_one("#cb-na", Checkbox).value

        try:
            records = generate_passwords(
                count=count,
                length=length,
                no_letters=no_letters,
                no_numbers=no_numbers,
                no_specials=no_specials,
                no_ambiguous=no_ambiguous,
                comment=comment_val,
            )
        except ValueError as e:
            self.set_status(f"✗  {e}")
            return

        save_to_history(records)
        passwords = [r["password"] for r in records]
        self._last_passwords = passwords

        # Rebuild results pane
        scroll = self.query_one("#results-scroll", ScrollableContainer)
        scroll.remove_children()
        for i, pwd in enumerate(passwords, 1):
            scroll.mount(PasswordRow(i, pwd))

        # Refresh history strip
        self._refresh_history()

        plural = "password" if count == 1 else "passwords"
        self.set_status(
            f"Generated {count} {plural}  ·  {length} chars  ·  "
            "click a row or press Ctrl+C to copy"
        )

    def _refresh_history(self) -> None:
        table   = self.query_one("#history-table", DataTable)
        history = load_history()

        table.clear(columns=True)
        table.add_columns("#", "Password", "Strength", "Created", "Comment")

        for i, item in enumerate(history, 1):
            pwd     = item.get("password", "")
            ts      = item.get("timestamp", 0)
            comment = item.get("comment") or "-"
            score   = _strength_score(pwd)
            bar     = "█" * (score + 1) * 2 + "░" * (4 - score) * 2
            label   = _STRENGTH_LABELS[score]
            table.add_row(str(i), pwd, f"{bar} {label}", format_time_ago(ts), comment)


# ── Entry point ───────────────────────────────────────────────────────────────

def run_tui(
    length:       int  = 16,
    count:        int  = 1,
    no_numbers:   bool = False,
    no_letters:   bool = False,
    no_specials:  bool = False,
    no_ambiguous: bool = False,
    comment:      str  = "",
) -> None:
    PassgenApp(
        length=length,
        count=count,
        no_numbers=no_numbers,
        no_letters=no_letters,
        no_specials=no_specials,
        no_ambiguous=no_ambiguous,
        comment=comment,
    ).run()
