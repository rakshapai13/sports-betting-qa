"""Thin client for the Sports Betting REST API.

Read helpers (`get_matches`, `get_balance`) return domain values and raise on an
unexpected status. Write helpers return the raw ``requests.Response`` so that tests
can assert on status codes and error bodies of negative cases.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any

import requests

from betting_qa.api.models import Match, Selection
from betting_qa.utils.money import to_money

log = logging.getLogger(__name__)

USER_ID_HEADER = "x-user-id"


class BettingApiClient:
    """Calls the API on behalf of one user (identified by the ``x-user-id`` header)."""

    def __init__(self, base_url: str, user_id: str, timeout: float = 15.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({USER_ID_HEADER: user_id})

    def close(self) -> None:
        self._session.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> requests.Response:
        response = self._session.request(
            method, f"{self._base_url}{path}", timeout=self._timeout, **kwargs
        )
        log.info("%s %s -> %s %s", method, path, response.status_code, response.text[:300])
        return response

    def get_matches(self) -> list[Match]:
        response = self._request("GET", "/api/matches")
        response.raise_for_status()
        return [Match.from_api(item) for item in response.json()]

    def get_balance(self) -> Decimal:
        """Persisted balance. This is the source of truth for every balance assertion."""
        response = self._request("GET", "/api/balance")
        response.raise_for_status()
        return to_money(response.json()["balance"])

    def reset_balance(self) -> requests.Response:
        return self._request("POST", "/api/reset-balance")

    def place_bet(
        self, match_id: str, selection: Selection | str, stake: Decimal | float
    ) -> requests.Response:
        """Place a single bet. Accepts invalid values on purpose, for negative tests."""
        payload = {
            "matchId": match_id,
            "selection": selection.value if isinstance(selection, Selection) else selection,
            "stake": float(stake),
        }
        return self._request("POST", "/api/place-bet", json=payload)
