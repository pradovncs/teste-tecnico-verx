import pytest

from src.core.models import Stock


class TestStock:
    """Tests for the Stock dataclass."""

    def test_creates_stock_with_attributes(self):
        stock = Stock(symbol="PETR4.SA", name="Petrobras", price="38.50")
        assert stock.symbol == "PETR4.SA"
        assert stock.name == "Petrobras"
        assert stock.price == "38.50"

    def test_to_dict_returns_plain_dict(self):
        stock = Stock(symbol="VALE3.SA", name="Vale S.A.", price="62.30")
        result = stock.to_dict()
        assert result == {"symbol": "VALE3.SA", "name": "Vale S.A.", "price": "62.30"}
        assert isinstance(result, dict)

    def test_equality_by_value(self):
        stock1 = Stock(symbol="AAPL", name="Apple Inc.", price="195.42")
        stock2 = Stock(symbol="AAPL", name="Apple Inc.", price="195.42")
        assert stock1 == stock2

    def test_inequality_on_different_values(self):
        stock1 = Stock(symbol="AAPL", name="Apple Inc.", price="195.42")
        stock2 = Stock(symbol="MSFT", name="Microsoft", price="378.91")
        assert stock1 != stock2

    def test_repr_contains_fields(self):
        stock = Stock(symbol="PETR4.SA", name="Petrobras", price="38.50")
        r = repr(stock)
        assert "PETR4.SA" in r
        assert "Petrobras" in r
        assert "38.50" in r


class TestStockValidation:
    """Tests for __post_init__ validation."""

    def test_empty_symbol_raises_value_error(self):
        with pytest.raises(ValueError, match="symbol"):
            Stock(symbol="", name="Test", price="10.00")

    def test_blank_symbol_raises_value_error(self):
        with pytest.raises(ValueError, match="symbol"):
            Stock(symbol="   ", name="Test", price="10.00")

    def test_empty_name_raises_value_error(self):
        with pytest.raises(ValueError, match="name"):
            Stock(symbol="TEST", name="", price="10.00")

    def test_blank_name_raises_value_error(self):
        with pytest.raises(ValueError, match="name"):
            Stock(symbol="TEST", name="   ", price="10.00")
