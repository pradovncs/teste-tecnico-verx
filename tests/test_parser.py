import os

from src.parser import StockParser


MOCKS_DIR = os.path.join(os.path.dirname(__file__), "mocks")


def _read_mock(filename):
    with open(os.path.join(MOCKS_DIR, filename), "r", encoding="utf-8") as f:
        return f.read()


class TestStockParserNormalTable:
    """Tests for parsing a well-formed screener table."""

    def setup_method(self):
        self.parser = StockParser()
        self.html = _read_mock("sample_table.html")

    def test_returns_list_of_dicts(self):
        result = self.parser.parse(self.html)
        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)

    def test_extracts_correct_number_of_rows(self):
        result = self.parser.parse(self.html)
        assert len(result) == 3

    def test_extracts_symbol(self):
        result = self.parser.parse(self.html)
        assert result[0]["symbol"] == "AMX.BA"
        assert result[1]["symbol"] == "NOKA.BA"
        assert result[2]["symbol"] == "GGAL.BA"

    def test_extracts_name(self):
        result = self.parser.parse(self.html)
        assert result[0]["name"] == "América Móvil, S.A.B. de C.V."
        assert result[1]["name"] == "Nokia Corporation"

    def test_extracts_price(self):
        result = self.parser.parse(self.html)
        assert result[0]["price"] == "2089.00"
        assert result[1]["price"] == "557.50"
        assert result[2]["price"] == "1450.75"

    def test_each_dict_has_required_keys(self):
        result = self.parser.parse(self.html)
        for stock in result:
            assert "symbol" in stock
            assert "name" in stock
            assert "price" in stock


class TestStockParserEmptyTable:
    """Tests for parsing empty or missing tables."""

    def setup_method(self):
        self.parser = StockParser()

    def test_empty_tbody_returns_empty_list(self):
        html = "<html><body><table><thead></thead><tbody></tbody></table></body></html>"
        result = self.parser.parse(html)
        assert result == []

    def test_no_table_returns_empty_list(self):
        html = "<html><body><p>No data</p></body></html>"
        result = self.parser.parse(html)
        assert result == []

    def test_empty_html_returns_empty_list(self):
        html = ""
        result = self.parser.parse(html)
        assert result == []


class TestStockParserIncompleteData:
    """Tests for rows with missing or incomplete data."""

    def setup_method(self):
        self.parser = StockParser()

    def test_row_missing_price_is_skipped(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a data-symbol="TEST">TEST</a></td>
                <td>Test Corp</td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert result == []

    def test_row_missing_name_is_skipped(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a data-symbol="TEST">TEST</a></td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert result == []

    def test_mixed_valid_and_invalid_rows(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a data-symbol="GOOD">GOOD</a></td>
                <td>Good Corp</td>
                <td><span data-field="regularMarketPrice">100.00</span></td>
            </tr>
            <tr>
                <td><a data-symbol="BAD">BAD</a></td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["symbol"] == "GOOD"


class TestStockParserRankingColumn:
    """Tests for tables with a leading ranking number column."""

    def setup_method(self):
        self.parser = StockParser()

    def test_skips_ranking_column(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td>1</td>
                <td><a data-symbol="PETR4.SA">PETR4.SA</a></td>
                <td>Petrobras PN</td>
                <td><span data-field="regularMarketPrice">38.50</span></td>
            </tr>
            <tr>
                <td>2</td>
                <td><a data-symbol="VALE3.SA">VALE3.SA</a></td>
                <td>Vale ON</td>
                <td><span data-field="regularMarketPrice">62.30</span></td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 2
        assert result[0]["symbol"] == "PETR4.SA"
        assert result[0]["name"] == "Petrobras PN"
        assert result[0]["price"] == "38.50"
        assert result[1]["symbol"] == "VALE3.SA"

    def test_fallback_extract_with_ranking_column(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td>1</td>
                <td>PETR4.SA</td>
                <td>Petrobras PN</td>
                <td>38.50</td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["symbol"] == "PETR4.SA"
        assert result[0]["name"] == "Petrobras PN"
        assert result[0]["price"] == "38.50"

    def test_no_ranking_column_offset_is_zero(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a data-symbol="PETR4.SA">PETR4.SA</a></td>
                <td>Petrobras PN</td>
                <td><span data-field="regularMarketPrice">38.50</span></td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["symbol"] == "PETR4.SA"


class TestStockParserHrefExtraction:
    """Tests for extracting symbol from link href when data-symbol is absent."""

    def setup_method(self):
        self.parser = StockParser()

    def test_extracts_symbol_from_href(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a href="/quote/NVDA/">NVIDIA Corporation</a></td>
                <td>NVIDIA Corporation</td>
                <td>175.20</td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["symbol"] == "NVDA"
        assert result[0]["name"] == "NVIDIA Corporation"
        assert result[0]["price"] == "175.20"

    def test_extracts_name_from_second_quote_link(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td>1</td>
                <td><a href="/quote/PETR4.SA/" data-symbol="PETR4.SA">PETR4.SA</a></td>
                <td><a href="/quote/PETR4.SA/">Petrobras PN</a></td>
                <td>Chart</td>
                <td>38.50</td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["symbol"] == "PETR4.SA"
        assert result[0]["name"] == "Petrobras PN"
        assert result[0]["price"] == "38.50"

    def test_extracts_price_via_fin_streamer(self):
        html = """
        <html><body><table><tbody>
            <tr>
                <td><a href="/quote/VALE3.SA/" data-symbol="VALE3.SA">VALE3.SA</a></td>
                <td><a href="/quote/VALE3.SA/">Vale ON</a></td>
                <td><fin-streamer data-field="regularMarketPrice" data-value="62.30">62.30</fin-streamer></td>
            </tr>
        </tbody></table></body></html>
        """
        result = self.parser.parse(html)
        assert len(result) == 1
        assert result[0]["price"] == "62.30"


class TestStockParserYahooScreener:
    """Tests using a realistic Yahoo Finance equity screener HTML fixture."""

    def setup_method(self):
        self.parser = StockParser()
        self.html = _read_mock("screener_table.html")

    def test_extracts_all_rows(self):
        result = self.parser.parse(self.html)
        assert len(result) == 3

    def test_extracts_symbols(self):
        result = self.parser.parse(self.html)
        assert result[0]["symbol"] == "PETR4.SA"
        assert result[1]["symbol"] == "VALE3.SA"
        assert result[2]["symbol"] == "ITUB4.SA"

    def test_extracts_names_from_data_testid_cell(self):
        result = self.parser.parse(self.html)
        assert result[0]["name"] == "Petróleo Brasileiro S.A. - Petrobras"
        assert result[1]["name"] == "Vale S.A."
        assert result[2]["name"] == "Itaú Unibanco Holding S.A."

    def test_extracts_prices_from_fin_streamer(self):
        result = self.parser.parse(self.html)
        assert result[0]["price"] == "38.50"
        assert result[1]["price"] == "62.30"
        assert result[2]["price"] == "8.05"
