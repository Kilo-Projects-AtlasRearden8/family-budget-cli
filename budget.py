"""Simple monthly family budget with local JSON storage.

Tracks income, bills, groceries, and savings in a single JSON file.
Provides monthly totals, net-savings math, overspending alerts, and CSV export.
Local-first: no network, no API keys, no accounts.
"""

from __future__ import annotations

import csv
import json
from datetime import date
from pathlib import Path
from typing import Any

DEFAULT_DATA_FILE = Path("budget.json")

CATEGORIES = ("income", "bills", "groceries", "savings")
EXPENSE_CATEGORIES = ("bills", "groceries", "savings")


class BudgetError(Exception):
    """Raised for invalid budget input."""


class Entry:
    """One budget line item."""

    def __init__(self, entry_id: int, entry_date: date, category: str,
                 amount: float, description: str = "") -> None:
        self.id = entry_id
        self.date = entry_date
        self.category = category
        self.amount = amount
        self.description = description

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "category": self.category,
            "amount": self.amount,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Entry":
        return cls(
            entry_id=int(data["id"]),
            entry_date=date.fromisoformat(data["date"]),
            category=str(data["category"]),
            amount=float(data["amount"]),
            description=str(data.get("description", "")),
        )


class Budget:
    """In-memory budget backed by a local JSON file."""

    def __init__(self, data_file: str | Path = DEFAULT_DATA_FILE) -> None:
        self.data_file = Path(data_file)
        self.entries: list[Entry] = []
        self._next_id = 1
        self._load()

    def _load(self) -> None:
        if not self.data_file.exists():
            return
        if self.data_file.stat().st_size == 0:
            return
        with self.data_file.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        self.entries = [Entry.from_dict(item) for item in raw]
        self._next_id = max((entry.id for entry in self.entries), default=0) + 1

    def save(self) -> None:
        with self.data_file.open("w", encoding="utf-8") as handle:
            json.dump([entry.to_dict() for entry in self.entries], handle, indent=2)

    def add(self, entry_date: date, category: str, amount: float,
            description: str = "") -> Entry:
        """Add and persist a new entry. Returns the created entry."""
        if category not in CATEGORIES:
            raise BudgetError(f"unknown category: {category!r}")
        if amount <= 0:
            raise BudgetError("amount must be positive")
        entry = Entry(self._next_id, entry_date, category, amount, description)
        self.entries.append(entry)
        self._next_id += 1
        self.save()
        return entry

    def entries_for_month(self, month: int | None = None,
                          year: int | None = None) -> list[Entry]:
        today = date.today()
        month = today.month if month is None else month
        year = today.year if year is None else year
        return [entry for entry in self.entries
                if entry.date.year == year and entry.date.month == month]

    def totals(self, month: int | None = None, year: int | None = None) -> dict[str, float]:
        result = {category: 0.0 for category in CATEGORIES}
        for entry in self.entries_for_month(month, year):
            result[entry.category] += entry.amount
        return result

    def net_savings(self, month: int | None = None,
                    year: int | None = None) -> float:
        totals = self.totals(month, year)
        expenses = sum(totals[cat] for cat in EXPENSE_CATEGORIES)
        return totals["income"] - expenses

    def overspending_alerts(self, month: int | None = None,
                            year: int | None = None) -> list[str]:
        """Return human-readable alerts when spending outruns income."""
        alerts: list[str] = []
        totals = self.totals(month, year)
        income = totals["income"]
        expenses = sum(totals[cat] for cat in EXPENSE_CATEGORIES)
        if expenses > income and income > 0:
            shortfall = expenses - income
            alerts.append(
                f"Overspending: total expenses ({expenses:.2f}) exceed "
                f"income ({income:.2f}) by {shortfall:.2f}"
            )
        for category in EXPENSE_CATEGORIES:
            if totals[category] > income and income > 0:
                alerts.append(
                    f"Overspending: {category} ({totals[category]:.2f}) exceeds "
                    f"income ({income:.2f})"
                )
        return alerts

    def export_csv(self, path: str | Path, month: int | None = None,
                   year: int | None = None) -> int:
        """Write entries for a month to CSV. Returns rows written."""
        path = Path(path)
        rows = self.entries_for_month(month, year)
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(["id", "date", "category", "amount", "description"])
            for entry in rows:
                writer.writerow([entry.id, entry.date.isoformat(),
                                 entry.category, f"{entry.amount:.2f}",
                                 entry.description])
        return len(rows)
