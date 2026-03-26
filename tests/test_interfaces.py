import pytest

from src.core.interfaces import ICrawler, IDriver, IExporter, IParser


class TestIDriverCannotBeInstantiated:
    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            IDriver()


class TestIParserCannotBeInstantiated:
    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            IParser()


class TestIExporterCannotBeInstantiated:
    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            IExporter()


class TestICrawlerCannotBeInstantiated:
    def test_raises_type_error(self):
        with pytest.raises(TypeError):
            ICrawler()


class TestPartialImplementationFails:
    def test_missing_method_raises_type_error(self):
        class IncompleteDriver(IDriver):
            def open(self, url):
                pass

        with pytest.raises(TypeError):
            IncompleteDriver()

    def test_missing_parse_raises_type_error(self):
        class IncompleteParser(IParser):
            pass

        with pytest.raises(TypeError):
            IncompleteParser()

    def test_missing_export_raises_type_error(self):
        class IncompleteExporter(IExporter):
            pass

        with pytest.raises(TypeError):
            IncompleteExporter()

    def test_missing_crawl_raises_type_error(self):
        class IncompleteCrawler(ICrawler):
            pass

        with pytest.raises(TypeError):
            IncompleteCrawler()
