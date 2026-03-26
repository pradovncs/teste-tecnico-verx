from unittest.mock import MagicMock, patch

from src.core.config import CrawlerConfig
from src.crawler import YahooFinanceCrawler
from src.core.models import Stock


@patch("src.crawler.Paginator")
@patch("src.crawler.RegionFilter")
@patch("src.crawler.ConsentHandler")
class TestYahooFinanceCrawlerCrawl:
    """Tests for the main crawl orchestration flow."""

    def test_opens_base_url(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        config = CrawlerConfig()
        mock_driver = MagicMock()
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []

        crawler = YahooFinanceCrawler(config=config, driver=mock_driver)
        crawler.crawl("Brazil", output_path=None)

        mock_driver.open.assert_called_once_with(config.base_url)

    def test_delegates_to_consent_handler(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []

        crawler = YahooFinanceCrawler(driver=mock_driver)
        crawler.crawl("Brazil", output_path=None)

        mock_consent_cls.assert_called_once_with(mock_driver)
        mock_consent_cls.return_value.dismiss.assert_called_once()

    def test_delegates_to_region_filter(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []

        crawler = YahooFinanceCrawler(driver=mock_driver)
        crawler.crawl("Brazil", output_path=None)

        mock_filter_cls.assert_called_once_with(mock_driver)
        mock_filter_cls.return_value.apply.assert_called_once_with("Brazil")

    def test_delegates_to_paginator(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        mock_parser = MagicMock()
        stocks = [Stock(symbol="A", name="A Corp", price="10")]
        mock_paginator_cls.return_value.scrape_all_pages.return_value = stocks

        crawler = YahooFinanceCrawler(driver=mock_driver, parser=mock_parser)
        result = crawler.crawl("Brazil", output_path=None)

        mock_paginator_cls.assert_called_once_with(mock_driver, mock_parser)
        mock_paginator_cls.return_value.wait_for_table.assert_called_once()
        mock_paginator_cls.return_value.set_page_size.assert_called_once_with(100)
        mock_paginator_cls.return_value.scrape_all_pages.assert_called_once()
        assert result == stocks

    def test_calls_exporter_with_data_and_path(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls, tmp_path):
        mock_driver = MagicMock()
        stocks = [Stock(symbol="TEST", name="Test Corp", price="100.00")]
        mock_paginator_cls.return_value.scrape_all_pages.return_value = stocks
        mock_exporter = MagicMock()

        filepath = str(tmp_path / "output.csv")
        crawler = YahooFinanceCrawler(driver=mock_driver, exporter=mock_exporter)
        crawler.crawl("Brazil", output_path=filepath)

        mock_exporter.export.assert_called_once_with(stocks, filepath)

    def test_returns_parsed_stocks(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        expected = [
            Stock(symbol="AMX.BA", name="América Móvil", price="2089.00"),
            Stock(symbol="NOKA.BA", name="Nokia Corporation", price="557.50"),
        ]
        mock_paginator_cls.return_value.scrape_all_pages.return_value = expected

        crawler = YahooFinanceCrawler(driver=mock_driver)
        result = crawler.crawl("Brazil", output_path=None)

        assert result == expected

    def test_uses_config_default_output(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        stocks = [Stock(symbol="A", name="A Corp", price="10")]
        mock_paginator_cls.return_value.scrape_all_pages.return_value = stocks
        mock_exporter = MagicMock()

        crawler = YahooFinanceCrawler(driver=mock_driver, exporter=mock_exporter)
        crawler.crawl("Brazil")

        mock_exporter.export.assert_called_once_with(stocks, CrawlerConfig().output_path)

    def test_skips_export_when_output_path_is_empty(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []
        mock_exporter = MagicMock()

        crawler = YahooFinanceCrawler(driver=mock_driver, exporter=mock_exporter)
        crawler.crawl("Brazil", output_path="")

        mock_exporter.export.assert_not_called()

    def test_does_not_quit_injected_driver(self, mock_consent_cls, mock_filter_cls, mock_paginator_cls):
        mock_driver = MagicMock()
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []

        crawler = YahooFinanceCrawler(driver=mock_driver)
        crawler.crawl("Brazil", output_path=None)

        mock_driver.quit.assert_not_called()


class TestYahooFinanceCrawlerDefaults:
    """Tests for default dependency injection."""

    @patch("src.crawler.Paginator")
    @patch("src.crawler.RegionFilter")
    @patch("src.crawler.ConsentHandler")
    @patch("src.crawler.BrowserDriver")
    def test_creates_and_quits_driver_when_none_injected(
        self, mock_driver_cls, mock_consent_cls, mock_filter_cls, mock_paginator_cls
    ):
        mock_instance = MagicMock()
        mock_driver_cls.return_value = mock_instance
        mock_paginator_cls.return_value.scrape_all_pages.return_value = []

        crawler = YahooFinanceCrawler()
        crawler.crawl("Brazil", output_path="")

        mock_driver_cls.assert_called_once()
        mock_instance.quit.assert_called_once()

    def test_uses_default_parser_and_exporter(self):
        crawler = YahooFinanceCrawler()
        assert crawler._parser is not None
        assert crawler._exporter is not None

    def test_uses_default_config(self):
        crawler = YahooFinanceCrawler()
        assert crawler._config is not None
        assert crawler._config.base_url == "https://finance.yahoo.com/research-hub/screener/equity/"
