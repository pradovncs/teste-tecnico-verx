import logging
import os
import re

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class StockParser:
    """Parses HTML from Yahoo Finance screener and extracts stock data."""

    _PRICE_RE = re.compile(r"^[\d,]+\.\d+$")

    def parse(self, html):
        """Extract stock data from the screener HTML table.

        Args:
            html: Raw HTML string containing the screener results table.

        Returns:
            List of dicts with keys: symbol, name, price.
        """
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

    def _parse_row(self, row):
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

            return {"symbol": symbol, "name": name, "price": price}
        except (AttributeError, IndexError) as exc:
            logger.debug("Error parsing row: %s", exc)
            return None

    def _extract_symbol(self, row, cells):
        """Extract the stock ticker symbol from a row."""
        # Primary: data-symbol attribute on link
        tag = row.select_one("a[data-symbol]")
        if tag:
            return tag.get("data-symbol")

        # Secondary: extract from /quote/ link href
        link = row.select_one('a[href*="/quote/"]')
        if link:
            href = link.get("href", "")
            parts = href.rstrip("/").split("/")
            if parts:
                return parts[-1]

        # Tertiary: find link text matching ticker pattern
        for a_tag in row.select("a"):
            text = a_tag.get_text(strip=True)
            if self._TICKER_RE.match(text):
                return text

        # Quaternary: cell-based fallback
        offset = self._get_data_offset(cells)
        if offset < len(cells):
            text = cells[offset].get_text(strip=True)
            if text:
                return text
        return None

    def _extract_name(self, row, cells):
        """Extract the company name from a row."""
        # Primary: dedicated company name cell via data-testid-cell
        name_cell = row.select_one('td[data-testid-cell="companyshortname.raw"]')
        if name_cell:
            div = name_cell.select_one("div[title]")
            if div:
                return div.get("title")
            return name_cell.get_text(strip=True)

        # Secondary: any element with a title attribute that looks like a name
        for el in row.select("[title]"):
            title = el.get("title", "").strip()
            if title and len(title) > 3 and not title.startswith("http"):
                # Skip if it's just a ticker symbol
                if not self._TICKER_RE.match(title):
                    return title

        # Tertiary: /quote/ link without data-symbol (second link usually has company name)
        links = row.select('a[href*="/quote/"]')
        for link in links:
            if not link.get("data-symbol"):
                text = link.get_text(strip=True)
                if text and not self._TICKER_RE.match(text):
                    return text

        # Quaternary: cell-based fallback
        offset = self._get_data_offset(cells)
        name_idx = offset + 1
        if name_idx < len(cells):
            return cells[name_idx].get_text(strip=True)
        return None

    def _extract_price(self, row, cells):
        """Extract the stock price from a row."""
        # Primary: fin-streamer or any element with regularMarketPrice
        tag = row.select_one(
            'fin-streamer[data-field="regularMarketPrice"], '
            '[data-field="regularMarketPrice"], '
            'span[data-field="regularMarketPrice"]'
        )
        if tag:
            val = tag.get("data-value") or tag.get_text(strip=True)
            if val:
                return val

        # Secondary: cell with data-testid-cell for price
        price_cell = row.select_one(
            'td[data-testid-cell="regularMarketPrice.fmt"], '
            'td[data-testid-cell="regularMarketPrice"]'
        )
        if price_cell:
            return price_cell.get_text(strip=True)

        # Tertiary: first cell that looks like a price (number with decimal)
        offset = self._get_data_offset(cells)
        for cell in cells[offset:]:
            text = cell.get_text(strip=True)
            cleaned = text.replace(",", "")
            if self._PRICE_RE.match(cleaned):
                return text

        return None

    def _get_data_offset(self, cells):
        """Determine column offset to skip a leading ranking number column."""
        if cells and cells[0].get_text(strip=True).isdigit():
            return 1
        return 0

    def _dump_debug_html(self, rows):
        """Save first row HTML for offline debugging."""
        try:
            os.makedirs("debug_output", exist_ok=True)
            path = os.path.join("debug_output", "parser_debug_row.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(str(rows[0]))
            logger.debug("Saved debug row HTML to %s", path)

            # Log cell details for the first row
            cells = rows[0].find_all("td")
            logger.debug("First row has %d cells", len(cells))
            for i, cell in enumerate(cells[:8]):
                text = cell.get_text(strip=True)[:60]
                attrs = {k: v for k, v in cell.attrs.items()} if cell.attrs else {}
                logger.debug("  cell[%d]: text='%s' attrs=%s", i, text, attrs)
        except Exception as exc:
            logger.debug("Failed to dump debug HTML: %s", exc)
