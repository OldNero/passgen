"""
src/passgen/core.py
Shared core logic: password generation, history management, constants.
"""

import json
import secrets
import string
import time
from pathlib import Path

# ── Constants ─────────────────────────────────────────────────────────────────
HISTORY_FILE = Path.home() / ".passgen_history.json"
MAX_HISTORY  = 25
AMBIGUOUS    = "il1Lo0O|"


# ── Time formatting ───────────────────────────────────────────────────────────

def format_time_ago(timestamp: float) -> str:
    if not timestamp:
        return "unknown"
    diff = max(0, int(time.time() - timestamp))
    if diff < 60:
        return "less than a minute ago"
    elif diff < 120:
        return "1 minute ago"
    elif diff < 3600:
        return f"{diff // 60} minutes ago"
    elif diff < 7200:
        return "1 hour ago"
    elif diff < 86400:
        return f"{diff // 3600} hours ago"
    elif diff < 172800:
        return "yesterday"
    else:
        return f"{diff // 86400} days ago"


# ── History helpers ───────────────────────────────────────────────────────────

def load_history(file_path: Path | None = None) -> list[dict]:
    target = file_path or HISTORY_FILE
    if target.exists():
        try:
            data = json.loads(target.read_text())
            clean = []
            for item in data:
                if isinstance(item, str):
                    clean.append({"password": item, "timestamp": 0, "comment": "-"})
                else:
                    clean.append(item)
            return clean
        except json.JSONDecodeError:
            return []
    return []


def save_to_history(new_passwords: list[dict], file_path: Path | None = None) -> None:
    target = file_path or HISTORY_FILE
    history = load_history(target)
    history.extend(new_passwords)
    history = history[-MAX_HISTORY:]
    target.write_text(json.dumps(history, indent=2))
    target.chmod(0o600)  # Restrict to owner only


# ── Password generation ───────────────────────────────────────────────────────

def build_pool(
    no_letters:   bool = False,
    no_numbers:   bool = False,
    no_specials:  bool = False,
    no_ambiguous: bool = False,
) -> str:
    pool = ""
    if not no_letters:
        pool += string.ascii_letters
    if not no_numbers:
        pool += string.digits
    if not no_specials:
        pool += string.punctuation

    if no_ambiguous:
        pool = "".join(c for c in pool if c not in AMBIGUOUS)

    if not pool:
        raise ValueError(
            "Error: All character sets are excluded! Can't generate a password."
        )
    return pool


def generate_passwords(
    count:        int  = 1,
    length:       int  = 16,
    no_letters:   bool = False,
    no_numbers:   bool = False,
    no_specials:  bool = False,
    no_ambiguous: bool = False,
    comment:      str  = "",
) -> list[dict]:
    """Generate `count` passwords and return them as history record dicts."""
    pool = build_pool(
        no_letters=no_letters,
        no_numbers=no_numbers,
        no_specials=no_specials,
        no_ambiguous=no_ambiguous,
    )
    now = time.time()
    return [
        {
            "password": "".join(secrets.choice(pool) for _ in range(length)),
            "timestamp": now,
            "comment": comment,
        }
        for _ in range(count)
    ]
