"""Fixtures shared by the API and UI tests."""

from __future__ import annotations

import re
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from selenium.webdriver.remote.webdriver import WebDriver

from betting_qa.api.client import BettingApiClient
from betting_qa.api.data_setup import pick_upcoming_match
from betting_qa.api.models import Match
from betting_qa.config import Settings
from betting_qa.ui.driver_factory import create_chrome_driver
from betting_qa.ui.pages.betting_page import BettingPage

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--headed",
        action="store_true",
        help="Show the browser window (overrides QA_HEADLESS).",
    )


@pytest.fixture(scope="session")
def settings(pytestconfig: pytest.Config) -> Settings:
    loaded = Settings.from_env()
    if pytestconfig.getoption("--headed"):
        loaded = replace(loaded, headless=False)
    return loaded


@pytest.fixture(scope="session")
def api_client(settings: Settings) -> Iterator[BettingApiClient]:
    client = BettingApiClient(settings.base_url, settings.user_id, settings.api_timeout)
    yield client
    client.close()


@pytest.fixture(autouse=True)
def known_balance(api_client: BettingApiClient) -> Iterator[None]:
    """Give every test the same starting balance and leave the account clean afterwards.

    Tests share one user account, so each test resets it rather than depending on what
    an earlier test (or a manual session) left behind.
    """
    api_client.reset_balance().raise_for_status()
    yield
    api_client.reset_balance()


@pytest.fixture
def upcoming_match(api_client: BettingApiClient) -> Match:
    """A real upcoming match taken from the live catalogue (no hard-coded ids or odds)."""
    return pick_upcoming_match(api_client.get_matches())


@pytest.fixture
def driver(settings: Settings) -> Iterator[WebDriver]:
    browser = create_chrome_driver(settings)
    yield browser
    browser.quit()


@pytest.fixture
def betting_page(driver: WebDriver, settings: Settings) -> BettingPage:
    return BettingPage(driver, settings).open()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]) -> Iterator[None]:
    """Save a screenshot when a UI test fails, so a failure can be triaged without a re-run."""
    outcome = yield
    report = outcome.get_result()
    browser = getattr(item, "funcargs", {}).get("driver")
    if report.when == "call" and report.failed and browser is not None:
        ARTIFACTS_DIR.mkdir(exist_ok=True)
        target = ARTIFACTS_DIR / f"{re.sub(r'[^A-Za-z0-9_.-]+', '_', item.nodeid)}.png"
        browser.save_screenshot(str(target))
        report.sections.append(("screenshot", str(target)))
