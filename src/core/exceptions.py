class CrawlerError(Exception):
    """Base exception for all crawler-related errors."""


class NavigationError(CrawlerError):
    """Raised when browser navigation fails."""


class ParseError(CrawlerError):
    """Raised when HTML parsing fails."""


class ExportError(CrawlerError):
    """Raised when data export fails."""


class FilterError(CrawlerError):
    """Raised when region filter application fails."""


class PaginationError(CrawlerError):
    """Raised when page navigation fails."""
