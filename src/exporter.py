import csv
import logging
import os

logger = logging.getLogger(__name__)


class CSVExporter:
    """Exports stock data to CSV files."""

    FIELDNAMES = ["symbol", "name", "price"]

    def export(self, data, filepath):
        """Export a list of stock dicts to a CSV file.

        Args:
            data: List of dicts with keys: symbol, name, price.
            filepath: Destination file path for the CSV output.
        """
        logger.info("Exporting rows=%d to filepath=%s", len(data), filepath)
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=self.FIELDNAMES,
                quoting=csv.QUOTE_ALL,
            )
            writer.writeheader()
            writer.writerows(data)
        logger.info("CSV export complete filepath=%s", filepath)
