from unittest.mock import MagicMock, patch

import pytest

from src.core.config import CrawlerConfig
from src.core.exceptions import BlockedError, CaptchaError
from src.core.models import Contribuinte
from src.crawler import CadespCrawler

VALID = "11.222.333/0001-81"


def _contrib():
    return [Contribuinte(cnpj="11222333000181", nome_empresarial="ACME")]


@patch("src.crawler.CnpjConsulta")
class TestCrawl:
    def test_opens_base_url(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = []
        mock_consulta_cls.return_value.run.return_value = "<html></html>"

        crawler = CadespCrawler(driver=driver, solver=MagicMock(), parser=parser)
        crawler.crawl(VALID, output_path="")

        driver.open.assert_called_with(CrawlerConfig().base_url)

    def test_returns_parsed_results(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = _contrib()
        mock_consulta_cls.return_value.run.return_value = "<html>x</html>"

        crawler = CadespCrawler(driver=driver, solver=MagicMock(), parser=parser)
        result = crawler.crawl(VALID, output_path="")

        assert result == _contrib()

    def test_exports_results(self, mock_consulta_cls, tmp_path):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = _contrib()
        exporter = MagicMock()
        mock_consulta_cls.return_value.run.return_value = "<html>x</html>"

        path = str(tmp_path / "out.csv")
        crawler = CadespCrawler(driver=driver, solver=MagicMock(), parser=parser, exporter=exporter)
        crawler.crawl(VALID, output_path=path)

        exporter.export.assert_called_once_with(_contrib(), path)

    def test_skips_export_when_empty_path(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = _contrib()
        exporter = MagicMock()
        mock_consulta_cls.return_value.run.return_value = "<html>x</html>"

        crawler = CadespCrawler(driver=driver, solver=MagicMock(), parser=parser, exporter=exporter)
        crawler.crawl(VALID, output_path="")

        exporter.export.assert_not_called()

    def test_does_not_quit_injected_driver(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = []
        mock_consulta_cls.return_value.run.return_value = "<html></html>"

        crawler = CadespCrawler(driver=driver, solver=MagicMock(), parser=parser)
        crawler.crawl(VALID, output_path="")

        driver.quit.assert_not_called()

    def test_retries_on_captcha_error(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock(); parser.parse.return_value = _contrib()
        # primeira tentativa falha o captcha, segunda funciona
        mock_consulta_cls.return_value.run.side_effect = [
            CaptchaError("recusado"),
            "<html>ok</html>",
        ]
        config = CrawlerConfig(max_captcha_attempts=3)

        crawler = CadespCrawler(config=config, driver=driver, solver=MagicMock(), parser=parser)
        result = crawler.crawl(VALID, output_path="")

        assert result == _contrib()
        assert mock_consulta_cls.return_value.run.call_count == 2

    def test_gives_up_after_max_attempts(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock()
        mock_consulta_cls.return_value.run.side_effect = CaptchaError("recusado")
        config = CrawlerConfig(max_captcha_attempts=2)

        crawler = CadespCrawler(config=config, driver=driver, solver=MagicMock(), parser=parser)
        with pytest.raises(CaptchaError):
            crawler.crawl(VALID, output_path="")
        assert mock_consulta_cls.return_value.run.call_count == 2

    def test_blocked_not_retried(self, mock_consulta_cls):
        driver = MagicMock()
        parser = MagicMock()
        mock_consulta_cls.return_value.run.side_effect = BlockedError("f5")
        config = CrawlerConfig(max_captcha_attempts=3)

        crawler = CadespCrawler(config=config, driver=driver, solver=MagicMock(), parser=parser)
        with pytest.raises(BlockedError):
            crawler.crawl(VALID, output_path="")
        assert mock_consulta_cls.return_value.run.call_count == 1


class TestDefaults:
    @patch("src.crawler.CnpjConsulta")
    @patch("src.crawler.AntiCaptchaSolver")
    @patch("src.crawler.StealthBrowserDriver")
    def test_creates_and_quits_default_driver(
        self, mock_driver_cls, mock_solver_cls, mock_consulta_cls
    ):
        instance = MagicMock()
        mock_driver_cls.return_value = instance
        mock_consulta_cls.return_value.run.return_value = "<html></html>"
        parser = MagicMock(); parser.parse.return_value = []

        config = CrawlerConfig(anticaptcha_key="key")
        crawler = CadespCrawler(config=config, parser=parser)
        crawler.crawl(VALID, output_path="")

        mock_driver_cls.assert_called_once()
        mock_solver_cls.assert_called_once_with("key")
        instance.quit.assert_called_once()

    def test_uses_default_parser_exporter(self):
        crawler = CadespCrawler()
        assert crawler._parser is not None
        assert crawler._exporter is not None

    def test_uses_cadesp_base_url(self):
        crawler = CadespCrawler()
        assert "cadesp.fazenda.sp.gov.br" in crawler._config.base_url
