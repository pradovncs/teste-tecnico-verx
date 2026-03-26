import argparse
import logging
import sys

from src.core.config import CrawlerConfig, setup_logging
from src.core.exceptions import CrawlerError
from src.crawler import YahooFinanceCrawler

logger = logging.getLogger(__name__)


def main():
    """CLI entry point for the Yahoo Finance Stock Crawler."""
    config = CrawlerConfig()

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
        default=config.output_path,
        help=f"Output CSV file path (default: {config.output_path})",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    setup_logging(args.log_level)

    logger.info("Starting Yahoo Finance Crawler region=%s output=%s", args.region, args.output)

    try:
        crawler = YahooFinanceCrawler(config=config)
        stocks = crawler.crawl(region=args.region, output_path=args.output)

        logger.info("Done — found %d stocks for region '%s'", len(stocks), args.region)
        print(f"Found {len(stocks)} stocks for region '{args.region}'")
        print(f"CSV saved to: {args.output}")
    except CrawlerError as exc:
        logger.error("Crawl failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
