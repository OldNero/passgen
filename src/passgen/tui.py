"""
src/passgen/tui.py
Full-screen Textual TUI for passgen.
"""

import secrets
import string
import time
from pathlib import Path
from typing import ClassVar

from textual import on, work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.css.query import NoMatches
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
    TabbedContent,
    TabPane,
)

try:
    from passgen.core import (
        AMBIGUOUS,
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
        AMBIGUOUS,
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


# ── CSS ───────────────────────────────────────────────────────────────────────
CSS = """
Screen {
    background: #0d0d14;
}

/* ── Header / Footer ─────────────────────────────────── */
Header {
    background: #0d0d14;
    color: #7ee8fa;
    text-style: bold;
    height: 3;
}

Footer {
    background: #12121f;
    color: #555577;
}

/* ── Layout containers ───────────────────────────────── */
#layout {
    layout: horizontal;
    height: 1fr;
    padding: 0 1;
}

#left-panel {
    width: 32;
    min-width: 28;
    padding: 0 1 1 1;
    background: #12121f;
    border: solid #1e1e35;
    border-title-color: #7ee8fa;
    border-title-style: bold;
}

#right-panel {
    width: 1fr;
    padding: 0 1 1 1;
    background: #0d0d14;
    border: solid #1e1e35;
    border-title-color: #a78bfa;
    border-title-style: bold;
    margin-left: 1;
}

/* ── Controls (left panel) ───────────────────────────── */
.section-label {
    color: #7ee8fa;
    text-style: bold;
    margin-top: 1;
    margin-bottom: 0;
}

.sub-label {
    color: #555577;
    margin-bottom: 0;
}

.length-row {
    layout: horizontal;
    height: 3;
    margin-top: 0;
    margin-bottom: 0;
}

#length-input {
    width: 6;
    border: solid #2a2a45;
    background: #0d0d14;
    color: #e2e8ff;
}

#length-input:focus {
    border: solid #7ee8fa;
}

#length-display {
    width: 1fr;
    padding: 1 1;
    color: #555577;
    text-align: right;
}

#count-input {
    width: 6;
    border: solid #2a2a45;
    background: #0d0d14;
    color: #e2e8ff;
}

#count-input:focus {
    border: solid #7ee8fa;
}

#comment-input {
    width: 1fr;
    border: solid #2a2a45;
    background: #0d0d14;
    color: #e2e8ff;
    margin-top: 0;
}

#comment-input:focus {
    border: solid #7ee8fa;
}

Checkbox {
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    color: #a0aabb;
}

Checkbox:hover {
    color: #e2e8ff;
    background: #1e1e35;
}

Checkbox.-on {
    color: #7ee8fa;
}

/* ── Buttons ─────────────────────────────────────────── */
#generate-btn {
    margin-top: 1;
    width: 1fr;
    background: #7ee8fa;
    color: #0d0d14;
    border: none;
    text-style: bold;
}

#generate-btn:hover {
    background: #a78bfa;
    color: #0d0d14;
}

#generate-btn:focus {
    background: #a78bfa;
}

#clear-hist-btn {
    margin-top: 1;
    width: 1fr;
    background: #1e1e35;
    color: #ff6b6b;
    border: solid #ff6b6b;
    text-style: bold;
}

#clear-hist-btn:hover {
    background: #ff6b6b;
    color: #0d0d14;
}

/* ── Tabs ────────────────────────────────────────────── */
TabbedContent {
    height: 1fr;
}

TabPane {
    padding: 1 0 0 0;
    background: #0d0d14;
}

/* ── Password result list ────────────────────────────── */
#results-scroll {
    height: 1fr;
    background: #0d0d14;
}

.pwd-row {
    layout: horizontal;
    height: 3;
    padding: 0 1;
    margin-bottom: 1;
    background: #12121f;
    border: solid #1e1e35;
    border-left: solid #2a2a45 3;
}

.pwd-row:hover {
    border-left: solid #7ee8fa 3;
    background: #1a1a2e;
}

.pwd-row.-copied {
    border-left: solid #22c55e 3;
    background: #0f2620;
}

.pwd-idx {
    width: 4;
    padding: 1 1;
    color: #3a3a55;
    text-style: bold;
}

.pwd-text {
    width: 1fr;
    padding: 1 0;
    color: #e2e8ff;
    text-style: bold;
}

.pwd-strength {
    width: 20;
    padding: 1 1;
    text-align: right;
}

.pwd-copy-hint {
    width: 16;
    padding: 1 0;
    color: #3a3a55;
    text-align: right;
}

/* ── History DataTable ───────────────────────────────── */
#history-table {
    height: 1fr;
    background: #0d0d14;
}

DataTable {
    background: #0d0d14;
    border: solid #1e1e35;
}

DataTable > .datatable--header {
    background: #12121f;
    color: #a78bfa;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: #1e1e35;
    color: #7ee8fa;
}

DataTable > .datatable--hover {
    background: #1a1a2e;
}

/* ── Status bar ──────────────────────────────────────── */
#status-bar {
    height: 1;
    background: #12121f;
    padding: 0 2;
    color: #555577;
    dock: bottom;
}

/* ── Empty state ──────────────────────────────────────── */
#empty-state {
    height: 1fr;
    content-align: center middle;
    color: #2a2a45;
    text-style: italic;
}
"""


# ── Strength helpers ──────────────────────────────────────────────────────────

_STRENGTH_COLORS = ["red", "dark_orange", "yellow", "green", "bright_green"]
_STRENGTH_LABELS = ["Very Weak", "Weak", "Fair", "Strong", "Very Strong"]


def _strength_score(pwd: str) -> int:
    classes = 0
    if any(c in string.ascii_lowercase for c in pwd):
        classes += 1
    if any(c in string.ascii_uppercase for c in pwd):
        classes += 1
    if any(c in string.digits for c in pwd):
        classes += 1
    if any(c in string.punctuation for c in pwd):
        classes += 1
    if len(pwd) < 8:
        classes = max(0, classes - 1)
    return classes


def _strength_markup(pwd: str) -> str:
    score = _strength_score(pwd)
    color = _STRENGTH_COLORS[score]
    label = _STRENGTH_LABELS[score]
    bar = "█" * (score + 1) + "░" * (4 - score)
    return f"[{color}]{bar} {label}[/{color}]"


# ── Password Row widget ───────────────────────────────────────────────────────

class PasswordRow(Static):
    """A single password row that can be clicked to copy."""

    DEFAULT_CSS = ""

    def __init__(self, index: int, password: str, **kwargs):
        super().__init__(**kwargs)
        self.index = index
        self.password = password
        self._copied = False

    def compose(self) -> ComposeResult:
        yield Label(f"{self.index}", classes="pwd-idx")
        yield Label(self.password, classes="pwd-text")
        yield Static(_strength_markup(self.password), classes="pwd-strength", markup=True)
        yield Label("click to copy", classes="pwd-copy-hint")

    def on_click(self) -> None:
        copy_to_clipboard(self.password)
        self._copied = True
        self.add_class("-copied")
        copy_label = self.query_one(".pwd-copy-hint", Label)
        copy_label.update("✓ Copied!")
        copy_label.styles.color = "#22c55e"
        self.app.set_status(f"✓ Copied: {self.password}")
        # Reset after 2 seconds
        self.set_timer(2.0, self._reset_copied)

    def _reset_copied(self) -> None:
        self._copied = False
        self.remove_class("-copied")
        copy_label = self.query_one(".pwd-copy-hint", Label)
        copy_label.update("click to copy")
        copy_label.styles.color = None


# ── History tab ───────────────────────────────────────────────────────────────

class HistoryTab(Vertical):
    """History tab content."""

    def compose(self) -> ComposeResult:
        yield DataTable(id="history-table", cursor_type="row")
        yield Button("🗑  Clear History", id="clear-hist-btn")

    def on_mount(self) -> None:
        self.refresh_table()

    def refresh_table(self) -> None:
        table = self.query_one(DataTable)
        table.clear(columns=True)
        table.add_columns("#", "Password", "Strength", "Created", "Comment")
        history = load_history()
        if not history:
            return
        for i, item in enumerate(history, 1):
            pwd     = item.get("password", "")
            ts      = item.get("timestamp", 0)
            comment = item.get("comment") or "-"
            score   = _strength_score(pwd)
            color   = _STRENGTH_COLORS[score]
            label   = _STRENGTH_LABELS[score]
            bar     = "█" * (score + 1) + "░" * (4 - score)
            table.add_row(
                str(i),
                pwd,
                f"{bar} {label}",
                format_time_ago(ts),
                comment,
                key=str(i),
            )

    @on(DataTable.RowSelected, "#history-table")
    def on_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one(DataTable)
        row_vals = table.get_row(event.row_key)
        if row_vals:
            pwd = str(row_vals[1])
            copy_to_clipboard(pwd)
            self.app.set_status(f"✓ Copied from history: {pwd}")

    @on(Button.Pressed, "#clear-hist-btn")
    def on_clear(self) -> None:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        self.refresh_table()
        self.app.set_status("Password history cleared.")


# ── Main TUI App ──────────────────────────────────────────────────────────────

class PassgenApp(App):
    """Passgen — Modern Terminal Password Generator."""

    CSS = CSS
    TITLE = "Passgen"
    SUB_TITLE = "Secure Password Generator"

    BINDINGS: ClassVar[list[Binding]] = [
        Binding("g",      "generate",  "Generate",       show=True),
        Binding("ctrl+h", "show_history", "History",     show=True),
        Binding("q",      "quit",      "Quit",           show=True),
    ]

    _passwords: reactive[list[str]] = reactive([], recompose=False)

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

    # ── Layout ──────────────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()

        with Horizontal(id="layout"):
            # ── Left: controls ──────────────────────────────────────────
            with Vertical(id="left-panel"):
                yield Label("LENGTH", classes="section-label")
                with Horizontal(classes="length-row"):
                    yield Input(
                        value=str(self._init_length),
                        id="length-input",
                        type="integer",
                        restrict=r"[0-9]*",
                    )
                    yield Label(
                        f"{self._init_length} chars",
                        id="length-display",
                    )

                yield Label("COUNT", classes="section-label")
                with Horizontal(classes="length-row"):
                    yield Input(
                        value=str(self._init_count),
                        id="count-input",
                        type="integer",
                        restrict=r"[0-9]*",
                    )
                    yield Label("passwords", id="count-display", classes="sub-label")

                yield Label("EXCLUDE", classes="section-label")
                yield Checkbox(
                    "No Numbers",
                    value=self._init_no_numbers,
                    id="cb-no-numbers",
                )
                yield Checkbox(
                    "No Letters",
                    value=self._init_no_letters,
                    id="cb-no-letters",
                )
                yield Checkbox(
                    "No Specials",
                    value=self._init_no_specials,
                    id="cb-no-specials",
                )
                yield Checkbox(
                    "No Ambiguous",
                    value=self._init_no_ambiguous,
                    id="cb-no-ambiguous",
                )

                yield Label("COMMENT / LABEL", classes="section-label")
                yield Input(
                    value=self._init_comment,
                    placeholder="optional label…",
                    id="comment-input",
                )

                yield Button("⚿  Generate", id="generate-btn", variant="primary")

            # ── Right: results + history ────────────────────────────────
            with Vertical(id="right-panel"):
                with TabbedContent("Results", "History", id="tabs"):
                    with TabPane("Results", id="tab-results"):
                        with ScrollableContainer(id="results-scroll"):
                            yield Static(
                                "Press [bold cyan]G[/bold cyan] or click "
                                "[bold cyan]Generate[/bold cyan] to create passwords.",
                                id="empty-state",
                                markup=True,
                            )

                    with TabPane("History", id="tab-history"):
                        yield HistoryTab(id="history-tab")

        yield Static("", id="status-bar")
        yield Footer()

    # ── Actions ──────────────────────────────────────────────────────────────

    def action_generate(self) -> None:
        self.query_one("#generate-btn", Button).press()

    def action_show_history(self) -> None:
        tabs = self.query_one(TabbedContent)
        tabs.active = "tab-history"
        # Refresh the history table
        try:
            self.query_one(HistoryTab).refresh_table()
        except NoMatches:
            pass

    def set_status(self, message: str) -> None:
        try:
            self.query_one("#status-bar", Static).update(message)
        except NoMatches:
            pass

    # ── Event handlers ────────────────────────────────────────────────────────

    @on(Input.Changed, "#length-input")
    def on_length_changed(self, event: Input.Changed) -> None:
        val = event.value.strip()
        if val.isdigit():
            self.query_one("#length-display", Label).update(f"{val} chars")

    @on(Button.Pressed, "#generate-btn")
    def on_generate(self, event: Button.Pressed) -> None:
        self._do_generate()

    def _do_generate(self) -> None:
        # Read controls
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

        no_numbers   = self.query_one("#cb-no-numbers",   Checkbox).value
        no_letters   = self.query_one("#cb-no-letters",   Checkbox).value
        no_specials  = self.query_one("#cb-no-specials",  Checkbox).value
        no_ambiguous = self.query_one("#cb-no-ambiguous", Checkbox).value

        # Build pool
        try:
            pool = build_pool(
                no_letters=no_letters,
                no_numbers=no_numbers,
                no_specials=no_specials,
                no_ambiguous=no_ambiguous,
            )
        except ValueError as e:
            self.set_status(str(e))
            return

        # Generate
        now = time.time()
        passwords = [
            "".join(secrets.choice(pool) for _ in range(length))
            for _ in range(count)
        ]

        # Save to history
        records = [
            {"password": p, "timestamp": now, "comment": comment_val}
            for p in passwords
        ]
        save_to_history(records)

        # Update results pane
        scroll = self.query_one("#results-scroll", ScrollableContainer)
        scroll.remove_children()

        for i, pwd in enumerate(passwords, 1):
            scroll.mount(PasswordRow(i, pwd, classes="pwd-row"))

        # Switch to results tab
        self.query_one(TabbedContent).active = "tab-results"

        plural = "password" if count == 1 else "passwords"
        self.set_status(
            f"Generated {count} {plural}  ·  length {length}  ·  "
            f"click any password to copy"
        )


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
    """Launch the Textual TUI with initial settings from CLI args."""
    app = PassgenApp(
        length=length,
        count=count,
        no_numbers=no_numbers,
        no_letters=no_letters,
        no_specials=no_specials,
        no_ambiguous=no_ambiguous,
        comment=comment,
    )
    app.run()
