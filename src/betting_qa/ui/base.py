"""Shared Selenium plumbing for page objects and page components.

Only this module talks to ``WebDriverWait``. Pages and components express intent
("click", "read text", "wait until gone") and never sleep.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from typing import TypeVar

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

Locator = tuple[str, str]
T = TypeVar("T")


class UiObject:
    """Base class for anything that reads from or acts on the browser."""

    def __init__(self, driver: WebDriver, timeout: float = 10.0) -> None:
        self.driver = driver
        self.timeout = timeout

    def wait_until(self, condition: Callable[[WebDriver], T], timeout: float | None = None) -> T:
        return WebDriverWait(self.driver, timeout or self.timeout).until(condition)

    def visible(self, locator: Locator, timeout: float | None = None) -> WebElement:
        return self.wait_until(EC.visibility_of_element_located(locator), timeout)

    def is_present(self, locator: Locator) -> bool:
        return bool(self.driver.find_elements(*locator))

    def text_of(self, locator: Locator) -> str:
        return self.visible(locator).text.strip()

    def click(self, locator: Locator) -> None:
        """Scroll the element to mid-viewport (clear of the sticky header), then click."""
        element = self.wait_until(EC.presence_of_element_located(locator))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
        self.wait_until(EC.element_to_be_clickable(locator)).click()

    def wait_gone(self, locator: Locator, timeout: float | None = None) -> None:
        self.wait_until(EC.invisibility_of_element_located(locator), timeout)

    def eventually(self, read: Callable[[], T], expected: T, timeout: float | None = None) -> T:
        """Poll ``read`` until it returns ``expected``; return the last value either way.

        Lets a test assert on a value that updates asynchronously and still report
        what the UI actually showed when the wait ran out.
        """
        last = read()

        def matches(_: WebDriver) -> bool:
            nonlocal last
            last = read()
            return last == expected

        with suppress(TimeoutException):
            self.wait_until(matches, timeout)
        return last
