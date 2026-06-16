from unittest.mock import MagicMock

from src.scraping.driver import StealthBrowserDriver


def _driver():
    """Cria o driver sem abrir o navegador real, com a página mockada."""
    d = StealthBrowserDriver.__new__(StealthBrowserDriver)
    d._page = MagicMock()
    d._context = MagicMock()
    d._browser = MagicMock()
    d._playwright = MagicMock()
    d._timeout = 30
    d._min_delay = 0
    d._max_delay = 0
    d._stealth = True
    d._headless = True
    d._browser_name = "chromium"
    return d


class TestDriverMethods:
    def test_open(self):
        d = _driver()
        d.open("http://x")
        d._page.goto.assert_called_once()
        assert d._page.goto.call_args[0][0] == "http://x"

    def test_get_html(self):
        d = _driver()
        d._page.content.return_value = "<html>x</html>"
        assert d.get_html() == "<html>x</html>"

    def test_screenshot_element(self):
        d = _driver()
        el = MagicMock()
        el.screenshot.return_value = b"png"
        assert d.screenshot_element(el) == b"png"

    def test_type_text_clears_and_types(self):
        d = _driver()
        el = MagicMock()
        d.type_text(el, "ab")
        el.fill.assert_called_once_with("")
        assert el.type.call_count == 2

    def test_click_element_uses_native_click(self):
        d = _driver()
        el = MagicMock()
        d.click_element(el)
        el.click.assert_called_once()

    def test_click_element_falls_back_to_force(self):
        d = _driver()
        el = MagicMock()
        el.click.side_effect = [Exception("intercepted"), None]
        d.click_element(el)
        assert el.click.call_count == 2
        assert el.click.call_args.kwargs.get("force") is True

    def test_wait_for_uses_page(self):
        d = _driver()
        d.wait_for("#sel")
        d._page.wait_for_selector.assert_called_once()
        assert d._page.wait_for_selector.call_args[0][0] == "#sel"

    def test_select_option_by_value(self):
        d = _driver()
        d.select_option("#sel", "CNPJ")
        d._page.select_option.assert_called_once_with("#sel", value="CNPJ")

    def test_select_option_falls_back_to_label(self):
        d = _driver()
        d._page.select_option.side_effect = [Exception("no value"), None]
        d.select_option("#sel", "CNPJ")
        assert d._page.select_option.call_count == 2
        assert d._page.select_option.call_args.kwargs.get("label") == "CNPJ"

    def test_recover_recreates_context(self):
        d = _driver()
        d._new_context = MagicMock()
        d.recover()
        d._new_context.assert_called_once()

    def test_quit_closes_everything(self):
        d = _driver()
        context, browser, pw = d._context, d._browser, d._playwright
        d.quit()
        context.close.assert_called_once()
        browser.close.assert_called_once()
        pw.stop.assert_called_once()

    def test_context_manager_quits(self):
        d = _driver()
        pw = d._playwright
        with d as ctx:
            assert ctx is d
        pw.stop.assert_called_once()
