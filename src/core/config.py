import logging
import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class CrawlerConfig:
    """Immutable configuration for the Yahoo Finance crawler."""

    base_url: str = "https://finance.yahoo.com/research-hub/screener/equity/"
    timeout: int = 30
    output_path: str = field(default_factory=lambda: os.path.join("output", "stocks.csv"))
    headless: bool = True
    page_size: int = 100


# Constantes de conveniência
_DEFAULT = CrawlerConfig()
BASE_URL = _DEFAULT.base_url
TIMEOUT = _DEFAULT.timeout
OUTPUT_PATH = _DEFAULT.output_path
HEADLESS = _DEFAULT.headless

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"


def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    log_level = os.environ.get("LOG_LEVEL", level).upper()
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, log_level, logging.INFO),
    )
