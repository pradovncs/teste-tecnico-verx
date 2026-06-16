import csv
import json
import logging
import os
from typing import List

from src.core.exceptions import ExportError
from src.core.interfaces import IExporter
from src.core.models import Contribuinte

logger = logging.getLogger(__name__)


class CSVExporter(IExporter):
    """Exporta os contribuintes para CSV (ou JSON, conforme a extensão)."""

    BASE_FIELDS = ["cnpj", "inscricao_estadual", "nome_empresarial", "situacao_cadastral"]

    def export(self, data: List[Contribuinte], filepath: str) -> None:
        """Exporta uma lista de ``Contribuinte`` para o caminho informado.

        Se ``filepath`` terminar em ``.json`` exporta em JSON, caso contrário CSV.

        Raises:
            ExportError: Se o arquivo não puder ser escrito.
        """
        logger.info("Exportando %d registro(s) para %s", len(data), filepath)
        rows = [c.to_dict() for c in data]
        try:
            os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
            if filepath.lower().endswith(".json"):
                self._write_json(rows, filepath)
            else:
                self._write_csv(rows, filepath)
            logger.info("Exportação concluída: %s", filepath)
        except OSError as exc:
            raise ExportError(f"Falha ao exportar para {filepath}: {exc}") from exc

    def _write_csv(self, rows: List[dict], filepath: str) -> None:
        """Escreve as linhas em CSV, unindo campos base e extras."""
        fieldnames = list(self.BASE_FIELDS)
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in rows:
                writer.writerow({k: row.get(k, "") for k in fieldnames})

    def _write_json(self, rows: List[dict], filepath: str) -> None:
        """Escreve as linhas em JSON."""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)
