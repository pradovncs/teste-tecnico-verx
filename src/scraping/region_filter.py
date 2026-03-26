import logging
import time

from src.core.exceptions import FilterError
from src.core.interfaces import IDriver

logger = logging.getLogger(__name__)

_TABLE_SELECTOR = "table tbody tr"


class RegionFilter:
    """Applies a region filter on the Yahoo Finance screener."""

    CHIP_SELECTOR = "button.fin-size-small.menuBtn.tw-rounded-md"
    SEARCH_SELECTOR = 'input[placeholder="Search..."]'
    APPLY_SELECTOR = "button[aria-label='Apply']"

    def __init__(self, driver: IDriver) -> None:
        self._driver = driver

    def apply(self, region: str) -> None:
        """Open the region dropdown, deselect defaults, select target region, and apply.

        Args:
            region: Region name to select (e.g. 'Brazil').

        Raises:
            FilterError: If the region filter chip cannot be found.
        """
        try:
            chip = self._find_chip()
            if not chip:
                raise FilterError("Region filter chip not found on the page")

            logger.info("Step 1: Opening region filter dropdown")
            self._driver.click_element(chip)
            self._driver.wait_for(self.SEARCH_SELECTOR, timeout=5)

            logger.info("Step 2: Removing default region")
            self._remove_current()

            logger.info("Step 3+4: Searching and selecting region=%s", region)
            self._type_and_select(region)

            logger.info("Step 5: Clicking Apply")
            self._click_apply()
            self._driver.wait_for(_TABLE_SELECTOR, timeout=15)

            logger.info("Region filter applied successfully region=%s", region)
        except FilterError:
            raise
        except Exception as exc:
            raise FilterError(f"Failed to apply region filter: {exc}") from exc

    def _find_chip(self):
        """Find the Region filter chip button on the screener."""
        buttons = self._driver.find_all(self.CHIP_SELECTOR)
        logger.debug("Found %d filter chip buttons", len(buttons))
        for btn in buttons:
            try:
                if "region" in btn.text.lower():
                    logger.debug("Found region chip text=%s", btn.text.strip())
                    return btn
            except Exception:
                continue

        # Fallback: busca botões dentro da área de filtros
        all_buttons = self._driver.find_all("section button, nav button, div[class*='filter'] button")
        logger.debug("Fallback — searching %d buttons for 'region'", len(all_buttons))
        for btn in all_buttons:
            try:
                if "region" in btn.text.lower():
                    logger.debug("Found region button (fallback) text=%s", btn.text.strip())
                    return btn
            except Exception:
                continue
        return None

    def _remove_current(self) -> None:
        """Uncheck any currently selected region checkboxes via JavaScript."""
        unchecked_count = self._driver.execute_script("""
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
            time.sleep(0.3)

    def _type_and_select(self, region: str) -> None:
        """Type the region name in the search box and click its checkbox."""
        try:
            search_input = self._driver.wait_for(self.SEARCH_SELECTOR, timeout=5)
        except Exception:
            logger.warning("Region search input not found")
            return

        search_input.clear()
        search_input.send_keys(region)
        logger.info("Typed region=%s into search box", region)
        time.sleep(0.5)

        clicked = self._driver.execute_script("""
            var region = arguments[0].toLowerCase();
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

    def _click_apply(self) -> None:
        """Click the Apply button to confirm the region filter."""
        try:
            btn = self._driver.wait_for(self.APPLY_SELECTOR, timeout=5)
            self._driver.click_element(btn)
            logger.info("Clicked Apply button")
        except Exception:
            clicked = self._driver.execute_script("""
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
