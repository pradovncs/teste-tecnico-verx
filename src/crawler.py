import logging
import time
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
            browser=self._config.browser,
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
        """Tenta a consulta, contornando captcha recusado e bloqueio do BIG-IP.

        Captcha recusado é tentado novamente recarregando a página. Um bloqueio
        do F5 BIG-IP dispara a recuperação do driver (novo fingerprint) e um
        backoff exponencial antes de nova tentativa, sem consumir as tentativas
        reservadas ao captcha.
        """
        captcha_attempts = max(1, self._config.max_captcha_attempts)
        block_attempts = max(1, self._config.max_block_attempts)
        last_error: Optional[Exception] = None
        block_count = 0
        attempt = 0

        while attempt < captcha_attempts:
            attempt += 1
            logger.info("Tentativa %d/%d", attempt, captcha_attempts)
            driver.open(self._config.base_url)
            consulta = CnpjConsulta(driver, solver)
            try:
                html = consulta.run(cnpj)
                return self._parser.parse(html)
            except CaptchaError as exc:
                last_error = exc
                logger.warning("Captcha falhou (tentativa %d): %s", attempt, exc)
                continue
            except BlockedError as exc:
                block_count += 1
                last_error = exc
                if block_count >= block_attempts:
                    logger.error(
                        "Bloqueio do F5 BIG-IP persistiu após %d tentativa(s)", block_count
                    )
                    raise
                backoff = self._block_backoff(block_count)
                logger.warning(
                    "Bloqueio do F5 BIG-IP (%d/%d). Recriando fingerprint e aguardando %.1fs",
                    block_count,
                    block_attempts,
                    backoff,
                )
                driver.recover()
                time.sleep(backoff)
                # Bloqueio não deve consumir as tentativas reservadas ao captcha.
                attempt -= 1

        raise CaptchaError(
            f"Não foi possível resolver o captcha em {captcha_attempts} tentativas: {last_error}"
        )

    def _block_backoff(self, block_count: int) -> float:
        """Backoff exponencial (segundos) entre tentativas após um bloqueio."""
        base = self._config.block_backoff_base
        delay = base * (2 ** (block_count - 1))
        return min(delay, self._config.block_backoff_max)
