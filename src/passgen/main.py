import argparse
import sys

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
    from passgen.rich_output import (
        print_cleared,
        print_error,
        print_history_table,
        print_passwords,
    )
    from passgen.tui import run_tui
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
    from rich_output import (  # type: ignore
        print_cleared,
        print_error,
        print_history_table,
        print_passwords,
    )
    from tui import run_tui  # type: ignore

# Re-export everything tests and external code expect from passgen.main
from passgen.core import (
    AMBIGUOUS as AMBIGUOUS,
    HISTORY_FILE as HISTORY_FILE,
    MAX_HISTORY as MAX_HISTORY,
    build_pool as build_pool,
    format_time_ago as format_time_ago,
    generate_passwords as generate_passwords,
    load_history as load_history,
    save_to_history as save_to_history,
)

__all__ = [
    "AMBIGUOUS",
    "HISTORY_FILE",
    "MAX_HISTORY",
    "build_pool",
    "format_time_ago",
    "generate_passwords",
    "load_history",
    "save_to_history",
]


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Passgen — Secure terminal password generator."
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Launch the full-screen interactive TUI.",
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

    # ── Launch full TUI ──────────────────────────────────────────────────────
    if args.interactive:
        run_tui(
            length=args.length,
            count=args.count,
            no_numbers=args.no_numbers,
            no_letters=args.no_letters,
            no_specials=args.no_specials,
            no_ambiguous=args.no_ambiguous,
            comment=args.comment,
        )
        return 0

    # ── Clear history ────────────────────────────────────────────────────────
    if args.clear_history:
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink()
        print_cleared()
        return 0

    # ── Show history ─────────────────────────────────────────────────────────
    if args.history:
        history = load_history()
        print_history_table(history)
        return 0

    # ── Generate passwords ───────────────────────────────────────────────────
    try:
        records = generate_passwords(
            count=args.count,
            length=args.length,
            no_letters=args.no_letters,
            no_numbers=args.no_numbers,
            no_specials=args.no_specials,
            no_ambiguous=args.no_ambiguous,
            comment=args.comment,
        )
    except ValueError as e:
        print_error(str(e))
        return 1

    save_to_history(records)
    print_passwords([r["password"] for r in records])

    return 0


if __name__ == "__main__":
    sys.exit(main())
