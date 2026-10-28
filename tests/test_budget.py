"""Tests for the family budget: totals and date math."""

from __future__ import annotations

import os
import tempfile
import unittest
from datetime import date

from budget import Budget, BudgetError, CATEGORIES, EXPENSE_CATEGORIES


def make_budget(path: str) -> Budget:
    return Budget(path)


class TestBudgetTotals(unittest.TestCase):
    def setUp(self) -> None:
        self.fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)
        self.budget = make_budget(self.path)

    def tearDown(self) -> None:
        os.unlink(self.path)

    def test_totals_start_empty(self) -> None:
        totals = self.budget.totals()
        for category in CATEGORIES:
            self.assertEqual(totals[category], 0.0)
        self.assertEqual(self.budget.net_savings(), 0.0)

    def test_add_income_updates_totals(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 4000.00, "paycheck")
        totals = self.budget.totals(10, 2026)
        self.assertEqual(totals["income"], 4000.00)
        self.assertEqual(totals["bills"], 0.0)
        self.assertEqual(self.budget.net_savings(10, 2026), 4000.00)

    def test_expenses_reduce_net_savings(self) -> None:
        self.budget.add(date(2026, 10, 2), "income", 5000.00)
        self.budget.add(date(2026, 10, 3), "bills", 1200.00, "rent")
        self.budget.add(date(2026, 10, 4), "groceries", 300.00)
        self.budget.add(date(2026, 10, 5), "savings", 500.00)
        totals = self.budget.totals(10, 2026)
        self.assertEqual(totals["bills"], 1200.00)
        self.assertEqual(totals["groceries"], 300.00)
        self.assertEqual(totals["savings"], 500.00)
        self.assertEqual(self.budget.net_savings(10, 2026), 3000.00)

    def test_totals_do_not_leak_into_other_months(self) -> None:
        self.budget.add(date(2026, 9, 30), "income", 1000.00)
        self.budget.add(date(2026, 10, 1), "income", 2000.00)
        self.budget.add(date(2026, 10, 31), "bills", 100.00)
        self.budget.add(date(2026, 11, 1), "bills", 50.00)
        october = self.budget.totals(10, 2026)
        self.assertEqual(october["income"], 2000.00)
        self.assertEqual(october["bills"], 100.00)
        november = self.budget.totals(11, 2026)
        self.assertEqual(november["income"], 0.0)
        self.assertEqual(november["bills"], 50.00)

    def test_year_rollover_keeps_months_separate(self) -> None:
        self.budget.add(date(2025, 12, 31), "income", 999.00)
        self.budget.add(date(2026, 1, 1), "income", 1.00)
        self.assertEqual(self.budget.totals(12, 2025)["income"], 999.00)
        self.assertEqual(self.budget.totals(1, 2026)["income"], 1.00)

    def test_default_month_is_current_month(self) -> None:
        from datetime import date as today_date
        today = today_date.today()
        self.budget.add(today, "income", 77.77)
        totals = self.budget.totals()
        self.assertEqual(totals["income"], 77.77)

    def test_rejects_unknown_category(self) -> None:
        with self.assertRaises(BudgetError):
            self.budget.add(date(2026, 10, 1), "fun", 10.00)

    def test_rejects_non_positive_amount(self) -> None:
        with self.assertRaises(BudgetError):
            self.budget.add(date(2026, 10, 1), "income", 0.00)
        with self.assertRaises(__import__("budget").BudgetError):
            self.budget.add(date(2026, 10, 1), "income", -5.00)

    def test_persists_and_reloads(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 1234.56)
        reloaded = make_budget(self.path)
        totals = reloaded.totals(10, 2026)
        self.assertEqual(totals["income"], 1234.56)
        self.assertEqual(reloaded.entries[0].id, 1)


class TestBudgetDateMath(unittest.TestCase):
    def setUp(self) -> None:
        self.fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)
        self.budget = make_budget(self.path)

    def tearDown(self) -> None:
        os.unlink(self.path)

    def test_month_boundary_november_to_december(self) -> None:
        self.budget.add(date(2026, 11, 30), "groceries", 50.00)
        self.budget.add(date(2026, 12, 1), "groceries", 60.00)
        self.assertEqual(self.budget.totals(11, 2026)["groceries"], 50.00)
        self.assertEqual(self.budget.totals(12, 2026)["groceries"], 60.00)

    def test_entries_for_month_filters_exactly(self) -> None:
        self.budget.add(date(2026, 10, 1), "bills", 10.00)
        self.budget.add(date(2026, 10, 31), "bills", 20.00)
        self.budget.add(date(2026, 9, 30), "bills", 99.00)
        self.budget.add(date(2026, 11, 1), "bills", 88.00)
        october = self.budget.entries_for_month(10, 2026)
        self.assertEqual(len(october), 2)
        self.assertEqual({e.date.day for e in october}, {1, 31})

    def test_net_savings_negative_when_expenses_exceed_income(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 100.00)
        self.budget.add(date(2026, 10, 2), "bills", 150.00)
        self.assertEqual(self.budget.net_savings(10, 2026), -50.00)

    def test_next_id_increments_after_reload(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 10.00)
        self.budget.add(date(2026, 10, 2), "income", 20.00)
        reloaded = make_budget(self.path)
        entry = reloaded.add(date(2026, 10, 3), "income", 30.00)
        self.assertEqual(entry.id, 3)


class TestBudgetAlertsAndExport(unittest.TestCase):
    def setUp(self) -> None:
        self.fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(self.fd)
        self.budget = make_budget(self.path)

    def tearDown(self) -> None:
        os.unlink(self.path)

    def test_overspending_alert_when_expenses_exceed_income(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 1000.00)
        self.budget.add(date(2026, 10, 2), "bills", 700.00)
        self.budget.add(date(2026, 10, 3), "groceries", 400.00)
        self.budget.add(date(2026, 10, 4), "savings", 100.00)
        alerts = self.budget.overspending_alerts(10, 2026)
        self.assertTrue(any("exceed" in alert for alert in alerts))

    def test_no_alert_within_income(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 2000.00)
        self.budget.add(date(2026, 10, 2), "bills", 500.00)
        self.assertEqual(self.budget.overspending_alerts(10, 2026), [])

    def test_no_income_no_alert(self) -> None:
        self.budget.add(date(2026, 10, 1), "bills", 500.00)
        self.assertEqual(self.budget.overspending_alerts(10, 2026), [])

    def test_export_csv_writes_header_and_rows(self) -> None:
        self.budget.add(date(2026, 10, 5), "income", 100.00, "pay")
        self.budget.add(date(2026, 10, 6), "bills", 50.00)
        out_path = self.path + ".csv"
        rows = self.budget.export_csv(out_path, 10, 2026)
        self.assertEqual(rows, 2)
        with open(out_path, "r", encoding="utf-8") as handle:
            lines = handle.read().strip().splitlines()
        self.assertEqual(lines[0], "id,date,category,amount,description")
        self.assertEqual(lines[1], "1,2026-10-05,income,100.00,pay")
        self.assertEqual(lines[2], "2,2026-10-06,bills,50.00,")
        os.unlink(out_path)

    def test_export_csv_filters_by_month(self) -> None:
        self.budget.add(date(2026, 10, 1), "income", 100.00)
        self.budget.add(date(2026, 11, 1), "income", 200.00)
        out_path = self.path + ".csv"
        self.budget.export_csv(out_path, 10, 2026)
        with open(out_path, "r", encoding="utf-8") as handle:
            lines = handle.read().strip().splitlines()
        self.assertEqual(len(lines), 2)  # header + 1 row
        os.unlink(out_path)


if __name__ == "__main__":
    unittest.main()
