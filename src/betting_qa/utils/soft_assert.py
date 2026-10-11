"""Soft assertions: run every check in a block, then fail once with the full list."""

from __future__ import annotations


class SoftAssert:
    """
    with SoftAssert() as check:
        check.equal(receipt.stake, stake, "receipt stake")
        check.is_true(receipt.bet_id, "receipt has a bet id")
    """

    def __init__(self) -> None:
        self.failures: list[str] = []

    def equal(self, actual, expected, what: str) -> None:
        if actual != expected:
            self.failures.append(f"{what}: expected {expected!r}, got {actual!r}")

    def is_true(self, condition, what: str) -> None:
        if not condition:
            self.failures.append(f"{what}: not true")

    def __enter__(self) -> SoftAssert:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # If the block itself blew up, let that error through instead of masking it.
        if exc_type is None and self.failures:
            lines = "\n".join(f"  {i}. {msg}" for i, msg in enumerate(self.failures, start=1))
            raise AssertionError(f"{len(self.failures)} check(s) failed:\n{lines}")
