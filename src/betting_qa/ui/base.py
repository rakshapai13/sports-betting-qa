"""Wait helpers shared by the page object and its components. Nothing here sleeps."""

from __future__ import annotations

from contextlib import suppress

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]


class UiObject:
    def __init__(self, driver: WebDriver, timeout: float = 10) -> None:
        self.driver = driver
        self.timeout = timeout

    def wait_until(self, condition, timeout: float | None = None):
        return WebDriverWait(self.driver, timeout or self.timeout).until(condition)

    def visible(self, locator: Locator) -> WebElement:
        return self.wait_until(EC.visibility_of_element_located(locator))

    def text_of(self, locator: Locator) -> str:
        return self.visible(locator).text.strip()

    def is_present(self, locator: Locator) -> bool:
        return bool(self.driver.find_elements(*locator))

    def click(self, locator: Locator) -> None:
        # The header is sticky. Without centring first, a card low in the list gets
        # scrolled up underneath it and the header takes the click.
        element = self.wait_until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.wait_until(EC.element_to_be_clickable(locator)).click()

    def wait_gone(self, locator: Locator) -> None:
        self.wait_until(EC.invisibility_of_element_located(locator))

    def eventually(self, read, expected):
        """Poll `read()` until it returns `expected`.

        Returns the last value seen even on timeout, so the caller's assert can
        report what was actually on screen.
        """
        last = read()

        def matches(_driver) -> bool:
            nonlocal last
            last = read()
            return last == expected

        with suppress(TimeoutException):
            self.wait_until(matches)
        return last
