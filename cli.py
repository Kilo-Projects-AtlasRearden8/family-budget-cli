"""Command-line interface for the family budget."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from typing import Any, Callable

from budget import (CATEGORIES, Budget, BudgetError, DEFAULT_DATA_FILE,
                    EXPENSE_CATEGORIES)


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date: {value!r} (use YYYY-MM-DD)"
        ) from exc


def month_year_args(parser: argparse.ArgumentParser) -> None:
    today = date.today()
    parser.add_argument("--month", type=int, default=today.month,
                        choices=range(1, 13), metavar="1-12",
                        help="month (default: current month)")
    parser.add_argument("--year", type=int, default=today.year,
                        help="year (default: current year)")


def cmd_add(args: argparse.Namespace, budget: Budget) -> int:
    try:
        entry = budget.add(args.date, args.category, args.amount,
                           args.description)
    except BudgetError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"added {entry.category}: {entry.amount:.2f} on {entry.date} "
          f"({entry.description or 'no description'})")
    return 0


def cmd_list(args: argparse.Namespace, budget: Budget) -> int:
    entries = budget.entries_for_month(args.month, args.year)
    if not entries:
        print(f"no entries for {args.year}-{args.month:02d}")
        return 0
    print(f"{'ID':<4} {'DATE':<12} {'CATEGORY':<12} {'AMOUNT':>10} DESCRIPTION")
    for entry in entries:
        print(f"{entry.id:<4} {entry.date.isoformat():<12} "
              f"{entry.category:<12} {entry.amount:>10.2f} {entry.description}")
    return 0


def cmd_totals(args: argparse.Namespace, budget: Budget) -> int:
    totals = budget.totals(args.month, args.year)
    net = budget.net_savings(args.month, args.year)
    print(f"budget for {args.year}-{args.month:02d}")
    for category in CATEGORIES:
        print(f"  {category:<12} {totals[category]:>10.2f}")
    print(f"  {'net savings':<12} {net:>10.2f}")
    return 0


def cmd_export(args: argparse.Namespace, budget: Budget) -> int:
    try:
        rows = budget.export_csv(args.output, args.month, args.year)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(f"exported {rows} row(s) to {args.output}")
    return 0


def cmd_alert(args: argparse.Namespace, budget: Budget) -> int:
    alerts = budget.overspending_alerts(args.month, args.year)
    if not alerts:
        print(f"no overspending alerts for {args.year}-{args.month:02d}")
        return 0
    print(f"overspending alerts for {args.year}-{args.month:02d}:")
    for alert in alerts:
        print(f"  - {alert}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="budget",
        description="Simple monthly family budget (local JSON storage).",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add a budget entry")
    add_parser.add_argument("category", choices=CATEGORIES,
                            help="income, bills, groceries, or savings")
    add_parser.add_argument("amount", type=float, help="positive amount")
    add_parser.add_argument("--date", type=parse_date, default=date.today(),
                            help="entry date YYYY-MM-DD (default: today)")
    add_parser.add_argument("--desc", default="", dest="description",
                            help="optional description")
    add_parser.set_defaults(func=cmd_add)

    list_parser = subparsers.add_parser("list", help="list entries for a month")
    month_year_args(list_parser)
    list_parser.set_defaults(func=cmd_list)

    totals_parser = subparsers.add_parser("totals", help="show monthly totals")
    month_year_args(totals_parser)
    totals_parser.set_defaults(func=cmd_totals)

    export_parser = subparsers.add_parser("export", help="export month to CSV")
    export_parser.add_argument("output", help="output CSV path")
    month_year_args(export_parser)
    export_parser.set_defaults(func=cmd_export)

    alert_parser = subparsers.add_parser("alert", help="check overspending")
    month_year_args(alert_parser)
    alert_parser.set_defaults(func=cmd_alert)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    budget = Budget(DEFAULT_DATA_FILE)
    return args.func(args, budget)


if __name__ == "__main__":
    sys.exit(main())
