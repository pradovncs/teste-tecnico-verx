import pytest

from src.core.exceptions import (
    CrawlerError,
    ExportError,
    FilterError,
    NavigationError,
    PaginationError,
    ParseError,
)


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        "exc_class",
        [NavigationError, ParseError, ExportError, FilterError, PaginationError],
    )
    def test_subclass_of_crawler_error(self, exc_class):
        assert issubclass(exc_class, CrawlerError)

    def test_crawler_error_is_exception(self):
        assert issubclass(CrawlerError, Exception)


class TestExceptionUsage:
    def test_can_catch_parse_error_as_crawler_error(self):
        with pytest.raises(CrawlerError):
            raise ParseError("bad html")

    def test_can_catch_export_error_as_crawler_error(self):
        with pytest.raises(CrawlerError):
            raise ExportError("disk full")

    def test_can_catch_filter_error_as_crawler_error(self):
        with pytest.raises(CrawlerError):
            raise FilterError("region not found")

    def test_preserves_message(self):
        exc = ParseError("invalid table structure")
        assert str(exc) == "invalid table structure"

    def test_exception_chaining(self):
        try:
            try:
                raise ValueError("original")
            except ValueError as original:
                raise ParseError("wrapper") from original
        except ParseError as exc:
            assert exc.__cause__ is not None
            assert isinstance(exc.__cause__, ValueError)
