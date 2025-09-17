from __future__ import annotations

import json
import os
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from serp_tool.logging import app_logger


class DailyQuotaExceededError(Exception):
    def __init__(self, message: str = "Daily request limit reached. Please try again tomorrow."):
        super().__init__(message)
        self.error_type = "daily_quota_exceeded"


@dataclass
class UsageSnapshot:
    date: str
    used: int
    quota: int


class UsageTracker:
    """Thread-safe daily API request usage tracker with JSON persistence.

    Notes:
    - Counts REAL API requests only (call `increment()` when a real request is made).
    - Resets automatically if the stored date != today (local system time).
    - Storage is a small JSON file: {"date": "YYYY-MM-DD", "used": int, "quota": int}.
    - Uses an in-process `threading.Lock` and atomic write via temp+rename.
    """

    _instance: Optional["UsageTracker"] = None
    _instance_lock = threading.Lock()

    def __init__(self, storage_path: Path, daily_quota: int = 100) -> None:
        self.storage_path = Path(storage_path)
        self.daily_quota = int(daily_quota or 100)
        self._lock = threading.Lock()
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        # Initialize file if missing
        if not self.storage_path.exists():
            self._write_state({"date": self._today_str(), "used": 0, "quota": self.daily_quota})

    @classmethod
    def get_shared(cls) -> "UsageTracker":
        # Lazy singleton tied to config
        from config import config  # local import to avoid circulars during startup
        with cls._instance_lock:
            if cls._instance is None:
                storage = Path(config._project_root) / "state" / "usage.json"
                cfg_quota = int(os.getenv("DAILY_QUOTA", config._get("usage.daily_quota", 100) or 100))
                # Allow overriding storage path from config
                custom_path = config._get("usage.storage_path")
                if custom_path:
                    storage = Path(custom_path)
                cls._instance = UsageTracker(storage, cfg_quota)
            return cls._instance

    def _today_str(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")

    def _read_state(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f) or {}
        except FileNotFoundError:
            data = {}
        except Exception:
            data = {}
        # Normalize
        if not isinstance(data, dict):
            data = {}
        date_str = data.get("date") or self._today_str()
        used = int(data.get("used", 0) or 0)
        quota = int(data.get("quota", self.daily_quota) or self.daily_quota)
        return {"date": date_str, "used": used, "quota": quota}

    def _write_state(self, state: Dict[str, Any]) -> None:
        tmp_path = self.storage_path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(state, f)
        os.replace(tmp_path, self.storage_path)

    @contextmanager
    def _locked(self):
        self._lock.acquire()
        try:
            yield
        finally:
            self._lock.release()

    def _ensure_today_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        today = self._today_str()
        if state.get("date") != today:
            state = {"date": today, "used": 0, "quota": int(state.get("quota", self.daily_quota) or self.daily_quota)}
        return state

    def get_snapshot(self) -> UsageSnapshot:
        with self._locked():
            state = self._ensure_today_state(self._read_state())
            if state["date"] != self._read_state().get("date"):
                # Persist reset if happened
                self._write_state(state)
            return UsageSnapshot(date=state["date"], used=state["used"], quota=state["quota"])

    def remaining(self) -> int:
        snap = self.get_snapshot()
        return max(0, int(snap.quota) - int(snap.used))

    def ensure_can_consume(self, n: int = 1) -> None:
        if n < 0:
            return
        with self._locked():
            state = self._ensure_today_state(self._read_state())
            if state["date"] != self._read_state().get("date"):
                self._write_state(state)
            if state["used"] + n > state["quota"]:
                raise DailyQuotaExceededError()

    def increment(self, by: int = 1) -> UsageSnapshot:
        if by <= 0:
            return self.get_snapshot()
        with self._locked():
            state = self._ensure_today_state(self._read_state())
            if state["date"] != self._read_state().get("date"):
                self._write_state(state)
            new_used = state["used"] + by
            state["used"] = new_used
            self._write_state(state)
            app_logger.info(
                f"Usage incremented by {by}. Used {state['used']} / {state['quota']} today.",
                extra={"action": "usage_increment", "status": "success", "used": state["used"], "quota": state["quota"]},
            )
            return UsageSnapshot(date=state["date"], used=state["used"], quota=state["quota"])


