"""Apply the checked-in Supabase migrations without ever dropping user data."""

import argparse
import subprocess
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply migrations to the selected Supabase database",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Apply migrations to the local Supabase database instead of the linked project",
    )
    args = parser.parse_args()

    if not args.apply:
        print("No changes were made.")
        print("Review supabase/migrations, then run `python init_db.py --apply` to apply them.")
        return 0

    command = ["supabase", "db", "push", "--local" if args.local else "--linked"]
    try:
        return subprocess.run(command, check=False).returncode
    except FileNotFoundError:
        print("Supabase CLI is required; install it before applying migrations.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
