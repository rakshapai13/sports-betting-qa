"""Domain objects shared by the API client, the page objects and the tests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any


class Selection(str, Enum):
    """The three outcomes of a match-winner market."""

    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"

    @property
    def key(self) -> str:
        """Lower-case form used in the API odds object and in UI element ids."""
        return self.value.lower()

    @property
    def label(self) -> str:
        """Human-readable form shown in the bet slip, e.g. 'Home'."""
        return self.value.capitalize()


@dataclass(frozen=True)
class Match:
    """One football match as returned by ``GET /api/matches``."""

    id: str
    competition: str
    kickoff_date: date
    home_team: str
    away_team: str
    odds: Mapping[Selection, Decimal]

    @classmethod
    def from_api(cls, payload: Mapping[str, Any]) -> Match:
        return cls(
            id=payload["id"],
            competition=payload["competition"],
            kickoff_date=date.fromisoformat(payload["kickoffDate"]),
            home_team=payload["homeTeam"],
            away_team=payload["awayTeam"],
            odds={s: Decimal(str(payload["odds"][s.key])) for s in Selection},
        )

    @property
    def fixture(self) -> str:
        """Display name. The spec fixes the order: home team first, away team second."""
        return f"{self.home_team} vs {self.away_team}"

    def is_upcoming(self, today: date) -> bool:
        return self.kickoff_date > today
