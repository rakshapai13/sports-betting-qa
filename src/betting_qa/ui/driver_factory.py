"""Browser start-up. Selenium Manager finds the matching chromedriver by itself."""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.remote.webdriver import WebDriver

from betting_qa.config import Settings


def create_chrome_driver(settings: Settings) -> WebDriver:
    width, height = settings.window_size
    options = Options()
    options.add_argument(f"--window-size={width},{height}")
    if settings.headless:
        options.add_argument("--headless=new")
    # Needed on CI runners and in containers, makes no difference on a laptop.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)
