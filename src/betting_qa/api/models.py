"""Match and selection, as used by the API client, the page objects and the tests."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum


class Selection(str, Enum):
    HOME = "HOME"
    DRAW = "DRAW"
    AWAY = "AWAY"

    @property
    def key(self) -> str:
        """Lower-case name, as used in the API odds object and in the odds button ids."""
        return self.value.lower()

    @property
    def label(self) -> str:
        """Name as the bet slip shows it: 'Home', 'Draw', 'Away'."""
        return self.value.capitalize()


@dataclass(frozen=True)
class Match:
    id: str
    kickoff_date: date
    home_team: str
    away_team: str
    odds: dict[Selection, Decimal]

    @classmethod
    def from_api(cls, data: dict) -> Match:
        return cls(
            id=data["id"],
            kickoff_date=date.fromisoformat(data["kickoffDate"]),
            home_team=data["homeTeam"],
            away_team=data["awayTeam"],
            odds={s: Decimal(str(data["odds"][s.key])) for s in Selection},
        )

    @property
    def fixture(self) -> str:
        """Home team first, as the spec requires everywhere the match is shown."""
        return f"{self.home_team} vs {self.away_team}"
