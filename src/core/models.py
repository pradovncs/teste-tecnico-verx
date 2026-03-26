from dataclasses import asdict, dataclass


@dataclass
class Stock:
    """Represents a stock extracted from the Yahoo Finance screener."""

    symbol: str
    name: str
    price: str

    def __post_init__(self) -> None:
        if not self.symbol or not self.symbol.strip():
            raise ValueError("Stock symbol cannot be empty")
        if not self.name or not self.name.strip():
            raise ValueError("Stock name cannot be empty")

    def to_dict(self) -> dict:
        """Convert to a plain dictionary."""
        return asdict(self)
