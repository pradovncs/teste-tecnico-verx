from unittest.mock import MagicMock, patch

from src.scraping.driver import StealthBrowserDriver


def _driver():
    """Cria o driver sem abrir o navegador real, com _driver mockado."""
    d = StealthBrowserDriver.__new__(StealthBrowserDriver)
    d._driver = MagicMock()
    d._timeout = 30
    d._min_delay = 0
    d._max_delay = 0
    return d


class TestDriverMethods:
    def test_open(self):
        d = _driver()
        d.open("http://x")
        d._driver.get.assert_called_once_with("http://x")

    def test_get_html(self):
        d = _driver()
        d._driver.page_source = "<html>x</html>"
        assert d.get_html() == "<html>x</html>"

    def test_screenshot_element(self):
        d = _driver()
        el = MagicMock()
        el.screenshot_as_png = b"png"
        assert d.screenshot_element(el) == b"png"

    def test_type_text_clears_and_sends(self):
        d = _driver()
        el = MagicMock()
        d.type_text(el, "ab")
        el.clear.assert_called_once()
        assert el.send_keys.call_count == 2

    def test_click_element_uses_native_click(self):
        d = _driver()
        el = MagicMock()
        d.click_element(el)
        el.click.assert_called_once()

    def test_click_element_falls_back_to_js(self):
        d = _driver()
        el = MagicMock()
        el.click.side_effect = Exception("intercepted")
        d.click_element(el)
        d._driver.execute_script.assert_called_once()

    @patch("src.scraping.driver.Select")
    def test_select_option_by_value(self, mock_select_cls):
        d = _driver()
        d.wait_for = MagicMock(return_value=MagicMock())
        d.select_option("#sel", "CNPJ")
        mock_select_cls.return_value.select_by_value.assert_called_once_with("CNPJ")

    @patch("src.scraping.driver.Select")
    def test_select_option_falls_back_to_text(self, mock_select_cls):
        d = _driver()
        d.wait_for = MagicMock(return_value=MagicMock())
        mock_select_cls.return_value.select_by_value.side_effect = Exception("no value")
        d.select_option("#sel", "CNPJ")
        mock_select_cls.return_value.select_by_visible_text.assert_called_once_with("CNPJ")

    def test_quit(self):
        d = _driver()
        d.quit()
        d._driver.quit.assert_called_once()

    def test_context_manager_quits(self):
        d = _driver()
        with d as ctx:
            assert ctx is d
        d._driver.quit.assert_called_once()
