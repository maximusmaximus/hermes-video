"""
src/budget/ledger.py — Strict Daily Inference Budget Enforcement.

Enforces:
  1. Maximum $5.00 daily total inference spend on Venice across all operations.
  2. Maximum $1.00 daily inference spend on the Controller Hermes Agent.
  3. Pre-flight authorization: prevents API calls before exceeding quotas.
  4. Rolling 24-hour window accounting persisted in SQLite.
"""

import os
import json
import sqlite3
import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple


class BudgetExceededException(Exception):
    """Raised when an inference call would exceed daily budget thresholds."""
    pass


# Venice AI default estimated pricing per 1,000 tokens (USD)
DEFAULT_MODEL_PRICING = {
    # Text / Reasoning models
    "deepseek-v4-flash": {"input_per_1k": 0.00015, "output_per_1k": 0.00060},
    "deepseek-v4-pro": {"input_per_1k": 0.00050, "output_per_1k": 0.00200},
    "llama-3.3-70b": {"input_per_1k": 0.00040, "output_per_1k": 0.00080},
    "qwen-2.5-vl-72b": {"input_per_1k": 0.00050, "output_per_1k": 0.00150},
    # Default fallback rate
    "default": {"input_per_1k": 0.00030, "output_per_1k": 0.00100},
}


class BudgetLedger:
    """Manages persistent daily inference budgeting for hermes-video."""

    def __init__(
        self,
        db_path: Optional[str] = None,
        daily_total_limit: float = 5.00,
        daily_controller_limit: float = 1.00,
        daily_worker_limit: float = 4.00,
        window_hours: int = 24,
    ):
        if db_path is None:
            # Default to local data directory
            root = Path(__file__).resolve().parent.parent.parent
            self.db_path = root / "data" / "budget.db"
        else:
            self.db_path = Path(db_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.daily_total_limit = daily_total_limit
        self.daily_controller_limit = daily_controller_limit
        self.daily_worker_limit = daily_worker_limit
        self.window_hours = window_hours

        self._init_db()

    def _init_db(self):
        """Initialize the SQLite schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS inference_ledger (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    role TEXT NOT NULL, -- 'controller' or 'worker'
                    model TEXT NOT NULL,
                    input_tokens INTEGER DEFAULT 0,
                    output_tokens INTEGER DEFAULT 0,
                    cost_usd REAL NOT NULL,
                    metadata TEXT
                )
                """
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_timestamp ON inference_ledger (timestamp);"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_role ON inference_ledger (role);"
            )
            conn.commit()

    def calculate_cost(
        self, model: str, input_tokens: int, output_tokens: int
    ) -> float:
        """Estimate or compute cost based on token counts."""
        pricing = DEFAULT_MODEL_PRICING.get(model, DEFAULT_MODEL_PRICING["default"])
        cost = (input_tokens / 1000.0) * pricing["input_per_1k"] + (
            output_tokens / 1000.0
        ) * pricing["output_per_1k"]
        return round(cost, 6)

    def get_window_cutoff(self) -> str:
        """Returns the ISO string for the start of the current rolling window."""
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            hours=self.window_hours
        )
        return cutoff.isoformat()

    def get_usage(self, role: Optional[str] = None) -> float:
        """Calculate total spend in the rolling window (optionally filtered by role)."""
        cutoff = self.get_window_cutoff()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            if role:
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(cost_usd), 0.0)
                    FROM inference_ledger
                    WHERE timestamp >= ? AND role = ?
                    """,
                    (cutoff, role),
                )
            else:
                cursor.execute(
                    """
                    SELECT COALESCE(SUM(cost_usd), 0.0)
                    FROM inference_ledger
                    WHERE timestamp >= ?
                    """,
                    (cutoff,),
                )
            row = cursor.fetchone()
            return round(row[0] if row else 0.0, 4)

    def get_budget_summary(self) -> Dict[str, Any]:
        """Returns comprehensive breakdown of daily usage and remaining balances."""
        total_used = self.get_usage()
        controller_used = self.get_usage(role="controller")
        worker_used = self.get_usage(role="worker")

        return {
            "window_hours": self.window_hours,
            "total_limit_usd": self.daily_total_limit,
            "total_used_usd": total_used,
            "total_remaining_usd": max(0.0, round(self.daily_total_limit - total_used, 4)),
            "controller_limit_usd": self.daily_controller_limit,
            "controller_used_usd": controller_used,
            "controller_remaining_usd": max(
                0.0, round(self.daily_controller_limit - controller_used, 4)
            ),
            "worker_limit_usd": self.daily_worker_limit,
            "worker_used_usd": worker_used,
            "worker_remaining_usd": max(
                0.0, round(self.daily_worker_limit - worker_used, 4)
            ),
        }

    def check_authorization(
        self, role: str, projected_cost: float
    ) -> Tuple[bool, str]:
        """
        Pre-flight check: determines if an inference call with projected cost
        is authorized under current daily limits.
        """
        if role not in ("controller", "worker"):
            return False, f"Invalid role '{role}'. Must be 'controller' or 'worker'."

        total_used = self.get_usage()
        if total_used + projected_cost > self.daily_total_limit:
            return (
                False,
                f"Total daily budget limit (${self.daily_total_limit:.2f}) would be exceeded. "
                f"Current: ${total_used:.4f}, Projected: ${projected_cost:.4f}",
            )

        if role == "controller":
            controller_used = self.get_usage(role="controller")
            if controller_used + projected_cost > self.daily_controller_limit:
                return (
                    False,
                    f"Controller agent daily limit (${self.daily_controller_limit:.2f}) would be exceeded. "
                    f"Current: ${controller_used:.4f}, Projected: ${projected_cost:.4f}",
                )

        if role == "worker":
            worker_used = self.get_usage(role="worker")
            if worker_used + projected_cost > self.daily_worker_limit:
                return (
                    False,
                    f"Worker daily limit (${self.daily_worker_limit:.2f}) would be exceeded. "
                    f"Current: ${worker_used:.4f}, Projected: ${projected_cost:.4f}",
                )

        return True, "Authorized"

    def record_usage(
        self,
        role: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
        strict_check: bool = True,
    ) -> float:
        """
        Record completed inference in ledger.
        If strict_check is True, raises BudgetExceededException if pre-flight check fails.
        """
        if cost_usd is None:
            cost_usd = self.calculate_cost(model, input_tokens, output_tokens)

        if strict_check:
            authorized, reason = self.check_authorization(role, cost_usd)
            if not authorized:
                raise BudgetExceededException(reason)

        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        meta_json = json.dumps(metadata) if metadata else None

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO inference_ledger (
                    timestamp, role, model, input_tokens, output_tokens, cost_usd, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    now_iso,
                    role,
                    model,
                    input_tokens,
                    output_tokens,
                    cost_usd,
                    meta_json,
                ),
            )
            conn.commit()

        return cost_usd
