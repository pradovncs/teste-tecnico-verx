import logging
from typing import List, Optional

from src.core.config import CrawlerConfig
from src.core.exceptions import CrawlerError
from src.core.interfaces import ICrawler, IDriver, IExporter, IParser
from src.core.models import Stock
from src.io.exporter import CSVExporter
from src.io.parser import StockParser
from src.scraping.consent_handler import ConsentHandler
from src.scraping.driver import BrowserDriver
from src.scraping.paginator import Paginator
from src.scraping.region_filter import RegionFilter

logger = logging.getLogger(__name__)


class YahooFinanceCrawler(ICrawler):
    """Orchestrates the full crawling flow: navigate, filter, parse, export."""

    def __init__(
        self,
        config: Optional[CrawlerConfig] = None,
        driver: Optional[IDriver] = None,
        parser: Optional[IParser] = None,
        exporter: Optional[IExporter] = None,
    ) -> None:
        self._config = config or CrawlerConfig()
        self._driver = driver
        self._parser = parser or StockParser()
        self._exporter = exporter or CSVExporter()

    def crawl(self, region: str, output_path: Optional[str] = None) -> List[Stock]:
        """Execute the full crawl: open page, filter by region, parse and export.

        Args:
            region: Region name to filter stocks (e.g. "Brazil").
            output_path: File path for CSV output. Uses config default when None
                         is not explicitly passed.

        Returns:
            List of Stock instances found for the given region.

        Raises:
            CrawlerError: If a critical step of the crawl fails.
        """
        effective_output = output_path if output_path is not None else self._config.output_path
        logger.info("Starting crawl region=%s output_path=%s", region, effective_output)
        driver = self._driver or BrowserDriver(
            headless=self._config.headless,
            timeout=self._config.timeout,
        )

        try:
            driver.open(self._config.base_url)

            ConsentHandler(driver).dismiss()

            paginator = Paginator(driver, self._parser)
            paginator.wait_for_table()

            RegionFilter(driver).apply(region)
            paginator.set_page_size(self._config.page_size)

            stocks = paginator.scrape_all_pages()
            logger.info("Crawl complete — total_stocks=%d", len(stocks))

            if effective_output:
                self._exporter.export(stocks, effective_output)

            return stocks
        finally:
            if self._driver is None:
                driver.quit()
