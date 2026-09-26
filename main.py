#!/usr/bin/env python3
"""
ANUSINT (Automated Network Username Spoofing Investigation &
Notification Tool) — a small OSINT toolkit for spotting impersonation, built on
publicly accessible data only (no login, no auth-wall bypass, no bulk
scraping). See README.md for full setup and legal/ethical scope.

Subcommands:
    check-username   Check if a username exists across major platforms
    snapshot          Fetch public Instagram profile data
    compare           Compare a genuine account against suspected fakes

Run `python3 main.py <subcommand> --help` for subcommand-specific options.
"""

import argparse
import sys

import username_checker
import profile_snapshot
import impersonation_check


def build_arg_parser():
    parser = argparse.ArgumentParser(
        prog="anusint",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # Each subcommand delegates argument parsing to its own module so
    # `--help` on a subcommand shows exactly the same flags as running
    # that module standalone.
    subparsers.add_parser(
        "check-username", add_help=False,
        help="Check if a username exists across major platforms",
    )
    subparsers.add_parser(
        "snapshot", add_help=False,
        help="Fetch public Instagram profile data",
    )
    subparsers.add_parser(
        "compare", add_help=False,
        help="Compare a genuine account against suspected impersonators",
    )
    return parser


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        build_arg_parser().print_help()
        sys.exit(0)

    command, rest = sys.argv[1], sys.argv[2:]

    if command == "check-username":
        username_checker.main(rest)
    elif command == "snapshot":
        profile_snapshot.main(rest)
    elif command == "compare":
        impersonation_check.main(rest)
    else:
        print(f"Unknown command: {command}\n")
        build_arg_parser().print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
