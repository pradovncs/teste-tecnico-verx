import os

import pytest

from src.core.exceptions import ExportError
from src.io.exporter import CSVExporter
from src.core.models import Stock


class TestCSVExporterNormal:
    """Tests for standard CSV export."""

    def setup_method(self):
        self.exporter = CSVExporter()

    def test_creates_csv_file(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [Stock(symbol="AAPL", name="Apple Inc.", price="195.42")]

        self.exporter.export(data, filepath)

        assert os.path.exists(filepath)

    def test_csv_has_correct_header(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [Stock(symbol="AAPL", name="Apple Inc.", price="195.42")]

        self.exporter.export(data, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()

        assert first_line == '"symbol","name","price"'

    def test_csv_has_correct_data_rows(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [
            Stock(symbol="AAPL", name="Apple Inc.", price="195.42"),
            Stock(symbol="MSFT", name="Microsoft Corporation", price="378.91"),
        ]

        self.exporter.export(data, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 3  # header + 2 data rows
        assert '"AAPL"' in lines[1]
        assert '"MSFT"' in lines[2]

    def test_csv_quotes_all_fields(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [Stock(symbol="AAPL", name="Apple Inc.", price="195.42")]

        self.exporter.export(data, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        data_line = lines[1].strip()
        assert data_line == '"AAPL","Apple Inc.","195.42"'


class TestCSVExporterEmpty:
    """Tests for exporting empty data."""

    def setup_method(self):
        self.exporter = CSVExporter()

    def test_empty_list_creates_file_with_header_only(self, tmp_path):
        filepath = str(tmp_path / "output.csv")

        self.exporter.export([], filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert len(lines) == 1
        assert '"symbol","name","price"' in lines[0]


class TestCSVExporterSpecialChars:
    """Tests for handling special characters."""

    def setup_method(self):
        self.exporter = CSVExporter()

    def test_handles_commas_in_name(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [
            Stock(symbol="AMX.BA", name="América Móvil, S.A.B. de C.V.", price="2089.00")
        ]

        self.exporter.export(data, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        assert '"América Móvil, S.A.B. de C.V."' in lines[1]

    def test_handles_unicode_characters(self, tmp_path):
        filepath = str(tmp_path / "output.csv")
        data = [
            Stock(symbol="TEST", name="Ação Brasileña São Paulo", price="100.00")
        ]

        self.exporter.export(data, filepath)

        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        assert "Ação Brasileña São Paulo" in content

    def test_creates_parent_directories(self, tmp_path):
        filepath = str(tmp_path / "nested" / "dir" / "output.csv")
        data = [Stock(symbol="TEST", name="Test", price="1.00")]

        self.exporter.export(data, filepath)

        assert os.path.exists(filepath)


class TestCSVExporterErrors:
    """Tests for export error handling."""

    def test_raises_export_error_on_write_failure(self, tmp_path):
        exporter = CSVExporter()
        # Create a regular file, then try to write inside it as if it were a dir
        blocker = tmp_path / "blocker"
        blocker.write_text("x")
        bad_path = str(blocker / "output.csv")
        data = [Stock(symbol="TEST", name="Test", price="1.00")]

        with pytest.raises(ExportError):
            exporter.export(data, bad_path)
