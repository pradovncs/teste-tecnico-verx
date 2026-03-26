import csv
import logging
import os
from typing import List

from src.core.exceptions import ExportError
from src.core.interfaces import IExporter
from src.core.models import Stock

logger = logging.getLogger(__name__)


class CSVExporter(IExporter):
    """Exporta dados de ações para CSV."""

    FIELDNAMES = ["symbol", "name", "price"]

    def export(self, data: List[Stock], filepath: str) -> None:
        """Export a list of Stock instances to a CSV file.

        Args:
            data: List of Stock instances to export.
            filepath: Destination file path for the CSV output.

        Raises:
            ExportError: If the file cannot be written.
        """
        logger.info("Exporting rows=%d to filepath=%s", len(data), filepath)
        try:
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)

            with open(filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=self.FIELDNAMES,
                    quoting=csv.QUOTE_ALL,
                )
                writer.writeheader()
                writer.writerows([s.to_dict() for s in data])
            logger.info("CSV export complete filepath=%s", filepath)
        except OSError as exc:
            raise ExportError(f"Failed to export CSV to {filepath}: {exc}") from exc
