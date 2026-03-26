import argparse
import logging

from src.config import OUTPUT_PATH, setup_logging
from src.crawler import YahooFinanceCrawler

logger = logging.getLogger(__name__)


def main():
    """CLI entry point for the Yahoo Finance Stock Crawler."""
    parser = argparse.ArgumentParser(
        description="Yahoo Finance Stock Crawler - Scrape stocks by region"
    )
    parser.add_argument(
        "--region",
        required=True,
        help='Region to filter stocks (e.g. "Brazil")',
    )
    parser.add_argument(
        "--output",
        default=OUTPUT_PATH,
        help=f"Output CSV file path (default: {OUTPUT_PATH})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    setup_logging()
    if args.log_level:
        logging.getLogger().setLevel(getattr(logging, args.log_level))

    logger.info("Starting Yahoo Finance Crawler region=%s output=%s", args.region, args.output)

    crawler = YahooFinanceCrawler()
    stocks = crawler.crawl(region=args.region, output_path=args.output)

    logger.info("Done — found %d stocks for region '%s'", len(stocks), args.region)
    print(f"Found {len(stocks)} stocks for region '{args.region}'")
    print(f"CSV saved to: {args.output}")


if __name__ == "__main__":
    main()
