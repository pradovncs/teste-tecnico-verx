import logging
import os

BASE_URL = "https://finance.yahoo.com/research-hub/screener/equity/"

TIMEOUT = 30

OUTPUT_PATH = os.path.join("examples", "output.csv")

HEADLESS = True

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()


def setup_logging():
    """Configure structured logging for the application."""
    logging.basicConfig(
        format=LOG_FORMAT,
        level=getattr(logging, LOG_LEVEL, logging.INFO),
    )
