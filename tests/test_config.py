import os

from src.core.config import CrawlerConfig, setup_logging


class TestCrawlerConfigDefaults:
    def setup_method(self):
        self.config = CrawlerConfig()

    def test_default_base_url(self):
        assert self.config.base_url == "https://finance.yahoo.com/research-hub/screener/equity/"

    def test_default_timeout(self):
        assert self.config.timeout == 30

    def test_default_output_path(self):
        assert self.config.output_path == os.path.join("output", "stocks.csv")

    def test_default_headless(self):
        assert self.config.headless is True

    def test_default_page_size(self):
        assert self.config.page_size == 100


class TestCrawlerConfigCustom:
    def test_custom_values(self):
        config = CrawlerConfig(
            base_url="https://example.com",
            timeout=10,
            output_path="custom.csv",
            headless=False,
            page_size=25,
        )
        assert config.base_url == "https://example.com"
        assert config.timeout == 10
        assert config.output_path == "custom.csv"
        assert config.headless is False
        assert config.page_size == 25

    def test_frozen_config_is_immutable(self):
        config = CrawlerConfig()
        try:
            config.timeout = 99
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass


class TestSetupLogging:
    def test_setup_logging_does_not_raise(self):
        setup_logging("DEBUG")
