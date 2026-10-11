"""Client for the Sports Betting REST API."""

from __future__ import annotations

import logging
from decimal import Decimal

import requests

from betting_qa.api.models import Match, Selection
from betting_qa.utils.money import to_money

log = logging.getLogger(__name__)


class BettingApiClient:
    def __init__(self, base_url: str, user_id: str, timeout: float = 15) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers["x-user-id"] = user_id

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        response = self.session.request(
            method, self.base_url + path, timeout=self.timeout, **kwargs
        )
        log.info("%s %s -> %s %s", method, path, response.status_code, response.text[:200])
        return response

    def get_matches(self) -> list[Match]:
        response = self._request("GET", "/api/matches")
        response.raise_for_status()
        return [Match.from_api(item) for item in response.json()]

    def get_balance(self) -> Decimal:
        response = self._request("GET", "/api/balance")
        response.raise_for_status()
        return to_money(response.json()["balance"])

    def reset_balance(self) -> requests.Response:
        return self._request("POST", "/api/reset-balance")

    def place_bet(self, match_id: str, selection: Selection, stake: Decimal) -> requests.Response:
        """Returns the raw response so a test can check the status and error body itself."""
        body = {"matchId": match_id, "selection": selection.value, "stake": float(stake)}
        return self._request("POST", "/api/place-bet", json=body)
