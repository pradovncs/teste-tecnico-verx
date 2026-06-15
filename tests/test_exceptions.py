from src.core.exceptions import (
    BlockedError,
    CaptchaError,
    ConsultaError,
    CrawlerError,
    ExportError,
    InvalidCNPJError,
    NavigationError,
    ParseError,
)


def test_all_inherit_from_crawler_error():
    for exc in (
        NavigationError,
        ParseError,
        ExportError,
        CaptchaError,
        ConsultaError,
        BlockedError,
        InvalidCNPJError,
    ):
        assert issubclass(exc, CrawlerError)


def test_can_be_caught_as_base():
    try:
        raise CaptchaError("boom")
    except CrawlerError as exc:
        assert str(exc) == "boom"
