from abc import ABC, abstractmethod
from typing import Any, List, Optional


class IDriver(ABC):
    """Interface para drivers de automação do navegador."""

    @abstractmethod
    def open(self, url: str) -> None:
        ...

    @abstractmethod
    def find(self, selector: str) -> Any:
        ...

    @abstractmethod
    def find_all(self, selector: str) -> List[Any]:
        ...

    @abstractmethod
    def wait_for(self, selector: str, timeout: Optional[int] = None) -> Any:
        ...

    @abstractmethod
    def wait_for_invisible(self, selector: str, timeout: Optional[int] = None) -> bool:
        ...

    @abstractmethod
    def execute_script(self, script: str, *args: Any) -> Any:
        ...

    @abstractmethod
    def click_element(self, element: Any) -> None:
        ...

    @abstractmethod
    def get_html(self) -> str:
        ...

    @abstractmethod
    def quit(self) -> None:
        ...

    @abstractmethod
    def __enter__(self) -> "IDriver":
        ...

    @abstractmethod
    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        ...


class IParser(ABC):
    """Interface para parsers de dados de ações."""

    @abstractmethod
    def parse(self, html: str) -> list:
        ...


class IExporter(ABC):
    """Interface para exportadores de dados."""

    @abstractmethod
    def export(self, data: list, filepath: str) -> None:
        ...


class ICrawler(ABC):
    """Interface para o crawler."""

    @abstractmethod
    def crawl(self, region: str, output_path: Optional[str] = None) -> list:
        ...
