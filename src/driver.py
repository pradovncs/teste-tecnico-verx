from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from src.config import TIMEOUT, HEADLESS


class BrowserDriver:
    """Controls the Selenium WebDriver for browser automation."""

    def __init__(self, headless=HEADLESS, timeout=TIMEOUT):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        service = Service(ChromeDriverManager().install())
        self._driver = webdriver.Chrome(service=service, options=options)
        self._timeout = timeout

    def open(self, url):
        """Navigate to the given URL."""
        self._driver.get(url)

    def find(self, selector):
        """Find a single element by CSS selector."""
        return self._driver.find_element(By.CSS_SELECTOR, selector)

    def find_all(self, selector):
        """Find all elements matching the CSS selector."""
        return self._driver.find_elements(By.CSS_SELECTOR, selector)

    def wait_for(self, selector, timeout=None):
        """Wait for an element to be present in the DOM."""
        wait = WebDriverWait(self._driver, timeout or self._timeout)
        return wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
        )

    def get_html(self):
        """Return the full page source HTML."""
        return self._driver.page_source

    def quit(self):
        """Close the browser and end the session."""
        self._driver.quit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.quit()
        return False
