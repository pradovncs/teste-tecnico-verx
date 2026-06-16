import os
from unittest.mock import patch

from src.core.config import CrawlerConfig, setup_logging


class TestCrawlerConfig:
    def test_defaults(self):
        config = CrawlerConfig()
        assert "cadesp.fazenda.sp.gov.br" in config.base_url
        assert config.timeout == 30
        assert config.headless is True
        assert config.stealth is True
        assert config.max_captcha_attempts == 3

    def test_is_frozen(self):
        config = CrawlerConfig()
        try:
            config.timeout = 5  # type: ignore[misc]
            assert False, "should be immutable"
        except Exception:
            pass

    def test_reads_anticaptcha_key_from_env(self):
        with patch.dict(os.environ, {"ANTICAPTCHA_KEY": "abc123"}):
            assert CrawlerConfig().anticaptcha_key == "abc123"

    def test_override_values(self):
        config = CrawlerConfig(headless=False, stealth=False, anticaptcha_key="k")
        assert config.headless is False
        assert config.stealth is False
        assert config.anticaptcha_key == "k"


def test_setup_logging_runs():
    setup_logging("DEBUG")
