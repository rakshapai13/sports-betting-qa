"""Soft assertions: collect every failed check, then fail once with the full list.

A UI journey is slow to run, so an end-to-end test should report everything that is
wrong with the journey in a single run instead of stopping at the first mismatch.
"""

from __future__ import annotations

from types import TracebackType
from typing import Any


class SoftAssert:
    """Context manager that defers assertion failures until the block exits.

    Usage::

        with SoftAssert() as check:
            check.equal(receipt.stake, stake, "receipt stake")
            check.is_true(slip.is_empty(), "bet slip is cleared")
    """

    def __init__(self) -> None:
        self._failures: list[str] = []

    def equal(self, actual: Any, expected: Any, what: str) -> None:
        if actual != expected:
            self._failures.append(f"{what}: expected {expected!r}, got {actual!r}")

    def is_true(self, condition: Any, what: str) -> None:
        if not condition:
            self._failures.append(f"{what}: condition was not met")

    def __enter__(self) -> SoftAssert:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> bool:
        if exc_type is None and self._failures:
            listing = "\n".join(f"  {n}. {msg}" for n, msg in enumerate(self._failures, start=1))
            raise AssertionError(f"{len(self._failures)} check(s) failed:\n{listing}")
        return False
