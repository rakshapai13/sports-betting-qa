"""Runtime configuration, read once from environment variables (or a local .env file).

Nothing environment-specific is hard-coded in tests or page objects: point the same
suite at another deployment or user by changing the environment, not the code.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

DEFAULT_BASE_URL = "https://qae-assignment-tau.vercel.app"
_TRUTHY = {"1", "true", "yes", "on"}


class ConfigurationError(RuntimeError):
    """Raised when the suite is started without the configuration it needs."""


def _flag(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    return default if raw is None else raw.strip().lower() in _TRUTHY


@dataclass(frozen=True)
class Settings:
    """Everything the suite needs to know about where and how it runs."""

    base_url: str
    user_id: str
    headless: bool = True
    window_width: int = 1440
    window_height: int = 900
    ui_timeout: float = 10.0
    bet_outcome_timeout: float = 20.0
    api_timeout: float = 15.0
    chrome_binary: str | None = None
    chromedriver_path: str | None = None

    @classmethod
    def from_env(cls) -> Settings:
        load_dotenv()
        user_id = os.getenv("QA_USER_ID", "").strip()
        if not user_id:
            raise ConfigurationError(
                "QA_USER_ID is not set. Export it or copy .env.example to .env "
                "and fill in your user id."
            )
        return cls(
            base_url=os.getenv("QA_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
            user_id=user_id,
            headless=_flag("QA_HEADLESS", default=True),
            ui_timeout=float(os.getenv("QA_UI_TIMEOUT", "10")),
            bet_outcome_timeout=float(os.getenv("QA_BET_TIMEOUT", "20")),
            api_timeout=float(os.getenv("QA_API_TIMEOUT", "15")),
            chrome_binary=os.getenv("QA_CHROME_BINARY") or None,
            chromedriver_path=os.getenv("QA_CHROMEDRIVER") or None,
        )

    @property
    def app_url(self) -> str:
        """UI entry point. The application authenticates through the query string."""
        return f"{self.base_url}/?user-id={self.user_id}"
