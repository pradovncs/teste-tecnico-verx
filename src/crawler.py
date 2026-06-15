import logging
from typing import List, Optional

from src.captcha.solver import AntiCaptchaSolver
from src.core.config import CrawlerConfig
from src.core.exceptions import BlockedError, CaptchaError
from src.core.interfaces import ICaptchaSolver, ICrawler, IDriver, IExporter, IParser
from src.core.models import Contribuinte
from src.io.exporter import CSVExporter
from src.io.parser import ConsultaParser
from src.scraping.consulta import CnpjConsulta
from src.scraping.driver import StealthBrowserDriver

logger = logging.getLogger(__name__)


class CadespCrawler(ICrawler):
    """Orquestra a consulta pública do CADESP por CNPJ.

    Fluxo: abre a página (stealth) -> seleciona CNPJ -> preenche -> resolve
    captcha (AntiCaptcha) -> submete -> parseia -> exporta. Tenta novamente
    quando o captcha é recusado.
    """

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        driver: Optional[IDriver] = None,
        solver: Optional[ICaptchaSolver] = None,
        parser: Optional[IParser] = None,
        exporter: Optional[IExporter] = None,
    ) -> None:
        self._config = config or CrawlerConfig()
        self._driver = driver
        self._solver = solver
        self._parser = parser or ConsultaParser()
        self._exporter = exporter or CSVExporter()

    def crawl(self, cnpj: str, output_path: Optional[str] = None) -> List[Contribuinte]:
        """Executa a consulta completa para um CNPJ.

        Args:
            cnpj: CNPJ a consultar (com ou sem máscara).
            output_path: Caminho do arquivo de saída. Usa o padrão do config
                quando ``None``; ``""`` desativa a exportação.

        Returns:
            Lista de ``Contribuinte`` encontrados (geralmente um).

        Raises:
            CrawlerError: Se uma etapa crítica falhar.
        """
        effective_output = output_path if output_path is not None else self._config.output_path
        logger.info("Iniciando consulta cnpj=%s output=%s", cnpj, effective_output)

        driver = self._driver or StealthBrowserDriver(
            headless=self._config.headless,
            timeout=self._config.timeout,
            stealth_mode=self._config.stealth,
            min_delay=self._config.min_delay,
            max_delay=self._config.max_delay,
        )
        solver = self._solver or AntiCaptchaSolver(self._config.anticaptcha_key)

        try:
            results = self._consultar_com_retentativa(driver, solver, cnpj)
            logger.info("Consulta concluída — registros=%d", len(results))

            if effective_output:
                self._exporter.export(results, effective_output)
            return results
        finally:
            if self._driver is None:
                driver.quit()

    def _consultar_com_retentativa(
        self, driver: IDriver, solver: ICaptchaSolver, cnpj: str
    ) -> List[Contribuinte]:
        """Tenta a consulta múltiplas vezes para contornar captcha recusado."""
        attempts = max(1, self._config.max_captcha_attempts)
        last_error: Optional[Exception] = None

        for attempt in range(1, attempts + 1):
            logger.info("Tentativa %d/%d", attempt, attempts)
            driver.open(self._config.base_url)
            consulta = CnpjConsulta(driver, solver)
            try:
                html = consulta.run(cnpj)
                return self._parser.parse(html)
            except CaptchaError as exc:
                last_error = exc
                logger.warning("Captcha falhou (tentativa %d): %s", attempt, exc)
                continue
            except BlockedError:
                # Bloqueio do firewall não se resolve repetindo de imediato.
                raise

        raise CaptchaError(
            f"Não foi possível resolver o captcha em {attempts} tentativas: {last_error}"
        )
