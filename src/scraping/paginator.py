import logging
import time
from typing import List

from src.core.interfaces import IDriver, IParser
from src.core.models import Stock

logger = logging.getLogger(__name__)


class Paginator:
    """Handles multi-page scraping with deduplication and page-size control."""

    TABLE_SELECTOR = "table tbody tr"
    NEXT_BTN_SELECTOR = "button[data-testid='next-page-button']"
    PAGE_SIZE_BTN_SELECTOR = (
        "button[class*='tertiary-btn fin-size-small menuBtn rounded rightAlign']"
    )

    def __init__(self, driver: IDriver, parser: IParser) -> None:
        self._driver = driver
        self._parser = parser

    def scrape_all_pages(self) -> List[Stock]:
        """Scrape data from all pages, deduplicating by symbol."""
        all_stocks: List[Stock] = []
        seen_symbols: set = set()
        page = 1

        while True:
            logger.info("Scraping page=%d", page)
            html = self._driver.get_html()
            page_stocks = self._parser.parse(html)

            new_stocks = []
            for stock in page_stocks:
                if stock.symbol not in seen_symbols:
                    seen_symbols.add(stock.symbol)
                    new_stocks.append(stock)

            all_stocks.extend(new_stocks)
            logger.info(
                "Page %d — new_stocks=%d total=%d", page, len(new_stocks), len(all_stocks)
            )

            if not new_stocks or not self._go_to_next_page():
                break

            page += 1

        return all_stocks

    def _go_to_next_page(self) -> bool:
        """Click the Next button if available and enabled."""
        try:
            next_buttons = self._driver.find_all(self.NEXT_BTN_SELECTOR)
            if not next_buttons:
                logger.info("No next button found — last page reached")
                return False

            next_btn = next_buttons[-1]
            if not next_btn.is_enabled() or next_btn.get_attribute("disabled"):
                logger.info("Next button disabled — last page reached")
                return False

            old_first = self._get_first_symbol()

            logger.info("Clicking next page button")
            next_btn.click()
            self._wait_for_page_change(old_first)
            return True
        except Exception as exc:
            logger.warning("Failed to go to next page error=%s", exc)
            return False

    _FIRST_SYMBOL_JS = (
        "var el = document.querySelector('table tbody tr a[data-symbol]');"
        "return el ? el.getAttribute('data-symbol') : '';"
    )

    def _get_first_symbol(self) -> str:
        """Pega o símbolo da primeira linha da tabela via JS atômico."""
        try:
            return self._driver.execute_script(self._FIRST_SYMBOL_JS) or ""
        except Exception:
            return ""

    def _wait_for_page_change(self, old_first: str, timeout: int = 10) -> None:
        """Espera até o conteúdo da tabela mudar."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            current = self._get_first_symbol()
            if current and current != old_first:
                return
            time.sleep(0.3)
        logger.warning("Timeout waiting for page content to change")

    def wait_for_table(self) -> None:
        """Wait for the results table to be present in the DOM."""
        self._driver.wait_for(self.TABLE_SELECTOR)

    def set_page_size(self, size: int = 100) -> None:
        """Change the number of results per page."""
        logger.info("Setting page size to %d", size)
        try:
            btn = self._driver.wait_for(self.PAGE_SIZE_BTN_SELECTOR, timeout=5)
            self._driver.click_element(btn)
            self._driver.wait_for(
                '[role="option"], [role="listbox"] li, ul li', timeout=5
            )

            clicked = self._driver.execute_script("""
                var size = arguments[0];
                var items = document.querySelectorAll(
                    '[role="option"], [role="listbox"] li, ul li'
                );
                for (var i = 0; i < items.length; i++) {
                    if (items[i].textContent.trim() === size) {
                        items[i].click();
                        return true;
                    }
                }
                return false;
            """, str(size))

            if clicked:
                logger.info("Page size set to %d", size)
                time.sleep(0.5)
                self.wait_for_table()
            else:
                logger.warning("Page size option %d not found in dropdown", size)
        except Exception as exc:
            logger.warning("Failed to set page size error=%s", exc)
