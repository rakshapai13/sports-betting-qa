"""Creates the browser. The only place that knows which browser is used and how it is configured."""

from __future__ import annotations

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webdriver import WebDriver

from betting_qa.config import Settings


def create_chrome_driver(settings: Settings) -> WebDriver:
    """Start desktop Chrome.

    Selenium Manager (bundled with Selenium 4.6+) downloads a matching chromedriver
    automatically; ``QA_CHROME_BINARY`` / ``QA_CHROMEDRIVER`` override that for CI
    images or locked-down machines.
    """
    options = ChromeOptions()
    if settings.headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={settings.window_width},{settings.window_height}")
    # Needed inside containers and CI runners; harmless on a workstation.
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    if settings.chrome_binary:
        options.binary_location = settings.chrome_binary

    service = ChromeService(executable_path=settings.chromedriver_path)
    driver = webdriver.Chrome(options=options, service=service)
    driver.set_page_load_timeout(30)
    return driver
