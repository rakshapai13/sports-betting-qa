from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from betting_qa.api.client import BettingApiClient
from betting_qa.api.data_setup import pick_upcoming_match
from betting_qa.config import Settings
from betting_qa.ui.driver_factory import create_chrome_driver
from betting_qa.ui.pages.betting_page import BettingPage

ARTIFACTS = Path(__file__).parent.parent / "artifacts"


def pytest_addoption(parser):
    parser.addoption("--headed", action="store_true", help="run the UI tests in a visible browser")


@pytest.fixture(scope="session")
def settings(pytestconfig) -> Settings:
    settings = Settings.from_env()
    if pytestconfig.getoption("--headed"):
        settings = replace(settings, headless=False)
    return settings


@pytest.fixture(scope="session")
def api_client(settings) -> BettingApiClient:
    return BettingApiClient(settings.base_url, settings.user_id, settings.api_timeout)


@pytest.fixture(autouse=True)
def reset_balance(api_client):
    """All tests share one user account, so each one starts from a reset balance
    and puts it back afterwards."""
    api_client.reset_balance().raise_for_status()
    yield
    api_client.reset_balance()


@pytest.fixture
def upcoming_match(api_client):
    """A real upcoming match from the catalogue, so no match id or odds are hard-coded."""
    return pick_upcoming_match(api_client.get_matches())


@pytest.fixture
def driver(settings):
    driver = create_chrome_driver(settings)
    yield driver
    driver.quit()


@pytest.fixture
def betting_page(driver, settings) -> BettingPage:
    return BettingPage(driver, settings).open()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Save a screenshot when a UI test fails."""
    report = (yield).get_result()
    driver = item.funcargs.get("driver")
    if driver and report.when == "call" and report.failed:
        ARTIFACTS.mkdir(exist_ok=True)
        name = re.sub(r"\W+", "_", item.name)
        driver.save_screenshot(str(ARTIFACTS / f"{name}.png"))
