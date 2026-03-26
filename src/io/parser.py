import logging
import re
from typing import List, Optional

from bs4 import BeautifulSoup

from src.core.exceptions import ParseError
from src.core.interfaces import IParser
from src.core.models import Stock

logger = logging.getLogger(__name__)


class StockParser(IParser):
    """Extrai dados de ações do HTML usando BeautifulSoup."""

    _PRICE_RE = re.compile(r"^[\d,]+\.\d+$")
    _TICKER_RE = re.compile(r"^[A-Z]{1,5}(\.[A-Z]{1,2})?$")

    def parse(self, html: str) -> List[Stock]:
        """Extract stock data from the screener HTML table.

        Args:
            html: Raw HTML string containing the screener results table.

        Returns:
            List of Stock instances extracted from the HTML.

        Raises:
            ParseError: If the HTML cannot be parsed at all.
        """
        try:
            soup = BeautifulSoup(html, "lxml")
            rows = soup.select("table tbody tr")
            logger.info("Parsing HTML — found rows=%d in table", len(rows))
            stocks = []

            for row in rows:
                stock = self._parse_row(row)
                if stock:
                    stocks.append(stock)

            logger.info("Parsed stocks=%d from rows=%d", len(stocks), len(rows))
            return stocks
        except ParseError:
            raise
        except Exception as exc:
            raise ParseError(f"Failed to parse HTML: {exc}") from exc

    def _parse_row(self, row) -> Optional[Stock]:
        """Extract symbol, name, and price from a single table row."""
        try:
            cells = row.find_all("td")
            if not cells:
                return None

            symbol = self._extract_symbol(row, cells)
            name = self._extract_name(row, cells)
            price = self._extract_price(row, cells)

            if not all([symbol, name, price]):
                logger.debug(
                    "Skipping row — symbol=%s name=%s price=%s cells=%d first_cell=%s",
                    symbol, name, price, len(cells),
                    cells[0].get_text(strip=True)[:50] if cells else "N/A",
                )
                return None

            return Stock(symbol=symbol, name=name, price=price)
        except (AttributeError, IndexError) as exc:
            logger.debug("Error parsing row: %s", exc)
            return None

    def _extract_symbol(self, row, cells) -> Optional[str]:
        """Extract the stock ticker symbol from a row."""
        tag = row.select_one("a[data-symbol]")
        if tag:
            return tag.get("data-symbol")

        # Tenta extrair do href /quote/TICKER
        link = row.select_one('a[href*="/quote/"]')
        if link:
            href = link.get("href", "")
            parts = href.rstrip("/").split("/")
            if parts:
                return parts[-1]

        # Link com texto que parece ticker
        for a_tag in row.select("a"):
            text = a_tag.get_text(strip=True)
            if self._TICKER_RE.match(text):
                return text

        # Fallback: pega da célula pela posição
        offset = self._get_data_offset(cells)
        if offset < len(cells):
            text = cells[offset].get_text(strip=True)
            if text:
                return text
        return None

    def _extract_name(self, row, cells) -> Optional[str]:
        """Extract the company name from a row."""
        name_cell = row.select_one('td[data-testid-cell="companyshortname.raw"]')
        if name_cell:
            div = name_cell.select_one("div[title]")
            if div:
                return div.get("title")
            return name_cell.get_text(strip=True)

        # Procura título que pareça nome de empresa
        for el in row.select("[title]"):
            title = el.get("title", "").strip()
            if title and len(title) > 3 and not title.startswith("http"):
                if not self._TICKER_RE.match(title):
                    return title

        # Link /quote/ sem data-symbol geralmente tem o nome da empresa
        links = row.select('a[href*="/quote/"]')
        for link in links:
            if not link.get("data-symbol"):
                text = link.get_text(strip=True)
                if text and not self._TICKER_RE.match(text):
                    return text

        # Fallback: pega da célula pela posição
        offset = self._get_data_offset(cells)
        name_idx = offset + 1
        if name_idx < len(cells):
            return cells[name_idx].get_text(strip=True)
        return None

    def _extract_price(self, row, cells) -> Optional[str]:
        """Extract the stock price from a row."""
        tag = row.select_one(
            'fin-streamer[data-field="regularMarketPrice"], '
            '[data-field="regularMarketPrice"], '
            'span[data-field="regularMarketPrice"]'
        )
        if tag:
            val = tag.get("data-value") or tag.get_text(strip=True)
            if val:
                return val

        price_cell = row.select_one(
            'td[data-testid-cell="regularMarketPrice.fmt"], '
            'td[data-testid-cell="regularMarketPrice"]'
        )
        if price_cell:
            return price_cell.get_text(strip=True)

        # Fallback: primeira célula que parece preço (número com ponto decimal)
        offset = self._get_data_offset(cells)
        for cell in cells[offset:]:
            text = cell.get_text(strip=True)
            cleaned = text.replace(",", "")
            if self._PRICE_RE.match(cleaned):
                return text

        return None

    def _get_data_offset(self, cells) -> int:
        """Determine column offset to skip a leading ranking number column."""
        if cells and cells[0].get_text(strip=True).isdigit():
            return 1
        return 0
