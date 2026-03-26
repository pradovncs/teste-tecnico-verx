from unittest.mock import MagicMock

from src.core.models import Stock
from src.scraping.paginator import Paginator


class TestPaginatorScrapeAllPages:
    """Tests for multi-page scraping with deduplication."""

    def test_paginates_through_multiple_pages(self):
        mock_driver = MagicMock()
        mock_driver.get_html.side_effect = [
            "<html>page1</html>",
            "<html>page2</html>",
        ]
        mock_driver.wait_for.return_value = MagicMock()

        next_btn_call_count = [0]

        def mock_find_all(selector):
            if "next-page" in selector:
                next_btn_call_count[0] += 1
                if next_btn_call_count[0] == 1:
                    btn = MagicMock()
                    btn.is_enabled.return_value = True
                    btn.get_attribute.return_value = None
                    return [btn]
                return []
            return []

        mock_driver.find_all.side_effect = mock_find_all

        js_calls = [0]

        def mock_execute_script(script, *args):
            if "data-symbol" in script:
                js_calls[0] += 1
                return "SYM_A" if js_calls[0] <= 1 else "SYM_B"
            return None

        mock_driver.execute_script.side_effect = mock_execute_script

        mock_parser = MagicMock()
        stocks_p1 = [Stock(symbol="A", name="A Corp", price="10")]
        stocks_p2 = [Stock(symbol="B", name="B Corp", price="20")]
        mock_parser.parse.side_effect = [stocks_p1, stocks_p2]

        paginator = Paginator(mock_driver, mock_parser)
        result = paginator.scrape_all_pages()

        assert len(result) == 2
        assert result[0].symbol == "A"
        assert result[1].symbol == "B"
        assert mock_parser.parse.call_count == 2

    def test_stops_when_next_button_disabled(self):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = "<html>page1</html>"
        mock_driver.wait_for.return_value = MagicMock()

        def mock_find_all(selector):
            if "next-page" in selector:
                btn = MagicMock()
                btn.is_enabled.return_value = False
                return [btn]
            return [MagicMock()]

        mock_driver.find_all.side_effect = mock_find_all

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            Stock(symbol="A", name="A Corp", price="10")
        ]

        paginator = Paginator(mock_driver, mock_parser)
        result = paginator.scrape_all_pages()

        assert len(result) == 1
        assert mock_parser.parse.call_count == 1

    def test_stops_when_no_next_button_found(self):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = "<html>page1</html>"
        mock_driver.wait_for.return_value = MagicMock()

        def mock_find_all(selector):
            if "next-page" in selector:
                return []
            return [MagicMock()]

        mock_driver.find_all.side_effect = mock_find_all

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            Stock(symbol="A", name="A Corp", price="10")
        ]

        paginator = Paginator(mock_driver, mock_parser)
        result = paginator.scrape_all_pages()

        assert len(result) == 1

    def test_deduplicates_stocks_across_pages(self):
        mock_driver = MagicMock()
        mock_driver.get_html.side_effect = ["<html>p1</html>", "<html>p2</html>"]
        mock_driver.wait_for.return_value = MagicMock()

        call_count = [0]

        def mock_find_all(selector):
            if "next-page" in selector:
                call_count[0] += 1
                if call_count[0] == 1:
                    btn = MagicMock()
                    btn.is_enabled.return_value = True
                    btn.get_attribute.return_value = None
                    return [btn]
                return []
            return []

        mock_driver.find_all.side_effect = mock_find_all

        js_calls = [0]

        def mock_execute_script(script, *args):
            if "data-symbol" in script:
                js_calls[0] += 1
                return "SYM_P1" if js_calls[0] <= 1 else "SYM_P2"
            return None

        mock_driver.execute_script.side_effect = mock_execute_script

        mock_parser = MagicMock()
        mock_parser.parse.side_effect = [
            [Stock(symbol="A", name="A Corp", price="10"),
             Stock(symbol="B", name="B Corp", price="20")],
            [Stock(symbol="A", name="A Corp", price="10"),
             Stock(symbol="C", name="C Corp", price="30")],
        ]

        paginator = Paginator(mock_driver, mock_parser)
        result = paginator.scrape_all_pages()

        assert [s.symbol for s in result] == ["A", "B", "C"]


class TestPaginatorPageSize:
    """Tests for setting the page size."""

    def test_set_page_size_clicks_button_via_js(self):
        mock_driver = MagicMock()
        mock_btn = MagicMock()
        mock_driver.wait_for.return_value = mock_btn
        mock_driver.execute_script.return_value = True

        paginator = Paginator(mock_driver, MagicMock())
        paginator.set_page_size(100)

        mock_driver.click_element.assert_called_once_with(mock_btn)

    def test_set_page_size_handles_timeout(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.side_effect = Exception("timeout")

        paginator = Paginator(mock_driver, MagicMock())
        paginator.set_page_size(100)


class TestPaginatorWaitForTable:
    """Tests for waiting for the table to load."""

    def test_wait_for_table_calls_driver(self):
        mock_driver = MagicMock()

        paginator = Paginator(mock_driver, MagicMock())
        paginator.wait_for_table()

        mock_driver.wait_for.assert_called_once_with("table tbody tr")
