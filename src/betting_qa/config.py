"""Run settings, read from environment variables or a local .env file."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://qae-assignment-tau.vercel.app"


@dataclass(frozen=True)
class Settings:
    base_url: str
    user_id: str
    headless: bool = True
    window_size: tuple[int, int] = (1440, 900)
    ui_timeout: float = 10
    bet_timeout: float = 20  # a placement normally resolves in 2-3 seconds
    api_timeout: float = 15

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        user_id = os.getenv("QA_USER_ID", "").strip()
        if not user_id:
            raise RuntimeError(
                "QA_USER_ID is not set. Export it or add it to a .env file (see .env.example)."
            )
        return cls(
            base_url=os.getenv("QA_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            user_id=user_id,
            headless=os.getenv("QA_HEADLESS", "1") != "0",
        )

    @property
    def app_url(self) -> str:
        # The UI takes the user from the query string; the API takes it from a header.
        return f"{self.base_url}/?user-id={self.user_id}"
