from bs4 import BeautifulSoup


class StockParser:
    """Parses HTML from Yahoo Finance screener and extracts stock data."""

    def parse(self, html):
        """Extract stock data from the screener HTML table.

        Args:
            html: Raw HTML string containing the screener results table.

        Returns:
            List of dicts with keys: symbol, name, price.
        """
        soup = BeautifulSoup(html, "lxml")
        rows = soup.select("table tbody tr")
        stocks = []

        for row in rows:
            stock = self._parse_row(row)
            if stock:
                stocks.append(stock)

        return stocks

    def _parse_row(self, row):
        """Extract symbol, name, and price from a single table row."""
        try:
            symbol = self._extract_symbol(row)
            name = self._extract_name(row)
            price = self._extract_price(row)

            if not all([symbol, name, price]):
                return None

            return {"symbol": symbol, "name": name, "price": price}
        except (AttributeError, IndexError):
            return None

    def _extract_symbol(self, row):
        """Extract the stock ticker symbol from a row."""
        tag = row.select_one("a[data-symbol]")
        if tag:
            return tag.get("data-symbol")

        cell = row.select_one("td:first-child")
        return cell.get_text(strip=True) if cell else None

    def _extract_name(self, row):
        """Extract the company name from a row."""
        cells = row.find_all("td")
        if len(cells) >= 2:
            return cells[1].get_text(strip=True)
        return None

    def _extract_price(self, row):
        """Extract the stock price from a row."""
        tag = row.select_one('[data-field="regularMarketPrice"]')
        if tag:
            return tag.get_text(strip=True)

        cells = row.find_all("td")
        if len(cells) >= 3:
            return cells[2].get_text(strip=True)
        return None
