import csv
import json
import os

import pytest

from src.core.exceptions import ExportError
from src.core.models import Contribuinte
from src.io.exporter import CSVExporter


def _sample():
    return [
        Contribuinte(
            cnpj="11222333000181",
            inscricao_estadual="111",
            nome_empresarial="ACME",
            situacao_cadastral="Ativo",
            extras={"municipio": "SP"},
        )
    ]


class TestCSVExport:
    def test_writes_csv(self, tmp_path):
        path = str(tmp_path / "out.csv")
        CSVExporter().export(_sample(), path)

        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert rows[0]["cnpj"] == "11222333000181"
        assert rows[0]["nome_empresarial"] == "ACME"
        assert rows[0]["municipio"] == "SP"

    def test_creates_parent_dirs(self, tmp_path):
        path = str(tmp_path / "nested" / "dir" / "out.csv")
        CSVExporter().export(_sample(), path)
        assert os.path.exists(path)

    def test_empty_data_writes_header_only(self, tmp_path):
        path = str(tmp_path / "empty.csv")
        CSVExporter().export([], path)
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "cnpj" in content


class TestJSONExport:
    def test_writes_json_by_extension(self, tmp_path):
        path = str(tmp_path / "out.json")
        CSVExporter().export(_sample(), path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data[0]["cnpj"] == "11222333000181"
        assert data[0]["municipio"] == "SP"


class TestErrors:
    def test_raises_export_error_on_oserror(self):
        # Caminho inválido (diretório como arquivo) força OSError.
        with pytest.raises(ExportError):
            CSVExporter().export(_sample(), "/proc/should-not-write/out.csv")
