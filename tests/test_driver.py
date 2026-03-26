from unittest.mock import patch, MagicMock

from src.driver import BrowserDriver


class TestBrowserDriverInit:
    """Tests for BrowserDriver initialization."""

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_creates_driver_with_headless(self, mock_service, mock_chrome, mock_manager):
        driver = BrowserDriver(headless=True)
        options_used = mock_chrome.call_args[1]["options"]
        assert "--headless=new" in options_used.arguments
        driver.quit()

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_creates_driver_without_headless(self, mock_service, mock_chrome, mock_manager):
        driver = BrowserDriver(headless=False)
        options_used = mock_chrome.call_args[1]["options"]
        assert "--headless=new" not in options_used.arguments
        driver.quit()


class TestBrowserDriverNavigation:
    """Tests for BrowserDriver navigation methods."""

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_open_calls_get(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        driver = BrowserDriver()
        driver.open("https://example.com")

        mock_instance.get.assert_called_once_with("https://example.com")
        driver.quit()

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_find_uses_css_selector(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        driver = BrowserDriver()
        driver.find("table.results")

        mock_instance.find_element.assert_called_once()
        driver.quit()

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_find_all_uses_css_selector(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        driver = BrowserDriver()
        driver.find_all("tr.row")

        mock_instance.find_elements.assert_called_once()
        driver.quit()

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_get_html_returns_page_source(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_instance.page_source = "<html><body>Test</body></html>"
        mock_chrome.return_value = mock_instance

        driver = BrowserDriver()
        html = driver.get_html()

        assert html == "<html><body>Test</body></html>"
        driver.quit()


class TestBrowserDriverWaitFor:
    """Tests for BrowserDriver wait_for method."""

    @patch("src.driver.WebDriverWait")
    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_wait_for_uses_default_timeout(
        self, mock_service, mock_chrome, mock_manager, mock_wait
    ):
        driver = BrowserDriver(timeout=10)
        driver.wait_for("table")

        mock_wait.assert_called_once_with(driver._driver, 10)
        driver.quit()

    @patch("src.driver.WebDriverWait")
    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_wait_for_uses_custom_timeout(
        self, mock_service, mock_chrome, mock_manager, mock_wait
    ):
        driver = BrowserDriver(timeout=10)
        driver.wait_for("table", timeout=30)

        mock_wait.assert_called_once_with(driver._driver, 30)
        driver.quit()


class TestBrowserDriverContextManager:
    """Tests for BrowserDriver context manager."""

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_context_manager_calls_quit(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        with BrowserDriver() as driver:
            driver.open("https://example.com")

        mock_instance.quit.assert_called_once()

    @patch("src.driver.ChromeDriverManager")
    @patch("src.driver.webdriver.Chrome")
    @patch("src.driver.Service")
    def test_context_manager_quits_on_exception(self, mock_service, mock_chrome, mock_manager):
        mock_instance = MagicMock()
        mock_chrome.return_value = mock_instance

        try:
            with BrowserDriver() as driver:
                raise ValueError("test error")
        except ValueError:
            pass

        mock_instance.quit.assert_called_once()
