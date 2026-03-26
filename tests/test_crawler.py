from unittest.mock import MagicMock, patch

from src.crawler import YahooFinanceCrawler
from src.config import BASE_URL


class TestYahooFinanceCrawlerCrawl:
    """Tests for the main crawl orchestration flow."""

    def _make_mock_driver(self, html="<html></html>"):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = html
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        return mock_driver

    def test_opens_base_url(self):
        mock_driver = self._make_mock_driver()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = []

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        crawler.crawl("Brazil", output_path=None)

        mock_driver.open.assert_called_once_with(BASE_URL)

    def test_calls_parser_with_html(self):
        html = "<html><table><tbody><tr></tr></tbody></table></html>"
        mock_driver = self._make_mock_driver(html)
        mock_parser = MagicMock()
        mock_parser.parse.return_value = []

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        crawler.crawl("Brazil", output_path=None)

        mock_parser.parse.assert_called_once_with(html)

    def test_calls_exporter_with_data_and_path(self, tmp_path):
        mock_driver = self._make_mock_driver()
        mock_parser = MagicMock()
        stocks = [{"symbol": "TEST", "name": "Test Corp", "price": "100.00"}]
        mock_parser.parse.return_value = stocks
        mock_exporter = MagicMock()

        filepath = str(tmp_path / "output.csv")
        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser, exporter=mock_exporter
        )
        crawler.crawl("Brazil", output_path=filepath)

        mock_exporter.export.assert_called_once_with(stocks, filepath)

    def test_returns_parsed_stocks(self):
        mock_driver = self._make_mock_driver()
        mock_parser = MagicMock()
        expected = [
            {"symbol": "AMX.BA", "name": "América Móvil", "price": "2089.00"},
            {"symbol": "NOKA.BA", "name": "Nokia Corporation", "price": "557.50"},
        ]
        mock_parser.parse.return_value = expected

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        result = crawler.crawl("Brazil", output_path=None)

        assert result == expected

    def test_skips_export_when_output_path_is_none(self):
        mock_driver = self._make_mock_driver()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = []
        mock_exporter = MagicMock()

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser, exporter=mock_exporter
        )
        crawler.crawl("Brazil", output_path=None)

        mock_exporter.export.assert_not_called()

    def test_does_not_quit_injected_driver(self):
        mock_driver = self._make_mock_driver()
        mock_parser = MagicMock()
        mock_parser.parse.return_value = []

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        crawler.crawl("Brazil", output_path=None)

        mock_driver.quit.assert_not_called()


class TestYahooFinanceCrawlerPagination:
    """Tests for multi-page scraping via next button."""

    def test_paginates_through_multiple_pages(self):
        mock_driver = MagicMock()
        mock_driver.get_html.side_effect = [
            "<html>page1</html>",
            "<html>page2</html>",
        ]
        mock_driver.wait_for.return_value = MagicMock()

        next_btn_call_count = [0]

        def mock_find_all(selector):
            if "Next" in selector or "next-page" in selector:
                next_btn_call_count[0] += 1
                if next_btn_call_count[0] == 1:
                    btn = MagicMock()
                    btn.is_enabled.return_value = True
                    btn.get_attribute.return_value = None
                    return [btn]
                return []
            return [MagicMock()]

        mock_driver.find_all.side_effect = mock_find_all

        mock_parser = MagicMock()
        stocks_p1 = [{"symbol": "A", "name": "A Corp", "price": "10"}]
        stocks_p2 = [{"symbol": "B", "name": "B Corp", "price": "20"}]
        mock_parser.parse.side_effect = [stocks_p1, stocks_p2]

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        result = crawler.crawl("Brazil", output_path=None)

        assert len(result) == 2
        assert result[0]["symbol"] == "A"
        assert result[1]["symbol"] == "B"
        assert mock_parser.parse.call_count == 2

    def test_stops_when_next_button_disabled(self):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = "<html>page1</html>"
        mock_driver.wait_for.return_value = MagicMock()

        def mock_find_all(selector):
            if "Next" in selector or "next-page" in selector:
                btn = MagicMock()
                btn.is_enabled.return_value = False
                return [btn]
            return [MagicMock()]

        mock_driver.find_all.side_effect = mock_find_all

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            {"symbol": "A", "name": "A Corp", "price": "10"}
        ]

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        result = crawler.crawl("Brazil", output_path=None)

        assert len(result) == 1
        assert mock_parser.parse.call_count == 1

    def test_stops_when_no_next_button_found(self):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = "<html>page1</html>"
        mock_driver.wait_for.return_value = MagicMock()

        def mock_find_all(selector):
            if "Next" in selector or "next-page" in selector:
                return []
            return [MagicMock()]

        mock_driver.find_all.side_effect = mock_find_all

        mock_parser = MagicMock()
        mock_parser.parse.return_value = [
            {"symbol": "A", "name": "A Corp", "price": "10"}
        ]

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        result = crawler.crawl("Brazil", output_path=None)

        assert len(result) == 1


class TestYahooFinanceCrawlerFilter:
    """Tests for the region filter application."""

    def test_waits_for_table_after_filter(self):
        mock_driver = MagicMock()
        mock_driver.get_html.return_value = "<html></html>"
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]

        mock_parser = MagicMock()
        mock_parser.parse.return_value = []

        crawler = YahooFinanceCrawler(
            driver=mock_driver, parser=mock_parser
        )
        crawler.crawl("Brazil", output_path=None)

        assert mock_driver.wait_for.call_count >= 1


class TestYahooFinanceCrawlerDefaults:
    """Tests for default dependency injection."""

    @patch("src.crawler.BrowserDriver")
    def test_creates_driver_when_none_injected(self, mock_driver_cls):
        mock_instance = MagicMock()
        mock_instance.get_html.return_value = "<html></html>"
        mock_instance.wait_for.return_value = MagicMock()
        mock_instance.find.return_value = MagicMock()
        mock_instance.find_all.return_value = [MagicMock()]
        mock_driver_cls.return_value = mock_instance

        mock_parser = MagicMock()
        mock_parser.parse.return_value = []

        crawler = YahooFinanceCrawler(parser=mock_parser)
        crawler.crawl("Brazil", output_path=None)

        mock_driver_cls.assert_called_once()
        mock_instance.quit.assert_called_once()

    def test_uses_default_parser_and_exporter(self):
        crawler = YahooFinanceCrawler()
        assert crawler._parser is not None
        assert crawler._exporter is not None
