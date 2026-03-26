import logging

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.config import TIMEOUT, HEADLESS

logger = logging.getLogger(__name__)


class BrowserDriver:
    """Controls the Selenium WebDriver for browser automation."""

    def __init__(self, headless=HEADLESS, timeout=TIMEOUT):
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

        service = Service(ChromeDriverManager().install())
        self._driver = webdriver.Chrome(service=service, options=options)
        self._timeout = timeout
        logger.info("BrowserDriver initialized successfully")

    def open(self, url):
        """Navigate to the given URL."""
        logger.info("Navigating to url=%s", url)
        self._driver.get(url)

    def find(self, selector):
        """Find a single element by CSS selector."""
        logger.debug("Finding element selector=%s", selector)
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_all(self, selector):
        """Find all elements matching the CSS selector."""
        elements = self._driver.find_elements(By.CSS_SELECTOR, selector)
        logger.debug("Found count=%d elements for selector=%s", len(elements), selector)
        return elements

    def wait_for(self, selector, timeout=None):
        """Wait for an element to be present in the DOM."""
        t = timeout or self._timeout
        logger.debug("Waiting for selector=%s timeout=%s", selector, t)
        wait = WebDriverWait(self._driver, t)
        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def execute_script(self, script, *args):
        """Execute JavaScript in the browser context."""
        return self._driver.execute_script(script, *args)

    def click_element(self, element):
        """Click an element using JavaScript to avoid interception issues."""
        self._driver.execute_script("arguments[0].click();", element)

    def get_html(self):
        """Return the full page source HTML."""
        html = self._driver.page_source
        logger.debug("Got page source length=%d", len(html))
        return html

    def quit(self):
        """Close the browser and end the session."""
        logger.info("Closing browser")
        self._driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        return False
