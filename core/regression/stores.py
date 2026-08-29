from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from core.regression.interfaces import FailureStoreInterface, RegressionStoreInterface
from core.schemas.failure import FailureRecord
from core.schemas.regression import RegressionRecord


class InMemoryFailureStore(FailureStoreInterface):
    """In-memory failure store for tests and fast ephemeral execution."""

    def __init__(self, initial_failures: Optional[List[FailureRecord]] = None):
        self._failures: Dict[str, FailureRecord] = {}
        if initial_failures:
            for f in initial_failures:
                self.save_failure(f)

    def get_failure(self, failure_id: str) -> Optional[FailureRecord]:
        return self._failures.get(failure_id)

    def list_failures(self, verified_only: bool = True) -> List[FailureRecord]:
        if not verified_only:
            return list(self._failures.values())
        return [f for f in self._failures.values() if f.verification.status.lower() == "verified"]

    def save_failure(self, failure: FailureRecord) -> None:
        self._failures[failure.failure_id] = failure


class JsonFileFailureStore(FailureStoreInterface):
    """File-backed failure storage reading/writing JSON files in a directory."""

    def __init__(self, directory_path: str | Path):
        self.dir_path = Path(directory_path)
        self.dir_path.mkdir(parents=True, exist_ok=True)

    def get_failure(self, failure_id: str) -> Optional[FailureRecord]:
        file_path = self.dir_path / f"{failure_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return FailureRecord.model_validate(data)

    def list_failures(self, verified_only: bool = True) -> List[FailureRecord]:
        results: List[FailureRecord] = []
        for file_path in self.dir_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    record = FailureRecord.model_validate(data)
                    if not verified_only or record.verification.status.lower() == "verified":
                        results.append(record)
            except Exception:
                continue
        return results

    def save_failure(self, failure: FailureRecord) -> None:
        file_path = self.dir_path / f"{failure.failure_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(failure.model_dump_json(indent=2))


class InMemoryRegressionStore(RegressionStoreInterface):
    """In-memory regression store for tests and fast ephemeral execution."""

    def __init__(self, initial_regressions: Optional[List[RegressionRecord]] = None):
        self._regressions: Dict[str, RegressionRecord] = {}
        if initial_regressions:
            for r in initial_regressions:
                self.save_regression(r)

    def get_regression(self, regression_id: str) -> Optional[RegressionRecord]:
        return self._regressions.get(regression_id)

    def list_regressions(self, enabled_only: bool = True) -> List[RegressionRecord]:
        if not enabled_only:
            return list(self._regressions.values())
        return [r for r in self._regressions.values() if r.enabled]

    def save_regression(self, regression: RegressionRecord) -> None:
        self._regressions[regression.regression_id] = regression

    def set_enabled(self, regression_id: str, enabled: bool) -> bool:
        if regression_id in self._regressions:
            self._regressions[regression_id].enabled = enabled
            return True
        return False


class JsonFileRegressionStore(RegressionStoreInterface):
    """File-backed regression storage reading/writing JSON files in a directory."""

    def __init__(self, directory_path: str | Path):
        self.dir_path = Path(directory_path)
        self.dir_path.mkdir(parents=True, exist_ok=True)

    def get_regression(self, regression_id: str) -> Optional[RegressionRecord]:
        file_path = self.dir_path / f"{regression_id}.json"
        if not file_path.exists():
            return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return RegressionRecord.model_validate(data)

    def list_regressions(self, enabled_only: bool = True) -> List[RegressionRecord]:
        results: List[RegressionRecord] = []
        for file_path in self.dir_path.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    record = RegressionRecord.model_validate(data)
                    if not enabled_only or record.enabled:
                        results.append(record)
            except Exception:
                continue
        return results

    def save_regression(self, regression: RegressionRecord) -> None:
        file_path = self.dir_path / f"{regression.regression_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(regression.model_dump_json(indent=2))

    def set_enabled(self, regression_id: str, enabled: bool) -> bool:
        reg = self.get_regression(regression_id)
        if reg is None:
            return False
        reg.enabled = enabled
        self.save_regression(reg)
        return True
