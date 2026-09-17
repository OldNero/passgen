import argparse
import json
import secrets
import string
import sys
import time
from pathlib import Path

try:
    from passgen.picker import pick_and_copy
except ModuleNotFoundError:
    from picker import pick_and_copy

# History file config
HISTORY_FILE = Path.home() / ".passgen_history.json"
MAX_HISTORY = 25
AMBIGUOUS = "il1Lo0O|"


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


# History helper
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


def print_history_table(history: list[dict]):
    if not history:
        print("No history found.")
        return
    h_idx, h_pwd, h_time, h_comm = "#", "Password", "Created", "Comment"
    w_idx = max(len(h_idx), len(str(len(history))))
    w_pwd = max(len(h_pwd), max(len(item["password"]) for item in history))
    w_time = max(
        len(h_time),
        max(len(format_time_ago(item.get("timestamp", 0))) for item in history),
    )
    w_comm = max(len(h_comm), max(len(item.get("comment") or "-") for item in history))
    sep_top = f"┌─{'─' * w_idx}─┬─{'─' * w_pwd}─┬─{'─' * w_time}─┬─{'─' * w_comm}─┐"
    header = f"│ {h_idx:<{w_idx}} │ {h_pwd:<{w_pwd}} │ {h_time:<{w_time}} │ {h_comm:<{w_comm}} │"
    sep_mid = f"├─{'─' * w_idx}─┼─{'─' * w_pwd}─┼─{'─' * w_time}─┼─{'─' * w_comm}─┤"
    sep_bot = f"└─{'─' * w_idx}─┴─{'─' * w_pwd}─┴─{'─' * w_time}─┴─{'─' * w_comm}─┘"
    print(f"\n--- Stored Passwords ({len(history)}/{MAX_HISTORY}) ---")
    print(sep_top)
    print(header)
    print(sep_mid)
    for idx, item in enumerate(history, 1):
        pwd = item["password"]
        time_str = format_time_ago(item.get("timestamp", 0))
        comment = item.get("comment") or "-"
        print(
            f"│ {idx:<{w_idx}} │ {pwd:<{w_pwd}} │ {time_str:<{w_time}} │ {comment:<{w_comm}} │"
        )
    print(sep_bot)


def save_to_history(new_passwords, file_path: Path | None = None):
    target = file_path or HISTORY_FILE
    history = load_history(target)
    history.extend(new_passwords)
    history = history[-MAX_HISTORY:]
    target.write_text(json.dumps(history, indent=2))
    target.chmod(0o600)  # Restrict to owner only


def build_pool(
    no_letters: bool = False,
    no_numbers: bool = False,
    no_specials: bool = False,
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


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Interactive click-to-copy mode.",
    )
    parser.add_argument(
        "-l", "--length", type=int, default=16, help="Password length in characters."
    )
    parser.add_argument(
        "-c", "--count", type=int, default=1, help="The number of passwords generated."
    )
    parser.add_argument(
        "-na",
        "--no-ambiguous",
        action="store_true",
        help="Removes ambiguous characters.",
    )
    parser.add_argument(
        "-nn",
        "--no-numbers",
        action="store_true",
        help="Removes numbers from password.",
    )
    parser.add_argument(
        "-nl",
        "--no-letters",
        action="store_true",
        help="Removes letters from password.",
    )
    parser.add_argument(
        "-ns",
        "--no-specials",
        action="store_true",
        help="Removes special characters from password.",
    )
    parser.add_argument(
        "-H",
        "--history",
        action="store_true",
        help=f"Show password history. Max {MAX_HISTORY}.",
    )
    parser.add_argument(
        "--clear-history", action="store_true", help="Clear saved password history."
    )
    parser.add_argument(
        "-m",
        "--comment",
        type=str,
        default="",
        help="Comment or label for the password.",
    )
    return parser


def main(argv=None):
    parser = get_parser()
    args = parser.parse_args(argv)

    if args.clear_history:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        print("Password history cleared.")
        return 0

    if args.history:
        history = load_history()
        if args.interactive:
            if not history:
                print("No history found.")
            else:
                pick_and_copy(history)
            return 0
        print_history_table(history)
        return 0

    pool = build_pool(
        no_letters=args.no_letters,
        no_numbers=args.no_numbers,
        no_specials=args.no_specials,
        no_ambiguous=args.no_ambiguous,
    )

    current_time = time.time()
    new_records = []

    for _ in range(args.count):
        password = "".join(secrets.choice(pool) for _ in range(args.length))
        new_records.append(
            {"password": password, "timestamp": current_time, "comment": args.comment}
        )
        if not args.interactive:
            print(password)

    save_to_history(new_records)

    if args.interactive:
        # Pass generated passwords to the picker
        pick_and_copy([p["password"] for p in new_records])

    return 0


if __name__ == "__main__":
    sys.exit(main())

