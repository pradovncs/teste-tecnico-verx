import pytest

from src.core.interfaces import (
    ICaptchaSolver,
    ICrawler,
    IDriver,
    IExporter,
    IParser,
)


@pytest.mark.parametrize("iface", [IDriver, ICaptchaSolver, IParser, IExporter, ICrawler])
def test_interfaces_cannot_be_instantiated(iface):
    with pytest.raises(TypeError):
        iface()
