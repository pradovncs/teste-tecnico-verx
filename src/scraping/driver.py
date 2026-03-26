import logging
from typing import Any, List, Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.core.interfaces import IDriver

logger = logging.getLogger(__name__)


class BrowserDriver(IDriver):
    """Wrapper do Selenium Chrome WebDriver."""

    def __init__(self, headless: bool = True, timeout: int = 30) -> None:
        logger.info("Initializing BrowserDriver headless=%s timeout=%s", headless, timeout)
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/131.0.0.0 Safari/537.36"
        )

        self._driver = webdriver.Chrome(options=options)
        self._timeout = timeout
        logger.info("BrowserDriver initialized successfully")

    def open(self, url: str) -> None:
        """Navigate to the given URL."""
        logger.info("Navigating to url=%s", url)
        self._driver.get(url)

    def find(self, selector: str) -> Any:
        """Find a single element by CSS selector."""
        logger.debug("Finding element selector=%s", selector)
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_all(self, selector: str) -> List[Any]:
        """Find all elements matching the CSS selector."""
        elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
        logger.debug("Found count=%d elements for selector=%s", len(elements), selector)
        return elements

    def wait_for(self, selector: str, timeout: Optional[int] = None) -> Any:
        """Wait for an element to be present in the DOM."""
        t = timeout or self._timeout
        logger.debug("Waiting for selector=%s timeout=%s", selector, t)
        wait = WebDriverWait(self._driver, t)
        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def wait_for_invisible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """Wait for an element to become invisible or absent from the DOM."""
        t = timeout or self._timeout
        logger.debug("Waiting for invisible selector=%s timeout=%s", selector, t)
        wait = WebDriverWait(self._driver, t)
        return wait.until(
            EC.invisibility_of_element_located((By.CSS_SELECTOR, selector))
        )

    def execute_script(self, script: str, *args: Any) -> Any:
        """Execute JavaScript in the browser context."""
        return self._driver.execute_script(script, *args)

    def click_element(self, element: Any) -> None:
        """Click an element using JavaScript to avoid interception issues."""
        self._driver.execute_script("arguments[0].click();", element)

    def get_html(self) -> str:
        """Return the full page source HTML."""
        html = self._driver.page_source
        logger.debug("Got page source length=%d", len(html))
        return html

    def quit(self) -> None:
        """Close the browser and end the session."""
        logger.info("Closing browser")
        self._driver.quit()

    def __enter__(self) -> "BrowserDriver":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.quit()
        return False
