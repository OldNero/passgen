"""
src/passgen/picker.py
Interactive click-to-copy terminal selector for generated passwords.
"""

import base64
import curses
import shutil
import subprocess
import sys


def copy_to_clipboard(text: str) -> bool:
    """
    Copies text to the system clipboard.
    Tries OSC 52 first (terminal native), with fallback to system utilities.
    """
    # 1. Try OSC-52 (works natively in most modern terminals)
    try:
        b64 = base64.b64encode(text.encode("utf-8")).decode("ascii")
        sys.stdout.write(f"\033]52;c;{b64}\a")
        sys.stdout.flush()
    except Exception:
        pass

    # 2. Linux Wayland fallback
    if shutil.which("wl-copy"):
        try:
            subprocess.run(["wl-copy"], input=text.encode(), check=True)
            return True
        except Exception:
            pass

    # 3. Linux X11 fallback
    if shutil.which("xclip"):
        try:
            subprocess.run(
                ["xclip", "-selection", "clipboard"], input=text.encode(), check=True
            )
            return True
        except Exception:
            pass

    # 4. macOS fallback
    if shutil.which("pbcopy"):
        try:
            subprocess.run(["pbcopy"], input=text.encode(), check=True)
            return True
        except Exception:
            pass

    return True


def pick_and_copy(items: list[str | dict]) -> str | None:
    """
    Displays an interactive list in the terminal where the user can
    click a password with the mouse (or use arrow keys + Enter) to copy it.
    Supports either plain password strings or history dictionary records.
    """
    if not items:
        return None

    # Normalize items to list of (password, display_label)
    entries: list[tuple[str, str]] = []
    for item in items:
        if isinstance(item, dict):
            pwd = str(item.get("password", ""))
            comment = item.get("comment")
            if comment and comment != "-":
                entries.append((pwd, f"{pwd}  ({comment})"))
            else:
                entries.append((pwd, pwd))
        else:
            pwd = str(item)
            entries.append((pwd, pwd))

    def _curses_menu(stdscr):
        curses.curs_set(0)  # Hide cursor
        # Enable all mouse click events
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)

        selected_idx = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()
            max_visible = max(1, h - 3)

            # Adjust scroll offset to keep selected_idx visible
            if selected_idx < scroll_offset:
                scroll_offset = selected_idx
            elif selected_idx >= scroll_offset + max_visible:
                scroll_offset = selected_idx - max_visible + 1

            # Header
            title = "🖱️ Click a password to copy (or use ↑/↓ + Enter | 'q' to quit):"
            stdscr.addstr(0, 0, title[: w - 1], curses.A_BOLD)
            stdscr.addstr(1, 0, "─" * min(w - 1, 65))

            # Password List
            visible_entries = entries[scroll_offset : scroll_offset + max_visible]
            for rel_idx, (pwd, label) in enumerate(visible_entries):
                abs_idx = scroll_offset + rel_idx
                row = rel_idx + 2

                is_highlighted = abs_idx == selected_idx
                style = curses.A_REVERSE if is_highlighted else curses.A_NORMAL

                prefix = f"{abs_idx + 1:2d}. "
                stdscr.addstr(row, 2, prefix, style)

                max_label_len = max(0, w - 2 - len(prefix) - 1)
                stdscr.addstr(
                    row,
                    2 + len(prefix),
                    label[:max_label_len],
                    style | curses.A_UNDERLINE,
                )

            stdscr.refresh()

            key = stdscr.getch()

            # 1. Mouse Click Detection
            if key == curses.KEY_MOUSE:
                try:
                    _, _, y, _, bstate = curses.getmouse()
                    if bstate & (curses.BUTTON1_CLICKED | curses.BUTTON1_PRESSED):
                        clicked_row = y - 2
                        clicked_idx = scroll_offset + clicked_row
                        if 0 <= clicked_idx < len(entries):
                            return entries[clicked_idx][0]
                except curses.error:
                    pass

            # 2. Keyboard Navigation
            elif key == curses.KEY_UP:
                selected_idx = (selected_idx - 1) % len(entries)
            elif key == curses.KEY_DOWN:
                selected_idx = (selected_idx + 1) % len(entries)
            elif key in (curses.KEY_ENTER, 10, 13):
                return entries[selected_idx][0]

            # 3. Direct number selection (1-9)
            elif ord("1") <= key <= ord("9"):
                idx = key - ord("1")
                if idx < len(entries):
                    return entries[idx][0]

            # 4. Quit ('q' or ESC)
            elif key in (ord("q"), ord("Q"), 27):
                return None

    try:
        chosen = curses.wrapper(_curses_menu)
    except KeyboardInterrupt:
        print("\nSelection cancelled.")
        return None
    except Exception:
        return None

    if chosen:
        copy_to_clipboard(chosen)
        print(f"\n✓ Copied to clipboard: {chosen}")
        return chosen
    else:
        print("\nSelection cancelled.")
        return None

