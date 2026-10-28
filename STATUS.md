# STATUS

## What was built

A local-first Python CLI for a simple monthly family budget, created for
Asdale Dynamics, LLC.

Core module (`budget.py`):
- Local JSON storage in a single file (`budget.json` by default)
- Add entries for income, bills, groceries, and savings with date + description
- Monthly totals per category
- Net savings (income minus expenses)
- Overspending alerts when spending outruns income
- CSV export for a given month
- Input validation (unknown category rejected, non-positive amount rejected)

Command-line interface (`cli.py`):
- `add` — add a budget entry
- `list` — list entries for a month
- `totals` — show monthly totals and net savings
- `export` — export a month to CSV
- `alert` — check overspending for a month

Tests (`tests/test_budget.py`): 18 tests covering totals and date math
(month boundaries, year rollover, filtering by month, persistence, IDs,
alerts, CSV export).

Supporting files:
- `LICENSE` — MIT License, copyright line exactly
  `Copyright (c) 2026 Asdale Dynamics, LLC`
- `README.md` — usage, credit to Asdale Dynamics, LLC
- `.gitignore` — excludes runtime data and Python caches

## How to run it

Requires Python 3.8+ (tested on Python 3.13). No external packages.

```bash
cd /workspace/kilo-lab/family-budget-cli

python3 cli.py add income 4000 --desc "paycheck"
python3 cli.py add bills 1200 --desc rent
python3 cli.py add groceries 300
python3 cli.py add savings 500
python3 cli.py totals
python3 cli.py alert
python3 cli.py export october.csv --month 10 --year 2026
python3 cli.py --help
```

## Verification results

Tests: `python3 -m pytest` → 18 passed.
Tests without pytest: `python3 -m unittest discover -s tests` → 18 passed.

CLI smoke test (add income/bills/groceries/savings, totals, export CSV,
alert): all commands run successfully and produce correct output.
Overspending alert confirmed: income 100, bills 200 produces two alerts
(total expenses exceed income; bills exceed income).
Persistence confirmed: entries survive reload from `budget.json`.
Month/year filtering confirmed: entries do not leak across month or year
boundaries; net savings can be negative.

No `.github/workflows` files were added. No API keys, secrets, or personal
data in any file.

## Known gaps

- No graphical interface; CLI only
- No per-category budget targets or alerts (only total/per-category vs income)
- No recurring transactions or scheduled entries
- No multi-month summary view
- No edit/delete for individual entries (entries are append-only)
- Default storage path is `budget.json` in the current working directory;
  there is no flag to choose a different data file
- Negative amounts are rejected at entry time; existing data with negative
  amounts (if hand-edited in JSON) would not be sanitized on load
