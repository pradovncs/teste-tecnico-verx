import logging
import time

from src.config import BASE_URL, OUTPUT_PATH
from src.driver import BrowserDriver
from src.parser import StockParser
from src.exporter import CSVExporter

logger = logging.getLogger(__name__)


class YahooFinanceCrawler:
    """Orchestrates the full crawling flow: navigate, filter, parse, export."""

    TABLE_SELECTOR = "table tbody tr"
    NEXT_BTN_SELECTOR = "button[data-testid='next-page-button']"
    REGION_BTN_SELECTOR = "button.fin-size-small.menuBtn.tw-rounded-md"
    APPLY_BTN_SELECTOR = "button[aria-label='Apply']"
    REGION_SEARCH_SELECTOR = 'input[placeholder="Search..."]'
    PAGE_SIZE_BTN_SELECTOR = "button[class*='tertiary-btn fin-size-small menuBtn rounded rightAlign']"
    CONSENT_SELECTORS = [
        'button[name="agree"]',
        '.consent-overlay button.accept-all',
        'button[value="agree"]',
        'button.accept-all',
    ]

    def __init__(self, driver=None, parser=None, exporter=None):
        self._driver = driver
        self._parser = parser or StockParser()
        self._exporter = exporter or CSVExporter()

    def crawl(self, region, output_path=OUTPUT_PATH):
        """Execute the full crawl: open page, filter by region, parse and export.

        Args:
            region: Region name to filter stocks (e.g. "Brazil").
            output_path: File path for CSV output.

        Returns:
            List of dicts with keys: symbol, name, price.
        """
        logger.info("Starting crawl region=%s output_path=%s", region, output_path)
        driver = self._driver or BrowserDriver()

        try:
            driver.open(BASE_URL)
            self._dismiss_consent(driver)
            self._wait_for_table(driver)
            self._apply_region_filter(driver, region)
            self._set_page_size(driver, 100)

            stocks = self._scrape_all_pages(driver)
            logger.info("Crawl complete — total_stocks=%d", len(stocks))

            if output_path:
                self._exporter.export(stocks, output_path)

            return stocks
        finally:
            if self._driver is None:
                driver.quit()

    def _scrape_all_pages(self, driver):
        """Scrape data from all pages by clicking the Next button."""
        all_stocks = []
        seen_symbols = set()
        page = 1

        while True:
            logger.info("Scraping page=%d", page)
            html = driver.get_html()
            page_stocks = self._parser.parse(html)

            new_stocks = []
            for stock in page_stocks:
                if stock["symbol"] not in seen_symbols:
                    seen_symbols.add(stock["symbol"])
                    new_stocks.append(stock)

            all_stocks.extend(new_stocks)
            logger.info("Page %d — new_stocks=%d total=%d", page, len(new_stocks), len(all_stocks))

            if not new_stocks or not self._go_to_next_page(driver):
                break

            page += 1

        return all_stocks

    def _go_to_next_page(self, driver):
        """Click the Next button if available and enabled.

        Returns:
            True if navigated to next page, False if no more pages.
        """
        try:
            next_buttons = driver.find_all(self.NEXT_BTN_SELECTOR)
            if not next_buttons:
                logger.info("No next button found — last page reached")
                return False

            next_btn = next_buttons[-1]
            if not next_btn.is_enabled() or next_btn.get_attribute("disabled"):
                logger.info("Next button disabled — last page reached")
                return False

            logger.info("Clicking next page button")
            next_btn.click()
            time.sleep(2)
            self._wait_for_table(driver)
            return True
        except Exception as exc:
            logger.warning("Failed to go to next page error=%s", exc)
            return False

    def _dismiss_consent(self, driver):
        """Dismiss cookie consent banner if present."""
        for selector in self.CONSENT_SELECTORS:
            try:
                btn = driver.wait_for(selector, timeout=3)
                btn.click()
                logger.info("Dismissed consent banner via selector=%s", selector)
                time.sleep(1)
                return
            except Exception:
                continue
        logger.debug("No consent banner found")

    def _apply_region_filter(self, driver, region):
        """Change the screener's region filter to the target region.

        Steps:
        1. Click the Region filter chip to open the dropdown.
        2. Uncheck any pre-selected region (e.g. United States).
        3. Type the desired region in the Search input.
        4. Check the matching region checkbox.
        5. Click Apply.

        Args:
            driver: BrowserDriver instance.
            region: Region name to select (e.g. 'Brazil').
        """
        try:
            # Step 1: Open the region filter dropdown
            region_chip = self._find_region_chip(driver)
            if not region_chip:
                logger.warning("Region filter chip not found")
                return

            logger.info("Step 1: Opening region filter dropdown")
            driver.click_element(region_chip)
            time.sleep(2)

            # Step 2: Uncheck default region
            logger.info("Step 2: Removing default region")
            self._remove_current_region(driver)

            # Step 3+4: Search and select desired region
            logger.info("Step 3+4: Searching and selecting region=%s", region)
            self._type_and_select_region(driver, region)
            time.sleep(1)

            # Step 5: Click Apply
            logger.info("Step 5: Clicking Apply")
            self._click_apply(driver)
            time.sleep(5)

            try:
                self._wait_for_table(driver)
                logger.info("Region filter applied successfully region=%s", region)
            except Exception:
                logger.warning("Table not yet loaded after filter — waiting more")
                time.sleep(5)
        except Exception as exc:
            logger.error("Failed to apply region filter error=%s", exc)
            time.sleep(3)

    def _find_region_chip(self, driver):
        """Find the Region filter chip on the screener."""
        buttons = driver.find_all(self.REGION_BTN_SELECTOR)
        logger.debug("Found %d filter chip buttons", len(buttons))
        for btn in buttons:
            try:
                if "region" in btn.text.lower():
                    logger.debug("Found region chip text=%s", btn.text.strip())
                    return btn
            except Exception:
                continue

        # Fallback: search all buttons for 'Region' text
        all_buttons = driver.find_all("button")
        logger.debug("Fallback — searching %d buttons for 'region'", len(all_buttons))
        for btn in all_buttons:
            try:
                if "region" in btn.text.lower():
                    logger.debug("Found region button (fallback) text=%s", btn.text.strip())
                    return btn
            except Exception:
                continue
        return None

    def _remove_current_region(self, driver):
        """Uncheck any currently selected region checkboxes via JavaScript."""
        unchecked_count = driver.execute_script("""
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            var count = 0;
            for (var i = 0; i < checkboxes.length; i++) {
                if (checkboxes[i].checked) {
                    var parent = checkboxes[i].closest('label')
                        || checkboxes[i].parentElement;
                    if (parent) { parent.click(); } else { checkboxes[i].click(); }
                    count++;
                }
            }
            return count;
        """)
        logger.info("Unchecked %d default region(s)", unchecked_count)
        if unchecked_count > 0:
            time.sleep(1)

    def _type_and_select_region(self, driver, region):
        """Type the region name in the search box and click its checkbox."""
        try:
            search_input = driver.wait_for(self.REGION_SEARCH_SELECTOR, timeout=5)
        except Exception:
            logger.warning("Region search input not found")
            return

        search_input.clear()
        search_input.send_keys(region)
        logger.info("Typed region=%s into search box", region)
        time.sleep(2)

        # Use JavaScript to find and click the checkbox matching the region
        clicked = driver.execute_script("""
            var region = arguments[0].toLowerCase();
            // Strategy 1: labels wrapping checkboxes
            var labels = document.querySelectorAll('label');
            for (var i = 0; i < labels.length; i++) {
                if (labels[i].textContent.trim().toLowerCase().indexOf(region) !== -1) {
                    var cb = labels[i].querySelector('input[type="checkbox"]');
                    if (cb && !cb.checked) {
                        labels[i].click();
                        return 'label:' + labels[i].textContent.trim();
                    }
                }
            }
            // Strategy 2: checkbox with parent containing region text
            var checkboxes = document.querySelectorAll('input[type="checkbox"]');
            for (var j = 0; j < checkboxes.length; j++) {
                var parent = checkboxes[j].parentElement;
                while (parent && parent.tagName !== 'BODY') {
                    var text = parent.textContent.trim().toLowerCase();
                    if (text.indexOf(region) !== -1 && text.length < 100) {
                        if (!checkboxes[j].checked) {
                            parent.click();
                            return 'parent:' + parent.textContent.trim();
                        }
                        break;
                    }
                    parent = parent.parentElement;
                }
            }
            return null;
        """, region)

        if clicked:
            logger.info("Selected region via %s", clicked)
        else:
            logger.warning("No checkbox found for region=%s", region)

    def _click_apply(self, driver):
        """Click the Apply button to apply filters."""
        try:
            btn = driver.wait_for(self.APPLY_BTN_SELECTOR, timeout=5)
            driver.click_element(btn)
            logger.info("Clicked Apply button")
        except Exception:
            # Fallback: find Apply via JS
            clicked = driver.execute_script("""
                var buttons = document.querySelectorAll('button');
                for (var i = 0; i < buttons.length; i++) {
                    var text = buttons[i].textContent.trim();
                    if (text === 'Apply' || text === 'Done') {
                        buttons[i].click();
                        return text;
                    }
                }
                return null;
            """)
            if clicked:
                logger.info("Clicked %s button via JS fallback", clicked)
            else:
                logger.warning("Apply/Done button not found")

    def _set_page_size(self, driver, size=100):
        """Change the number of results per page.

        Args:
            driver: BrowserDriver instance.
            size: Number of results per page (25, 50, or 100).
        """
        logger.info("Setting page size to %d", size)
        try:
            btn = driver.wait_for(self.PAGE_SIZE_BTN_SELECTOR, timeout=5)
            driver.click_element(btn)
            time.sleep(2)

            # Use JavaScript to click the option matching the size
            clicked = driver.execute_script("""
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
                time.sleep(3)
                self._wait_for_table(driver)
            else:
                logger.warning("Page size option %d not found in dropdown", size)
        except Exception as exc:
            logger.warning("Failed to set page size error=%s", exc)

    def _wait_for_table(self, driver):
        """Wait for the results table to be present in the DOM."""
        driver.wait_for(self.TABLE_SELECTOR)
