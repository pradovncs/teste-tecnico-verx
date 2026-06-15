class CrawlerError(Exception):
    """Base exception for all crawler-related errors."""


class NavigationError(CrawlerError):
    """Raised when browser navigation fails."""


class ParseError(CrawlerError):
    """Raised when HTML parsing fails."""


class ExportError(CrawlerError):
    """Raised when data export fails."""


class CaptchaError(CrawlerError):
    """Raised when the image captcha cannot be solved."""


class ConsultaError(CrawlerError):
    """Raised when the CNPJ consultation form cannot be submitted."""


class BlockedError(CrawlerError):
    """Raised when the site (F5 BIG-IP firewall) blocks the request."""


class InvalidCNPJError(CrawlerError):
    """Raised when the provided CNPJ is invalid."""
