"""
Unit tests for the BudgetLedger daily inference enforcement.
"""

import os
import unittest
import tempfile
from pathlib import Path

from src.budget.ledger import BudgetLedger, BudgetExceededException


class TestBudgetLedger(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        db_path = Path(self.tmpdir.name) / "test_budget.db"
        self.ledger = BudgetLedger(
            db_path=str(db_path),
            daily_total_limit=5.00,
            daily_controller_limit=1.00,
            daily_worker_limit=4.00,
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_initial_budget_empty(self):
        summary = self.ledger.get_budget_summary()
        self.assertEqual(summary["total_used_usd"], 0.0)
        self.assertEqual(summary["controller_used_usd"], 0.0)
        self.assertEqual(summary["total_remaining_usd"], 5.00)
        self.assertEqual(summary["controller_remaining_usd"], 1.00)

    def test_record_controller_usage(self):
        cost = self.ledger.record_usage(
            role="controller",
            model="deepseek-v4-flash",
            input_tokens=10000,
            output_tokens=5000,
            cost_usd=0.25,
        )
        self.assertEqual(cost, 0.25)
        summary = self.ledger.get_budget_summary()
        self.assertEqual(summary["controller_used_usd"], 0.25)
        self.assertEqual(summary["total_used_usd"], 0.25)
        self.assertEqual(summary["controller_remaining_usd"], 0.75)

    def test_controller_daily_limit_exceeded(self):
        self.ledger.record_usage(
            role="controller",
            model="deepseek-v4-flash",
            input_tokens=10000,
            output_tokens=5000,
            cost_usd=0.90,
        )
        with self.assertRaises(BudgetExceededException):
            self.ledger.record_usage(
                role="controller",
                model="deepseek-v4-flash",
                input_tokens=5000,
                output_tokens=2000,
                cost_usd=0.20,
            )

    def test_total_daily_limit_exceeded(self):
        self.ledger.record_usage(
            role="controller",
            model="deepseek-v4-flash",
            input_tokens=100,
            output_tokens=100,
            cost_usd=0.80,
        )
        self.ledger.record_usage(
            role="worker",
            model="deepseek-v4-flash",
            input_tokens=100,
            output_tokens=100,
            cost_usd=3.80,
        )
        with self.assertRaises(BudgetExceededException):
            self.ledger.record_usage(
                role="worker",
                model="deepseek-v4-flash",
                input_tokens=100,
                output_tokens=100,
                cost_usd=0.50,
            )


if __name__ == "__main__":
    unittest.main()
