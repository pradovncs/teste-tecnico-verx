import logging

from src.core.interfaces import IDriver

logger = logging.getLogger(__name__)


class ConsentHandler:
    """Dismisses cookie consent banners on web pages."""

    SELECTORS = [
        'button[name="agree"]',
        '.consent-overlay button.accept-all',
        'button[value="agree"]',
        'button.accept-all',
    ]

    def __init__(self, driver: IDriver) -> None:
        self._driver = driver

    def dismiss(self) -> None:
        """Try each known consent selector and click the first match."""
        for selector in self.SELECTORS:
            try:
                btn = self._driver.wait_for(selector, timeout=3)
                btn.click()
                logger.info("Dismissed consent banner via selector=%s", selector)
                try:
                    self._driver.wait_for_invisible(selector, timeout=3)
                except Exception:
                    pass
                return
            except Exception:
                continue
        logger.debug("No consent banner found")
