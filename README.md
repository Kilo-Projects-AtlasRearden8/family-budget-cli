# Family Budget CLI

A simple, local-first command-line tool for building a monthly family budget.
Track income, bills, groceries, and savings in a plain JSON file on your own
machine. No accounts, no API keys, no network calls, no personal data leaves
your computer.

Built and maintained by **Asdale Dynamics, LLC** (Indiana, formed October
2026) — beginner-friendly AI education, books, and practical tools you can
actually use. Part of the same plain-English, step-by-step spirit found in
_The Massive AI Manual_ and at dylanasdale.github.io.

## What it does

- Add income, bills, groceries, and savings entries with a date and description
- View monthly totals and net savings (income minus expenses)
- Get overspending alerts when spending outruns income
- Export a month's entries to CSV
- Store everything locally in a single JSON file (`budget.json` by default)

## Who this is for

Anyone who wants a dead-simple, private budgeting tool without signing up for
anything. Built with the Asdale Dynamics, LLC focus on accessible life-admin
helpers — low-energy, ADHD-friendly, and tested.

## Requirements

- Python 3.8 or later (tested on Python 3.13)
- No external packages — only the standard library

## Installation

There is nothing to install. Clone or download this folder and run:

```bash
python3 cli.py
```

## Usage

Add an entry (defaults to today's date):

```bash
python3 cli.py add income 4000 --desc "paycheck"
python3 cli.py add bills 1200 --desc rent --date 2026-10-01
python3 cli.py add groceries 300
python3 cli.py add savings 500
```

View this month's totals:

```bash
python3 cli.py totals
```

View a different month:

```bash
python3 cli.py totals --month 9 --year 2026
```

List entries for a month:

```bash
python3 cli.py list --month 10 --year 2026
```

Check for overspending:

```bash
python3 cli.py alert --month 10 --year 2026
```

Export a month to CSV:

```bash
python3 cli.py export october.csv --month 10 --year 2026
```

See all options:

```bash
python3 cli.py --help
python3 cli.py add --help
```

## Storage

Data lives in `budget.json` in the folder where you run the tool. It is plain
JSON — you can open it in any text editor, back it up however you like, and
move it between machines. Nothing is ever sent over the network.

## Tests

Run the test suite (totals and date math) with:

```bash
python3 -m pytest
```

or, without pytest:

```bash
python3 -m unittest discover -s tests
```

## Credit

Created by **Asdale Dynamics, LLC**. Copyright (c) 2026 Asdale Dynamics, LLC.

Licensed under the MIT License. See LICENSE for details.
